"""
Files API Endpoints
Handles file operations, uploads, downloads, and workspace management
"""

import os
import json
import shutil
import logging
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from io import BytesIO

from app.models.files import (
    FileInfo, FileUploadResponse, FileDownloadRequest,
    DirectoryListing, WorkspaceInfo, FileOperation
)
from app.models.common import SuccessResponse, APIError
from app.dependencies import get_database, get_config, get_permission_manager
from app.core.permission_manager import PermissionManager
from app.core.config import (
    MAX_FILE_SIZE, MAX_FILE_PREVIEW_SIZE, MAX_FILE_PREVIEW_LINES
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Supported file types for upload
SUPPORTED_UPLOAD_TYPES = [
    '.txt', '.csv', '.tsv', '.json', '.yaml', '.yml',
    '.xml', '.fasta', '.fa', '.fastq', '.fq',
    '.mzml', '.mzxml', '.raw', '.wiff', '.d',
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx'
]


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    workspace_path: str = "default_workspace",
    subdirectory: str = "input_files",
    overwrite: bool = False,
    perm_manager: PermissionManager = Depends(get_permission_manager),
    db=Depends(get_database)
) -> FileUploadResponse:
    """Upload file to workspace"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No filename provided"
            )

        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in SUPPORTED_UPLOAD_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file_ext}. Supported types: {', '.join(SUPPORTED_UPLOAD_TYPES)}"
            )

        # Check file size
        if hasattr(file, 'size') and file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
            )

        # Validate workspace permissions
        workspace_perms = await perm_manager.check_workspace_permissions(workspace_path)
        if not workspace_perms["exists"] and not workspace_perms.get("parent_writable", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid workspace: {workspace_path}"
            )

        # Ensure workspace structure exists
        await perm_manager.ensure_workspace_structure(workspace_path)

        # Create safe filename
        safe_filename = perm_manager.get_safe_filename(file.filename)
        target_dir = Path(workspace_path) / subdirectory
        target_dir.mkdir(parents=True, exist_ok=True)

        # Create upload file path
        file_path = perm_manager.create_upload_file_path(workspace_path, safe_filename)

        # Check if file exists
        if file_path.exists() and not overwrite:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"File already exists: {file.filename}. Use overwrite=true to replace."
            )

        # Save file
        try:
            content = await file.read()
            with open(file_path, 'wb') as f:
                f.write(content)

            # Set file permissions
            await perm_manager.set_file_permissions(
                str(file_path),
                readable=True,
                writable=True,
                executable=False
            )

        except Exception as e:
            # Clean up on error
            if file_path.exists():
                file_path.unlink()
            raise e

        # Get file info
        file_info = await perm_manager.get_file_permissions_info(str(file_path))

        # Record file in database
        file_record = {
            "filename": file.filename,
            "safe_filename": safe_filename,
            "file_path": str(file_path),
            "workspace_path": workspace_path,
            "subdirectory": subdirectory,
            "size": len(content),
            "mime_type": mimetypes.guess_type(file.filename)[0] or "application/octet-stream",
            "uploaded_at": datetime.now().isoformat()
        }

        await save_file_record_to_database(db, file_record)

        logger.info(f"Uploaded file: {file.filename} to {file_path}")

        return FileUploadResponse(
            filename=file.filename,
            file_path=str(file_path),
            workspace_path=workspace_path,
            subdirectory=subdirectory,
            size=len(content),
            mime_type=file_record["mime_type"],
            upload_time=datetime.now(),
            message="File uploaded successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
        )


@router.post("/download", response_model=FileResponse)
async def download_file(
    request: FileDownloadRequest,
    perm_manager: PermissionManager = Depends(get_permission_manager)
) -> FileResponse:
    """Download file from workspace"""
    try:
        # Validate file path is within workspace
        if not perm_manager.validate_file_access(request.file_path, request.workspace_path):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="File access denied: path outside workspace"
            )

        # Check if file exists
        file_path = Path(request.file_path)
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {request.file_path}"
            )

        if not file_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Path is not a file: {request.file_path}"
            )

        # Check file permissions
        file_info = await perm_manager.get_file_permissions_info(str(file_path))
        if not file_info.get("readable", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"File not readable: {request.file_path}"
            )

        # Determine media type
        media_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"

        return FileResponse(
            path=str(file_path),
            filename=file_path.name,
            media_type=media_type
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File download failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File download failed: {str(e)}"
        )


@router.get("/list/{workspace_path:path}", response_model=DirectoryListing)
async def list_directory(
    workspace_path: str,
    subdirectory: str = "",
    recursive: bool = False,
    show_hidden: bool = False,
    perm_manager: PermissionManager = Depends(get_permission_manager)
) -> DirectoryListing:
    """List files and directories in workspace"""
    try:
        # Validate workspace permissions
        workspace_perms = await perm_manager.check_workspace_permissions(workspace_path)
        if not workspace_perms["exists"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace not found: {workspace_path}"
            )

        if not workspace_perms["readable"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Workspace not readable: {workspace_path}"
            )

        # Build target directory path
        target_dir = Path(workspace_path)
        if subdirectory:
            target_dir = target_dir / subdirectory

        # Validate path is within workspace
        if not perm_manager.validate_file_access(str(target_dir), workspace_path):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Directory access denied: path outside workspace"
            )

        if not target_dir.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Directory not found: {target_dir}"
            )

        if not target_dir.is_dir():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Path is not a directory: {target_dir}"
            )

        # List directory contents
        files = []
        directories = []

        if recursive:
            # Recursive listing
            for root, dirs, filenames in os.walk(target_dir):
                # Filter hidden directories if requested
                if not show_hidden:
                    dirs[:] = [d for d in dirs if not d.startswith('.')]

                root_path = Path(root)
                relative_root = root_path.relative_to(Path(workspace_path))

                # Add directories
                for dirname in dirs:
                    dir_path = root_path / dirname
                    dir_info = await perm_manager.get_file_permissions_info(str(dir_path))
                    dir_relative_path = relative_root / dirname

                    directories.append(FileInfo(
                        name=dirname,
                        path=str(dir_relative_path),
                        absolute_path=str(dir_path),
                        is_directory=True,
                        size=0,
                        modified_time=datetime.fromtimestamp(dir_info.get("modified", 0)),
                        mime_type="application/x-directory",
                        permissions=dir_info
                    ))

                # Add files
                for filename in filenames:
                    if not show_hidden and filename.startswith('.'):
                        continue

                    file_path = root_path / filename
                    file_info = await perm_manager.get_file_permissions_info(str(file_path))
                    file_relative_path = relative_root / filename

                    files.append(FileInfo(
                        name=filename,
                        path=str(file_relative_path),
                        absolute_path=str(file_path),
                        is_directory=False,
                        size=file_info.get("size", 0),
                        modified_time=datetime.fromtimestamp(file_info.get("modified", 0)),
                        mime_type=mimetypes.guess_type(str(file_path))[0] or "application/octet-stream",
                        permissions=file_info
                    ))
        else:
            # Non-recursive listing
            for item in target_dir.iterdir():
                if not show_hidden and item.name.startswith('.'):
                    continue

                item_info = await perm_manager.get_file_permissions_info(str(item))
                relative_path = item.relative_to(Path(workspace_path))

                if item.is_dir():
                    directories.append(FileInfo(
                        name=item.name,
                        path=str(relative_path),
                        absolute_path=str(item),
                        is_directory=True,
                        size=0,
                        modified_time=datetime.fromtimestamp(item_info.get("modified", 0)),
                        mime_type="application/x-directory",
                        permissions=item_info
                    ))
                else:
                    files.append(FileInfo(
                        name=item.name,
                        path=str(relative_path),
                        absolute_path=str(item),
                        is_directory=False,
                        size=item_info.get("size", 0),
                        modified_time=datetime.fromtimestamp(item_info.get("modified", 0)),
                        mime_type=mimetypes.guess_type(str(item))[0] or "application/octet-stream",
                        permissions=item_info
                    ))

        return DirectoryListing(
            workspace_path=workspace_path,
            subdirectory=subdirectory,
            files=sorted(files, key=lambda x: (x.is_directory, x.name.lower())),
            directories=sorted(directories, key=lambda x: x.name.lower()),
            total_files=len(files),
            total_directories=len(directories),
            recursive=recursive
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Directory listing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Directory listing failed: {str(e)}"
        )


@router.get("/workspace/{workspace_path:path}", response_model=WorkspaceInfo)
async def get_workspace_info(
    workspace_path: str,
    perm_manager: PermissionManager = Depends(get_permission_manager),
    db=Depends(get_database)
) -> WorkspaceInfo:
    """Get workspace information and statistics"""
    try:
        # Validate workspace permissions
        workspace_perms = await perm_manager.check_workspace_permissions(workspace_path)

        # Get workspace statistics
        workspace_dir = Path(workspace_path)
        total_size = 0
        file_count = 0
        directory_count = 0

        if workspace_dir.exists():
            for root, dirs, files in os.walk(workspace_dir):
                directory_count += len(dirs)
                file_count += len(files)

                for file in files:
                    file_path = Path(root) / file
                    try:
                        total_size += file_path.stat().st_size
                    except (OSError, IOError):
                        pass

        # Get file records from database
        file_records = await get_file_records_from_database(db, workspace_path)

        # Get subdirectories
        subdirectories = []
        if workspace_dir.exists() and workspace_dir.is_dir():
            for item in workspace_dir.iterdir():
                if item.is_dir():
                    sub_info = await perm_manager.get_file_permissions_info(str(item))
                    subdirectories.append({
                        "name": item.name,
                        "path": str(item),
                        "created": datetime.fromtimestamp(sub_info.get("created", 0)),
                        "size": sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
                    })

        return WorkspaceInfo(
            workspace_path=workspace_path,
            exists=workspace_perms["exists"],
            readable=workspace_perms.get("readable", False),
            writable=workspace_perms.get("writable", False),
            total_size=total_size,
            file_count=file_count,
            directory_count=directory_count,
            uploaded_files=len(file_records),
            subdirectories=subdirectories,
            permissions=workspace_perms,
            created_at=datetime.fromtimestamp(workspace_perms.get("created", 0)) if workspace_perms.get("created") else None,
            last_modified=datetime.fromtimestamp(workspace_perms.get("modified", 0)) if workspace_perms.get("modified") else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get workspace info failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Get workspace info failed: {str(e)}"
        )


@router.post("/operation", response_model=SuccessResponse)
async def file_operation(
    operation: FileOperation,
    background_tasks: BackgroundTasks,
    perm_manager: PermissionManager = Depends(get_permission_manager),
    db=Depends(get_database)
) -> SuccessResponse:
    """Perform file operations (copy, move, delete)"""
    try:
        source_path = Path(operation.source_path)
        target_path = Path(operation.target_path) if operation.target_path else None

        # Validate source path
        if not perm_manager.validate_file_access(str(source_path), operation.workspace_path):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Source file access denied: path outside workspace"
            )

        if not source_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source file not found: {source_path}"
            )

        if operation.action == "delete":
            # Delete file
            if source_path.is_file():
                source_path.unlink()
            else:
                shutil.rmtree(str(source_path))

            # Remove from database
            await delete_file_record_from_database(db, str(source_path))

            logger.info(f"Deleted file: {source_path}")
            return SuccessResponse(
                success=True,
                message=f"File deleted successfully: {source_path.name}"
            )

        elif operation.action in ["copy", "move"]:
            if not target_path:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Target path required for copy/move operations"
                )

            # Validate target path
            if not perm_manager.validate_file_access(str(target_path), operation.workspace_path):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Target file access denied: path outside workspace"
                )

            # Create target directory if needed
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Perform operation
            if operation.action == "copy":
                if source_path.is_file():
                    shutil.copy2(str(source_path), str(target_path))
                else:
                    shutil.copytree(str(source_path), str(target_path))

                logger.info(f"Copied file: {source_path} -> {target_path}")
                message = f"File copied successfully: {source_path.name} -> {target_path.name}"

            elif operation.action == "move":
                shutil.move(str(source_path), str(target_path))

                # Update database record
                await update_file_record_path_in_database(db, str(source_path), str(target_path))

                logger.info(f"Moved file: {source_path} -> {target_path}")
                message = f"File moved successfully: {source_path.name} -> {target_path.name}"

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid operation: {operation.action}"
            )

        return SuccessResponse(
            success=True,
            message=message
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File operation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File operation failed: {str(e)}"
        )


@router.get("/preview/{workspace_path:path}", response_model=Dict[str, Any])
async def preview_file(
    workspace_path: str,
    file_path: str,
    max_lines: int = MAX_FILE_PREVIEW_LINES,
    perm_manager: PermissionManager = Depends(get_permission_manager)
) -> Dict[str, Any]:
    """Preview file content (for text files)"""
    try:
        # Validate file path
        full_path = Path(workspace_path) / file_path

        if not perm_manager.validate_file_access(str(full_path), workspace_path):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="File access denied: path outside workspace"
            )

        if not full_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {full_path}"
            )

        if not full_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Path is not a file: {full_path}"
            )

        # Check file size (limit to 1MB for preview)
        file_size = full_path.stat().st_size
        if file_size > MAX_FILE_PREVIEW_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large for preview (>{MAX_FILE_PREVIEW_SIZE // (1024*1024)}MB)"
            )

        # Determine if file is text
        mime_type = mimetypes.guess_type(str(full_path))[0]
        if mime_type and not mime_type.startswith('text/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File preview not available for binary files"
            )

        # Read file content
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = []
                total_lines = 0

                for i, line in enumerate(f):
                    total_lines += 1
                    if i < max_lines:
                        lines.append({
                            "line_number": i + 1,
                            "content": line.rstrip('\n')
                        })

            return {
                "filename": full_path.name,
                "file_path": file_path,
                "size": file_size,
                "total_lines": total_lines,
                "preview_lines": len(lines),
                "content": lines,
                "mime_type": mime_type or "text/plain"
            }

        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File encoding not supported for preview"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File preview failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File preview failed: {str(e)}"
        )


# Helper functions
async def save_file_record_to_database(db, file_record: Dict[str, Any]):
    """Save file record to database"""
    try:
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO files (
                filename, safe_filename, file_path, workspace_path,
                subdirectory, size, mime_type, uploaded_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            file_record["filename"],
            file_record["safe_filename"],
            file_record["file_path"],
            file_record["workspace_path"],
            file_record["subdirectory"],
            file_record["size"],
            file_record["mime_type"],
            file_record["uploaded_at"]
        ))

        db.commit()

    except Exception as e:
        logger.error(f"Failed to save file record to database: {e}")
        raise


async def get_file_records_from_database(db, workspace_path: str) -> List[Dict[str, Any]]:
    """Get file records from database for workspace"""
    try:
        cursor = db.cursor()

        cursor.execute("""
            SELECT filename, file_path, size, mime_type, uploaded_at
            FROM files WHERE workspace_path = ?
            ORDER BY uploaded_at DESC
        """, (workspace_path,))

        return [
            {
                "filename": row[0],
                "file_path": row[1],
                "size": row[2],
                "mime_type": row[3],
                "uploaded_at": row[4]
            }
            for row in cursor.fetchall()
        ]

    except Exception as e:
        logger.error(f"Failed to get file records from database: {e}")
        return []


async def delete_file_record_from_database(db, file_path: str):
    """Delete file record from database"""
    try:
        cursor = db.cursor()

        cursor.execute("DELETE FROM files WHERE file_path = ?", (file_path,))

        db.commit()

    except Exception as e:
        logger.error(f"Failed to delete file record from database: {e}")
        raise


async def update_file_record_path_in_database(db, old_path: str, new_path: str):
    """Update file record path in database"""
    try:
        cursor = db.cursor()

        cursor.execute("UPDATE files SET file_path = ? WHERE file_path = ?", (new_path, old_path))

        db.commit()

    except Exception as e:
        logger.error(f"Failed to update file record in database: {e}")
        raise