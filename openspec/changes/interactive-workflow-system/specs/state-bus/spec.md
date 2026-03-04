## ADDED Requirements

### Requirement: Centralized state dispatch and subscription
The system SHALL provide a State Bus (Pinia Store) that manages all inter-node state communication through centralized dispatch and subscription.

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

## MODIFIED Requirements

### Requirement: Visualization Store upgrade
The existing `visualization` Pinia Store SHALL be extended (not replaced) to support State Bus functionality.

#### Scenario: Backward compatible API
- **WHEN** existing code calls `visualization.updateSelection(nodeId, selection)`
- **THEN** the call SHALL internally delegate to `stateBus.dispatch(nodeId, 'selection_out', selection)`
- **AND** all existing selection-based functionality SHALL continue to work
