# Interactive Visualization Nodes

## Purpose

Enable users to interactively explore and analyze mass spectrometry data through visualization nodes in the workflow editor. These nodes allow users to visualize, filter, and select data subsets without triggering backend executions, with selection state propagating to downstream nodes for real-time data exploration.

## Requirements

### Requirement: Interactive node registration and rendering
The system SHALL support a distinct `interactive` node type in the VueFlow canvas, rendered by `InteractiveNode.vue` based on the tool's `visualization.type` field.

#### Scenario: Interactive node appears in workflow canvas
- **WHEN** a node's tool definition has `executionMode: "interactive"`
- **THEN** VueFlow SHALL render it using the `InteractiveNode` component (not `ToolNode`)
- **AND** the node SHALL display its `visualization.type` to determine which Viewer component to render

#### Scenario: Interactive node shows loading state
- **WHEN** the node's data is being fetched from the backend
- **THEN** the node SHALL display a loading indicator
- **AND** the node SHALL not render the visualization chart/table until data is ready

#### Scenario: Interactive node shows error state
- **WHEN** data fetching fails or the upstream execution has no data
- **THEN** the node SHALL display an error message with retry option

### Requirement: FeatureMap Viewer node
The system SHALL provide a FeatureMap Viewer node that displays mass spectrometry feature data as a scatter plot (RT vs Mass).

#### Scenario: FeatureMap renders feature data
- **WHEN** the node receives tabular data with RT, Mass (or MassError), and Intensity columns
- **THEN** the system SHALL render a scatter plot with RT on X axis, Mass on Y axis
- **AND** point size or color SHALL encode Intensity

#### Scenario: FeatureMap TopN rendering filter
- **WHEN** the user sets a TopN limit (e.g., 10000)
- **THEN** the system SHALL render only the top N features by Intensity
- **AND** the full dataset SHALL remain in memory (filter is display-only)

#### Scenario: FeatureMap brush selection
- **WHEN** the user draws a rectangular selection on the scatter plot
- **THEN** the system SHALL update the node's selection state with all features inside the bounding box
- **AND** downstream nodes connected to this node SHALL automatically update

#### Scenario: FeatureMap range filter
- **WHEN** the user sets RT range, Mass range, or Intensity range filters
- **THEN** the system SHALL update the selection state to reflect only features within those ranges

### Requirement: Spectrum Viewer node
The system SHALL provide a Spectrum Viewer node that displays mass spectrum data (m/z vs Intensity).

#### Scenario: Spectrum Viewer loads data from connected file
- **WHEN** the node's input is connected to a processing node's output port
- **THEN** the system SHALL load the connected file's data using the P1 node-data-access API
- **AND** render an m/z vs Intensity bar/line chart

#### Scenario: Spectrum Viewer filters by upstream selection
- **WHEN** the node's input is connected to an interactive node's selection state
- **THEN** the system SHALL display only the spectra/entries matching the upstream selection
- **AND** automatically re-render when the upstream selection changes

#### Scenario: Spectrum peak selection
- **WHEN** the user clicks or brush-selects peaks in the spectrum
- **THEN** the system SHALL update the node's selection state with selected peak indices

### Requirement: Table Viewer node
The system SHALL provide a Table Viewer node that displays tabular data using AG Grid.

#### Scenario: Table Viewer renders columns and rows
- **WHEN** the node receives tabular data (columns + rows)
- **THEN** the system SHALL render an AG Grid table with column headers matching the data
- **AND** support sorting and column filtering natively

#### Scenario: Table row selection
- **WHEN** the user clicks or multi-selects rows in the table
- **THEN** the system SHALL update the node's selection state with selected row indices

#### Scenario: Table export
- **WHEN** the user clicks "Export CSV" or "Export Excel"
- **THEN** the system SHALL export the currently visible/filtered data directly from the browser
- **AND** no backend request SHALL be made

#### Scenario: Table column text filter
- **WHEN** the user types in a column filter input
- **THEN** the system SHALL filter rows matching the input text client-side

### Requirement: Interactive tool definitions
The system SHALL include tool definition JSON files for each interactive node type.

#### Scenario: Interactive tool definition structure
- **WHEN** a tool has `executionMode: "interactive"`
- **THEN** the tool definition SHALL include a `visualization` block with `type` (featuremap / spectrum / table)
- **AND** the tool SHALL have `ports.inputs` defining what data types it accepts
- **AND** the tool SHALL have `ports.outputs` with `dataType: "selection"` for downstream state passing

### Requirement: Backend execution skips interactive nodes
The system SHALL skip nodes with `executionMode: "interactive"` during workflow execution.

#### Scenario: Interactive node is skipped during execution
- **WHEN** the workflow engine encounters a node with tool `executionMode: "interactive"`
- **THEN** the engine SHALL skip task generation for that node
- **AND** mark the node's execution status as "skipped"
- **AND** downstream processing nodes SHALL still receive their expected inputs from pre-interactive processing nodes
