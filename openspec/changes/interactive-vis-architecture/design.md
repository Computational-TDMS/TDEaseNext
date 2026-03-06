# Design: Unified Architecture for Interactive Workflow Visualization (v2)

## 1. Port-Aware Data Infrastructure

To resolve the "Missing Data" issue, we are formalizing the Data Context. Interactive nodes SHALL no longer guess their input files based on the upstream node ID alone.

### Data Addressing Protocol
The `VisualizationStore` and `NodeDataAccess API` SHALL use a triplet-based addressing scheme:
`DataAddress = { nodeId: string, portId: string, executionId: string }`

1.  **Canvas Edges**: Edges from Compute nodes to View nodes SHALL store the `source.portId`.
2.  **API Update**: The backend `/api/nodes/{node_id}/data` endpoint SHALL support an optional `port_id` query parameter.
3.  **Client Logic**:
    ```typescript
    // New resolution pattern
    const sourceNodeId = edge.source.nodeId;
    const sourcePortId = edge.source.portId;
    const data = await store.loadNodeData(nodeId, executionId, sourceNodeId, sourcePortId);
    ```

## 2. Vis-Interaction Infrastructure (Tiered Architecture)

We are refactoring the current monolithic `InteractiveNode.vue` into a decoupled infrastructure:

### Tier 1: Canvas Wrapper (`InteractiveNode.vue`)
- **Responsibility**: VueFlow integration, resizing handles, state edge connections.
- **Visuals**: Clean, minimal border. Distinct styling for "Unconfigured" vs "Data Ready".

### Tier 2: Visualization Container (`VisContainer.vue`)
- **Responsibility**: Common UI scaffolding and data lifecycle.
- **"Headless" Mode**: The container SHALL detect if it is inside a VueFlow node or a standalone Page. When standalone, it hides specific canvas-sync logic but remains connected to the `VisualizationStore` and `StateBus`.

### Tier 3: Atomic Viewers
- **Responsibility**: Pure data rendering.
- **Example**: `BaseScatterPlot.vue`, `BaseTableView.vue`.
- **Interface**: Receives `columns[]` and `rows[]`. Emits `selection: indices[]`.

## 3. Bimodal Canvas Layout (UI/UX)

The canvas SHALL visually distinguish between the "Physical Data Flow" and the "Logical Interaction Flow".

### Pipeline Distinction
| Feature | Physical (Data) Edge | Logical (Interaction) Edge |
|---------|---------------------|---------------------------|
| **Visual Style** | Solid Blue Line | Dashed Orange Line |
| **Animation** | Slow Pulse (Static) | Fast Flow Pulse (on Interaction) |
| **Source Type** | Compute Node Port | View Node State Port |
| **Target Type** | View Node Data Port | View Node State Input |

### Interaction Feedback
When a user interacts with a "Primary" viewer (e.g., FeatureMap), the outgoing Dashed edges SHALL briefly animate a "data packet" flow to show the selection state propagating to downstream viewers.

## 4. Requirement Updates

1.  **State Persistence**: All axis mappings and viewport settings SHALL be persisted in the `workflow.nodes[].data.visualizationConfig` object.
2.  **Aggregation Logic**: If an interactive node is connected to multiple data sources, it SHALL provide a tabbed interface or a multi-file merge logic in the Config Panel.
3.  **Schema Caching**: Upstream tool schemas SHALL be cached at the workspace level to allow instant Config Panel rendering before execution completion.

