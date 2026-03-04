import json
import sqlite3

from app.database.init_db import initialize_database
from app.services.execution_store import ExecutionStore


def _insert_workflow(db_path: str, workflow_id: str, workspace_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO workflows
            (id, user_id, workspace_id, name, description, vueflow_data, workspace_path, status, created_at, updated_at, metadata, workflow_format)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                workflow_id,
                "default_user",
                "default_workspace",
                f"wf_{workflow_id}",
                "",
                "{}",
                workspace_path,
                "created",
                "2026-03-04T00:00:00Z",
                "2026-03-04T00:00:00Z",
                "{}",
                "vueflow",
            ),
        )
        conn.commit()
    finally:
        conn.close()


def test_execution_store_persists_node_command_trace(tmp_path):
    db_path = tmp_path / "trace_test.db"
    assert initialize_database(str(db_path))

    store = ExecutionStore(db_path=str(db_path))
    execution_id = "exec_trace_1"
    workflow_id = "wf_trace"
    workspace = str(tmp_path / "workspace")
    node_id = "pbfgen_1"

    _insert_workflow(str(db_path), workflow_id, workspace)
    store.create(execution_id, workflow_id, workspace_path=workspace)
    store.create_node(execution_id, node_id, "node_pbfgen_1")

    trace_payload = {
        "node_id": node_id,
        "tool_id": "pbfgen",
        "cmd_parts": ["python.exe", "mock_pbfgen.py", "-i", "demo.raw"],
        "input_flags": ["-i", "demo.raw"],
        "positional_args": [],
    }
    store.update_node_command_trace(execution_id, node_id, trace_payload)

    node = store.get_node(execution_id, node_id)
    assert node is not None
    assert node.get("command_trace")
    restored = json.loads(node["command_trace"])
    assert restored["node_id"] == node_id
    assert restored["tool_id"] == "pbfgen"
    assert "-i" in restored["cmd_parts"]
