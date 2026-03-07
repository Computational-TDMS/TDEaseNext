from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from app.core.executor.base import TaskSpec
from app.core.executor.errors import ExecutableNotFoundError, WorkspaceValidationError
from app.core.executor.local import LocalExecutor, _validate_launch_contract, split_prebuilt_command


def _make_workspace_dir() -> Path:
    base = Path("data") / "test_tmp_dirs"
    base.mkdir(parents=True, exist_ok=True)
    path = (base / f"local_executor_security_{uuid4().hex}").resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.mark.asyncio
async def test_local_executor_passes_injection_payload_as_literal(monkeypatch):
    workspace = _make_workspace_dir()
    payload = "demo; echo PWNED && whoami"
    captured: list[list[str]] = []

    def _capture_run_command(args, workdir, conda_env=None, log_callback=None, task_id=""):
        captured.append(list(args))

    monkeypatch.setattr("app.core.executor.local.run_command", _capture_run_command)

    tools_registry = {
        "echo_tool": {
            "id": "echo_tool",
            "executionMode": "script",
            "command": {"interpreter": "python", "executable": "tests/fixtures/tools/mock_echo_argv_tool.py"},
            "ports": {"inputs": [], "outputs": []},
            "parameters": {"name": {"type": "value", "flag": "--name"}},
            "output": {"flagSupported": False},
        }
    }
    executor = LocalExecutor(tools_registry)
    spec = TaskSpec(
        node_id="echo_1",
        tool_id="echo_tool",
        params={"name": payload},
        input_paths=[],
        output_paths=[],
        workspace_path=workspace,
        task_id="exec:echo_1",
    )
    await executor.execute(spec)

    assert captured, "Expected command launch call"
    argv = captured[0]
    assert payload in argv
    assert "--name" in argv


def test_validate_launch_contract_rejects_path_traversal_workspace():
    with pytest.raises(WorkspaceValidationError):
        _validate_launch_contract(["python"], Path(".."))


def test_validate_launch_contract_rejects_unknown_executable():
    workspace = _make_workspace_dir()
    with pytest.raises(ExecutableNotFoundError):
        _validate_launch_contract(["definitely-not-a-real-executable-xyz"], workspace)


def test_split_prebuilt_command_windows_quoting():
    cmd = 'python.exe -c "print(1)" --name "A B"'
    parts = split_prebuilt_command(cmd, on_windows=True)
    assert parts[0] == "python.exe"
    assert parts[1] == "-c"
    assert parts[2] == '"print(1)"'
    assert parts[-1] == '"A B"'


def test_split_prebuilt_command_non_windows_quoting():
    cmd = 'python -c "print(1)" --name "A B"'
    parts = split_prebuilt_command(cmd, on_windows=False)
    assert parts[0] == "python"
    assert parts[1] == "-c"
    assert parts[2] == "print(1)"
    assert parts[-1] == "A B"
