"""
Executor interface - 执行器抽象

定义标准接口：submit, cancel, get_status
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


@dataclass
class TaskSpec:
    """单次任务规格"""

    node_id: str
    tool_id: str
    params: Dict[str, Any]
    input_paths: List[Path]
    output_paths: List[Path]
    workspace_path: Path
    conda_env: Optional[str] = None
    cmd: Optional[str] = None
    log_callback: Optional[Callable[[str, str], None]] = None  # (message, level) -> None


class Executor(ABC):
    """执行器抽象基类"""

    @abstractmethod
    async def execute(self, spec: TaskSpec) -> None:
        """执行任务"""
        pass

    @abstractmethod
    async def cancel(self, task_id: str) -> bool:
        """取消任务"""
        pass
