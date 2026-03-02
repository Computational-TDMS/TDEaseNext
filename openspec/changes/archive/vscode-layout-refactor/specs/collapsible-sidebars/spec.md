## ADDED Requirements

### Requirement: Primary sidebar collapse and expand
The system SHALL provide a primary sidebar (node palette) that can be collapsed and expanded by the user.

#### Scenario: Collapse primary sidebar via button
- **WHEN** user clicks the collapse button in toolbar
- **THEN** primary sidebar width transitions to 0px
- **AND** canvas container expands to fill available space
- **AND** collapse state is persisted

#### Scenario: Expand primary sidebar via button
- **WHEN** user clicks the expand button in toolbar
- **THEN** primary sidebar width transitions to 280px
- **AND** canvas container shrinks to accommodate sidebar
- **AND** expand state is persisted

### Requirement: Secondary sidebar collapse and expand
The system SHALL provide a secondary sidebar (property panel) that can be collapsed and expanded by the user.

#### Scenario: Collapse secondary sidebar via button
- **WHEN** user clicks the collapse button on secondary sidebar header
- **THEN** secondary sidebar width transitions to 0px
- **AND** canvas container expands to fill available space
- **AND** collapse state is persisted

#### Scenario: Expand secondary sidebar via button
- **WHEN** user clicks the expand button in toolbar
- **THEN** secondary sidebar width transitions to 260px
- **AND** canvas container shrinks to accommodate sidebar
- **AND** expand state is persisted

#### Scenario: Auto-collapse secondary sidebar when no node selected
- **WHEN** user deselects all nodes in the canvas
- **THEN** secondary sidebar automatically collapses
- **AND** state is persisted

### Requirement: Smooth collapse animation
The system SHALL animate sidebar collapse and expand transitions smoothly.

#### Scenario: Collapse animation duration
- **WHEN** user triggers sidebar collapse
- **THEN** width transition completes within 200ms
- **AND** transition uses ease timing function

#### Scenario: Expand animation duration
- **WHEN** user triggers sidebar expand
- **THEN** width transition completes within 200ms
- **AND** transition uses ease timing function
