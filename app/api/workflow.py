"""
Workflow API Endpoints
Handles workflow creation, execution, and management
"""

import json
import uuid
import shutil
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from fastapi.responses import JSONResponse, Response

from app.models.workflow import (
    WorkflowCreate, WorkflowResponse, WorkflowUpdate,
    WorkflowStatus, WorkflowValidation, WorkflowImportRequest, WorkflowListResponse
)
from app.models.execution import ExecutionRequest
from app.models.common import SuccessResponse, APIError
from app.dependencies import get_database, get_config
from app.core.platform_manager import get_platform_manager
from app.core.permission_manager import PermissionManager, get_permission_manager
from app.services.workflow_format import validate_workflow_document
from app.services.workflow_diff import has_structure_changed
from app.core.time_utils import utc_now, utc_now_iso_z

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=WorkflowListResponse)
async def list_workflows(
    page: int = 1,
    page_size: int = 20,
    db=Depends(get_database)
) -> WorkflowListResponse:
    """List workflows"""
    try:
        cursor = db.cursor()
        offset = (page - 1) * page_size
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM workflows")
        total = cursor.fetchone()[0]
        
        # Get workflows
        cursor.execute("""
            SELECT id, name, description, status, created_at, updated_at
            FROM workflows
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (page_size, offset))
        
        rows = cursor.fetchall()
        workflows = []
        for row in rows:
            workflows.append({
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "status": row[3],
                "created_at": datetime.fromisoformat(row[4]),
                "updated_at": datetime.fromisoformat(row[5] or row[4]),
                "version": "1.0.0" # Mock version for now
            })
            
        return WorkflowListResponse(
            workflows=workflows,
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        logger.error(f"Failed to list workflows: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list workflows: {str(e)}"
        )

@router.post("/import", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def import_workflow(
    req: WorkflowImportRequest,
    db=Depends(get_database),
    perm_manager: PermissionManager = Depends(get_permission_manager)
) -> WorkflowResponse:
    try:
        workspace_perms = await perm_manager.check_workspace_permissions(req.workspace_path)
        if not workspace_perms["exists"]:
            if not workspace_perms.get("parent_writable", False):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workspace directory invalid")
            await perm_manager.ensure_workspace_structure(req.workspace_path)

        ok, fmt, parsed = validate_workflow_document(req.document)
        if not ok:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Workflow document invalid: {parsed}")

        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        workflow_dir = Path("data/workflows") / workflow_id
        workflow_dir.mkdir(parents=True, exist_ok=True)
        (workflow_dir / "workflow_files").mkdir(exist_ok=True)
        (workflow_dir / "logs").mkdir(exist_ok=True)
        (workflow_dir / "results").mkdir(exist_ok=True)
        (workflow_dir / "temp").mkdir(exist_ok=True)

        # Save workflow document based on format
        if fmt == "vueflow":
            doc_file = workflow_dir / "workflow.json"
            doc_file.write_text(req.document, encoding="utf-8")
        elif fmt == "ga":
            doc_file = workflow_dir / "workflow.ga"
            doc_file.write_text(req.document, encoding="utf-8")
        elif fmt == "format2_yaml":
            doc_file = workflow_dir / "workflow.gxwf.yml"
            doc_file.write_text(req.document, encoding="utf-8")
        else:
            doc_file = workflow_dir / "workflow.gxwf.json"
            doc_file.write_text(req.document, encoding="utf-8")

        workflow_config = {
            "id": workflow_id,
            "name": req.name,
            "description": req.description,
            "vueflow_data": {},
            "workspace_path": req.workspace_path,
            "created_at": datetime.now().isoformat(),
            "status": "created",
            "metadata": req.metadata or {},
            "workflow_format": fmt,
            "workflow_document": req.document,
        }

        config_file = workflow_dir / "config.yaml"
        with open(config_file, 'w') as f:
            import yaml
            yaml.safe_dump(workflow_config, f, default_flow_style=False)

        await save_workflow_to_database(db, workflow_config)

        return WorkflowResponse(
            id=workflow_id,
            name=req.name,
            description=req.description,
            status="created",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            vueflow_data={},
            workspace_path=req.workspace_path,
            validation_status=WorkflowValidation(valid=True, errors=[], warnings=[], generated_files=[]),
            execution_count=0,
            last_execution_id=None,
            metadata=req.metadata
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to import workflow: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Workflow import failed: {e}")


@router.post("/", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow: WorkflowCreate,
    background_tasks: BackgroundTasks,
    db=Depends(get_database),
    config=Depends(get_config),
    perm_manager: PermissionManager = Depends(get_permission_manager)
) -> WorkflowResponse:
    """Create a new workflow from VueFlow data"""
    try:
        # Validate workspace permissions
        workspace_perms = await perm_manager.check_workspace_permissions(
            workflow.workspace_path
        )

        if not workspace_perms["exists"]:
            if not workspace_perms.get("parent_writable", False):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Workspace directory does not exist and cannot be created"
                )

            # Create workspace structure
            await perm_manager.ensure_workspace_structure(workflow.workspace_path)

        # Generate workflow ID
        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        # Create workflow directory structure
        workflow_dir = Path("data/workflows") / workflow_id
        workflow_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (workflow_dir / "workflow_files").mkdir(exist_ok=True)
        (workflow_dir / "logs").mkdir(exist_ok=True)
        (workflow_dir / "results").mkdir(exist_ok=True)
        (workflow_dir / "temp").mkdir(exist_ok=True)

        # Normalize workflow data to ensure format_version and metadata are included
        from src.workflow.normalizer import WorkflowNormalizer
        normalizer = WorkflowNormalizer()
        normalized_vueflow_data = normalizer.normalize(workflow.vueflow_data)
        # 确保 vueflow_data.metadata.id 与后端生成的 workflow_id 一致
        if "metadata" not in normalized_vueflow_data:
            normalized_vueflow_data["metadata"] = {}
        normalized_vueflow_data["metadata"]["id"] = workflow_id
        
        # Save workflow configuration
        workflow_config = {
            "id": workflow_id,
            "name": workflow.name,
            "description": workflow.description,
            "vueflow_data": normalized_vueflow_data,  # Use normalized data with format_version and metadata
            "workspace_path": workflow.workspace_path,
            "created_at": datetime.now().isoformat(),
            "status": "created",
            "metadata": workflow.metadata or {},
            "workflow_format": "vueflow"
        }

        config_file = workflow_dir / "config.yaml"
        with open(config_file, 'w') as f:
            import yaml
            yaml.safe_dump(workflow_config, f, default_flow_style=False)

        # Validate VueFlow data structure
        validation_result = await validate_vueflow_structure(workflow.vueflow_data)
        if not validation_result["valid"]:
            # Clean up on validation failure
            shutil.rmtree(workflow_dir, ignore_errors=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"VueFlow data validation failed: {validation_result['error']}"
            )

        # Save workflow to database
        await save_workflow_to_database(db, workflow_config)

        logger.info(f"Created workflow {workflow_id}: {workflow.name}")

        return WorkflowResponse(
            id=workflow_id,
            name=workflow.name,
            description=workflow.description,
            status="created",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            vueflow_data=workflow.vueflow_data,
            workspace_path=workflow.workspace_path,
            validation_status=validation_result,
            execution_count=0,
            last_execution_id=None,
            metadata=workflow.metadata
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create workflow {workflow.name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow creation failed: {str(e)}"
        )


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    db=Depends(get_database)
) -> WorkflowResponse:
    """Get workflow by ID"""
    try:
        workflow_data = await get_workflow_from_database(db, workflow_id)

        if not workflow_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )

        # Get validation status
        validation_status = await get_workflow_validation_status(workflow_id)

        # Get execution history
        execution_history = await get_workflow_execution_history(db, workflow_id)

        return WorkflowResponse(
            id=workflow_id,
            name=workflow_data["name"],
            description=workflow_data["description"],
            status=workflow_data["status"],
            created_at=datetime.fromisoformat(workflow_data["created_at"]),
            updated_at=datetime.fromisoformat(workflow_data.get("updated_at", workflow_data["created_at"])),
            vueflow_data=workflow_data["vueflow_data"],
            workspace_path=workflow_data["workspace_path"],
            validation_status=validation_status,
            execution_count=len(execution_history),
            last_execution_id=execution_history[-1]["id"] if execution_history else None,
            metadata=workflow_data.get("metadata", {})
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow {workflow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve workflow: {str(e)}"
        )


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    workflow_update: WorkflowUpdate,
    db=Depends(get_database),
    perm_manager: PermissionManager = Depends(get_permission_manager)
) -> WorkflowResponse:
    """Update existing workflow"""
    try:
        # Check if workflow exists
        existing_workflow = await get_workflow_from_database(db, workflow_id)
        if not existing_workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )

        # Validate workspace permissions if workspace is being updated
        if workflow_update.workspace_path:
            workspace_perms = await perm_manager.check_workspace_permissions(
                workflow_update.workspace_path
            )
            if not workspace_perms["exists"] and not workspace_perms.get("parent_writable", False):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid workspace directory"
                )

        # Update workflow data
        update_data = workflow_update.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.now().isoformat()

        # Handle vueflow_data update
        if "vueflow_data" in update_data and update_data["vueflow_data"]:
            existing_workflow["vueflow_data"] = update_data["vueflow_data"]
        
        # Handle workspace_path update (if provided)
        if "workspace_path" in update_data and update_data["workspace_path"]:
            existing_workflow["workspace_path"] = update_data["workspace_path"]

        # Merge with existing data (excluding vueflow_data and workspace_path which are handled above)
        for key, value in update_data.items():
            if key not in ["id", "vueflow_data", "workspace_path"]:  # Don't allow ID changes, handle vueflow_data and workspace_path separately
                existing_workflow[key] = value

        # Save updated workflow
        await save_workflow_to_database(db, existing_workflow)

        # Update file-based config
        workflow_dir = Path("data/workflows") / workflow_id
        if workflow_dir.exists():
            config_file = workflow_dir / "config.yaml"
            with open(config_file, 'w') as f:
                import yaml
                yaml.safe_dump(existing_workflow, f, default_flow_style=False)

        logger.info(f"Updated workflow {workflow_id}")

        return await get_workflow(workflow_id, db)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update workflow {workflow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow update failed: {str(e)}"
        )


@router.delete("/{workflow_id}", response_model=SuccessResponse)
async def delete_workflow(
    workflow_id: str,
    db=Depends(get_database)
) -> SuccessResponse:
    """Delete workflow"""
    try:
        # Check if workflow exists
        workflow_data = await get_workflow_from_database(db, workflow_id)
        if not workflow_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )

        # Check if workflow is currently running
        if workflow_data.get("status") == "running":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete workflow that is currently running"
            )

        # Delete from database
        await delete_workflow_from_database(db, workflow_id)

        # Delete workflow directory
        workflow_dir = Path("data/workflows") / workflow_id
        if workflow_dir.exists():
            shutil.rmtree(workflow_dir, ignore_errors=True)

        logger.info(f"Deleted workflow {workflow_id}")

        return SuccessResponse(
            success=True,
            message=f"Workflow {workflow_id} deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete workflow {workflow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow deletion failed: {str(e)}"
        )


@router.get("/{workflow_id}/status", response_model=WorkflowStatus)
async def get_workflow_status(
    workflow_id: str,
    db=Depends(get_database)
) -> WorkflowStatus:
    """Get current workflow status"""
    try:
        workflow_data = await get_workflow_from_database(db, workflow_id)
        if not workflow_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )

        return WorkflowStatus(
            workflow_id=workflow_id,
            status=workflow_data.get("status", "unknown"),
            engine_status={},
            last_updated=datetime.now()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow status {workflow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow status: {str(e)}"
        )


# Helper functions
async def validate_vueflow_structure(vueflow_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate VueFlow data structure"""
    try:
        errors = []
        warnings = []

        # Check required keys
        if "nodes" not in vueflow_data:
            errors.append("Missing 'nodes' in VueFlow data")

        if "edges" not in vueflow_data:
            errors.append("Missing 'edges' in VueFlow data")

        nodes = vueflow_data.get("nodes", [])
        edges = vueflow_data.get("edges", [])

        # Validate nodes
        if not isinstance(nodes, list):
            errors.append("'nodes' must be a list")
        else:
            for i, node in enumerate(nodes):
                if not isinstance(node, dict):
                    errors.append(f"Node {i} must be an object")
                    continue

                if "id" not in node:
                    errors.append(f"Node {i} missing 'id'")

                if "type" not in node:
                    warnings.append(f"Node {i} missing 'type'")

        # Validate edges
        if not isinstance(edges, list):
            errors.append("'edges' must be a list")
        else:
            for i, edge in enumerate(edges):
                if not isinstance(edge, dict):
                    errors.append(f"Edge {i} must be an object")
                    continue

                if "id" not in edge:
                    errors.append(f"Edge {i} missing 'id'")

                if "source" not in edge or "target" not in edge:
                    errors.append(f"Edge {i} missing 'source' or 'target'")

        # Check for connected components
        node_ids = {node.get("id") for node in nodes if node.get("id")}
        edge_sources = {edge.get("source") for edge in edges if edge.get("source")}
        edge_targets = {edge.get("target") for edge in edges if edge.get("target")}

        disconnected_nodes = node_ids - edge_sources - edge_targets
        if disconnected_nodes and len(disconnected_nodes) != len(node_ids):
            warnings.append(f"Some nodes appear disconnected: {disconnected_nodes}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Validation error: {str(e)}"],
            "warnings": []
        }


async def save_workflow_to_database(db, workflow_data: Dict[str, Any]):
    """
    Save workflow data to database.
    
    Args:
        db: Database connection (sqlite3.Connection or similar)
        workflow_data: Workflow data dictionary
    """
    try:
        cursor = db.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO workflows (
                id, name, description, vueflow_data, workspace_path,
                status, created_at, updated_at, metadata, workflow_format, workflow_document
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            workflow_data["id"],
            workflow_data["name"],
            workflow_data["description"],
            json.dumps(workflow_data.get("vueflow_data", {})),
            workflow_data["workspace_path"],
            workflow_data["status"],
            workflow_data["created_at"],
            workflow_data.get("updated_at", workflow_data["created_at"]),
            json.dumps(workflow_data.get("metadata", {})),
            workflow_data.get("workflow_format"),
            workflow_data.get("workflow_document")
        ))

        db.commit()

    except Exception as e:
        logger.error(f"Failed to save workflow to database: {e}")
        raise


async def get_workflow_from_database(db, workflow_id: str) -> Optional[Dict[str, Any]]:
    """Get workflow data from database"""
    try:
        cursor = db.cursor()

        cursor.execute("""
            SELECT id, name, description, vueflow_data, workspace_path,
                   status, created_at, updated_at, metadata
            FROM workflows WHERE id = ?
        """, (workflow_id,))

        row = cursor.fetchone()
        if not row:
            return None

        return {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "vueflow_data": json.loads(row[3]),
            "workspace_path": row[4],
            "status": row[5],
            "created_at": row[6],
            "updated_at": row[7],
            "metadata": json.loads(row[8]) if row[8] else {}
        }

    except Exception as e:
        logger.error(f"Failed to get workflow from database: {e}")
        return None


async def delete_workflow_from_database(db, workflow_id: str):
    """Delete workflow from database"""
    try:
        cursor = db.cursor()

        cursor.execute("DELETE FROM workflows WHERE id = ?", (workflow_id,))

        db.commit()

    except Exception as e:
        logger.error(f"Failed to delete workflow from database: {e}")
        raise


async def get_workflow_validation_status(workflow_id: str) -> WorkflowValidation:
    """Get workflow validation status"""
    try:
        workflow_dir = Path("data/workflows") / workflow_id

        generated_files = []
        if workflow_dir.exists():
            for file_path in workflow_dir.rglob("*"):
                if file_path.is_file() and file_path.name != "config.yaml":
                    generated_files.append(str(file_path.relative_to(workflow_dir)))

        return WorkflowValidation(
            valid=bool(generated_files),
            errors=[],
            warnings=[],
            generated_files=generated_files
        )

    except Exception as e:
        logger.error(f"Failed to get validation status for {workflow_id}: {e}")
        return WorkflowValidation(
            valid=False,
            errors=[f"Failed to get validation status: {str(e)}"],
            warnings=[],
            generated_files=[]
        )


async def get_workflow_execution_history(db, workflow_id: str) -> List[Dict[str, Any]]:
    """Get workflow execution history"""
    try:
        cursor = db.cursor()

        # Check if completed_at column exists
        cursor.execute("PRAGMA table_info(executions)")
        columns = [row[1] for row in cursor.fetchall()]
        has_completed_at = 'completed_at' in columns
        
        if has_completed_at:
            cursor.execute("""
                SELECT id, status, created_at, completed_at
                FROM executions
                WHERE workflow_id = ?
                ORDER BY created_at DESC
            """, (workflow_id,))
        else:
            cursor.execute("""
                SELECT id, status, created_at, COALESCE(end_time, created_at) as completed_at
                FROM executions
                WHERE workflow_id = ?
                ORDER BY created_at DESC
            """, (workflow_id,))
        rows = cursor.fetchall()
        return [
            {"id": row[0], "status": row[1], "created_at": row[2], "completed_at": row[3]}
            for row in rows
        ]

    except Exception as e:
        logger.error(f"Failed to get execution history for {workflow_id}: {e}")
        return []
from uuid import uuid4
from app.models.schemas import ExecuteRequest, WorkflowExecutionResponse, BatchConfig, BatchSample
from app.services.paths import get_workflows_root
from app.dependencies import get_workflow_service
from app.services.runner import execution_manager


def _load_sample_context_from_workspace(user_id: str, workspace_id: str, sample_id: str) -> Optional[Dict[str, str]]:
    """
    从工作区的 samples.json 加载样品上下文（新方法，推荐使用）。

    这是 implement-workspace-hierarchy 引入的新方式。
    样品定义存储在 samples.json 中，由 UnifiedWorkspaceManager 管理。

    Args:
        user_id: 用户 ID
        workspace_id: 工作区 ID
        sample_id: 样品 ID

    Returns:
        样品上下文字典，如果样品不存在则返回 None
    """
    try:
        from app.services.unified_workspace_manager import get_unified_workspace_manager
        manager = get_unified_workspace_manager()
        return manager.get_sample_context(user_id, workspace_id, sample_id)
    except Exception as e:
        logger.warning(f"Failed to load sample context from workspace: {e}")
        return None


async def _run_workflow_background(
    workflow_service,
    wf_v2: Dict[str, Any],
    workspace_dir: Path,
    execution_id: str,
    workflow_id: str,
    sample_ctx: Dict[str, str],
    dryrun: bool,
    resume: bool,
    simulate: bool,
) -> None:
    """后台执行工作流，完成后更新 execution_store 与 execution_manager"""
    execution_store = workflow_service.execution_store
    event_loop = asyncio.get_running_loop()
    try:
        from app.core.websocket import manager as ws_manager
    except Exception:
        ws_manager = None

    async def _broadcast_status(status: str, progress: int = None):
        """Broadcast status update to WebSocket"""
        try:
            if not ws_manager:
                return
            await ws_manager.broadcast_to_execution(execution_id, {
                "type": "status",
                "status": status,
                "progress": progress,
                "execution_id": execution_id
            })
        except Exception:
            pass  # WebSocket may not be available

    def _make_log_callback(eid: str):
        def _cb(msg: str, level: str = "info"):
            node_id = None
            if isinstance(msg, str) and msg.startswith("[command_trace] "):
                try:
                    trace_payload = json.loads(msg.split("[command_trace] ", 1)[1])
                    node_id = trace_payload.get("node_id")
                    if node_id:
                        execution_store.update_node_command_trace(eid, node_id, trace_payload)
                except Exception as e:
                    logger.warning("Failed to persist command trace for execution %s: %s", eid, e)

            log_entry = {
                "timestamp": utc_now_iso_z(),
                "level": (level or "info").lower(),
                "message": msg,
            }
            if node_id:
                log_entry["node_id"] = node_id
            ex = execution_manager.get(eid)
            if ex:
                ex.logs.append(log_entry)
            if ws_manager:
                try:
                    asyncio.run_coroutine_threadsafe(
                        ws_manager.broadcast_to_execution(
                            eid,
                            {
                                "type": "log",
                                "data": log_entry,
                                "execution_id": eid,
                            },
                        ),
                        event_loop,
                    )
                except Exception:
                    pass
        return _cb

    log_cb = _make_log_callback(execution_id) if not (dryrun or simulate) else None

    # Broadcast running status
    await _broadcast_status("running", 0)

    try:
        result = await workflow_service.execute_workflow(
            workflow_json=wf_v2,
            workspace_path=workspace_dir,
            parameters={"sample_context": sample_ctx, "sample": sample_ctx.get("sample")},
            dryrun=dryrun,
            resume=resume,
            simulate=simulate,
            execution_id=execution_id,
            workflow_id=workflow_id,
            log_callback=log_cb,
        )
        exec_status = result.get("status", "completed")
        exec_error = result.get("error", "")
        execution_store.finish(execution_id, exec_status)
        execution_manager.update_status(
            execution_id,
            exec_status,
            end_time=utc_now_iso_z(),
            progress=100 if exec_status == "completed" else 0,
        )

        # Broadcast final status
        await _broadcast_status(exec_status, 100 if exec_status == "completed" else 0)

        if exec_error:
            ex = execution_manager.get(execution_id)
            if ex:
                ex.logs.append({
                    "timestamp": utc_now_iso_z(),
                    "level": "error",
                    "message": exec_error,
                })
    except Exception as e:
        logger.exception("Background workflow execution failed: %s", e)
        execution_store.finish(execution_id, "failed")
        execution_manager.update_status(
            execution_id,
            "failed",
            end_time=utc_now_iso_z(),
            progress=0,
        )

        # Broadcast failed status
        await _broadcast_status("failed", 0)

        ex = execution_manager.get(execution_id)
        if ex:
            ex.logs.append({
                "timestamp": utc_now_iso_z(),
                "level": "error",
                "message": str(e),
            })


@router.post("/execute", response_model=WorkflowExecutionResponse)
async def execute(
    request_data: dict,
    background_tasks: BackgroundTasks,
    db=Depends(get_database),
    workflow_service=Depends(get_workflow_service),
):
    """
    Execute workflow using TDEase 2.0 engine (FlowEngine + LocalExecutor).
    Supports dryrun, resume (breakpoint continuation), simulate (mock run).
    For actual execution: returns immediately with executionId; workflow runs in background.
    Frontend should poll GET /api/executions/{execution_id} and /logs for status and logs.
    """
    try:
        from src.workflow.normalizer import WorkflowNormalizer
        # 新架构：支持 workflow_id（从数据库加载）或 workflow（直接传递）
        workflow_id_param = request_data.get("workflow_id") if isinstance(request_data, dict) else None
        workflow_raw = request_data.get("workflow") if isinstance(request_data, dict) else None
        parameters_raw = request_data.get("parameters", {}) if isinstance(request_data, dict) else {}

        # 优先使用 workflow_id 从数据库加载
        if workflow_id_param:
            workflow_data = await get_workflow_from_database(db, workflow_id_param)
            if not workflow_data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workflow {workflow_id_param} not found")
            workflow_raw = workflow_data.get("vueflow_data", {})
        elif isinstance(workflow_raw, str):
            # 兼容旧格式：workflow 参数是 ID
            workflow_data = await get_workflow_from_database(db, workflow_raw)
            if not workflow_data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workflow {workflow_raw} not found")
            workflow_raw = workflow_data.get("vueflow_data", {})
        wf_v2 = WorkflowNormalizer().normalize(workflow_raw)
        metadata = wf_v2.get("metadata", {}) or {}
        edges = wf_v2.get("edges", [])
        logger.info("Execute workflow edges: %s", [(e.get("source"), "->", e.get("target")) for e in edges])
        workflow_id = str(metadata.get("id") or f"wf_{utc_now().strftime('%Y%m%d_%H%M%S')}")

        # ===== 工作区路径：新架构用 workspace 目录，兼容旧格式用 data/workflows/{workflow_id} =====
        user_id = request_data.get("user_id") if isinstance(request_data, dict) else None
        workspace_id = request_data.get("workspace_id") if isinstance(request_data, dict) else None
        sample_ids = request_data.get("sample_ids") if isinstance(request_data, dict) else None

        if user_id and workspace_id and sample_ids:
            from app.services.unified_workspace_manager import get_unified_workspace_manager
            manager = get_unified_workspace_manager()
            workspace_dir = manager.get_workspace_path(user_id, workspace_id)
            workspace_dir = workspace_dir.resolve() if isinstance(workspace_dir, Path) else Path(workspace_dir).resolve()
        else:
            root_base = Path(get_workflows_root())
            root_base.mkdir(parents=True, exist_ok=True)
            workspace_dir = root_base / workflow_id

        workspace_dir.mkdir(parents=True, exist_ok=True)
        (workspace_dir / "logs").mkdir(parents=True, exist_ok=True)
        (workspace_dir / "results").mkdir(parents=True, exist_ok=True)
        try:
            cursor = db.cursor()
            cursor.execute("SELECT id FROM workflows WHERE id = ?", (workflow_id,))
            if not cursor.fetchone():
                workflow_config = {
                    "id": workflow_id,
                    "name": metadata.get("name", "Direct Execution Workflow"),
                    "description": metadata.get("description", ""),
                    "vueflow_data": wf_v2,
                    "workspace_path": str(workspace_dir),
                    "created_at": utc_now_iso_z(),
                    "status": "created",
                    "metadata": metadata,
                    "workflow_format": "vueflow",
                }
                workflow_config["workflow_document"] = json.dumps(wf_v2)
                await save_workflow_to_database(db, workflow_config)
        except Exception as e:
            logger.warning("Ensure workflow in DB: %s", e)
        execution_id = str(uuid4())
        execution_store = workflow_service.execution_store

        dryrun = bool(parameters_raw.get("dryrun", False))
        # 断点续传：默认 True，检查输出文件存在则跳过已完成的节点；传 resume=False 可强制从头执行
        resume = bool(parameters_raw.get("resume", True))
        simulate = bool(parameters_raw.get("simulate", False))

        # ===== 样品上下文：新架构(workspace) 或 兼容旧格式(parameters.sample_context) =====
        sample_id = None  # Initialize sample_id for execution record
        if user_id and workspace_id and sample_ids:
            # 新架构: 从 database 加载
            sample_id = sample_ids[0] if isinstance(sample_ids, list) else sample_ids
            ctx = _load_sample_context_from_workspace(user_id, workspace_id, sample_id)
            if not ctx:
                raise HTTPException(
                    status_code=404,
                    detail=f"Sample '{sample_id}' not found in workspace '{workspace_id}' for user '{user_id}'."
                )
            sample_ctx = ctx
            logger.info(f"Loaded sample context from workspace: user={user_id}, workspace={workspace_id}, sample={sample_id}")
        else:
            # 兼容旧格式: dryrun/simulate 时允许仅传 parameters.sample_context
            sample_ctx = parameters_raw.get("sample_context", {}) or {"sample": parameters_raw.get("sample", "default")}
            if not sample_ctx:
                raise HTTPException(
                    status_code=400,
                    detail="Provide either (user_id, workspace_id, sample_ids) or parameters.sample_context."
                )

        # 确保所有值都是字符串
        for k, v in sample_ctx.items():
            if v is not None:
                sample_ctx[k] = str(v)

        # 注入 raw_path/fasta_path 到 data_loader/fasta_loader 节点，供 validator 通过
        _inject_sample_paths_into_workflow(wf_v2, sample_ctx)

        # 检测结构变更：如果 workflow_id 存在，比较当前结构与上次执行的结构
        workflow_snapshot = None
        try:
            existing_workflow = await get_workflow_from_database(db, workflow_id)
            if existing_workflow:
                from app.services.workflow_diff import get_last_execution_snapshot
                last_exec_id, last_snapshot = get_last_execution_snapshot(db, workflow_id)
                if last_snapshot:
                    if has_structure_changed(last_snapshot, wf_v2):
                        workflow_snapshot = json.dumps(wf_v2)
                else:
                    if has_structure_changed(existing_workflow.get("vueflow_data", {}), wf_v2):
                        workflow_snapshot = json.dumps(wf_v2)
            else:
                workflow_snapshot = json.dumps(wf_v2)
        except Exception as e:
            logger.warning(f"Failed to detect structure change, saving snapshot anyway: {e}")
            workflow_snapshot = json.dumps(wf_v2)

        execution_store.create(execution_id, workflow_id, str(workspace_dir), sample_id, workflow_snapshot)
        execution_manager.create(execution_id, str(workspace_dir), workflow_id)
        execution_manager.update_status(execution_id, "running", start_time=utc_now_iso_z())
        execution_store.start(execution_id)
        for node in wf_v2.get("nodes", []):
            nid = node.get("id")
            if nid:
                execution_store.create_node(execution_id, nid, f"node_{nid}")

        # dryrun/simulate 快速完成，同步执行；实际执行则后台运行，立即返回
        if dryrun or simulate:
            await _run_workflow_background(
                workflow_service, wf_v2, workspace_dir, execution_id, workflow_id,
                sample_ctx, dryrun, resume, simulate,
            )
            ex = execution_manager.get(execution_id)
            resp_logs = [log for log in (ex.logs if ex else [])] if ex else []
            return WorkflowExecutionResponse(
                executionId=execution_id,
                status=ex.status if ex else "completed",
                startTime=ex.start_time or utc_now_iso_z(),
                endTime=ex.end_time or utc_now_iso_z(),
                progress=ex.progress if ex else 100,
                logs=resp_logs,
                nodes=[{"node_id": n["node_id"], "status": n["status"]} for n in execution_store.get_nodes(execution_id)],
                results=None,
            )
        else:
            background_tasks.add_task(
                _run_workflow_background,
                workflow_service, wf_v2, workspace_dir, execution_id, workflow_id,
                sample_ctx, dryrun, resume, simulate,
            )
            return WorkflowExecutionResponse(
                executionId=execution_id,
                status="running",
                startTime=utc_now_iso_z(),
                endTime=None,
                progress=0,
                logs=[],
                nodes=[{"node_id": nid, "status": "pending"} for nid in [n.get("id") for n in wf_v2.get("nodes", [])]],
                results=None,
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Execute failed: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Execution failed: {e}")


@router.get("/{workflow_id}/export/cwl", response_class=Response)
async def export_workflow_to_cwl(
    workflow_id: str,
    db=Depends(get_database),
    format: str = "yaml"
) -> Response:
    """
    Export workflow from database to CWL format.
    
    Args:
        workflow_id: Workflow ID
        db: Database connection
        format: Output format ("yaml" or "json")
        
    Returns:
        CWL workflow file
    """
    try:
        # Get workflow from database
        workflow_data = await get_workflow_from_database(db, workflow_id)
        if not workflow_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        # Get workflow JSON
        workflow_json = workflow_data.get("vueflow_data", {})
        if not workflow_json:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Workflow JSON data not found"
            )
        
        # Export to CWL
        from app.services.cwl_exporter import CWLExporter
        exporter = CWLExporter()
        cwl_workflow = exporter.export_workflow_to_cwl(workflow_json, tools=None)
        
        # Format output
        import yaml as yaml_lib
        import json as json_lib
        
        if format.lower() == "json":
            content = json_lib.dumps(cwl_workflow, indent=2)
            media_type = "application/json"
            filename = f"{workflow_id}.cwl.json"
        else:
            content = yaml_lib.dump(cwl_workflow, default_flow_style=False, allow_unicode=True)
            media_type = "application/x-yaml"
            filename = f"{workflow_id}.cwl"
        
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export workflow to CWL: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CWL export failed: {str(e)}"
        )


@router.post("/{workflow_id}/batch-config", response_model=SuccessResponse)
async def save_batch_config(
    workflow_id: str,
    batch_config: BatchConfig,
    db=Depends(get_database)
) -> SuccessResponse:
    """Save batch processing configuration for a workflow"""
    try:
        cursor = db.cursor()
        
        # Check if workflow exists
        cursor.execute("SELECT id FROM workflows WHERE id = ?", (workflow_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow '{workflow_id}' not found"
            )
        
        # Save batch config as JSON
        batch_config_json = json.dumps(batch_config.model_dump(), ensure_ascii=False)
        cursor.execute("""
            UPDATE workflows
            SET batch_config = ?, updated_at = ?
            WHERE id = ?
        """, (batch_config_json, utc_now_iso_z(), workflow_id))
        db.commit()
        
        logger.info(f"Batch config saved for workflow {workflow_id}")
        return SuccessResponse(message="Batch configuration saved successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save batch config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save batch configuration: {str(e)}"
        )


@router.get("/{workflow_id}/batch-config", response_model=BatchConfig)
async def get_batch_config(
    workflow_id: str,
    db=Depends(get_database)
) -> BatchConfig:
    """Get batch processing configuration for a workflow"""
    try:
        cursor = db.cursor()
        cursor.execute("SELECT batch_config FROM workflows WHERE id = ?", (workflow_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow '{workflow_id}' not found"
            )
        
        batch_config_json = row[0]
        if not batch_config_json:
            # Return empty batch config if not set
            return BatchConfig(samples=[], global_params={})
        
        batch_config_dict = json.loads(batch_config_json)
        return BatchConfig(**batch_config_dict)
        
    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid batch config JSON for workflow {workflow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Invalid batch configuration format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to get batch config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get batch configuration: {str(e)}"
        )


def _inject_sample_paths_into_workflow(wf: Dict[str, Any], sample_ctx: Dict[str, str]) -> None:
    """将 sample_ctx 中的 raw_path/fasta_path 注入到 data_loader/fasta_loader 节点，供 validator 校验通过"""
    for node in wf.get("nodes", []):
        data = node.get("data", {}) or {}
        tool_type = data.get("type", "")
        params = data.get("params", {}) or {}
        if tool_type == "data_loader" and sample_ctx.get("raw_path"):
            params["input_sources"] = [sample_ctx["raw_path"]]
        elif tool_type == "fasta_loader" and sample_ctx.get("fasta_path"):
            params["fasta_file"] = sample_ctx["fasta_path"]
        node["data"] = {**data, "params": params}


def _replace_placeholders(workflow_json: Dict[str, Any], placeholder_values: Dict[str, Any]) -> Dict[str, Any]:
    """Replace placeholder variables in workflow JSON with actual values"""
    import json
    workflow_str = json.dumps(workflow_json)
    
    for key, value in placeholder_values.items():
        placeholder = f"{{{key}}}"
        workflow_str = workflow_str.replace(placeholder, str(value))
    
    return json.loads(workflow_str)


@router.post("/{workflow_id}/execute-batch", response_model=List[WorkflowExecutionResponse])
async def execute_batch(
    workflow_id: str,
    user_id: str,
    workspace_id: str,
    sample_ids: List[str],
    db=Depends(get_database),
    workflow_service=Depends(get_workflow_service),
) -> List[WorkflowExecutionResponse]:
    """
    批量执行工作流 - 基于新架构，从 samples.json 加载样品上下文

    新架构参数:
    - user_id: 用户ID
    - workspace_id: 工作区ID
    - sample_ids: 样品ID列表

    复用单样本执行路径，遍历 samples.json 中的样品定义。
    """
    try:
        from app.services.paths import get_workflows_root
        from uuid import uuid4

        # Get workflow
        cursor = db.cursor()
        cursor.execute("""
            SELECT vueflow_data, workflow_document, workflow_format
            FROM workflows
            WHERE id = ?
        """, (workflow_id,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow '{workflow_id}' not found"
            )

        vueflow_data_str, workflow_document_str, workflow_format = row
        workflow_json = json.loads(vueflow_data_str)

        # 验证样品存在
        from app.services.unified_workspace_manager import get_unified_workspace_manager
        manager = get_unified_workspace_manager()
        samples = manager.list_samples(user_id, workspace_id)
        valid_samples = set(s.get("id") for s in samples)

        # 验证所有请求的样品ID都存在
        invalid_samples = set(sample_ids) - valid_samples
        if invalid_samples:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Samples not found in workspace '{workspace_id}': {invalid_samples}. "
                      f"Available samples: {valid_samples}"
            )

        from src.workflow.normalizer import WorkflowNormalizer
        normalizer = WorkflowNormalizer()
        wf_v2 = normalizer.normalize(workflow_json)

        # Create workspace directory
        root_base = Path(get_workflows_root())
        root_base.mkdir(parents=True, exist_ok=True)

        execution_responses = []

        # 遍历样品，复用单样本执行逻辑
        for sample_id in sample_ids:
            # 加载样品上下文（从 samples.json）
            sample_ctx = _load_sample_context_from_workspace(user_id, workspace_id, sample_id)
            if not sample_ctx:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Sample '{sample_id}' not found in workspace '{workspace_id}'"
                )

            # 每个样本独立的工作区目录
            workspace_dir = root_base / workflow_id / f"batch_{sample_id}"
            workspace_dir.mkdir(parents=True, exist_ok=True)
            (workspace_dir / "logs").mkdir(parents=True, exist_ok=True)
            (workspace_dir / "results").mkdir(parents=True, exist_ok=True)

            # 使用 UnifiedWorkspaceManager 设置执行目录
            manager.set_execution_directory(user_id, workspace_id, sample_id, str(workspace_dir))

            execution_id = str(uuid4())
            store = workflow_service.execution_store

            # 检测结构变更（仅第一个样本）
            workflow_snapshot = None
            if len(execution_responses) == 0:
                try:
                    existing_workflow = await get_workflow_from_database(db, workflow_id)
                    if existing_workflow:
                        from app.services.workflow_diff import get_last_execution_snapshot
                        last_exec_id, last_snapshot = get_last_execution_snapshot(db, workflow_id)
                        if last_snapshot:
                            if has_structure_changed(last_snapshot, wf_v2):
                                workflow_snapshot = json.dumps(wf_v2)
                        else:
                            if has_structure_changed(existing_workflow.get("vueflow_data", {}), wf_v2):
                                workflow_snapshot = json.dumps(wf_v2)
                    else:
                        workflow_snapshot = json.dumps(wf_v2)
                except Exception as e:
                    logger.warning(f"Failed to detect structure change in batch, saving snapshot: {e}")
                    workflow_snapshot = json.dumps(wf_v2)

            store.create(execution_id, workflow_id, str(workspace_dir), workflow_snapshot)
            execution_manager.create(execution_id, str(workspace_dir), workflow_id)
            execution_manager.update_status(execution_id, "running", start_time=utc_now_iso_z())
            store.start(execution_id)

            # 创建节点记录
            for node in wf_v2.get("nodes", []):
                nid = node.get("id")
                if nid:
                    store.create_node(execution_id, nid, f"node_{nid}")

            # 复用单样本执行逻辑（传递样品上下文）
            result = await workflow_service.execute_workflow(
                workflow_json=wf_v2,
                workspace_path=workspace_dir,
                parameters={
                    "user_id": user_id,
                    "workspace_id": workspace_id,
                    "sample_ids": [sample_id],
                    "sample_context": sample_ctx,
                    "sample": sample_ctx.get("sample", sample_id)
                },
                dryrun=False,
                resume=True,
                simulate=False,
                execution_id=execution_id,
                workflow_id=workflow_id,
            )

            store.finish(execution_id, result.get("status", "completed"))
            execution_manager.update_status(
                execution_id,
                result.get("status", "completed"),
                end_time=utc_now_iso_z(),
                progress=100 if result.get("status") == "completed" else 0,
            )

            execution_responses.append(WorkflowExecutionResponse(
                executionId=execution_id,
                status=result.get("status", "completed"),
                startTime=utc_now_iso_z(),
                endTime=utc_now_iso_z(),
                progress=100 if result.get("status") == "completed" else 0,
                logs=[],
                nodes=[{"node_id": k, "status": v} for k, v in result.get("nodes", {}).items()],
                results=None,
            ))

            logger.info(f"Batch execution completed for sample '{sample_id}': {execution_id}")

        return execution_responses

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch execution failed: {str(e)}"
        )


@router.get("/{workflow_id}/latest-execution")
async def get_latest_execution(
    workflow_id: str,
    db=Depends(get_database)
):
    """
    Get the most recent completed execution for a workflow.

    Returns:
    - Latest execution metadata (execution_id, status, start_time, end_time, sample_id)
    """
    try:
        from app.services.execution_store import ExecutionStore
        store = ExecutionStore()
        execution = store.get_latest_completed_execution(workflow_id)

        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No completed execution found for workflow: {workflow_id}"
            )

        return execution

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest execution: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get latest execution: {str(e)}"
        )

