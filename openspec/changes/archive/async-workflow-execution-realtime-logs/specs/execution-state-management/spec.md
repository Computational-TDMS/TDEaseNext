# Capability: Execution State Management

## ADDED Requirements

### Requirement: In-memory execution registry
The system SHALL maintain an in-memory registry of all active executions accessible by `execution_id`.

#### Scenario: Create execution record
- **WHEN** workflow execution is submitted
- **THEN** system creates execution record in memory
- **AND** record includes: `executionId`, `workflowId`, `workspace`, `status`, `startTime`, `progress`, `logs[]`
- **AND** record is retrievable via `GET /api/executions/{execution_id}`

#### Scenario: Retrieve execution state
- **WHEN** client requests execution status via `GET /api/executions/{execution_id}`
- **THEN** system returns current execution state
- **AND** response includes all execution metadata and logs collected so far

### Requirement: Progress tracking
The system SHALL track and update execution progress percentage during workflow execution.

#### Scenario: Progress initialization
- **WHEN** execution starts
- **THEN** system initializes progress to `0`

#### Scenario: Progress updates during execution
- **WHEN** workflow node completes execution
- **THEN** system calculates progress based on completed nodes vs total nodes
- **AND** system updates progress value in execution record
- **AND** progress is integer between 0 and 100

### Requirement: Node-level status tracking
The system SHALL track execution status for individual nodes within workflow.

#### Scenario: Node status updates
- **WHEN** node execution begins
- **THEN** system creates node status record with status `running`
- **WHEN** node execution completes successfully
- **THEN** system updates node status to `completed`
- **AND** system stores `endTime` for node
- **WHEN** node execution fails
- **THEN** system updates node status to `failed`
- **AND** system stores error message for node

#### Scenario: Retrieve node statuses
- **WHEN** client requests `GET /api/executions/{execution_id}/nodes`
- **THEN** system returns array of all node statuses
- **AND** each node status includes: `nodeId`, `status`, `progress`, `startTime`, `endTime`, `errorMessage`

### Requirement: Execution cleanup
The system SHALL automatically cleanup completed execution records after a timeout period.

#### Scenario: Cleanup after completion
- **WHEN** execution completes (status: `completed`, `failed`, or `cancelled`)
- **THEN** system schedules cleanup for 1 hour later
- **AND** system removes execution record from memory after timeout
- **AND** system removes log handler for execution

#### Scenario: Manual cleanup before timeout
- **WHEN** system needs memory before cleanup timeout
- **THEN** system may cleanup least-recently-used completed executions
- **AND** system logs cleanup action

### Requirement: Concurrent execution support
The system SHALL support multiple concurrent workflow executions.

#### Scenario: Multiple simultaneous executions
- **WHEN** multiple clients submit workflow executions simultaneously
- **THEN** system creates separate execution record for each
- **AND** each execution runs independently
- **AND** logs are not interleaved between executions
- **AND** each execution has unique `execution_id`

### Requirement: Execution state persistence
The system SHALL persist execution metadata to database for audit trail.

#### Scenario: Database record creation
- **WHEN** execution is created
- **THEN** system creates database record in `executions` table
- **AND** record includes: `execution_id`, `workflow_id`, `workspace`, `status`, `start_time`
- **AND** database record persists after in-memory cleanup

#### Scenario: Database record update on completion
- **WHEN** execution completes
- **THEN** system updates database record with: `end_time`, `status`, `error_message` (if failed)

### Requirement: Execution isolation
The system SHALL ensure logs and state are isolated between concurrent executions.

#### Scenario: Log isolation
- **WHEN** two executions run simultaneously
- **AND** execution A generates log message
- **THEN** log is associated only with execution A
- **AND** execution B's log retrieval does not include execution A's logs

#### Scenario: State isolation
- **WHEN** two executions run simultaneously
- **THEN** each execution has independent state
- **AND** status changes in one execution do not affect the other
