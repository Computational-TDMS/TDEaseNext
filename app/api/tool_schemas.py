import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from app.services.tool_registry import get_tool_registry as get_app_tool_registry

logger = logging.getLogger(__name__)
router = APIRouter()

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
