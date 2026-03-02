"""
Tools API Endpoints
Handles tool discovery, registration, and management
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from fastapi.responses import JSONResponse

from app.models.tools import (
    ToolInfo, ToolRegistration, ToolValidationResult, ToolListResponse,
    ToolDiscoveryRequest
)
from app.models.common import SuccessResponse, APIError
from app.dependencies import get_database, get_config, get_permission_manager, get_tool_registry
from app.core.platform_manager import get_platform_manager
from app.core.permission_manager import PermissionManager
from app.services.tool_registry import ToolRegistry as AppToolRegistry

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/schemas", response_model=Dict[str, Any])
async def get_tool_schemas() -> Dict[str, Any]:
    """Return tool registry schemas for frontend rendering"""
    try:
        reg = get_tool_registry()
        return {"registry": reg.list_tools()}
    except Exception as e:
        logger.error(f"Failed to get tool schemas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tool schemas: {str(e)}"
        )


@router.get("/discovery", response_model=Dict[str, List[ToolInfo]])
async def discover_tools(
    platform_manager=Depends(get_platform_manager)
) -> Dict[str, List[ToolInfo]]:
    """Discover available tools on the system"""
    try:
        logger.info("Starting tool discovery...")

        # Get all available tools
        discovered_tools = await platform_manager.get_available_tools()

        # Organize tools by category
        tools_by_category = {}
        for tool_name, tool_info in discovered_tools.items():
            category = tool_info.get("category", "other")

            if category not in tools_by_category:
                tools_by_category[category] = []

            # Convert to ToolInfo model
            tool_info_model = ToolInfo(
                name=tool_name,
                version=tool_info.get("version", "unknown"),
                description=tool_info.get("description", ""),
                category=category,
                executable_path=tool_info.get("path", ""),
                is_available=tool_info.get("available", False),
                platform_info=tool_info.get("platform_info", {}),
                metadata=tool_info.get("metadata", {})
            )

            tools_by_category[category].append(tool_info_model)

        logger.info(f"Discovered {sum(len(tools) for tools in tools_by_category.values())} tools")

        return tools_by_category

    except Exception as e:
        logger.error(f"Tool discovery failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tool discovery failed: {str(e)}"
        )


@router.get("/registered", response_model=ToolListResponse)
async def get_registered_tools(
    category: Optional[str] = None,
    available_only: bool = False,
    db=Depends(get_database)
) -> ToolListResponse:
    """Get registered tools with optional filtering"""
    try:
        cursor = db.cursor()

        # Build query based on filters
        query = "SELECT * FROM tools"
        params = []

        if category:
            query += " WHERE category = ?"
            params.append(category)

        if available_only:
            if category:
                query += " AND is_available = 1"
            else:
                query += " WHERE is_available = 1"

        query += " ORDER BY category, name"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Convert to ToolInfo models
        tools = []
        for row in rows:
            tool_info = ToolInfo(
                name=row[1],
                version=row[2],
                description=row[3],
                category=row[4],
                executable_path=row[5],
                is_available=bool(row[6]),
                platform_info=json.loads(row[7]) if row[7] else {},
                metadata=json.loads(row[8]) if row[8] else {}
            )
            tools.append(tool_info)

        return ToolListResponse(
            tools=tools,
            total=len(tools),
            category=category,
            available_only=available_only
        )

    except Exception as e:
        logger.error(f"Failed to get registered tools: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get registered tools: {str(e)}"
        )


@router.get("/{tool_name}", response_model=ToolInfo)
async def get_tool(
    tool_name: str,
    db=Depends(get_database)
) -> ToolInfo:
    """Get specific tool information"""
    try:
        cursor = db.cursor()

        cursor.execute("""
            SELECT name, version, description, category, executable_path,
                   is_available, platform_info, metadata
            FROM tools WHERE name = ?
        """, (tool_name,))

        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool {tool_name} not found"
            )

        return ToolInfo(
            name=row[0],
            version=row[1],
            description=row[2],
            category=row[3],
            executable_path=row[4],
            is_available=bool(row[5]),
            platform_info=json.loads(row[6]) if row[6] else {},
            metadata=json.loads(row[7]) if row[7] else {}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tool {tool_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tool: {str(e)}"
        )


@router.post("/register", response_model=ToolValidationResult, status_code=status.HTTP_201_CREATED)
async def register_tool(
    tool_registration: ToolRegistration,
    background_tasks: BackgroundTasks,
    db=Depends(get_database),
    platform_manager=Depends(get_platform_manager)
) -> ToolValidationResult:
    """Register a new tool"""
    try:
        tool_name = tool_registration.name

        # Check if tool already exists
        cursor = db.cursor()
        cursor.execute("SELECT name FROM tools WHERE name = ?", (tool_name,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tool {tool_name} already registered"
            )

        # Validate tool executable
        validation_result = await validate_tool_executable(
            tool_registration, platform_manager
        )

        if not validation_result["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tool validation failed: {', '.join(validation_result['errors'])}"
            )

        # Save tool to database
        tool_data = {
            "name": tool_name,
            "version": tool_registration.version,
            "description": tool_registration.description,
            "category": tool_registration.category,
            "executable_path": tool_registration.executable_path,
            "is_available": validation_result["is_available"],
            "platform_info": validation_result.get("platform_info", {}),
            "metadata": tool_registration.metadata or {},
            "created_at": datetime.now().isoformat()
        }

        await save_tool_to_database(db, tool_data)

        logger.info(f"Registered tool {tool_name}")

        return ToolValidationResult(
            valid=True,
            errors=[],
            warnings=validation_result.get("warnings", []),
            is_available=validation_result["is_available"],
            detected_version=validation_result.get("detected_version"),
            platform_info=validation_result.get("platform_info", {})
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to register tool {tool_registration.name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tool registration failed: {str(e)}"
        )


@router.put("/{tool_name}", response_model=ToolInfo)
async def update_tool(
    tool_name: str,
    tool_update: ToolUpdateRequest,
    db=Depends(get_database),
    platform_manager=Depends(get_platform_manager)
) -> ToolInfo:
    """Update existing tool registration"""
    try:
        # Check if tool exists
        cursor = db.cursor()
        cursor.execute("SELECT * FROM tools WHERE name = ?", (tool_name,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool {tool_name} not found"
            )

        # Build update data
        update_data = tool_update.model_dump(exclude_unset=True)

        # If executable path is updated, revalidate
        if "executable_path" in update_data:
            temp_registration = ToolRegistration(
                name=tool_name,
                executable_path=update_data["executable_path"],
                version=update_data.get("version", row[2]),
                description=update_data.get("description", row[3]),
                category=update_data.get("category", row[4]),
                metadata=update_data.get("metadata", json.loads(row[8]) if row[8] else {})
            )

            validation_result = await validate_tool_executable(
                temp_registration, platform_manager
            )

            if not validation_result["valid"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Updated tool validation failed: {', '.join(validation_result['errors'])}"
                )

            update_data["is_available"] = validation_result["is_available"]
            update_data["platform_info"] = validation_result.get("platform_info", {})

        # Update database
        set_clauses = []
        params = []

        for key, value in update_data.items():
            if key in ["version", "description", "category", "executable_path", "is_available", "platform_info", "metadata"]:
                set_clauses.append(f"{key} = ?")
                if isinstance(value, dict):
                    params.append(json.dumps(value))
                else:
                    params.append(value)

        if set_clauses:
            set_clauses.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(tool_name)

            query = f"UPDATE tools SET {', '.join(set_clauses)} WHERE name = ?"
            cursor.execute(query, params)
            db.commit()

        logger.info(f"Updated tool {tool_name}")

        # Return updated tool info
        return await get_tool(tool_name, db)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update tool {tool_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tool update failed: {str(e)}"
        )


@router.delete("/{tool_name}", response_model=SuccessResponse)
async def unregister_tool(
    tool_name: str,
    db=Depends(get_database)
) -> SuccessResponse:
    """Unregister a tool"""
    try:
        # Check if tool exists
        cursor = db.cursor()
        cursor.execute("SELECT name FROM tools WHERE name = ?", (tool_name,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool {tool_name} not found"
            )

        # Delete from database
        cursor.execute("DELETE FROM tools WHERE name = ?", (tool_name,))
        db.commit()

        logger.info(f"Unregistered tool {tool_name}")

        return SuccessResponse(
            success=True,
            message=f"Tool {tool_name} unregistered successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unregister tool {tool_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tool unregistration failed: {str(e)}"
        )


@router.post("/search", response_model=ToolListResponse)
async def search_tools(
    search_request: ToolSearchRequest,
    db=Depends(get_database)
) -> ToolListResponse:
    """Search tools by various criteria"""
    try:
        cursor = db.cursor()

        # Build search query
        query = "SELECT * FROM tools WHERE 1=1"
        params = []

        if search_request.query:
            query += " AND (name LIKE ? OR description LIKE ?)"
            params.extend([f"%{search_request.query}%", f"%{search_request.query}%"])

        if search_request.category:
            query += " AND category = ?"
            params.append(search_request.category)

        if search_request.available_only is not None:
            query += " AND is_available = ?"
            params.append(1 if search_request.available_only else 0)

        if search_request.min_version:
            query += " AND version >= ?"
            params.append(search_request.min_version)

        query += " ORDER BY "
        if search_request.sort_by == "name":
            query += "name"
        elif search_request.sort_by == "version":
            query += "version"
        elif search_request.sort_by == "created_at":
            query += "created_at"
        else:
            query += "category, name"

        if search_request.sort_order == "desc":
            query += " DESC"

        # Add limit and offset
        query += " LIMIT ? OFFSET ?"
        params.extend([search_request.limit, search_request.offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Get total count for pagination
        count_query = "SELECT COUNT(*) FROM tools WHERE " + query.split("ORDER BY")[0].split("LIMIT")[0]
        count_params = params[:-2]  # Remove limit and offset
        cursor.execute(count_query, count_params)
        total_count = cursor.fetchone()[0]

        # Convert to ToolInfo models
        tools = []
        for row in rows:
            tool_info = ToolInfo(
                name=row[1],
                version=row[2],
                description=row[3],
                category=row[4],
                executable_path=row[5],
                is_available=bool(row[6]),
                platform_info=json.loads(row[7]) if row[7] else {},
                metadata=json.loads(row[8]) if row[8] else {}
            )
            tools.append(tool_info)

        return ToolListResponse(
            tools=tools,
            total=total_count,
            query=search_request.query,
            category=search_request.category,
            available_only=search_request.available_only
        )

    except Exception as e:
        logger.error(f"Tool search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tool search failed: {str(e)}"
        )


@router.post("/refresh", response_model=SuccessResponse)
async def refresh_tools(
    background_tasks: BackgroundTasks,
    db=Depends(get_database),
    platform_manager=Depends(get_platform_manager)
) -> SuccessResponse:
    """Refresh tool discovery and registration"""
    try:
        # Add background task to refresh tools
        background_tasks.add_task(refresh_tools_background, db, platform_manager)

        return SuccessResponse(
            success=True,
            message="Tool refresh started in background"
        )

    except Exception as e:
        logger.error(f"Failed to start tool refresh: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start tool refresh: {str(e)}"
        )


@router.get("/categories", response_model=List[str])
async def get_tool_categories(
    db=Depends(get_database)
) -> List[str]:
    """Get all available tool categories"""
    try:
        cursor = db.cursor()

        cursor.execute("SELECT DISTINCT category FROM tools WHERE category IS NOT NULL ORDER BY category")
        rows = cursor.fetchall()

        return [row[0] for row in rows if row[0]]

    except Exception as e:
        logger.error(f"Failed to get tool categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tool categories: {str(e)}"
        )


@router.get("/stats", response_model=Dict[str, Any])
async def get_tool_stats(
    db=Depends(get_database)
) -> Dict[str, Any]:
    """Get tool statistics"""
    try:
        cursor = db.cursor()

        # Total tools
        cursor.execute("SELECT COUNT(*) FROM tools")
        total_tools = cursor.fetchone()[0]

        # Available tools
        cursor.execute("SELECT COUNT(*) FROM tools WHERE is_available = 1")
        available_tools = cursor.fetchone()[0]

        # Tools by category
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM tools
            WHERE category IS NOT NULL
            GROUP BY category
            ORDER BY count DESC
        """)
        category_counts = {row[0]: row[1] for row in cursor.fetchall()}

        # Recently added tools (last 7 days)
        cursor.execute("""
            SELECT COUNT(*) FROM tools
            WHERE created_at >= datetime('now', '-7 days')
        """)
        recent_tools = cursor.fetchone()[0]

        return {
            "total_tools": total_tools,
            "available_tools": available_tools,
            "unavailable_tools": total_tools - available_tools,
            "availability_percentage": (available_tools / total_tools * 100) if total_tools > 0 else 0,
            "category_counts": category_counts,
            "recent_tools": recent_tools,
            "categories_count": len(category_counts)
        }

    except Exception as e:
        logger.error(f"Failed to get tool stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tool stats: {str(e)}"
        )


# Helper functions
async def validate_tool_executable(
    tool_registration: ToolRegistration,
    platform_manager
) -> Dict[str, Any]:
    """Validate tool executable and get version info"""
    try:
        executable_path = tool_registration.executable_path

        # Check if executable exists and is accessible
        if not platform_manager.validate_executable(executable_path):
            return {
                "valid": False,
                "is_available": False,
                "errors": [f"Executable not found or not accessible: {executable_path}"],
                "warnings": []
            }

        # Get version information
        version_info = await platform_manager.get_tool_version(executable_path)

        # Get platform information
        platform_info = platform_manager.get_platform_info()

        return {
            "valid": True,
            "is_available": True,
            "detected_version": version_info,
            "platform_info": platform_info,
            "errors": [],
            "warnings": []
        }

    except Exception as e:
        return {
            "valid": False,
            "is_available": False,
            "errors": [f"Validation error: {str(e)}"],
            "warnings": []
        }


async def save_tool_to_database(db, tool_data: Dict[str, Any]):
    """Save tool data to database"""
    try:
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO tools (
                name, version, description, category, executable_path,
                is_available, platform_info, metadata, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tool_data["name"],
            tool_data["version"],
            tool_data["description"],
            tool_data["category"],
            tool_data["executable_path"],
            tool_data["is_available"],
            json.dumps(tool_data.get("platform_info", {})),
            json.dumps(tool_data.get("metadata", {})),
            tool_data["created_at"],
            tool_data.get("updated_at", tool_data["created_at"])
        ))

        db.commit()

    except Exception as e:
        logger.error(f"Failed to save tool to database: {e}")
        raise


async def refresh_tools_background(db, platform_manager):
    """Background task to refresh tool discovery"""
    try:
        logger.info("Starting background tool refresh...")

        # Discover tools
        discovered_tools = await platform_manager.get_available_tools()

        updated_count = 0
        added_count = 0

        for tool_name, tool_info in discovered_tools.items():
            cursor = db.cursor()

            # Check if tool already exists
            cursor.execute("SELECT * FROM tools WHERE name = ?", (tool_name,))
            existing_tool = cursor.fetchone()

            tool_data = {
                "name": tool_name,
                "version": tool_info.get("version", "unknown"),
                "description": tool_info.get("description", ""),
                "category": tool_info.get("category", "other"),
                "executable_path": tool_info.get("path", ""),
                "is_available": tool_info.get("available", False),
                "platform_info": tool_info.get("platform_info", {}),
                "metadata": tool_info.get("metadata", {}),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            if existing_tool:
                # Update existing tool
                cursor.execute("""
                    UPDATE tools SET version = ?, description = ?, category = ?,
                                   executable_path = ?, is_available = ?,
                                   platform_info = ?, metadata = ?, updated_at = ?
                    WHERE name = ?
                """, (
                    tool_data["version"],
                    tool_data["description"],
                    tool_data["category"],
                    tool_data["executable_path"],
                    tool_data["is_available"],
                    json.dumps(tool_data["platform_info"]),
                    json.dumps(tool_data["metadata"]),
                    tool_data["updated_at"],
                    tool_name
                ))
                updated_count += 1
            else:
                # Add new tool
                await save_tool_to_database(db, tool_data)
                added_count += 1

        logger.info(f"Tool refresh completed: {added_count} added, {updated_count} updated")

    except Exception as e:
        logger.error(f"Background tool refresh failed: {e}")
