# Specification: Interactive Node Mapping & State Bus

## Purpose

Define the required behavior for the new "View Node" architecture, which decouples visual mapping from canvas edges and introduces a Semantic State Bus for cross-tool filtering.

## Requirements

### Requirement: Distinct View Node Behavior
The workflow engine and canvas SHALL distinguish Compute Nodes from View (Interactive) Nodes based on their `executionMode`.

#### Scenario: View Node placement on canvas
- **WHEN** a tool with `executionMode: "interactive"` is placed on the canvas
- **THEN** it SHALL only expose input ports of type `data/file` and output ports of type `state/selection`
- **AND** it SHALL NOT expose column-level input ports on the canvas

#### Scenario: Workflow Execution skipping
- **WHEN** the backend workflow engine executes a snapshot
- **THEN** it SHALL automatically skip all nodes with `executionMode: "interactive"`
- **AND** log them as `status: skipped`

### Requirement: In-Panel Schema Data Mapping
Interactive visualization nodes SHALL provide an internal configuration panel for mapping data columns to visual axes.

#### Scenario: Auto-populating the mapping panel
- **WHEN** a user double-clicks an Interactive Node to open its config panel
- **AND** the node is connected to an upstream Compute Node's file output (e.g., `topfd_1[ms1feature]`)
- **THEN** the panel SHALL read the upstream port's `schema` definition (or dynamically fetch the headers if no schema is predefined)
- **AND** it SHALL populate dropdowns for required visual mapping properties (e.g., `X Axis`, `Y Axis`) with the available column names
- **AND** it SHALL pre-select columns if the tool definition specifies a `defaultMapping`

### Requirement: Semantic State Bus Interactivity
Interactive nodes SHALL communicate transient user interaction state (e.g., selections) via a dedicated State Bus without modifying the underlying data files.

#### Scenario: Emitting a selection state
- **WHEN** a user selects a subset of data points in a View Node (e.g., brushing a region in the FeatureMap Viewer)
- **THEN** the node SHALL emit an event to the State Bus with `semanticType: state/selection_ids`
- **AND** the payload SHALL contain the row indices of the selected items

#### Scenario: Receiving a selection state for cross-filtering
- **WHEN** a View Node (e.g., Spectrum Viewer) receives a `state/selection_ids` payload from an incoming State Edge
- **THEN** it SHALL immediately query the `NodeDataAccess API` using these specific row IDs to subset its currently loaded data memory block
- **AND** it SHALL re-render its view to highlight or exclusively show the selected subset

### Requirement: Dynamic HTML Association View
The system SHALL support dynamic HTML fragment loading based on MS1 feature selections to display PRSM/MS2 sequences.

#### Scenario: HTML Viewer associated with Feature Selection
- **WHEN** an `HtmlViewer` interactive node receives both a `data/html` file connection (from TopPIC) AND a `state/selection_ids` connection (from FeatureMap Viewer)
- **AND** the user clicks an MS1 feature point in the FeatureMap Viewer
- **THEN** the `HtmlViewer` SHALL request the specific HTML sub-page corresponding to the emitted feature ID
- **AND** it SHALL render the HTML sequence/spectra view in an iframe or shadow DOM within the node's visual boundary
