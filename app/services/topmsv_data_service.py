"""
TopMSV HTML data parsing service.

Parses TopPIC/TopFD JavaScript assignment files under *_html outputs and
converts them into API-friendly JSON payloads for interactive viewers.
This is the canonical data source for interactive TopMSV; path resolution
uses tool-defined subResources (e.g. toppic ports.outputs[html_folder].subResources)
when provided, falling back to built-in patterns for backward compatibility.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_ID_SPLIT_RE = re.compile(r"[,\s;]+")


def _to_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _to_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        if isinstance(value, bool):
            return None
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        if isinstance(value, bool):
            return None
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _parse_int_tokens(value: Any) -> List[int]:
    if value is None:
        return []
    if isinstance(value, list):
        result: List[int] = []
        for item in value:
            parsed = _to_int(item)
            if parsed is not None:
                result.append(parsed)
        return sorted(set(result))

    text = str(value).strip()
    if not text:
        return []

    result: List[int] = []
    for token in _ID_SPLIT_RE.split(text):
        if not token:
            continue
        parsed = _to_int(token)
        if parsed is not None:
            result.append(parsed)
    return sorted(set(result))


def _parse_js_assignment_file(file_path: Path) -> Dict[str, Any]:
    content = file_path.read_text(encoding="utf-8", errors="ignore")
    start = content.find("{")
    end = content.rfind("}")
    if start < 0 or end < start:
        raise ValueError(f"Cannot find JSON object payload in file: {file_path}")
    payload = content[start : end + 1]
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON payload in file {file_path}: {exc}") from exc


def _rank_path(path: Path) -> tuple[int, int]:
    text = str(path).lower()
    preferred = 0 if "toppic_prsm" in text else 1
    return (preferred, len(path.parts))


def _rank_path_by_prefer(path: Path, prefer_paths: List[str]) -> tuple[int, int]:
    """Sort key: lower preferred index first, then shorter path."""
    text = str(path).lower()
    preferred = next(
        (i for i, p in enumerate(prefer_paths) if p.lower() in text),
        len(prefer_paths),
    )
    return (preferred, len(path.parts))


def _resolve_subresource_path(
    html_root: Path,
    id_value: int,
    config: Dict[str, Any],
) -> Optional[Path]:
    """
    Resolve a sub-resource file path from tool-defined subResources config.
    config: { "pattern": "**/data_js/prsms/prsm{id}.js", "preferPaths": [...], "optional": bool }
    """
    if not config or not isinstance(config, dict):
        return None
    pattern = config.get("pattern") or ""
    if not pattern or "{id}" not in pattern:
        return None
    glob_pattern = pattern.replace("{id}", str(id_value))
    prefer_paths = config.get("preferPaths")
    if not isinstance(prefer_paths, list):
        prefer_paths = []
    optional = bool(config.get("optional"))

    globbed = list(html_root.glob(glob_pattern))
    if not globbed:
        if optional:
            return None
        raise FileNotFoundError(
            f"Sub-resource file not found for id={id_value} (pattern={glob_pattern}) under {html_root}"
        )
    if prefer_paths:
        globbed.sort(key=lambda p: _rank_path_by_prefer(p, prefer_paths))
    else:
        globbed.sort(key=lambda p: len(p.parts))
    return globbed[0]


def _find_prsm_js_file(
    html_root: Path,
    prsm_id: int,
    sub_resources: Optional[Dict[str, Any]] = None,
) -> Path:
    if sub_resources and "prsm_js" in sub_resources:
        path = _resolve_subresource_path(html_root, prsm_id, sub_resources["prsm_js"])
        if path is not None:
            return path
        raise FileNotFoundError(f"PrSM file not found for prsm_id={prsm_id} under {html_root}")

    direct_candidates = [
        html_root / "toppic_prsm_cutoff" / "data_js" / "prsms" / f"prsm{prsm_id}.js",
        html_root / "toppic_prsm" / "data_js" / "prsms" / f"prsm{prsm_id}.js",
    ]
    for candidate in direct_candidates:
        if candidate.exists():
            return candidate

    globbed = list(html_root.glob(f"**/data_js/prsms/prsm{prsm_id}.js"))
    if not globbed:
        raise FileNotFoundError(f"PrSM file not found for prsm_id={prsm_id} under {html_root}")

    globbed.sort(key=_rank_path)
    return globbed[0]


def _find_spectrum_js_file(
    html_root: Path,
    spectrum_id: int,
    sub_resources: Optional[Dict[str, Any]] = None,
) -> Optional[Path]:
    if sub_resources and "spectrum_js" in sub_resources:
        return _resolve_subresource_path(
            html_root, spectrum_id, sub_resources["spectrum_js"]
        )

    direct_candidates = [
        html_root / "topfd" / "ms2_json" / f"spectrum{spectrum_id}.js",
    ]
    for candidate in direct_candidates:
        if candidate.exists():
            return candidate

    globbed = list(html_root.glob(f"**/ms2_json/spectrum{spectrum_id}.js"))
    if not globbed:
        return None
    globbed.sort(key=lambda path: len(path.parts))
    return globbed[0]


def _extract_sequence(annotation: Dict[str, Any]) -> str:
    first_pos = _to_int(annotation.get("first_residue_position"))
    last_pos = _to_int(annotation.get("last_residue_position"))
    residues = _to_list(annotation.get("residue"))

    if residues and first_pos is not None and last_pos is not None and last_pos >= first_pos:
        letters: List[str] = []
        for residue in residues:
            if not isinstance(residue, dict):
                continue
            pos = _to_int(residue.get("position"))
            acid = str(residue.get("acid", "")).strip()
            if pos is None or not acid:
                continue
            if first_pos <= pos <= last_pos:
                letters.append(acid)
        if letters:
            return "".join(letters)

    annotated_seq = str(annotation.get("annotated_seq") or "")
    cleaned = annotated_seq
    if cleaned.startswith("[") and "]-" in cleaned:
        cleaned = cleaned.split("]-", 1)[1]
    cleaned = re.sub(r"\[[^\]]+\]", "", cleaned)
    cleaned = cleaned.replace("(", "").replace(")", "")
    cleaned = re.sub(r"[^A-Z]", "", cleaned)
    return cleaned


def _extract_breakpoints(annotation: Dict[str, Any]) -> List[int]:
    breakpoints = set()
    for cleavage in _to_list(annotation.get("cleavage")):
        if not isinstance(cleavage, dict):
            continue
        if not cleavage.get("matched_peaks"):
            continue
        cleavage_pos = _to_int(cleavage.get("position"))
        if cleavage_pos is None:
            continue
        if cleavage_pos > 1:
            breakpoints.add(cleavage_pos - 1)
    return sorted(breakpoints)


def _extract_modifications(annotation: Dict[str, Any]) -> List[Dict[str, Any]]:
    modifications: List[Dict[str, Any]] = []

    for ptm_entry in _to_list(annotation.get("ptm")):
        if not isinstance(ptm_entry, dict):
            continue
        ptm_info = ptm_entry.get("ptm") if isinstance(ptm_entry.get("ptm"), dict) else {}
        occurrences = _to_list(ptm_entry.get("occurence") or ptm_entry.get("occurrence"))
        for occurrence in occurrences:
            if not isinstance(occurrence, dict):
                continue
            left_pos = _to_int(occurrence.get("left_pos") or occurrence.get("left_position"))
            right_pos = _to_int(occurrence.get("right_pos") or occurrence.get("right_position"))
            if right_pos is None:
                right_pos = left_pos
            modifications.append(
                {
                    "kind": "ptm",
                    "label": str(ptm_info.get("abbreviation") or ptm_entry.get("ptm_type") or "PTM"),
                    "ptm_type": str(ptm_entry.get("ptm_type") or ""),
                    "left_position": left_pos,
                    "right_position": right_pos,
                    "annotation": str(occurrence.get("anno") or ""),
                    "mono_mass": _to_float(ptm_info.get("mono_mass")),
                    "unimod": str(ptm_info.get("unimod") or ""),
                }
            )

    for shift_entry in _to_list(annotation.get("mass_shift")):
        if not isinstance(shift_entry, dict):
            continue
        left_pos = _to_int(shift_entry.get("left_position") or shift_entry.get("left_pos"))
        right_pos = _to_int(shift_entry.get("right_position") or shift_entry.get("right_pos"))
        if right_pos is None:
            right_pos = left_pos
        modifications.append(
            {
                "kind": "mass_shift",
                "label": str(shift_entry.get("anno") or shift_entry.get("shift") or "mass_shift"),
                "ptm_type": str(shift_entry.get("shift_type") or ""),
                "left_position": left_pos,
                "right_position": right_pos,
                "annotation": str(shift_entry.get("anno") or ""),
                "mono_mass": _to_float(shift_entry.get("shift")),
                "unimod": "",
            }
        )

    modifications.sort(
        key=lambda item: (
            item.get("left_position") if item.get("left_position") is not None else 10**9,
            item.get("right_position") if item.get("right_position") is not None else 10**9,
            str(item.get("kind") or ""),
        )
    )
    return modifications


def _extract_peak_ions(matched_ions: Any) -> List[Dict[str, Any]]:
    ions_container = matched_ions if isinstance(matched_ions, dict) else {}
    ions = _to_list(ions_container.get("matched_ion"))
    result: List[Dict[str, Any]] = []
    for ion in ions:
        if not isinstance(ion, dict):
            continue
        ion_position = _to_int(ion.get("ion_position"))
        ion_type = str(ion.get("ion_type") or "")
        result.append(
            {
                "ion_type": ion_type,
                "ion_position": ion_position,
                "display_position": _to_int(ion.get("ion_display_position")),
                "theoretical_mass": _to_float(ion.get("theoretical_mass")),
                "mass_error": _to_float(ion.get("mass_error")),
                "ppm": _to_float(ion.get("ppm")),
                "label": f"{ion_type}{ion_position or ''}".strip(),
            }
        )
    return result


def _extract_matched_peaks(prsm_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    ms = prsm_payload.get("ms") if isinstance(prsm_payload.get("ms"), dict) else {}
    peaks_container = ms.get("peaks") if isinstance(ms.get("peaks"), dict) else {}
    peaks = _to_list(peaks_container.get("peak"))

    rows: List[Dict[str, Any]] = []
    for peak in peaks:
        if not isinstance(peak, dict):
            continue
        ions = _extract_peak_ions(peak.get("matched_ions"))
        rows.append(
            {
                "peak_id": _to_int(peak.get("peak_id")),
                "spec_id": _to_int(peak.get("spec_id")),
                "monoisotopic_mass": _to_float(peak.get("monoisotopic_mass")),
                "monoisotopic_mz": _to_float(peak.get("monoisotopic_mz")),
                "intensity": _to_float(peak.get("intensity")),
                "charge": _to_int(peak.get("charge")),
                "matched_ion_count": len(ions),
                "matched_ions": ions,
                "matched_ion_labels": ", ".join(
                    ion["label"] for ion in ions if isinstance(ion.get("label"), str) and ion["label"]
                ),
            }
        )
    return rows


def _extract_raw_spectrum(ms2_payload: Dict[str, Any]) -> Dict[str, Any]:
    raw_peaks: List[Dict[str, Any]] = []
    for idx, peak in enumerate(_to_list(ms2_payload.get("peaks"))):
        if not isinstance(peak, dict):
            continue
        mz = _to_float(peak.get("mz"))
        intensity = _to_float(peak.get("intensity"))
        if mz is None or intensity is None:
            continue
        raw_peaks.append({"index": idx, "mz": mz, "intensity": intensity})

    envelope_rows: List[Dict[str, Any]] = []
    for envelope in _to_list(ms2_payload.get("envelopes")):
        if not isinstance(envelope, dict):
            continue
        envelope_rows.append(
            {
                "id": _to_int(envelope.get("id")),
                "mono_mass": _to_float(envelope.get("mono_mass")),
                "charge": _to_int(envelope.get("charge")),
                "peak_count": len(_to_list(envelope.get("env_peaks"))),
            }
        )

    return {
        "scan": _to_int(ms2_payload.get("scan")),
        "retention_time": _to_float(ms2_payload.get("retention_time")),
        "target_mz": _to_float(ms2_payload.get("target_mz")),
        "min_mz": _to_float(ms2_payload.get("min_mz")),
        "max_mz": _to_float(ms2_payload.get("max_mz")),
        "n_ion_type": str(ms2_payload.get("n_ion_type") or ""),
        "c_ion_type": str(ms2_payload.get("c_ion_type") or ""),
        "raw_peaks": raw_peaks,
        "raw_peak_count": len(raw_peaks),
        "envelopes": envelope_rows,
    }


def build_topmsv_prsm_payload(
    html_root: Path,
    prsm_id: int,
    spectrum_id: Optional[int] = None,
    sub_resources: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build normalized TopMSV payload for a selected PrSM ID from HTML output assets.
    When sub_resources is provided (from tool definition ports.outputs[].subResources),
    path resolution uses those patterns instead of hardcoded paths.
    """
    if prsm_id < 0:
        raise ValueError("prsm_id must be non-negative")
    if not html_root.exists() or not html_root.is_dir():
        raise FileNotFoundError(f"HTML root folder not found: {html_root}")

    prsm_file = _find_prsm_js_file(html_root, prsm_id, sub_resources)
    prsm_object = _parse_js_assignment_file(prsm_file)
    prsm_payload = prsm_object.get("prsm") if isinstance(prsm_object.get("prsm"), dict) else {}

    if not prsm_payload:
        raise ValueError(f"PrSM payload is missing in file: {prsm_file}")

    annotated_protein = (
        prsm_payload.get("annotated_protein")
        if isinstance(prsm_payload.get("annotated_protein"), dict)
        else {}
    )
    annotation = annotated_protein.get("annotation") if isinstance(annotated_protein.get("annotation"), dict) else {}

    ms_header = {}
    ms = prsm_payload.get("ms") if isinstance(prsm_payload.get("ms"), dict) else {}
    if isinstance(ms.get("ms_header"), dict):
        ms_header = ms.get("ms_header")

    available_spectrum_ids = _parse_int_tokens(ms_header.get("ids"))
    if not available_spectrum_ids:
        available_spectrum_ids = sorted(
            {
                spec_id
                for spec_id in (
                    _to_int(entry.get("spec_id"))
                    for entry in _to_list((ms.get("peaks") or {}).get("peak") if isinstance(ms.get("peaks"), dict) else [])
                    if isinstance(entry, dict)
                )
                if spec_id is not None
            }
        )

    selected_spectrum_id = (
        spectrum_id
        if spectrum_id is not None
        else (available_spectrum_ids[0] if available_spectrum_ids else None)
    )
    if spectrum_id is not None and available_spectrum_ids and spectrum_id not in available_spectrum_ids:
        raise ValueError(
            f"spectrum_id {spectrum_id} is not listed in prsm ms_header.ids: {available_spectrum_ids}"
        )

    spectrum_file: Optional[Path] = None
    ms2_data: Dict[str, Any] = {
        "scan": None,
        "retention_time": None,
        "target_mz": None,
        "min_mz": None,
        "max_mz": None,
        "n_ion_type": "",
        "c_ion_type": "",
        "raw_peaks": [],
        "raw_peak_count": 0,
        "envelopes": [],
    }

    if selected_spectrum_id is not None:
        spectrum_file = _find_spectrum_js_file(
            html_root, selected_spectrum_id, sub_resources
        )
        if spectrum_file is not None:
            spectrum_payload = _parse_js_assignment_file(spectrum_file)
            ms2_data = _extract_raw_spectrum(spectrum_payload)
        else:
            logger.warning(
                "TopMSV spectrum file not found for spectrum_id=%s under %s",
                selected_spectrum_id,
                html_root,
            )

    sequence_data = {
        "value": _extract_sequence(annotation),
        "annotated": str(annotation.get("annotated_seq") or ""),
        "first_position": _to_int(annotation.get("first_residue_position")),
        "last_position": _to_int(annotation.get("last_residue_position")),
        "protein_length": _to_int(annotation.get("protein_length")),
        "breakpoints": _extract_breakpoints(annotation),
        "modifications": _extract_modifications(annotation),
    }

    return {
        "prsm_id": _to_int(prsm_payload.get("prsm_id")) or prsm_id,
        "protein_accession": str(
            annotated_protein.get("sequence_name")
            or annotated_protein.get("sequence_description")
            or ""
        ),
        "protein_description": str(annotated_protein.get("sequence_description") or ""),
        "source": {
            "html_root": str(html_root),
            "prsm_file": str(prsm_file),
            "spectrum_file": str(spectrum_file) if spectrum_file else None,
        },
        "ms_header": {
            "spectrum_file_name": str(ms_header.get("spectrum_file_name") or ""),
            "ms1_ids": _parse_int_tokens(ms_header.get("ms1_ids")),
            "ms1_scans": _parse_int_tokens(ms_header.get("ms1_scans")),
            "spectrum_ids": available_spectrum_ids,
            "scans": _parse_int_tokens(ms_header.get("scans")),
            "precursor_mono_mass": _to_float(ms_header.get("precursor_mono_mass")),
            "precursor_charge": _to_int(ms_header.get("precursor_charge")),
            "precursor_mz": _to_float(ms_header.get("precursor_mz")),
            "feature_inte": _to_float(ms_header.get("feature_inte")),
        },
        "sequence": sequence_data,
        "ms2": {
            "available_spectrum_ids": available_spectrum_ids,
            "selected_spectrum_id": selected_spectrum_id,
            "selected_scan_id": ms2_data.get("scan"),
            "raw_peaks": ms2_data.get("raw_peaks") or [],
            "raw_peak_count": ms2_data.get("raw_peak_count") or 0,
            "envelopes": ms2_data.get("envelopes") or [],
            "target_mz": ms2_data.get("target_mz"),
            "min_mz": ms2_data.get("min_mz"),
            "max_mz": ms2_data.get("max_mz"),
            "retention_time": ms2_data.get("retention_time"),
            "matched_peaks": _extract_matched_peaks(prsm_payload),
        },
    }
