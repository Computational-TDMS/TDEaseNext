# Design: Unified Architecture for Interactive Workflow Visualization

## Overview

This design addresses the friction between backend file-level execution and frontend column-level interactive visualizations. To satisfy the complex interrogation workflows (e.g., cross-filtering from MS1 features to MS2 spectra and PrSM mapping), we are introducing a strict architectural separation:

1.  **Compute Nodes**: Responsible for backend execution. Their ports exclusively pass `data/file` objects (e.g., `.mzML`, `.ms1ft`).
2.  **View Nodes (Interactive)**: Placed on the same canvas but do NOT execute. They accept File-level inputs and "awaken" when data is available. Column mapping is pushed entirely into an **Internal Configuration Panel** within the node, rather than cluttering the canvas with column-level edge wiring.

These nodes communicate their interactive state (e.g., a user's brush selection) over a frontend **Semantic Event Bus** using `state/selection` edges.

## Rationale / Trade-offs

*   **Why not column-level ports on the Canvas?** While creating `data/column` output ports for every column (Mass, RT, Intensity, etc.) gives ultimate flexibility, it causes extreme visual clutter on the canvas for complex tools like MSPathFinder that output dozens of columns. It also breaks the paradigm of "File Flow", making the graph difficult to parse at a high level.
*   **Why Internal Configuration Panels?** By retaining File-level connections on the main canvas (`promex` -> `featuremap_viewer`), we maintain high-level lineage. The detailed mapping (X Axis = RT, Y Axis = Mass) becomes an internal concern of the `featuremap_viewer`, manageable via a clean property panel. Since we know the schema of most Bioinformatics outputs, we can auto-populate these mapping dropdowns.
*   **Why a Semantic Event Bus?** Cross-filtering requires passing transient row IDs or criteria (e.g., "Filter Table to show only these 5 selected MS1 features"). Passing huge raw subsets between nodes is highly inefficient. Passing `state/selection_ids` allows downstream nodes to quickly query the `NodeDataAccess API` to render their specific view of the *same* underlying data or related HTML fragments.

## Architecture

### 1. Node Classes and State Edges

The VueFlow canvas will render two visually distinct layers of connections:

#### A. Data Pipeline (File Edges)
*   Represent the physical lineage of files.
*   Connections like: `topfd_1[ms1feature]` -> `featuremap_1[input_file]`.
*   These connections fuel the `NodeDataAccess API`. Once `topfd_1` completes, `featuremap_1` triggers a data fetch.

#### B. State Pipeline (Semantic State Edges)
*   Represent the flow of user interaction.
*   Connections like: `featuremap_1[selection]` -> `spectrum_1[selection_in]`.
*   When a user brushes the FeatureMap, an event containing the row IDs is emitted over this edge.

### 2. The Internal Configuration Panel

Interactive nodes (like `InteractiveNode.vue`) will be augmented to read the schema of their connected input files.

1.  **Schema Declaration**: Compute tools will declare their known column schemas in their JSON definitions.
    ```json
    "outputs": [
      {
        "id": "ms1feature",
        "dataType": "feature",
        "schema": [
          { "id": "Mass", "type": "number" },
          { "id": "RT", "type": "number" }
        ]
      }
    ]
    ```
2.  **Panel Rendering**: When the user opens the View Node's configuration panel, it uses the incoming file's `schema` to populate a dropdown. If no schema is predefined, the node will dynamically fetch the file headers via the `/data` API upon execution completion.
3.  **Default Mapping**: To save setup time, View Node tool definitions can declare a `defaultMapping` (e.g., `featuremap_viewer.json` dictates that X maps to `RT`, Y maps to `Mass`).

### 3. Cross-Filtering Execution Flow

**Scenario: User selects features in MS1, mapping to MS2 HTML Views**

1.  **User Action**: The `FeatureMapViewer` widget records a brush selection.
2.  **Emission**: The widget emits a Vue event containing `selectedRowIndices`.
3.  **State Bus**: The `StateBus` intercepts this and identifies all outgoing `state/selection_ids` edges connected to the node.
4.  **Propagation**: The indices are delivered to the connected `SpectrumViewer` and the new `HtmlViewer` node.
5.  **Re-rendering**:
    *   The `SpectrumViewer` filters its internal data to highlight the matching M/Z peaks.
    *   The `HtmlViewer` queries the TopPIC `_html` output endpoint using the selected IDs, fetching and rendering the specific PrSM visualization.

## Technical Requirements

1.  **Tool Definition Extensions**: Update `config/tools/*.json` to support output `schema` and input `defaultMapping`.
2.  **VueFlow Enhancements**: Add custom edge styles for `state/selection` to visually differentiate them from data flow.
3.  **InteractiveNode.vue Refactor**: Implement the Internal Configuration Panel with dynamic schema loading and mapping interface.
4.  **NodeDataAccess API Cache**: Ensure the frontend aggressively caches file data to support zero-latency cross-filtering without redundantly hitting the backend when State Edges trigger re-renders.
