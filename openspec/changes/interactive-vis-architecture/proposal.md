# Proposal: Unified Architecture for Interactive Workflow Visualization

## Context
Bioinformatics workflows (e.g., TopFD, ProMex, MSPathFinder) involve distinct phases:
1. **Backend Execution**: Heavy CLI tools process files (mzML, FASTA) into summary files (feature tables, PrSM results).
2. **Frontend Interrogation**: Researchers interactively cross-filter, annotate, and visually inspect the results across interrelated dimensions (e.g., MS1 Features -> MS2 Spectra -> Modification mapping).

Currently, the disconnect between "File-level Execution Ports" and "Column-level Visual Interaction" causes friction. Our previous attempt to map columns purely via VueFlow connections on the canvas proved inadequate for the complex interactivity workflows defined in `docs/WORKFLOW_REQUIREMENTS.md`.

## The Problem
- **Conceptual Disconnect**: Visualizations are fundamentally different from Backend Compute Nodes, yet they run on the same Editor Canvas.
- **Deep Association Needs**: Interactions span across files (clicking an MS1 point in FeatureMap needs to pull sequence tags from an MS2 HTML file and filter a PrSM list). Pure canvas port-wiring cannot easily capture this cross-file semantic linking dynamically.
- **Data Access Layer**: Visual nodes must load substantial data (feature files) without hanging the browser, converting it into renderable columns.

## Proposed Solution: The "View Node" Architecture

We propose a radical architectural distinction between **Compute Nodes (Backend)** and **View Nodes (Frontend)**, unified by a new state-messaging bus.

### 1. Distinct Node Classes
- **Compute Node**: Configured via static `tool.json`. Produces physical files. Its ports ONLY pass `data/file` (e.g., `mzML`, `ms1feature`, `tsv`).
- **View Node (Interactive Node)**: Configured purely via its *Internal Configuration Panel*. It "awakens" when its connected upstream File ports receive data.
  - **No Column Ports on Canvas**: Instead of littering the VueFlow canvas with 50 column-level output ports, the user connects the **File Port** (`ms1feature` output) to the View Node (`FeatureMap` input).
  - **In-Panel Data Mapping**: Double-clicking the View Node opens the Configuration Panel. Since we know the schema of standard tools (TopFD/ProMex), the panel *auto-populates* dropdowns: "X Axis: [RT]", "Y Axis: [Mass]".

### 2. The Semantic Event Bus (Cross-Filtering)
To satisfy the complex flows in `WORKFLOW_REQUIREMENTS.md`, View Nodes communicate via a frontend-only Event Bus using "Semantic State Edges".
- **Selection State Propagation**: A brush selection on a FeatureMap (MS1) emits `semanticType: state/selection_ids`.
- **Dynamic Queries**: The Spectrum or Table Viewer receives these IDs. Instead of receiving raw data, they use these IDs to query the `NodeDataAccess API` to subset the currently loaded `.ms1ft` or `PrSM.tsv` and render the subset.
- **HTML Injection View**: For MS2 HTML viewer association, an `HTML Viewer Node` is connected to both the Feature Selection state and the `_html` file output of TopPIC. When a feature is clicked, it pulls the matching `.html` fragment.

### 3. Modifying Tool Definitions (`config/tools/`)
- View nodes like `featuremap_viewer.json` will require an input port of type `data/file` (accepting tabular/feature formats), and output ports of `state/selection`.
- They will encapsulate a `defaultMapping` configuration specifying which columns map to which visual channels, saving users from manual configuration for standard pipelines.

### 4. Refining the Test Workflow (`wf_test_full.json`)
The test workflow design will look like this:
1. `topfd_1` outputs `output-ms1feature`.
2. A single Edge connects `topfd_1` -> `featuremap_1` (File-level connection).
3. Inside `featuremap_1`, parameters define `xAxis: RT`, `yAxis: Mass` (defaulted by the backend).
4. `featuremap_1` outputs a `state/selection` Edge to `spectrum_1`.
5. A third `table_viewer` node connects to MSPathFinder's TSV, receiving the `state/selection` to filter PrSM results based on MS1 brush selections.

## Impact
- **Canvas Cleanliness**: The main canvas remains clean, showing data lineage (files) and interaction flow (states) without being overwhelmed by column wiring.
- **Deep Interactivity**: By passing IDs/States, we can achieve true cross-tool filtering (Feature -> MS2 -> PrSM).
- **Backend/Frontend Separation**: The backend remains ignorant of visual axes; it only serves files and queries via Node Data Access.

## Technical Requirements
- Update `InteractiveNode.vue` to render dynamic data-mapping panels based on incoming file schemas.
- Ensure the `StateBus` supports broadcasting row IDs and semantic filters across View Nodes reliably.
- Introduce an `HTMLViewer` interactive node for rendering PrSM MS2 HTML fragments.

## Success Criteria
- [ ] Users can map columns to axes inside the Configuration Panel of interactive nodes.
- [ ] Brushing an MS1 FeatureMap dynamically filters a connected MS2 Spectrum/Table in real-time.
- [ ] The `wf_test_full.json` can be loaded and interactively explored per `WORKFLOW_REQUIREMENTS.md` specs.
