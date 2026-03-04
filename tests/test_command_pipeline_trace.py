from app.core.executor.command_pipeline import CommandPipeline


def test_build_with_trace_includes_input_flags_and_positional_args():
    tool_def = {
        "id": "trace_tool",
        "executionMode": "script",
        "command": {"interpreter": "python", "executable": "tests/fixtures/tools/mock_echo_argv_tool.py"},
        "ports": {
            "inputs": [
                {"id": "raw_input", "flag": "-i", "dataType": "raw"},
                {"id": "fasta_file", "positional": True, "positionalOrder": 1, "dataType": "fasta"},
            ],
            "outputs": [{"id": "output", "handle": "output", "pattern": "{sample}.txt"}],
        },
        "parameters": {"capture_path": {"type": "value", "flag": "--capture-path"}},
        "output": {"flagSupported": True, "flag": "-o", "flagValue": "{output_path}"},
    }
    pipeline = CommandPipeline(tool_def)

    cmd_parts, trace = pipeline.build_with_trace(
        param_values={"capture_path": "trace.json"},
        input_files={"raw_input": "D:/tmp/a.raw", "fasta_file": "D:/tmp/db.fasta"},
        output_target="D:/tmp/out.txt",
    )

    assert trace.tool_id == "trace_tool"
    assert trace.output_flag["flag"] == "-o"
    assert trace.output_flag["value"] == "D:/tmp/out.txt"
    assert trace.parameter_flags == ["--capture-path", "trace.json"]
    assert trace.input_flags == ["-i", "D:/tmp/a.raw"]
    assert trace.positional_args == ["D:/tmp/db.fasta"]
    assert trace.cmd_parts == cmd_parts
