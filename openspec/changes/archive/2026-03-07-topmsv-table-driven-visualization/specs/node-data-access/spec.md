## MODIFIED Requirements

### Requirement: Tabular file parsing
The system SHALL parse tab-separated and comma-separated text files into structured column/row format, including TSV files that contain non-tabular preamble blocks.

#### Scenario: Parse standard TSV file
- **WHEN** parsing a file with extension `.tsv`, `.txt`, `.ms1ft`, or `.feature` and the first non-empty line is a tabular header
- **THEN** the system SHALL use that header line as columns and parse subsequent tab-separated lines as data rows

#### Scenario: Parse TopPIC TSV with parameter preamble
- **WHEN** parsing a `.tsv` file whose leading lines are parameter banners or key-value metadata before the true tabular header
- **THEN** the system SHALL skip the preamble and detect the first valid tabular header line
- **AND** parse all following tab-separated records under that detected header

#### Scenario: TSV header cannot be detected
- **WHEN** parsing a TSV-like file where no valid tabular header can be detected after preamble skipping
- **THEN** the system SHALL mark the output as `parseable: false`
- **AND** return `data: null` without failing the entire node data response

#### Scenario: Parse CSV file
- **WHEN** parsing a file with extension `.csv`
- **THEN** the system SHALL treat the first line as column headers and subsequent lines as data rows, using comma (`,`) as delimiter

#### Scenario: Non-parseable file format
- **WHEN** the file extension is `.pbf`, `.raw`, `.mzml`, `.png`, `.jpg`, `.fasta`, or other binary format
- **THEN** the system SHALL mark the output as `parseable: false` and return `data: null`
