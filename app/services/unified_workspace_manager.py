"""
Unified Workspace Manager - Complete workspace management system

Combines hierarchical user/workspace management with execution directory structure:
- users/{user_id}/workspaces/{workspace_id}/
  - samples.json (sample definitions with context) - DEPRECATED, now using database
  - workflows/ (workflow definitions)
  - executions/{exec_id}/ (execution records with isolation)
  - data/ (shared data files: raw/, fasta/, reference/)
"""

import json
import os
import re
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from app.services.sample_store import sample_store, SampleValidationError

logger = logging.getLogger(__name__)


class UnifiedWorkspaceManager:
    """
    Unified workspace management system.

    Provides:
    - Hierarchical path management (users → workspaces → executions)
    - Sample context management (load/validate/auto-derive)
    - Execution directory isolation
    - File operations (validate, resolve, copy)
    """

    def __init__(self, data_root: str = "data"):
        """Initialize unified workspace manager"""
        self.data_root = Path(data_root)
        self.users_dir = self.data_root / "users"
        self.sample_store = sample_store  # Add sample_store reference

    # ========== Path Management ==========

    def get_user_path(self, user_id: str) -> Path:
        """Get user directory path"""
        return self.users_dir / user_id

    def get_workspace_path(self, user_id: str, workspace_id: str) -> Path:
        """Get workspace directory path"""
        return self.get_user_path(user_id) / "workspaces" / workspace_id

    def get_samples_file(self, user_id: str, workspace_id: str) -> Path:
        """Get samples.json file path"""
        return self.get_workspace_path(user_id, workspace_id) / "samples.json"

    def get_workflows_dir(self, user_id: str, workspace_id: str) -> Path:
        """Get workflows directory path"""
        return self.get_workspace_path(user_id, workspace_id) / "workflows"

    def get_executions_dir(self, user_id: str, workspace_id: str) -> Path:
        """Get executions directory path"""
        return self.get_workspace_path(user_id, workspace_id) / "executions"

    def get_data_dir(self, user_id: str, workspace_id: str) -> Path:
        """Get data directory path"""
        return self.get_workspace_path(user_id, workspace_id) / "data"

    def get_execution_dir(self, user_id: str, workspace_id: str, execution_id: str) -> Path:
        """Get specific execution directory path"""
        return self.get_executions_dir(user_id, workspace_id) / execution_id

    # ========== User Management ==========

    def create_user(self, user_id: str, username: str, email: str = "",
                    display_name: str = "") -> Dict[str, Any]:
        """Create a new user"""
        user_path = self.get_user_path(user_id)
        user_path.mkdir(parents=True, exist_ok=True)

        user_meta = {
            "user_id": user_id,
            "username": username,
            "email": email,
            "display_name": display_name or username,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "settings": {
                "default_workspace": None,
                "max_workspaces": 10,
                "max_executions_per_workspace": 100
            }
        }

        user_file = user_path / "user.json"
        with open(user_file, 'w') as f:
            json.dump(user_meta, f, indent=2)

        return user_meta

    # ========== Workspace Management ==========

    def create_workspace(self, user_id: str, workspace_id: str,
                        name: str, description: str = "") -> Dict[str, Any]:
        """Create a new workspace with full directory structure"""
        workspace_path = self.get_workspace_path(user_id, workspace_id)

        # Create directory structure
        (workspace_path / "workflows").mkdir(parents=True, exist_ok=True)
        (workspace_path / "executions").mkdir(parents=True, exist_ok=True)
        (workspace_path / "data" / "raw").mkdir(parents=True, exist_ok=True)
        (workspace_path / "data" / "fasta").mkdir(parents=True, exist_ok=True)
        (workspace_path / "data" / "reference").mkdir(parents=True, exist_ok=True)

        # Create workspace metadata
        workspace_meta = {
            "workspace_id": workspace_id,
            "name": name,
            "description": description,
            "owner": user_id,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "settings": {
                "max_samples": 1000,
                "retention_days": 30,
                "auto_cleanup": True
            },
            "statistics": {
                "total_samples": 0,
                "total_workflows": 0,
                "total_executions": 0
            }
        }

        workspace_file = workspace_path / "workspace.json"
        with open(workspace_file, 'w') as f:
            json.dump(workspace_meta, f, indent=2)

        # Note: samples.json is no longer created - data is stored in database
        # Legacy samples.json files will be migrated to database automatically

        return workspace_meta

    def list_workspaces(self, user_id: str) -> List[Dict[str, Any]]:
        """List all workspaces for a user"""
        user_path = self.get_user_path(user_id)
        workspaces_dir = user_path / "workspaces"

        if not workspaces_dir.exists():
            return []

        workspaces = []
        for workspace_dir in workspaces_dir.iterdir():
            if workspace_dir.is_dir():
                workspace_file = workspace_dir / "workspace.json"
                if workspace_file.exists():
                    with open(workspace_file, 'r') as f:
                        workspaces.append(json.load(f))

        return workspaces

    def delete_workspace(self, user_id: str, workspace_id: str) -> bool:
        """Delete a workspace and all its contents"""
        workspace_path = self.get_workspace_path(user_id, workspace_id)
        if workspace_path.exists():
            shutil.rmtree(workspace_path)
            return True
        return False

    # ========== Sample Management ==========

    def load_samples(self, user_id: str, workspace_id: str) -> Dict[str, Any]:
        """Load samples - from database"""
        samples_list = self.sample_store.list_by_workspace(workspace_id, limit=10000)

        samples_data = {
            "version": "1.0",
            "workspace_id": workspace_id,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "samples": {}
        }

        for sample in samples_list:
            samples_data["samples"][sample["id"]] = {
                "id": sample["id"],
                "name": sample["name"],
                "description": sample["description"],
                "context": sample["context"],
                "data_paths": sample["data_paths"],
                "metadata": sample["metadata"],
                "created_at": sample["created_at"]
            }

        return samples_data

    def save_samples(self, user_id: str, workspace_id: str,
                    samples_data: Dict[str, Any]) -> None:
        """Save samples - deprecated, saving to database instead (kept for compatibility)"""
        # No longer needed, data is saved directly to database via add_sample/update_sample
        pass

    def add_sample(self, user_id: str, workspace_id: str,
                  sample_id: str, name: str, context: Dict[str, str],
                  data_paths: Dict[str, str], description: str = "",
                  metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add a sample - save to database

        Args:
            user_id: User identifier
            workspace_id: Workspace identifier
            sample_id: Unique sample identifier
            name: Sample display name
            context: Placeholder values for workflow resolution
            data_paths: File path mappings
            description: Sample description
            metadata: Additional sample metadata

        Returns:
            The created sample dictionary

        Raises:
            SampleValidationError: If sample data is invalid
            RuntimeError: If database operation fails
        """
        sample_data = {
            "user_id": user_id,
            "workspace_id": workspace_id,
            "name": name,
            "description": description,
            "context": context,
            "data_paths": data_paths,
            "metadata": metadata or {}
        }

        try:
            self.sample_store.save(sample_id, sample_data)
        except SampleValidationError as e:
            logger.error(f"Validation error adding sample {sample_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to save sample {sample_id}: {e}")
            raise RuntimeError(f"Failed to save sample {sample_id}: {e}")

        self._update_workspace_stats(user_id, workspace_id)

        result = self.sample_store.get(sample_id)
        if not result:
            raise RuntimeError(f"Sample {sample_id} was saved but could not be retrieved")
        return result

    def update_sample(self, user_id: str, workspace_id: str,
                     sample_id: str, **updates) -> Optional[Dict[str, Any]]:
        """Update sample - update database record

        Args:
            user_id: User identifier
            workspace_id: Workspace identifier
            sample_id: Sample identifier
            **updates: Fields to update

        Returns:
            Updated sample dictionary, or None if not found

        Raises:
            SampleValidationError: If update data is invalid
            RuntimeError: If database operation fails
        """
        sample = self.sample_store.get(sample_id)
        if not sample:
            return None

        # Create new dict with updates (immutable pattern)
        updated_sample = {**sample}
        for field in ["name", "description", "context", "data_paths", "metadata"]:
            if field in updates:
                updated_sample[field] = updates[field]

        try:
            self.sample_store.save(sample_id, updated_sample)
        except SampleValidationError as e:
            logger.error(f"Validation error updating sample {sample_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to update sample {sample_id}: {e}")
            raise RuntimeError(f"Failed to update sample {sample_id}: {e}")

        return self.sample_store.get(sample_id)

    def delete_sample(self, user_id: str, workspace_id: str, sample_id: str) -> bool:
        """Delete sample - from database

        Args:
            user_id: User identifier
            workspace_id: Workspace identifier
            sample_id: Sample identifier

        Returns:
            True if sample was deleted, False if not found

        Raises:
            RuntimeError: If database operation fails
        """
        try:
            success = self.sample_store.delete(sample_id)
            if success:
                self._update_workspace_stats(user_id, workspace_id)
            return success
        except Exception as e:
            logger.error(f"Failed to delete sample {sample_id}: {e}")
            raise RuntimeError(f"Failed to delete sample {sample_id}: {e}")

    def list_samples(self, user_id: str, workspace_id: str) -> List[Dict[str, Any]]:
        """List samples - from database"""
        return self.sample_store.list_by_workspace(workspace_id)

    def get_sample_context(self, user_id: str, workspace_id: str,
                          sample_id: str) -> Optional[Dict[str, str]]:
        """
        Get sample context for placeholder resolution.

        Returns None if sample not found.
        """
        sample = self.sample_store.get(sample_id)
        if not sample:
            return None

        # Build full context with auto-derivation
        return self._build_sample_context(sample, user_id, workspace_id)

    def _build_sample_context(self, sample: Dict[str, Any],
                             user_id: str, workspace_id: str) -> Dict[str, str]:
        """
        Build complete sample context with derivation and merging.

        data_paths now stores absolute paths, use them directly.
        Priority: Explicit values > Derived values
        """
        explicit_context = sample.get("context", {})
        data_paths = sample.get("data_paths", {})

        # Base context
        derived = {
            "sample": sample.get("id", ""),
        }

        # Get absolute path from data_paths (already absolute, use directly)
        raw_path = data_paths.get("raw", "")
        if raw_path:
            raw_file = Path(raw_path)
            derived["raw_path"] = raw_path  # Use absolute path directly
            derived["input_basename"] = raw_file.stem
            derived["input_dir"] = str(raw_file.parent)
            derived["input_ext"] = raw_file.suffix.lstrip(".")

        fasta_path = data_paths.get("fasta", "")
        if fasta_path:
            derived["fasta_path"] = fasta_path  # Use absolute path directly

        # Merge: explicit overrides derived
        return {**derived, **explicit_context}

    # ========== Execution Management ==========

    def create_execution_dir(self, user_id: str, workspace_id: str,
                            execution_id: str) -> Path:
        """
        Create execution directory with isolated structure.

        Returns path to execution directory.
        """
        exec_dir = self.get_execution_dir(user_id, workspace_id, execution_id)
        exec_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (exec_dir / "inputs").mkdir(exist_ok=True)
        (exec_dir / "outputs").mkdir(exist_ok=True)
        (exec_dir / "logs").mkdir(exist_ok=True)

        # Create execution metadata
        execution_meta = {
            "execution_id": execution_id,
            "workspace_id": workspace_id,
            "status": "created",
            "created_at": datetime.utcnow().isoformat() + "Z",
        }

        exec_file = exec_dir / "execution.json"
        with open(exec_file, 'w') as f:
            json.dump(execution_meta, f, indent=2)

        return exec_dir

    def update_execution_status(self, user_id: str, workspace_id: str,
                               execution_id: str, status: str,
                               **updates) -> None:
        """Update execution status"""
        exec_dir = self.get_execution_dir(user_id, workspace_id, execution_id)
        exec_file = exec_dir / "execution.json"

        if not exec_file.exists():
            return

        with open(exec_file, 'r') as f:
            meta = json.load(f)

        meta["status"] = status
        if status in ("completed", "failed", "cancelled"):
            meta["completed_at"] = datetime.utcnow().isoformat() + "Z"

        meta.update(updates)

        with open(exec_file, 'w') as f:
            json.dump(meta, f, indent=2)

    # ========== File Operations ==========

    def ensure_directory_structure(self, workspace_path: Path) -> None:
        """Ensure workspace directory structure exists"""
        subdirs = ["inputs", "outputs", "logs", "temp"]
        for subdir in subdirs:
            (workspace_path / subdir).mkdir(parents=True, exist_ok=True)

    def validate_input_file(self, file_path: str) -> Tuple[bool, str]:
        """Validate input file exists and is readable"""
        path = Path(file_path)

        if not path.exists():
            return False, f"Input file does not exist: {file_path}"

        if not path.is_file():
            return False, f"Input path is not a file: {file_path}"

        if path.stat().st_size == 0:
            return False, f"Input file is empty: {file_path}"

        return True, ""

    def resolve_input_path(self, raw_path: str, data_root: str = "/data") -> str:
        """Resolve input path to absolute path"""
        path = Path(raw_path)

        if path.is_absolute():
            return str(path)
        elif raw_path.startswith("./") or raw_path.startswith("../"):
            return str(Path(data_root) / raw_path)
        else:
            return str(Path(data_root) / raw_path)

    def copy_to_workspace(self, source_file: str, workspace_path: Path,
                         category: str = "inputs") -> str:
        """Copy file to workspace directory"""
        source_path = Path(source_file)
        dest_dir = workspace_path / category
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / source_path.name

        shutil.copy2(source_path, dest_path)
        return str(dest_path)

    # ========== Workflow Management ==========

    def save_workflow(self, user_id: str, workspace_id: str,
                     workflow_data: Dict[str, Any]) -> str:
        """Save workflow definition to workspace"""
        workflows_dir = self.get_workflows_dir(user_id, workspace_id)
        workflows_dir.mkdir(parents=True, exist_ok=True)

        workflow_id = workflow_data.get("workflow_id") or workflow_data.get("id")
        if not workflow_id:
            raise ValueError("Workflow must have 'workflow_id' or 'id' field")

        workflow_file = workflows_dir / f"{workflow_id}.json"
        with open(workflow_file, 'w') as f:
            json.dump(workflow_data, f, indent=2)

        return str(workflow_file)

    def load_workflow(self, user_id: str, workspace_id: str,
                     workflow_id: str) -> Optional[Dict[str, Any]]:
        """Load workflow definition from workspace"""
        workflows_dir = self.get_workflows_dir(user_id, workspace_id)
        workflow_file = workflows_dir / f"{workflow_id}.json"

        if not workflow_file.exists():
            return None

        with open(workflow_file, 'r') as f:
            return json.load(f)

    def list_workflows(self, user_id: str, workspace_id: str) -> List[Dict[str, Any]]:
        """List all workflows in workspace"""
        workflows_dir = self.get_workflows_dir(user_id, workspace_id)
        workflows = []

        if not workflows_dir.exists():
            return []

        for workflow_file in workflows_dir.glob("*.json"):
            try:
                with open(workflow_file, 'r') as f:
                    workflows.append(json.load(f))
            except Exception:
                continue

        return workflows

    # ========== Statistics ==========

    def _update_workspace_stats(self, user_id: str, workspace_id: str) -> None:
        """Update workspace statistics"""
        workspace_path = self.get_workspace_path(user_id, workspace_id)
        workspace_file = workspace_path / "workspace.json"

        if not workspace_file.exists():
            return

        with open(workspace_file, 'r') as f:
            workspace_meta = json.load(f)

        # Count samples
        samples_data = self.load_samples(user_id, workspace_id)
        sample_count = len(samples_data.get("samples", {}))

        # Count workflows
        workflows_count = len(self.list_workflows(user_id, workspace_id))

        # Count executions
        executions_dir = self.get_executions_dir(user_id, workspace_id)
        execution_count = len([d for d in executions_dir.iterdir() if d.is_dir()]) if executions_dir.exists() else 0

        workspace_meta["statistics"] = {
            "total_samples": sample_count,
            "total_workflows": workflows_count,
            "total_executions": execution_count
        }
        workspace_meta["updated_at"] = datetime.utcnow().isoformat() + "Z"

        with open(workspace_file, 'w') as f:
            json.dump(workspace_meta, f, indent=2)


# Global instance
_unified_manager = None


def get_unified_workspace_manager(data_root: str = "data") -> UnifiedWorkspaceManager:
    """Get global unified workspace manager instance"""
    global _unified_manager
    if _unified_manager is None:
        _unified_manager = UnifiedWorkspaceManager(data_root)
    return _unified_manager