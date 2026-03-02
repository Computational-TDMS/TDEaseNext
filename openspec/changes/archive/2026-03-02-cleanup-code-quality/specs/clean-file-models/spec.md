## ADDED Requirements

### Requirement: Single FileInfo model definition
The system SHALL maintain exactly one FileInfo model definition as the source of truth.

#### Scenario: FileInfo consolidation
- **WHEN** the application defines file information models
- **THEN** the system SHALL consolidate FileInfo from `app/models/common.py` and `app/models/files.py`
- **AND** the consolidated model SHALL include fields: id, filename, filepath, size, file_type, metadata, created_at, updated_at

### Requirement: Consistent FileInfo usage
The system SHALL use the consolidated FileInfo model across all modules.

#### Scenario: FileInfo import standardization
- **WHEN** a module requires FileInfo model
- **THEN** the module SHALL import from the single canonical location
- **AND** the module SHALL NOT import FileInfo from multiple locations

### Requirement: Model field completeness
The consolidated FileInfo model SHALL contain all necessary fields from both original models.

#### Scenario: Field preservation during consolidation
- **GIVEN** FileInfo in `app/models/common.py` has created_at, updated_at
- **AND** FileInfo in `app/models/files.py` has file_type, metadata
- **WHEN** models are consolidated
- **THEN** the new FileInfo SHALL include all six fields
