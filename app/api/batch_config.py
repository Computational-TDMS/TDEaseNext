"""
Batch Configuration API
Handles batch processing configurations stored separately from workflows, linked to user_id
"""

import json
import uuid
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse

from app.models.schemas import BatchConfig, BatchSample
from app.models.common import SuccessResponse
from app.dependencies import get_database

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/batch-configs", tags=["batch-configs"])


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_batch_config(
    user_id: str,
    name: str,
    batch_config: BatchConfig,
    description: Optional[str] = None,
    db=Depends(get_database)
) -> dict:
    """Create a new batch configuration for a user"""
    try:
        cursor = db.cursor()
        
        # Generate config ID
        config_id = f"batch_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Save batch config as JSON
        batch_config_json = json.dumps(batch_config.model_dump(), ensure_ascii=False)
        now = datetime.utcnow().isoformat()
        
        cursor.execute("""
            INSERT INTO batch_configs (id, user_id, name, description, config_data, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (config_id, user_id, name, description, batch_config_json, now, now))
        db.commit()
        
        logger.info(f"Batch config {config_id} created for user {user_id}")
        return {
            "id": config_id,
            "user_id": user_id,
            "name": name,
            "description": description,
            "created_at": now,
            "updated_at": now
        }
        
    except Exception as e:
        logger.error(f"Failed to create batch config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create batch configuration: {str(e)}"
        )


@router.get("/", response_model=List[dict])
async def list_batch_configs(
    user_id: str,
    db=Depends(get_database)
) -> List[dict]:
    """List all batch configurations for a user"""
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT id, user_id, name, description, created_at, updated_at, is_shared
            FROM batch_configs
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,))
        
        rows = cursor.fetchall()
        return [
            {
                "id": row[0],
                "user_id": row[1],
                "name": row[2],
                "description": row[3],
                "created_at": row[4],
                "updated_at": row[5],
                "is_shared": bool(row[6]) if row[6] is not None else False
            }
            for row in rows
        ]
        
    except Exception as e:
        logger.error(f"Failed to list batch configs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list batch configurations: {str(e)}"
        )


@router.get("/{config_id}", response_model=dict)
async def get_batch_config(
    config_id: str,
    user_id: Optional[str] = None,
    db=Depends(get_database)
) -> dict:
    """Get a specific batch configuration"""
    try:
        cursor = db.cursor()
        
        if user_id:
            cursor.execute("""
                SELECT id, user_id, name, description, config_data, created_at, updated_at, is_shared
                FROM batch_configs
                WHERE id = ? AND user_id = ?
            """, (config_id, user_id))
        else:
            cursor.execute("""
                SELECT id, user_id, name, description, config_data, created_at, updated_at, is_shared
                FROM batch_configs
                WHERE id = ?
            """, (config_id,))
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch configuration '{config_id}' not found"
            )
        
        batch_config_dict = json.loads(row[4])
        return {
            "id": row[0],
            "user_id": row[1],
            "name": row[2],
            "description": row[3],
            "config": BatchConfig(**batch_config_dict).model_dump(),
            "created_at": row[5],
            "updated_at": row[6],
            "is_shared": bool(row[7]) if row[7] is not None else False
        }
        
    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid batch config JSON for config {config_id}: {e}")
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


@router.put("/{config_id}", response_model=dict)
async def update_batch_config(
    config_id: str,
    user_id: str,
    batch_config: BatchConfig,
    name: Optional[str] = None,
    description: Optional[str] = None,
    db=Depends(get_database)
) -> dict:
    """Update a batch configuration"""
    try:
        cursor = db.cursor()
        
        # Check if config exists and belongs to user
        cursor.execute("SELECT id, name, description FROM batch_configs WHERE id = ? AND user_id = ?", (config_id, user_id))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch configuration '{config_id}' not found or access denied"
            )
        
        # Update batch config
        batch_config_json = json.dumps(batch_config.model_dump(), ensure_ascii=False)
        update_name = name or row[1]
        update_description = description if description is not None else row[2]
        now = datetime.utcnow().isoformat()
        
        cursor.execute("""
            UPDATE batch_configs
            SET config_data = ?, name = ?, description = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
        """, (batch_config_json, update_name, update_description, now, config_id, user_id))
        db.commit()
        
        logger.info(f"Batch config {config_id} updated for user {user_id}")
        return {
            "id": config_id,
            "user_id": user_id,
            "name": update_name,
            "description": update_description,
            "updated_at": now
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update batch config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update batch configuration: {str(e)}"
        )


@router.delete("/{config_id}", response_model=SuccessResponse)
async def delete_batch_config(
    config_id: str,
    user_id: str,
    db=Depends(get_database)
) -> SuccessResponse:
    """Delete a batch configuration"""
    try:
        cursor = db.cursor()
        
        # Check if config exists and belongs to user
        cursor.execute("SELECT id FROM batch_configs WHERE id = ? AND user_id = ?", (config_id, user_id))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch configuration '{config_id}' not found or access denied"
            )
        
        cursor.execute("DELETE FROM batch_configs WHERE id = ? AND user_id = ?", (config_id, user_id))
        db.commit()
        
        logger.info(f"Batch config {config_id} deleted for user {user_id}")
        return SuccessResponse(message="Batch configuration deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete batch config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete batch configuration: {str(e)}"
        )


