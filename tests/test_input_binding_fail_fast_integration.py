from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest

from app.services.workflow_service import WorkflowService


class _StaticToolRegistry:
    def __init__(self, tools: dict):
        self._tools = tools

    def list_tools(self) -> dict:
        return self._tools


class _RecordingExecutionStore:
    def __init__(self) -> None:
        self.status_updates: list[dict] = []
        self.command_traces: dict[tuple[str, str], dict] = {}

    def update_node_status(
        self,
        execution_id: str,
        node_id: str,
        status: str,
        progress: int | None = None,
        error_message: str | None = None,
    ) -> None:
        self.status_updates.append(
            {
                "execution_id": execution_id,
                "node_id": node_id,
                "status": status,
                "progress": progress,
                "error_message": error_message,
            }
        )

    def update_node_command_trace(self, execution_id: str, node_id: str, command_trace: dict) -> None:
        self.command_traces[(execution_id, node_id)] = command_trace


@pytest.mark.asyncio
async def test_workflow_fails_before_executor_when_required_input_missing():
    tools = {
        "target_tool": {
            "id": "target_tool",
            "executionMode": "script",
            "command": {"interpreter": "python", "executable": "tests/fixtures/tools/mock_echo_argv_tool.py"},
            "ports": {
                "inputs": [
                    {
                        "id": "required_raw",
                        "dataType": "raw",
                        "accept": ["raw"],
                        "required": True,
                    }
                ],
                "outputs": [{"id": "out", "handle": "out", "dataType": "txt", "pattern": "{sample}.txt"}],
            },
            "parameters": {},
            "output": {"flagSupported": False},
        }
    }

    workflow = {
        "metadata": {"id": "wf_fail_fast_missing_required"},
        "format_version": "2.0",
        "nodes": [{"id": "target_1", "data": {"type": "target_tool", "params": {}}}],
        "edges": [],
    }

    mock_executor = Mock()
    mock_executor.execute = AsyncMock()
    recording_store = _RecordingExecutionStore()

    service = WorkflowService(
        tool_registry=_StaticToolRegistry(tools),
        executor=mock_executor,
        execution_store=recording_store,
    )
    result = await service.execute_workflow(
        workflow_json=workflow,
        workspace_path=".",
        parameters={"sample_context": {"sample": "demo"}},
        execution_id="exec_fail_fast_missing",
    )

    assert result["status"] == "failed"
    assert "Missing required input binding for port 'required_raw'" in (result.get("error") or "")
    assert mock_executor.execute.await_count == 0

    key = ("exec_fail_fast_missing", "target_1")
    assert key in recording_store.command_traces
    trace = recording_store.command_traces[key]
    assert trace["input_binding"]["status"] == "failed"
    assert trace["input_binding"]["error"]["code"] == "INPUT_BINDING_CONTRACT_VIOLATION"

    error_updates = [item for item in recording_store.status_updates if item["error_message"]]
    assert error_updates, "Expected an explicit failed node status with error_message"
