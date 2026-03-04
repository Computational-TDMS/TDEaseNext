# Node Data Access

## Purpose

Provides API endpoints for retrieving node output data from workflow executions. This capability enables the frontend to access structured output data for interactive visualization and analysis.

Output file paths are derived dynamically from tool definitions (ports.outputs.pattern) combined with execution context (workflow_snapshot, sample_context), eliminating the need for additional database persistence.

## Requirements

### Requirement: Node output data retrieval
The system SHALL provide an API endpoint to retrieve structured output data for a specific node within an execution, using tool definition patterns to resolve file paths.

#### Scenario: Successful data retrieval for a node with tabular output
- **WHEN** client sends `GET /api/executions/{execution_id}/nodes/{node_id}/data?include_data=true`
- **AND** the execution exists with a valid workflow_snapshot and sample_id
- **AND** the node's tool definition has `ports.outputs` with resolvable patterns
- **AND** the resolved output files exist on disk
- **THEN** the system SHALL return a response with `outputs[]` array, each containing `port_id`, `data_type`, `file_name`, `file_size`, `exists: true`, and `data` with `columns`, `rows`, `total_rows`

#### Scenario: Data retrieval without inline data
- **WHEN** client sends `GET /api/executions/{execution_id}/nodes/{node_id}/data` (without `include_data` or `include_data=false`)
- **THEN** the system SHALL return the same `outputs[]` structure but with `data: null` for all outputs
- **AND** each output SHALL still include `port_id`, `data_type`, `file_name`, `file_size`, `exists`, `parseable`

#### Scenario: Node output file does not exist
- **WHEN** the resolved output path does not exist on disk
- **THEN** the system SHALL return the output entry with `exists: false`, `parseable: false`, `data: null`
- **AND** the response status SHALL still be 200 (partial data is valid)

#### Scenario: Execution not found
- **WHEN** the execution_id does not exist in the database
- **THEN** the system SHALL return HTTP 404

#### Scenario: Node not found in workflow snapshot
- **WHEN** the node_id does not exist in the execution's workflow_snapshot
- **THEN** the system SHALL return HTTP 404

### Requirement: Node output file listing
The system SHALL provide an API endpoint to list output files for a specific node without loading file contents.

#### Scenario: List node output files
- **WHEN** client sends `GET /api/executions/{execution_id}/nodes/{node_id}/files`
- **THEN** the system SHALL return a list of output file metadata including `port_id`, `data_type`, `file_name`, `file_path` (relative to workspace), `file_size`, `exists`

### Requirement: Output path resolution via tool definition
The system SHALL resolve node output file paths by combining `workflow_snapshot`, `tool_registry`, and `sample_context` at query time, without requiring additional database columns.

#### Scenario: Path resolution chain
- **WHEN** resolving output paths for a node
- **THEN** the system SHALL:
  1. Query `executions` table for `workflow_snapshot`, `workspace_path`, `sample_id`
  2. Parse `workflow_snapshot` to find the node's `type` (tool_id)
  3. Query `tool_registry` for `ports.outputs[].pattern`
  4. Query `samples` table for `sample_context` using `sample_id`
  5. Format each pattern with `sample_context` placeholders
  6. Return resolved absolute paths

#### Scenario: Tool has no output patterns
- **WHEN** the node's tool definition has no `ports.outputs` or no patterns
- **THEN** the system SHALL return an empty `outputs[]` array

### Requirement: Tabular file parsing
The system SHALL parse tab-separated and comma-separated text files into structured column/row format.

#### Scenario: Parse TSV file
- **WHEN** parsing a file with extension `.tsv`, `.txt`, `.ms1ft`, or `.feature`
- **THEN** the system SHALL treat the first line as column headers and subsequent lines as data rows, using tab (`\t`) as delimiter

#### Scenario: Parse CSV file
- **WHEN** parsing a file with extension `.csv`
- **THEN** the system SHALL treat the first line as column headers and subsequent lines as data rows, using comma (`,`) as delimiter

#### Scenario: Non-parseable file format
- **WHEN** the file extension is `.pbf`, `.raw`, `.mzml`, `.png`, `.jpg`, `.fasta`, or other binary format
- **THEN** the system SHALL mark the output as `parseable: false` and return `data: null`

### Requirement: Latest execution query
The system SHALL provide an API endpoint to retrieve the most recent successful execution for a given workflow.

#### Scenario: Workflow has completed executions
- **WHEN** client sends `GET /api/workflows/{workflow_id}/latest-execution`
- **AND** the workflow has at least one execution with status "completed"
- **THEN** the system SHALL return the most recent completed execution's metadata (execution_id, status, start_time, end_time, sample_id)

#### Scenario: Workflow has no completed executions
- **WHEN** the workflow has no executions with status "completed"
- **THEN** the system SHALL return HTTP 404

#### Scenario: Workflow not found
- **WHEN** the workflow_id does not exist
- **THEN** the system SHALL return HTTP 404
