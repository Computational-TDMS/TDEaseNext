## ADDED Requirements

### Requirement: Sidebar width resize via drag handle
The system SHALL allow users to resize sidebar widths by dragging a resize handle between sidebar and canvas.

#### Scenario: Drag primary sidebar resize handle
- **WHEN** user drags the resize handle between primary sidebar and canvas
- **THEN** primary sidebar width updates in real-time during drag
- **AND** canvas container adjusts accordingly
- **AND** new width is persisted after drag ends

#### Scenario: Drag secondary sidebar resize handle
- **WHEN** user drags the resize handle between canvas and secondary sidebar
- **THEN** secondary sidebar width updates in real-time during drag
- **AND** canvas container adjusts accordingly
- **AND** new width is persisted after drag ends

### Requirement: Sidebar width constraints
The system SHALL enforce minimum and maximum width constraints on sidebar resize.

#### Scenario: Minimum width constraint
- **WHEN** user drags sidebar below minimum width (200px)
- **THEN** sidebar width stops at 200px
- **AND** visual feedback indicates minimum limit reached

#### Scenario: Maximum width constraint
- **WHEN** user drags sidebar above maximum width (500px)
- **THEN** sidebar width stops at 500px
- **AND** visual feedback indicates maximum limit reached

### Requirement: Bottom panel height resize via drag handle
The system SHALL allow users to resize the bottom panel height by dragging a resize handle at the top of the panel.

#### Scenario: Drag bottom panel resize handle
- **WHEN** user drags the resize handle at top of bottom panel
- **THEN** panel height updates in real-time during drag
- **AND** editor-row container height adjusts accordingly
- **AND** new height is persisted after drag ends

### Requirement: Bottom panel height constraints
The system SHALL enforce minimum and maximum height constraints on bottom panel resize.

#### Scenario: Minimum height constraint
- **WHEN** user drags bottom panel below minimum height (150px)
- **THEN** panel height stops at 150px
- **AND** visual feedback indicates minimum limit reached

#### Scenario: Maximum height constraint
- **WHEN** user drags bottom panel above maximum height (60% of viewport)
- **THEN** panel height stops at 60% of viewport
- **AND** visual feedback indicates maximum limit reached

### Requirement: Resize handle visibility
The system SHALL show resize handles only when the corresponding panel is expanded.

#### Scenario: Hide resize handle when collapsed
- **WHEN** sidebar or panel is collapsed
- **THEN** corresponding resize handle is hidden
- **AND** cursor does not change to resize indicator

#### Scenario: Show resize handle when expanded
- **WHEN** sidebar or panel is expanded
- **THEN** corresponding resize handle is visible
- **AND** cursor changes to resize indicator on hover
