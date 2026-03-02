## Why

The codebase contains residual Snakemake code after decoupling, duplicate implementations (Tool Registry, FileInfo models), inconsistent error handling, and unused imports. These issues increase technical debt, reduce maintainability, and can cause runtime errors.

## What Changes

- **Remove Snakemake Residuals**
  - Clean up database schema (`snakemake_args` column)
  - Remove Snakemake-specific code from logging, WebSocket monitoring, and node mapping
  - Update model field names and comments to reflect FlowEngine architecture

- **Consolidate Duplicate Implementations**
  - Merge three `get_tool_registry()` functions into single implementation
  - Unify duplicate FileInfo models into one canonical definition
  - Use dependency injection pattern consistently

- **Standardize Error Handling**
  - Replace hardcoded HTTP status codes with `status.HTTP_*` constants
  - Ensure consistent error response format across all API endpoints

- **Code Cleanup**
  - Remove unused imports (`StreamingResponse`, external `src.nodes` references)
  - Extract magic numbers to configuration constants
  - Complete empty schema files (e.g., `workflow.py`)

- **BREAKING**: Database migration required to rename `snakemake_args` → `engine_args`

## Capabilities

### New Capabilities
- `unified-tool-registry`: Centralized tool registry access using dependency injection
- `clean-file-models`: Single source of truth for file information models
- `engine-architecture`: Remove all Snakemake references and standardize on FlowEngine terminology

### Modified Capabilities
- None (this is internal refactoring without external API behavior changes)

## Impact

- **Database**: Requires migration to rename columns and remove legacy fields
- **Services**: `tool_registry.py`, `log_handler.py`, `node_mapper.py` require updates
- **API**: All endpoint files need error handling standardization
- **Dependencies**: May remove unused services (`cwl_exporter.py`, `engine_adapter.py`)
- **Tests**: Database and integration tests need updates for schema changes
