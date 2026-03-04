from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Dict, Any


PROTON_MASS = 1.007276466812
WATER_MASS = 18.010564684

AMINO_ACID_MASS = {
    "A": 71.037113805,
    "R": 156.10111105,
    "N": 114.04292747,
    "D": 115.026943065,
    "C": 103.009184505,
    "E": 129.042593135,
    "Q": 128.05857754,
    "G": 57.021463735,
    "H": 137.058911875,
    "I": 113.084064015,
    "L": 113.084064015,
    "K": 128.09496305,
    "M": 131.040484645,
    "F": 147.068413945,
    "P": 97.052763875,
    "S": 87.032028435,
    "T": 101.047678505,
    "W": 186.07931298,
    "Y": 163.063328575,
    "V": 99.068413945,
}


@dataclass(frozen=True)
class SpectrumPeak:
    mz: float
    intensity: float


def _ppm_error(observed: float, theoretical: float) -> float:
    return (observed - theoretical) / theoretical * 1e6


def _sequence_masses(sequence: str) -> List[float]:
    masses: List[float] = []
    for aa in sequence:
        if aa not in AMINO_ACID_MASS:
            raise ValueError(f"Unknown amino acid: {aa}")
        masses.append(AMINO_ACID_MASS[aa])
    return masses


def _theoretical_ions(sequence: str) -> List[Dict[str, float]]:
    masses = _sequence_masses(sequence)
    ions: List[Dict[str, float]] = []
    n = len(masses)
    if n < 2:
        return ions

    prefix = [0.0]
    for mass in masses:
        prefix.append(prefix[-1] + mass)

    for i in range(1, n):
        b_mass = prefix[i] + PROTON_MASS
        y_mass = (prefix[n] - prefix[i]) + WATER_MASS + PROTON_MASS
        ions.append({"mz": b_mass, "type": f"b{i}"})
        ions.append({"mz": y_mass, "type": f"y{n - i}"})

    return ions


def match_fragments(
    sequence: str,
    spectrum_data: Iterable[Dict[str, Any]],
    ppm_tolerance: float,
) -> List[Dict[str, Any]]:
    peaks = [SpectrumPeak(mz=float(p["mz"]), intensity=float(p.get("intensity", 0.0))) for p in spectrum_data]
    if not peaks:
        return []

    ions = _theoretical_ions(sequence)
    annotations: List[Dict[str, Any]] = []

    for ion in ions:
        theo_mz = ion["mz"]
        closest = min(peaks, key=lambda p: abs(p.mz - theo_mz))
        error = _ppm_error(closest.mz, theo_mz)
        if abs(error) <= ppm_tolerance:
            annotations.append(
                {
                    "mz": theo_mz,
                    "type": ion["type"],
                    "error": error,
                    "matchedMz": closest.mz,
                }
            )

    return annotations
