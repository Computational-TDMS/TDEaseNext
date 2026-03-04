"""
工作流执行端到端测试 - 通过 API 真实调用后端，执行 Data Loader -> A -> B -> C 链式工作流

调用路径：
  TestClient.post("/api/workflows/execute", ...)
    -> FastAPI 路由 POST /api/workflows/execute
    -> workflow_service.execute_workflow()
    -> FlowEngine + LocalExecutor + ShellRunner
    -> 实际执行 shell 命令（python tool_a.py ... 等）

即：直接通过 HTTP API 调用后端，后端完整执行工作流（非 simulate/dryrun）。

依赖：
- config/tools/tool_a.json, tool_b.json, tool_c.json
- tests/fixtures/tools/tool_a.py, tool_b.py, tool_c.py
- tests/fixtures/workflow_abc.json
- tests/fixtures/dummy.raw

运行：
  uv run python tests/test_workflow_execution.py
  或
  uv run pytest tests/test_workflow_execution.py -v
"""
import json
from pathlib import Path

try:
    import pytest
except ImportError:
    pytest = None

# 工作流 fixture 路径
FIXTURE_DIR = (Path(__file__).parent / "fixtures").resolve()
WORKFLOW_ABC = FIXTURE_DIR / "workflow_abc.json"
DUMMY_RAW = FIXTURE_DIR / "dummy.raw"


def _load_workflow() -> dict:
    with open(WORKFLOW_ABC, "r", encoding="utf-8") as f:
        wf = json.load(f)
    # 注入 fixture 路径，满足 validator 的路径检查
    for node in wf.get("nodes", []):
        data = node.get("data") or {}
        params = data.get("params") or {}
        if "input_sources" in params:
            srcs = params["input_sources"]
            if isinstance(srcs, list):
                params["input_sources"] = [
                    str(DUMMY_RAW) if (isinstance(p, str) and p == "__FIXTURE_PATH__") else p
                    for p in srcs
                ]
        node["data"] = {**data, "params": params}
    return wf


def test_workflow_abc_execution_real():
    """
    通过 API 真实执行 A -> B -> C 工作流（不 simulate、不 dryrun）。
    调用：POST /api/workflows/execute -> 后端完整执行。

    验证：
    - 执行完成 (status=completed)
    - 输出文件 dummy_a.txt, dummy_b.txt, dummy_c.txt 存在
    - A 输出包含 TOOL_A_SIGNATURE
    - B 输出包含 TOOL_A_SIGNATURE 与 TOOL_B_SIGNATURE（证明 B 读到 A）
    - C 输出包含 TOOL_B_SIGNATURE（证明 C 读到 B）
    """
    from fastapi.testclient import TestClient
    from app.main import app
    from app.services.paths import get_workflows_root

    workflow = _load_workflow()
    # sample 来自 data_loader 的 input 文件 stem (dummy.raw -> dummy)
    sample = "dummy"

    client = TestClient(app)
    resp = client.post(
        "/api/workflows/execute",
        json={
            "workflow": workflow,
            "parameters": {
                "sample": sample,
                "sample_context": {"sample": sample},
                "dryrun": False,
                "simulate": False,
                "resume": False,
            },
        },
    )

    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert "executionId" in data
    execution_id = data["executionId"]
    status = data.get("status")
    if status == "running":
        # Poll until completed
        import time
        deadline = time.time() + 30
        while time.time() < deadline:
            resp2 = client.get(f"/api/executions/{execution_id}")
            assert resp2.status_code == 200, f"Expected 200, got {resp2.status_code}: {resp2.text}"
            status = resp2.json().get("status")
            if status in ("completed", "failed"):
                break
            time.sleep(0.5)
    assert status in ("completed", "dryrun"), f"Expected completed, got {status}"

    workspace = Path(get_workflows_root()) / "wf_abc_test"
    assert workspace.exists(), f"Workspace not found: {workspace}"

    out_a = workspace / f"{sample}_a.txt"
    out_b = workspace / f"{sample}_b.txt"
    out_c = workspace / f"{sample}_c.txt"

    assert out_a.exists(), f"Tool A output not found: {out_a}"
    assert out_b.exists(), f"Tool B output not found: {out_b}"
    assert out_c.exists(), f"Tool C output not found: {out_c}"

    content_a = out_a.read_text(encoding="utf-8")
    content_b = out_b.read_text(encoding="utf-8")
    content_c = out_c.read_text(encoding="utf-8")

    # 内容验证：签名链确保上游输出被下游真正读取
    assert "TOOL_A_SIGNATURE=" in content_a, "A must output TOOL_A_SIGNATURE"
    assert "TOOL_A_SIGNATURE=" in content_b, "B must contain A's output (read verified)"
    assert "TOOL_B_SIGNATURE=" in content_b, "B must output TOOL_B_SIGNATURE"
    assert "TOOL_B_SIGNATURE=" in content_c, "C must contain B's output (read verified)"

    print(f"[OK] Workflow executed: executionId={data['executionId']}, status={data['status']}")
    print(f"     Outputs: {out_a.name}, {out_b.name}, {out_c.name}")

    # 清理：可选，避免堆积
    # import shutil
    # if workspace.exists():
    #     shutil.rmtree(workspace, ignore_errors=True)


def run_manual():
    """手动运行测试（便于调试）"""
    print("=== Workflow ABC Execution Test ===\n")
    test_workflow_abc_execution_real()
    print("\n=== Test passed ===")


if __name__ == "__main__":
    run_manual()
