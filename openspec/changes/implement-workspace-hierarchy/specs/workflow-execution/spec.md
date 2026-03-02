## MODIFIED Requirements

### Requirement: Load sample context from workspace
The system SHALL load sample context from the workspace's `samples.json` file during workflow execution.

#### Scenario: Load context for single sample
- **WHEN** a workflow is executed for a single sample
- **THEN** the system loads the sample's context from `samples.json`
- **AND** uses the context for placeholder resolution

#### Scenario: Load context for multiple samples
- **WHEN** a workflow is executed for multiple samples
- **THEN** the system loads each sample's context from `samples.json`
- **AND** creates an isolated execution context for each sample

### Requirement: Validate placeholders before execution
The system SHALL validate all required placeholders before starting workflow execution.

#### Scenario: Validation passes
- **WHEN** all required placeholders are present in sample contexts
- **THEN** the system proceeds with workflow execution

#### Scenario: Validation fails
- **WHEN** any required placeholder is missing from sample contexts
- **THEN** the system raises a `ValueError` before execution starts
- **AND** the error message lists missing placeholders
- **AND** no execution resources are consumed

### Requirement: Create isolated execution directory
The system SHALL create an isolated directory for each workflow execution.

#### Scenario: Create execution directory
- **WHEN** a workflow execution starts
- **THEN** the system creates `executions/{execution_id}/` directory
- **AND** creates subdirectories: `inputs/`, `outputs/`, `logs/`
- **AND** creates `execution.json` with execution metadata

#### Scenario: Execution directory naming
- **WHEN** creating an execution directory
- **THEN** the directory name follows the format `exec_YYYYMMDD_HHMMSS`
- **OR** the directory name includes a unique identifier

### Requirement: Execute workflow per sample
The system SHALL execute the workflow independently for each sample.

#### Scenario: Single sample execution
- **WHEN** a workflow is executed for one sample
- **THEN** the system creates one execution directory
- **AND** executes the workflow with the sample's context
- **AND** stores results in the execution directory

#### Scenario: Multiple sample execution
- **WHEN** a workflow is executed for multiple samples
- **THEN** the system creates one execution directory per sample
- **AND** executes each sample independently with its context
- **AND** stores each sample's results in its execution directory

### Requirement: Parallel sample execution
The system SHALL support parallel execution of multiple samples.

#### Scenario: Parallel execution enabled
- **WHEN** parallel execution is enabled and multiple samples are provided
- **THEN** the system executes samples concurrently
- **AND** respects the configured resource limits (cores, memory)

#### Scenario: Parallel execution disabled
- **WHEN** parallel execution is disabled
- **THEN** the system executes samples sequentially
- **AND** each sample starts after the previous one completes

### Requirement: Store execution metadata
The system SHALL store execution metadata in `execution.json`.

#### Scenario: Execution metadata is created
- **WHEN** an execution starts
- **THEN** the system creates `execution.json` with:
  - `execution_id`: unique identifier
  - `workflow_id`: workflow being executed
  - `workspace_id`: workspace containing the workflow
  - `samples`: list of sample IDs being executed
  - `status`: current execution status
  - `created_at`: execution start timestamp
  - `parameters`: execution parameters

#### Scenario: Execution metadata is updated
- **WHEN** an execution completes or fails
- **THEN** the system updates `execution.json` with:
  - `status`: final status (completed/failed)
  - `completed_at`: completion timestamp
  - `error_message`: error details if failed
