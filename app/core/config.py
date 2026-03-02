"""
Application Configuration Constants

Centralized configuration for file handling, API limits, and other application settings.
"""

# File upload and preview limits
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MAX_FILE_PREVIEW_SIZE = 1024 * 1024  # 1MB
MAX_FILE_PREVIEW_LINES = 100  # Maximum lines for file preview

# API pagination defaults
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Workspace settings
DEFAULT_WORKSPACE_PATH = "data/workflows"
MAX_FILENAME_LENGTH = 255

# Supported file categories
TEXT_FILE_EXTENSIONS = {
    '.txt', '.csv', '.json', '.xml', '.yaml', '.yml',
    '.md', '.py', '.js', '.ts', '.html', '.css',
    '.sh', '.bash', '.zsh', '.fish',
    '.conf', '.config', '.ini', '.cfg',
}

# Chunk size for file operations
FILE_CHUNK_SIZE = 8192  # 8KB chunks for file reading
