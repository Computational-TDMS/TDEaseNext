## ADDED Requirements

### Requirement: Extract required placeholders
The system SHALL extract all required placeholders from tool output patterns before workflow execution.

#### Scenario: Extract placeholders from tool
- **WHEN** a tool has output pattern `{sample}_proteoforms.tsv`
- **THEN** the system extracts `sample` as a required placeholder
- **AND** adds it to the required placeholders list

#### Scenario: Extract multiple placeholders
- **WHEN** a tool has output pattern `{sample}_{fasta_filename}_results.tsv`
- **THEN** the system extracts `sample` and `fasta_filename` as required placeholders
- **AND** adds both to the required placeholders list

### Requirement: Validate sample context
The system SHALL validate that sample context contains all required placeholders before workflow execution.

#### Scenario: Validation passes
- **WHEN** a sample context contains all required placeholders
- **THEN** the system allows workflow execution to proceed

#### Scenario: Validation fails with missing placeholder
- **WHEN** a sample context is missing a required placeholder
- **THEN** the system raises a `ValueError`
- **AND** the error message includes the missing placeholder name
- **AND** the error message includes the list of available placeholders

#### Scenario: Validation fails with multiple missing placeholders
- **WHEN** a sample context is missing multiple required placeholders
- **THEN** the system raises a `ValueError`
- **AND** the error message lists all missing placeholders
- **AND** the error message includes the pattern that could not be resolved

### Requirement: Resolve output paths
The system SHALL resolve output file paths by replacing placeholders with actual values from sample context.

#### Scenario: Resolve path successfully
- **WHEN** pattern is `{sample}_proteoforms.tsv` and context has `sample: "sample1"`
- **THEN** the system returns `sample1_proteoforms.tsv`

#### Scenario: Resolve path with multiple placeholders
- **WHEN** pattern is `{sample}_{fasta_filename}_results.tsv` and context has `sample: "sample1", fasta_filename: "db"`
- **THEN** the system returns `sample1_db_results.tsv`

### Requirement: No silent placeholder substitution
The system SHALL NOT silently replace missing placeholders with default values.

#### Scenario: Missing placeholder causes error
- **WHEN** a placeholder in the pattern is not in the sample context
- **THEN** the system raises a `ValueError`
- **AND** does NOT replace the placeholder with "out" or any default value

#### Scenario: All placeholders present
- **WHEN** all placeholders in the pattern are in the sample context
- **THEN** the system resolves the path successfully
- **AND** does NOT use any default value substitution

### Requirement: Auto-derive common context values
The system SHALL automatically derive common context values when not explicitly provided.

#### Scenario: Derive input_basename
- **WHEN** sample context does not include `input_basename`
- **AND** input files are available
- **THEN** the system derives `input_basename` from the first input file's stem
- **AND** adds it to the context

#### Scenario: Derive input_ext
- **WHEN** sample context does not include `input_ext`
- **AND** input files are available
- **THEN** the system derives `input_ext` from the first input file's extension
- **AND** adds it to the context

#### Scenario: Explicit values override derived values
- **WHEN** sample context explicitly defines `input_basename`
- **THEN** the system uses the explicit value
- **AND** does NOT override it with derived values
