"""
ExecutionManager: in-memory execution registry for API (get/stop).
Execution records are persisted in ExecutionStore; create/get/stop stay in sync.
"""
import logging
from typing import Dict, Optional
from datetime import datetime

from app.services.execution_store import ExecutionStore

logger = logging.getLogger(__name__)


class Execution:
    def __init__(self, execution_id: str, workspace: str):
        self.id = execution_id
        self.workspace = workspace
        self.status = "pending"
        self.start_time: Optional[str] = None
        self.end_time: Optional[str] = None
        self.progress = 0
        self.logs: list[dict] = []


class ExecutionManager:
    def __init__(self):
        self.executions: Dict[str, Execution] = {}
        self.store = ExecutionStore()

    def create(
        self,
        execution_id: str,
        workspace: str,
        workflow_id: Optional[str] = None,
    ) -> Execution:
        ex = Execution(execution_id, workspace)
        self.executions[execution_id] = ex
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

    async def stop(self, execution_id: str) -> None:
        ex = self.get(execution_id)
        if not ex:
            return
        ex.status = "cancelled"
        ex.end_time = datetime.utcnow().isoformat() + "Z"
        ex.logs.append({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": "warning",
            "message": "Execution cancelled",
        })


execution_manager = ExecutionManager()
