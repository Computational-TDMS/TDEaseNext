from pathlib import Path

from app.services.input_binding_planner import plan_input_bindings


def test_plan_input_bindings_binds_flagged_input_with_mismatched_source_handle():
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
    expected = Path("workspace/dummy.raw")
    completed_outputs = {"data_loader_1": [expected]}

    plan, decisions = plan_input_bindings(
        node_id="pbfgen_1",
        edges=edges,
        nodes_map=nodes_map,
        tools_registry=tools_registry,
        completed_outputs=completed_outputs,
        target_tool_id="pbfgen",
    )

    assert plan["input_file"] == expected
    assert len(decisions) == 1
    assert decisions[0].status == "bound"
    assert decisions[0].target_port_id == "input_file"


def test_plan_input_bindings_traces_skipped_edge_when_source_not_ready():
    tools_registry = {
        "source_tool": {"ports": {"outputs": [{"id": "output", "handle": "output", "dataType": "raw"}]}},
        "target_tool": {"ports": {"inputs": [{"id": "input_file", "dataType": "raw", "required": True}]}},
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
            "targetHandle": "input-input_file",
        }
    ]

    plan, decisions = plan_input_bindings(
        node_id="target_1",
        edges=edges,
        nodes_map=nodes_map,
        tools_registry=tools_registry,
        completed_outputs={},
        target_tool_id="target_tool",
    )

    assert plan == {}
    assert len(decisions) == 1
    assert decisions[0].status == "skipped"
    assert decisions[0].reason == "source-not-ready"
