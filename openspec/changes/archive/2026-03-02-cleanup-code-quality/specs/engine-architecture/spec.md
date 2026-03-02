## ADDED Requirements

### Requirement: Snakemake removal from database schema
The system SHALL remove all Snakemake-specific columns from database tables.

#### Scenario: Database column rename
- **GIVEN** the executions table contains column `snakemake_args`
- **WHEN** database migration runs
- **THEN** the column SHALL be renamed to `engine_args`
- **AND** the column `snakemake_status` SHALL be removed

### Requirement: Snakemake removal from data models
The system SHALL not contain references to Snakemake in model field definitions or comments.

#### Scenario: Model field name updates
- **WHEN** models define engine-related fields
- **THEN** field names SHALL use `engine_*` prefix (e.g., `engine_args`, `engine_status`)
- **AND** comments SHALL NOT mention "snakemake" or "legacy snakemake"

### Requirement: Snakemake removal from logging
The system SHALL not use "snakemake" as a logger name.

#### Scenario: Logger name update
- **GIVEN** `app/services/log_handler.py` creates logger with name "snakemake"
- **WHEN** the service initializes logging
- **THEN** the logger SHALL use a generic name like "tdease.engine" or "tdease.workflow"

### Requirement: Snakemake removal from WebSocket monitoring
The system SHALL not monitor Snakemake-specific status files via WebSocket.

#### Scenario: WebSocket file monitoring update
- **GIVEN** WebSocket monitors `.snakemake/status` files
- **WHEN** WebSocket status monitoring is implemented
- **THEN** the monitor SHALL track FlowEngine status instead
- **AND** SHALL NOT reference `.snakemake/` directory

### Requirement: Snakemake removal from node mapping
The system SHALL not contain Snakemake rule mapping logic.

#### Scenario: Node mapper update
- **GIVEN** `app/services/node_mapper.py` maps Snakemake rules to frontend nodes
- **WHEN** node mapping is performed
- **THEN** the mapper SHALL translate FlowEngine nodes
- **AND** SHALL NOT contain Snakemake rule references
