# TOPMSV HTML-Driven Integration Guide

## Overview

TopMSV viewers now consume TopPIC HTML output directly, instead of TSV-embedded bundle fields.

The interaction chain is:

1. `toppic` produces `html_folder` (`{sample}_html`)
2. `table_viewer` emits `state/selection_ids` (PrSM ID)
3. `topmsv_sequence_viewer` and `topmsv_ms2_viewer` call backend TopMSV API by selected PrSM ID
4. Backend parses:
   - `toppic_prsm_cutoff/data_js/prsms/prsm{ID}.js`
   - `topfd/ms2_json/spectrum{ID}.js` (optional/fallback aware)

## Node and Port Mapping

| Node | Input | Purpose |
|---|---|---|
| `topmsv_sequence_viewer` | `html_folder` + `selection_in` | Render sequence, PTM/mass-shift, cleavage breakpoints |
| `topmsv_ms2_viewer` | `html_folder` + `selection_in` | Render raw MS2 peaks and matched deconvoluted peaks |

`selection_in` keeps semantic type: `state/selection_ids`.

## Backend API

TopMSV viewers use:

`GET /api/executions/{execution_id}/nodes/{source_node_id}/topmsv/prsm/{prsm_id}`

Query:

- `spectrum_id` (optional): override selected spectrum
- `port_id` (optional, default `html_folder`)

Response includes:

- sequence payload (`sequence.value`, `sequence.modifications`, `sequence.breakpoints`)
- ms2 payload (`ms2.raw_peaks`, `ms2.matched_peaks`, `ms2.available_spectrum_ids`)
- source metadata (`source.html_root`, `source.prsm_file`, `source.spectrum_file`)

## Frontend Loading Notes

- `visualizationStore.loadNodeData` supports non-tabular fallback for TopMSV nodes.
- If source output is a directory/non-parseable file, it still returns source metadata row.
- TopMSV components use that metadata + selection state to fetch full HTML-derived payload.

## Workflow Requirements

- Keep TopPIC HTML output enabled (`skip_html_folder=false`).
- TopMSV viewers should connect to `toppic.html_folder`.
- Selection source table must output PrSM IDs on `state/selection_ids`.
