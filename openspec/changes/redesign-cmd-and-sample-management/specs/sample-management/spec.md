## ADDED Requirements

### Requirement: Structured Sample Table
The system SHALL support a structured Sample Table in `metadata.sample_table`, where each entry contains a `sample_id` and a `files` map associating file roles (raw, fasta, etc.) to file paths.

#### Scenario: Single sample with raw and fasta
- **WHEN** the workflow metadata contains:
  ```json
  { "sample_table": [{ "sample_id": "SampleA", "files": { "raw": "/data/SampleA.raw", "fasta": "/data/db.fasta" } }] }
  ```
- **THEN** the SampleResolver SHALL produce context `{ "sample": "SampleA", "fasta_filename": "db" }` for placeholder resolution

#### Scenario: Multiple samples
- **WHEN** the sample_table contains 3 entries with different sample_ids
- **THEN** the system SHALL execute the workflow once per sample, each with its own resolved context

#### Scenario: Sample with additional metadata
- **WHEN** a sample entry contains a `metadata` field with custom key-value pairs
- **THEN** those keys SHALL be available as additional placeholders during pattern resolution

### Requirement: Placeholder resolution from Sample Table
The SampleResolver SHALL resolve all `{placeholder}` patterns in output_patterns using the Sample Table entry, deriving `sample` from `sample_id` and file-role-based placeholders (e.g. `fasta_filename`) from the stem of the corresponding file path in `files`.

#### Scenario: Resolve {sample} placeholder
- **WHEN** an output pattern is `{sample}_ms2.msalign` and the current sample_id is `SampleA`
- **THEN** the resolved path SHALL be `SampleA_ms2.msalign`

#### Scenario: Resolve {fasta_filename} placeholder
- **WHEN** an output pattern is `{fasta_filename}.fasta` and the current sample's `files.fasta` is `/data/UniProt_sorghum.fasta`
- **THEN** the resolved path SHALL be `UniProt_sorghum.fasta`

#### Scenario: Missing placeholder
- **WHEN** a pattern contains `{custom_key}` but neither the sample_table entry nor its metadata provides `custom_key`
- **THEN** the system SHALL raise a clear error: `Missing placeholder 'custom_key' for pattern '...'. Available: [...]`

### Requirement: Backward compatibility with flat sample_context
The system SHALL support the legacy `metadata.sample_context` flat dict format by automatically converting it to a single-row Sample Table.

#### Scenario: Legacy workflow with sample_context
- **WHEN** a workflow has `metadata.sample_context: { "sample": "SampleA", "fasta_filename": "db" }` and no `sample_table`
- **THEN** the system SHALL treat it as `sample_table: [{ "sample_id": "SampleA", "files": { "fasta": "db.fasta" } }]`

#### Scenario: Both sample_table and sample_context present
- **WHEN** both `sample_table` and `sample_context` exist in metadata
- **THEN** `sample_table` SHALL take precedence and `sample_context` SHALL be ignored

### Requirement: Fallback sample derivation from loader nodes
When neither `sample_table` nor `sample_context` is present, the system SHALL attempt to derive sample information from data_loader and fasta_loader nodes, but SHALL emit a deprecation warning.

#### Scenario: No sample metadata, has data_loader
- **WHEN** the workflow has no `sample_table` and no `sample_context`, but has a data_loader node with `input_sources: ["/data/SampleA.raw"]`
- **THEN** the system SHALL derive `sample_id = "SampleA"` from the file stem and emit a deprecation warning

#### Scenario: No sample metadata, has both loaders
- **WHEN** the workflow has data_loader and fasta_loader but no explicit sample metadata
- **THEN** the system SHALL derive both `sample` and `fasta_filename` from the respective loader nodes

### Requirement: Batch execution via Sample Table
The system SHALL support batch execution by iterating over all entries in the Sample Table, executing the workflow once per sample with isolated workspace directories.

#### Scenario: Batch execution with 3 samples
- **WHEN** the sample_table has 3 entries and the user triggers execution
- **THEN** the system SHALL execute 3 independent workflow runs, each in `<workspace>/<sample_id>/`

#### Scenario: Incremental batch execution
- **WHEN** a sample's outputs already exist in its workspace directory and `resume` is `true`
- **THEN** the system SHALL skip completed nodes for that sample (existing resume behavior)
