## ADDED Requirements

### Requirement: Sample definition structure
The system SHALL store sample definitions in `samples.json` with a standard structure including id, name, context, data_paths, and metadata.

#### Scenario: Sample definition has required fields
- **WHEN** a sample is defined in `samples.json`
- **THEN** the sample includes `id` field
- **AND** the sample includes `name` field
- **AND** the sample includes `context` field with placeholder values
- **AND** the sample includes `data_paths` field with file path templates

#### Scenario: Sample definition has optional fields
- **WHEN** a sample is defined with additional information
- **THEN** the sample may include `description` field
- **AND** the sample may include `metadata` field with custom properties
- **AND** the sample includes `created_at` timestamp

### Requirement: Add sample to workspace
The system SHALL allow adding new samples to a workspace.

#### Scenario: Add sample successfully
- **WHEN** a user adds a sample with valid data
- **THEN** the system adds the sample to `samples.json`
- **AND** sets `created_at` timestamp
- **AND** updates workspace statistics

#### Scenario: Add sample with duplicate ID
- **WHEN** a user adds a sample with an existing sample_id
- **THEN** the system returns an error
- **AND** does not modify the existing sample

### Requirement: Get sample context
The system SHALL provide sample context for placeholder resolution.

#### Scenario: Get context for existing sample
- **WHEN** a user requests context for an existing sample_id
- **THEN** the system returns the sample's context dictionary
- **AND** the context includes all placeholder values defined in the sample

#### Scenario: Get context for non-existent sample
- **WHEN** a user requests context for a non-existent sample_id
- **THEN** the system returns `None`
- **AND** does not raise an exception

### Requirement: List samples
The system SHALL allow listing all samples in a workspace.

#### Scenario: List samples successfully
- **WHEN** a user lists samples in a workspace
- **THEN** the system returns an array of sample definitions
- **AND** each sample includes all fields from `samples.json`

#### Scenario: List samples in empty workspace
- **WHEN** a user lists samples in a workspace with no samples
- **THEN** the system returns an empty array
- **AND** does not raise an error

### Requirement: Update sample
The system SHALL allow updating existing samples.

#### Scenario: Update sample successfully
- **WHEN** a user updates a sample with valid data
- **THEN** the system updates the sample in `samples.json`
- **AND** updates the `updated_at` timestamp
- **AND** preserves fields that were not updated

#### Scenario: Update non-existent sample
- **WHEN** a user tries to update a non-existent sample
- **THEN** the system returns an error
- **AND** does not create a new sample

### Requirement: Delete sample
The system SHALL allow deleting samples from a workspace.

#### Scenario: Delete sample successfully
- **WHEN** a user deletes a sample
- **THEN** the system removes the sample from `samples.json`
- **AND** updates workspace statistics
- **AND** returns success confirmation

#### Scenario: Delete non-existent sample
- **WHEN** a user tries to delete a non-existent sample
- **THEN** the system returns an error
- **AND** does not modify `samples.json`

### Requirement: Sample context merging
The system SHALL merge explicit context values with auto-derived values.

#### Scenario: Explicit value takes precedence
- **WHEN** a sample explicitly defines `input_basename: "custom_name"`
- **AND** the system would derive `input_basename: "file1"` from input files
- **THEN** the system uses `"custom_name"` as the context value
- **AND** does NOT override with the derived value

#### Scenario: Derived value used when not explicit
- **WHEN** a sample does NOT define `input_basename`
- **AND** input files are available
- **THEN** the system derives `input_basename` from input files
- **AND** adds it to the context

### Requirement: Sample data paths with placeholders
The system SHALL support placeholders in sample data path templates.

#### Scenario: Resolve data path with sample placeholder
- **WHEN** a sample has data path `results/{sample}.mzML`
- **AND** the sample_id is `sample1`
- **THEN** the resolved path is `results/sample1.mzML`

#### Scenario: Resolve data path with multiple placeholders
- **WHEN** a sample has data path `{sample}_{input_basename}_processed.tsv`
- **AND** context is `{sample: "s1", input_basename: "raw1"}`
- **THEN** the resolved path is `s1_raw1_processed.tsv`
