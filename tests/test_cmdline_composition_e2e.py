import json
from pathlib import Path

import pytest

from app.services.workflow_service import WorkflowService


class _StaticToolRegistry:
    def __init__(self, tools: dict):
        self._tools = tools

    def list_tools(self) -> dict:
        return self._tools


@pytest.mark.asyncio
async def test_e2e_cmdline_pbfgen_flag_input_resolves_from_mismatched_handles(tmp_path: Path):
    tools = {
        "source_raw": {
            "id": "source_raw",
            "executionMode": "script",
            "command": {"interpreter": "python", "executable": "tests/fixtures/tools/mock_source_tool.py"},
            "ports": {
                "inputs": [],
                "outputs": [
                    {
                        "id": "output",
                        "handle": "output",
                        "dataType": "raw",
                        "pattern": "{sample}.raw",
                        "provides": ["raw"],
                    }
                ],
            },
            "parameters": {},
            "output": {"flagSupported": True, "flag": "--out", "flagValue": "{output_path}"},
        },
        "pbfgen_mock": {
            "id": "pbfgen_mock",
            "executionMode": "script",
            "command": {"interpreter": "python", "executable": "tests/fixtures/tools/mock_pbfgen_tool.py"},
            "ports": {
                "inputs": [
                    {
                        "id": "input_file",
                        "flag": "-i",
                        "dataType": "raw",
                        "accept": ["raw", "mzml"],
                        "required": True,
                    }
                ],
                "outputs": [{"id": "output", "handle": "output", "dataType": "pbf", "pattern": "{sample}.pbf"}],
            },
            "parameters": {"capture_path": {"type": "value", "flag": "--capture-path"}},
            "output": {"flagSupported": False},
        },
    }

    workflow = {
        "metadata": {"id": "wf_cmdline_pbfgen"},
        "format_version": "2.0",
        "nodes": [
            {"id": "source_1", "data": {"type": "source_raw", "params": {}}},
            {
                "id": "pbfgen_1",
                "data": {
                    "type": "pbfgen_mock",
                    "params": {"capture_path": "pbfgen_cmdline.json"},
                },
            },
        ],
        "edges": [
            {
                "id": "e_source_to_pbf",
                "source": "source_1",
                "target": "pbfgen_1",
                "sourceHandle": "output-mzml",
                "targetHandle": "input-input_file",
            }
        ],
    }

    logs: list[tuple[str, str]] = []

    def _log_callback(message: str, level: str) -> None:
        logs.append((message, level))

    service = WorkflowService(tool_registry=_StaticToolRegistry(tools))
    result = await service.execute_workflow(
        workflow_json=workflow,
        workspace_path=tmp_path,
        parameters={"sample_context": {"sample": "demo"}},
        log_callback=_log_callback,
    )

    assert result["status"] == "completed", result

    raw_path = tmp_path / "demo.raw"
    assert raw_path.exists(), f"Expected upstream raw file: {raw_path}"

    capture_file = tmp_path / "pbfgen_cmdline.json"
    assert capture_file.exists(), f"Expected cmdline capture file: {capture_file}"
    payload = json.loads(capture_file.read_text(encoding="utf-8"))
    argv = payload["argv"]

    assert "-i" in argv, f"Expected -i in argv, got: {argv}"
    assert argv[argv.index("-i") + 1] == str(raw_path)
    assert any("PBFGEN_ARGV_JSON=" in msg for msg, _ in logs), "Expected runtime stdout log via log_callback"
    trace_logs = [msg for msg, _ in logs if msg.startswith("[command_trace] ")]
    assert trace_logs, "Expected structured command_trace log"
    trace_payload = json.loads(trace_logs[-1].split("[command_trace] ", 1)[1])
    assert "-i" in trace_payload["cmd_parts"], trace_payload
    assert str(raw_path) in trace_payload["cmd_parts"], trace_payload


@pytest.mark.asyncio
async def test_e2e_cmdline_toppic_style_positional_order_is_stable(tmp_path: Path):
    tools = {
        "source_fasta": {
            "id": "source_fasta",
            "executionMode": "script",
            "command": {"interpreter": "python", "executable": "tests/fixtures/tools/mock_source_tool.py"},
            "ports": {
                "inputs": [],
                "outputs": [{"id": "output", "handle": "output", "dataType": "fasta", "pattern": "{sample}.fasta"}],
            },
            "parameters": {},
            "output": {"flagSupported": True, "flag": "--out", "flagValue": "{output_path}"},
        },
        "source_msalign": {
            "id": "source_msalign",
            "executionMode": "script",
            "command": {"interpreter": "python", "executable": "tests/fixtures/tools/mock_source_tool.py"},
            "ports": {
                "inputs": [],
                "outputs": [{"id": "output", "handle": "output", "dataType": "msalign", "pattern": "{sample}.msalign"}],
            },
            "parameters": {},
            "output": {"flagSupported": True, "flag": "--out", "flagValue": "{output_path}"},
        },
        "toppic_mock": {
            "id": "toppic_mock",
            "executionMode": "script",
            "command": {"interpreter": "python", "executable": "tests/fixtures/tools/mock_echo_argv_tool.py"},
            "ports": {
                "inputs": [
                    {"id": "fasta_file", "dataType": "fasta", "accept": ["fasta"], "positional": True, "positionalOrder": 1},
                    {"id": "ms2_file", "dataType": "msalign", "accept": ["msalign"], "positional": True, "positionalOrder": 2},
                ],
                "outputs": [{"id": "output", "handle": "output", "dataType": "prsm", "pattern": "{sample}.prsm"}],
            },
            "parameters": {"capture_path": {"type": "value", "flag": "--capture-path"}},
            "output": {"flagSupported": False},
        },
    }

    workflow = {
        "metadata": {"id": "wf_cmdline_toppic"},
        "format_version": "2.0",
        "nodes": [
            {"id": "fasta_1", "data": {"type": "source_fasta", "params": {}}},
            {"id": "ms2_1", "data": {"type": "source_msalign", "params": {}}},
            {"id": "toppic_1", "data": {"type": "toppic_mock", "params": {"capture_path": "toppic_cmdline.json"}}},
        ],
        "edges": [
            {
                "id": "e_fasta_toppic",
                "source": "fasta_1",
                "target": "toppic_1",
                "sourceHandle": "output-anything",
                "targetHandle": "input-fasta",
            },
            {
                "id": "e_msalign_toppic",
                "source": "ms2_1",
                "target": "toppic_1",
                "sourceHandle": "output-other",
                "targetHandle": "input-msalign",
            },
        ],
    }

    service = WorkflowService(tool_registry=_StaticToolRegistry(tools))
    result = await service.execute_workflow(
        workflow_json=workflow,
        workspace_path=tmp_path,
        parameters={"sample_context": {"sample": "demo"}},
    )

    assert result["status"] == "completed", result

    fasta_path = str(tmp_path / "demo.fasta")
    msalign_path = str(tmp_path / "demo.msalign")
    capture_file = tmp_path / "toppic_cmdline.json"
    payload = json.loads(capture_file.read_text(encoding="utf-8"))
    argv = payload["argv"]

    assert len(argv) >= 2, f"Expected positional args in argv, got: {argv}"
    assert argv[-2:] == [fasta_path, msalign_path], f"Positional order mismatch: {argv}"
