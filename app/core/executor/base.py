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
    input_paths: List[Path]  # 保持向后兼容，按 positional 顺序排列
    output_paths: List[Path]
    workspace_path: Path
    input_files: Optional[Dict[str, Path]] = None  # port_id -> Path 映射，支持所有输入端口（包括 flag 和 positional）
    conda_env: Optional[str] = None
    cmd: Optional[str] = None
    log_callback: Optional[Callable[[str, str], None]] = None  # (message, level) -> None
    task_id: str = ""  # 任务标识符，格式为 {execution_id}:{node_id}，用于进程追踪和取消


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
