# Workspace File Browser

## Purpose

Provides API endpoints for browsing workspace file systems and previewing file contents. This capability enables the frontend to render a file browser sidebar and show file previews to users.

## Requirements

### Requirement: Workspace directory tree listing
The system SHALL provide an API endpoint to return the complete directory tree structure of a workspace, suitable for rendering a file browser sidebar.

#### Scenario: List workspace files
- **WHEN** client sends `GET /api/users/{user_id}/workspaces/{workspace_id}/files`
- **AND** the workspace exists
- **THEN** the system SHALL return a recursive tree structure where each entry contains `name`, `type` ("file" or "directory"), `path` (relative to workspace root)
- **AND** file entries SHALL include `size` (bytes), `extension`, `modified` (timestamp)
- **AND** directory entries SHALL include `children` (recursive)
- **AND** entries SHALL be sorted: directories first, then files, alphabetically

#### Scenario: Workspace not found
- **WHEN** the workspace path does not exist
- **THEN** the system SHALL return HTTP 404

#### Scenario: Hidden files excluded
- **WHEN** traversing the directory tree
- **THEN** entries whose name starts with `.` SHALL be excluded

### Requirement: File content preview
The system SHALL provide an API endpoint to preview file contents within a workspace, limited to a configurable number of rows for tabular files.

#### Scenario: Preview tabular file
- **WHEN** client sends `GET /api/users/{user_id}/workspaces/{workspace_id}/file-content?path=relative/path.tsv&max_rows=50`
- **AND** the file exists and is a tabular format (.tsv, .csv, .txt, .ms1ft, .feature)
- **THEN** the system SHALL return `file_type: "tabular"` with `content` containing `columns`, `rows` (up to max_rows), `total_rows`, `preview_rows`

#### Scenario: Preview text file
- **WHEN** the file is a non-tabular text file (e.g., .fasta, .log, .json, .yaml)
- **THEN** the system SHALL return `file_type: "text"` with `content` as the raw text string (truncated to a reasonable limit, e.g., 100KB)

#### Scenario: Binary file
- **WHEN** the file is a binary format (.pbf, .raw, .mzml, .png, .exe)
- **THEN** the system SHALL return `file_type: "binary"` with `content: null` and file metadata only

#### Scenario: Default max_rows
- **WHEN** `max_rows` is not provided
- **THEN** the system SHALL default to 100 rows

#### Scenario: File not found
- **WHEN** the requested file path does not exist within the workspace
- **THEN** the system SHALL return HTTP 404

#### Scenario: Path traversal prevention
- **WHEN** the requested path contains `..` or attempts to escape the workspace root
- **THEN** the system SHALL return HTTP 403
