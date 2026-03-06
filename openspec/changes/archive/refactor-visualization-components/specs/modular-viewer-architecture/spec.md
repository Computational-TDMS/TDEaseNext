# Spec: Modular Viewer Architecture

## ADDED Requirements

### Requirement: Base viewer component
The system SHALL provide a base ECharts viewer component that encapsulates common viewer functionality.

#### Scenario: Render chart container
- **WHEN** a viewer component extends the base viewer
- **THEN** the base viewer SHALL render a chart container element
- **AND** the container SHALL be properly sized and responsive

#### Scenario: Provide toolbar slot
- **WHEN** a viewer component needs custom toolbar controls
- **THEN** the base viewer SHALL provide a toolbar slot
- **AND** the viewer can inject custom toolbar content
- **AND** the toolbar SHALL be rendered at the top of the viewer

#### Scenario: Provide config panel slot
- **WHEN** a viewer component needs custom configuration panel
- **THEN** the base viewer SHALL provide a config panel slot
- **AND** the viewer can inject custom configuration forms
- **AND** the config panel SHALL be rendered when in edit mode

#### Scenario: Provide selection info slot
- **WHEN** a viewer component needs custom selection display
- **THEN** the base viewer SHALL provide a selection info slot
- **AND** the viewer can inject custom selection information
- **AND** the selection info SHALL be shown when items are selected

### Requirement: Shared viewer functionality
The base viewer SHALL provide common functionality that all viewers can use.

#### Scenario: Fullscreen toggle
- **WHEN** a viewer component needs fullscreen capability
- **THEN** the base viewer SHALL provide fullscreen state and toggle method
- **AND** the viewer can access these via slot props
- **AND** fullscreen toggle SHALL work consistently across all viewers

#### Scenario: Export functionality
- **WHEN** a viewer component needs export capability
- **THEN** the base viewer SHALL provide export functionality
- **AND** the viewer can trigger export via slot props
- **AND** export SHALL work consistently across all viewers

#### Scenario: Chart instance access
- **WHEN** a viewer component needs to access the ECharts instance
- **THEN** the base viewer SHALL expose the chart instance
- **AND** the viewer can access it via defineExpose or ref
- **AND** the instance SHALL be properly typed

### Requirement: Viewer-specific customization
The base viewer SHALL allow viewers to customize behavior while sharing structure.

#### Scenario: Custom chart rendering
- **WHEN** a viewer component needs to render a specific chart type
- **THEN** the viewer SHALL provide a render function or component
- **AND** the base viewer SHALL call this function to render the chart
- **AND** the viewer has full control over chart options

#### Scenario: Custom event handling
- **WHEN** a viewer component needs custom event handlers
- **THEN** the viewer SHALL attach its own event handlers to the chart
- **AND** the base viewer SHALL not interfere with viewer-specific events
- **AND** events SHALL be properly cleaned up on unmount

#### Scenario: Custom configuration
- **WHEN** a viewer component needs viewer-specific configuration
- **THEN** the viewer SHALL define its own configuration interface
- **AND** the base viewer SHALL accept the viewer's config type
- **AND** TypeScript SHALL enforce type safety for the viewer's config

### Requirement: Props and emits interface
The base viewer SHALL define a standard interface for props and emits.

#### Scenario: Standard data prop
- **WHEN** a viewer component receives data
- **THEN** the base viewer SHALL accept a `data` prop of type `TableData | null`
- **AND** the viewer SHALL receive the data via props
- **AND** the data SHALL be reactive

#### Scenario: Standard config prop
- **WHEN** a viewer component receives configuration
- **THEN** the base viewer SHALL accept a `config` prop
- **AND** the config type SHALL be generic to support viewer-specific types
- **AND** the config SHALL be reactive

#### Scenario: Standard emits
- **WHEN** a viewer component needs to emit events
- **THEN** the base viewer SHALL provide standard emits for selectionChange, configChange, and export
- **AND** viewers can emit these events
- **AND** parent components can handle the events

### Requirement: Edit mode support
The base viewer SHALL support edit mode for configuration.

#### Scenario: Show config panel in edit mode
- **WHEN** the edit mode prop is true
- **THEN** the base viewer SHALL display the config panel slot
- **AND** viewers can inject their configuration forms
- **AND** the config panel SHALL be visible

#### Scenario: Hide config panel in view mode
- **WHEN** the edit mode prop is false
- **THEN** the base viewer SHALL NOT display the config panel slot
- **AND** the viewer SHALL be in read-only view mode
- **AND** configuration SHALL NOT be modifiable

### Requirement: Responsive design
The base viewer SHALL be responsive and work on different screen sizes.

#### Scenario: Responsive chart container
- **WHEN** the browser window is resized
- **THEN** the chart container SHALL resize appropriately
- **AND** the chart SHALL maintain proper aspect ratio
- **AND** the chart SHALL not overflow its container

#### Scenario: Responsive toolbar
- **WHEN** the screen width is small (e.g., mobile)
- **THEN** the toolbar SHALL adapt to the small screen
- **AND** toolbar controls SHALL be appropriately sized
- **AND** the toolbar SHALL remain functional

### Requirement: Accessibility
The base viewer SHALL meet basic accessibility standards.

#### Scenario: Keyboard navigation
- **WHEN** a user uses keyboard navigation
- **THEN** the viewer SHALL be keyboard accessible
- **AND** toolbar buttons SHALL be focusable
- **AND** the chart SHALL receive appropriate focus

#### Scenario: Screen reader support
- **WHEN** a screen reader is used
- **THEN** the viewer SHALL provide appropriate ARIA labels
- **AND** chart data SHALL be available in alternative formats
- **AND** toolbar controls SHALL have descriptive labels

### Requirement: Performance optimization
The base viewer SHALL be optimized for performance.

#### Scenario: Efficient re-renders
- **WHEN** data or configuration updates
- **THEN** the viewer SHALL minimize unnecessary re-renders
- **AND** the chart SHALL update efficiently
- **AND** performance SHALL not degrade

#### Scenario: Memory management
- **WHEN** a viewer component unmounts
- **THEN** all resources SHALL be properly disposed
- **AND** no memory leaks SHALL occur
- **AND** the ECharts instance SHALL be destroyed

### Requirement: Type safety
The base viewer SHALL provide full TypeScript type safety.

#### Scenario: Generic config type
- **WHEN** a viewer component extends the base viewer
- **THEN** the base viewer SHALL accept a generic config type parameter
- **AND** TypeScript SHALL enforce the config type for that viewer
- **AND** autocomplete SHALL work for configuration fields

#### Scenario: Type-safe props
- **WHEN** a component uses the base viewer
- **THEN** all props SHALL be properly typed
- **AND** TypeScript SHALL validate prop usage
- **AND** prop defaults SHALL be type-safe
