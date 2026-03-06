# Spec: Node Component Modularization

## ADDED Requirements

### Requirement: Node header component
The system SHALL provide a dedicated NodeHeader component for rendering node title and actions.

#### Scenario: Render node title
- **WHEN** a node is rendered
- **THEN** the NodeHeader SHALL display the node label
- **AND** the header SHALL show an appropriate icon based on node state
- **AND** the header SHALL display the visualization type tag if present

#### Scenario: Render node state icon
- **WHEN** a node is in loading state
- **THEN** the header SHALL display a loading icon
- **AND** the icon SHALL be animated

#### Scenario: Render node error state
- **WHEN** a node has an error
- **THEN** the header SHALL display an error icon
- **AND** the icon SHALL be visually distinct

#### Scenario: Render node actions
- **WHEN** a node is rendered
- **THEN** the header SHALL display action buttons
- **AND** the header SHALL include edit mode toggle button
- **AND** the header SHALL include retry button if there's an error
- **AND** the header SHALL include fullscreen toggle button

#### Scenario: Emit action events
- **WHEN** a user clicks a header action button
- **THEN** the NodeHeader SHALL emit the corresponding event
- **AND** the parent component SHALL handle the event
- **AND** the event payload SHALL include necessary data

### Requirement: Node configuration panel component
The system SHALL provide a dedicated NodeConfigPanel component for rendering node configuration.

#### Scenario: Render configuration tabs
- **WHEN** a node is in edit mode
- **THEN** the NodeConfigPanel SHALL display configuration tabs
- **AND** the panel SHALL include Data Mapping tab
- **AND** the panel SHALL include Appearance tab
- **AND** the panel SHALL include Export tab

#### Scenario: Render column mapping configuration
- **WHEN** the Data Mapping tab is active
- **THEN** the panel SHALL display column mapping controls
- **AND** the controls SHALL be appropriate for the visualization type
- **AND** the panel SHALL use ColumnConfigPanel for applicable types
- **AND** the panel SHALL show custom config for special types (heatmap, volcano)

#### Scenario: Render appearance configuration
- **WHEN** the Appearance tab is active
- **THEN** the panel SHALL display appearance controls
- **AND** the panel SHALL use ColorSchemeConfig for applicable types
- **AND** the panel SHALL show a message for unsupported types

#### Scenario: Render export configuration
- **WHEN** the Export tab is active
- **THEN** the panel SHALL display export controls
- **AND** the panel SHALL use VisualizationExport component
- **AND** the panel SHALL pass appropriate props for export

#### Scenario: Emit configuration changes
- **WHEN** a user modifies configuration
- **THEN** the NodeConfigPanel SHALL emit a config change event
- **AND** the event SHALL contain the new configuration
- **AND** the parent component SHALL handle the configuration update

### Requirement: Node state manager composable
The system SHALL provide a composable for managing node state logic.

#### Scenario: Manage node state
- **WHEN** a component uses useNodeStateManager
- **THEN** the composable SHALL provide node state (idle, loading, error, ready)
- **AND** the state SHALL update reactively
- **AND** the state SHALL be computed from data source status

#### Scenario: Manage error state
- **WHEN** a data source has an error
- **THEN** the composable SHALL set error state
- **AND** the composable SHALL provide error message
- **AND** the composable SHALL provide retry function

#### Scenario: Manage loading state
- **WHEN** a data source is loading
- **THEN** the composable SHALL set loading state
- **AND** the composable SHALL show loading indicator
- **AND** the composable SHALL hide content during loading

#### Scenario: Manage edit mode
- **WHEN** a user toggles edit mode
- **THEN** the composable SHALL update edit mode state
- **AND** the composable SHALL provide toggle function
- **AND** the composable SHALL emit edit mode change event

### Requirement: InteractiveNode orchestration
The refactored InteractiveNode component SHALL orchestrate child components and manage node-level concerns.

#### Scenario: Compose node from components
- **WHEN** InteractiveNode renders
- **THEN** it SHALL use NodeHeader for header
- **AND** it SHALL use NodeConfigPanel for configuration
- **AND** it SHALL use useNodeStateManager for state
- **AND** it SHALL dynamically load the appropriate viewer component

#### Scenario: Manage data flow
- **WHEN** data flows from upstream to the node
- **THEN** InteractiveNode SHALL receive data via props
- **AND** it SHALL process the data for the viewer
- **AND** it SHALL pass processed data to the viewer
- **AND** it SHALL handle data transformation errors

#### Scenario: Handle viewer events
- **WHEN** a viewer emits events (selection, config change)
- **THEN** InteractiveNode SHALL handle the events
- **AND** it SHALL forward events to parent workflow
- **AND** it SHALL update node state as needed

#### Scenario: Manage viewer lifecycle
- **WHEN** the node mounts or unmounts
- **THEN** InteractiveNode SHALL manage viewer lifecycle
- **AND** it SHALL clean up resources on unmount
- **AND** it SHALL preserve viewer state when possible

### Requirement: Component size reduction
The refactored components SHALL be significantly smaller than the original monolithic component.

#### Scenario: NodeHeader component size
- **WHEN** NodeHeader is implemented
- **THEN** the component SHALL be approximately 100-150 lines
- **AND** the component SHALL have single responsibility (header display and actions)
- **AND** the component SHALL be independently testable

#### Scenario: NodeConfigPanel component size
- **WHEN** NodeConfigPanel is implemented
- **THEN** the component SHALL be approximately 200-250 lines
- **AND** the component SHALL have single responsibility (configuration UI)
- **AND** the component SHALL be independently testable

#### Scenario: InteractiveNode component size
- **WHEN** InteractiveNode is refactored
- **THEN** the component SHALL be approximately 250-300 lines (down from 874)
- **AND** the component SHALL focus on orchestration
- **AND** the component SHALL delegate to child components

### Requirement: Props and emits interface
The refactored components SHALL maintain the same external interface as the original.

#### Scenario: Maintain original props
- **WHEN** InteractiveNode is used
- **THEN** it SHALL accept the same props as before
- **AND** all existing prop usages SHALL continue to work
- **AND** TypeScript types SHALL be compatible

#### Scenario: Maintain original emits
- **WHEN** InteractiveNode emits events
- **THEN** it SHALL emit the same events as before
- **AND** all existing event handlers SHALL continue to work
- **AND** event payloads SHALL be compatible

#### Scenario: Maintain original slots
- **WHEN** InteractiveNode is used with slots
- **THEN** it SHALL support the same slots as before
- **AND** all existing slot usages SHALL continue to work

### Requirement: Independent component testing
Each refactored component SHALL be independently testable.

#### Scenario: Test NodeHeader in isolation
- **WHEN** testing NodeHeader
- **THEN** the component SHALL be testable without InteractiveNode
- **AND** the component SHALL accept mock props for testing
- **AND** the component SHALL emit events for test verification

#### Scenario: Test NodeConfigPanel in isolation
- **WHEN** testing NodeConfigPanel
- **THEN** the component SHALL be testable without InteractiveNode
- **AND** the component SHALL accept mock props for testing
- **AND** the component SHALL emit config changes for test verification

#### Scenario: Test useNodeStateManager in isolation
- **WHEN** testing useNodeStateManager
- **THEN** the composable SHALL be testable without components
- **AND** the composable SHALL accept mock data sources
- **AND** the composable SHALL provide reactive state for testing

### Requirement: Visual and functional parity
The refactored components SHALL maintain visual and functional parity with the original.

#### Scenario: Visual appearance
- **WHEN** the refactored node renders
- **THEN** it SHALL appear identical to the original node
- **AND** spacing SHALL be consistent
- **AND** colors SHALL be consistent
- **AND** layout SHALL be consistent

#### Scenario: User interactions
- **WHEN** a user interacts with the refactored node
- **THEN** all interactions SHALL work identically to the original
- **AND** edit mode toggle SHALL work
- **AND** configuration changes SHALL work
- **AND** export SHALL work
- **AND** fullscreen SHALL work

#### Scenario: Data flow
- **WHEN** data flows through the refactored node
- **THEN** data flow SHALL be identical to the original
- **AND** upstream selection SHALL be respected
- **AND** node output SHALL be correct
- **AND** error handling SHALL work

### Requirement: Backward compatibility
The refactored components SHALL be backward compatible with existing code.

#### Scenario: Drop-in replacement
- **WHEN** the refactored InteractiveNode replaces the original
- **THEN** all existing code SHALL work without modification
- **AND** all parent components SHALL continue to function
- **AND** no breaking changes SHALL be introduced

#### Scenario: Configuration compatibility
- **WHEN** existing node configurations are used
- **THEN** the refactored components SHALL accept the configurations
- **AND** configuration formats SHALL be compatible
- **AND** default values SHALL match original behavior
