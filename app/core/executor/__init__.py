"""Executor adapters - local and remote task execution."""

from .base import TaskSpec, Executor
from .local import LocalExecutor
from .mock import MockExecutor

__all__ = ["TaskSpec", "Executor", "LocalExecutor", "MockExecutor"]
