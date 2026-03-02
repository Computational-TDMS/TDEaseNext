"""
FastAPI Dependency Injection
Shared services and configuration management
"""

import os
import yaml
from pathlib import Path
from typing import Generator, Optional
import sqlite3
import logging

# Try to import FastAPI components, but handle gracefully for core functionality tests
try:
    from fastapi import Depends, HTTPException, status
    from app.models.common import APIError
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

    # Define fallback constants for core functionality
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str):
            self.status_code = status_code
            self.detail = detail
            super().__init__(detail)

    class status:
        HTTP_400_BAD_REQUEST = 400
        HTTP_403_FORBIDDEN = 403
        HTTP_404_NOT_FOUND = 404
        HTTP_409_CONFLICT = 409
        HTTP_500_INTERNAL_SERVER_ERROR = 500
        HTTP_507_INSUFFICIENT_STORAGE = 507

    def Depends(dependency):
        """Fallback Depends function for core functionality"""
        return dependency

# Re-export status codes for convenience
if FASTAPI_AVAILABLE:
    HTTP_400_BAD_REQUEST = status.HTTP_400_BAD_REQUEST
    HTTP_403_FORBIDDEN = status.HTTP_403_FORBIDDEN
    HTTP_404_NOT_FOUND = status.HTTP_404_NOT_FOUND
    HTTP_409_CONFLICT = status.HTTP_409_CONFLICT
    HTTP_500_INTERNAL_SERVER_ERROR = status.HTTP_500_INTERNAL_SERVER_ERROR
    HTTP_507_INSUFFICIENT_STORAGE = status.HTTP_507_INSUFFICIENT_STORAGE
else:
    HTTP_400_BAD_REQUEST = status.HTTP_400_BAD_REQUEST
    HTTP_403_FORBIDDEN = status.HTTP_403_FORBIDDEN
    HTTP_404_NOT_FOUND = status.HTTP_404_NOT_FOUND
    HTTP_409_CONFLICT = status.HTTP_409_CONFLICT
    HTTP_500_INTERNAL_SERVER_ERROR = status.HTTP_500_INTERNAL_SERVER_ERROR
    HTTP_507_INSUFFICIENT_STORAGE = status.HTTP_507_INSUFFICIENT_STORAGE

logger = logging.getLogger(__name__)

# Global configuration cache
_config_cache: Optional[dict] = None


class Config:
    """Configuration management class"""

    def __init__(self, config_path: str = "config/app_config.yaml"):
        self.config_path = Path(config_path)
        self._config = None
        self._load_config()

    def _load_config(self):
        """Load configuration from YAML file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f)
            else:
                logger.warning(f"Config file not found: {self.config_path}, using defaults")
                self._config = self._get_default_config()
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self._config = self._get_default_config()

    def _get_default_config(self) -> dict:
        """Get default configuration"""
        return {
            "app": {
                "name": "TDEase",
                "version": "1.0.0",
                "host": "0.0.0.0",
                "port": 8000,
                "debug": False
            },
            "database": {
                "type": "sqlite",
                "path": "data/tdease.db"
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        }

    def get(self, key: str, default=None):
        """Get configuration value using dot notation"""
        if not self._config:
            self._load_config()

        keys = key.split('.')
        value = self._config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def reload(self):
        """Reload configuration from file"""
        self._load_config()


# Global config instance
config = Config()


def get_config() -> Config:
    """Dependency to get configuration"""
    return config


# Global database instance
_db_connection: Optional[sqlite3.Connection] = None


def get_database() -> sqlite3.Connection:
    """Dependency to get database connection"""
    global _db_connection

    if _db_connection is None:
        # Import database initializer
        from app.database.init_db import get_database_connection as get_conn

        db_path = config.get("database.path", "data/tdease.db")
        _db_connection = get_conn(db_path)

    return _db_connection


def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Dependency to get database connection (auto-closing)"""
    conn = get_database()
    try:
        yield conn
    finally:
        # Don't close the shared connection, just release it
        pass


# Tool registry import (lazy loading to avoid circular imports)
_tool_registry = None
_workflow_service = None


def get_workflow_service():
    """Dependency to get WorkflowService (TDEase 2.0 engine)"""
    global _workflow_service
    if _workflow_service is None:
        from app.services.workflow_service import WorkflowService
        from app.services.execution_store import ExecutionStore
        from app.services.tool_registry import get_tool_registry as _get_app_tool_registry
        reg = _get_app_tool_registry()
        store = ExecutionStore()
        _workflow_service = WorkflowService(tool_registry=reg, execution_store=store)
    return _workflow_service


def get_tool_registry():
    """Dependency to get tool registry instance"""
    global _tool_registry
    if _tool_registry is None:
        from app.services.tool_registry import get_tool_registry as _get_app_tool_registry
        _tool_registry = _get_app_tool_registry()
    return _tool_registry


def validate_workspace_path(workspace_path: str) -> str:
    """Validate and normalize workspace path"""
    if not workspace_path or workspace_path.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace path is required"
        )

    # Normalize path
    normalized_path = os.path.abspath(workspace_path.strip())

    # Check if parent directory exists and is writable
    parent_dir = os.path.dirname(normalized_path)
    if not os.path.exists(parent_dir):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Parent directory does not exist: {parent_dir}"
        )

    if not os.access(parent_dir, os.W_OK):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Parent directory is not writable: {parent_dir}"
        )

    return normalized_path


def get_workspace_dir(workspace_path: str = Depends(validate_workspace_path)) -> str:
    """Dependency to get validated workspace directory"""
    return workspace_path


class ErrorHandler:
    """Error handling utilities"""

    @staticmethod
    def handle_database_error(error: Exception) -> HTTPException:
        """Convert database errors to HTTP exceptions"""
        logger.error(f"Database error: {error}")

        if "UNIQUE constraint" in str(error):
            return HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Resource already exists"
            )
        elif "NOT NULL constraint" in str(error):
            return HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Required field is missing"
            )
        else:
            return HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database operation failed"
            )

    @staticmethod
    def handle_file_error(error: Exception) -> HTTPException:
        """Convert file system errors to HTTP exceptions"""
        logger.error(f"File system error: {error}")

        if "Permission denied" in str(error):
            return HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied"
            )
        elif "No such file" in str(error) or "does not exist" in str(error):
            return HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        elif "No space left" in str(error):
            return HTTPException(
                status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
                detail="Insufficient storage space"
            )
        else:
            return HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="File operation failed"
            )


def handle_error(error: Exception) -> HTTPException:
    """Generic error handler"""
    logger.error(f"Unhandled error: {error}", exc_info=True)

    if isinstance(error, HTTPException):
        return error
    else:
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )