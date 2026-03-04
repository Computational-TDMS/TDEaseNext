"""
Workspace API Endpoints

Provides REST API for:
- User workspace management
- Sample CRUD operations
- Workspace metadata management
- Workspace file browsing
"""
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.services.unified_workspace_manager import get_unified_workspace_manager

router = APIRouter()


# ========== Request/Response Models ==========

class CreateWorkspaceRequest(BaseModel):
    """Request to create a new workspace"""
    workspace_id: str = Field(..., description="Unique workspace identifier")
    name: str = Field(..., description="Workspace display name")
    description: str = Field("", description="Workspace description")


class CreateSampleRequest(BaseModel):
    """Request to add a sample to workspace"""
    id: str = Field(..., description="Unique sample identifier")
    name: str = Field(..., description="Sample display name")
    context: Dict[str, str] = Field(..., description="Placeholder values for this sample")
    data_paths: Dict[str, str] = Field(..., description="File path templates")
    description: str = Field("", description="Sample description")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Sample metadata")


class UpdateSampleRequest(BaseModel):
    """Request to update a sample"""
    name: Optional[str] = None
    description: Optional[str] = None
    context: Optional[Dict[str, str]] = None
    data_paths: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None


# ========== Workspace Endpoints ==========

@router.get("/users/{user_id}/workspaces")
async def list_workspaces(user_id: str):
    """List all workspaces for a user"""
    manager = get_unified_workspace_manager()
    workspaces = manager.list_workspaces(user_id)
    return {
        "user_id": user_id,
        "workspaces": workspaces,
        "count": len(workspaces)
    }


@router.post("/users/{user_id}/workspaces")
async def create_workspace(user_id: str, request: CreateWorkspaceRequest):
    """Create a new workspace"""
    manager = get_unified_workspace_manager()

    # Ensure user exists
    user_path = manager.get_user_path(user_id)
    if not user_path.exists():
        manager.create_user(user_id, user_id)

    # Create workspace
    workspace_meta = manager.create_workspace(
        user_id=user_id,
        workspace_id=request.workspace_id,
        name=request.name,
        description=request.description
    )

    return workspace_meta


@router.get("/users/{user_id}/workspaces/{workspace_id}")
async def get_workspace(user_id: str, workspace_id: str):
    """Get workspace metadata"""
    manager = get_unified_workspace_manager()
    workspace_path = manager.get_workspace_path(user_id, workspace_id)
    workspace_file = workspace_path / "workspace.json"

    if not workspace_file.exists():
        raise HTTPException(status_code=404, detail=f"Workspace '{workspace_id}' not found")

    import json
    with open(workspace_file, 'r') as f:
        return json.load(f)


@router.delete("/users/{user_id}/workspaces/{workspace_id}")
async def delete_workspace(user_id: str, workspace_id: str):
    """Delete a workspace and all its contents"""
    manager = get_unified_workspace_manager()
    success = manager.delete_workspace(user_id, workspace_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"Workspace '{workspace_id}' not found")

    return {"message": f"Workspace '{workspace_id}' deleted successfully"}


# ========== Sample Endpoints ==========

@router.get("/users/{user_id}/workspaces/{workspace_id}/samples")
async def list_samples(user_id: str, workspace_id: str):
    """List all samples in workspace"""
    manager = get_unified_workspace_manager()
    samples = manager.list_samples(user_id, workspace_id)

    return {
        "user_id": user_id,
        "workspace_id": workspace_id,
        "samples": samples,
        "count": len(samples)
    }


@router.post("/users/{user_id}/workspaces/{workspace_id}/samples")
async def add_sample(user_id: str, workspace_id: str, request: CreateSampleRequest):
    """Add a sample to workspace"""
    manager = get_unified_workspace_manager()

    # Check workspace exists
    workspace_path = manager.get_workspace_path(user_id, workspace_id)
    if not workspace_path.exists():
        raise HTTPException(status_code=404, detail=f"Workspace '{workspace_id}' not found")

    # Add sample
    sample_def = manager.add_sample(
        user_id=user_id,
        workspace_id=workspace_id,
        sample_id=request.id,
        name=request.name,
        context=request.context,
        data_paths=request.data_paths,
        description=request.description,
        metadata=request.metadata
    )

    return sample_def


@router.get("/users/{user_id}/workspaces/{workspace_id}/samples/{sample_id}")
async def get_sample(user_id: str, workspace_id: str, sample_id: str):
    """Get a specific sample"""
    manager = get_unified_workspace_manager()
    samples_data = manager.load_samples(user_id, workspace_id)
    sample = samples_data.get("samples", {}).get(sample_id)

    if not sample:
        raise HTTPException(status_code=404, detail=f"Sample '{sample_id}' not found")

    return sample


@router.put("/users/{user_id}/workspaces/{workspace_id}/samples/{sample_id}")
async def update_sample(user_id: str, workspace_id: str, sample_id: str, request: UpdateSampleRequest):
    """Update a sample"""
    manager = get_unified_workspace_manager()

    # Build updates dict (only include non-None fields)
    updates = {}
    if request.name is not None:
        updates["name"] = request.name
    if request.description is not None:
        updates["description"] = request.description
    if request.context is not None:
        updates["context"] = request.context
    if request.data_paths is not None:
        updates["data_paths"] = request.data_paths
    if request.metadata is not None:
        updates["metadata"] = request.metadata

    sample = manager.update_sample(user_id, workspace_id, sample_id, **updates)

    if not sample:
        raise HTTPException(status_code=404, detail=f"Sample '{sample_id}' not found")

    return sample


@router.delete("/users/{user_id}/workspaces/{workspace_id}/samples/{sample_id}")
async def delete_sample(user_id: str, workspace_id: str, sample_id: str):
    """Delete a sample"""
    manager = get_unified_workspace_manager()
    success = manager.delete_sample(user_id, workspace_id, sample_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"Sample '{sample_id}' not found")

    return {"message": f"Sample '{sample_id}' deleted successfully"}


@router.get("/users/{user_id}/workspaces/{workspace_id}/files")
async def get_workspace_files(user_id: str, workspace_id: str):
    """
    List files in workspace for file browser UI.

    Returns:
    - Directory structure and files (sorted: directories first, then files, alphabetically)
    - Hidden files (starting with .) are excluded
    """
    manager = get_unified_workspace_manager()
    workspace_dir = manager.get_workspace_path(user_id, workspace_id)

    if not workspace_dir or not workspace_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Workspace not found: {user_id}/{workspace_id}"
        )

    def build_tree(path: Path, base_path: Path) -> List[Dict[str, Any]]:
        """Build directory tree recursively"""
        items = []
        try:
            for item in path.iterdir():
                # Skip hidden files
                if item.name.startswith('.'):
                    continue

                rel_path = str(item.relative_to(base_path))

                if item.is_dir():
                    items.append({
                        "name": item.name,
                        "type": "directory",
                        "path": rel_path,
                        "children": build_tree(item, base_path)
                    })
                else:
                    items.append({
                        "name": item.name,
                        "type": "file",
                        "path": rel_path,
                        "size": item.stat().st_size,
                        "extension": item.suffix,
                        "modified": item.stat().st_mtime
                    })
        except PermissionError:
            pass

        # Sort: directories first, then files, alphabetically
        items.sort(key=lambda x: (x["type"] != "directory", x["name"]))
        return items

    tree = build_tree(workspace_dir, workspace_dir)

    return {
        "user_id": user_id,
        "workspace_id": workspace_id,
        "workspace_path": str(workspace_dir),
        "tree": tree
    }


@router.get("/users/{user_id}/workspaces/{workspace_id}/file-content")
async def get_file_content(
    user_id: str,
    workspace_id: str,
    path: str,
    max_rows: int = 100
):
    """
    Get file content preview within a workspace.

    Query parameters:
    - path: Relative path to file from workspace root
    - max_rows: Maximum rows to return for tabular files (default: 100)

    Returns:
    - File metadata and content (tabular, text, or binary)
    """
    manager = get_unified_workspace_manager()
    workspace_dir = manager.get_workspace_path(user_id, workspace_id)

    if not workspace_dir or not workspace_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Workspace not found: {user_id}/{workspace_id}"
        )

    # Path traversal prevention
    if ".." in path or path.startswith("/"):
        raise HTTPException(
            status_code=403,
            detail="Path traversal detected"
        )

    file_path = workspace_dir / path

    # Ensure file is within workspace
    try:
        file_path.resolve().relative_to(workspace_dir.resolve())
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="Path outside workspace"
        )

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {path}"
        )

    if not file_path.is_file():
        raise HTTPException(
            status_code=400,
            detail="Path is not a file"
        )

    # Determine file type
    extension = file_path.suffix.lower()
    file_size = file_path.stat().st_size

    # Tabular extensions
    tabular_extensions = {'.tsv', '.txt', '.csv', '.ms1ft', '.feature'}

    if extension in tabular_extensions:
        # Parse as tabular
        from app.services.node_data_service import parse_tabular_file
        try:
            data = parse_tabular_file(file_path, max_rows)
            return {
                "file_path": path,
                "file_name": file_path.name,
                "file_size": file_size,
                "file_type": "tabular",
                "content": {
                    "columns": data["columns"],
                    "rows": data["rows"],
                    "total_rows": data["total_rows"],
                    "preview_rows": len(data["rows"])
                }
            }
        except Exception as e:
            return {
                "file_path": path,
                "file_name": file_path.name,
                "file_size": file_size,
                "file_type": "text",
                "content": f"Failed to parse file: {str(e)}"
            }
    else:
        # Binary extensions
        binary_extensions = {'.pbf', '.raw', '.mzml', '.png', '.jpg', '.jpeg'}
        if extension in binary_extensions or file_size > 10 * 1024 * 1024:  # 10MB threshold
            return {
                "file_path": path,
                "file_name": file_path.name,
                "file_size": file_size,
                "file_type": "binary",
                "content": None
            }
        else:
            # Try to read as text
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    # Read up to 100KB
                    content = f.read(100 * 1024)
                return {
                    "file_path": path,
                    "file_name": file_path.name,
                    "file_size": file_size,
                    "file_type": "text",
                    "content": content
                }
            except UnicodeDecodeError:
                return {
                    "file_path": path,
                    "file_name": file_path.name,
                    "file_size": file_size,
                    "file_type": "binary",
                    "content": None
                }
