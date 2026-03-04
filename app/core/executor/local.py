"""
LocalExecutor - 本地执行器

FlowEngine 原生本地执行器，使用 ShellRunner 执行命令，支持 Conda 环境。
集成进程注册表以支持进程取消功能。
"""
import asyncio
import json
import logging
import platform
import shlex
import subprocess
from pathlib import Path
from typing import List

from .base import Executor, TaskSpec
from .command_pipeline import CommandPipeline
from .shell_runner import run_shell
from .process_registry import process_registry

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
    task_id: str = "",
) -> None:
    """同步执行 Shell 命令，支持 Conda，可选 log_callback 捕获 stdout/stderr"""
    if len(cmd_parts) == 1 and isinstance(cmd_parts[0], str):
        cmd_str = cmd_parts[0]
    else:
        cmd_str = _cmd_parts_to_shell_string(cmd_parts)
    run_shell(cmd=cmd_str, workdir=workdir, conda_env=conda_env, log_callback=log_callback, task_id=task_id)


class LocalExecutor(Executor):
    """本地执行器 - 使用 CommandPipeline 构建命令，ShellRunner 执行"""

    def __init__(self, tools_registry: dict):
        self.tools_registry = tools_registry

    async def execute(self, spec: TaskSpec) -> None:
        tool_info = self.tools_registry.get(spec.tool_id, {})

        if spec.cmd:
            # Use pre-built command if provided
            cmd_parts = [spec.cmd]
            trace_payload = {
                "tool_id": spec.tool_id,
                "execution_mode": "prebuilt",
                "node_id": spec.node_id,
                "cmd_parts": cmd_parts,
                "input_files": {k: str(v) for k, v in (spec.input_files or {}).items()},
                "params": spec.params,
            }
        else:
            # Build command using new CommandPipeline
            pipeline = CommandPipeline(tool_info)

            # Convert input_paths/input_files to input_files Dict[str, str]
            # 优先使用 spec.input_files（port_id -> Path 映射），否则回退到 positional 逻辑
            input_files = {}
            if spec.input_files:
                # 使用新的字典格式，支持所有输入端口（包括 flag 和 positional）
                input_files = {port_id: str(path) for port_id, path in spec.input_files.items()}
                logger.info(f"[LocalExecutor] Using spec.input_files: {input_files}")
            else:
                # 向后兼容：只处理 positional 端口
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
                logger.info(f"[LocalExecutor] Using spec.input_paths fallback: {input_files}")

            # Determine output directory
            output_target = str(spec.output_paths[0]) if spec.output_paths else None

            logger.info(f"[LocalExecutor] Building command for tool {spec.tool_id}")
            # Build command
            cmd_parts, trace = pipeline.build_with_trace(
                param_values=spec.params,
                input_files=input_files,
                output_target=output_target
            )
            trace_payload = trace.to_dict()
            trace_payload["node_id"] = spec.node_id

        conda = spec.conda_env or tool_info.get("conda_env")
        log_cb = getattr(spec, "log_callback", None)
        if log_cb:
            try:
                log_cb(f"[command_trace] {json.dumps(trace_payload, ensure_ascii=False)}", "info")
            except Exception:
                logger.exception("[LocalExecutor] Failed to emit command trace")
        task_id = getattr(spec, "task_id", "")
        await asyncio.to_thread(_run_shell, cmd_parts, spec.workspace_path, conda, log_cb, task_id)

    async def cancel(self, task_id: str) -> bool:
        """
        取消指定任务。

        通过进程注册表终止进程。使用两阶段终止策略：
        1. SIGTERM (优雅终止)
        2. 如果 3 秒后仍在运行，使用 SIGKILL (强制终止)

        Args:
            task_id: 任务标识符，格式为 {execution_id}:{node_id}

        Returns:
            bool: 如果成功取消返回 True，否则返回 False
        """
        logger.info(f"[LocalExecutor] Attempting to cancel task_id={task_id}")
        result = process_registry.cancel(task_id)
        if result:
            logger.info(f"[LocalExecutor] Successfully cancelled task_id={task_id}")
        else:
            logger.warning(f"[LocalExecutor] Failed to cancel task_id={task_id} (not found in registry)")
        return result
