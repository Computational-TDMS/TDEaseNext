# Environment Agnostic Tool Configuration

## Purpose

TBD: Describe capability intent and scope.

## Requirements

### Requirement: Shared tool configuration SHALL be environment-agnostic
Version-controlled tool definitions SHALL avoid machine-specific absolute executable paths and rely on profile-resolved configuration.

#### Scenario: Shared config passes portability validation
- **WHEN** tool definitions are loaded from repository-managed config
- **THEN** non-portable absolute-path patterns are rejected by validation
- **AND** configuration loading reports actionable migration guidance

### Requirement: Tool resolution SHALL support profile-based overrides
Tool executable resolution SHALL support environment profiles with deterministic precedence.

#### Scenario: Profile override selects environment-specific executable
- **WHEN** an environment profile override provides a tool executable path
- **THEN** the resolved executable uses profile override precedence
- **AND** fallback behavior is deterministic when override is absent

### Requirement: Active execution path SHALL not depend on deprecated legacy registries
The active workflow execution stack SHALL use one authoritative tool registry path and not require deprecated duplicates.

#### Scenario: FlowEngine execution resolves tools without legacy registry coupling
- **WHEN** workflow execution starts through the active service stack
- **THEN** tool lookup succeeds via the authoritative registry path
- **AND** deprecated legacy registry modules are not required for execution
