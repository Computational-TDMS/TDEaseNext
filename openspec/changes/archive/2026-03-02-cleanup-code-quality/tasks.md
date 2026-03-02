## 1. Database Migration (Critical - Blocking)

- [x] 1.1 Create Alembic migration file for Snakemake field removal
- [x] 1.2 Add migration operation to rename `snakemake_args` → `engine_args`
- [x] 1.3 Add migration operation to drop `snakemake_status` column
- [x] 1.4 Create downgrade migration for rollback capability
- [x] 1.5 Test migration on development database
- [x] 1.6 Update `app/models/execution.py` field from `snakemake_args` to `engine_args`
- [x] 1.7 Remove `snakemake_status` field from `app/models/workflow.py`
- [x] 1.8 Update all references to old field names in database queries

## 2. FileInfo Model Consolidation (Critical)

- [x] 2.1 Create consolidated FileInfo model in `app/models/common.py` with all fields (id, filename, filepath, size, file_type, metadata, created_at, updated_at)
- [x] 2.2 Update imports in `app/models/files.py` to use consolidated FileInfo
- [x] 2.3 Search and replace all FileInfo imports across codebase
- [x] 2.4 Remove duplicate FileInfo definition from `app/models/files.py`
- [x] 2.5 Update Pydantic schemas to match consolidated FileInfo model
- [x] 2.6 Run tests to verify no broken references

## 3. Tool Registry Unification (Critical)

- [x] 3.1 Verify `get_tool_registry()` in `app/services/tool_registry.py` is complete
- [x] 3.2 Remove duplicate `get_tool_registry()` from `app/dependencies.py`
- [x] 3.3 Remove duplicate `get_tool_registry()` from `app/api/tools.py`
- [x] 3.4 Remove `from src.nodes.tool_registry import ToolRegistry` from `app/dependencies.py`
- [x] 3.5 Update all API endpoints to use `Depends(get_tool_registry)` from services
- [x] 3.6 Add type hints for tool registry dependency injection
- [x] 3.7 Run tests to verify tool registry functionality

## 4. Model Field Cleanup (High Priority)

- [x] 4.1 Update `app/models/execution.py` remove "legacy: snakemake_args" from field description
- [x] 4.2 Update `app/models/workflow.py` remove "legacy field name" from snakemake_status description
- [x] 4.3 Search all model files for "snakemake" references in comments/descriptions
- [x] 4.4 Replace Snakemake references with FlowEngine terminology
- [x] 4.5 Update database schema documentation if it exists

## 5. Logging System Updates (High Priority)

- [x] 5.1 Update `app/services/log_handler.py` logger name from "snakemake" to "tdease.engine"
- [x] 5.2 Search for any other hardcoded "snakemake" logger instances
- [x] 5.3 Update logging configuration if needed
- [x] 5.4 Test logging output after changes

## 6. WebSocket Monitoring Updates (High Priority)

- [x] 6.1 Locate `.snakemake/status` file monitoring in `app/core/websocket.py`
- [x] 6.2 Update WebSocket monitor to track FlowEngine status instead
- [x] 6.3 Remove any Snakemake-specific file path references
- [x] 6.4 Test WebSocket status notifications

## 7. Node Mapper Refactoring (High Priority)

- [x] 7.1 Review `app/services/node_mapper.py` for Snakemake rule mapping logic
- [x] 7.2 Identify FlowEngine node equivalents
- [x] 7.3 Update mapper to translate FlowEngine nodes
- [x] 7.4 Remove Snakemake rule references
- [x] 7.5 Update frontend if needed to match new node structure

## 8. Error Handling Standardization (High Priority)

- [x] 8.1 Audit all API files for hardcoded HTTP status codes
- [x] 8.2 Add `from fastapi import status` to files that need it
- [x] 8.3 Replace hardcoded status codes in `app/api/tools.py`
- [x] 8.4 Replace hardcoded status codes in `app/api/files.py`
- [x] 8.5 Replace hardcoded status codes in `app/api/workflows.py`
- [x] 8.6 Replace hardcoded status codes in `app/api/executions.py`
- [x] 8.7 Replace hardcoded status codes in remaining API files
- [x] 8.8 Run tests to verify error responses remain correct

## 9. Import Cleanup (Medium Priority)

- [x] 9.1 Remove unused `StreamingResponse` from `app/api/files.py`
- [x] 9.2 Search for all unused imports across app/ directory
- [x] 9.3 Remove unused imports from each file
- [x] 9.4 Verify application starts without import errors

## 10. Schema Completion (Medium Priority)

- [x] 10.1 Review `app/schemas/workflow.py` requirements
- [x] 10.2 Add necessary Pydantic schemas to workflow.py
- [x] 10.3 Verify schemas match model definitions
- [x] 10.4 Add validation rules as needed

## 11. Configuration Constants (Medium Priority)

- [x] 11.1 Extract `MAX_FILE_SIZE` from `app/api/files.py` to config
- [x] 11.2 Search for other magic numbers in API files
- [x] 11.3 Extract magic numbers to `app/core/config.py`
- [x] 11.4 Update references to use config constants

## 12. Service Review and Cleanup (Medium Priority)

- [x] 12.1 Search for imports of `app/services/cwl_exporter.py`
- [x] 12.2 Search for imports of `app/services/engine_adapter.py`
- [x] 12.3 If unused, document reason and remove files
- [x] 12.4 If used, update documentation and ensure compatibility

## 13. Testing and Verification (All Phases)

- [x] 13.1 Run full test suite after Phase 1 (Critical) changes
- [x] 13.2 Run full test suite after Phase 2 (High Priority) changes
- [x] 13.3 Run full test suite after Phase 3 (Medium Priority) changes
- [x] 13.4 Test database migration rollback
- [x] 13.5 Verify all API endpoints return correct responses
- [x] 13.6 Check logs for any remaining Snakemake references
- [x] 13.7 Run integration tests with staging database

## 14. Documentation Updates (Low Priority)

- [x] 14.1 Update README to reflect FlowEngine architecture
- [x] 14.2 Update API documentation if it references old fields
- [x] 14.3 Update database schema documentation
- [x] 14.4 Document migration process for future deployments
