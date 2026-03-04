from pathlib import Path

from app.services.workflow_service import _resolve_input_paths


def test_resolve_input_paths_handles_mismatched_source_handle_for_single_output():
    tools_registry = {
        "data_loader": {
            "ports": {
                "outputs": [
                    {
                        "id": "output",
                        "handle": "output",
                        "dataType": "raw",
                        "pattern": "{sample}.raw",
                        "provides": ["raw"],
                    }
                ]
            }
        },
        "pbfgen": {
            "ports": {
                "inputs": [
                    {
                        "id": "input_file",
                        "dataType": "raw",
                        "accept": ["raw", "mzml"],
                        "required": True,
                    }
                ]
            }
        },
    }
    nodes_map = {
        "data_loader_1": {"id": "data_loader_1", "data": {"type": "data_loader"}},
        "pbfgen_1": {"id": "pbfgen_1", "data": {"type": "pbfgen"}},
    }
    edges = [
        {
            "id": "e_data_pbfgen",
            "source": "data_loader_1",
            "target": "pbfgen_1",
            "sourceHandle": "output-mzml",
            "targetHandle": "input-input_file",
        }
    ]
    expected_path = Path("workspace/dummy.raw")
    completed_outputs = {"data_loader_1": [expected_path]}

    result = _resolve_input_paths(
        node_id="pbfgen_1",
        edges=edges,
        nodes_map=nodes_map,
        tools_registry=tools_registry,
        sample_ctx={"sample": "dummy"},
        workspace=Path("workspace"),
        completed_outputs=completed_outputs,
        target_tool_id="pbfgen",
    )

    assert result["input_file"] == expected_path


def test_resolve_input_paths_can_match_target_port_by_datatype_and_accept():
    tools_registry = {
        "source_tool": {
            "ports": {
                "outputs": [
                    {
                        "id": "pbf",
                        "handle": "pbf",
                        "dataType": "pbf",
                        "pattern": "{sample}.pbf",
                        "provides": ["pbf"],
                    },
                    {
                        "id": "ms1ft",
                        "handle": "ms1ft",
                        "dataType": "ms1ft",
                        "pattern": "{sample}.ms1ft",
                        "provides": ["ms1ft", "feature"],
                    },
                ]
            }
        },
        "target_tool": {
            "ports": {
                "inputs": [
                    {
                        "id": "feature_file",
                        "dataType": "ms1ft",
                        "accept": ["ms1ft", "feature"],
                        "required": True,
                    }
                ]
            }
        },
    }
    nodes_map = {
        "source_1": {"id": "source_1", "data": {"type": "source_tool"}},
        "target_1": {"id": "target_1", "data": {"type": "target_tool"}},
    }
    edges = [
        {
            "id": "e_source_target",
            "source": "source_1",
            "target": "target_1",
            "sourceHandle": "output-unknown",
            "targetHandle": "input-ms1ft",
        }
    ]
    pbf = Path("workspace/dummy.pbf")
    ms1ft = Path("workspace/dummy.ms1ft")
    completed_outputs = {"source_1": [pbf, ms1ft]}

    result = _resolve_input_paths(
        node_id="target_1",
        edges=edges,
        nodes_map=nodes_map,
        tools_registry=tools_registry,
        sample_ctx={"sample": "dummy"},
        workspace=Path("workspace"),
        completed_outputs=completed_outputs,
        target_tool_id="target_tool",
    )

    assert result["feature_file"] == ms1ft


def test_resolve_input_paths_fallbacks_to_single_target_input_when_target_handle_missing():
    tools_registry = {
        "source_tool": {
            "ports": {
                "outputs": [
                    {
                        "id": "raw",
                        "handle": "raw",
                        "dataType": "raw",
                        "pattern": "{sample}.raw",
                    }
                ]
            }
        },
        "target_tool": {
            "ports": {
                "inputs": [
                    {
                        "id": "input_file",
                        "dataType": "raw",
                        "required": True,
                    }
                ]
            }
        },
    }
    nodes_map = {
        "source_1": {"id": "source_1", "data": {"type": "source_tool"}},
        "target_1": {"id": "target_1", "data": {"type": "target_tool"}},
    }
    edges = [
        {
            "id": "e_source_target",
            "source": "source_1",
            "target": "target_1",
            "sourceHandle": "output-raw",
            "targetHandle": "",
        }
    ]
    raw = Path("workspace/dummy.raw")
    completed_outputs = {"source_1": [raw]}

    result = _resolve_input_paths(
        node_id="target_1",
        edges=edges,
        nodes_map=nodes_map,
        tools_registry=tools_registry,
        sample_ctx={"sample": "dummy"},
        workspace=Path("workspace"),
        completed_outputs=completed_outputs,
        target_tool_id="target_tool",
    )

    assert result["input_file"] == raw
