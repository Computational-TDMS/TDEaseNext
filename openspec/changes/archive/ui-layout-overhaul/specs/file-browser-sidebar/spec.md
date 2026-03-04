# File Browser Sidebar

## Purpose

Provides a workspace file browser panel within the Primary Sidebar of the workflow editor. Users can browse the directory tree of the active workspace, inspect file metadata, and preview file contents. This panel is integrated as one of the Activity Bar tabs alongside the Node Toolbox.

## Requirements

### Requirement: Workspace directory tree display
The system SHALL render the workspace directory tree in the File Browser sidebar panel using a tree component.

#### Scenario: File browser loads on tab activation
- **WHEN** the user activates the `files` tab in the Activity Bar
- **THEN** the File Browser SHALL fetch the workspace directory tree from `GET /api/users/{user_id}/workspaces/{workspace_id}/files`
- **AND** display the result as a collapsible tree (directories before files, sorted alphabetically)
- **AND** show a loading indicator while fetching

#### Scenario: File browser shows placeholder when API unavailable
- **WHEN** the backend `workspace-file-browser` capability is not available (request fails)
- **THEN** the File Browser SHALL display a message: "文件浏览功能需要后端 API 支持"
- **AND** SHALL NOT crash the application

#### Scenario: Directory expand and collapse
- **WHEN** the user clicks a directory node in the tree
- **THEN** that directory's children SHALL expand or collapse
- **AND** expanded state SHALL be preserved within the current session

### Requirement: File content preview
The system SHALL allow users to preview file contents by clicking a file node.

#### Scenario: Clicking a tabular file shows preview in bottom panel
- **WHEN** the user clicks a file with a recognized tabular extension (.tsv, .csv, .feature, .ms1ft)
- **THEN** the system SHALL fetch `GET /api/users/{user_id}/workspaces/{workspace_id}/file-content?path=...&max_rows=100`
- **AND** display the first 100 rows in the Bottom Panel as a table
- **AND** show total row count if available

#### Scenario: Clicking a text file shows text preview
- **WHEN** the user clicks a file returning `file_type: "text"`
- **THEN** the Bottom Panel SHALL display the raw text content in a monospace code area

#### Scenario: Binary files show metadata only
- **WHEN** the user clicks a file returning `file_type: "binary"`
- **THEN** the system SHALL display file metadata (name, size, modified) but not attempt to render content
