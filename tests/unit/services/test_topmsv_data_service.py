from pathlib import Path

import pytest

from app.services.topmsv_data_service import build_topmsv_prsm_payload


def _write_js_assignment(file_path: Path, variable: str, payload: str) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(f"{variable} =\n{payload}\n", encoding="utf-8")


def test_build_topmsv_prsm_payload_parses_sequence_and_ms2(tmp_path: Path) -> None:
    html_root = tmp_path / "sample_html"
    prsm_file = html_root / "toppic_prsm_cutoff" / "data_js" / "prsms" / "prsm7.js"
    spectrum_file = html_root / "topfd" / "ms2_json" / "spectrum66.js"

    _write_js_assignment(
        prsm_file,
        "prsm_data",
        """
{
  "prsm": {
    "prsm_id": "7",
    "ms": {
      "ms_header": {
        "ids": "66",
        "scans": "127",
        "precursor_mono_mass": "5990.0699",
        "precursor_charge": "9",
        "precursor_mz": "666.5706"
      },
      "peaks": {
        "peak": [
          {
            "spec_id": "66",
            "peak_id": "0",
            "monoisotopic_mass": "3040.7637",
            "monoisotopic_mz": "609.1600",
            "intensity": "2377.28",
            "charge": "5",
            "matched_ions": {
              "matched_ion": {
                "ion_type": "C",
                "ion_position": "29",
                "ion_display_position": "29",
                "theoretical_mass": "3040.7707",
                "mass_error": "-0.0070",
                "ppm": "-2.29"
              }
            }
          }
        ]
      }
    },
    "annotated_protein": {
      "sequence_name": "sp|P0TEST|TEST_PROTEIN",
      "sequence_description": "test protein",
      "annotation": {
        "annotated_seq": "[Acetyl]-ACDEFG",
        "first_residue_position": "1",
        "last_residue_position": "6",
        "protein_length": "100",
        "residue": [
          { "position": "1", "acid": "A" },
          { "position": "2", "acid": "C" },
          { "position": "3", "acid": "D" },
          { "position": "4", "acid": "E" },
          { "position": "5", "acid": "F" },
          { "position": "6", "acid": "G" }
        ],
        "cleavage": [
          { "position": "3", "matched_peaks": { "matched_peak": { "peak_id": "0" } } }
        ],
        "ptm": {
          "ptm_type": "Protein variable",
          "ptm": {
            "abbreviation": "Acetyl",
            "unimod": "1",
            "mono_mass": "42.0105650000"
          },
          "occurence": {
            "left_pos": "1",
            "right_pos": "1",
            "anno": "A"
          }
        },
        "mass_shift": {
          "id": "0",
          "left_position": "5",
          "right_position": "6",
          "shift": "126.7786802558",
          "anno": "+126.7787",
          "shift_type": "unexpected"
        }
      }
    }
  }
}
""",
    )

    _write_js_assignment(
        spectrum_file,
        "ms2_data",
        """
{
  "id": 66,
  "scan": 127,
  "retention_time": 294.7,
  "target_mz": 667.24,
  "min_mz": 666.94,
  "max_mz": 667.54,
  "n_ion_type": "C",
  "c_ion_type": "Z_DOT",
  "peaks": [
    { "mz": "204.5197", "intensity": "34.2" },
    { "mz": "207.4945", "intensity": "28.8" }
  ],
  "envelopes": [
    { "id": 0, "mono_mass": 5282.03, "charge": 7, "env_peaks": [{ "mz": 755.58, "intensity": 606.6 }] }
  ]
}
""",
    )

    result = build_topmsv_prsm_payload(html_root=html_root, prsm_id=7)

    assert result["prsm_id"] == 7
    assert result["protein_accession"] == "sp|P0TEST|TEST_PROTEIN"
    assert result["sequence"]["value"] == "ACDEFG"
    assert result["sequence"]["breakpoints"] == [2]
    assert len(result["sequence"]["modifications"]) == 2

    assert result["ms2"]["selected_spectrum_id"] == 66
    assert result["ms2"]["raw_peak_count"] == 2
    assert len(result["ms2"]["matched_peaks"]) == 1
    assert result["ms2"]["matched_peaks"][0]["matched_ion_labels"] == "C29"


def test_build_topmsv_prsm_payload_raises_when_prsm_js_missing(tmp_path: Path) -> None:
    html_root = tmp_path / "sample_html"
    html_root.mkdir(parents=True)

    with pytest.raises(FileNotFoundError):
        build_topmsv_prsm_payload(html_root=html_root, prsm_id=999)
