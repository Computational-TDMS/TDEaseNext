import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, status
from app.services.tool_registry import get_tool_registry as get_app_tool_registry
from app.core.executor.command_pipeline import CommandPipeline, build_command_with_trace

logger = logging.getLogger(__name__)
router = APIRouter()


# Request/Response Models
class CommandPreviewRequest(BaseModel):
    """Request model for command preview"""
    tool_id: str = Field(..., description="Tool identifier")
    param_values: Dict[str, Any] = Field(default_factory=dict, description="Parameter values from UI")
    input_files: Dict[str, str] = Field(default_factory=dict, description="Input file paths (port_id -> path)")
    output_target: Optional[str] = Field(None, description="Output file path")


class CommandPreviewResponse(BaseModel):
    """Response model for command preview"""
    tool_id: str
    command: str = Field(..., description="Full command string (for display)")
    command_parts: list[str] = Field(..., description="Command parts as list")
    trace: Dict[str, Any] = Field(..., description="Detailed assembly trace")

@router.get("/schemas", response_model=Dict[str, Any])
async def get_tool_schemas() -> Dict[str, Any]:
    """Get tool schemas for frontend rendering"""
    try:
        reg = get_app_tool_registry()
        return {"registry": reg.list_tools()}
    except Exception as e:
        logger.error(f"Failed to get tool schemas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tool schemas: {e}"
        )


@router.post("/preview", response_model=CommandPreviewResponse)
async def preview_command(request: CommandPreviewRequest) -> CommandPreviewResponse:
    """
    Preview command assembly for a tool without executing it.

    This endpoint uses the same CommandPipeline logic as actual execution,
    ensuring the preview matches what will actually run.

    In preview mode, placeholders like <input_port> and <output_dir> are used
    instead of actual file paths, since the actual paths depend on workflow execution.

    Query parameters:
    - tool_id: Tool identifier
    - param_values: Parameter values from UI (includes empty values that will be filtered)
    - input_files: Input file paths mapping (port_id -> path) - leave empty for preview with placeholders
    - output_target: Optional output file path - leave null for preview with placeholders
    """
    try:
        reg = get_app_tool_registry()
        tools = reg.list_tools()

        if request.tool_id not in tools:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool '{request.tool_id}' not found"
            )

        tool_def = tools[request.tool_id]

        # Use preview mode to get placeholders instead of requiring actual paths
        pipeline = CommandPipeline(tool_def, preview_mode=True)
        cmd_parts, trace = pipeline.build_with_trace(
            param_values=request.param_values,
            input_files=request.input_files,
            output_target=request.output_target
        )

        # Return command string and detailed trace
        return CommandPreviewResponse(
            tool_id=request.tool_id,
            command=" ".join(cmd_parts),
            command_parts=cmd_parts,
            trace=trace.to_dict()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to preview command for tool {request.tool_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview command: {str(e)}"
        )
