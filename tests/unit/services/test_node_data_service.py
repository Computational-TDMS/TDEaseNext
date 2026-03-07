"""
Unit tests for NodeDataService
"""
import json
import sqlite3
import pytest
from pathlib import Path
from app.services.node_data_service import parse_tabular_file, resolve_node_outputs


class TestParseTabularFile:
    """Test suite for parse_tabular_file"""

    def test_parse_tsv_file(self, tmp_path):
        """Test parsing TSV file"""
        file_path = tmp_path / "test.tsv"
        content = "col1\tcol2\tcol3\nval1\tval2\tval3\nval4\tval5\tval6\n"
        file_path.write_text(content, encoding='utf-8')

        result = parse_tabular_file(file_path)

        assert result["columns"] == ["col1", "col2", "col3"]
        assert len(result["rows"]) == 2
        assert result["total_rows"] == 2
        assert result["rows"][0] == {"col1": "val1", "col2": "val2", "col3": "val3"}
        assert result["rows"][1] == {"col1": "val4", "col2": "val5", "col3": "val6"}

    def test_parse_csv_file(self, tmp_path):
        """Test parsing CSV file"""
        file_path = tmp_path / "test.csv"
        content = "col1,col2,col3\nval1,val2,val3\nval4,val5,val6\n"
        file_path.write_text(content, encoding='utf-8')

        result = parse_tabular_file(file_path)

        assert result["columns"] == ["col1", "col2", "col3"]
        assert len(result["rows"]) == 2

    def test_parse_toppic_preamble_tsv_file(self, tmp_path):
        """TSV parser should skip TopPIC-style preamble and detect the real header."""
        file_path = tmp_path / "toppic_prsm.tsv"
        content = (
            "********************** Parameters **********************\n"
            "Protein database file:\tD:/fake/db.fasta\n"
            "Spectrum file:\tD:/fake/sample_ms2.msalign\n"
            "********************** Parameters **********************\n"
            "\n"
            "Data file name\tPrsm ID\tSpectrum ID\tScan(s)\n"
            "sample_ms2.msalign\t1\t10\t100\n"
            "sample_ms2.msalign\t2\t11\t101\n"
        )
        file_path.write_text(content, encoding="utf-8")

        result = parse_tabular_file(file_path)

        assert result["columns"] == ["Data file name", "Prsm ID", "Spectrum ID", "Scan(s)"]
        assert result["total_rows"] == 2
        assert result["rows"][0]["Prsm ID"] == "1"

    def test_parse_tsv_header_detection_failure_raises_value_error(self, tmp_path):
        """TSV with only preamble/key-value lines should fail header detection."""
        file_path = tmp_path / "invalid_tsv.tsv"
        content = (
            "********************** Parameters **********************\n"
            "Protein database file:\tD:/fake/db.fasta\n"
            "Spectrum file:\tD:/fake/sample_ms2.msalign\n"
            "********************** Parameters **********************\n"
        )
        file_path.write_text(content, encoding="utf-8")

        with pytest.raises(ValueError, match="No tabular header detected"):
            parse_tabular_file(file_path)

    def test_parse_with_max_rows(self, tmp_path):
        """Test parsing with max_rows limit"""
        file_path = tmp_path / "test.tsv"
        content = "col1\tcol2\n" + "\n".join(f"val{i}\tval{i}" for i in range(100))
        file_path.write_text(content, encoding='utf-8')

        result = parse_tabular_file(file_path, max_rows=10)

        assert len(result["rows"]) == 10  # Only 10 rows loaded
        assert result["total_rows"] == 100  # But total count is correct

    def test_parse_nonexistent_file(self, tmp_path):
        """Test error when file doesn't exist"""
        with pytest.raises(FileNotFoundError, match="File not found"):
            parse_tabular_file(tmp_path / "nonexistent.tsv")

    def test_parse_empty_file(self, tmp_path):
        """Test parsing empty file"""
        file_path = tmp_path / "empty.tsv"
        file_path.write_text("", encoding='utf-8')

        result = parse_tabular_file(file_path)

        assert result["columns"] == []
        assert result["rows"] == []
        assert result["total_rows"] == 0

    def test_parse_file_with_only_header(self, tmp_path):
        """Test parsing file with only header row"""
        file_path = tmp_path / "header_only.tsv"
        file_path.write_text("col1\tcol2\tcol3\n", encoding='utf-8')

        result = parse_tabular_file(file_path)

        assert result["columns"] == ["col1", "col2", "col3"]
        assert result["rows"] == []
        assert result["total_rows"] == 0

    def test_parse_malformed_rows(self, tmp_path):
        """Test handling rows with mismatched column count"""
        file_path = tmp_path / "malformed.tsv"
        content = "col1\tcol2\tcol3\nval1\tval2\nval4\tval5\tval6\n"
        file_path.write_text(content, encoding='utf-8')

        result = parse_tabular_file(file_path)

        # Malformed row should use index-based keys
        assert len(result["rows"]) == 2
        assert result["rows"][0] == {"col_0": "val1", "col_1": "val2"}
        assert result["rows"][1] == {"col1": "val4", "col2": "val5", "col3": "val6"}


def _build_execution_db(tmp_path: Path, workflow_snapshot: dict) -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    db.execute(
        """
        CREATE TABLE executions (
            id TEXT PRIMARY KEY,
            workflow_snapshot TEXT,
            workspace_path TEXT,
            sample_id TEXT,
            workflow_id TEXT
        )
        """
    )
    db.execute(
        """
        INSERT INTO executions (id, workflow_snapshot, workspace_path, sample_id, workflow_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("exec-1", json.dumps(workflow_snapshot), str(tmp_path), None, None),
    )
    db.commit()
    return db


def _mock_tool_registry(monkeypatch):
    registry = {
        "topfd": {
            "id": "topfd",
            "ports": {
                "outputs": [
                    {
                        "id": "ms1feature",
                        "handle": "ms1feature",
                        "dataType": "feature",
                        "pattern": "{sample}_ms1.feature",
                        "schema": [{"name": "mz", "type": "number"}],
                    },
                    {
                        "id": "ms2feature",
                        "handle": "ms2feature",
                        "dataType": "feature",
                        "pattern": "{sample}_ms2.feature",
                        "schema": [{"name": "scan", "type": "number"}],
                    },
                ]
            },
        }
    }

    monkeypatch.setattr(
        "app.services.tool_registry.get_tool_registry",
        lambda: registry,
    )


def test_resolve_node_outputs_filters_requested_port_and_keeps_requested_port_id(tmp_path, monkeypatch):
    _mock_tool_registry(monkeypatch)

    ms1_file = tmp_path / "default_ms1.feature"
    ms2_file = tmp_path / "default_ms2.feature"
    ms1_file.write_text("mz\tintensity\n100.1\t1200\n", encoding="utf-8")
    ms2_file.write_text("scan\tcharge\n5\t2\n", encoding="utf-8")

    workflow_snapshot = {
        "nodes": [
            {"id": "topfd_node", "type": "topfd"},
        ]
    }
    db = _build_execution_db(tmp_path, workflow_snapshot)

    result = resolve_node_outputs(
        execution_id="exec-1",
        node_id="topfd_node",
        db=db,
        port_id="ms1feature",
        include_data=True,
    )

    assert result["port_id"] == "ms1feature"
    assert len(result["outputs"]) == 1
    assert result["outputs"][0]["port_id"] == "ms1feature"
    assert result["outputs"][0]["schema"] == [{"name": "mz", "type": "number"}]
    assert result["outputs"][0]["data"] is not None


def test_resolve_node_outputs_includes_schema_for_each_output_port(tmp_path, monkeypatch):
    _mock_tool_registry(monkeypatch)

    (tmp_path / "default_ms1.feature").write_text("mz\tintensity\n100.1\t1200\n", encoding="utf-8")
    (tmp_path / "default_ms2.feature").write_text("scan\tcharge\n5\t2\n", encoding="utf-8")

    workflow_snapshot = {
        "nodes": [
            {"id": "topfd_node", "type": "topfd"},
        ]
    }
    db = _build_execution_db(tmp_path, workflow_snapshot)

    result = resolve_node_outputs(
        execution_id="exec-1",
        node_id="topfd_node",
        db=db,
        include_data=False,
    )

    outputs_by_port = {output["port_id"]: output for output in result["outputs"]}
    assert result["port_id"] is None
    assert "ms1feature" in outputs_by_port
    assert "ms2feature" in outputs_by_port
    assert outputs_by_port["ms1feature"]["schema"] == [{"name": "mz", "type": "number"}]
    assert outputs_by_port["ms2feature"]["schema"] == [{"name": "scan", "type": "number"}]


def test_resolve_node_outputs_marks_tsv_without_detectable_header_as_not_parseable(tmp_path, monkeypatch):
    registry = {
        "broken_tsv_tool": {
            "id": "broken_tsv_tool",
            "ports": {
                "outputs": [
                    {
                        "id": "broken",
                        "handle": "broken",
                        "dataType": "tsv",
                        "pattern": "{sample}_broken.tsv",
                    }
                ]
            },
        }
    }
    monkeypatch.setattr(
        "app.services.tool_registry.get_tool_registry",
        lambda: registry,
    )

    (tmp_path / "default_broken.tsv").write_text(
        "Protein database file:\tD:/fake/db.fasta\n"
        "Spectrum file:\tD:/fake/sample_ms2.msalign\n",
        encoding="utf-8",
    )

    workflow_snapshot = {"nodes": [{"id": "broken_node", "type": "broken_tsv_tool"}]}
    db = _build_execution_db(tmp_path, workflow_snapshot)

    result = resolve_node_outputs(
        execution_id="exec-1",
        node_id="broken_node",
        db=db,
        include_data=False,
    )

    assert len(result["outputs"]) == 1
    assert result["outputs"][0]["parseable"] is False


def test_resolve_node_outputs_rejects_node_not_in_execution_for_empty_snapshot(monkeypatch):
    registry = {
        "table_viewer": {
            "id": "table_viewer",
            "ports": {
                "outputs": [
                    {
                        "id": "output",
                        "handle": "output",
                        "dataType": "tsv",
                        "pattern": "table.tsv",
                    }
                ]
            },
        }
    }
    monkeypatch.setattr("app.services.tool_registry.get_tool_registry", lambda: registry)

    db = sqlite3.connect(":memory:")
    db.execute(
        """
        CREATE TABLE executions (
            id TEXT PRIMARY KEY,
            workflow_snapshot TEXT,
            workspace_path TEXT,
            sample_id TEXT,
            workflow_id TEXT
        )
        """
    )
    db.execute(
        """
        CREATE TABLE execution_nodes (
            id TEXT PRIMARY KEY,
            execution_id TEXT,
            node_id TEXT
        )
        """
    )
    db.execute(
        """
        CREATE TABLE workflows (
            id TEXT PRIMARY KEY,
            vueflow_data TEXT
        )
        """
    )
    db.execute(
        """
        INSERT INTO executions (id, workflow_snapshot, workspace_path, sample_id, workflow_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("exec-legacy", None, str(Path.cwd()), None, "wf-test"),
    )
    db.execute(
        """
        INSERT INTO workflows (id, vueflow_data)
        VALUES (?, ?)
        """,
        (
            "wf-test",
            json.dumps(
                {
                    "nodes": [
                        {"id": "some_other_node", "type": "table_viewer"},
                    ]
                }
            ),
        ),
    )
    db.commit()

    with pytest.raises(ValueError, match="older workflow revision"):
        resolve_node_outputs(
            execution_id="exec-legacy",
            node_id="prsm_bundle_builder_1",
            db=db,
            include_data=False,
        )
