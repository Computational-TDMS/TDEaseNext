"""
File Permission and Workspace Management
Cross-platform file permission handling and workspace management
"""

import os
import stat
import platform
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
import time

logger = logging.getLogger(__name__)


class PermissionManager:
    """Cross-platform permission and workspace management"""

    def __init__(self):
        self.platform = platform.system().lower()

    def get_platform_info(self) -> Dict[str, Any]:
        """Get current platform information"""
        return {
            "system": self.platform,
            "has_chmod": hasattr(os, 'chmod'),
            "has_file_attributes": hasattr(stat, 'file_attributes'),
            "supports_ownership": self.platform != "windows"
        }

    async def check_workspace_permissions(self, workspace_path: str) -> Dict[str, Any]:
        """Check workspace directory permissions"""
        permissions = {
            "exists": False,
            "readable": False,
            "writable": False,
            "executable": False,
            "is_directory": False,
            "error": None
        }

        try:
            abs_path = os.path.abspath(workspace_path)
            permissions["exists"] = os.path.exists(abs_path)

            if not permissions["exists"]:
                # Check if parent directory is writable for creation
                parent_path = os.path.dirname(abs_path)
                if parent_path and os.path.exists(parent_path):
                    permissions["parent_writable"] = os.access(parent_path, os.W_OK)
                else:
                    permissions["error"] = f"Parent directory does not exist: {parent_path}"
                return permissions

            permissions["is_directory"] = os.path.isdir(abs_path)

            if permissions["is_directory"]:
                permissions["readable"] = os.access(abs_path, os.R_OK)
                permissions["writable"] = os.access(abs_path, os.W_OK)
                permissions["executable"] = os.access(abs_path, os.X_OK)

                # Get detailed permissions on Unix/Linux
                if self.platform != "windows":
                    stat_info = os.stat(abs_path)
                    permissions.update(self._get_unix_permissions(stat_info))

                # Get Windows-specific info
                if self.platform == "windows":
                    permissions.update(await self._get_windows_permissions(abs_path))

            else:
                permissions["error"] = "Path exists but is not a directory"

        except Exception as e:
            logger.error(f"Permission check failed for {workspace_path}: {e}")
            permissions["error"] = str(e)

        return permissions

    def _get_unix_permissions(self, stat_info) -> Dict[str, Any]:
        """Get Unix/Linux specific permission information"""
        mode = stat_info.st_mode

        return {
            "mode": oct(mode)[-3:],
            "mode_octal": oct(mode),
            "uid": stat_info.st_uid,
            "gid": stat_info.st_gid,
            "owner_read": bool(mode & stat.S_IRUSR),
            "owner_write": bool(mode & stat.S_IWUSR),
            "owner_execute": bool(mode & stat.S_IXUSR),
            "group_read": bool(mode & stat.S_IRGRP),
            "group_write": bool(mode & stat.S_IWGRP),
            "group_execute": bool(mode & stat.S_IXGRP),
            "other_read": bool(mode & stat.S_IROTH),
            "other_write": bool(mode & stat.S_IWOTH),
            "other_execute": bool(mode & stat.S_IXOTH),
            "is_setuid": bool(mode & stat.S_ISUID),
            "is_setgid": bool(mode & stat.S_ISGID),
            "is_sticky": bool(mode & stat.S_ISVTX)
        }

    async def _get_windows_permissions(self, path: str) -> Dict[str, Any]:
        """Get Windows specific permission information"""
        permissions = {
            "readonly": False,
            "hidden": False,
            "system": False,
            "archive": False,
            "encrypted": False,
            "compressed": False,
            "sparse": False,
            "reparse_point": False,
            "offline": False,
            "not_content_indexed": False
        }

        try:
            stat_info = os.stat(path)
            if hasattr(stat, 'file_attributes'):
                attrs = stat_info.st_file_attributes

                # Windows file attribute constants
                FILE_ATTRIBUTE_READONLY = 0x1
                FILE_ATTRIBUTE_HIDDEN = 0x2
                FILE_ATTRIBUTE_SYSTEM = 0x4
                FILE_ATTRIBUTE_ARCHIVE = 0x20
                FILE_ATTRIBUTE_ENCRYPTED = 0x4000
                FILE_ATTRIBUTE_COMPRESSED = 0x800
                FILE_ATTRIBUTE_SPARSE = 0x200
                FILE_ATTRIBUTE_REPARSE_POINT = 0x400
                FILE_ATTRIBUTE_OFFLINE = 0x1000
                FILE_ATTRIBUTE_NOT_CONTENT_INDEXED = 0x2000

                permissions.update({
                    "readonly": bool(attrs & FILE_ATTRIBUTE_READONLY),
                    "hidden": bool(attrs & FILE_ATTRIBUTE_HIDDEN),
                    "system": bool(attrs & FILE_ATTRIBUTE_SYSTEM),
                    "archive": bool(attrs & FILE_ATTRIBUTE_ARCHIVE),
                    "encrypted": bool(attrs & FILE_ATTRIBUTE_ENCRYPTED),
                    "compressed": bool(attrs & FILE_ATTRIBUTE_COMPRESSED),
                    "sparse": bool(attrs & FILE_ATTRIBUTE_SPARSE),
                    "reparse_point": bool(attrs & FILE_ATTRIBUTE_REPARSE_POINT),
                    "offline": bool(attrs & FILE_ATTRIBUTE_OFFLINE),
                    "not_content_indexed": bool(attrs & FILE_ATTRIBUTE_NOT_CONTENT_INDEXED)
                })

        except Exception as e:
            logger.debug(f"Failed to get Windows permissions for {path}: {e}")

        return permissions

    async def ensure_workspace_structure(self, workspace_path: str) -> bool:
        """Ensure workspace has proper directory structure"""
        try:
            abs_path = os.path.abspath(workspace_path)

            # Create workspace if it doesn't exist
            if not os.path.exists(abs_path):
                os.makedirs(abs_path, exist_ok=True)
                logger.info(f"Created workspace directory: {abs_path}")

            # Create subdirectories
            subdirs = ["input_files", "workflow_files", "results", "logs"]
            for subdir in subdirs:
                subdir_path = os.path.join(abs_path, subdir)
                os.makedirs(subdir_path, exist_ok=True)
                logger.debug(f"Ensured subdirectory exists: {subdir_path}")

                # Set appropriate permissions on Unix/Linux
                if self.platform != "windows":
                    try:
                        os.chmod(subdir_path, 0o755)
                        logger.debug(f"Set permissions 755 on: {subdir_path}")
                    except Exception as e:
                        logger.warning(f"Failed to set permissions on {subdir_path}: {e}")

            return True

        except Exception as e:
            logger.error(f"Workspace structure creation failed for {workspace_path}: {e}")
            return False

    def validate_file_access(self, file_path: str, workspace_root: str) -> bool:
        """Validate file access is within allowed workspace"""
        try:
            abs_file = os.path.abspath(file_path)
            abs_workspace = os.path.abspath(workspace_root)

            # Check if file is within workspace directory
            return abs_file.startswith(abs_workspace + os.sep) or abs_file == abs_workspace

        except Exception:
            return False

    def get_safe_filename(self, filename: str) -> str:
        """Generate platform-safe filename"""
        if not filename:
            return f"file_{int(time.time())}"

        # Platform-specific unsafe characters
        if self.platform == "windows":
            unsafe_chars = '<>:"/\\|?*'
        else:
            unsafe_chars = '/\\'

        safe_name = filename
        for char in unsafe_chars:
            safe_name = safe_name.replace(char, '_')

        # Remove control characters
        safe_name = ''.join(char for char in safe_name if ord(char) >= 32)

        # Ensure filename is not empty and has reasonable length
        if not safe_name or len(safe_name) > 255:
            safe_name = f"file_{int(time.time())}"

        # Ensure filename doesn't start with dot or hyphen (hidden files on Unix)
        if safe_name.startswith(('.', '-')):
            safe_name = f"file_{safe_name.lstrip('.-')}"

        return safe_name

    async def get_file_permissions_info(self, file_path: str) -> Dict[str, Any]:
        """Get detailed file permission information"""
        try:
            if not os.path.exists(file_path):
                return {
                    "accessible": False,
                    "error": "File does not exist"
                }

            stat_info = os.stat(file_path)
            is_dir = os.path.isdir(file_path)

            permissions = {
                "accessible": True,
                "exists": True,
                "is_directory": is_dir,
                "size": stat_info.st_size,
                "modified": stat_info.st_mtime,
                "created": getattr(stat_info, 'st_ctime', stat_info.st_mtime)
            }

            if self.platform != "windows":
                permissions.update(self._get_unix_permissions(stat_info))
            else:
                permissions.update(await self._get_windows_permissions(file_path))

            return permissions

        except Exception as e:
            logger.error(f"Failed to get file permissions for {file_path}: {e}")
            return {
                "accessible": False,
                "error": str(e)
            }

    async def list_workspace_files(self, workspace_path: str) -> List[Dict[str, Any]]:
        """List files in user workspace with metadata"""
        files = []

        try:
            if not os.path.exists(workspace_path):
                return files

            for root, dirs, filenames in os.walk(workspace_path):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    try:
                        rel_path = os.path.relpath(file_path, workspace_path)
                        file_info = await self.get_file_permissions_info(file_path)
                        file_info["relative_path"] = rel_path
                        file_info["workspace_path"] = workspace_path
                        files.append(file_info)
                    except Exception as e:
                        logger.warning(f"Failed to get info for {file_path}: {e}")

        except Exception as e:
            logger.error(f"Failed to list workspace files {workspace_path}: {e}")

        return files

    def create_upload_file_path(self, workspace_path: str, original_filename: str) -> str:
        """Create safe upload file path in workspace"""
        safe_filename = self.get_safe_filename(original_filename)
        input_files_dir = os.path.join(workspace_path, "input_files")

        # Ensure input_files directory exists
        os.makedirs(input_files_dir, exist_ok=True)

        # Create full path
        file_path = os.path.join(input_files_dir, safe_filename)

        # Handle filename collisions
        counter = 1
        while os.path.exists(file_path):
            name, ext = os.path.splitext(safe_filename)
            file_path = os.path.join(input_files_dir, f"{name}_{counter}{ext}")
            counter += 1

        return file_path

    async def set_file_permissions(self, file_path: str, readable: bool = True,
                                 writable: bool = True, executable: bool = False) -> bool:
        """Set file permissions with platform-appropriate method"""
        try:
            if self.platform != "windows":
                # Unix/Linux - use chmod
                mode = 0o000
                if readable:
                    mode |= 0o444  # r--r--r--
                if writable:
                    mode |= 0o222  # -w--w--w-
                if executable:
                    mode |= 0o111  # --x--x--

                os.chmod(file_path, mode)
                logger.debug(f"Set Unix permissions {oct(mode)} on {file_path}")
            else:
                # Windows - limited permission control
                # Remove readonly attribute if writable
                if writable and os.path.exists(file_path):
                    try:
                        import win32api, win32con, winerror

                        attrs = win32api.GetFileAttributesW(file_path)
                        if attrs & win32con.FILE_ATTRIBUTE_READONLY:
                            win32api.SetFileAttributesW(
                                file_path,
                                attrs & ~win32con.FILE_ATTRIBUTE_READONLY
                            )
                    except ImportError:
                        # pywin32 not available, basic handling only
                        logger.warning("pywin32 not available for Windows permission management")
                        pass

            return True

        except Exception as e:
            logger.error(f"Failed to set permissions for {file_path}: {e}")
            return False


# Singleton instance for global use
_permission_manager = None


def get_permission_manager() -> PermissionManager:
    """Get global permission manager instance"""
    global _permission_manager
    if _permission_manager is None:
        _permission_manager = PermissionManager()
    return _permission_manager