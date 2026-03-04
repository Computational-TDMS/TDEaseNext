## ADDED Requirements

### Requirement: Visualization Pinia Store
The system SHALL maintain a dedicated Pinia store (`visualization`) that manages all interactive node data and selection states independently from the workflow topology store.

#### Scenario: Node data cached on load
- **WHEN** an interactive node loads data from the backend
- **THEN** the visualization store SHALL cache the full dataset under the node's ID
- **AND** subsequent renders of the same node SHALL read from the cache without re-fetching

#### Scenario: Node data cleared on execution reset
- **WHEN** a new workflow execution is triggered
- **THEN** the visualization store SHALL clear all cached node data and selection states

#### Scenario: Selection state updated
- **WHEN** a user interaction in an interactive node produces a selection
- **THEN** the visualization store SHALL update `nodeSelections[nodeId]` with the new selection
- **AND** any Vue computed properties watching that key SHALL re-evaluate

### Requirement: Connection-based data source resolution
The system SHALL determine whether each interactive node's data comes from a file (upstream processing node) or from a state (upstream interactive node), by analyzing VueFlow connections at runtime.

#### Scenario: File source detected
- **WHEN** the upstream connected node's tool has `executionMode` other than "interactive"
- **THEN** the data source type SHALL be "file"
- **AND** the system SHALL use the P1 `GET /api/executions/{execution_id}/nodes/{node_id}/data` API to load data

#### Scenario: State source detected
- **WHEN** the upstream connected node's tool has `executionMode: "interactive"`
- **THEN** the data source type SHALL be "state"
- **AND** the system SHALL subscribe to `nodeSelections[upstreamNodeId]` in the visualization store

#### Scenario: No upstream connection
- **WHEN** an interactive node has no incoming connections
- **THEN** the node SHALL display an "awaiting input" prompt
- **AND** no data loading SHALL be attempted

### Requirement: Downstream node automatic update
The system SHALL automatically propagate selection changes from an upstream interactive node to all directly connected downstream interactive nodes.

#### Scenario: Upstream selection change triggers downstream update
- **WHEN** `nodeSelections[upstreamNodeId]` changes in the visualization store
- **THEN** all downstream interactive nodes connected to that node SHALL re-filter and re-render their views
- **AND** the update SHALL happen synchronously within the same Vue reactivity cycle (no user action required)

#### Scenario: Multi-hop propagation
- **WHEN** NodeA → NodeB → NodeC are all interactive nodes
- **AND** the user changes selection in NodeA
- **THEN** NodeB SHALL update first, then NodeC SHALL update based on NodeB's filtered view

### Requirement: Latest execution context binding
The system SHALL automatically bind interactive nodes to the latest completed execution when a workflow is opened in editor mode, enabling data preview without re-running.

#### Scenario: Interactive node loads latest execution data on open
- **WHEN** the user opens a workflow in the editor
- **AND** a latest completed execution exists (via `GET /api/workflows/{workflow_id}/latest-execution`)
- **THEN** interactive nodes SHALL automatically load their data using that execution's ID
- **AND** no user action SHALL be required to see the data preview
