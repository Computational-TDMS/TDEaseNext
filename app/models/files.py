from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class FileInfo(BaseModel):
    """Unified file information model - imports from app.models.common.FileInfo"""

    # Import the canonical FileInfo from common module
    # This class is kept for backward compatibility but will be deprecated
    pass


class DirectoryFileInfo(BaseModel):
    """Extended file info for directory listing operations"""
    name: str
    path: str
    absolute_path: str
    is_directory: bool
    size: int
    modified_time: datetime
    mime_type: str
    permissions: Dict[str, Any]

class FileUploadResponse(BaseModel):
    filename: str
    file_path: str
    workspace_path: str
    subdirectory: str
    size: int
    mime_type: str
    upload_time: datetime
    message: str

class FileDownloadRequest(BaseModel):
    file_path: str
    workspace_path: str


class DirectoryListing(BaseModel):
    workspace_path: str
    subdirectory: str
    files: List[DirectoryFileInfo]
    directories: List[DirectoryFileInfo]
    total_files: int
    total_directories: int
    recursive: bool


class WorkspaceInfo(BaseModel):
    workspace_path: str
    exists: bool
    readable: bool
    writable: bool
    total_size: int
    file_count: int
    directory_count: int
    uploaded_files: int
    subdirectories: List[Dict[str, Any]]
    permissions: Dict[str, Any]
    created_at: Optional[datetime] = None
    last_modified: Optional[datetime] = None

class FileOperation(BaseModel):
    workspace_path: str
    source_path: str
    target_path: Optional[str] = None
    action: str = Field(..., pattern="^(copy|move|delete)$")
