"""
Engine Adapter - Legacy adapter for external workflow execution systems

This module contains optional adapters for external workflow systems.
The main FlowEngine path uses LocalExecutor + ShellRunner directly.

The SnakemakeCLIAdapter is kept for reference/compatibility but is NOT used
by the main FlowEngine execution path. It was part of the pre-migration architecture
when the system depended on Snakemake for workflow execution.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional, List


class EngineAdapter:
    """Base class for engine adapters (for future extensions)"""
    pass


class SnakemakeCLIAdapter(EngineAdapter):
    """
    Legacy Snakemake CLI adapter (DEPRECATED - NOT USED)

    This adapter was used for Snakefile-based execution before the FlowEngine migration.
    It is NOT used by the current execution path (FlowEngine + LocalExecutor + ShellRunner).

    Kept for reference only. Remove entirely if no legacy workflows need Snakemake support.
    """
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = project_root or str(Path(__file__).resolve().parents[2])

    def _build_cmd(self, cores: int, use_conda: bool) -> List[str]:
        cmd = [
            sys.executable,
            "-m", "snakemake",
            "--snakefile", "Snakefile",
            "--configfile", "config.yaml",
            "--cores", str(cores),
        ]
        if use_conda:
            cmd += [
                "--use-conda",
                "--conda-frontend",
                "conda",
                "--conda-prefix",
                ".snakemake/conda",
            ]
        return cmd

    async def spawn(self, workspace: str, cores: int = 4, use_conda: bool = True) -> asyncio.subprocess.Process:
        """Spawn Snakemake process (legacy method, not used by FlowEngine)"""
        cmd = self._build_cmd(cores, use_conda)
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{self.project_root}:{env.get('PYTHONPATH','')}"
        return await asyncio.create_subprocess_exec(
            *cmd,
            cwd=workspace,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=env,
        )


# Note: Snakemake 已解耦。当前执行路径: FlowEngine + LocalExecutor + ShellRunner。
# The SnakemakeCLIAdapter above is kept for reference only and is NOT used.

