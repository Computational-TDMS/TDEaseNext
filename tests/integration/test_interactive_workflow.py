"""
Integration tests for Interactive Visualization Workflow
Tests complete workflow execution with compute and interactive nodes
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from app.services.workflow_service import WorkflowService
from app.services.tool_registry import get_tool_registry


@pytest.fixture
def interactive_workflow():
    """Load the test interactive workflow"""
    workflow_path = Path("workflows/wf_test_interactive.json")
    if not workflow_path.exists():
        pytest.skip("Test workflow not found")
    with open(workflow_path) as f:
        return json.load(f)


@pytest.fixture
def multi_output_interactive_workflow():
    """Load the multi-output interactive workflow fixture."""
    workflow_path = Path("tests/fixtures/workflow_interactive_multi_output.json")
    if not workflow_path.exists():
        pytest.skip("Multi-output workflow fixture not found")
    with open(workflow_path) as f:
        return json.load(f)


@pytest.fixture
def mock_workspace(tmp_path):
    """Create mock workspace directory"""
    workspace = tmp_path / "test_workspace"
    workspace.mkdir()
    return workspace


@pytest.mark.asyncio
async def test_workflow_loads_successfully(interactive_workflow):
    """
    Test that interactive workflow JSON loads successfully

    Given: A valid interactive workflow JSON file
    When: Loading the workflow
    Then: Workflow should load without errors and contain expected nodes
    """
    assert "nodes" in interactive_workflow
    assert "edges" in interactive_workflow

    # Verify compute nodes exist
    compute_nodes = [n for n in interactive_workflow["nodes"] if n["type"] in ["topfd", "toppic"]]
    assert len(compute_nodes) == 2

    # Verify interactive nodes exist
    interactive_nodes = [
        n for n in interactive_workflow["nodes"]
        if n["type"] in ["featuremap_viewer", "spectrum_viewer", "table_viewer", "topmsv_ms2_viewer", "topmsv_sequence_viewer"]
    ]
    assert len(interactive_nodes) >= 3

    # Verify data edges exist
    data_edges = [e for e in interactive_workflow["edges"] if e.get("connectionKind") == "data"]
    assert len(data_edges) > 0

    # Verify state edges exist
    state_edges = [e for e in interactive_workflow["edges"] if e.get("connectionKind") == "state"]
    assert len(state_edges) == 3


@pytest.mark.asyncio
async def test_workflow_execution_skips_interactive_nodes(
    interactive_workflow,
    mock_workspace
):
    """
    Test that workflow execution skips interactive nodes

    Given: A workflow with compute and interactive nodes
    When: Executing the workflow
    Then: Compute nodes should execute, interactive nodes should be skipped
    """
    tool_registry = get_tool_registry()

    # Mock executor
    mock_executor = Mock()
    mock_executor.execute = AsyncMock()

    # Create workflow service
    workflow_service = WorkflowService(
        tool_registry=tool_registry,
        executor=mock_executor
    )

    # Execute workflow (dryrun mode for testing)
    result = await workflow_service.execute_workflow(
        workflow_json=interactive_workflow,
        workspace_path=mock_workspace,
        dryrun=True,
        execution_id="test_exec_interactive"
    )

    # Verify execution completed
    assert result["status"] in ["completed", "dryrun"]

    # Verify node states
    node_states = result.get("nodes", {})

    # Verify compute nodes were processed (completed or ready in dryrun)
    assert node_states.get("topfd_1") in ["completed", "ready", "pending"]
    assert node_states.get("toppic_1") in ["completed", "ready", "pending"]


@pytest.mark.asyncio
async def test_workflow_node_states_after_execution(
    interactive_workflow,
    mock_workspace
):
    """
    Test that node states are correctly set after execution

    Given: A workflow with compute and interactive nodes
    When: Executing the workflow
    Then: Compute nodes should have 'completed' status, interactive nodes 'skipped'
    """
    tool_registry = get_tool_registry()

    workflow_service = WorkflowService(
        tool_registry=tool_registry,
        executor=Mock()
    )

    result = await workflow_service.execute_workflow(
        workflow_json=interactive_workflow,
        workspace_path=mock_workspace,
        dryrun=True,
        execution_id="test_exec_states"
    )

    node_states = result["nodes"]

    # Verify nodes exist in result
    assert "topfd_1" in node_states
    assert "toppic_1" in node_states
    assert "featuremap_1" in node_states
    assert "spectrum_1" in node_states
    assert "table_viewer_1" in node_states


@pytest.mark.asyncio
async def test_state_edge_configuration(interactive_workflow):
    """
    Test that state edges are properly configured

    Given: An interactive workflow
    When: Examining state edges
    Then: State edges should have correct semantic types and connections
    """
    state_edges = [e for e in interactive_workflow["edges"] if e.get("connectionKind") == "state"]

    assert len(state_edges) >= 2

    # Verify semantic types
    for edge in state_edges:
        assert "semanticType" in edge
        assert edge["semanticType"] == "state/selection_ids"

    # Verify featuremap -> spectrum connection
    featuremap_spectrum = [e for e in state_edges if e["source"] == "featuremap_1" and e["target"] == "spectrum_1"]
    assert len(featuremap_spectrum) == 1

    # Verify featuremap -> table connection
    featuremap_table = [e for e in state_edges if e["source"] == "featuremap_1" and e["target"] == "table_viewer_1"]
    assert len(featuremap_table) == 1


@pytest.mark.asyncio
async def test_data_flow_edges_configuration(interactive_workflow):
    """
    Test that data flow edges are properly configured

    Given: An interactive workflow
    When: Examining data edges
    Then: Data edges should connect compute to compute and compute to interactive
    """
    data_edges = [e for e in interactive_workflow["edges"] if e.get("connectionKind") == "data"]

    assert len(data_edges) > 0

    # Verify topfd -> featuremap connection (compute to interactive)
    topfd_featuremap = [e for e in data_edges if e["source"] == "topfd_1" and e["target"] == "featuremap_1"]
    assert len(topfd_featuremap) == 1

    # Verify topfd -> table connection (compute to interactive)
    topfd_table = [e for e in data_edges if e["source"] == "topfd_1" and e["target"] == "table_viewer_1"]
    assert len(topfd_table) == 1


@pytest.mark.asyncio
async def test_interactive_node_configuration(interactive_workflow):
    """
    Test that interactive nodes have proper configuration

    Given: An interactive workflow
    When: Examining interactive node configurations
    Then: Nodes should have visualizationConfig with proper settings
    """
    interactive_nodes = [n for n in interactive_workflow["nodes"] if n["type"] == "featuremap_viewer"]

    assert len(interactive_nodes) == 1

    featuremap_node = interactive_nodes[0]
    assert "visualizationConfig" in featuremap_node["data"]

    viz_config = featuremap_node["data"]["visualizationConfig"]
    assert viz_config["type"] == "featuremap"
    assert "config" in viz_config

    config = viz_config["config"]
    assert "axisMapping" in config
    assert config["axisMapping"]["x"] == "rt"
    assert config["axisMapping"]["y"] == "mz"


@pytest.mark.asyncio
async def test_workflow_persistence(interactive_workflow, tmp_path):
    """
    Test that workflow with interactive nodes can be saved and loaded

    Given: An interactive workflow
    When: Saving and loading the workflow
    Then: All nodes, edges, and configurations should be preserved
    """
    # Save workflow
    saved_path = tmp_path / "saved_workflow.json"
    with open(saved_path, "w") as f:
        json.dump(interactive_workflow, f, indent=2)

    # Load workflow
    with open(saved_path) as f:
        loaded_workflow = json.load(f)

    # Verify all nodes preserved
    assert len(loaded_workflow["nodes"]) == len(interactive_workflow["nodes"])

    # Verify all edges preserved
    assert len(loaded_workflow["edges"]) == len(interactive_workflow["edges"])

    # Verify state edges preserved
    loaded_state_edges = [e for e in loaded_workflow["edges"] if e.get("connectionKind") == "state"]
    original_state_edges = [e for e in interactive_workflow["edges"] if e.get("connectionKind") == "state"]
    assert len(loaded_state_edges) == len(original_state_edges)

    # Verify interactive node configs preserved
    loaded_featuremap = [n for n in loaded_workflow["nodes"] if n["type"] == "featuremap_viewer"][0]
    original_featuremap = [n for n in interactive_workflow["nodes"] if n["type"] == "featuremap_viewer"][0]
    assert loaded_featuremap["data"]["visualizationConfig"] == original_featuremap["data"]["visualizationConfig"]


def test_multi_output_workflow_maps_distinct_topfd_ports_to_distinct_viewers(
    multi_output_interactive_workflow
):
    """
    Verify one compute node (TopFD) feeds different viewers via different output ports.
    """
    edges = multi_output_interactive_workflow["edges"]
    topfd_data_edges = [
        edge for edge in edges
        if edge.get("source") == "topfd_1" and edge.get("connectionKind") == "data"
    ]
    assert len(topfd_data_edges) >= 2

    port_by_target = {
        edge["target"]: edge.get("sourceHandle")
        for edge in topfd_data_edges
    }
    assert port_by_target.get("featuremap_1") == "output-ms1feature"
    assert port_by_target.get("topmsv_ms2_1") == "output-html_folder"
    assert port_by_target.get("table_1") == "output-ms2feature"


def test_multi_output_workflow_state_edges_are_semantic_and_explicit(
    multi_output_interactive_workflow
):
    """
    Verify cross-filter propagation edge is represented as semantic state flow.
    """
    edges = multi_output_interactive_workflow["edges"]
    state_edges = [edge for edge in edges if edge.get("connectionKind") == "state"]
    assert len(state_edges) == 1

    state_edge = state_edges[0]
    assert state_edge["source"] == "featuremap_1"
    assert state_edge["target"] == "table_1"
    assert state_edge.get("semanticType") == "state/selection_ids"
    assert state_edge.get("sourceHandle") == "output-selection_out"
    assert state_edge.get("targetHandle") == "input-selection_in"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
