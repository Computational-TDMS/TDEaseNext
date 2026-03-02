## ADDED Requirements

### Requirement: Interactive execution mode type
The Tool Definition Schema SHALL support `executionMode: "interactive"` for nodes that do not execute CLI commands but instead provide data to the frontend for interactive visualization and filtering.

#### Scenario: Interactive node in workflow
- **WHEN** a workflow contains a node with `executionMode: "interactive"`
- **THEN** the FlowEngine SHALL mark the node as "awaiting_interaction" instead of executing a command

#### Scenario: Interactive node skipped in batch mode
- **WHEN** a batch execution encounters an interactive node and no user interaction is available
- **THEN** the system SHALL skip the interactive node and pass through upstream outputs unchanged

### Requirement: Data read API for visualization
The system SHALL provide an API endpoint that reads output files from upstream nodes and returns structured data suitable for frontend visualization (tables, charts, spectra).

#### Scenario: Read upstream TSV output
- **WHEN** an interactive node requests data from its upstream node's TSV output
- **THEN** the API SHALL return the data as JSON with column definitions and row data, supporting pagination and filtering parameters

#### Scenario: Large file handling
- **WHEN** an upstream output file exceeds 100MB
- **THEN** the API SHALL support streaming or paginated access rather than loading the entire file into memory

### Requirement: Filter result writeback
Interactive visualization nodes SHALL support writing filter results back as node output, enabling downstream nodes to consume the filtered dataset.

#### Scenario: User applies filter in visualization node
- **WHEN** a user selects specific rows/proteoforms in the frontend visualization and confirms the selection
- **THEN** the system SHALL write the filtered results to the node's output path, making them available to downstream nodes

#### Scenario: Visualization node output pattern
- **WHEN** a visualization node defines output pattern `{sample}_filtered.tsv`
- **THEN** the filtered data SHALL be written to that resolved path in the workspace

### Requirement: Frontend component type mapping
Interactive tool definitions SHALL include a `visualization` field specifying the frontend component type to render (e.g. `table`, `spectrum`, `chart`, `sequence`).

#### Scenario: Table visualization
- **WHEN** an interactive tool has `visualization.type: "table"` and `visualization.columns: ["protein", "evalue", "mass"]`
- **THEN** the frontend SHALL render an interactive table with those columns, supporting sorting, filtering, and row selection

#### Scenario: Unknown visualization type
- **WHEN** the frontend encounters an unsupported visualization type
- **THEN** it SHALL render a fallback raw-data table view with a warning message
