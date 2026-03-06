# TopMSV PrSM Bundle

## Purpose

Provides workflow nodes and data contracts for building PrSM (ProteoSpectrum Identification) bundles that normalize TopPIC and TopFD outputs into viewer-ready tabular artifacts for interactive visualization.

## Requirements

### Requirement: PrSM bundle builder node
The system SHALL provide a `prsm_bundle_builder` workflow node that normalizes TopPIC and TopFD outputs into viewer-ready tabular artifacts.

#### Scenario: Build bundle from TopPIC and TopFD outputs
- **WHEN** the node receives `toppic.prsm_single` and `topfd.ms2_msalign` inputs for a completed execution
- **THEN** the node SHALL parse both sources and produce normalized outputs for downstream interactive viewers

#### Scenario: Optional TopFD feature mapping
- **WHEN** `topfd.ms2feature` is connected in addition to required inputs
- **THEN** the node SHALL enrich bundle rows with feature linkage fields without changing required output schema

#### Scenario: Partial mapping visibility
- **WHEN** a PrSM row cannot be mapped to an MS2 spectrum block
- **THEN** the node SHALL still emit the PrSM row with `mapping_status` indicating the missing mapping

### Requirement: PrSM bundle output contracts
The `prsm_bundle_builder` node SHALL emit two TSV outputs with stable schemas for TopMSV interaction nodes.

#### Scenario: Clean PrSM table output
- **WHEN** bundle generation succeeds
- **THEN** the node SHALL output `prsm_table_clean.tsv` containing normalized PrSM columns suitable for direct table rendering

#### Scenario: Unified bundle output
- **WHEN** bundle generation succeeds
- **THEN** the node SHALL output `prsm_bundle.tsv` with one row per PrSM including at least `prsm_id`, `spectrum_id`, `scan`, sequence/modification fields, and serialized MS2 peaks
- **AND** the serialized MS2 peaks SHALL be embedded in `prsm_bundle.tsv` rows in the initial release

#### Scenario: MS2 peak payload cap
- **WHEN** writing serialized MS2 peaks into `prsm_bundle.tsv`
- **THEN** the node SHALL cap peaks by intensity TopN with a configurable threshold
- **AND** the node SHALL apply a default TopN value when no explicit threshold is provided

#### Scenario: Stable key guarantee
- **WHEN** table sorting or filtering changes row order in the frontend
- **THEN** downstream nodes SHALL still resolve records by `prsm_id` rather than row index

### Requirement: Workflow-level TopMSV branch wiring
The workflow definition SHALL support a dedicated TopMSV branch driven by bundle outputs.

#### Scenario: Bundle node inserted into wf_test_full
- **WHEN** `workflows/wf_test_full.json` is updated for this capability
- **THEN** it SHALL include a `prsm_bundle_builder_1` node connected from `toppic_1.prsm_single` and `topfd_1.ms2_msalign`

#### Scenario: HTML outputs disabled for table-driven mode
- **WHEN** the TopMSV branch is enabled in `wf_test_full`
- **THEN** `topfd_1` and `toppic_1` parameters SHALL set `skip_html_folder=true`
