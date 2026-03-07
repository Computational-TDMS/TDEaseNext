"""
Process runner for executor paths.

Runs commands as argument vectors with shell=False by default.
"""
from __future__ import annotations

import logging
import os
import shlex
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Callable, List, Optional

from .errors import CommandExecutionError, ExecutableNotFoundError, WorkspaceValidationError
from .process_registry import process_registry

logger = logging.getLogger(__name__)

ON_WINDOWS = os.name == "nt"


def _is_conda_env_path(conda_env: str) -> bool:
    if not conda_env:
        return False
    return os.path.isabs(conda_env) or os.sep in conda_env or conda_env.startswith(".")


def _build_env() -> dict:
    env = dict(os.environ)
    for var in ["R_LIBS", "PYTHONPATH", "PERLLIB", "PERL5LIB"]:
        env.pop(var, None)
    return env


def _resolve_conda_prefix(conda_env: str) -> List[str]:
    conda_exe = shutil.which("conda")
    if not conda_exe:
        raise ExecutableNotFoundError("conda executable not found in PATH")

    args: List[str] = [conda_exe, "run", "--no-capture-output"]
    if _is_conda_env_path(conda_env):
        args.extend(["-p", conda_env])
    else:
        args.extend(["-n", conda_env])
    return args


def _run_with_capture(
    launch_args: List[str],
    workdir: Path,
    log_callback: Callable[[str, str], None],
    task_id: str = "",
) -> None:
    proc = None
    try:
        proc = subprocess.Popen(
            launch_args,
            cwd=workdir,
            env=_build_env(),
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        if task_id and proc:
            process_registry.register(task_id, proc)

        def read_stream(stream, level: str) -> None:
            for line in iter(stream.readline, ""):
                line = line.rstrip()
                if line:
                    log_callback(line, level)

        t_out = threading.Thread(target=read_stream, args=(proc.stdout, "info"), daemon=True)
        t_err = threading.Thread(target=read_stream, args=(proc.stderr, "info"), daemon=True)
        t_out.start()
        t_err.start()
        proc.wait()
        t_out.join(timeout=1)
        t_err.join(timeout=1)
        if proc.returncode != 0:
            raise CommandExecutionError(f"Command failed with exit code {proc.returncode}")
    finally:
        if task_id and proc:
            process_registry.unregister(task_id)


def run_command(
    args: List[str],
    workdir: Path,
    conda_env: Optional[str] = None,
    log_callback: Optional[Callable[[str, str], None]] = None,
    task_id: str = "",
) -> None:
    workdir = Path(workdir)
    if not workdir.exists() or not workdir.is_dir():
        raise WorkspaceValidationError(f"Workspace directory does not exist: {workdir}")

    if not args:
        raise ExecutableNotFoundError("No executable provided")

    launch_args = list(args)
    if conda_env:
        launch_args = _resolve_conda_prefix(conda_env) + launch_args

    logger.info(
        "[ShellRunner] Executing in %s: %s",
        workdir,
        launch_args[:12] + ["..."] if len(launch_args) > 12 else launch_args,
    )

    if log_callback:
        _run_with_capture(launch_args, workdir, log_callback, task_id)
        return

    proc = None
    try:
        proc = subprocess.Popen(
            launch_args,
            cwd=workdir,
            env=_build_env(),
            shell=False,
        )
        if task_id and proc:
            process_registry.register(task_id, proc)
        proc.wait()
        if proc.returncode != 0:
            raise CommandExecutionError(f"Command failed with exit code {proc.returncode}")
    finally:
        if task_id and proc:
            process_registry.unregister(task_id)


def run_shell(
    cmd: str,
    workdir: Path,
    conda_env: Optional[str] = None,
    log_callback: Optional[Callable[[str, str], None]] = None,
    task_id: str = "",
) -> None:
    """
    Legacy compatibility wrapper for string commands.

    String command is tokenized then executed without shell expansion.
    """
    if not isinstance(cmd, str) or not cmd.strip():
        raise ExecutableNotFoundError("No executable provided")
    args = shlex.split(cmd, posix=not ON_WINDOWS)
    run_command(args=args, workdir=workdir, conda_env=conda_env, log_callback=log_callback, task_id=task_id)
