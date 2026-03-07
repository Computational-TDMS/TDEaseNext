"""
Simple integration tests for interactive node execution
"""

import pytest
from pathlib import Path
from app.services.tool_registry import ToolRegistry, get_tool_registry


def test_tool_registry_loads_interactive_tool():
    """Test that tool registry can load tools with executionMode=interactive"""
    registry = get_tool_registry()
    
    # Reload to pick up new tool definitions
    registry.reload()
    
    # Check that featuremap_viewer is loaded
    tool = registry.get("featuremap_viewer")
    assert tool is not None, "featuremap_viewer tool should be loaded"
    assert tool.get("executionMode") == "interactive", "executionMode should be 'interactive'"
    assert tool.get("defaultMapping") is not None, "defaultMapping should be present"
    assert "x" in tool["defaultMapping"], "defaultMapping should have 'x' key"


def test_tool_registry_loads_compute_tool():
    """Test that tool registry can load tools with executionMode=compute"""
    registry = get_tool_registry()
    
    # Check that topfd is loaded
    tool = registry.get("topfd")
    assert tool is not None, "topfd tool should be loaded"
    assert tool.get("executionMode") in ["native", "compute"], "executionMode should be 'native' or 'compute'"


def test_tool_registry_loads_topmsv_tools_with_state_contracts():
    """TopMSV tools should pass schema loading with explicit state metadata."""
    registry = get_tool_registry()
    registry.reload()

    bundle_builder = registry.get("prsm_bundle_builder")
    ms2_viewer = registry.get("topmsv_ms2_viewer")
    sequence_viewer = registry.get("topmsv_sequence_viewer")

    assert bundle_builder is not None, "prsm_bundle_builder tool should be loaded"
    assert ms2_viewer is not None, "topmsv_ms2_viewer tool should be loaded"
    assert sequence_viewer is not None, "topmsv_sequence_viewer tool should be loaded"

    assert bundle_builder.get("executionMode") == "script"
    bundle_inputs = {port["id"] for port in bundle_builder["ports"]["inputs"]}
    bundle_outputs = {port["id"] for port in bundle_builder["ports"]["outputs"]}
    assert {"prsm_single", "ms2_msalign"}.issubset(bundle_inputs)
    assert {"prsm_table_clean", "prsm_bundle"}.issubset(bundle_outputs)

    for viewer in (ms2_viewer, sequence_viewer):
        assert viewer.get("executionMode") == "interactive"
        assert viewer.get("selection_key_field") == "Prsm ID"
        state_port = next(
            p for p in viewer["ports"]["inputs"] if p.get("id") == "selection_in"
        )
        assert state_port.get("portKind") == "state-in"
        assert state_port.get("semanticType") == "state/selection_ids"


def test_tool_definition_schema_validation():
    """Test that ToolDefinition accepts new fields"""
    from app.schemas.tool import ToolDefinition
    
    # Create a tool with all new fields
    tool_data = {
        "id": "test_interactive",
        "name": "Test Interactive",
        "executionMode": "interactive",
        "defaultMapping": {
            "x": "col1",
            "y": "col2"
        },
        "ports": {
            "inputs": [
                {
                    "id": "input1",
                    "name": "Input 1",
                    "dataType": "feature",
                    "required": True,
                    "pattern": "{sample}.feature"
                }
            ],
            "outputs": [
                {
                    "id": "output1",
                    "name": "Output 1",
                    "pattern": "output.txt",
                    "column_schema": [
                        {"name": "id", "type": "number", "description": "ID"},
                        {"name": "value", "type": "string", "description": "Value"}
                    ]
                }
            ]
        },
        "parameters": {}
    }
    
    tool_def = ToolDefinition(**tool_data)
    assert tool_def.executionMode == "interactive"
    assert tool_def.defaultMapping == {"x": "col1", "y": "col2"}
    # Outputs are stored in ports field
    assert len(tool_def.ports.get("outputs", [])) == 1
    # Check the column_schema in the output
    output_data = tool_def.ports["outputs"][0]
    assert "column_schema" in output_data
    assert len(output_data["column_schema"]) == 2


def test_output_column_schema_field():
    """Test that ToolOutputDef column_schema field works correctly"""
    from app.schemas.tool import ToolOutputDef
    
    # Create with column_schema
    output = ToolOutputDef(
        id="output1",
        pattern="output.txt",
        column_schema=[
            {"name": "col1", "type": "string", "description": "Column 1"},
            {"name": "col2", "type": "number", "description": "Column 2"}
        ]
    )
    
    assert output.column_schema is not None
    assert len(output.column_schema) == 2
    assert output.column_schema[0]["name"] == "col1"
    assert output.column_schema[1]["type"] == "number"
    
    # Create without column_schema (optional)
    output2 = ToolOutputDef(
        id="output2",
        pattern="output2.txt"
    )
    
    assert output2.column_schema is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
