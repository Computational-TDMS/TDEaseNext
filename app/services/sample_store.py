"""
Sample Store - Database-backed sample storage management
"""
import json
import sqlite3
import logging
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from app.database.init_db import get_database_connection

logger = logging.getLogger(__name__)


class SampleValidationError(Exception):
    """Raised when sample data validation fails"""
    pass


def validate_sample_id(sample_id: str) -> bool:
    """Validate sample ID format"""
    if not sample_id:
        return False
    if len(sample_id) > 128:
        return False
    # Allow alphanumeric, underscore, hyphen
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', sample_id))


def validate_sample_data(sample_data: Dict[str, Any]) -> None:
    """Validate sample data before saving

    Raises:
        SampleValidationError: If validation fails
    """
    required_fields = ["user_id", "workspace_id", "name", "context", "data_paths"]
    missing_fields = []

    for field in required_fields:
        if field not in sample_data or not sample_data[field]:
            missing_fields.append(field)

    if missing_fields:
        raise SampleValidationError(f"Missing required fields: {missing_fields}")

    # Validate user_id and workspace_id format
    user_id = sample_data.get("user_id", "")
    workspace_id = sample_data.get("workspace_id", "")
    if not isinstance(user_id, str) or len(user_id) > 128:
        raise SampleValidationError("Invalid user_id format")
    if not isinstance(workspace_id, str) or len(workspace_id) > 128:
        raise SampleValidationError("Invalid workspace_id format")

    # Validate name
    name = sample_data.get("name", "")
    if not isinstance(name, str) or len(name) > 256:
        raise SampleValidationError("Invalid name format or length")

    # Validate context and data_paths are dictionaries
    if not isinstance(sample_data.get("context"), dict):
        raise SampleValidationError("context must be a dictionary")

    if not isinstance(sample_data.get("data_paths"), dict):
        raise SampleValidationError("data_paths must be a dictionary")


class SampleStore:
    """Database-backed sample storage management"""

    # Default limits
    DEFAULT_LIST_LIMIT = 100
    DEFAULT_SEARCH_LIMIT = 50

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or "data/tdease.db"

    def _conn(self) -> sqlite3.Connection:
        return get_database_connection(self.db_path)

    def _row_to_sample_dict(self, row) -> Dict[str, Any]:
        """Convert database row to sample dictionary

        IMPORTANT: All SELECT queries must explicitly specify columns in this order:
            id, user_id, workspace_id, name, description, context, data_paths, metadata, created_at, updated_at

        The SELECT statement's column order (not the table's physical order) determines the row format.

        Args:
            row: Database row from samples table

        Returns:
            Sample dictionary

        Raises:
            JSONDecodeError: If JSON fields are malformed
        """
        try:
            context = json.loads(row[5]) if row[5] else {}
            data_paths = json.loads(row[6]) if row[6] else {}
            metadata = json.loads(row[7]) if row[7] else {}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON for sample {row[0]}: {e}")
            raise

        return {
            "id": row[0],
            "user_id": row[1],
            "workspace_id": row[2],
            "name": row[3],
            "description": row[4],
            "context": context,
            "data_paths": data_paths,
            "metadata": metadata,
            "created_at": row[8],
            "updated_at": row[9]
        }

    def get(self, sample_id: str) -> Optional[Dict[str, Any]]:
        """Get sample by ID

        Args:
            sample_id: Sample identifier

        Returns:
            Sample dictionary if found, None otherwise
        """
        with self._conn() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, user_id, workspace_id, name, description, context, data_paths, metadata, created_at, updated_at
                FROM samples WHERE id = ?
            """, (sample_id,))

            row = cursor.fetchone()
            if not row:
                return None

            try:
                return self._row_to_sample_dict(row)
            except json.JSONDecodeError:
                return None

    def save(self, sample_id: str, sample_data: Dict[str, Any]) -> bool:
        """Save or update sample

        Args:
            sample_id: Unique sample identifier
            sample_data: Sample data dictionary

        Returns:
            True if successful, False otherwise

        Raises:
            SampleValidationError: If sample data validation fails
        """
        # Validate sample_id
        if not validate_sample_id(sample_id):
            logger.error(f"Invalid sample_id format: {sample_id}")
            raise SampleValidationError(f"Invalid sample_id format: {sample_id}")

        # Validate sample data
        validate_sample_data(sample_data)

        try:
            with self._conn() as conn:
                cursor = conn.cursor()

                now = datetime.utcnow().isoformat() + "Z"

                cursor.execute("SELECT id FROM samples WHERE id = ?", (sample_id,))
                exists = cursor.fetchone() is not None

                if exists:
                    cursor.execute("""
                        UPDATE samples SET
                            user_id = ?, workspace_id = ?, name = ?, description = ?,
                            context = ?, data_paths = ?, metadata = ?, updated_at = ?
                        WHERE id = ?
                    """, (
                        sample_data.get("user_id", ""),
                        sample_data.get("workspace_id", ""),
                        sample_data.get("name", ""),
                        sample_data.get("description", ""),
                        json.dumps(sample_data.get("context", {}), ensure_ascii=False),
                        json.dumps(sample_data.get("data_paths", {}), ensure_ascii=False),
                        json.dumps(sample_data.get("metadata", {}), ensure_ascii=False),
                        now,
                        sample_id
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO samples (
                            id, user_id, workspace_id, name, description, context, data_paths, metadata, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        sample_id,
                        sample_data.get("user_id", ""),
                        sample_data.get("workspace_id", ""),
                        sample_data.get("name", ""),
                        sample_data.get("description", ""),
                        json.dumps(sample_data.get("context", {}), ensure_ascii=False),
                        json.dumps(sample_data.get("data_paths", {}), ensure_ascii=False),
                        json.dumps(sample_data.get("metadata", {}), ensure_ascii=False),
                        now,
                        now
                    ))

                conn.commit()
                return True

        except SampleValidationError:
            raise
        except sqlite3.IntegrityError as e:
            logger.error(f"Integrity error saving sample {sample_id}: {e}")
            raise
        except sqlite3.DatabaseError as e:
            logger.error(f"Database error saving sample {sample_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error saving sample {sample_id}: {e}")
            return False

    def delete(self, sample_id: str) -> bool:
        """Delete sample by ID

        Args:
            sample_id: Sample identifier

        Returns:
            True if sample was deleted, False if not found

        Raises:
            SampleValidationError: If sample_id format is invalid
            RuntimeError: If database operation fails
        """
        if not validate_sample_id(sample_id):
            raise SampleValidationError(f"Invalid sample_id format: {sample_id}")

        try:
            with self._conn() as conn:
                cursor = conn.cursor()

                cursor.execute("DELETE FROM samples WHERE id = ?", (sample_id,))
                conn.commit()

                return cursor.rowcount > 0

        except sqlite3.DatabaseError as e:
            logger.error(f"Database error deleting sample {sample_id}: {e}")
            raise RuntimeError(f"Failed to delete sample {sample_id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error deleting sample {sample_id}: {e}")
            raise

    def list_by_workspace(self, workspace_id: str, limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        """List all samples in a workspace

        Args:
            workspace_id: Workspace identifier
            limit: Maximum samples to return (default: DEFAULT_LIST_LIMIT)
            offset: Number of samples to skip

        Returns:
            List of sample dictionaries
        """
        if limit is None:
            limit = self.DEFAULT_LIST_LIMIT

        with self._conn() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, user_id, workspace_id, name, description, context, data_paths, metadata, created_at, updated_at
                FROM samples
                WHERE workspace_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (workspace_id, limit, offset))

            samples = []
            for row in cursor.fetchall():
                try:
                    samples.append(self._row_to_sample_dict(row))
                except json.JSONDecodeError:
                    continue

            return samples

    def search(self, workspace_id: str, query: str, limit: int = None) -> List[Dict[str, Any]]:
        """Search samples by name or description

        Args:
            workspace_id: Workspace identifier
            query: Search query string
            limit: Maximum samples to return (default: DEFAULT_SEARCH_LIMIT)

        Returns:
            List of matching sample dictionaries
        """
        if limit is None:
            limit = self.DEFAULT_SEARCH_LIMIT

        with self._conn() as conn:
            cursor = conn.cursor()

            # Sanitize search query to prevent wildcard injection
            if "%" in query or "_" in query:
                logger.warning(f"Potentially malicious search pattern detected: {query}")
                # Escape special characters
                query = query.replace("%", "\\%").replace("_", "\\_")

            search_pattern = f"%{query}%"
            cursor.execute("""
                SELECT id, user_id, workspace_id, name, description, context, data_paths, metadata, created_at, updated_at
                FROM samples
                WHERE workspace_id = ? AND (name LIKE ? OR description LIKE ?)
                ORDER BY created_at DESC
                LIMIT ?
            """, (workspace_id, search_pattern, search_pattern, limit))

            samples = []
            for row in cursor.fetchall():
                try:
                    samples.append(self._row_to_sample_dict(row))
                except json.JSONDecodeError:
                    continue

            return samples

    def get_by_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get sample by execution_id

        Args:
            execution_id: Execution identifier

        Returns:
            Sample dictionary if found, None otherwise
        """
        with self._conn() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT s.id, s.user_id, s.workspace_id, s.name, s.description, s.context, s.data_paths, s.metadata, s.created_at, s.updated_at
                FROM samples s
                JOIN executions e ON s.id = e.sample_id
                WHERE e.id = ?
            """, (execution_id,))

            row = cursor.fetchone()
            if not row:
                return None

            try:
                return self._row_to_sample_dict(row)
            except json.JSONDecodeError:
                return None

    def list_executions(self, sample_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """List all executions for a sample"""
        conn = self._conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, workflow_id, status, start_time, end_time, workspace_path
            FROM executions
            WHERE sample_id = ?
            ORDER BY start_time DESC
            LIMIT ?
        """, (sample_id, limit))

        executions = []
        for row in cursor.fetchall():
            executions.append({
                "id": row[0],
                "workflow_id": row[1],
                "status": row[2],
                "start_time": row[3],
                "end_time": row[4],
                "workspace_path": row[5]
            })

        return executions


# Global instance
sample_store = SampleStore()
