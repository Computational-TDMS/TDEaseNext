from __future__ import annotations

import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest

from app.api import execution as execution_api
from app.database.init_db import initialize_database
from app.services.execution_store import ExecutionStore


class _DummyExecution:
    def __init__(self, execution_id: str, *, status: str = "running", progress: int = 20):
        self.id = execution_id
        self.status = status
        self.start_time = "2026-03-04T00:00:00Z"
        self.end_time = None
        self.progress = progress
        self.logs = []
        self.workspace = "data/workflows/fallback"


def _make_tmp_dir() -> Path:
    base = Path("data") / "test_tmp_dirs"
    base.mkdir(parents=True, exist_ok=True)
    path = (base / f"execution_fallback_{uuid4().hex}").resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


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
async def test_status_endpoint_reads_from_persistent_store_when_runtime_missing(monkeypatch):
    tmp_dir = _make_tmp_dir()
    db_path = tmp_dir / "fallback_status.db"
    assert initialize_database(str(db_path))

    store = ExecutionStore(db_path=str(db_path))
    execution_id = "exec_persisted_only"
    workflow_id = "wf_persisted_only"
    workspace = str(tmp_dir / "workspace")
    _insert_workflow(str(db_path), workflow_id, workspace)
    store.create(execution_id, workflow_id, workspace_path=workspace)
    store.create_node(execution_id, "node_1", "node_node_1")
    store.update_node_status(execution_id, "node_1", "completed", progress=100)
    store.finish(execution_id, "completed")

    monkeypatch.setattr(execution_api, "execution_store", store)
    monkeypatch.setattr(execution_api.execution_manager, "get", lambda _eid: None)

    resp = await execution_api.get_execution_status(execution_id)
    assert resp.executionId == execution_id
    assert resp.status == "completed"
    assert resp.nodes and resp.nodes[0].status == "completed"


@pytest.mark.asyncio
async def test_status_endpoint_prefers_persisted_terminal_state_over_runtime(monkeypatch):
    tmp_dir = _make_tmp_dir()
    db_path = tmp_dir / "fallback_terminal.db"
    assert initialize_database(str(db_path))

    store = ExecutionStore(db_path=str(db_path))
    execution_id = "exec_terminal_reconcile"
    workflow_id = "wf_terminal_reconcile"
    workspace = str(tmp_dir / "workspace2")
    _insert_workflow(str(db_path), workflow_id, workspace)
    store.create(execution_id, workflow_id, workspace_path=workspace)
    store.finish(execution_id, "failed")

    runtime = _DummyExecution(execution_id, status="running", progress=40)
    monkeypatch.setattr(execution_api, "execution_store", store)
    monkeypatch.setattr(execution_api.execution_manager, "get", lambda _eid: runtime)

    resp = await execution_api.get_execution_status(execution_id)
    assert resp.status == "failed"
    assert resp.progress == 0


@pytest.mark.asyncio
async def test_node_trace_endpoint_uses_persistent_fallback(monkeypatch):
    tmp_dir = _make_tmp_dir()
    db_path = tmp_dir / "fallback_trace.db"
    assert initialize_database(str(db_path))

    store = ExecutionStore(db_path=str(db_path))
    execution_id = "exec_trace_fallback"
    workflow_id = "wf_trace_fallback"
    workspace = str(tmp_dir / "workspace3")
    _insert_workflow(str(db_path), workflow_id, workspace)
    store.create(execution_id, workflow_id, workspace_path=workspace)
    store.create_node(execution_id, "node_1", "node_node_1")
    store.update_node_command_trace(
        execution_id,
        "node_1",
        {"node_id": "node_1", "tool_id": "demo", "cmd_parts": ["python", "demo.py"]},
    )

    monkeypatch.setattr(execution_api, "execution_store", store)
    monkeypatch.setattr(execution_api.execution_manager, "get", lambda _eid: None)

    payload = await execution_api.get_execution_node_trace(execution_id, "node_1")
    assert payload["command_trace"]["tool_id"] == "demo"
