from __future__ import annotations

import builtins
import json
from pathlib import Path
from uuid import uuid4

import pytest

from app.dependencies import get_tool_registry as get_dependency_tool_registry
from app.services.tool_registry import ToolRegistry
from app.services.workflow_service import WorkflowService


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


@pytest.fixture
def local_tools_tmpdir() -> Path:
    root = Path.cwd() / ".pytest-run" / "tool_registry_profiles"
    root.mkdir(parents=True, exist_ok=True)
    run_dir = root / uuid4().hex
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def test_profile_precedence_base_then_profile_then_data(local_tools_tmpdir: Path) -> None:
    config_tools = local_tools_tmpdir / "config" / "tools"
    profile_dir = config_tools / "profiles" / "dev"
    data_tools = local_tools_tmpdir / "data" / "tools"

    _write_json(
        config_tools / "demo_tool.json",
        {
            "id": "demo_tool",
            "name": "Demo Tool",
            "executionMode": "native",
            "command": {"executable": "base-command"},
            "ports": {"inputs": [], "outputs": [{"id": "out", "pattern": "{sample}.txt"}]},
            "parameters": {},
        },
    )
    _write_json(
        profile_dir / "demo_tool.json",
        {
            "id": "demo_tool",
            "command": {"executable": "profile-command"},
        },
    )
    _write_json(
        data_tools / "demo_tool.json",
        {
            "id": "demo_tool",
            "command": {"executable": "local-command"},
        },
    )

    registry = ToolRegistry(
        config_tools_dir=config_tools,
        data_tools_dir=data_tools,
        profiles="dev",
        config_profiles_dir=config_tools / "profiles",
    )
    resolved = registry.get("demo_tool")
    assert resolved is not None
    assert resolved["command"]["executable"] == "local-command"


def test_profile_fallback_uses_base_when_override_absent(local_tools_tmpdir: Path) -> None:
    config_tools = local_tools_tmpdir / "config" / "tools"
    data_tools = local_tools_tmpdir / "data" / "tools"

    _write_json(
        config_tools / "demo_tool.json",
        {
            "id": "demo_tool",
            "name": "Demo Tool",
            "executionMode": "native",
            "command": {"executable": "base-command"},
            "ports": {"inputs": [], "outputs": [{"id": "out", "pattern": "{sample}.txt"}]},
            "parameters": {},
        },
    )

    registry = ToolRegistry(
        config_tools_dir=config_tools,
        data_tools_dir=data_tools,
        profiles="qa",
        config_profiles_dir=config_tools / "profiles",
    )
    resolved = registry.get("demo_tool")
    assert resolved is not None
    assert resolved["command"]["executable"] == "base-command"


def test_shared_config_rejects_absolute_path_with_guidance(local_tools_tmpdir: Path, caplog) -> None:
    config_tools = local_tools_tmpdir / "config" / "tools"
    data_tools = local_tools_tmpdir / "data" / "tools"

    _write_json(
        config_tools / "bad_tool.json",
        {
            "id": "bad_tool",
            "name": "Bad Tool",
            "executionMode": "native",
            "command": {"executable": "C:\\\\tooling\\\\bad_tool.exe"},
            "ports": {"inputs": [], "outputs": [{"id": "out", "pattern": "{sample}.txt"}]},
            "parameters": {},
        },
    )

    caplog.set_level("WARNING")
    registry = ToolRegistry(config_tools_dir=config_tools, data_tools_dir=data_tools)

    assert registry.get("bad_tool") is None
    assert "non-portable absolute executable path" in caplog.text
    assert "data/tools/*.json" in caplog.text


def test_local_data_override_can_use_absolute_path(local_tools_tmpdir: Path) -> None:
    config_tools = local_tools_tmpdir / "config" / "tools"
    data_tools = local_tools_tmpdir / "data" / "tools"

    _write_json(
        config_tools / "demo_tool.json",
        {
            "id": "demo_tool",
            "name": "Demo Tool",
            "executionMode": "native",
            "command": {"executable": "portable-command"},
            "ports": {"inputs": [], "outputs": [{"id": "out", "pattern": "{sample}.txt"}]},
            "parameters": {},
        },
    )
    _write_json(
        data_tools / "demo_tool.json",
        {
            "id": "demo_tool",
            "command": {"executable": "C:\\\\local\\\\demo_tool.exe"},
        },
    )

    registry = ToolRegistry(config_tools_dir=config_tools, data_tools_dir=data_tools)
    resolved = registry.get("demo_tool")
    assert resolved is not None
    assert resolved["command"]["executable"] == "C:\\\\local\\\\demo_tool.exe"


@pytest.mark.asyncio
async def test_workflow_execution_path_does_not_import_legacy_registry(local_tools_tmpdir: Path, monkeypatch) -> None:
    config_tools = local_tools_tmpdir / "config" / "tools"
    data_tools = local_tools_tmpdir / "data" / "tools"
    workspace = local_tools_tmpdir / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)

    _write_json(
        config_tools / "noop_tool.json",
        {
            "id": "noop_tool",
            "name": "Noop Tool",
            "executionMode": "script",
            "command": {
                "executable": "tests/fixtures/tools/mock_source_tool.py",
                "interpreter": "python",
            },
            "ports": {
                "inputs": [],
                "outputs": [{"id": "out", "pattern": "{sample}.txt", "handle": "out"}],
            },
            "parameters": {},
        },
    )

    registry = ToolRegistry(config_tools_dir=config_tools, data_tools_dir=data_tools)
    workflow_service = WorkflowService(tool_registry=registry)

    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "src.nodes.tool_registry" or name.startswith("src.nodes.tool_registry."):
            raise AssertionError("legacy tool registry import should not be required")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    workflow = {
        "metadata": {"id": "wf_no_legacy_registry", "name": "No Legacy Registry"},
        "format_version": "2.0",
        "nodes": [
            {
                "id": "n1",
                "type": "tool",
                "data": {"type": "noop_tool", "params": {}},
            }
        ],
        "edges": [],
    }

    result = await workflow_service.execute_workflow(
        workflow_json=workflow,
        workspace_path=workspace,
        parameters={"sample": "demo"},
        simulate=True,
        dryrun=False,
        resume=False,
    )
    assert result["status"] == "completed"


def test_dependency_injection_uses_authoritative_registry() -> None:
    registry = get_dependency_tool_registry()
    assert registry.__class__.__module__ == "app.services.tool_registry"
