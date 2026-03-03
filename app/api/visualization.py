"""
Visualization API Endpoints
Interactive data access for visualization components
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse, FileResponse

from app.dependencies import get_database
from app.services.unified_workspace_manager import get_unified_workspace_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nodes", tags=["visualization"])


@router.get("/{execution_id}/data")
async def get_node_data(
    execution_id: str,
    node_id: Optional[str] = None,
    db=Depends(get_database)
) -> Dict[str, Any]:
    """
    Get output data from a node for visualization

    Query parameters:
    - execution_id: Execution identifier
    - node_id: Node identifier (optional, if not specified returns all node outputs)

    Returns:
    - File paths and metadata for node outputs
    - For interactive tools, returns data file location and format
    """
    try:
        from app.services.paths import get_workflows_root

        # Get execution info
        cursor = db.cursor()
        cursor.execute(
            "SELECT workspace_path, workflow_snapshot FROM executions WHERE id = ?",
            (execution_id,)
        )
        row = cursor.fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution '{execution_id}' not found"
            )

        workspace_path, workflow_snapshot = row
        workspace_dir = Path(workspace_path)

        if not workspace_dir.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace directory not found: {workspace_path}"
            )

        results_dir = workspace_dir / "results"
        if not results_dir.exists():
            return {
                "execution_id": execution_id,
                "node_id": node_id,
                "data": [],
                "files": [],
                "message": "No results directory found"
            }

        # Collect output files
        output_files = []
        if node_id:
            # Get specific node outputs
            node_pattern = f"*{node_id}*"
            for file_path in results_dir.glob(node_pattern):
                if file_path.is_file():
                    output_files.append({
                        "name": file_path.name,
                        "path": str(file_path),
                        "size": file_path.stat().st_size,
                        "extension": file_path.suffix,
                        "relative_path": str(file_path.relative_to(workspace_dir))
                    })
        else:
            # Get all output files
            for file_path in results_dir.iterdir():
                if file_path.is_file():
                    output_files.append({
                        "name": file_path.name,
                        "path": str(file_path),
                        "size": file_path.stat().st_size,
                        "extension": file_path.suffix,
                        "relative_path": str(file_path.relative_to(workspace_dir))
                    })

        return {
            "execution_id": execution_id,
            "node_id": node_id,
            "workspace_path": str(workspace_dir),
            "results_dir": str(results_dir),
            "files": output_files,
            "total_files": len(output_files)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting node data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get node data: {str(e)}"
        )


@router.get("/{execution_id}/preview")
async def preview_data_file(
    execution_id: str,
    file_path: str,
    max_rows: int = 100,
    db=Depends(get_database)
) -> Dict[str, Any]:
    """
    Preview tabular data file (first N rows)

    Query parameters:
    - execution_id: Execution identifier
    - file_path: Relative path to file from results directory
    - max_rows: Maximum number of rows to return (default: 100)

    Returns:
    - File metadata and preview data
    """
    try:
        # Get execution workspace
        cursor = db.cursor()
        cursor.execute(
            "SELECT workspace_path FROM executions WHERE id = ?",
            (execution_id,)
        )
        row = cursor.fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution '{execution_id}' not found"
            )

        workspace_path = row[0]
        file_full_path = Path(workspace_path) / "results" / file_path

        if not file_full_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {file_path}"
            )

        # Determine file type and read accordingly
        extension = file_full_path.suffix.lower()

        if extension in ['.tsv', '.csv', '.txt']:
            # Tabular file preview
            data = []
            with open(file_full_path, 'r', encoding='utf-8') as f:
                # Read header
                header = f.readline().strip()
                if extension == '.csv':
                    columns = header.split(',')
                else:
                    columns = header.split('\t')

                # Read data rows
                for i, line in enumerate(f):
                    if i >= max_rows:
                        break
                    if extension == '.csv':
                        values = line.strip().split(',')
                    else:
                        values = line.strip().split('\t')

                    row_data = dict(zip(columns, values))
                    data.append(row_data)

            return {
                "execution_id": execution_id,
                "file_path": file_path,
                "file_name": file_full_path.name,
                "file_size": file_full_path.stat().st_size,
                "file_type": "tabular",
                "columns": columns,
                "row_count": len(data),
                "preview_rows": data,
                "max_rows_limit": max_rows
            }

        else:
            # Binary or other file - just return metadata
            return {
                "execution_id": execution_id,
                "file_path": file_path,
                "file_name": file_full_path.name,
                "file_size": file_full_path.stat().st_size,
                "file_type": "binary",
                "message": "Preview not available for this file type"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview data: {str(e)}"
        )


@router.get("/workspaces/{user_id}/{workspace_id}/files")
async def list_workspace_files(
    user_id: str,
    workspace_id: str,
    db=Depends(get_database)
) -> Dict[str, Any]:
    """
    List files in workspace for file browser UI

    Returns:
    - Directory structure and files
    """
    try:
        manager = get_unified_workspace_manager()
        workspace_dir = manager.get_workspace_path(user_id, workspace_id)

        if not workspace_dir or not workspace_dir.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace not found: {user_id}/{workspace_id}"
            )

        # Build directory tree
        def build_tree(path: Path, base_path: Path) -> Dict[str, Any]:
            items = []
            try:
                for item in path.iterdir():
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

            # Sort: directories first, then files, then alphabetically
            items.sort(key=lambda x: (x["type"] != "directory", x["name"]))
            return items

        tree = build_tree(workspace_dir, workspace_dir)

        return {
            "user_id": user_id,
            "workspace_id": workspace_id,
            "workspace_path": str(workspace_dir),
            "tree": tree,
            "total_items": sum(len(items) if isinstance(items, list) else 1
                            for items in [tree] if isinstance(tree, list) else [tree]])
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing workspace files: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list workspace files: {str(e)}"
        )


# Export the router for use in main app
visualization_router = router
