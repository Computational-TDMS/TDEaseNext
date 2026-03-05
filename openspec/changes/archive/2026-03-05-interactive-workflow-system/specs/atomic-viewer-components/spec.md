## ADDED Requirements

### Requirement: Atomic ScatterPlot widget
The system SHALL provide a reusable ScatterPlot widget that can be configured with arbitrary column mappings.

#### Scenario: ScatterPlot renders with configurable axes
- **WHEN** a node's visualization config specifies `type: "scatter"` with `axisMapping: { x: "RT", y: "Mass", color: "Intensity" }`
- **THEN** the ScatterPlot widget SHALL render data with the specified column mappings
- **AND** axis labels SHALL match the mapped column names

#### Scenario: ScatterPlot brush selection emits state
- **WHEN** the user draws a rectangular brush selection on the scatter plot
- **THEN** the widget SHALL emit a state update with `semanticType: "state/selection_ids"` containing all row indices within the brush region
- **AND** the widget SHALL also emit `semanticType: "state/viewport"` with the brush region coordinates

#### Scenario: ScatterPlot responds to external filter
- **WHEN** the widget receives a `state/selection_ids` via its state-in port
- **THEN** the widget SHALL highlight the selected points with a distinct color
- **AND** non-selected points SHALL be dimmed but still visible

### Requirement: Atomic Spectrum widget
The system SHALL provide a reusable Spectrum widget that renders m/z vs Intensity and supports annotation overlays.

#### Scenario: Spectrum renders peak data
- **WHEN** a node's visualization config specifies `type: "spectrum"`
- **THEN** the widget SHALL render vertical bars for each peak (m/z on X axis, Intensity on Y axis)
- **AND** hovering a peak SHALL show a tooltip with m/z and intensity values

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

### Requirement: Atomic Table widget
The system SHALL provide a reusable Table widget using AG Grid with state port integration.

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

## MODIFIED Requirements

### Requirement: InteractiveNode container upgrade
The existing `InteractiveNode.vue` container SHALL be enhanced to support the atomic widget composition pattern.

#### Scenario: Single widget mode (backward compatible)
- **WHEN** a node's visualization config has only `type` and `config`
- **THEN** the container SHALL render the corresponding single widget (existing behavior)

#### Scenario: Multi-widget composition mode
- **WHEN** a node's visualization config includes a `components` array
- **THEN** the container SHALL render multiple widgets according to their layout declarations
- **AND** widgets within the same node SHALL share the same data context
