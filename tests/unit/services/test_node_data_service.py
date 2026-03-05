"""
Unit tests for NodeDataService
"""
import pytest
from pathlib import Path
from app.services.node_data_service import parse_tabular_file, TABULAR_EXTENSIONS


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
