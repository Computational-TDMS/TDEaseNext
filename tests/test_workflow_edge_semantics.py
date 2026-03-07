from __future__ import annotations

import pytest

from app.core.engine.graph import WorkflowGraph
from app.services.workflow_service import WorkflowService
from src.workflow.normalizer import WorkflowNormalizer


class _StaticToolRegistry:
    def __init__(self, tools: dict):
        self._tools = tools

    def list_tools(self) -> dict:
        return self._tools


class _StateFailingExecutor:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def execute(self, spec) -> None:
        self.calls.append(spec.node_id)
        if spec.node_id == "state_source_1":
            raise RuntimeError("state-node-failure")

    async def cancel(self, task_id: str) -> bool:
        return False


def test_normalizer_preserves_edge_semantics_and_defaults_connection_kind():
    workflow = {
        "metadata": {"id": "wf_edge_norm"},
        "nodes": [{"id": "n1", "data": {"type": "a"}}, {"id": "n2", "data": {"type": "b"}}],
        "edges": [
            {
                "id": "e_state",
                "source": "n1",
                "target": "n2",
                "sourceHandle": "output-selection_out",
                "targetHandle": "input-selection_in",
                "connectionKind": "state",
                "semanticType": "state/selection_ids",
            },
            {
                "id": "e_legacy",
                "source": "n1",
                "target": "n2",
                "sourceHandle": "output-data",
                "targetHandle": "input-data",
            },
        ],
    }

    normalized = WorkflowNormalizer().normalize(workflow)
    by_id = {edge["id"]: edge for edge in normalized["edges"]}

    assert by_id["e_state"]["connectionKind"] == "state"
    assert by_id["e_state"]["semanticType"] == "state/selection_ids"
    assert by_id["e_legacy"]["connectionKind"] == "data"
    assert by_id["e_legacy"]["semanticType"] is None


def test_graph_excludes_state_edges_from_dependencies_but_keeps_metadata():
    nodes = [{"id": "data_src"}, {"id": "state_src"}, {"id": "target"}]
    edges = [
        {"id": "e_data", "source": "data_src", "target": "target", "connectionKind": "data"},
        {
            "id": "e_state",
            "source": "state_src",
            "target": "target",
            "connectionKind": "state",
            "semanticType": "state/selection_ids",
        },
    ]

    graph = WorkflowGraph(nodes, edges)
    target = graph.get_node("target")
    assert target is not None
    assert target.predecessors == {"data_src"}

    metadata = {edge["id"]: edge for edge in graph.edges()}
    assert metadata["e_data"]["dependency"] is True
    assert metadata["e_state"]["dependency"] is False
    assert metadata["e_state"]["semanticType"] == "state/selection_ids"


@pytest.mark.asyncio
async def test_state_edge_failure_does_not_block_data_dependency_execution():
    tools = {
        "data_source": {
            "id": "data_source",
            "executionMode": "script",
            "command": {"interpreter": "python", "executable": "tests/fixtures/tools/mock_source_tool.py"},
            "ports": {
                "inputs": [],
                "outputs": [{"id": "output", "handle": "output", "dataType": "raw", "pattern": "{sample}.raw"}],
            },
            "parameters": {},
            "output": {"flagSupported": False},
        },
        "state_source": {
            "id": "state_source",
            "executionMode": "script",
            "command": {"interpreter": "python", "executable": "tests/fixtures/tools/mock_source_tool.py"},
            "ports": {
                "inputs": [],
                "outputs": [{"id": "selection", "handle": "selection", "dataType": "state", "pattern": "selection.json"}],
            },
            "parameters": {},
            "output": {"flagSupported": False},
        },
        "consumer": {
            "id": "consumer",
            "executionMode": "script",
            "command": {"interpreter": "python", "executable": "tests/fixtures/tools/mock_echo_argv_tool.py"},
            "ports": {
                "inputs": [{"id": "input_file", "dataType": "raw", "accept": ["raw"], "required": True}],
                "outputs": [{"id": "output", "handle": "output", "dataType": "txt", "pattern": "{sample}.txt"}],
            },
            "parameters": {},
            "output": {"flagSupported": False},
        },
    }

    workflow = {
        "metadata": {"id": "wf_state_edge_execution"},
        "format_version": "2.0",
        "nodes": [
            {"id": "data_source_1", "data": {"type": "data_source", "params": {}}},
            {"id": "state_source_1", "data": {"type": "state_source", "params": {}}},
            {"id": "consumer_1", "data": {"type": "consumer", "params": {}}},
        ],
        "edges": [
            {
                "id": "e_data",
                "source": "data_source_1",
                "target": "consumer_1",
                "sourceHandle": "output-raw",
                "targetHandle": "input-input_file",
                "connectionKind": "data",
            },
            {
                "id": "e_state",
                "source": "state_source_1",
                "target": "consumer_1",
                "sourceHandle": "output-selection",
                "targetHandle": "input-selection_in",
                "connectionKind": "state",
                "semanticType": "state/selection_ids",
            },
        ],
    }

    executor = _StateFailingExecutor()
    service = WorkflowService(tool_registry=_StaticToolRegistry(tools), executor=executor)
    result = await service.execute_workflow(
        workflow_json=workflow,
        workspace_path=".",
        parameters={"sample_context": {"sample": "demo"}},
        execution_id="exec_state_edge_behavior",
    )

    assert result["status"] == "failed"
    assert result["nodes"]["state_source_1"] == "failed"
    assert result["nodes"]["consumer_1"] == "completed"
    assert "consumer_1" in executor.calls

    edge_meta = {edge["id"]: edge for edge in result.get("edge_metadata", [])}
    assert edge_meta["e_data"]["dependency"] is True
    assert edge_meta["e_state"]["dependency"] is False
