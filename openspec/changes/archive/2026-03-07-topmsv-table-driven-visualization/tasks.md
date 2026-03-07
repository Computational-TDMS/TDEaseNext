## 1. Tool Definitions And Contracts

- [x] 1.1 Add `config/tools/prsm_bundle_builder.json` with required inputs (`prsm_single`, `ms2_msalign`) and outputs (`prsm_table_clean`, `prsm_bundle`).
- [x] 1.2 Add `config/tools/topmsv_ms2_viewer.json` and `config/tools/topmsv_sequence_viewer.json` as `executionMode: "interactive"` tools with `state/selection_ids` state port contracts.
- [x] 1.3 Define and validate `selection_key_field: "Prsm ID"` for TopMSV interactive nodes that consume table selections.
- [x] 1.4 Extend tool schema validation/tests so new tool definitions and state port metadata pass registry loading checks.

## 2. Bundle Builder Implementation

- [x] 2.1 Implement backend execution logic for `prsm_bundle_builder` to parse TopPIC PrSM TSV and TopFD MS2 msalign inputs.
- [x] 2.2 Generate `prsm_table_clean.tsv` and `prsm_bundle.tsv` with stable `prsm_id`, `mapping_status`, and embedded `ms2_peaks_json` fields.
- [x] 2.3 Add configurable MS2 peak TopN truncation with a default value in bundle generation.
- [x] 2.4 Add unit tests using workspace fixtures to verify join logic, missing-mapping behavior, and output column contracts.

## 3. Node Data Access Parsing Upgrade

- [x] 3.1 Update `app/services/node_data_service.py` tabular parser to skip TopPIC-style preamble lines and detect the real header.
- [x] 3.2 Preserve existing TSV/CSV parsing behavior for standard files and unsupported extension fallback behavior.
- [x] 3.3 Add tests for standard TSV, TopPIC preamble TSV, and header-detection failure (`parseable: false`).

## 4. TopMSV Interactive Viewers

- [x] 4.1 Register new visualization types in frontend node rendering dispatch (`InteractiveNode` and related typing/config files).
- [x] 4.2 Implement `topmsv_ms2_viewer` to render selected PrSM peak lists and handle missing-spectrum mappings with explicit empty state.
- [x] 4.3 Implement `topmsv_sequence_viewer` in read-only mode to render proteoform sequence and modification annotations for selected PrSM.
- [x] 4.4 Update PrSM table interaction to emit and consume `state/selection_ids` using `Prsm ID` values rather than row indices.

## 5. Workflow Integration

- [x] 5.1 Extend `workflows/wf_test_full.json` with `prsm_bundle_builder_1`, `prsm_table_1`, `ms2_viewer_1`, and `seq_viewer_1`.
- [x] 5.2 Add data edges from `toppic_1`/`topfd_1` to bundle node and from bundle outputs to table/MS2/sequence viewers.
- [x] 5.3 Add state edges from PrSM table to MS2/sequence viewers using `connectionKind: "state"` and correct `state-out -> state-in` handles.
- [x] 5.4 Set `skip_html_folder=true` for `topfd_1` and `toppic_1` in this workflow branch.

## 6. Documentation And Verification

- [x] 6.1 Update `docs/TOPMSV.md` with table-driven implementation path and node/output mapping.
- [x] 6.2 Update `docs/TOPMSV_Architecture.md` with final dataflow diagram and state propagation rules.
- [x] 6.3 Run targeted backend/frontend tests plus workflow validation and record results in the change notes.
