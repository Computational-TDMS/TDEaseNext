import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4
from app.database.init_db import get_database_connection

class ExecutionStore:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or "data/tdease.db"

    def _conn(self) -> sqlite3.Connection:
        return get_database_connection(self.db_path)

    def create(
        self,
        execution_id: str,
        workflow_id: str,
        workspace_path: str,
        workflow_snapshot: Optional[str] = None
    ) -> None:
        """
        Create execution record.
        
        Args:
            execution_id: Execution ID
            workflow_id: Workflow ID
            workspace_path: Workspace directory path
            workflow_snapshot: JSON string of workflow structure snapshot (only saved on structure changes)
        """
        now = datetime.utcnow().isoformat() + "Z"
        with self._conn() as conn:
            try:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO executions
                    (id, workflow_id, status, start_time, end_time, engine_args, config_overrides, environment, workspace_path, workflow_snapshot, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (execution_id, workflow_id, "pending", now, None, None, None, None, workspace_path, workflow_snapshot, now),
                )
                conn.commit()
            except Exception as e:
                raise

    def start(self, execution_id: str) -> None:
        now = datetime.utcnow().isoformat() + "Z"
        with self._conn() as conn:
            conn.execute(
                "UPDATE executions SET status=?, start_time=? WHERE id=?",
                ("running", now, execution_id),
            )
            conn.commit()

    def finish(self, execution_id: str, status: str) -> None:
        now = datetime.utcnow().isoformat() + "Z"
        with self._conn() as conn:
            conn.execute(
                "UPDATE executions SET status=?, end_time=? WHERE id=?",
                (status, now, execution_id),
            )
            conn.commit()
    
    def create_node(
        self,
        execution_id: str,
        node_id: str,
        rule_name: Optional[str] = None
    ) -> str:
        """
        Create execution node record.

        Args:
            execution_id: Execution ID
            node_id: Frontend node ID
            rule_name: Engine rule name (optional)

        Returns:
            Node record ID
        """
        node_record_id = str(uuid4())
        now = datetime.utcnow().isoformat() + "Z"
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO execution_nodes
                (id, execution_id, node_id, rule_name, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (node_record_id, execution_id, node_id, rule_name, "pending", now),
            )
            conn.commit()
        return node_record_id
    
    def update_node_status(
        self,
        execution_id: str,
        node_id: str,
        status: str,
        progress: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Update node execution status.
        
        Args:
            execution_id: Execution ID
            node_id: Frontend node ID
            status: New status (pending, running, completed, failed)
            progress: Progress percentage (0-100)
            error_message: Error message if failed
        """
        now = datetime.utcnow().isoformat() + "Z"
        updates = ["status=?"]
        values = [status]
        
        if status == "running":
            updates.append("start_time=?")
            values.append(now)
        elif status in ("completed", "failed", "cancelled"):
            updates.append("end_time=?")
            values.append(now)
        
        if progress is not None:
            updates.append("progress=?")
            values.append(progress)
        
        if error_message:
            updates.append("error_message=?")
            values.append(error_message)
        
        values.extend([execution_id, node_id])
        
        with self._conn() as conn:
            conn.execute(
                f"UPDATE execution_nodes SET {', '.join(updates)} WHERE execution_id=? AND node_id=?",
                values
            )
            conn.commit()
    
    def get_nodes(self, execution_id: str) -> List[Dict[str, Any]]:
        """
        Get all nodes for an execution.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            List of node records
        """
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM execution_nodes WHERE execution_id=? ORDER BY created_at",
                (execution_id,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_node(self, execution_id: str, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific node record.
        
        Args:
            execution_id: Execution ID
            node_id: Frontend node ID
            
        Returns:
            Node record or None
        """
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM execution_nodes WHERE execution_id=? AND node_id=?",
                (execution_id, node_id)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
