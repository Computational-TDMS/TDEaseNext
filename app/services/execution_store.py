import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from uuid import uuid4
from app.database.init_db import get_database_connection
from app.core.time_utils import utc_now_iso_z

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
        sample_id: Optional[str] = None,
        workflow_snapshot: Optional[str] = None
    ) -> None:
        """
        Create execution record.

        Args:
            execution_id: Execution ID
            workflow_id: Workflow ID
            workspace_path: Workspace directory path
            sample_id: Sample ID (optional)
            workflow_snapshot: JSON string of workflow structure snapshot (only saved on structure changes)
        """
        now = utc_now_iso_z()
        workspace_id = Path(workspace_path).name if workspace_path else "default_workspace"
        with self._conn() as conn:
            try:
                try:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO executions
                        (id, user_id, workspace_id, workflow_id, sample_id, status, start_time, end_time, engine_args, config_overrides, environment, workspace_path, workflow_snapshot, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            execution_id,
                            "default_user",
                            workspace_id,
                            workflow_id,
                            sample_id,
                            "pending",
                            now,
                            None,
                            None,
                            None,
                            None,
                            workspace_path,
                            workflow_snapshot,
                            now,
                        ),
                    )
                except sqlite3.OperationalError:
                    # Backward compatibility for old schema without user/workspace columns
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO executions
                        (id, workflow_id, sample_id, status, start_time, end_time, engine_args, config_overrides, environment, workspace_path, workflow_snapshot, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (execution_id, workflow_id, sample_id, "pending", now, None, None, None, None, workspace_path, workflow_snapshot, now),
                    )
                conn.commit()
            except Exception as e:
                raise

    def start(self, execution_id: str) -> None:
        now = utc_now_iso_z()
        with self._conn() as conn:
            conn.execute(
                "UPDATE executions SET status=?, start_time=? WHERE id=?",
                ("running", now, execution_id),
            )
            conn.commit()

    def finish(self, execution_id: str, status: str) -> None:
        now = utc_now_iso_z()
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
        now = utc_now_iso_z()
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
        now = utc_now_iso_z()
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

    def update_node_command_trace(
        self,
        execution_id: str,
        node_id: str,
        command_trace: Dict[str, Any],
    ) -> None:
        """
        Persist node command assembly trace JSON.

        Args:
            execution_id: Execution ID
            node_id: Frontend node ID
            command_trace: Structured command trace payload
        """
        payload = json.dumps(command_trace, ensure_ascii=False)
        with self._conn() as conn:
            conn.execute(
                "UPDATE execution_nodes SET command_trace=? WHERE execution_id=? AND node_id=?",
                (payload, execution_id, node_id),
            )
            conn.commit()

    def get_latest_completed_execution(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent completed execution for a workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Execution record with metadata or None if no completed execution found
        """
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT id, workflow_id, sample_id, status, start_time, end_time, workspace_path
                FROM executions
                WHERE workflow_id = ? AND status = 'completed'
                ORDER BY end_time DESC
                LIMIT 1
                """,
                (workflow_id,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "id": row["id"],
                    "workflow_id": row["workflow_id"],
                    "sample_id": row["sample_id"],
                    "status": row["status"],
                    "start_time": row["start_time"],
                    "end_time": row["end_time"],
                    "workspace_path": row["workspace_path"]
                }
            return None
