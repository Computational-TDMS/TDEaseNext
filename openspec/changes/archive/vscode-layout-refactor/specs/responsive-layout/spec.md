## ADDED Requirements

### Requirement: Responsive breakpoints for sidebar auto-collapse
The system SHALL automatically collapse sidebars based on viewport width breakpoints.

#### Scenario: Collapse secondary sidebar at 1024px breakpoint
- **WHEN** viewport width is less than 1024px
- **THEN** secondary sidebar is collapsed by default
- **AND** primary sidebar remains expanded

#### Scenario: Collapse primary sidebar at 768px breakpoint
- **WHEN** viewport width is less than 768px
- **THEN** primary sidebar is collapsed by default
- **AND** secondary sidebar is also collapsed

#### Scenario: Restore expanded state above breakpoint
- **WHEN** viewport width increases above 1024px
- **THEN** previously expanded sidebars are restored
- **AND** persisted state is respected

### Requirement: Canvas minimum width preservation
The system SHALL ensure canvas container maintains minimum usable width across all viewport sizes.

#### Scenario: Canvas minimum width enforcement
- **WHEN** viewport width is less than sum of sidebar widths
- **THEN** canvas container maintains minimum width of 300px
- **AND** overflow is handled by workspace container

### Requirement: User manual override priority
The system SHALL prioritize user manual expand/collapse actions over automatic breakpoint behavior.

#### Scenario: Manual expand overrides breakpoint default
- **WHEN** user manually expands secondary sidebar below 1024px
- **THEN** sidebar remains expanded
- **AND** state is persisted
- **AND** subsequent page loads respect user preference

#### Scenario: Manual collapse persists above breakpoint
- **WHEN** user manually collapses sidebar above breakpoint
- **THEN** sidebar remains collapsed
- **AND** state is persisted

### Requirement: Breakpoint-aware layout initialization
The system SHALL initialize layout state based on current viewport width on page load.

#### Scenario: Initial load below 1024px
- **WHEN** page loads at viewport width 800px
- **THEN** secondary sidebar is collapsed
- **AND** primary sidebar is expanded

#### Scenario: Initial load below 768px
- **WHEN** page loads at viewport width 600px
- **THEN** both primary and secondary sidebars are collapsed
- **AND** toolbar expand buttons are available

### Requirement: Smooth layout transitions on viewport resize
The system SHALL smoothly adjust layout when viewport crosses breakpoints.

#### Scenario: Viewport resize from 1100px to 900px
- **WHEN** user resizes viewport from 1100px to 900px
- **THEN** secondary sidebar collapses with animation
- **AND** canvas expands smoothly

#### Scenario: Viewport resize from 700px to 1200px
- **WHEN** user resizes viewport from 700px to 1200px
- **THEN** sidebars restore to previously expanded state
- **AND** layout adjusts smoothly
