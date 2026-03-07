# Durable Execution State And Resume

## Purpose

TBD: Describe capability intent and scope.

## Requirements

### Requirement: Execution status APIs SHALL support persistent fallback lookup
Execution status endpoints SHALL return persisted execution data when in-memory runtime state is unavailable.

#### Scenario: Status query after process restart
- **WHEN** an execution id is not present in in-memory runtime registry
- **THEN** the API queries persistent execution storage
- **AND** returns execution and node status data when persisted records exist

### Requirement: Resume policy SHALL require completion evidence for required outputs
A node SHALL be considered resumable only when required completion evidence is present, not merely any output file.

#### Scenario: Partial output does not qualify as completed node
- **WHEN** only non-required or partial outputs exist for a node
- **THEN** resume evaluation marks the node as not completed
- **AND** the node is scheduled for execution

### Requirement: Terminal execution states SHALL remain consistent across memory and storage
The system SHALL reconcile terminal state transitions so API consumers see consistent status after restarts.

#### Scenario: Persisted terminal state is authoritative
- **WHEN** in-memory status is missing or stale and storage shows a terminal state
- **THEN** the API returns the persisted terminal state
- **AND** node statuses align with persisted node records for that execution
