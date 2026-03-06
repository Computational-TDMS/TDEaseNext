# Spec: ECharts Abstraction

## ADDED Requirements

### Requirement: ECharts lifecycle management
The system SHALL provide a composable function that manages the complete lifecycle of ECharts instances including initialization, option updates, resize handling, and disposal.

#### Scenario: Initialize ECharts on mount
- **WHEN** a component mounts and provides a container DOM element
- **THEN** the system SHALL initialize an ECharts instance attached to that container
- **AND** the instance SHALL be ready to receive chart options

#### Scenario: Automatic disposal on unmount
- **WHEN** a component unmounts
- **THEN** the system SHALL automatically dispose of the ECharts instance
- **AND** all event listeners SHALL be removed
- **AND** memory SHALL be freed

#### Scenario: Update chart options
- **WHEN** chart data or configuration changes
- **THEN** the system SHALL update the ECharts instance with new options
- **AND** the chart SHALL re-render with the new data

#### Scenario: Responsive resize handling
- **WHEN** the browser window is resized
- **THEN** the system SHALL automatically resize the ECharts instance
- **AND** the chart SHALL maintain proper aspect ratio and clarity

### Requirement: Event handling abstraction
The system SHALL provide a unified API for attaching and detaching ECharts event listeners.

#### Scenario: Attach brush event listener
- **WHEN** a component needs to handle brush selection events
- **THEN** the system SHALL provide a method to attach a brush event handler
- **AND** the handler SHALL receive brush selection coordinates

#### Scenario: Attach click event listener
- **WHEN** a component needs to handle click events on chart elements
- **THEN** the system SHALL provide a method to attach a click event handler
- **AND** the handler SHALL receive the clicked element data

#### Scenario: Automatic event cleanup
- **WHEN** a component unmounts
- **THEN** all attached event listeners SHALL be automatically removed
- **AND** no memory leaks SHALL occur from dangling listeners

### Requirement: Theme support
The system SHALL support ECharts theme initialization with consistent theming across all chart instances.

#### Scenario: Initialize with default theme
- **WHEN** a chart is initialized without specifying a theme
- **THEN** the system SHALL use the default ECharts theme
- **AND** the chart SHALL render with standard styling

#### Scenario: Initialize with custom theme
- **WHEN** a chart is initialized with a specific theme name
- **THEN** the system SHALL initialize the chart with that theme
- **AND** the chart SHALL render with the specified theme's colors and styles

### Requirement: Type safety
The system SHALL provide TypeScript types for all ECharts-related functionality.

#### Scenario: Type-safe chart instance access
- **WHEN** a component accesses the ECharts instance
- **THEN** the type SHALL be `echarts.ECharts | null`
- **AND** TypeScript SHALL enforce proper type checking

#### Scenario: Type-safe option updates
- **WHEN** a component updates chart options
- **THEN** the option type SHALL be `EChartsOption`
- **AND** TypeScript SHALL validate the option structure

### Requirement: Error handling
The system SHALL handle ECharts initialization and runtime errors gracefully.

#### Scenario: Handle missing container
- **WHEN** initialization is attempted but the container element is not available
- **THEN** the system SHALL not throw an error
- **AND** the chart instance SHALL remain null
- **AND** a warning SHALL be logged

#### Scenario: Handle invalid options
- **WHEN** invalid chart options are provided
- **THEN** the system SHALL catch the error from ECharts
- **AND** the error SHALL be logged for debugging
- **AND** the chart SHALL remain in its previous valid state
