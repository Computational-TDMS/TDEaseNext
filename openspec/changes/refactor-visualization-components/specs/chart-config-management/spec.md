# Spec: Chart Config Management

## ADDED Requirements

### Requirement: Centralized configuration types
The system SHALL provide centralized TypeScript types for all chart configurations.

#### Scenario: Scatter plot configuration type
- **WHEN** a component defines scatter plot configuration
- **THEN** the system SHALL provide a `ScatterConfig` type
- **AND** the type SHALL include x-axis column, y-axis column, color scheme, and point size
- **AND** TypeScript SHALL enforce type safety

#### Scenario: Heatmap configuration type
- **WHEN** a component defines heatmap configuration
- **THEN** the system SHALL provide a `HeatmapConfig` type
- **AND** the type SHALL include row column, column column, value column, and color scheme
- **AND** TypeScript SHALL enforce type safety

#### Scenario: Volcano plot configuration type
- **WHEN** a component defines volcano plot configuration
- **THEN** the system SHALL provide a `VolcanoConfig` type
- **AND** the type SHALL include fold change column, p-value column, name column, and thresholds
- **AND** TypeScript SHALL enforce type safety

#### Scenario: Spectrum configuration type
- **WHEN** a component defines spectrum configuration
- **THEN** the system SHALL provide a `SpectrumConfig` type
- **AND** the type SHALL include m/z column, intensity column, peak threshold, and normalization flag
- **AND** TypeScript SHALL enforce type safety

### Requirement: Configuration validation
The system SHALL validate configuration objects before they are applied to charts.

#### Scenario: Validate required fields
- **WHEN** a configuration object is created
- **THEN** the system SHALL validate that all required fields are present
- **AND** validation SHALL fail if required fields are missing
- **AND** appropriate error messages SHALL be displayed

#### Scenario: Validate column references
- **WHEN** a configuration references data columns
- **THEN** the system SHALL validate that the referenced columns exist in the data
- **AND** validation SHALL fail if columns are not found
- **AND** the error message SHALL indicate which columns are invalid

#### Scenario: Validate numeric ranges
- **WHEN** a configuration includes numeric parameters (e.g., thresholds)
- **THEN** the system SHALL validate that values are within acceptable ranges
- **AND** validation SHALL fail if values are out of range
- **AND** the error message SHALL indicate the valid range

### Requirement: Configuration defaults
The system SHALL provide sensible default values for all optional configuration fields.

#### Scenario: Default color scheme
- **WHEN** a configuration does not specify a color scheme
- **THEN** the system SHALL apply a default color scheme
- **AND** the default SHALL be visually appealing and accessible

#### Scenario: Default point size
- **WHEN** a scatter plot configuration does not specify point size
- **THEN** the system SHALL apply a default point size
- **AND** the default SHALL be appropriate for most data densities

#### Scenario: Default thresholds
- **WHEN** a volcano plot configuration does not specify thresholds
- **THEN** the system SHALL apply scientifically reasonable defaults
- **AND** the defaults SHALL be commonly used values (e.g., FC=2, p=0.05)

### Requirement: Configuration merging
The system SHALL support merging user configuration with default configuration.

#### Scenario: Merge with defaults
- **WHEN** a user provides partial configuration
- **THEN** the system SHALL merge user values with default values
- **AND** user values SHALL take precedence
- **AND** missing values SHALL be filled from defaults

#### Scenario: Merge with previous config
- **WHEN** a user updates existing configuration
- **THEN** the system SHALL merge new values with previous values
- **AND** only changed values SHALL be updated
- **AND** unchanged values SHALL be preserved

### Requirement: Configuration persistence
The system SHALL persist configuration changes and make them available to other components.

#### Scenario: Emit config change event
- **WHEN** a user modifies configuration
- **THEN** the system SHALL emit a configuration change event
- **AND** the event SHALL contain the full new configuration
- **AND** parent components SHALL be able to save the configuration

#### Scenario: Apply configuration from props
- **WHEN** a component receives configuration via props
- **THEN** the system SHALL apply the prop configuration
- **AND** local configuration SHALL be initialized from props
- **AND** changes SHALL emit events to update parent

### Requirement: Configuration reset
The system SHALL provide a method to reset configuration to defaults.

#### Scenario: Reset to defaults
- **WHEN** a user triggers a reset action
- **THEN** the system SHALL reset all configuration values to defaults
- **AND** the chart SHALL update to reflect default configuration
- **AND** a config change event SHALL be emitted

#### Scenario: Reset specific field
- **WHEN** a user resets a specific configuration field
- **THEN** the system SHALL reset only that field to its default value
- **AND** other fields SHALL remain unchanged

### Requirement: Type-safe configuration API
The system SHALL provide a type-safe API for configuration management.

#### Scenario: Type-safe config access
- **WHEN** a component accesses configuration
- **THEN** the configuration type SHALL be specific to the chart type
- **AND** TypeScript SHALL enforce proper field access

#### Scenario: Type-safe config updates
- **WHEN** a component updates configuration
- **THEN** the update method SHALL accept only valid configuration fields
- **AND** TypeScript SHALL validate the update object

### Requirement: Configuration validation UI feedback
The system SHALL provide visual feedback for configuration validation errors.

#### Scenario: Display validation errors
- **WHEN** configuration validation fails
- **THEN** the system SHALL display error messages inline with the configuration form
- **AND** the error messages SHALL clearly indicate what needs to be fixed

#### Scenario: Disable invalid configurations
- **WHEN** configuration has validation errors
- **THEN** the system SHALL disable the apply/save button
- **AND** the button SHALL be enabled only when configuration is valid
