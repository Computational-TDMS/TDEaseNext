"""
Process Registry - 进程注册表

管理运行中的子进程，支持进程注册、注销和取消操作。
使用 threading.Lock 保证线程安全，支持并发执行。
"""
import logging
import subprocess
import threading
import time
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ProcessRegistry:
    """
    全局进程注册表，用于追踪运行中的子进程。

    维护 task_id -> subprocess.Popen 映射，提供进程注册、注销、查询和取消功能。
    所有操作都是线程安全的，使用 threading.Lock 保护内部状态。
    """

    _instance: Optional['ProcessRegistry'] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> 'ProcessRegistry':
        """单例模式，确保全局唯一的进程注册表"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """初始化进程注册表"""
        if self._initialized:
            return

        self._registry: Dict[str, subprocess.Popen] = {}
        self._mutex = threading.Lock()
        self._initialized = True
        logger.info("[ProcessRegistry] Initialized process registry")

    def register(self, task_id: str, process: subprocess.Popen) -> None:
        """
        注册一个运行中的进程。

        Args:
            task_id: 任务标识符，格式为 {execution_id}:{node_id}
            process: subprocess.Popen 对象

        Raises:
            ValueError: 如果 task_id 已存在或 process 为 None
        """
        if not task_id:
            raise ValueError("task_id cannot be empty")
        if not process:
            raise ValueError("process cannot be None")

        with self._mutex:
            if task_id in self._registry:
                logger.warning(f"[ProcessRegistry] task_id {task_id} already registered, overwriting")

            self._registry[task_id] = process
            logger.info(f"[ProcessRegistry] Registered process for task_id={task_id}, pid={process.pid}")

    def unregister(self, task_id: str) -> None:
        """
        注销一个进程。

        如果 task_id 不存在，静默忽略（避免双重注销导致异常）。

        Args:
            task_id: 任务标识符
        """
        with self._mutex:
            if task_id in self._registry:
                process = self._registry.pop(task_id)
                logger.info(f"[ProcessRegistry] Unregistered process for task_id={task_id}, pid={process.pid if process else 'N/A'}")
            else:
                # 静默忽略，避免双重注销导致异常
                logger.debug(f"[ProcessRegistry] task_id {task_id} not found in registry (already unregistered?)")

    def get(self, task_id: str) -> Optional[subprocess.Popen]:
        """
        获取指定 task_id 的进程对象。

        Args:
            task_id: 任务标识符

        Returns:
            subprocess.Popen 对象，如果不存在返回 None
        """
        with self._mutex:
            return self._registry.get(task_id)

    def cancel(self, task_id: str, timeout: int = 3) -> bool:
        """
        取消指定 task_id 的进程。

        使用两阶段终止策略：
        1. 先调用 process.terminate() (SIGTERM)，允许进程优雅退出
        2. 等待 timeout 秒（默认 3 秒）
        3. 如果进程仍在运行，调用 process.kill() (SIGKILL) 强制终止

        Args:
            task_id: 任务标识符
            timeout: 等待进程退出的超时时间（秒）

        Returns:
            bool: 如果进程成功终止（或已退出）返回 True，如果进程不存在返回 False
        """
        with self._mutex:
            process = self._registry.get(task_id)
            if not process:
                logger.warning(f"[ProcessRegistry] Cannot cancel task_id={task_id}: not found in registry")
                return False

        # 检查进程是否已退出
        poll_result = process.poll()
        if poll_result is not None:
            logger.info(f"[ProcessRegistry] Process for task_id={task_id} already exited (exit code={poll_result})")
            # 进程已退出，但仍需从注册表移除
            self.unregister(task_id)
            return True

        # 第一阶段：优雅终止 (SIGTERM)
        logger.info(f"[ProcessRegistry] Terminating process for task_id={task_id}, pid={process.pid}")
        process.terminate()

        # 等待进程退出
        try:
            process.wait(timeout=timeout)
            logger.info(f"[ProcessRegistry] Process for task_id={task_id} terminated gracefully")
            self.unregister(task_id)
            return True
        except subprocess.TimeoutExpired:
            # 第二阶段：强制终止 (SIGKILL)
            logger.warning(f"[ProcessRegistry] Process for task_id={task_id} did not exit after {timeout}s, killing")
            process.kill()
            process.wait(timeout=1)  # kill 后再等 1 秒
            logger.info(f"[ProcessRegistry] Process for task_id={task_id} killed")
            self.unregister(task_id)
            return True

    def list_active(self) -> List[str]:
        """
        列出所有活跃的 task_id。

        Returns:
            活跃的 task_id 列表
        """
        with self._mutex:
            # 清理已退出的进程
            active_tasks = []
            for task_id, process in list(self._registry.items()):
                if process.poll() is None:
                    active_tasks.append(task_id)
                else:
                    # 进程已退出，自动清理
                    logger.debug(f"[ProcessRegistry] Cleaning up dead process for task_id={task_id}")
                    del self._registry[task_id]

            return active_tasks

    def clear(self) -> None:
        """
        清空注册表。主要用于测试场景。

        警告：此操作不会终止进程，只是清空注册表。
        """
        with self._mutex:
            self._registry.clear()
            logger.info("[ProcessRegistry] Cleared process registry")


# 全局单例实例
process_registry = ProcessRegistry()
