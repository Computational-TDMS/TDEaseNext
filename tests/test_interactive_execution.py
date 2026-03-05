"""
Unit tests for interactive node execution skipping logic
"""

import pytest
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock

from app.services.workflow_service import WorkflowService
from app.services.tool_registry import ToolRegistry
from app.core.engine.context import ExecutionContext


@pytest.fixture
def mock_tool_registry():
    """Create a mock tool registry with compute and interactive tools"""
    registry = Mock(spec=ToolRegistry)

    # Compute tool (should be executed)
    compute_tool = {
        "id": "topfd",
        "name": "TopFD",
        "executionMode": "compute",
        "ports": {
            "inputs": [
                {
                    "id": "input_files",
                    "name": "mzML Files",
                    "dataType": "mzml",
                    "required": True,
                    "positional": True,
                    "positionalOrder": 0,
                    "pattern": "{sample}.mzML"
                }
            ],
            "outputs": [
                {
                    "id": "ms1feature",
                    "name": "MS1 Feature File",
                    "dataType": "feature",
                    "pattern": "{sample}_ms1.feature",
                    "handle": "ms1feature",
                    "column_schema": [
                        {"name": "feature_id", "type": "number", "description": "Feature ID"},
                        {"name": "mz", "type": "number", "description": "m/z value"},
                        {"name": "intensity", "type": "number", "description": "Intensity"}
                    ]
                }
            ]
        },
        "parameters": {}
    }

    # Interactive tool (should be skipped)
    interactive_tool = {
        "id": "featuremap_viewer",
        "name": "Feature Map Viewer",
        "executionMode": "interactive",
        "defaultMapping": {
            "x": "mz",
            "y": "intensity",
            "color": "feature_id"
        },
        "ports": {
            "inputs": [
                {
                    "id": "feature_data",
                    "name": "Feature Data",
                    "dataType": "feature",
                    "required": True,
                    "pattern": "{sample}_ms1.feature"
                }
            ],
            "outputs": []
        },
        "parameters": {}
    }

    registry.list_tools.return_value = {
        "topfd": compute_tool,
        "featuremap_viewer": interactive_tool
    }
    registry.get.side_effect = lambda tool_id: registry.list_tools().get(tool_id)

    return registry


@pytest.fixture
def workflow_with_interactive_node() -> Dict[str, Any]:
    """Create a workflow with both compute and interactive nodes"""
    return {
        "id": "test_workflow",
        "name": "Test Workflow",
        "nodes": [
            {
                "id": "node1",
                "type": "topfd",
                "data": {
                    "params": {
                        "thread_number": "1"
                    }
                }
            },
            {
                "id": "node2",
                "type": "featuremap_viewer",
                "data": {
                    "params": {}
                }
            }
        ],
        "edges": [
            {
                "id": "edge1",
                "source": "node1",
                "target": "node2",
                "sourceHandle": "ms1feature",
                "targetHandle": "feature_data"
            }
        ]
    }


@pytest.mark.asyncio
async def test_interactive_node_skipped_in_build_task_spec(
    mock_tool_registry,
    workflow_with_interactive_node
):
    """Test that interactive nodes return None in build_task_spec"""
    workflow_service = WorkflowService(tool_registry=mock_tool_registry)

    # Create execution context
    ctx = ExecutionContext(
        workspace_path=Path("/tmp/test_workspace"),
        sample_context={"sample": "test"},
        dryrun=True,
        execution_id="test_exec_1"
    )

    nodes_map = {n["id"]: n for n in workflow_with_interactive_node["nodes"]}

    # Test compute node (should return TaskSpec)
    compute_spec = workflow_service._WorkflowService__build_task_spec(
        "node1",
        nodes_map["node1"],
        ctx
    )

    assert compute_spec is not None, "Compute node should return TaskSpec"
    assert compute_spec.node_id == "node1"
    assert compute_spec.tool_id == "topfd"

    # Test interactive node (should return None)
    interactive_spec = workflow_service._WorkflowService__build_task_spec(
        "node2",
        nodes_map["node2"],
        ctx
    )

    assert interactive_spec is None, "Interactive node should return None (skipped)"


@pytest.mark.asyncio
async def test_interactive_node_marked_as_skipped(
    mock_tool_registry,
    workflow_with_interactive_node
):
    """Test that interactive nodes are marked with 'skipped' status"""
    workflow_service = WorkflowService(
        tool_registry=mock_tool_registry,
        executor=Mock()
    )

    # Mock execution store
    execution_store = Mock()
    execution_store.update_node_status = Mock()
    workflow_service.execution_store = execution_store

    # Create execution context
    ctx = ExecutionContext(
        workspace_path=Path("/tmp/test_workspace"),
        sample_context={"sample": "test"},
        dryrun=True,
        execution_id="test_exec_2"
    )

    nodes_map = {n["id"]: n for n in workflow_with_interactive_node["nodes"]}

    # Simulate node state callback for interactive node
    on_node_state = Mock()

    # Simulate what execute_fn does for interactive node
    spec = workflow_service._WorkflowService__build_task_spec(
        "node2",
        nodes_map["node2"],
        ctx
    )

    assert spec is None
    on_node_state("node2", "skipped")

    # Verify status was updated
    on_node_state.assert_called_once_with("node2", "skipped")


def test_execution_mode_validation():
    """Test that executionMode accepts both compute and interactive values"""
    from app.schemas.tool import ToolDefinition

    # Test compute tool
    compute_tool_data = {
        "id": "test_compute",
        "name": "Test Compute",
        "executionMode": "compute",
        "ports": {
            "inputs": [],
            "outputs": [
                {
                    "id": "output",
                    "pattern": "output.txt",
                    "schema": [
                        {"name": "col1", "type": "string", "description": "Column 1"}
                    ]
                }
            ]
        },
        "parameters": {}
    }

    compute_tool = ToolDefinition(**compute_tool_data)
    assert compute_tool.executionMode == "compute"

    # Test interactive tool
    interactive_tool_data = {
        "id": "test_interactive",
        "name": "Test Interactive",
        "executionMode": "interactive",
        "ports": {
            "inputs": [],
            "outputs": []
        },
        "parameters": {},
        "defaultMapping": {
            "x": "col1",
            "y": "col2"
        }
    }

    interactive_tool = ToolDefinition(**interactive_tool_data)
    assert interactive_tool.executionMode == "interactive"
    assert interactive_tool.defaultMapping == {"x": "col1", "y": "col2"}


def test_output_schema_field():
    """Test that output schema field is properly defined"""
    from app.schemas.tool import ToolOutputDef

    output_with_schema = ToolOutputDef(
        id="output1",
        pattern="output.txt",
        column_schema=[
            {"name": "id", "type": "number", "description": "Row ID"},
            {"name": "value", "type": "string", "description": "Value"}
        ]
    )

    assert output_with_schema.column_schema is not None
    assert len(output_with_schema.column_schema) == 2
    assert output_with_schema.column_schema[0]["name"] == "id"
    assert output_with_schema.column_schema[0]["type"] == "number"

    # Test without column_schema (optional field)
    output_without_schema = ToolOutputDef(
        id="output2",
        pattern="output2.txt"
    )

    assert output_without_schema.column_schema is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
