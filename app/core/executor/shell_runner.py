"""
ShellRunner - 独立 Shell 执行器

FlowEngine 原生 Shell 执行器，支持 Conda 环境激活。
使用 subprocess + conda run 进行命令执行。
支持 log_callback 捕获 stdout/stderr 供前端展示。
集成进程注册表以支持进程取消功能。
"""
import logging
import os
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Callable, List, Optional

from .process_registry import process_registry

logger = logging.getLogger(__name__)

ON_WINDOWS = os.name == "nt"


def _is_conda_env_path(conda_env: str) -> bool:
    """判断是否为 Conda 环境路径（绝对路径或包含路径分隔符）"""
    if not conda_env:
        return False
    return os.path.isabs(conda_env) or os.sep in conda_env or conda_env.startswith(".")


def run_shell(
    cmd: str,
    workdir: Path,
    conda_env: Optional[str] = None,
    log_callback: Optional[Callable[[str, str], None]] = None,
    task_id: str = "",
) -> None:
    """
    在指定工作目录执行 Shell 命令，可选 Conda 环境。

    Args:
        cmd: 要执行的命令字符串
        workdir: 工作目录路径
        conda_env: Conda 环境名（如 "topfd"）或路径（如 ".conda/envs/xxx"）
        log_callback: 可选，每行 stdout/stderr 回调 (message, level)，level 为 "info" 或 "error"
        task_id: 任务标识符，格式为 {execution_id}:{node_id}，用于进程追踪和取消

    Raises:
        subprocess.CalledProcessError: 命令返回非零退出码时
    """
    workdir = Path(workdir)
    if not workdir.exists():
        raise FileNotFoundError(f"Workspace directory does not exist: {workdir}")

    logger.info(f"[ShellRunner] Executing in {workdir}: {cmd[:500] + '...' if len(cmd) > 500 else cmd}")
    logger.debug("Executing in %s: %s", workdir, cmd[:200] + ("..." if len(cmd) > 200 else ""))

    if conda_env:
        _run_with_conda(cmd, workdir, conda_env, log_callback, task_id)
    else:
        _run_direct(cmd, workdir, log_callback, task_id)


def _run_direct(cmd: str, workdir: Path, log_callback: Optional[Callable[[str, str], None]] = None, task_id: str = "") -> None:
    """直接执行，无 Conda"""
    if log_callback:
        _run_with_capture(cmd, workdir, None, log_callback, task_id)
    else:
        result = subprocess.run(cmd, shell=True, cwd=workdir)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, cmd)


def _run_with_capture(
    cmd: str,
    workdir: Path,
    conda_env: Optional[str],
    log_callback: Callable[[str, str], None],
    task_id: str = "",
) -> None:
    """执行命令并实时捕获 stdout/stderr，通过 callback 输出"""
    proc = None

    try:
        if conda_env:
            conda_exe = shutil.which("conda")
            if not conda_exe:
                logger.warning("conda not found, running without conda")
                _run_with_capture(cmd, workdir, None, log_callback, task_id)
                return
            conda_args = [conda_exe, "run"]
            if _is_conda_env_path(conda_env):
                conda_args.extend(["-p", conda_env])
            else:
                conda_args.extend(["-n", conda_env])
            if ON_WINDOWS:
                conda_args.extend(["cmd", "/c", cmd])
            else:
                conda_args.extend(["bash", "-c", cmd])
            proc = subprocess.Popen(
                conda_args,
                cwd=workdir,
                env=_build_env(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
            )
        else:
            proc = subprocess.Popen(
                cmd,
                shell=True,
                cwd=workdir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
            )

        # 注册进程到进程注册表（如果提供了 task_id）
        if task_id and proc:
            process_registry.register(task_id, proc)
            logger.debug(f"[ShellRunner] Registered process for task_id={task_id}, pid={proc.pid}")

        def read_stream(stream, level: str):
            for line in iter(stream.readline, ""):
                line = line.rstrip()
                if line:
                    log_callback(line, level)

        t_out = threading.Thread(target=read_stream, args=(proc.stdout, "info"))
        t_err = threading.Thread(target=read_stream, args=(proc.stderr, "info"))
        t_out.daemon = True
        t_err.daemon = True
        t_out.start()
        t_err.start()
        proc.wait()
        t_out.join(timeout=1)
        t_err.join(timeout=1)
        if proc.returncode != 0:
            raise subprocess.CalledProcessError(proc.returncode, cmd)
    finally:
        # 确保进程从注册表注销
        if task_id and proc:
            process_registry.unregister(task_id)
            logger.debug(f"[ShellRunner] Unregistered process for task_id={task_id}")


def _run_with_conda(cmd: str, workdir: Path, conda_env: str, log_callback: Optional[Callable[[str, str], None]] = None, task_id: str = "") -> None:
    """通过 conda run 在指定环境中执行"""
    if log_callback:
        _run_with_capture(cmd, workdir, conda_env, log_callback, task_id)
        return
    conda_exe = shutil.which("conda")
    if not conda_exe:
        logger.warning("conda not found in PATH, running without conda activation")
        _run_direct(cmd, workdir, None, task_id)
        return

    conda_args: List[str] = [conda_exe, "run", "--no-capture-output"]
    if _is_conda_env_path(conda_env):
        conda_args.extend(["-p", conda_env])
    else:
        conda_args.extend(["-n", conda_env])

    if ON_WINDOWS:
        conda_args.extend(["cmd", "/c", cmd])
    else:
        conda_args.extend(["bash", "-c", cmd])

    result = subprocess.run(
        conda_args,
        cwd=workdir,
        env=_build_env(),
    )

    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, " ".join(conda_args))


def _build_env() -> dict:
    """构建执行环境变量，移除与 Conda 冲突的变量"""
    env = dict(os.environ)
    for var in ["R_LIBS", "PYTHONPATH", "PERLLIB", "PERL5LIB"]:
        env.pop(var, None)
    return env
