"""
Nodes API Endpoints
Handles node data retrieval for interactive visualization
"""

import logging
import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import JSONResponse

from app.dependencies import get_database
from app.services.node_data_service import parse_tabular_file, resolve_node_outputs
from app.services.tool_registry import get_tool_registry
from app.services.node_data_cache import get_node_data_cache

logger = logging.getLogger(__name__)
router = APIRouter()
_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_MAX_ROW_IDS = 10000


def _validate_identifier(value: str, field_name: str) -> str:
    if not _SAFE_ID_RE.fullmatch(value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name} format.",
        )
    return value


def _resolve_outputs_or_http(execution_id: str, node_id: str, db):
    try:
        return resolve_node_outputs(
            execution_id=execution_id,
            node_id=node_id,
            db=db,
            include_data=False,
        )
    except ValueError as exc:
        message = str(exc)
        if "not found" in message.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("/executions/{execution_id}/nodes/{node_id}/data/schema")
async def get_node_data_schema(
    execution_id: str,
    node_id: str,
    port_id: Optional[str] = None,
    db=Depends(get_database)
) -> JSONResponse:
    """
    Get column schema for node output data

    Args:
        execution_id: Execution ID
        node_id: Node ID
        port_id: Optional output port ID (if multiple outputs)
        db: Database connection

    Returns:
        {
            "execution_id": str,
            "node_id": str,
            "port_id": str,
            "schema": [
                {
                    "name": str,
                    "type": str,
                    "description": str,
                    "optional": bool
                }
            ]
        }
    """
    cache = get_node_data_cache()
    execution_id = _validate_identifier(execution_id, "execution_id")
    node_id = _validate_identifier(node_id, "node_id")
    if port_id:
        _validate_identifier(port_id, "port_id")

    # Check cache first
    cache_key = f"schema_{port_id or 'default'}"
    cached_result = cache.get(execution_id, node_id, cache_key)
    if cached_result is not None:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=cached_result
        )

    try:
        # 1. Get node outputs
        outputs_info = _resolve_outputs_or_http(execution_id, node_id, db)

        # 2. Get tool definition to extract schema
        cursor = db.cursor()
        cursor.execute(
            "SELECT workflow_snapshot FROM executions WHERE id = ?",
            (execution_id,)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution not found: {execution_id}"
            )

        import json
        workflow_snapshot = json.loads(row[0])
        nodes = workflow_snapshot.get("nodes", [])
        node_data = None
        for node in nodes:
            if node.get("id") == node_id:
                node_data = node
                break

        if not node_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Node not found: {node_id}"
            )

        tool_id = node_data.get("type", "")
        tool_registry = get_tool_registry()
        tool_info = tool_registry.get(tool_id)

        if not tool_info:
            # Fallback: infer schema from file
            if port_id:
                outputs = [o for o in outputs_info["outputs"] if o["port_id"] == port_id]
            else:
                outputs = outputs_info["outputs"]

            if not outputs:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No outputs found for node: {node_id}"
                )

            # Parse first output to infer schema
            output = outputs[0]
            if not output["exists"] or not output["parseable"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Output file not available or not parseable: {output['file_name']}"
                )

            file_path = Path(output["file_path"])
            table_data = parse_tabular_file(file_path, max_rows=1)

            # Infer schema from column names and first row
            schema = []
            for col_name in table_data["columns"]:
                # Try to infer type from first row value
                col_type = "string"
                if table_data["rows"]:
                    value = table_data["rows"][0].get(col_name, "")
                    try:
                        float(value)
                        col_type = "number"
                    except (ValueError, TypeError):
                        pass

                schema.append({
                    "name": col_name,
                    "type": col_type,
                    "description": f"Column '{col_name}'",
                    "optional": True
                })

            result = {
                "execution_id": execution_id,
                "node_id": node_id,
                "port_id": port_id or outputs[0]["port_id"],
                "schema": schema
            }
            # Store in cache
            cache.set(execution_id, node_id, result, cache_key)
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=result
            )

        # 3. Extract schema from tool definition
        ports = tool_info.get("ports", {}).get("outputs", [])
        if port_id:
            ports = [p for p in ports if p.get("id") == port_id or p.get("handle") == port_id]

        if not ports:
            # Use first output if no specific port requested
            ports = tool_info.get("ports", {}).get("outputs", [])

        if not ports:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No output ports found for tool: {tool_id}"
            )

        port = ports[0]
        schema = port.get("schema", [])

        result = {
            "execution_id": execution_id,
            "node_id": node_id,
            "port_id": port_id or port.get("id", ""),
            "schema": schema
        }
        # Store in cache
        cache.set(execution_id, node_id, result, cache_key)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get node data schema: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch node data schema."
        )


@router.get("/executions/{execution_id}/nodes/{node_id}/data/rows")
async def get_node_data_rows(
    execution_id: str,
    node_id: str,
    port_id: Optional[str] = None,
    offset: int = Query(0, ge=0, description="Row offset for pagination"),
    limit: int = Query(100, ge=1, le=10000, description="Maximum rows to return"),
    row_ids: Optional[str] = Query(None, description="Comma-separated list of row IDs to filter"),
    db=Depends(get_database)
) -> JSONResponse:
    """
    Get data rows from node output with optional filtering

    Args:
        execution_id: Execution ID
        node_id: Node ID
        port_id: Optional output port ID (if multiple outputs)
        offset: Row offset for pagination
        limit: Maximum rows to return (max 10000)
        row_ids: Comma-separated list of row IDs to filter (by index)
        db: Database connection

    Returns:
        {
            "execution_id": str,
            "node_id": str,
            "port_id": str,
            "columns": [str],
            "rows": [dict],
            "total_rows": int,
            "offset": int,
            "limit": int
        }
    """
    try:
        execution_id = _validate_identifier(execution_id, "execution_id")
        node_id = _validate_identifier(node_id, "node_id")
        if port_id:
            _validate_identifier(port_id, "port_id")

        # 1. Resolve node outputs
        outputs_info = _resolve_outputs_or_http(execution_id, node_id, db)

        # 2. Select appropriate output
        if port_id:
            outputs = [o for o in outputs_info["outputs"] if o["port_id"] == port_id]
        else:
            outputs = outputs_info["outputs"]

        if not outputs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No outputs found for node: {node_id}"
            )

        output = outputs[0]

        if not output["exists"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Output file does not exist: {output['file_name']}"
            )

        if not output["parseable"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Output file is not parseable: {output['file_name']}"
            )

        # 3. Parse file
        file_path = Path(output["file_path"])

        # Handle row ID filtering
        if row_ids:
            try:
                requested_ids = [int(x.strip()) for x in row_ids.split(",") if x.strip()]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid row_ids format. Must be comma-separated integers."
                )
            if not requested_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="row_ids cannot be empty.",
                )
            if any(row_id < 0 for row_id in requested_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="row_ids must be non-negative integers.",
                )
            if len(requested_ids) > _MAX_ROW_IDS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"row_ids length exceeds maximum {_MAX_ROW_IDS}.",
                )

            max_requested_id = max(requested_ids)
            table_data = parse_tabular_file(file_path, max_rows=max_requested_id + 1)

            # Filter by row index
            filtered_rows = []
            for row_id in requested_ids:
                if 0 <= row_id < len(table_data["rows"]):
                    filtered_rows.append(table_data["rows"][row_id])

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "execution_id": execution_id,
                    "node_id": node_id,
                    "port_id": output["port_id"],
                    "columns": table_data["columns"],
                    "rows": filtered_rows,
                    "total_rows": len(filtered_rows),
                    "offset": 0,
                    "limit": len(filtered_rows)
                }
            )

        # Normal pagination
        table_data = parse_tabular_file(file_path, max_rows=offset + limit)

        # Apply offset
        paginated_rows = table_data["rows"][offset:]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "execution_id": execution_id,
                "node_id": node_id,
                "port_id": output["port_id"],
                "columns": table_data["columns"],
                "rows": paginated_rows[:limit],
                "total_rows": table_data["total_rows"],
                "offset": offset,
                "limit": limit
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get node data rows: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch node data rows."
        )


@router.get("/executions/{execution_id}/nodes/{node_id}/html/{row_id}")
async def get_html_fragment(
    execution_id: str,
    node_id: str,
    row_id: int,
    db=Depends(get_database)
) -> JSONResponse:
    """
    Get HTML fragment for specific PrSM/feature by row ID

    Args:
        execution_id: Execution ID
        node_id: Node ID
        row_id: Row ID (index of the PrSM/feature)
        db: Database connection

    Returns:
        {
            "execution_id": str,
            "node_id": str,
            "row_id": int,
            "html": str,  # HTML fragment content
            "exists": bool
        }
    """
    try:
        # Validate row_id
        if row_id < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Row ID must be non-negative"
            )

        execution_id = _validate_identifier(execution_id, "execution_id")
        node_id = _validate_identifier(node_id, "node_id")

        # Check cache first
        cache = get_node_data_cache()
        cache_key = f"html_fragment_{row_id}"
        cached_result = cache.get(execution_id, node_id, cache_key)
        if cached_result is not None:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=cached_result
            )

        # Resolve node outputs
        outputs_info = _resolve_outputs_or_http(execution_id, node_id, db)

        # Find HTML output
        html_output = None
        for output in outputs_info["outputs"]:
            if output.get("is_directory") and output.get("file_name", "").endswith("_html"):
                html_output = output
                break

        if not html_output:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Node {node_id} does not have HTML output"
            )

        if not html_output["exists"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"HTML output directory does not exist"
            )

        # Look for PrSM HTML file
        html_dir = Path(html_output["file_path"])
        prsm_dir = html_dir / "prsm"

        if not prsm_dir.exists():
            # Try direct HTML files in directory
            html_files = list(html_dir.glob("*.html"))
            if row_id < len(html_files):
                html_content = html_files[row_id].read_text(encoding="utf-8", errors="ignore")
                result = {
                    "execution_id": execution_id,
                    "node_id": node_id,
                    "row_id": row_id,
                    "html": html_content,
                    "exists": True
                }
                cache.set(execution_id, node_id, result, cache_key)
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content=result
                )
            else:
                result = {
                    "execution_id": execution_id,
                    "node_id": node_id,
                    "row_id": row_id,
                    "html": f"HTML fragment for row {row_id} not found",
                    "exists": False
                }
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content=result
                )

        # Look for PrSM-specific HTML file
        prsm_file = prsm_dir / f"prsm_{row_id}.html"
        if prsm_file.exists():
            html_content = prsm_file.read_text(encoding="utf-8", errors="ignore")
            result = {
                "execution_id": execution_id,
                "node_id": node_id,
                "row_id": row_id,
                "html": html_content,
                "exists": True
            }
            cache.set(execution_id, node_id, result, cache_key)
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=result
            )
        else:
            result = {
                "execution_id": execution_id,
                "node_id": node_id,
                "row_id": row_id,
                "html": f"HTML fragment for row {row_id} not found",
                "exists": False
            }
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=result
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get HTML fragment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch HTML fragment."
        )
