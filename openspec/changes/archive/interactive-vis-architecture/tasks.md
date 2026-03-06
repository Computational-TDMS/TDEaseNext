# Implementation Tasks: Interactive Visualization Architecture (v2)

## Phase 1: Core Protocol & Backend (Data Context)

### Task 1.1: Backend Port-Aware Data Access
**Priority**: High
- [x] 1.1.1 Update `/api/nodes/{node_id}/data` to accept an optional `port_id` query parameter.
- [x] 1.1.2 Modify `workspace_data_api.py` to filter output files by the provided `port_id`.
- [x] 1.1.3 Ensure the response returns the schema associated with that specific port.

### Task 1.2: Frontend Port-Aware Addressing
**Priority**: High
- [x] 1.2.1 Update `VisualizationStore.ts` to use `(nodeId, portId, executionId)` for all data operations.
- [x] 1.2.2 Modify `loadNodeData` to pass the `port_id` to the backend API.
- [x] 1.2.3 Update `workflow-connector.ts` to extract `sourcePortId` from VueFlow connections.

## Phase 2: Frontend Infrastructure Refactor

### Task 2.1: Create VisContainer Infrastructure
**Priority**: High
- [x] 2.1.1 Implement `VisContainer.vue` with Header, Toolbar, and Config Drawer.
- [x] 2.1.2 Implement the dynamic `ColumnConfigPanel` inside the VisContainer drawer.
- [x] 2.1.3 Create a shared `useVisualizationData` composable for standardized data fetching and error handling.

### Task 2.2: Refactor InteractiveNode.vue
**Priority**: High
- [x] 2.2.1 Strip monolithic logic from `InteractiveNode.vue`, leaving only VueFlow wrapper code.
- [x] 2.2.2 Integrate `VisContainer` as the primary child of `InteractiveNode`.
- [x] 2.2.3 Ensure resizing and position state are correctly passed to the container.

### Task 2.3: Decouple Atomic Viewers
**Priority**: Medium
- [x] 2.3.1 Refactor `FeatureMapViewer.vue` and `TableViewer.vue` to be "Pure Components" (props in, events out).
- [x] 2.3.2 Remove any `useVisualizationStore` or `stateBus` calls from inside specific viewers; move to container.

## Phase 3: Bimodal Canvas Visualization

### Task 3.1: Semantic Edge Distinction
**Priority**: Medium
- [x] 3.1.1 Update `StateEdge.vue` with dashed line styling and orange theme.
- [x] 3.1.2 Implement interaction pulse animation in `StateBus.ts` when events are dispatched.
- [x] 3.1.3 Update `ConnectionDefinition` to strictly enforce `connectionKind` differentiation.

## Phase 4: Verification & Test Data

### Task 4.1: Multi-Output Test Workflow
**Priority**: Medium
- [x] 4.1.1 Create a test workflow where a node has 2+ outputs (e.g., TopFD) and 2+ different viewers are connected to different ports.
- [x] 4.1.2 Verify that each viewer loads the correct file data independently.
- [x] 4.1.3 Verify that cross-filtering propagates over the dashed interaction edges correctly.
