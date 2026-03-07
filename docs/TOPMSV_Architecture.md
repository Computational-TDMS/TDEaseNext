# TOPMSV HTML-Driven Architecture

## 1. Scope

TopMSV in TDEase uses TopPIC HTML assets as canonical visualization data source.
The viewers are interactive-only and selection-driven.

## 2. Dataflow

```text
TopPIC (html_folder) -----------------------> topmsv_sequence_viewer
       \                                      (sequence/mod/breakpoint)
        \-----> topmsv_ms2_viewer
               (raw spectrum + matched peaks)

table_viewer (PrSM ID selection, state/selection_ids)
    -> topmsv_sequence_viewer.selection_in
    -> topmsv_ms2_viewer.selection_in
```

## 3. API Boundary

TopMSV viewers do not parse large JS files in browser.
They request normalized payload from backend.

**Preferred (generic)**:
`GET /api/executions/{execution_id}/nodes/{source_node_id}/interactive-data/{selection_key}?resolver=topmsv_prsm&port_id=html_folder&spectrum_id=...`

**Legacy alias**: `GET /api/executions/{execution_id}/nodes/{source_node_id}/topmsv/prsm/{prsm_id}` (delegates to the same resolver).

Backend responsibilities:

1. **DataResolverRegistry** invokes the `topmsv_prsm` resolver with execution_id, node_id, selection_key (PrSM ID).
2. Resolve `html_folder` from execution snapshot + node outputs.
3. Read **subResources** from the source tool definition (e.g. `toppic` ports.outputs[html_folder].subResources) when present; otherwise use built-in path patterns.
4. Parse `prsm{ID}.js` and extract sequence/modification/breakpoint/matched peaks; parse `spectrum{ID}.js` when needed.
5. Return compact JSON for frontend rendering.

## 4. Frontend Responsibilities

1. Resolve upstream source node/port from workflow edges.
2. For TopMSV viewers, allow non-tabular data fallback to keep node mounted.
3. Read selection state (`PrSM ID`) and call TopMSV endpoint.
4. Render:
   - Sequence viewer: residue marks for PTM/mass-shift and breakpoints.
   - MS2 viewer: raw spectrum plot + matched deconvoluted peaks table + spectrum switch.

## 5. Contracts and Assumptions

- TopPIC HTML output folder exists in workspace (`*_html`).
- Path patterns are **tool-defined** when possible: `toppic` output port `html_folder` may declare `subResources.prsm_js` and `subResources.spectrum_js` (pattern with `{id}`, optional `preferPaths` / `optional`). If absent, built-in patterns apply: `**/data_js/prsms/prsm{ID}.js`, `**/ms2_json/spectrum{ID}.js`.
- Selection payload values are PrSM IDs (numeric).

## 6. Failure Handling

- Missing HTML folder or prsm JS: API returns 404.
- Invalid `prsm_id`/`spectrum_id`: API returns 400.
- Missing spectrum JS: API returns sequence + matched peaks; raw spectrum array may be empty.
- Missing selection: frontend stays in guidance state (no API call).
