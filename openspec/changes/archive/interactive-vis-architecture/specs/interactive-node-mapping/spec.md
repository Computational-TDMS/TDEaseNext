# Specification: Interactive Node Mapping & State Bus (v2)

## Purpose
Define the required behavior for the "Context-Aware View Node" architecture, ensuring reliable data loading from multi-port tools and a modular frontend infrastructure.

## Requirements

### Requirement: Port-Aware Data Resolution
The system SHALL resolve input data for interactive nodes using the specific output port ID from the upstream node.

#### Scenario: Connecting to a specific port
- **WHEN** an edge is created from a Compute Node (e.g., `TopFD`) to a View Node (e.g., `FeatureMap`)
- **THEN** the edge SHALL store the `source.portId` (e.g., `ms1feature`)
- **AND** the View Node SHALL use this `portId` when requesting data from the backend to ensure the correct file is loaded.

### Requirement: Modular Visualization Infrastructure
The frontend SHALL implement a tiered component structure for interactive nodes to ensure separation of concerns.

#### Scenario: VisContainer Scaffolding
- **WHEN** an `InteractiveNode` is rendered
- **THEN** it SHALL encapsulate a `VisContainer` component
- **AND** the `VisContainer` SHALL provide standardized Loading, Error, and Configuration UI states
- **AND** it SHALL provide a toolbar for common actions (Zoom, Reset, Axis Config).

### Requirement: Internal Schema-Based Mapping
Interactive nodes SHALL use the upstream port's schema to provide automated data mapping.

#### Scenario: Mapping columns in the Config Panel
- **WHEN** the Config Panel is opened for a connected View Node
- **THEN** it SHALL fetch the `schema` associated with the connected `portId`
- **AND** it SHALL populate mapping dropdowns with validated column names and types.

### Requirement: Bimodal Canvas Visualization
The canvas SHALL visually distinguish between Data (Physical) and Interaction (Logical) pipelines.

#### Scenario: Distinct Edge Styling
- **WHEN** two nodes are connected via a `connectionKind: "state"` (Semantic) edge
- **THEN** the edge SHALL render as a **dashed line** with a distinct color (e.g., Orange)
- **AND** it SHALL NOT represent physical file movement.
- **WHEN** connected via a `connectionKind: "data"` (Physical) edge
- **THEN** it SHALL render as a **solid line**.

