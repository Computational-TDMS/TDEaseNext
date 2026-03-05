# Interactive Visualization

## Purpose

Enable users to interactively explore and analyze mass spectrometry data through visualization nodes in the workflow editor. These nodes allow users to visualize, filter, and select data subsets without triggering backend executions, with selection state propagating to downstream nodes for real-time data exploration. The system provides reusable atomic visualization widgets that can be composed into interactive nodes with flexible layouts.

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

### Requirement: InteractiveNode container with widget composition
The `InteractiveNode.vue` container SHALL support both single widget and multi-widget composition patterns.

#### Scenario: Single widget mode (backward compatible)
- **WHEN** a node's visualization config has only `type` and `config`
- **THEN** the container SHALL render the corresponding single widget

#### Scenario: Multi-widget composition mode
- **WHEN** a node's visualization config includes a `components` array
- **THEN** the container SHALL render multiple widgets according to their layout declarations
- **AND** widgets within the same node SHALL share the same data context

### Requirement: FeatureMap Viewer node (ScatterPlot widget)
The system SHALL provide a FeatureMap Viewer node that displays mass spectrometry feature data as a scatter plot (RT vs Mass) using the atomic ScatterPlot widget.

#### Scenario: FeatureMap renders feature data
- **WHEN** a node's visualization config specifies `type: "scatter"` with `axisMapping: { x: "RT", y: "Mass", color: "Intensity" }`
- **THEN** the ScatterPlot widget SHALL render data with the specified column mappings
- **AND** axis labels SHALL match the mapped column names
- **AND** point size or color SHALL encode Intensity

#### Scenario: FeatureMap TopN rendering filter
- **WHEN** the user sets a TopN limit (e.g., 10000)
- **THEN** the system SHALL render only the top N features by Intensity
- **AND** the full dataset SHALL remain in memory (filter is display-only)

#### Scenario: ScatterPlot brush selection emits state
- **WHEN** the user draws a rectangular brush selection on the scatter plot
- **THEN** the widget SHALL emit a state update with `semanticType: "state/selection_ids"` containing all row indices within the brush region
- **AND** the widget SHALL also emit `semanticType: "state/viewport"` with the brush region coordinates
- **AND** downstream nodes connected to this node SHALL automatically update

#### Scenario: ScatterPlot responds to external filter
- **WHEN** the widget receives a `state/selection_ids` via its state-in port
- **THEN** the widget SHALL highlight the selected points with a distinct color
- **AND** non-selected points SHALL be dimmed but still visible

#### Scenario: FeatureMap range filter
- **WHEN** the user sets RT range, Mass range, or Intensity range filters
- **THEN** the system SHALL update the selection state to reflect only features within those ranges

### Requirement: Spectrum Viewer node (Spectrum widget)
The system SHALL provide a Spectrum Viewer node that displays mass spectrum data (m/z vs Intensity) using the atomic Spectrum widget.

#### Scenario: Spectrum renders peak data
- **WHEN** a node's visualization config specifies `type: "spectrum"`
- **THEN** the widget SHALL render vertical bars for each peak (m/z on X axis, Intensity on Y axis)
- **AND** hovering a peak SHALL show a tooltip with m/z and intensity values

#### Scenario: Spectrum Viewer loads data from connected file
- **WHEN** the node's input is connected to a processing node's output port
- **THEN** the system SHALL load the connected file's data using the P1 node-data-access API

#### Scenario: Spectrum applies external selection as filter
- **WHEN** the widget receives `state/selection_ids` via state-in
- **THEN** the widget SHALL display only the peaks corresponding to the selected indices
- **AND** automatically re-render when the upstream selection changes

#### Scenario: Spectrum displays annotation overlay
- **WHEN** the widget receives `state/annotation` data (e.g., from Compute Proxy fragment matching)
- **THEN** the widget SHALL render annotation labels above the corresponding peaks
- **AND** labels SHALL show the annotation type (e.g., "b3", "y5") and color-coded by ion type
- **AND** connecting lines SHALL link the label to the peak it annotates

#### Scenario: Spectrum peak selection emits state
- **WHEN** the user clicks or brush-selects peaks in the spectrum
- **THEN** the widget SHALL emit `state/selection_ids` with selected peak indices

### Requirement: Table Viewer node (Table widget)
The system SHALL provide a Table Viewer node that displays tabular data using AG Grid with the atomic Table widget.

#### Scenario: Table renders with dynamic columns
- **WHEN** a node receives tabular data
- **THEN** the Table widget SHALL auto-detect columns and render them
- **AND** support sorting, column-level filtering, and virtual scrolling

#### Scenario: Table highlights externally selected rows
- **WHEN** the widget receives `state/selection_ids` via state-in
- **THEN** the corresponding rows SHALL be highlighted with a distinct background color
- **AND** the table SHALL scroll to show the first highlighted row

#### Scenario: Table row selection emits state
- **WHEN** the user clicks or multi-selects rows in the table
- **THEN** the widget SHALL emit `state/selection_ids` with selected row indices

#### Scenario: Table export preserves selection
- **WHEN** the user exports data while a selection is active
- **THEN** the export SHALL include only the selected rows (with option to export all)
- **AND** no backend request SHALL be made for export

#### Scenario: Table column text filter
- **WHEN** the user types in a column filter input
- **THEN** the system SHALL filter rows matching the input text client-side

### Requirement: Annotation Overlay component
The system SHALL provide an AnnotationOverlay component that renders labels on top of chart visualizations.

#### Scenario: Overlay receives annotation data
- **WHEN** a `state/annotation` payload is dispatched to a node
- **THEN** the AnnotationOverlay SHALL render labels at the correct chart coordinates
- **AND** labels SHALL be interactive (hoverable for details, clickable for selection)

#### Scenario: Empty annotation overlay
- **WHEN** no annotation data is available
- **THEN** the AnnotationOverlay SHALL render nothing (transparent, no DOM)

### Requirement: FilterNode (pure logic node)
The system SHALL provide a FilterNode that accepts data and filter criteria, outputting filtered data without occupying canvas visual space as a large widget.

#### Scenario: FilterNode applies range filter
- **WHEN** a FilterNode receives `data/table` on data-in and `state/range` on state-in
- **THEN** the node SHALL output a filtered `data/table` on data-out containing only rows matching the range
- **AND** the filtering SHALL happen in real-time as the upstream range changes

#### Scenario: FilterNode applies selection filter
- **WHEN** a FilterNode receives `data/table` on data-in and `state/selection_ids` on state-in
- **THEN** the node SHALL output a `data/table` containing only the selected rows

#### Scenario: FilterNode visual representation
- **WHEN** a FilterNode is placed on the canvas
- **THEN** it SHALL render as a compact node (small icon + label, no chart area)
- **AND** display active filter count as a badge

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
