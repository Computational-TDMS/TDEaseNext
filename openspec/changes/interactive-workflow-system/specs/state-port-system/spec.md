## ADDED Requirements

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
