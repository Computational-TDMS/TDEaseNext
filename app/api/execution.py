import logging
import json
import uuid
from fastapi import APIRouter, HTTPException, status, Query, Depends
from app.services.runner import execution_manager
from app.services.execution_store import ExecutionStore
from app.services.log_handler import log_collector
from app.services.node_data_service import resolve_node_outputs
from app.services.data_resolver_registry import get_data_resolver_registry
from app.models.schemas import WorkflowExecutionResponse, NodeStatus, LogEntry
from app.models.common import SuccessResponse
from app.dependencies import get_database
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Optional
from app.core.executor.errors import ExecutionPublicError, ExecutorError

logger = logging.getLogger(__name__)
router = APIRouter()
execution_store = ExecutionStore()
TERMINAL_STATUSES = {"completed", "failed", "cancelled"}


def _public_execution_error(exc: Exception) -> ExecutionPublicError:
    if isinstance(exc, ExecutorError):
        return exc.to_public_error()
    return ExecutionPublicError(
        code="EXECUTION_INTERNAL_ERROR",
        message="Execution request failed due to an internal error.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _raise_sanitized_execution_http_error(operation: str, exc: Exception) -> None:
    correlation_id = uuid.uuid4().hex
    public_error = _public_execution_error(exc)
    logger.exception("%s failed [correlation_id=%s]: %s", operation, correlation_id, exc)
    raise HTTPException(
        status_code=public_error.status_code,
        detail=public_error.to_payload(correlation_id),
    )


def _parse_command_trace(value):
    if not value:
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return None
    return None


class _PersistedExecutionView:
    def __init__(self, record: dict):
        self.id = record["id"]
        self.status = record.get("status", "unknown")
        self.start_time = record.get("start_time")
        self.end_time = record.get("end_time")
        self.progress = 100 if self.status == "completed" else 0
        self.logs = []
        self.workspace = record.get("workspace_path")


def _get_execution_with_fallback(execution_id: str):
    runtime = execution_manager.get(execution_id)
    persisted = execution_store.get_execution(execution_id)

    if runtime and persisted:
        persisted_status = persisted.get("status")
        if persisted_status in TERMINAL_STATUSES:
            runtime.status = persisted_status
            runtime.end_time = persisted.get("end_time") or runtime.end_time
            runtime.start_time = runtime.start_time or persisted.get("start_time")
            runtime.progress = 100 if persisted_status == "completed" else 0

    if runtime:
        return runtime
    if persisted:
        return _PersistedExecutionView(persisted)
    return None

@router.get("/{execution_id}", response_model=WorkflowExecutionResponse)
async def get_execution_status(execution_id: str) -> WorkflowExecutionResponse:
    ex = _get_execution_with_fallback(execution_id)
    if not ex:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    
    # Get node statuses
    node_records = execution_store.get_nodes(execution_id)
    nodes = [
        NodeStatus(
            node_id=node["node_id"],
            rule_name=node.get("rule_name"),
            status=node["status"],
            progress=node.get("progress", 0),
            start_time=node.get("start_time"),
            end_time=node.get("end_time"),
            error_message=node.get("error_message"),
            command_trace=_parse_command_trace(node.get("command_trace")),
        )
        for node in node_records
    ]
    
    # Get logs from log handler
    log_handler = log_collector.get_handler(execution_id)
    logs = []
    if log_handler:
        logs = [
            LogEntry(
                timestamp=log["timestamp"],
                level=log["level"],
                message=log["message"]
            )
            for log in log_handler.get_logs(limit=1000)
        ]
    else:
        # Fallback to execution manager logs
        logs = [
            LogEntry(
                timestamp=log["timestamp"],
                level=log["level"],
                message=log["message"]
            )
            for log in ex.logs
        ]
    
    return WorkflowExecutionResponse(
        executionId=ex.id,
        status=ex.status,
        startTime=ex.start_time,
        endTime=ex.end_time,
        progress=ex.progress,
        logs=logs,
        nodes=nodes,
        results=None
    )

@router.get("/{execution_id}/logs")
async def get_execution_logs(
    execution_id: str,
    node_id: Optional[str] = Query(None, description="Filter by node ID"),
    level: Optional[str] = Query(None, description="Filter by log level"),
    limit: Optional[int] = Query(1000, description="Limit number of logs")
):
    """Get execution logs, optionally filtered by node or level."""
    ex = _get_execution_with_fallback(execution_id)
    if not ex:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    
    # Try to get logs from log handler
    log_handler = log_collector.get_handler(execution_id)
    if log_handler:
        logs = log_handler.get_logs(node_id=node_id, level=level, limit=limit)
    else:
        # Fallback to execution manager logs
        logs = ex.logs
        if node_id:
            # Filter by node_id in message (heuristic)
            logs = [log for log in logs if node_id in log.get("message", "")]
        if level:
            logs = [log for log in logs if log.get("level", "").lower() == level.lower()]
        if limit:
            logs = logs[-limit:]
    
    return {"logs": logs}

@router.get("/{execution_id}/nodes")
async def get_execution_nodes(execution_id: str):
    """Get all node statuses for an execution."""
    ex = _get_execution_with_fallback(execution_id)
    if not ex:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    
    node_records = execution_store.get_nodes(execution_id)
    nodes = [
        NodeStatus(
            node_id=node["node_id"],
            rule_name=node.get("rule_name"),
            status=node["status"],
            progress=node.get("progress", 0),
            start_time=node.get("start_time"),
            end_time=node.get("end_time"),
            error_message=node.get("error_message"),
            command_trace=_parse_command_trace(node.get("command_trace")),
        )
        for node in node_records
    ]
    
    return {"nodes": nodes}

@router.get("/{execution_id}/nodes/{node_id}")
async def get_execution_node(execution_id: str, node_id: str):
    """Get specific node status."""
    ex = _get_execution_with_fallback(execution_id)
    if not ex:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
    
    node_record = execution_store.get_node(execution_id, node_id)
    if not node_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
    
    return NodeStatus(
        node_id=node_record["node_id"],
        rule_name=node_record.get("rule_name"),
        status=node_record["status"],
        progress=node_record.get("progress", 0),
        start_time=node_record.get("start_time"),
        end_time=node_record.get("end_time"),
        error_message=node_record.get("error_message"),
        command_trace=_parse_command_trace(node_record.get("command_trace")),
    )


@router.get("/{execution_id}/nodes/{node_id}/trace")
async def get_execution_node_trace(execution_id: str, node_id: str):
    """Get command assembly trace for one node."""
    ex = _get_execution_with_fallback(execution_id)
    if not ex:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")

    node_record = execution_store.get_node(execution_id, node_id)
    if not node_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")

    trace = _parse_command_trace(node_record.get("command_trace"))
    if not trace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Command trace not found")
    return {"execution_id": execution_id, "node_id": node_id, "command_trace": trace}

@router.post("/{execution_id}/stop", response_model=SuccessResponse)
async def stop_execution(execution_id: str) -> SuccessResponse:
    """
    Stop a running workflow execution.

    Cancels all running nodes and updates the execution status to "cancelled".
    """
    ex = execution_manager.get(execution_id)
    if not ex:
        logger.warning(f"[API] Stop requested for non-existent execution {execution_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")

    logger.info(f"[API] Stop requested for execution {execution_id}, current status: {ex.status}")
    await execution_manager.stop(execution_id)
    return SuccessResponse(success=True, message=f"Execution {execution_id} stopped")

@router.get("/{execution_id}/download")
async def download_execution_result(execution_id: str):
    ex = _get_execution_with_fallback(execution_id)
    if not ex:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    results_dir = Path(ex.workspace) / "results"
    if not results_dir.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No results")
    for p in results_dir.glob("*"):
        if p.is_file():
            return FileResponse(str(p), filename=p.name)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No result files")


@router.get("/{execution_id}/nodes/{node_id}/data")
async def get_node_data(
    execution_id: str,
    node_id: str,
    port_id: Optional[str] = Query(None, description="Filter by specific output port ID"),
    include_data: bool = Query(False, description="Include parsed data in response"),
    max_rows: Optional[int] = Query(None, description="Maximum rows to parse (if include_data=true)"),
    db=Depends(get_database)
):
    """
    Get node output data with optional inline data content.

    Query parameters:
    - port_id: Optional port ID to filter outputs (for multi-output tools)
    - include_data: If true, parse and include file data in response
    - max_rows: Maximum rows to parse (for tabular files)

    Returns:
    - List of output ports with file metadata and optional parsed data
    """
    try:
        result = resolve_node_outputs(
            execution_id=execution_id,
            node_id=node_id,
            db=db,
            port_id=port_id,
            include_data=include_data,
            max_rows=max_rows
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        _raise_sanitized_execution_http_error("Get node data", e)


@router.get("/{execution_id}/nodes/{node_id}/files")
async def get_node_files(
    execution_id: str,
    node_id: str,
    db=Depends(get_database)
):
    """
    Get node output files list (without data content).

    Returns:
    - List of output ports with file metadata (no data content)
    """
    try:
        result = resolve_node_outputs(
            execution_id=execution_id,
            node_id=node_id,
            db=db,
            include_data=False
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        _raise_sanitized_execution_http_error("Get node files", e)


@router.get("/{execution_id}/nodes/{node_id}/interactive-data/{selection_key}")
async def get_interactive_data(
    execution_id: str,
    node_id: str,
    selection_key: str,
    resolver: str = Query(..., description="Resolver name (e.g. topmsv_prsm)"),
    port_id: Optional[str] = Query(None, description="Source output port (e.g. html_folder)"),
    spectrum_id: Optional[int] = Query(None, description="Optional spectrum ID (for topmsv_prsm)"),
    db=Depends(get_database),
):
    """
    Generic selection-driven interactive data endpoint.

    Resolvers load detailed payload for a selection key (e.g. PrSM ID) from the
    given execution/node output, using tool-defined subResources when available.

    Example: GET .../interactive-data/7?resolver=topmsv_prsm&port_id=html_folder&spectrum_id=66
    """
    try:
        registry = get_data_resolver_registry()
        payload = registry.resolve(
            name=resolver,
            execution_id=execution_id,
            node_id=node_id,
            selection_key=selection_key,
            db=db,
            port_id=port_id,
            spectrum_id=spectrum_id,
        )
        return payload
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        _raise_sanitized_execution_http_error("Load interactive data", exc)


@router.get("/{execution_id}/nodes/{node_id}/topmsv/prsm/{prsm_id}")
async def get_topmsv_prsm_data(
    execution_id: str,
    node_id: str,
    prsm_id: int,
    spectrum_id: Optional[int] = Query(None, description="Optional spectrum ID override"),
    port_id: Optional[str] = Query(None, description="Optional source output port (defaults to html_folder)"),
    db=Depends(get_database),
):
    """
    Load normalized TopMSV payload from TopPIC HTML output (source node).
    Delegates to interactive-data with resolver=topmsv_prsm. Prefer the generic
    endpoint GET .../interactive-data/{prsm_id}?resolver=topmsv_prsm for new clients.
    """
    if prsm_id < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="prsm_id must be non-negative",
        )
    if spectrum_id is not None and spectrum_id < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="spectrum_id must be non-negative",
        )
    try:
        registry = get_data_resolver_registry()
        return registry.resolve(
            name="topmsv_prsm",
            execution_id=execution_id,
            node_id=node_id,
            selection_key=str(prsm_id),
            db=db,
            port_id=port_id or "html_folder",
            spectrum_id=spectrum_id,
        )
    except HTTPException:
        raise
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        _raise_sanitized_execution_http_error("Load TopMSV PrSM data", exc)
