"""
LocalExecutor - 本地执行器

FlowEngine 原生本地执行器，使用 ShellRunner 执行命令，支持 Conda 环境。
"""
import asyncio
import logging
import platform
import shlex
import subprocess
from pathlib import Path
from typing import List

from .base import Executor, TaskSpec
from .command_pipeline import CommandPipeline
from .shell_runner import run_shell

logger = logging.getLogger(__name__)


def _cmd_parts_to_shell_string(cmd_parts: List[str]) -> str:
    """将命令参数列表转为 shell 安全字符串（正确处理含空格的参数如 JSON）"""
    if platform.system() == "Windows":
        return subprocess.list2cmdline(cmd_parts)
    return shlex.join(cmd_parts)


def _run_shell(
    cmd_parts: List[str],
    workdir: Path,
    conda_env: str = None,
    log_callback=None,
) -> None:
    """同步执行 Shell 命令，支持 Conda，可选 log_callback 捕获 stdout/stderr"""
    cmd_str = _cmd_parts_to_shell_string(cmd_parts)
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
            # spec.input_paths 按 positionalOrder 排序，需与 positional 端口顺序一致
            input_files = {}
            ports_inputs = tool_info.get("ports", {}).get("inputs", [])
            pos_inputs = [
                p for p in ports_inputs
                if isinstance(p, dict) and p.get("positional", False)
            ]
            pos_inputs.sort(key=lambda x: x.get("positionalOrder", 0))
            for i, port_def in enumerate(pos_inputs):
                port_id = port_def.get("id", f"input_{i}")
                if port_id and i < len(spec.input_paths):
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
