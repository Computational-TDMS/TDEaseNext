"""
Utilities for building TopMSV-ready PrSM bundle tables.

The bundle builder normalizes:
- TopPIC `*_prsm_single.tsv`
- TopFD `*_ms2.msalign`
- optional TopFD `*_ms2.feature`

into two files (names match config/tools/prsm_bundle_builder.json output patterns):
- `prsm_table_clean.tsv`
- `prsm_bundle.tsv`

Canonical interactive TopMSV data is provided by DataResolverRegistry (topmsv_prsm)
from HTML/JS assets; this bundle is for tabular views, cache, or export.
"""

from __future__ import annotations

import csv
import json
import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_NO_VALUE_MARKERS = {"", "-", "NA", "N/A", "null", "None"}
_SCAN_RE = re.compile(r"-?\d+")


def _to_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text in _NO_VALUE_MARKERS:
        return None
    try:
        return int(float(text))
    except (TypeError, ValueError):
        return None


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text in _NO_VALUE_MARKERS:
        return None
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def _parse_scan(value: Any) -> Optional[int]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    match = _SCAN_RE.search(text)
    if not match:
        return None
    return _to_int(match.group(0))


def _normalize_prsm_id(value: Any, fallback_index: int) -> str:
    text = (str(value).strip() if value is not None else "")
    return text if text else str(fallback_index)


def _split_modifications(raw: Any) -> List[str]:
    text = (str(raw).strip() if raw is not None else "")
    if not text or text in _NO_VALUE_MARKERS:
        return []
    parts = re.split(r"[;|]", text)
    return [part.strip() for part in parts if part.strip()]


def _extract_proteoform_sequence(proteoform: str, fallback: str = "") -> str:
    if not proteoform:
        proteoform = fallback
    if not proteoform:
        return ""
    # Remove bracket annotations (e.g. [+42.01], [Acetyl]) then keep letters only.
    without_brackets = re.sub(r"\[[^\]]*\]", "", proteoform)
    letters_only = "".join(ch for ch in without_brackets if ch.isalpha())
    return letters_only


def _detect_prsm_header(lines: List[str]) -> Tuple[int, List[str]]:
    for idx, raw in enumerate(lines):
        stripped = raw.strip()
        if not stripped:
            continue
        if "\t" not in stripped:
            continue
        columns = [part.strip() for part in stripped.split("\t")]
        if "Prsm ID" in columns:
            return idx, columns
    for idx, raw in enumerate(lines):
        stripped = raw.strip()
        if not stripped or stripped.startswith("*") or stripped.startswith("#"):
            continue
        if "\t" not in stripped:
            continue
        columns = [part.strip() for part in stripped.split("\t")]
        if len([c for c in columns if c]) < 2:
            continue
        if any(col.endswith(":") for col in columns if col):
            continue
        return idx, columns
    raise ValueError("Unable to detect TopPIC PrSM header row")


def read_toppic_prsm_table(prsm_single_path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    lines = prsm_single_path.read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines:
        raise ValueError(f"TopPIC PrSM file is empty: {prsm_single_path}")

    header_idx, columns = _detect_prsm_header(lines)
    rows: List[Dict[str, str]] = []

    for raw in lines[header_idx + 1 :]:
        if not raw.strip():
            continue
        values = [part.strip() for part in raw.split("\t")]
        if len(values) < len(columns):
            values.extend([""] * (len(columns) - len(values)))
        elif len(values) > len(columns):
            values = values[: len(columns)]
        rows.append({columns[i]: values[i] for i in range(len(columns))})

    return columns, rows


def parse_ms2_msalign(ms2_msalign_path: Path, top_n: int) -> Tuple[Dict[int, Dict[str, Any]], Dict[int, Dict[str, Any]]]:
    by_spectrum_id: Dict[int, Dict[str, Any]] = {}
    by_scan: Dict[int, Dict[str, Any]] = {}

    in_block = False
    current_meta: Dict[str, str] = {}
    current_peaks: List[Dict[str, Any]] = []

    def finalize_block() -> None:
        nonlocal current_meta, current_peaks, in_block
        spectrum_id = _to_int(current_meta.get("SPECTRUM_ID"))
        scan = _to_int(current_meta.get("SCANS"))
        if spectrum_id is None and scan is None:
            current_meta = {}
            current_peaks = []
            in_block = False
            return

        peaks_sorted = sorted(current_peaks, key=lambda item: item["intensity"], reverse=True)
        if top_n > 0:
            peaks_sorted = peaks_sorted[:top_n]
        peaks_sorted = sorted(peaks_sorted, key=lambda item: item["mass"])

        entry = {
            "spectrum_id": spectrum_id,
            "scan": scan,
            "retention_time": _to_float(current_meta.get("RETENTION_TIME")),
            "activation": current_meta.get("ACTIVATION", ""),
            "peaks": peaks_sorted,
        }

        if spectrum_id is not None and spectrum_id not in by_spectrum_id:
            by_spectrum_id[spectrum_id] = entry
        if scan is not None and scan not in by_scan:
            by_scan[scan] = entry

        current_meta = {}
        current_peaks = []
        in_block = False

    with open(ms2_msalign_path, "r", encoding="utf-8", errors="replace") as fp:
        for raw_line in fp:
            line = raw_line.strip()
            if not line:
                continue

            if line == "BEGIN IONS":
                in_block = True
                current_meta = {}
                current_peaks = []
                continue

            if line == "END IONS":
                finalize_block()
                continue

            if not in_block:
                continue

            if "=" in line:
                key, value = line.split("=", 1)
                current_meta[key.strip()] = value.strip()
                continue

            parts = [part.strip() for part in line.split("\t")]
            if len(parts) < 2:
                continue

            mass = _to_float(parts[0])
            intensity = _to_float(parts[1])
            if mass is None or intensity is None:
                continue

            peak: Dict[str, Any] = {"mass": mass, "intensity": intensity}
            if len(parts) > 2:
                charge = _to_int(parts[2])
                if charge is not None:
                    peak["charge"] = charge
            if len(parts) > 3:
                score = _to_float(parts[3])
                if score is not None:
                    peak["score"] = score
            current_peaks.append(peak)

    if in_block:
        finalize_block()

    return by_spectrum_id, by_scan


def parse_optional_ms2_feature(ms2_feature_path: Optional[Path]) -> Dict[int, Dict[str, str]]:
    if ms2_feature_path is None or not ms2_feature_path.exists():
        return {}

    with open(ms2_feature_path, "r", encoding="utf-8", errors="replace", newline="") as fp:
        reader = csv.DictReader(fp, delimiter="\t")
        if not reader.fieldnames:
            return {}

        result: Dict[int, Dict[str, str]] = {}
        for row in reader:
            spectrum_id = _to_int(row.get("Spectrum_ID") or row.get("Spectrum ID"))
            if spectrum_id is None or spectrum_id in result:
                continue
            result[spectrum_id] = {k: (v.strip() if isinstance(v, str) else "") for k, v in row.items()}
        return result


def _resolve_spectrum_mapping(
    spectrum_id: Optional[int],
    scan: Optional[int],
    by_spectrum_id: Dict[int, Dict[str, Any]],
    by_scan: Dict[int, Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    if spectrum_id is not None and spectrum_id in by_spectrum_id:
        return by_spectrum_id[spectrum_id]
    if scan is not None and scan in by_scan:
        return by_scan[scan]
    return None


def _write_tsv(path: Path, columns: List[str], rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=columns, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            normalized = {k: ("" if row.get(k) is None else row.get(k)) for k in columns}
            writer.writerow(normalized)


def _derive_companion_prsm_xml(prsm_single_path: Path) -> Optional[Path]:
    name = prsm_single_path.name
    candidates: List[Path] = []

    if name.endswith("_prsm_single.tsv"):
        candidates.append(prsm_single_path.with_name(name.replace("_prsm_single.tsv", "_prsm.xml")))
    if name.endswith(".tsv"):
        candidates.append(prsm_single_path.with_suffix(".xml"))

    unique: List[Path] = []
    seen = set()
    for candidate in candidates:
        key = str(candidate).lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)

    for candidate in unique:
        if candidate.exists():
            return candidate
    return None


def _extract_matched_peak_entries(cleavage_node: ET.Element) -> List[Dict[str, Any]]:
    matched: List[Dict[str, Any]] = []
    peak_nodes = cleavage_node.findall(".//matched_peaks") + cleavage_node.findall(".//matched_peak")
    for peak_node in peak_nodes:
        ion_type = (peak_node.findtext("ion_type") or "").strip()
        ion_display_position = _to_int(peak_node.findtext("ion_display_position"))
        peak_charge = _to_int(peak_node.findtext("peak_charge"))
        peak_mz = _to_float(peak_node.findtext("peak_mz") or peak_node.findtext("mass"))

        if (
            not ion_type
            and ion_display_position is None
            and peak_charge is None
            and peak_mz is None
        ):
            continue

        entry: Dict[str, Any] = {}
        if ion_type:
            entry["ion_type"] = ion_type
        if ion_display_position is not None:
            entry["ion_display_position"] = ion_display_position
        if peak_charge is not None:
            entry["peak_charge"] = peak_charge
        if peak_mz is not None:
            entry["peak_mz"] = peak_mz
        matched.append(entry)
    return matched


def parse_toppic_prsm_xml(
    prsm_xml_path: Optional[Path],
) -> Tuple[Dict[str, Dict[str, Any]], Dict[Tuple[Optional[int], Optional[int]], Dict[str, Any]]]:
    if prsm_xml_path is None or not prsm_xml_path.exists():
        return {}, {}

    by_prsm_id: Dict[str, Dict[str, Any]] = {}
    by_spectrum_scan: Dict[Tuple[Optional[int], Optional[int]], Dict[str, Any]] = {}

    try:
        tree = ET.parse(prsm_xml_path)
    except Exception as exc:
        logger.warning("Failed to parse TopPIC PrSM XML %s: %s", prsm_xml_path, exc)
        return {}, {}

    root = tree.getroot()
    for idx, prsm_node in enumerate(root.findall(".//prsm")):
        prsm_id = _normalize_prsm_id(prsm_node.findtext("prsm_id"), fallback_index=idx)
        spectrum_id = _to_int(prsm_node.findtext("spectrum_id"))
        spectrum_scan = _to_int(prsm_node.findtext("spectrum_scan"))

        cleavage_annotations: List[Dict[str, Any]] = []
        breakpoints: List[int] = []

        for cleavage_node in prsm_node.findall(".//cleavage"):
            position = _to_int(cleavage_node.findtext("position"))
            exist_n_ion = _to_int(cleavage_node.findtext("exist_n_ion"))
            exist_c_ion = _to_int(cleavage_node.findtext("exist_c_ion"))
            matched_peaks = _extract_matched_peak_entries(cleavage_node)

            if position is not None and position >= 0:
                break_after = position + 1
                if break_after > 0:
                    breakpoints.append(break_after)

            cleavage_entry: Dict[str, Any] = {}
            if position is not None:
                cleavage_entry["position"] = position
            if exist_n_ion is not None:
                cleavage_entry["exist_n_ion"] = exist_n_ion
            if exist_c_ion is not None:
                cleavage_entry["exist_c_ion"] = exist_c_ion
            if matched_peaks:
                cleavage_entry["matched_peaks"] = matched_peaks
            if cleavage_entry:
                cleavage_annotations.append(cleavage_entry)

        entry = {
            "prsm_id": prsm_id,
            "spectrum_id": spectrum_id,
            "scan": spectrum_scan,
            "match_peak_num": _to_int(prsm_node.findtext("match_peak_num")),
            "match_fragment_num": _to_int(prsm_node.findtext("match_fragment_num")),
            "norm_match_fragment_num": _to_int(prsm_node.findtext("norm_match_fragment_num")),
            "proteo_match_seq": (prsm_node.findtext("./proteoform/proteo_match_seq") or "").strip(),
            "fragment_breakpoints": sorted({bp for bp in breakpoints if bp > 0}),
            "cleavage_annotations": cleavage_annotations,
        }

        if prsm_id not in by_prsm_id:
            by_prsm_id[prsm_id] = entry
        key = (spectrum_id, spectrum_scan)
        if key not in by_spectrum_scan:
            by_spectrum_scan[key] = entry

    return by_prsm_id, by_spectrum_scan


# Default output filenames; should match config/tools/prsm_bundle_builder.json ports.outputs[].pattern
PRSM_TABLE_CLEAN_FILENAME = "prsm_table_clean.tsv"
PRSM_BUNDLE_FILENAME = "prsm_bundle.tsv"


def build_prsm_bundle(
    prsm_single_path: Path,
    ms2_msalign_path: Path,
    output_dir: Path,
    ms2_topn: int = 120,
    ms2_feature_path: Optional[Path] = None,
    output_filenames: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    if ms2_topn < 0:
        raise ValueError("ms2_topn must be >= 0")

    prsm_columns, prsm_rows = read_toppic_prsm_table(prsm_single_path)
    by_spectrum_id, by_scan = parse_ms2_msalign(ms2_msalign_path, ms2_topn)
    ms2_feature_map = parse_optional_ms2_feature(ms2_feature_path)
    prsm_xml_path = _derive_companion_prsm_xml(prsm_single_path)
    xml_by_prsm_id, xml_by_spectrum_scan = parse_toppic_prsm_xml(prsm_xml_path)
    if prsm_xml_path is not None:
        logger.info(
            "Loaded TopPIC PRSM XML annotations from %s (entries=%d)",
            prsm_xml_path,
            len(xml_by_prsm_id),
        )

    clean_columns = list(prsm_columns)
    for extra in ("prsm_id", "spectrum_id", "scan"):
        if extra not in clean_columns:
            clean_columns.append(extra)
    clean_rows: List[Dict[str, Any]] = []

    bundle_columns = [
        "prsm_id",
        "Prsm ID",
        "spectrum_id",
        "scan",
        "retention_time",
        "fragmentation",
        "proteoform_seq",
        "protein_accession",
        "protein_description",
        "feature_id",
        "feature_intensity",
        "match_peak_num",
        "match_fragment_num",
        "norm_match_fragment_num",
        "proteo_match_seq",
        "modifications_json",
        "fragment_breakpoints_json",
        "cleavage_annotations_json",
        "mapping_status",
        "ms2_peaks_json",
    ]
    bundle_rows: List[Dict[str, Any]] = []

    mapped_count = 0

    for index, row in enumerate(prsm_rows):
        prsm_id = _normalize_prsm_id(row.get("Prsm ID"), fallback_index=index)
        spectrum_id = _to_int(row.get("Spectrum ID"))
        scan = _parse_scan(row.get("Scan(s)") or row.get("Scans"))
        mapped_entry = _resolve_spectrum_mapping(spectrum_id, scan, by_spectrum_id, by_scan)
        mapping_status = "mapped" if mapped_entry else "missing_spectrum"
        if mapped_entry:
            mapped_count += 1

        xml_entry = (
            xml_by_prsm_id.get(prsm_id)
            or xml_by_spectrum_scan.get((spectrum_id, scan))
            or xml_by_spectrum_scan.get((spectrum_id, None))
            or xml_by_spectrum_scan.get((None, scan))
            or {}
        )
        fragment_breakpoints = xml_entry.get("fragment_breakpoints", [])
        cleavage_annotations = xml_entry.get("cleavage_annotations", [])

        modifications_payload = {
            "fixed_ptms": _split_modifications(row.get("Fixed PTMs")),
            "unexpected_modifications": _split_modifications(row.get("Unexpected modifications")),
            "variable_ptms": _split_modifications(row.get("Variable PTMs")),
        }

        ms2_feature_row = ms2_feature_map.get(spectrum_id or -1, {})
        feature_id = row.get("Feature ID") or ms2_feature_row.get("Fraction_feature_ID", "")
        feature_intensity = row.get("Feature intensity") or ms2_feature_row.get("Fraction_feature_intensity", "")

        clean_row = dict(row)
        clean_row["prsm_id"] = prsm_id
        clean_row["spectrum_id"] = "" if spectrum_id is None else str(spectrum_id)
        clean_row["scan"] = "" if scan is None else str(scan)
        clean_rows.append(clean_row)

        proteoform_seq = _extract_proteoform_sequence(
            row.get("Proteoform", ""),
            fallback=row.get("Database protein sequence", ""),
        )
        retention = row.get("Retention time", "") or row.get("Retention Time", "")
        fragmentation = row.get("Fragmentation", "")

        bundle_row = {
            "prsm_id": prsm_id,
            "Prsm ID": row.get("Prsm ID", prsm_id),
            "spectrum_id": "" if spectrum_id is None else str(spectrum_id),
            "scan": "" if scan is None else str(scan),
            "retention_time": retention,
            "fragmentation": fragmentation,
            "proteoform_seq": proteoform_seq,
            "protein_accession": row.get("Protein accession", ""),
            "protein_description": row.get("Protein description", ""),
            "feature_id": feature_id,
            "feature_intensity": feature_intensity,
            "match_peak_num": (
                "" if xml_entry.get("match_peak_num") is None
                else str(xml_entry["match_peak_num"])
            ),
            "match_fragment_num": (
                "" if xml_entry.get("match_fragment_num") is None
                else str(xml_entry["match_fragment_num"])
            ),
            "norm_match_fragment_num": (
                "" if xml_entry.get("norm_match_fragment_num") is None
                else str(xml_entry["norm_match_fragment_num"])
            ),
            "proteo_match_seq": xml_entry.get("proteo_match_seq", "") or row.get("Proteoform", ""),
            "modifications_json": json.dumps(modifications_payload, ensure_ascii=False, separators=(",", ":")),
            "fragment_breakpoints_json": json.dumps(
                fragment_breakpoints, ensure_ascii=False, separators=(",", ":")
            ),
            "cleavage_annotations_json": json.dumps(
                cleavage_annotations, ensure_ascii=False, separators=(",", ":")
            ),
            "mapping_status": mapping_status,
            "ms2_peaks_json": json.dumps(
                (mapped_entry or {}).get("peaks", []),
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        }
        bundle_rows.append(bundle_row)

    output_dir.mkdir(parents=True, exist_ok=True)
    names = output_filenames or {}
    clean_name = names.get("prsm_table_clean", PRSM_TABLE_CLEAN_FILENAME)
    bundle_name = names.get("prsm_bundle", PRSM_BUNDLE_FILENAME)
    clean_path = output_dir / clean_name
    bundle_path = output_dir / bundle_name
    _write_tsv(clean_path, clean_columns, clean_rows)
    _write_tsv(bundle_path, bundle_columns, bundle_rows)

    return {
        "prsm_total": len(prsm_rows),
        "mapped_total": mapped_count,
        "missing_total": len(prsm_rows) - mapped_count,
        "prsm_table_clean": str(clean_path),
        "prsm_bundle": str(bundle_path),
        "ms2_topn": ms2_topn,
    }
