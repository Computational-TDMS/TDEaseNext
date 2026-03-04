"""
Workflow Store - Unified workflow data storage management

This module provides a unified interface for storing and retrieving workflow data,
addressing the current architectural inconsistencies.
"""

import json
import sqlite3
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from app.database.init_db import get_database_connection


class WorkflowStore:
    """
    Unified workflow storage management.
    
    This class provides a consistent interface for storing and retrieving
    workflow data, addressing the current architectural inconsistencies.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize workflow store.
        
        Args:
            db_path: Path to SQLite database file (optional)
        """
        self.db_path = db_path or "data/tdease.db"
    
    def _conn(self) -> sqlite3.Connection:
        """Get database connection."""
        return get_database_connection(self.db_path)
    
    def get(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get workflow data by ID.

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow data dictionary or None if not found
        """
        conn = self._conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, user_id, workspace_id, name, description, vueflow_data, workspace_path,
                   status, created_at, updated_at, metadata, workflow_format, workflow_document
            FROM workflows WHERE id = ?
        """, (workflow_id,))

        row = cursor.fetchone()
        if not row:
            return None

        return {
            "id": row[0],
            "user_id": row[1],
            "workspace_id": row[2],
            "name": row[3],
            "description": row[4],
            "vueflow_data": json.loads(row[5]),
            "workspace_path": row[6],
            "status": row[7],
            "created_at": row[8],
            "updated_at": row[9],
            "metadata": json.loads(row[10]) if row[10] else {},
            "workflow_format": row[11],
            "workflow_document": row[12]
        }
    
    def save(self, workflow_id: str, workflow_data: Dict[str, Any]) -> bool:
        """
        Save workflow data.

        Args:
            workflow_id: Workflow ID
            workflow_data: Workflow data dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self._conn()
            cursor = conn.cursor()

            now = datetime.utcnow().isoformat() + "Z"

            # Check if workflow exists
            cursor.execute("SELECT id FROM workflows WHERE id = ?", (workflow_id,))
            exists = cursor.fetchone() is not None

            if exists:
                # Update existing workflow
                cursor.execute("""
                    UPDATE workflows SET
                        user_id = ?,
                        workspace_id = ?,
                        name = ?,
                        description = ?,
                        vueflow_data = ?,
                        workspace_path = ?,
                        status = ?,
                        updated_at = ?,
                        metadata = ?,
                        workflow_format = ?,
                        workflow_document = ?
                    WHERE id = ?
                """, (
                    workflow_data.get("user_id", "default_user"),
                    workflow_data.get("workspace_id", ""),
                    workflow_data.get("name", ""),
                    workflow_data.get("description", ""),
                    json.dumps(workflow_data.get("vueflow_data", {}), ensure_ascii=False),
                    workflow_data.get("workspace_path", ""),
                    workflow_data.get("status", "created"),
                    now,
                    json.dumps(workflow_data.get("metadata", {}), ensure_ascii=False),
                    workflow_data.get("workflow_format", "vueflow"),
                    workflow_data.get("workflow_document"),
                    workflow_id
                ))
            else:
                # Insert new workflow
                cursor.execute("""
                    INSERT INTO workflows (
                        id, user_id, workspace_id, name, description, vueflow_data, workspace_path,
                        status, created_at, updated_at, metadata, workflow_format, workflow_document
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    workflow_id,
                    workflow_data.get("user_id", "default_user"),
                    workflow_data.get("workspace_id", ""),
                    workflow_data.get("name", ""),
                    workflow_data.get("description", ""),
                    json.dumps(workflow_data.get("vueflow_data", {}), ensure_ascii=False),
                    workflow_data.get("workspace_path", ""),
                    workflow_data.get("status", "created"),
                    now,
                    now,
                    json.dumps(workflow_data.get("metadata", {}), ensure_ascii=False),
                    workflow_data.get("workflow_format", "vueflow"),
                    workflow_data.get("workflow_document")
                ))

            conn.commit()
            return True

        except Exception as e:
            print(f"Error saving workflow {workflow_id}: {e}")
            return False
    
    def delete(self, workflow_id: str) -> bool:
        """
        Delete workflow by ID.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self._conn()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM workflows WHERE id = ?", (workflow_id,))
            conn.commit()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            print(f"Error deleting workflow {workflow_id}: {e}")
            return False
    
    def list(self, user_id: Optional[str] = None, workspace_id: Optional[str] = None,
             limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List workflows with optional user/workspace filtering.

        Args:
            user_id: Filter by user ID (optional)
            workspace_id: Filter by workspace ID (optional)
            limit: Maximum number of workflows to return
            offset: Offset for pagination

        Returns:
            List of workflow data dictionaries
        """
        conn = self._conn()
        cursor = conn.cursor()

        if user_id and workspace_id:
            cursor.execute("""
                SELECT id, user_id, workspace_id, name, description, vueflow_data, workspace_path,
                       status, created_at, updated_at, metadata, workflow_format
                FROM workflows
                WHERE user_id = ? AND workspace_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (user_id, workspace_id, limit, offset))
        elif user_id:
            cursor.execute("""
                SELECT id, user_id, workspace_id, name, description, vueflow_data, workspace_path,
                       status, created_at, updated_at, metadata, workflow_format
                FROM workflows
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (user_id, limit, offset))
        else:
            cursor.execute("""
                SELECT id, user_id, workspace_id, name, description, vueflow_data, workspace_path,
                       status, created_at, updated_at, metadata, workflow_format
                FROM workflows
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))

        workflows = []
        for row in cursor.fetchall():
            workflows.append({
                "id": row[0],
                "user_id": row[1],
                "workspace_id": row[2],
                "name": row[3],
                "description": row[4],
                "vueflow_data": json.loads(row[5]),
                "workspace_path": row[6],
                "status": row[7],
                "created_at": row[8],
                "updated_at": row[9],
                "metadata": json.loads(row[10]) if row[10] else {},
                "workflow_format": row[11]
            })

        return workflows

    def count(self, user_id: Optional[str] = None, workspace_id: Optional[str] = None) -> int:
        """
        Get total number of workflows.

        Returns:
            Number of workflows
        """
        conn = self._conn()
        cursor = conn.cursor()

        if user_id and workspace_id:
            cursor.execute("SELECT COUNT(*) FROM workflows WHERE user_id = ? AND workspace_id = ?",
                         (user_id, workspace_id))
        elif user_id:
            cursor.execute("SELECT COUNT(*) FROM workflows WHERE user_id = ?", (user_id,))
        else:
            cursor.execute("SELECT COUNT(*) FROM workflows")
        return cursor.fetchone()[0]

    def search(self, query: str, user_id: Optional[str] = None,
               workspace_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search workflows by name or description.

        Args:
            query: Search query
            user_id: Filter by user ID (optional)
            workspace_id: Filter by workspace ID (optional)
            limit: Maximum number of results

        Returns:
            List of matching workflow data dictionaries
        """
        conn = self._conn()
        cursor = conn.cursor()

        search_pattern = f"%{query}%"

        if user_id and workspace_id:
            cursor.execute("""
                SELECT id, user_id, workspace_id, name, description, vueflow_data, workspace_path,
                       status, created_at, updated_at, metadata, workflow_format
                FROM workflows
                WHERE user_id = ? AND workspace_id = ? AND (name LIKE ? OR description LIKE ?)
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, workspace_id, search_pattern, search_pattern, limit))
        elif user_id:
            cursor.execute("""
                SELECT id, user_id, workspace_id, name, description, vueflow_data, workspace_path,
                       status, created_at, updated_at, metadata, workflow_format
                FROM workflows
                WHERE user_id = ? AND (name LIKE ? OR description LIKE ?)
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, search_pattern, search_pattern, limit))
        else:
            cursor.execute("""
                SELECT id, user_id, workspace_id, name, description, vueflow_data, workspace_path,
                       status, created_at, updated_at, metadata, workflow_format
                FROM workflows
                WHERE name LIKE ? OR description LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (search_pattern, search_pattern, limit))

        workflows = []
        for row in cursor.fetchall():
            workflows.append({
                "id": row[0],
                "user_id": row[1],
                "workspace_id": row[2],
                "name": row[3],
                "description": row[4],
                "vueflow_data": json.loads(row[5]),
                "workspace_path": row[6],
                "status": row[7],
                "created_at": row[8],
                "updated_at": row[9],
                "metadata": json.loads(row[10]) if row[10] else {},
                "workflow_format": row[11]
            })

        return workflows

    def list_by_workspace(self, user_id: str, workspace_id: str,
                         limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List workflows for a specific user workspace.

        Args:
            user_id: User ID
            workspace_id: Workspace ID
            limit: Maximum workflows to return
            offset: Offset for pagination

        Returns:
            List of workflow data dictionaries
        """
        return self.list(user_id=user_id, workspace_id=workspace_id, limit=limit, offset=offset)


# Global instance for easy access
workflow_store = WorkflowStore()
