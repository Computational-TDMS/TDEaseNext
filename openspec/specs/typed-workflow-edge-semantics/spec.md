# Typed Workflow Edge Semantics

## Purpose

TBD: Describe capability intent and scope.

## Requirements

### Requirement: Workflow normalization SHALL preserve edge semantic fields
The normalizer SHALL retain edge semantic fields required for typed scheduling and interaction handling.

#### Scenario: Semantic fields survive normalization
- **WHEN** an input workflow edge includes `connectionKind` and `semanticType`
- **THEN** the normalized workflow edge includes the same semantic values
- **AND** missing `connectionKind` defaults to `data` for backward compatibility

### Requirement: Scheduler dependencies SHALL be built from dependency-bearing edge kinds only
The execution graph SHALL treat only dependency-bearing edge kinds as predecessor constraints.

#### Scenario: State edge does not block compute scheduling
- **WHEN** a workflow contains both data edges and state edges to a node
- **THEN** scheduler predecessor checks use only dependency-bearing edges
- **AND** state-only edges do not prevent node readiness

### Requirement: State edges SHALL remain observable in runtime metadata
Even when excluded from scheduling dependencies, state edges SHALL remain available for APIs and traces.

#### Scenario: Edge metadata remains queryable
- **WHEN** execution metadata or topology traces are queried
- **THEN** state edges are present with their semantic fields
- **AND** their classification as non-dependency edges is explicit
