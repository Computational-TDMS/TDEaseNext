# Input Binding Contract Validation

## Purpose

TBD: Describe capability intent and scope.

## Requirements

### Requirement: Required input ports SHALL be validated before command execution
For each compute node, the system SHALL validate that all required input ports are bound before command assembly starts.

#### Scenario: Missing required input fails node early
- **WHEN** a target tool declares a required input port and no upstream output is bound to that port
- **THEN** the node is marked failed before command execution
- **AND** the error identifies the missing port id

### Requirement: Ambiguous required bindings SHALL fail deterministically
The system SHALL reject ambiguous bindings for required single-input ports instead of silently selecting one candidate.

#### Scenario: Multiple candidates for single required port
- **WHEN** multiple upstream candidates match a required single-input port
- **THEN** the node fails with an ambiguity error
- **AND** the error includes candidate edge identifiers and selection scores

### Requirement: Binding diagnostics SHALL be queryable from execution traces
Binding decisions SHALL be persisted as structured diagnostics for API retrieval and test assertions.

#### Scenario: Decision trace includes accepted and rejected bindings
- **WHEN** a node completes planning for inputs
- **THEN** execution trace data includes both bound and skipped decisions with reason fields
- **AND** each decision references edge id, source node, target port, and status
