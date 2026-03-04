# Workflow Layout Engine

## Purpose

Provides a VSCode-style, multi-panel layout system for the workflow editor. Replaces the manual Resizer implementation with a splitpanes-driven layout and introduces an Activity Bar for navigating primary sidebar panels. Fixes the root cause of canvas zoom/coordinate drift when panels are resized.

## Requirements

### Requirement: Activity Bar navigation
The system SHALL provide a fixed-width (48px) Activity Bar on the far left, containing icon buttons that toggle the Primary Sidebar panels.

#### Scenario: Clicking an active Activity Bar tab collapses the sidebar
- **WHEN** the user clicks an Activity Bar icon that is currently active
- **THEN** the Primary Sidebar SHALL collapse (`activePrimaryTab` set to `null`)

#### Scenario: Clicking an inactive Activity Bar tab opens its panel
- **WHEN** the user clicks an Activity Bar icon that is not currently active
- **THEN** the Primary Sidebar SHALL expand and display the corresponding panel content

#### Scenario: Three Activity Bar tabs available
- **WHEN** the Activity Bar is rendered
- **THEN** it SHALL display icons for: `palette` (Node Toolbox), `files` (File Browser), `visualizations` (Visualization Node List - placeholder)

### Requirement: Splitpanes-based resizable layout
The system SHALL use the `splitpanes` library (or equivalent) to drive horizontal and vertical panel splitting, replacing the manual `document.mousemove` Resizer.

#### Scenario: User drags a vertical divider
- **WHEN** the user drags the vertical divider between the Primary Sidebar and Canvas
- **THEN** the two panes SHALL resize smoothly
- **AND** the Canvas SHALL notify VueFlow of the new dimensions

#### Scenario: User drags the horizontal panel divider
- **WHEN** the user drags the horizontal divider between the Canvas row and the Bottom Panel
- **THEN** the bottom panel height SHALL change
- **AND** splitpanes SHALL store the pane size as a percentage

#### Scenario: Layout state persisted across sessions
- **WHEN** the user resizes any panel and refreshes the page
- **THEN** all panel sizes SHALL be restored from `localStorage` (key prefix: `tdease-workflow.`)

### Requirement: ResizeObserver canvas notification
The system SHALL mount a `ResizeObserver` on the VueFlow container. When the container dimensions change, VueFlow SHALL recalculate its viewport.

#### Scenario: Panel resize triggers VueFlow update
- **WHEN** the canvas container changes size due to panel resizing
- **THEN** VueFlow SHALL call `fitView()` within one animation frame
- **AND** the call SHALL be debounced to at most once per `requestAnimationFrame` cycle

#### Scenario: ResizeObserver cleaned up on unmount
- **WHEN** the VueFlow canvas component is unmounted
- **THEN** the ResizeObserver SHALL be disconnected
