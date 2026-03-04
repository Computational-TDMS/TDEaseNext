import pytest
import sqlite3

from app.database.init_db import initialize_database
from app.services.execution_store import ExecutionStore
from app.api import execution as execution_api


class _DummyExecution:
    def __init__(self, execution_id: str):
        self.id = execution_id
        self.status = "running"
        self.start_time = "2026-03-04T00:00:00Z"
        self.end_time = None
        self.progress = 10
        self.logs = []


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


@pytest.mark.asyncio
async def test_get_execution_status_returns_parsed_command_trace(tmp_path, monkeypatch):
    db_path = tmp_path / "api_trace_test.db"
    assert initialize_database(str(db_path))

    store = ExecutionStore(db_path=str(db_path))
    execution_id = "exec_api_trace_1"
    node_id = "pbfgen_1"
    workflow_id = "wf1"
    workspace_path = str(tmp_path / "ws")
    _insert_workflow(str(db_path), workflow_id, workspace_path)
    store.create(execution_id, workflow_id, workspace_path=workspace_path)
    store.create_node(execution_id, node_id, "node_pbfgen_1")
    store.update_node_command_trace(
        execution_id,
        node_id,
        {
            "node_id": node_id,
            "tool_id": "pbfgen",
            "cmd_parts": ["python.exe", "mock_pbfgen.py", "-i", "demo.raw"],
        },
    )

    monkeypatch.setattr(execution_api, "execution_store", store)
    monkeypatch.setattr(execution_api.execution_manager, "get", lambda _eid: _DummyExecution(_eid))

    resp = await execution_api.get_execution_status(execution_id)
    assert resp.executionId == execution_id
    assert resp.nodes
    assert resp.nodes[0].node_id == node_id
    assert isinstance(resp.nodes[0].command_trace, dict)
    assert resp.nodes[0].command_trace["tool_id"] == "pbfgen"


@pytest.mark.asyncio
async def test_get_execution_node_trace_endpoint_payload(tmp_path, monkeypatch):
    db_path = tmp_path / "api_trace_node_test.db"
    assert initialize_database(str(db_path))

    store = ExecutionStore(db_path=str(db_path))
    execution_id = "exec_api_trace_2"
    node_id = "toppic_1"
    workflow_id = "wf2"
    workspace_path = str(tmp_path / "ws2")
    _insert_workflow(str(db_path), workflow_id, workspace_path)
    store.create(execution_id, workflow_id, workspace_path=workspace_path)
    store.create_node(execution_id, node_id, "node_toppic_1")
    store.update_node_command_trace(
        execution_id,
        node_id,
        {
            "node_id": node_id,
            "tool_id": "toppic",
            "cmd_parts": ["toppic.exe", "db.fasta", "input.msalign"],
        },
    )

    monkeypatch.setattr(execution_api, "execution_store", store)
    monkeypatch.setattr(execution_api.execution_manager, "get", lambda _eid: _DummyExecution(_eid))

    payload = await execution_api.get_execution_node_trace(execution_id, node_id)
    assert payload["execution_id"] == execution_id
    assert payload["node_id"] == node_id
    assert payload["command_trace"]["tool_id"] == "toppic"
