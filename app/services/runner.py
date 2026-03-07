"""
ExecutionManager: in-memory execution registry for API (get/stop).
Execution records are persisted in ExecutionStore; create/get/stop stay in sync.

Enhanced with workflow cancellation support through process registry integration.
"""
import logging
from typing import Dict, Optional, Set
from datetime import datetime

from app.services.execution_store import ExecutionStore
from app.core.executor.process_registry import process_registry

logger = logging.getLogger(__name__)


class Execution:
    """Execution 记录，追踪执行状态和运行中的节点"""

    def __init__(self, execution_id: str, workspace: str):
        self.id = execution_id
        self.workspace = workspace
        self.status = "pending"
        self.start_time: Optional[str] = None
        self.end_time: Optional[str] = None
        self.progress = 0
        self.logs: list[dict] = []
        # 追踪运行中的节点，用于取消操作
        self.running_nodes: Set[str] = set()

    def add_running_node(self, node_id: str) -> None:
        """添加运行中的节点"""
        self.running_nodes.add(node_id)
        logger.debug(f"[Execution] Added running node {node_id} to execution {self.id}")

    def remove_running_node(self, node_id: str) -> None:
        """移除已完成的节点"""
        self.running_nodes.discard(node_id)
        logger.debug(f"[Execution] Removed node {node_id} from execution {self.id}")

    def get_running_nodes(self) -> Set[str]:
        """获取运行中的节点列表"""
        return self.running_nodes.copy()


class ExecutionManager:
    """执行管理器 - 管理执行记录和取消操作"""

    def __init__(self):
        self.executions: Dict[str, Execution] = {}
        self.store = ExecutionStore()

    def create(
        self,
        execution_id: str,
        workspace: str,
        workflow_id: Optional[str] = None,
        persist: bool = True,
    ) -> Execution:
        ex = Execution(execution_id, workspace)
        self.executions[execution_id] = ex
        if persist:
            try:
                self.store.create(execution_id, workflow_id or "unknown", workspace)
            except Exception as e:
                raise
        return ex

    def get(self, execution_id: str) -> Optional[Execution]:
        return self.executions.get(execution_id)

    def update_status(
        self,
        execution_id: str,
        status: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        progress: Optional[int] = None,
    ) -> None:
        ex = self.executions.get(execution_id)
        if ex:
            ex.status = status
            if start_time is not None:
                ex.start_time = start_time
            if end_time is not None:
                ex.end_time = end_time
            if progress is not None:
                ex.progress = progress

    def register_node_start(self, execution_id: str, node_id: str) -> None:
        """注册节点开始执行"""
        ex = self.get(execution_id)
        if ex:
            ex.add_running_node(node_id)

    def register_node_complete(self, execution_id: str, node_id: str) -> None:
        """注册节点完成执行"""
        ex = self.get(execution_id)
        if ex:
            ex.remove_running_node(node_id)

    async def stop(self, execution_id: str) -> None:
        """
        停止执行。

        通过进程注册表取消所有运行中的节点，并更新数据库状态。

        Args:
            execution_id: 执行 ID
        """
        ex = self.get(execution_id)
        if not ex:
            logger.warning(f"[ExecutionManager] Cannot stop execution {execution_id}: not found")
            return

        # 检查执行状态
        if ex.status in ("completed", "failed", "cancelled"):
            logger.info(f"[ExecutionManager] Execution {execution_id} is already {ex.status}, skipping stop")
            return

        logger.info(f"[ExecutionManager] Stopping execution {execution_id}")

        # 获取运行中的节点
        running_nodes = ex.get_running_nodes()
        logger.info(f"[ExecutionManager] Found {len(running_nodes)} running nodes: {running_nodes}")

        # 取消所有运行中的节点
        cancelled_count = 0
        for node_id in running_nodes:
            task_id = f"{execution_id}:{node_id}"
            logger.info(f"[ExecutionManager] Cancelling task {task_id}")
            try:
                result = process_registry.cancel(task_id)
                if result:
                    cancelled_count += 1
                    logger.info(f"[ExecutionManager] Successfully cancelled task {task_id}")
                else:
                    logger.warning(f"[ExecutionManager] Failed to cancel task {task_id} (not found in registry)")
            except Exception as e:
                logger.error(f"[ExecutionManager] Error cancelling task {task_id}: {e}")

        # 更新执行状态
        ex.status = "cancelled"
        ex.end_time = datetime.utcnow().isoformat() + "Z"
        ex.logs.append({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": "warning",
            "message": f"Execution cancelled. Cancelled {cancelled_count} running nodes.",
        })

        # 更新数据库状态
        try:
            self.store.finish(execution_id, "cancelled")

            # 更新所有运行中的节点状态为 cancelled
            for node_id in running_nodes:
                try:
                    self.store.update_node_status(execution_id, node_id, "cancelled")
                except Exception as e:
                    logger.error(f"[ExecutionManager] Error updating node {node_id} status: {e}")

            logger.info(f"[ExecutionManager] Updated database status for execution {execution_id}")
        except Exception as e:
            logger.error(f"[ExecutionManager] Error updating database status for execution {execution_id}: {e}")

    def cleanup(self, execution_id: str) -> None:
        """
        清理执行记录。

        在执行完成后调用，移除内存中的执行记录。

        Args:
            execution_id: 执行 ID
        """
        if execution_id in self.executions:
            ex = self.executions.pop(execution_id)
            logger.info(f"[ExecutionManager] Cleaned up execution {execution_id}")
        else:
            logger.warning(f"[ExecutionManager] Execution {execution_id} not found for cleanup")


execution_manager = ExecutionManager()
