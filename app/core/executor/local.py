"""
LocalExecutor - 本地执行器

FlowEngine 原生本地执行器，使用 ShellRunner 执行命令，支持 Conda 环境。
"""
import asyncio
import logging
from pathlib import Path
from typing import List

from .base import Executor, TaskSpec
from .command_pipeline import CommandPipeline
from .shell_runner import run_shell

logger = logging.getLogger(__name__)


def _run_shell(
    cmd_parts: List[str],
    workdir: Path,
    conda_env: str = None,
    log_callback=None,
) -> None:
    """同步执行 Shell 命令，支持 Conda，可选 log_callback 捕获 stdout/stderr"""
    # Convert command parts to shell string
    cmd_str = " ".join(cmd_parts)
    run_shell(cmd=cmd_str, workdir=workdir, conda_env=conda_env, log_callback=log_callback)


class LocalExecutor(Executor):
    """本地执行器 - 使用 CommandPipeline 构建命令，ShellRunner 执行"""

    def __init__(self, tools_registry: dict):
        self.tools_registry = tools_registry

    async def execute(self, spec: TaskSpec) -> None:
        tool_info = self.tools_registry.get(spec.tool_id, {})

        if spec.cmd:
            # Use pre-built command if provided
            cmd_parts = [spec.cmd]
        else:
            # Build command using new CommandPipeline
            pipeline = CommandPipeline(tool_info)

            # Convert input_paths List[Path] to input_files Dict[str, str]
            # Map port names to file paths
            input_files = {}
            ports_inputs = tool_info.get("ports", {}).get("inputs", [])
            for i, port_def in enumerate(ports_inputs):
                if isinstance(port_def, dict):
                    port_id = port_def.get("id", f"input_{i}")
                else:
                    port_id = f"input_{i}"
                if i < len(spec.input_paths):
                    input_files[port_id] = str(spec.input_paths[i])

            # Determine output directory
            output_dir = str(spec.output_paths[0].parent) if spec.output_paths else None

            # Build command
            cmd_parts = pipeline.build(
                param_values=spec.params,
                input_files=input_files,
                output_dir=output_dir
            )

        conda = spec.conda_env or tool_info.get("conda_env")
        log_cb = getattr(spec, "log_callback", None)
        await asyncio.to_thread(_run_shell, cmd_parts, spec.workspace_path, conda, log_cb)

    async def cancel(self, task_id: str) -> bool:
        return False
