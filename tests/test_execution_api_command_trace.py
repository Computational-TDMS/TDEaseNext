import pytest
import sqlite3
from pathlib import Path
from uuid import uuid4

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


def _make_tmp_dir() -> Path:
    base = Path("data") / "test_tmp_dirs"
    base.mkdir(parents=True, exist_ok=True)
    path = (base / f"execution_api_{uuid4().hex}").resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.mark.asyncio
async def test_get_execution_status_returns_parsed_command_trace(monkeypatch):
    tmp_dir = _make_tmp_dir()
    db_path = tmp_dir / "api_trace_test.db"
    assert initialize_database(str(db_path))

    store = ExecutionStore(db_path=str(db_path))
    execution_id = "exec_api_trace_1"
    node_id = "pbfgen_1"
    workflow_id = "wf1"
    workspace_path = str(tmp_dir / "ws")
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
async def test_get_execution_node_trace_endpoint_payload(monkeypatch):
    tmp_dir = _make_tmp_dir()
    db_path = tmp_dir / "api_trace_node_test.db"
    assert initialize_database(str(db_path))

    store = ExecutionStore(db_path=str(db_path))
    execution_id = "exec_api_trace_2"
    node_id = "toppic_1"
    workflow_id = "wf2"
    workspace_path = str(tmp_dir / "ws2")
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


@pytest.mark.asyncio
async def test_get_execution_status_exposes_contract_validation_failure(monkeypatch):
    tmp_dir = _make_tmp_dir()
    db_path = tmp_dir / "api_binding_fail_test.db"
    assert initialize_database(str(db_path))

    store = ExecutionStore(db_path=str(db_path))
    execution_id = "exec_api_binding_fail"
    node_id = "target_1"
    workflow_id = "wf_binding_fail"
    workspace_path = str(tmp_dir / "ws3")
    _insert_workflow(str(db_path), workflow_id, workspace_path)
    store.create(execution_id, workflow_id, workspace_path=workspace_path)
    store.create_node(execution_id, node_id, "node_target_1")
    store.update_node_status(
        execution_id,
        node_id,
        "failed",
        progress=0,
        error_message="Missing required input binding for port 'required_raw'",
    )
    store.update_node_command_trace(
        execution_id,
        node_id,
        {
            "node_id": node_id,
            "tool_id": "target_tool",
            "input_binding": {
                "status": "failed",
                "error": {
                    "code": "INPUT_BINDING_CONTRACT_VIOLATION",
                    "violations": [
                        {"code": "MISSING_REQUIRED_INPUT", "port_id": "required_raw"}
                    ],
                },
            },
        },
    )

    failed_execution = _DummyExecution(execution_id)
    failed_execution.status = "failed"
    failed_execution.progress = 0
    monkeypatch.setattr(execution_api, "execution_store", store)
    monkeypatch.setattr(execution_api.execution_manager, "get", lambda _eid: failed_execution)

    resp = await execution_api.get_execution_status(execution_id)
    assert resp.status == "failed"
    assert resp.nodes
    node = resp.nodes[0]
    assert node.error_message == "Missing required input binding for port 'required_raw'"
    assert node.command_trace["input_binding"]["error"]["code"] == "INPUT_BINDING_CONTRACT_VIOLATION"
