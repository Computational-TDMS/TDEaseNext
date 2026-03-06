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
The system SHALL parse tab-separated and comma-separated text files into structured column/row format, including TSV files that contain non-tabular preamble blocks.

#### Scenario: Parse standard TSV file
- **WHEN** parsing a file with extension `.tsv`, `.txt`, `.ms1ft`, or `.feature` and the first non-empty line is a tabular header
- **THEN** the system SHALL use that header line as columns and parse subsequent tab-separated lines as data rows

#### Scenario: Parse TopPIC TSV with parameter preamble
- **WHEN** parsing a `.tsv` file whose leading lines are parameter banners or key-value metadata before the true tabular header
- **THEN** the system SHALL skip the preamble and detect the first valid tabular header line
- **AND** parse all following tab-separated records under that detected header

#### Scenario: TSV header cannot be detected
- **WHEN** parsing a TSV-like file where no valid tabular header can be detected after preamble skipping
- **THEN** the system SHALL mark the output as `parseable: false`
- **AND** return `data: null` without failing the entire node data response

#### Scenario: Parse CSV file
- **WHEN** parsing a file with extension `.csv`
- **THEN** the system SHALL treat the first line as column headers and subsequent lines as data rows, using comma (`,`) as delimiter

#### Scenario: Non-parseable file format
- **WHEN** the file extension is `.pbf`, `.raw`, `.mzml`, `.png`, `.jpg`, `.fasta`, or other binary format
- **THEN** the system SHALL mark the output as `parseable: false` and return `data: null`

### Requirement: TopMSV PrSM table interaction
The system SHALL support a PrSM-centric table interaction mode where selections are propagated using stable PrSM identifiers.

#### Scenario: PrSM table emits stable selection IDs
- **WHEN** a user selects one or more rows in the PrSM table viewer
- **THEN** the node SHALL dispatch `state/selection_ids` using `Prsm ID` values from the selected rows

#### Scenario: PrSM table handles external selection
- **WHEN** the PrSM table receives `state/selection_ids` from another TopMSV node
- **THEN** it SHALL highlight rows whose `Prsm ID` values match the incoming IDs

### Requirement: TopMSV selection semantic reuse
The TopMSV branch SHALL reuse `state/selection_ids` as the selection semantic type and SHALL NOT introduce a new semantic type for PrSM IDs in this change.

#### Scenario: TopMSV state port semantic type
- **WHEN** TopMSV table, MS2 viewer, and sequence viewer ports are defined
- **THEN** their selection state ports SHALL use `semanticType: "state/selection_ids"`

### Requirement: TopMSV MS2 viewer node
The system SHALL provide a dedicated interactive node type for visualizing MS2 spectra from `prsm_bundle.tsv`.

#### Scenario: MS2 viewer renders selected PrSM spectrum
- **WHEN** `topmsv_ms2_viewer` receives a `state/selection_ids` payload with a single `Prsm ID`
- **THEN** it SHALL locate the corresponding row in `prsm_bundle.tsv` and render its MS2 peaks

#### Scenario: MS2 viewer updates on selection change
- **WHEN** the upstream PrSM selection changes
- **THEN** the MS2 viewer SHALL re-render synchronously with the newly selected PrSM data

#### Scenario: MS2 viewer missing mapping fallback
- **WHEN** the selected row has `mapping_status` indicating missing spectrum mapping
- **THEN** the viewer SHALL show a non-blocking empty-state message instead of throwing runtime errors

### Requirement: TopMSV sequence viewer node
The system SHALL provide a dedicated interactive node type for sequence visualization from `prsm_bundle.tsv`.

#### Scenario: Sequence viewer renders proteoform sequence
- **WHEN** `topmsv_sequence_viewer` receives a selected `Prsm ID`
- **THEN** it SHALL display the corresponding sequence and modification annotations

#### Scenario: Sequence viewer synchronized with MS2 viewer
- **WHEN** table selection changes
- **THEN** sequence and MS2 viewers SHALL display data from the same `Prsm ID` in the same reactivity cycle

#### Scenario: Sequence viewer read-only mode in v1
- **WHEN** a user inspects sequence content in `topmsv_sequence_viewer`
- **THEN** the viewer SHALL provide read-only sequence and modification rendering
- **AND** it SHALL NOT provide sequence editing or compute-proxy recalculation actions in this change

### Requirement: TopMSV state connections use state channel semantics
Selection propagation in the TopMSV branch SHALL use state connections, not data connections.

#### Scenario: Workflow edge kind for selection links
- **WHEN** `wf_test_full.json` defines selection links from PrSM table to TopMSV viewers
- **THEN** those edges SHALL use `connectionKind: "state"` and connect `state-out` to `state-in` ports only

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
