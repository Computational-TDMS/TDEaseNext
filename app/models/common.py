"""
Common data models and utilities
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


class APIError(BaseModel):
    """Standard API error response model"""

    error: str = Field(..., description="Error type identifier")
    detail: str = Field(..., description="Detailed error message")
    request_id: Optional[str] = Field(None, description="Unique request identifier")
    timestamp: Optional[datetime] = Field(None, description="Error timestamp")

class SuccessResponse(BaseModel):
    """Standard API success response model"""

    success: bool = Field(True, description="Success indicator")
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Optional response data")
    timestamp: Optional[datetime] = Field(None, description="Response timestamp")

class FileInfo(BaseModel):
    """File information model"""

    filename: str = Field(..., description="File name")
    path: str = Field(..., description="File path")
    size: int = Field(..., description="File size in bytes")
    content_type: Optional[str] = Field(None, description="MIME content type")
    created_at: Optional[datetime] = Field(None, description="File creation time")
    modified_at: Optional[datetime] = Field(None, description="File modification time")
    is_readable: Optional[bool] = Field(None, description="File read permission")
    is_writable: Optional[bool] = Field(None, description="File write permission")

class PaginationInfo(BaseModel):
    """Pagination information model"""

    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=1000, description="Items per page")
    total_items: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether next page exists")
    has_prev: bool = Field(..., description="Whether previous page exists")


class PaginatedResponse(BaseModel):
    """Generic paginated response model"""

    items: list = Field(..., description="List of items")
    pagination: PaginationInfo = Field(..., description="Pagination information")


def generate_request_id() -> str:
    """Generate unique request identifier"""
    return str(uuid.uuid4())
