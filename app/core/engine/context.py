"""
ExecutionContext - 执行上下文

承载工作空间路径、样本上下文、执行参数等。
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Optional


@dataclass
class ExecutionContext:
    """单次工作流执行的上下文"""

    workspace_path: Path
    sample_context: Dict[str, str] = field(default_factory=dict)
    config_overrides: Dict[str, Any] = field(default_factory=dict)
    dryrun: bool = False
    resume: bool = False
    execution_id: Optional[str] = None
    workflow_id: Optional[str] = None
    log_callback: Optional[Callable[[str, str], None]] = None  # (message, level) -> None

    def resolve_path(self, rel_path: str) -> Path:
        """将相对路径解析为工作空间内的绝对路径"""
        return (self.workspace_path / rel_path).resolve()
