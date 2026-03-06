# Proposal: Unified Architecture for Interactive Workflow Visualization (v2)

## Context
Bioinformatics workflows (e.g., TopFD, ProMex, MSPathFinder) involve distinct phases:
1. **Backend Execution**: Heavy CLI tools process files (mzML, FASTA) into summary files (feature tables, PrSM results).
2. **Frontend Interrogation**: Researchers interactively cross-filter, annotate, and visually inspect the results across interrelated dimensions.

## The Problem
- **Data Context Ambiguity**: Interactive nodes currently "guess" which upstream file to load. If a tool has multiple outputs, resolution fails.
- **Frontend Infrastructure Chaos**: `InteractiveNode.vue` is a monolith. There's no clear separation between canvas logic, data provisioning, and specific viewer implementations.
- **Canvas Semantic Clutter**: The layout doesn't distinguish between the *Process Pipeline* (files) and the *Interaction Pipeline* (selection states), making the workflow logic hard to follow.

## Proposed Solution: The "Context-Aware View Node" Architecture

### 1. Port-Aware Data Context
We are moving from "Node-based resolution" to "Port-based resolution".
- **Connection Context**: Every Data Edge on the canvas SHALL carry the `port_id` of the output it represents.
- **Data Provider**: Visual nodes will use a `DataProvider` service that takes `(nodeId, portId, executionId)` to fetch exact files, ensuring TopFD's `ms1feature` isn't confused with its `ms2feature`.

### 2. Vis-Interaction Infrastructure
We will refactor `InteractiveNode.vue` into a three-tier architecture:
1.  **Canvas Interface**: Handles handle rendering, node resizing, and position.
2.  **VisContainer**: A shared wrapper providing a Toolbar (Zoom, Export, Filter status), Data Loading states, and the Configuration Drawer.
3.  **Atomic Viewers**: Decoupled components (e.g., `ScatterPlotViewer`, `TableViewer`) that only receive typed data and emit interaction events.

### 3. Bimodal Canvas Pipeline
To clarify the layout, we will implement a "Pipeline Distinction":
- **Process Lineage (Solid Edges)**: Connects Compute nodes to Compute nodes, or Compute nodes to View nodes. Represents the physical flow of data files.
- **Interaction Topology (Dashed/Semantic Edges)**: Connects View nodes to View nodes. Represents the logical flow of selection states (e.g., filtering a table by clicking a map).

### 4. Simplified Scope
- **MS2 HTML Association**: Moved to Phase 2 (Low Priority).
- **Core Focus**: Stable MS1 feature mapping, reliable cross-filtering (Feature -> Table), and robust configuration persistence.

### 5. Unified Report View (Dashboards)
By decoupling the `VisContainer` from the VueFlow canvas, the architecture naturally supports a **"Report Mode"**:
- **Canvas-Free Rendering**: The same widgets used on the canvas can be instantiated in a linear or grid-based "Dashboard View".
- **Global Interaction Sync**: Since widgets communicate via the global `StateBus`, selections made in a FeatureMap on the Canvas will stay in sync with a Table in the Report View (and vice versa).

## Technical Requirements
- Refactor `VisualizationStore` to support port-level addressing.
- Implement `VisContainer` to standardize interactive node behavior.
- Update `StateEdge.vue` and `InteractiveNode.vue` visuals to reflect the process/interaction distinction.
- **New**: Ensure `VisContainer` can be initialized in "Headless" mode (without VueFlow context).

## Success Criteria
- [ ] Users can reliably load visual nodes from tools with multiple outputs.
- [ ] Viewers are decoupled and reusable outside the canvas context.
- [ ] The canvas clearly shows where data ends and interaction begins.
- [ ] Brushing an MS1 FeatureMap reliably filters a connected Table.

