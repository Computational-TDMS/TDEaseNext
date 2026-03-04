"""
MockExecutor - 模拟执行器

用于测试，记录任务但不实际执行 Shell 命令。
"""
from pathlib import Path
from typing import Any, Dict, List

from .base import Executor, TaskSpec


class MockExecutor(Executor):
    """模拟执行器：记录任务规格，不执行"""

    def __init__(self, tools_registry: dict):
        self.tools_registry = tools_registry
        self.executed_tasks: List[Dict[str, Any]] = []

    async def execute(self, spec: TaskSpec) -> None:
        self.executed_tasks.append({
            "node_id": spec.node_id,
            "tool_id": spec.tool_id,
            "params": spec.params,
            "input_paths": [str(p) for p in spec.input_paths],
            "output_paths": [str(p) for p in spec.output_paths],
            "workspace_path": str(spec.workspace_path),
        })

    async def cancel(self, task_id: str) -> bool:
        """模拟取消任务，始终返回 True"""
        return True
