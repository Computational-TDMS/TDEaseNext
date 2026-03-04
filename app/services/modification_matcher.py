from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Dict, Any, Union


def _ppm_error(observed: float, theoretical: float) -> float:
    return (observed - theoretical) / theoretical * 1e6


def load_modification_db(modification_db: Union[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    if isinstance(modification_db, list):
        return modification_db

    if isinstance(modification_db, str):
        path = Path(modification_db)
        if not path.exists():
            raise FileNotFoundError(f"Modification DB not found: {modification_db}")
        if path.suffix.lower() != ".json":
            raise ValueError("Only JSON modification databases are supported in this matcher")
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "modifications" in data:
            data = data["modifications"]
        if not isinstance(data, list):
            raise ValueError("Modification DB JSON must be a list of modifications")
        return data

    raise ValueError("Unsupported modification DB format")


def match_modifications(
    selected_peaks: Iterable[Dict[str, Any]],
    modification_db: Union[str, List[Dict[str, Any]]],
    ppm_tolerance: float,
) -> List[Dict[str, Any]]:
    modifications = load_modification_db(modification_db)
    matches: List[Dict[str, Any]] = []

    for peak in selected_peaks:
        peak_mz = float(peak["mz"])
        for mod in modifications:
            delta_mass = mod.get("deltaMass")
            if delta_mass is None:
                continue
            delta_mass = float(delta_mass)
            error = _ppm_error(peak_mz, delta_mass)
            if abs(error) <= ppm_tolerance:
                matches.append(
                    {
                        "peakMz": peak_mz,
                        "modification": mod.get("name", "unknown"),
                        "deltaMass": delta_mass,
                        "error": error,
                    }
                )

    matches.sort(key=lambda m: abs(m["error"]))
    return matches
