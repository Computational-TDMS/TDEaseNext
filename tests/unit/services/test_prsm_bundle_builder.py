import csv
import json
from pathlib import Path

from app.services.prsm_bundle_builder import build_prsm_bundle


FIXTURE_DIR = Path("tests/fixtures/topmsv")


def _read_tsv(path: Path):
    with open(path, "r", encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp, delimiter="\t")
        return list(reader)


def test_build_prsm_bundle_generates_expected_contract_and_topn(tmp_path):
    result = build_prsm_bundle(
        prsm_single_path=FIXTURE_DIR / "mini_prsm_single.tsv",
        ms2_msalign_path=FIXTURE_DIR / "mini_ms2.msalign",
        output_dir=tmp_path,
        ms2_topn=2,
    )

    clean_path = tmp_path / "prsm_table_clean.tsv"
    bundle_path = tmp_path / "prsm_bundle.tsv"
    assert clean_path.exists()
    assert bundle_path.exists()

    clean_rows = _read_tsv(clean_path)
    bundle_rows = _read_tsv(bundle_path)
    assert len(clean_rows) == 3
    assert len(bundle_rows) == 3
    assert result["prsm_total"] == 3
    assert result["mapped_total"] == 2
    assert result["missing_total"] == 1

    row_100 = next(row for row in bundle_rows if row["prsm_id"] == "100")
    row_102 = next(row for row in bundle_rows if row["prsm_id"] == "102")

    assert row_100["mapping_status"] == "mapped"
    assert row_102["mapping_status"] == "missing_spectrum"
    assert row_100["spectrum_id"] == "10"
    assert row_100["scan"] == "500"
    assert row_100["proteoform_seq"] == "ACDEFG"

    peaks_100 = json.loads(row_100["ms2_peaks_json"])
    assert len(peaks_100) == 2
    # TopN by intensity keeps 50 and 10 peaks.
    assert peaks_100[0]["intensity"] == 50.0
    assert peaks_100[1]["intensity"] == 10.0

    peaks_102 = json.loads(row_102["ms2_peaks_json"])
    assert peaks_102 == []

    expected_columns = {
        "prsm_id",
        "Prsm ID",
        "spectrum_id",
        "scan",
        "mapping_status",
        "ms2_peaks_json",
        "modifications_json",
    }
    assert expected_columns.issubset(set(bundle_rows[0].keys()))


def test_build_prsm_bundle_enriches_feature_fields_from_optional_ms2_feature(tmp_path):
    build_prsm_bundle(
        prsm_single_path=FIXTURE_DIR / "mini_prsm_single.tsv",
        ms2_msalign_path=FIXTURE_DIR / "mini_ms2.msalign",
        output_dir=tmp_path,
        ms2_feature_path=FIXTURE_DIR / "mini_ms2.feature",
    )

    bundle_rows = _read_tsv(tmp_path / "prsm_bundle.tsv")
    row_101 = next(row for row in bundle_rows if row["prsm_id"] == "101")

    assert row_101["feature_id"] == "8888"
    assert row_101["feature_intensity"] == "2222.2"


def test_build_prsm_bundle_loads_cleavage_annotations_from_companion_xml(tmp_path):
    prsm_single_path = tmp_path / "demo_prsm_single.tsv"
    prsm_single_path.write_text(
        (FIXTURE_DIR / "mini_prsm_single.tsv").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    # Companion path auto-discovered by builder: *_prsm_single.tsv -> *_prsm.xml
    companion_xml_path = tmp_path / "demo_prsm.xml"
    companion_xml_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<prsm_list>
  <prsm>
    <prsm_id>100</prsm_id>
    <spectrum_id>10</spectrum_id>
    <spectrum_scan>500</spectrum_scan>
    <match_peak_num>16</match_peak_num>
    <match_fragment_num>15</match_fragment_num>
    <norm_match_fragment_num>10</norm_match_fragment_num>
    <proteoform>
      <proteo_match_seq>[Acetyl]-ACD[+15.99]EFG</proteo_match_seq>
    </proteoform>
    <annotated_protein>
      <annotation>
        <cleavage>
          <position>0</position>
          <exist_n_ion>1</exist_n_ion>
          <exist_c_ion>0</exist_c_ion>
          <matched_peaks>
            <ion_type>b</ion_type>
            <ion_display_position>1</ion_display_position>
            <peak_charge>1</peak_charge>
          </matched_peaks>
        </cleavage>
        <cleavage>
          <position>3</position>
          <exist_n_ion>1</exist_n_ion>
          <exist_c_ion>1</exist_c_ion>
        </cleavage>
      </annotation>
    </annotated_protein>
  </prsm>
</prsm_list>
""",
        encoding="utf-8",
    )

    build_prsm_bundle(
        prsm_single_path=prsm_single_path,
        ms2_msalign_path=FIXTURE_DIR / "mini_ms2.msalign",
        output_dir=tmp_path,
        ms2_topn=2,
    )

    bundle_rows = _read_tsv(tmp_path / "prsm_bundle.tsv")
    row_100 = next(row for row in bundle_rows if row["prsm_id"] == "100")
    row_101 = next(row for row in bundle_rows if row["prsm_id"] == "101")

    assert row_100["match_peak_num"] == "16"
    assert row_100["match_fragment_num"] == "15"
    assert row_100["norm_match_fragment_num"] == "10"
    assert row_100["proteo_match_seq"] == "[Acetyl]-ACD[+15.99]EFG"
    assert json.loads(row_100["fragment_breakpoints_json"]) == [1, 4]

    cleavage_annotations = json.loads(row_100["cleavage_annotations_json"])
    assert len(cleavage_annotations) == 2
    assert cleavage_annotations[0]["position"] == 0
    assert cleavage_annotations[0]["exist_n_ion"] == 1
    assert cleavage_annotations[0]["exist_c_ion"] == 0
    assert cleavage_annotations[0]["matched_peaks"][0]["ion_type"] == "b"

    # Rows without XML entry should keep empty annotation payloads.
    assert json.loads(row_101["fragment_breakpoints_json"]) == []
    assert json.loads(row_101["cleavage_annotations_json"]) == []
