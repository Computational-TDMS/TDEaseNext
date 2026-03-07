## ADDED Requirements

### Requirement: TopMSV PrSM table interaction
The system SHALL support a PrSM-centric table interaction mode where selections are propagated using stable PrSM identifiers.

#### Scenario: PrSM table emits stable selection IDs
- **WHEN** a user selects one or more rows in the PrSM table viewer
- **THEN** the node SHALL dispatch `state/selection_ids` using `Prsm ID` values from the selected rows

#### Scenario: PrSM table handles external selection
- **WHEN** the PrSM table receives `state/selection_ids` from another TopMSV node
- **THEN** it SHALL highlight rows whose `Prsm ID` values match the incoming IDs

### Requirement: TopMSV selection semantic reuse
The TopMSV branch SHALL reuse `state/selection_ids` as the selection semantic type and SHALL NOT introduce a new semantic type for PrSM IDs in this change.

#### Scenario: TopMSV state port semantic type
- **WHEN** TopMSV table, MS2 viewer, and sequence viewer ports are defined
- **THEN** their selection state ports SHALL use `semanticType: "state/selection_ids"`

### Requirement: TopMSV MS2 viewer node
The system SHALL provide a dedicated interactive node type for visualizing MS2 spectra from `prsm_bundle.tsv`.

#### Scenario: MS2 viewer renders selected PrSM spectrum
- **WHEN** `topmsv_ms2_viewer` receives a `state/selection_ids` payload with a single `Prsm ID`
- **THEN** it SHALL locate the corresponding row in `prsm_bundle.tsv` and render its MS2 peaks

#### Scenario: MS2 viewer updates on selection change
- **WHEN** the upstream PrSM selection changes
- **THEN** the MS2 viewer SHALL re-render synchronously with the newly selected PrSM data

#### Scenario: MS2 viewer missing mapping fallback
- **WHEN** the selected row has `mapping_status` indicating missing spectrum mapping
- **THEN** the viewer SHALL show a non-blocking empty-state message instead of throwing runtime errors

### Requirement: TopMSV sequence viewer node
The system SHALL provide a dedicated interactive node type for sequence visualization from `prsm_bundle.tsv`.

#### Scenario: Sequence viewer renders proteoform sequence
- **WHEN** `topmsv_sequence_viewer` receives a selected `Prsm ID`
- **THEN** it SHALL display the corresponding sequence and modification annotations

#### Scenario: Sequence viewer synchronized with MS2 viewer
- **WHEN** table selection changes
- **THEN** sequence and MS2 viewers SHALL display data from the same `Prsm ID` in the same reactivity cycle

#### Scenario: Sequence viewer read-only mode in v1
- **WHEN** a user inspects sequence content in `topmsv_sequence_viewer`
- **THEN** the viewer SHALL provide read-only sequence and modification rendering
- **AND** it SHALL NOT provide sequence editing or compute-proxy recalculation actions in this change

### Requirement: TopMSV state connections use state channel semantics
Selection propagation in the TopMSV branch SHALL use state connections, not data connections.

#### Scenario: Workflow edge kind for selection links
- **WHEN** `wf_test_full.json` defines selection links from PrSM table to TopMSV viewers
- **THEN** those edges SHALL use `connectionKind: "state"` and connect `state-out` to `state-in` ports only
