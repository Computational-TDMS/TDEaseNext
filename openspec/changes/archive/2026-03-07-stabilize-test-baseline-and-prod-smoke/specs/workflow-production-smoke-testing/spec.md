## ADDED Requirements

### Requirement: Test discovery SHALL exclude transient runtime directories
Repository-level test collection SHALL ignore transient runtime artifact directories that are not part of committed test sources.

#### Scenario: Deterministic repository collection
- **WHEN** a developer or CI runner executes pytest from the repository root
- **THEN** only configured test paths are collected
- **AND** transient runtime directories are not traversed during collection

### Requirement: Production smoke workflow SHALL validate the real compute chain
The test suite SHALL include a production smoke workflow that validates the real compute execution path using minimal fixtures.

#### Scenario: Smoke chain succeeds with prerequisites
- **WHEN** required executables and minimal fixture data are present
- **THEN** the smoke test executes the minimal workflow path from loader through TopFD and TopPIC
- **AND** the test asserts required output artifacts are generated

### Requirement: Smoke tests SHALL degrade to explicit skip when prerequisites are missing
Smoke tests SHALL not fail general test runs when mandatory environment prerequisites are unavailable.

#### Scenario: Missing prerequisite yields actionable skip
- **WHEN** a required executable or fixture is missing
- **THEN** the smoke test is marked skipped
- **AND** the skip reason explicitly identifies the missing prerequisite
