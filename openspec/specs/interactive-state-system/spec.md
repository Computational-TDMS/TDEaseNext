# Interactive State System

## Purpose

Manage the runtime state of interactive visualization nodes and enable seamless state communication between nodes. This capability provides a three-tier architecture: node-level state caching (Visualization Store), inter-node state communication (State Bus), and typed state port definitions (State Port System), enabling real-time data exploration without backend round-trips.

## Requirements

### Requirement: Visualization Pinia Store (Node-Level State)
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
- **AND** the system SHALL subscribe to state updates for that upstream connection

#### Scenario: No upstream connection
- **WHEN** an interactive node has no incoming connections
- **THEN** the node SHALL display an "awaiting input" prompt
- **AND** no data loading SHALL be attempted

### Requirement: State Bus (Inter-Node Communication)
The system SHALL provide a State Bus (integrated into the Visualization Pinia Store) that manages all inter-node state communication through centralized dispatch and subscription.

#### Scenario: State dispatch from node
- **WHEN** a user interaction (brush select, click, filter change) occurs in a node
- **THEN** the node SHALL call `stateBus.dispatch(nodeId, portId, payload)` instead of direct emit
- **AND** the State Bus SHALL validate the payload against the port's `semanticType`
- **AND** the State Bus SHALL propagate the update to all subscribed downstream nodes

#### Scenario: State subscription by downstream node
- **WHEN** a connection exists from Node A's `state-out` port to Node B's `state-in` port
- **THEN** Node B SHALL automatically receive state updates via State Bus subscription
- **AND** updates SHALL be delivered within the same Vue reactivity tick (synchronous)

#### Scenario: State Bus ignores data connections
- **WHEN** a connection has `connectionKind: "data"`
- **THEN** the State Bus SHALL NOT create subscriptions for that connection
- **AND** data flow SHALL continue through existing file-based mechanisms

#### Scenario: Backward compatible API
- **WHEN** existing code calls `visualization.updateSelection(nodeId, selection)`
- **THEN** the call SHALL internally delegate to `stateBus.dispatch(nodeId, 'selection_out', selection)`
- **AND** all existing selection-based functionality SHALL continue to work

### Requirement: Downstream node automatic update
The system SHALL automatically propagate selection changes from an upstream interactive node to all directly connected downstream interactive nodes.

#### Scenario: Upstream selection change triggers downstream update
- **WHEN** a state dispatch occurs for an upstream node
- **THEN** all downstream interactive nodes connected to that node SHALL re-filter and re-render their views
- **AND** the update SHALL happen synchronously within the same Vue reactivity cycle (no user action required)

#### Scenario: Multi-hop propagation
- **WHEN** NodeA → NodeB → NodeC are all interactive nodes
- **AND** the user changes selection in NodeA
- **THEN** NodeB SHALL update first, then NodeC SHALL update based on NodeB's filtered view

### Requirement: Three-port model for interactive nodes
The system SHALL support three kinds of ports on interactive nodes: `data`, `state-in`, and `state-out`, distinguished by the `portKind` field on `PortDefinition`.

#### Scenario: Node declares state output port
- **WHEN** a tool definition includes a port with `portKind: "state-out"` and `semanticType: "state/selection_ids"`
- **THEN** the canvas SHALL render that port with a distinct visual style (dashed outline, orange color)
- **AND** the port SHALL only accept connections to compatible `state-in` ports

#### Scenario: Node declares state input port
- **WHEN** a tool definition includes a port with `portKind: "state-in"` and a list of `acceptedSemanticTypes`
- **THEN** the canvas SHALL only allow connections from `state-out` ports whose `semanticType` matches one of the accepted types
- **AND** invalid connections SHALL be visually rejected (red highlight + tooltip)

#### Scenario: Data port backward compatibility
- **WHEN** a port definition does NOT include a `portKind` field
- **THEN** the system SHALL default to `portKind: "data"`
- **AND** all existing tool definitions SHALL continue to work without modification

### Requirement: Semantic type validation on connection
The system SHALL validate semantic type compatibility when the user creates a connection between ports.

#### Scenario: Compatible semantic types
- **WHEN** the user drags a connection from a `state-out` port with `semanticType: "state/selection_ids"` to a `state-in` port that accepts `"state/selection_ids"`
- **THEN** the connection SHALL be created successfully
- **AND** the connection SHALL be rendered as a dashed line with state-specific styling

#### Scenario: Incompatible semantic types
- **WHEN** the user drags a connection from a `state-out` port with `semanticType: "state/selection_ids"` to a `state-in` port that only accepts `"state/range"`
- **THEN** the connection SHALL be rejected
- **AND** the canvas SHALL display a tooltip: "Incompatible types: selection_ids → range"

#### Scenario: State-to-data cross-kind connection
- **WHEN** the user attempts to connect a `state-out` port to a `data` port (or vice versa)
- **THEN** the connection SHALL be rejected with message: "Cannot connect state port to data port"

### Requirement: Connection visual differentiation
The system SHALL visually distinguish state connections from data connections on the canvas.

#### Scenario: State connection rendering
- **WHEN** a connection has `connectionKind: "state"`
- **THEN** the edge SHALL be rendered as a dashed line with orange color
- **AND** hovering the edge SHALL show the `semanticType` being transmitted

#### Scenario: Data connection rendering
- **WHEN** a connection has `connectionKind: "data"` or no `connectionKind`
- **THEN** the edge SHALL be rendered as a solid line with the existing default style

### Requirement: Cycle detection
The system SHALL detect and prevent circular state dependencies.

#### Scenario: Direct cycle prevention
- **WHEN** a user attempts to create a state connection that would form a cycle (A → B → A)
- **THEN** the system SHALL reject the connection
- **AND** display a message: "This connection would create a circular dependency"

#### Scenario: Indirect cycle prevention
- **WHEN** a user attempts to create a state connection that would form an indirect cycle (A → B → C → A)
- **THEN** the system SHALL run DFS on the state connection graph
- **AND** reject the connection if a cycle is detected

#### Scenario: Data connections excluded from cycle detection
- **WHEN** checking for cycles
- **THEN** only `state` connections SHALL be included in the cycle detection graph
- **AND** `data` connections SHALL NOT cause cycle detection failures

### Requirement: Multi-branch context isolation
The system SHALL isolate state propagation between independent branches of the workflow graph.

#### Scenario: Parallel branches do not interfere
- **GIVEN** Node A outputs to Branch B and Branch C (two separate paths)
- **WHEN** the user interacts with Branch B nodes
- **THEN** the state changes SHALL NOT propagate to Branch C nodes
- **AND** each branch SHALL maintain an independent interaction context

#### Scenario: State aggregation at join point
- **WHEN** a node receives multiple `state-in` connections from different branches
- **THEN** the node SHALL receive all upstream states
- **AND** the node SHALL wait for all upstream states to be ready before processing (Barrier)
- **AND** the node component SHALL decide how to merge the multiple states (intersection, union, etc.)

#### Scenario: Branch isolation after fan-out
- **GIVEN** a FeatureMap node sends `selection_ids` to both a Spectrum node and a Table node
- **WHEN** the user changes selection in the FeatureMap
- **THEN** both the Spectrum and Table nodes SHALL receive the same updated selection
- **AND** this is fan-out (one source, multiple targets), NOT a branch conflict

### Requirement: Latest execution context binding
The system SHALL automatically bind interactive nodes to the latest completed execution when a workflow is opened in editor mode, enabling data preview without re-running.

#### Scenario: Interactive node loads latest execution data on open
- **WHEN** the user opens a workflow in the editor
- **AND** a latest completed execution exists (via `GET /api/workflows/{workflow_id}/latest-execution`)
- **THEN** interactive nodes SHALL automatically load their data using that execution's ID
- **AND** no user action SHALL be required to see the data preview

### Requirement: Tool schema extension for state ports
The system SHALL extend `tool-schema.json` to support `portKind` and `semanticType` fields.

#### Scenario: Tool definition with state ports
- **WHEN** a tool JSON file defines ports with `portKind` and `semanticType`
- **THEN** the frontend tool loader SHALL parse these fields
- **AND** the node palette SHALL display the port types in the node preview

#### Scenario: Existing tool definitions remain valid
- **WHEN** a tool JSON file does NOT include `portKind` or `semanticType`
- **THEN** all ports SHALL default to `portKind: "data"`
- **AND** the tool SHALL function identically to its current behavior
