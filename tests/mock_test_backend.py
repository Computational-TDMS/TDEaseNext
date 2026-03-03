"""
Mock 测试 - 从 API 到 workspace 的端到端模拟测试

覆盖：API 请求、workspace 创建、dryrun、simulate（模拟运行）
"""
import json
from pathlib import Path

# 使用项目内的 fixture 路径，避免 validator 的路径检查失败
_FIXTURE_DIR = (Path(__file__).parent / "fixtures").resolve()
_RAW_PATH = str(_FIXTURE_DIR / "dummy.raw")

# 最小工作流：两个节点 data_loader -> msconvert
SAMPLE_WORKFLOW = {
    "metadata": {"id": "wf_mock_test", "name": "Mock Test Workflow"},
    "format_version": "2.0",
    "nodes": [
        {
            "id": "node_a",
            "type": "tool",
            "position": {"x": 0, "y": 0},
            "data": {"label": "Loader", "type": "data_loader", "params": {"input_sources": [_RAW_PATH]}},
        },
        {
            "id": "node_b",
            "type": "tool",
            "position": {"x": 200, "y": 0},
            "data": {"label": "MSConvert", "type": "msconvert_docker", "params": {"format": "mzML"}},
        },
    ],
    "edges": [
        {"id": "e1", "source": "node_a", "target": "node_b", "sourceHandle": "output-output", "targetHandle": "input-input_files"},
    ],
    "projectSettings": {},
}


def test_dryrun():
    """Dryrun 模式：仅遍历 DAG，不执行"""
    from app.core.engine import FlowEngine
    from app.core.engine.context import ExecutionContext

    ctx = ExecutionContext(workspace_path=Path(__file__).parent / "tmp_dryrun", dryrun=True)
    engine = FlowEngine(SAMPLE_WORKFLOW, ctx)
    import asyncio
    result = asyncio.run(engine.run())
    assert result["status"] == "dryrun"
    assert "nodes" in result
    print("[OK] dryrun: status=", result["status"], "nodes=", result["nodes"])


def test_simulate():
    """Simulate 模式：记录任务但不实际执行"""
    from app.services.workflow_service import WorkflowService
    from app.services.tool_registry import get_tool_registry
    from app.services.execution_store import ExecutionStore

    ws = Path(__file__).parent / "tmp_simulate"
    ws.mkdir(parents=True, exist_ok=True)
    try:
        reg = get_tool_registry()
        store = ExecutionStore()
        svc = WorkflowService(tool_registry=reg, execution_store=store)
        import asyncio
        result = asyncio.run(svc.execute_workflow(
            SAMPLE_WORKFLOW, ws, parameters={"sample_context": {"sample": "dummy"}},
            dryrun=False, simulate=True,
        ))
        assert result["status"] == "completed"
        assert "simulated_tasks" in result
        tasks = result["simulated_tasks"]
        assert len(tasks) == 2  # node_a, node_b
        print("[OK] simulate: tasks=", len(tasks), [t["node_id"] for t in tasks])
    finally:
        import shutil
        if ws.exists():
            shutil.rmtree(ws, ignore_errors=True)


def test_api_execute_dryrun():
    """API: POST /api/workflows/execute with dryrun=true"""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    resp = client.post("/api/workflows/execute", json={
        "workflow": SAMPLE_WORKFLOW,
        "parameters": {"dryrun": True, "sample": "dummy", "sample_context": {"sample": "dummy"}},
    })
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert "executionId" in data
    assert data["status"] in ("completed", "dryrun")
    print("[OK] API dryrun: executionId=", data["executionId"], "status=", data["status"])


def test_api_execute_simulate():
    """API: POST /api/workflows/execute with simulate=true"""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    resp = client.post("/api/workflows/execute", json={
        "workflow": SAMPLE_WORKFLOW,
        "parameters": {"simulate": True, "sample": "dummy", "sample_context": {"sample": "dummy"}},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "executionId" in data
    assert data["status"] == "completed"
    print("[OK] API simulate: executionId=", data["executionId"], "nodes=", data.get("nodes"))


def test_workspace_creation():
    """验证 execute 会创建 workspace 目录"""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.services.paths import get_workflows_root

    client = TestClient(app)
    resp = client.post("/api/workflows/execute", json={
        "workflow": SAMPLE_WORKFLOW,
        "parameters": {"simulate": True, "sample": "dummy", "sample_context": {"sample": "dummy"}},
    })
    assert resp.status_code == 200
    data = resp.json()
    root = Path(get_workflows_root())
    # workflow_id 来自 metadata.id
    wf_id = "wf_mock_test"
    ws_dir = root / wf_id
    assert ws_dir.exists()
    assert (ws_dir / "logs").exists()
    assert (ws_dir / "results").exists()
    print("[OK] workspace created:", ws_dir)


def run_all():
    print("=== Mock Backend Tests ===\n")
    test_dryrun()
    test_simulate()
    test_api_execute_dryrun()
    test_api_execute_simulate()
    test_workspace_creation()
    print("\n=== All tests passed ===")


if __name__ == "__main__":
    run_all()
