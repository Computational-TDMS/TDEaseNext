"""
Test fixtures for database and common test data
"""
import sqlite3
import tempfile
from pathlib import Path
import pytest
import json


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    db_path = tempfile.mktemp(suffix=".db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Create tables
    conn.execute("""
        CREATE TABLE executions (
            id TEXT PRIMARY KEY,
            workflow_id TEXT,
            workflow_snapshot TEXT,
            workspace_path TEXT,
            sample_id TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE samples (
            id TEXT PRIMARY KEY,
            name TEXT,
            context TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    yield conn

    conn.close()
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def sample_execution(temp_db):
    """Create a sample execution in database"""
    workflow_snapshot = {
        "nodes": [
            {
                "id": "node1",
                "type": "featuremap_viewer",
                "data": {"label": "Test Node"}
            },
            {
                "id": "node2",
                "type": "topfd",
                "data": {"label": "Compute Node"}
            }
        ],
        "edges": []
    }

    temp_db.execute(
        "INSERT INTO executions (id, workflow_id, workflow_snapshot, workspace_path, status) VALUES (?, ?, ?, ?, ?)",
        ("exec1", "workflow1", json.dumps(workflow_snapshot), "/tmp/workspace", "completed")
    )

    temp_db.execute(
        "INSERT INTO samples (id, name, context) VALUES (?, ?, ?)",
        ("sample1", "test_sample", json.dumps({"sample": "test"}))
    )

    temp_db.commit()
    return "exec1"


@pytest.fixture
def sample_workspace(tmp_path):
    """Create sample workspace with output files"""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    # Create sample output file
    output_file = workspace / "test_output.tsv"
    output_file.write_text("col1\tcol2\tcol3\nval1\tval2\tval3\nval4\tval5\tval6\n")

    return workspace
