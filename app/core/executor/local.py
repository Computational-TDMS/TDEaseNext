"""
LocalExecutor - 本地执行器

FlowEngine 原生本地执行器，使用 ShellRunner 执行命令，支持 Conda 环境。
集成进程注册表以支持进程取消功能。
"""
import asyncio
import json
import logging
import os
import shlex
import shutil
from pathlib import Path
from typing import List

from .base import Executor, TaskSpec
from .command_pipeline import CommandPipeline
from .errors import ExecutableNotFoundError, LaunchValidationError, WorkspaceValidationError
from .shell_runner import run_command
from .process_registry import process_registry

logger = logging.getLogger(__name__)
ON_WINDOWS = os.name == "nt"


def split_prebuilt_command(cmd: str, *, on_windows: bool | None = None) -> List[str]:
    if not isinstance(cmd, str) or not cmd.strip():
        raise LaunchValidationError("Prebuilt command is empty")
    windows_mode = ON_WINDOWS if on_windows is None else on_windows
    parts = shlex.split(cmd, posix=not windows_mode)
    if not parts:
        raise LaunchValidationError("Prebuilt command has no executable")
    return parts


def _resolve_executable(executable: str, workdir: Path) -> str:
    if not executable:
        raise ExecutableNotFoundError("Executable is empty")

    candidate = Path(executable)
    if candidate.is_absolute():
        if not candidate.exists():
            raise ExecutableNotFoundError(f"Executable not found: {candidate}")
        return str(candidate)

    has_path_sep = (os.sep in executable) or (os.altsep and os.altsep in executable)
    if has_path_sep:
        resolved = (workdir / candidate).resolve()
        if not resolved.exists():
            raise ExecutableNotFoundError(f"Executable not found: {resolved}")
        return str(resolved)

    resolved_from_path = shutil.which(executable)
    if not resolved_from_path:
        raise ExecutableNotFoundError(f"Executable not found in PATH: {executable}")
    return resolved_from_path


def _validate_launch_contract(cmd_parts: List[str], workdir: Path) -> List[str]:
    if not cmd_parts:
        raise LaunchValidationError("No command provided")

    raw_workdir = Path(workdir)
    if ".." in raw_workdir.parts:
        raise WorkspaceValidationError(f"Workspace path traversal is not allowed: {workdir}")

    resolved_workdir = raw_workdir.resolve()
    if not resolved_workdir.exists() or not resolved_workdir.is_dir():
        raise WorkspaceValidationError(f"Workspace directory does not exist: {workdir}")

    validated = list(cmd_parts)
    validated[0] = _resolve_executable(validated[0], resolved_workdir)
    return validated


def _run_command(
    cmd_parts: List[str],
    workdir: Path,
    conda_env: str = None,
    log_callback=None,
    task_id: str = "",
) -> None:
    """同步执行命令参数向量，默认 shell=False。"""
    validated_cmd = _validate_launch_contract(cmd_parts, workdir)
    run_command(args=validated_cmd, workdir=workdir, conda_env=conda_env, log_callback=log_callback, task_id=task_id)


class LocalExecutor(Executor):
    """本地执行器 - 使用 CommandPipeline 构建命令，ShellRunner 执行"""

    def __init__(self, tools_registry: dict):
        self.tools_registry = tools_registry

    async def execute(self, spec: TaskSpec) -> None:
        tool_info = self.tools_registry.get(spec.tool_id, {})

        if spec.cmd:
            # Legacy path: parse string into argv, then run in secure launch path.
            cmd_parts = split_prebuilt_command(spec.cmd)
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
        await asyncio.to_thread(_run_command, cmd_parts, spec.workspace_path, conda, log_cb, task_id)

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
