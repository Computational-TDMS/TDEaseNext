# Column-Level Port Mapping

## Purpose

Address the disconnect between file-level backend execution and column-level frontend visualization. In bioinformatics workflows, tools typically output tabular files whose column schemas (e.g., `Mass`, `RT`, `Intensity`) are mostly predefined and known prior to execution.

By extending the tool definition JSON to explicitly declare output column schemas, the frontend can render **column-level output ports** that users can connect directly to **column-level input ports** on interactive visualization nodes (such as the `X-Axis` port on a FeatureMap viewer). 

This allows users to wire up specific data columns to visualization axes interactively on the canvas *before* the workflow is ever executed. It also serves as the Single Source of Truth (SSOT) for data mapping, eliminating complex internal configuration panels. Moreover, it leaves room for dynamic column extension after execution for open-ended workflows.

## Requirements

### Requirement: Tool Definition Schema Extension
The system SHALL support defining known columns within tabular output ports in the tool JSON definitions.

#### Scenario: Declaring columns in a tabular output
- **WHEN** a tool definition declares an output port of type `data/table`
- **THEN** it MAY optionally include a `schema` array
- **AND** each schema item SHALL define `id` (exact column name in the output), `type` (e.g., "number", "string", "boolean"), and an optional `name`/`description`
- **AND** these predefined columns SHALL be used by the frontend to render static column ports even before the workflow is executed

### Requirement: Column-Level Port Rendering
The workflow canvas SHALL visually represent both file-level and column-level ports.

#### Scenario: Rendering structured tabular outputs
- **WHEN** a node has an output port with a defined `schema`
- **THEN** the node SHALL render the main file-level port (e.g., `feature_list`)
- **AND** the node SHALL render child ports for each defined column beneath or adjacent to the main port
- **AND** column-level ports SHALL be visually distinct from file-level ports (e.g., different shape, size, or color based on their data type like number or string)

### Requirement: Column-Level Inputs for Visualization Nodes
Interactive visualization nodes SHALL declare specific input ports for receiving column data.

#### Scenario: FeatureMap Viewer inputs
- **WHEN** configuring a FeatureMap Viewer node
- **THEN** its tool definition SHALL define `x_axis`, `y_axis`, and optional `color`/`size` input ports
- **AND** these ports SHALL have `dataType: "data/column"`
- **AND** they MAY restrict connections by specifying `acceptedTypes` (e.g., `x_axis` might only accept `["number"]`)

### Requirement: Connection Validation (Type Safety)
The system SHALL enforce type safety when users connect column output ports to column input ports.

#### Scenario: Connecting a column output to a column input
- **WHEN** a user drags a connection from a column output (e.g., `RT (number)`) to a column input (e.g., `X-Axis`)
- **THEN** the VueFlow canvas SHALL validate that both ports are of type `data/column`
- **AND** SHALL validate that the output column's data type (e.g., "number") is compatible with the input port's `acceptedTypes`
- **AND** SHALL visually reject the connection if types are incompatible (e.g., connecting a "string" column to an axis that requires a "number")

### Requirement: Single Source of Truth (SSOT) Data Mapping
Visualization nodes SHALL use the canvas connection (Edge) as the sole configuration for data mapping.

#### Scenario: Requesting column data for a visualization
- **WHEN** a visualization node needs data to render (e.g., a ScatterPlot)
- **THEN** it SHALL inspect incoming edges to its column input ports
- **AND** it SHALL trace the edge back to the root output file port on the source node
- **AND** it SHALL use the column `id` associated with the source port to extract only the necessary column data (either from a frontend cache or via an optimized backend data-access API request)
- **AND** the visualization node SHALL NOT maintain internal state replicating this mapping

### Requirement: Dynamic Port Extension (Post-Execution)
The system SHALL allow extending a node's column ports after execution to handle unknown or dynamically generated columns.

#### Scenario: Tool outputs additional columns
- **WHEN** a workflow node finishes execution
- **AND** the frontend loads the actual output tabular file via the Node Data Access API
- **THEN** the system SHALL parse the actual columns in the file
- **AND** it SHALL dynamically inject new column ports into the node for any columns that were not pre-defined in the tool's JSON `schema`
- **AND** users CAN subsequently connect these newly discovered column ports to visualization nodes
