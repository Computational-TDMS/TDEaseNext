"""
Cross-Platform Tool Discovery and Management
Handles tool discovery across Windows and Linux platforms
"""

import platform
import shutil
import subprocess
import asyncio
import os
import stat
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from re import search as regex_search

logger = logging.getLogger(__name__)


class PlatformToolManager:
    """Manages cross-platform tool discovery and validation"""

    def __init__(self, tool_registry=None):
        self.platform = platform.system().lower()
        self.tool_registry = tool_registry
        self.discovery_cache = {}
        self.cache_timeout = 3600  # 1 hour

    def get_platform_info(self) -> Dict[str, Any]:
        """Get current platform information"""
        return {
            "system": self.platform,
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "architecture": platform.architecture(),
            "platform": platform.platform()
        }

    async def discover_tool_paths(self, tool_type: str) -> List[str]:
        """Discover tool executable paths across platforms"""
        logger.info(f"Discovering tool paths for {tool_type} on {self.platform}")

        # Check cache first
        cache_key = f"{self.platform}_{tool_type}"
        current_time = time.time()

        if (cache_key in self.discovery_cache and
            current_time - self.discovery_cache[cache_key]["timestamp"] < self.cache_timeout):
            logger.debug(f"Using cached results for {tool_type}")
            return self.discovery_cache[cache_key]["paths"]

        paths = []

        if self.platform == "windows":
            paths = await self._discover_windows_tools(tool_type)
        else:
            paths = await self._discover_unix_tools(tool_type)

        # Cache results
        self.discovery_cache[cache_key] = {
            "paths": paths,
            "timestamp": current_time
        }

        logger.info(f"Found {len(paths)} paths for {tool_type}: {paths}")
        return paths

    async def _discover_windows_tools(self, tool_type: str) -> List[str]:
        """Discover tools on Windows platform"""
        paths = []

        if not self.tool_registry:
            logger.warning("Tool registry not available, using fallback discovery")
            return await self._fallback_windows_discovery(tool_type)

        tool_info = self.tool_registry.get_tool_info(tool_type)
        if not tool_info:
            logger.warning(f"Tool type {tool_type} not found in registry")
            return []

        tool_name = tool_info.get("tool_path", tool_type)
        logger.debug(f"Discovering Windows tool: {tool_name}")

        # Check PATH with extensions
        extensions = ['.exe', '.bat', '.cmd', '.ps1']
        for ext in extensions:
            full_name = tool_name + ext if not tool_name.endswith(ext) else tool_name
            path = shutil.which(full_name)
            if path:
                paths.append(path)
                logger.debug(f"Found in PATH: {full_name} -> {path}")

        # Check common installation directories
        common_dirs = self._get_windows_installation_dirs()
        for base_dir in common_dirs:
            if not base_dir.exists():
                continue

            logger.debug(f"Searching in: {base_dir}")
            try:
                for root, dirs, files in os.walk(base_dir):
                    # Limit depth to avoid long searches
                    depth = root.replace(str(base_dir), '').count(os.sep)
                    if depth > 3:
                        continue

                    for file in files:
                        file_lower = file.lower()
                        if (tool_name.lower() in file_lower and
                            any(file_lower.endswith(ext.lower()) for ext in extensions)):
                            full_path = os.path.join(root, file)
                            if os.path.isfile(full_path):
                                paths.append(full_path)
                                logger.debug(f"Found in directory: {full_path}")

            except (PermissionError, OSError) as e:
                logger.debug(f"Cannot search directory {base_dir}: {e}")
                continue

        # Remove duplicates
        paths = list(set(paths))
        return paths

    async def _discover_unix_tools(self, tool_type: str) -> List[str]:
        """Discover tools on Unix/Linux platforms"""
        paths = []

        if not self.tool_registry:
            logger.warning("Tool registry not available, using fallback discovery")
            return await self._fallback_unix_discovery(tool_type)

        tool_info = self.tool_registry.get_tool_info(tool_type)
        if not tool_info:
            logger.warning(f"Tool type {tool_type} not found in registry")
            return []

        tool_name = tool_info.get("tool_path", tool_type)
        logger.debug(f"Discovering Unix tool: {tool_name}")

        # Check PATH
        path = shutil.which(tool_name)
        if path:
            paths.append(path)
            logger.debug(f"Found in PATH: {tool_name} -> {path}")

        # Check common installation directories
        common_dirs = self._get_unix_installation_dirs()
        for base_dir in common_dirs:
            if not base_dir.exists():
                continue

            logger.debug(f"Searching in: {base_dir}")
            tool_path = base_dir / tool_name
            if tool_path.exists() and os.access(tool_path, os.X_OK):
                paths.append(str(tool_path))
                logger.debug(f"Found in directory: {tool_path}")

        # Remove duplicates
        paths = list(set(paths))
        return paths

    def _get_windows_installation_dirs(self) -> List[Path]:
        """Get common Windows installation directories"""
        program_files = [
            Path(os.environ.get("ProgramFiles", "C:\\Program Files")),
            Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")),
            Path("C:\\Program Files\\OpenMS"),
            Path("C:\\Program Files (x86)\\OpenMS"),
            Path("C:\\TopPIC Suite"),
            Path("C:\\ProteoWizard"),
            Path("C:\\msconvert"),
            Path("C:\\Tools")
        ]

        # Add user-specific directories
        user_profile = os.environ.get("USERPROFILE", "")
        if user_profile:
            user_dirs = [
                Path(user_profile) / "AppData" / "Local" / "Programs",
                Path(user_profile) / "AppData" / "Roaming",
                Path(user_profile) / "Downloads"
            ]
            program_files.extend(user_dirs)

        return [d for d in program_files if d.exists()]

    def _get_unix_installation_dirs(self) -> List[Path]:
        """Get common Unix/Linux installation directories"""
        home = Path.home()
        dirs = [
            Path("/usr/local/bin"),
            Path("/usr/bin"),
            Path("/opt/toppic"),
            Path("/opt/openms"),
            Path("/usr/local/toppic"),
            Path("/usr/local/openms"),
            Path("/opt/tools"),
            home / ".local" / "bin",
            home / "bin",
            home / "Tools"
        ]

        return [d for d in dirs if d.exists()]

    async def _fallback_windows_discovery(self, tool_type: str) -> List[str]:
        """Fallback Windows discovery when registry is not available"""
        tool_names = {
            "msconvert": ["msconvert.exe", "msconvert"],
            "topfd": ["topfd.exe", "topfd"],
            "toppic": ["toppic.exe", "toppic"],
            "topmg": ["topmg.exe", "topmg"],
            "topdiff": ["topdiff.exe", "topdiff"],
            "topindex": ["topindex.exe", "topindex"],
            "topdia": ["topdia.exe", "topdia"],
            "massql": ["massql.exe", "massql"]
        }

        names = tool_names.get(tool_type, [tool_type + ".exe", tool_type])
        paths = []

        for name in names:
            path = shutil.which(name)
            if path:
                paths.append(path)

        return paths

    async def _fallback_unix_discovery(self, tool_type: str) -> List[str]:
        """Fallback Unix discovery when registry is not available"""
        tool_names = {
            "msconvert": ["msconvert", "pwiz"],
            "topfd": ["topfd"],
            "toppic": ["toppic"],
            "massql": ["massql"]
        }

        names = tool_names.get(tool_type, [tool_type])
        paths = []

        for name in names:
            path = shutil.which(name)
            if path:
                paths.append(path)

        return paths

    async def validate_tool_execution(self, tool_path: str, tool_type: str) -> bool:
        """Validate that tool can execute and return version information"""
        logger.info(f"Validating tool execution: {tool_path}")

        try:
            # Handle Windows path escaping
            if self.platform == "windows":
                if " " in tool_path and not tool_path.startswith('"'):
                    tool_path = f'"{tool_path}"'

            # Test with --version or --help flags
            test_args = ["--version", "--help", "-h", "--version-check"]

            for arg in test_args:
                try:
                    result = await asyncio.create_subprocess_exec(
                        tool_path, arg,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        timeout=10
                    )
                    stdout, stderr = await result.communicate()

                    if result.returncode == 0:
                        logger.info(f"Tool validation successful: {tool_path} {arg}")
                        return True

                    # Some tools return non-zero for --help but still work
                    if arg in ["--help", "-h"] and "usage" in stderr.lower():
                        logger.info(f"Tool validation successful (help): {tool_path}")
                        return True

                except asyncio.TimeoutError:
                    logger.debug(f"Tool validation timeout: {tool_path} {arg}")
                    continue
                except Exception as e:
                    logger.debug(f"Tool validation error: {tool_path} {arg} - {e}")
                    continue

            logger.warning(f"Tool validation failed: {tool_path}")
            return False

        except Exception as e:
            logger.error(f"Tool validation exception: {tool_path} - {e}")
            return False

    async def get_tool_version(self, tool_path: str) -> Optional[str]:
        """Get tool version information"""
        try:
            # Handle Windows path escaping
            if self.platform == "windows" and " " in tool_path:
                tool_path = f'"{tool_path}"'

            result = await asyncio.create_subprocess_exec(
                tool_path, "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                timeout=10
            )

            stdout, stderr = await result.communicate()

            # Parse version from output
            version_output = stdout or stderr
            version_match = regex_search(r'(\d+\.\d+(?:\.\d+)?)', version_output)

            if version_match:
                return version_match.group(1)

            return None

        except Exception as e:
            logger.debug(f"Failed to get version for {tool_path}: {e}")
            return None

    def normalize_path(self, path: str) -> str:
        """Normalize path for current platform"""
        # Use os.path.normpath for platform-specific normalization
        normalized = os.path.normpath(path)

        if self.platform == "windows":
            # Handle Windows-specific path issues
            if not normalized.startswith('\\\\') and ':' not in normalized[:2]:
                # Convert relative to absolute
                normalized = os.path.abspath(normalized)

            # Ensure proper backslashes for Windows
            normalized = normalized.replace('/', '\\')
        else:
            # Unix/Linux - ensure forward slashes
            normalized = normalized.replace('\\', '/')

        return normalized

    def get_safe_filename(self, filename: str) -> str:
        """Generate platform-safe filename"""
        unsafe_chars = '<>:"/\\|?*' if self.platform == "windows" else '/\\'
        safe_name = filename

        for char in unsafe_chars:
            safe_name = safe_name.replace(char, '_')

        # Ensure filename is not empty and has reasonable length
        if not safe_name or len(safe_name) > 255:
            safe_name = f"file_{int(time.time())}"

        return safe_name

    async def get_tool_info(self, tool_type: str) -> Dict[str, Any]:
        """Get comprehensive tool information including platform details"""
        tool_paths = await self.discover_tool_paths(tool_type)

        if not tool_paths:
            return {
                "tool_type": tool_type,
                "is_available": False,
                "platform": self.platform,
                "paths": [],
                "version": None,
                "error": "Tool not found"
            }

        # Validate each path and get version
        valid_paths = []
        version = None

        for path in tool_paths:
            if await self.validate_tool_execution(path, tool_type):
                valid_paths.append(path)
                if not version:
                    version = await self.get_tool_version(path)

        return {
            "tool_type": tool_type,
            "is_available": len(valid_paths) > 0,
            "platform": self.platform,
            "paths": valid_paths,
            "version": version,
            "preferred_path": valid_paths[0] if valid_paths else None
        }

    async def get_available_tools(self) -> Dict[str, Any]:
        """Get all available tools with their information"""
        tools = {}
        common_tools = ["python", "pip", "curl", "wget", "git"]

        for tool_name in common_tools:
            tool_path = shutil.which(tool_name)
            if tool_path:
                version = await self.get_tool_version(tool_path)
                tools[tool_name] = {
                    "path": tool_path,
                    "available": True,
                    "version": version,
                    "category": "utility"
                }

        return tools

    def validate_executable(self, executable_path: str) -> bool:
        """Validate if executable exists and is executable"""
        path = Path(executable_path)
        return path.exists() and (path.is_file() or path.is_symlink()) and os.access(str(path), os.X_OK)


class PathManager:
    """Cross-platform path management utilities"""

    def __init__(self):
        self.platform = platform.system().lower()

    def validate_file_access(self, file_path: str, workspace_root: str) -> bool:
        """Validate file access is within allowed workspace"""
        try:
            abs_file = os.path.abspath(file_path)
            abs_workspace = os.path.abspath(workspace_root)

            # Check if file is within workspace directory
            return (abs_file == abs_workspace or
                    abs_file.startswith(abs_workspace + os.sep))

        except Exception as e:
            logger.error(f"File access validation error: {e}")
            return False

    def create_safe_path(self, base_path: str, *parts: str) -> str:
        """Create safe path joining with platform-specific separators"""
        try:
            if self.platform == "windows":
                # Windows: handle absolute paths properly
                if parts and os.path.isabs(parts[0]):
                    # If first part is absolute, ignore base_path
                    result_path = os.path.join(*parts)
                else:
                    result_path = os.path.join(base_path, *parts)
            else:
                # Unix: standard path joining
                result_path = os.path.join(base_path, *parts)

            # Normalize for platform
            return os.path.normpath(result_path)

        except Exception as e:
            logger.error(f"Path creation error: {e}")
            # Fallback to simple joining
            return os.path.join(base_path, *parts)


# Singleton instance for global use
_platform_manager = None


def get_platform_manager(tool_registry=None) -> PlatformToolManager:
    """Get global platform manager instance"""
    global _platform_manager
    if _platform_manager is None:
        _platform_manager = PlatformToolManager(tool_registry)
    return _platform_manager


def get_path_manager() -> PathManager:
    """Get path manager instance"""
    return PathManager()