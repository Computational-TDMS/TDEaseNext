## ADDED Requirements

### Requirement: Sidebar collapse state persistence
The system SHALL persist sidebar collapse/expand state to localStorage.

#### Scenario: Save primary sidebar state
- **WHEN** user toggles primary sidebar visibility
- **THEN** new state is saved to localStorage with key `workflow.primarySidebarVisible`
- **AND** save happens within 100ms of state change

#### Scenario: Save secondary sidebar state
- **WHEN** user toggles secondary sidebar visibility
- **THEN** new state is saved to localStorage with key `workflow.secondarySidebarVisible`
- **AND** save happens within 100ms of state change

#### Scenario: Load sidebar states on page load
- **WHEN** user navigates to workflow page
- **THEN** sidebar states are loaded from localStorage
- **AND** sidebars are initialized to saved states

### Requirement: Panel size persistence
The system SHALL persist resized panel dimensions to localStorage.

#### Scenario: Save primary sidebar width
- **WHEN** user finishes dragging primary sidebar resize handle
- **THEN** new width is saved to localStorage with key `workflow.primarySidebarWidth`
- **AND** save happens within 100ms of drag end

#### Scenario: Save secondary sidebar width
- **WHEN** user finishes dragging secondary sidebar resize handle
- **THEN** new width is saved to localStorage with key `workflow.secondarySidebarWidth`
- **AND** save happens within 100ms of drag end

#### Scenario: Save bottom panel height
- **WHEN** user finishes dragging bottom panel resize handle
- **THEN** new height is saved to localStorage with key `workflow.panelHeight`
- **AND** save happens within 100ms of drag end

#### Scenario: Load panel sizes on page load
- **WHEN** user navigates to workflow page
- **THEN** panel sizes are loaded from localStorage
- **AND** panels are initialized to saved dimensions

### Requirement: Graceful handling of storage failures
The system SHALL handle localStorage unavailability gracefully.

#### Scenario: Private mode or storage quota exceeded
- **WHEN** localStorage save fails (private mode, quota exceeded)
- **THEN** system continues with in-memory state
- **AND** no error is shown to user
- **AND** functionality remains intact for current session

#### Scenario: Load from corrupted storage
- **WHEN** localStorage contains invalid data for layout keys
- **THEN** system falls back to default layout values
- **AND** no error is shown to user
- **AND** default values are used

### Requirement: Storage key namespacing
The system SHALL use namespaced keys to avoid conflicts with other applications.

#### Scenario: Key namespace prefix
- **WHEN** saving layout state
- **THEN** all keys use `tdease-workflow.` prefix
- **AND** full key format is `tdease-workflow.{stateName}`

### Requirement: Layout reset capability
The system SHALL provide a method to reset layout to default values.

#### Scenario: Clear layout state
- **WHEN** user invokes layout reset (optional feature)
- **THEN** all layout-related localStorage keys are removed
- **AND** layout reverts to default values
- **AND** page reflects reset layout immediately
