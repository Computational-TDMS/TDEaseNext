# Workflow Cancellation Specification

## ADDED Requirements

### Requirement: User can cancel a running workflow execution

The system SHALL provide an API endpoint that allows users to cancel a running workflow execution. When cancelled, the system MUST terminate all running child processes associated with the execution and update the execution status to "cancelled" in the database.

#### Scenario: Successful workflow cancellation

- **WHEN** user sends a POST request to `/api/executions/{execution_id}/stop` for a running execution
- **THEN** the system SHALL terminate all running child processes for nodes in that execution
- **AND** the system SHALL update the execution status to "cancelled" in the database
- **AND** the system SHALL update all running node statuses to "cancelled"
- **AND** the system SHALL return a 200 OK response with success message

#### Scenario: Cancel already completed execution

- **WHEN** user sends a POST request to `/api/executions/{execution_id}/stop` for an execution that is already completed
- **THEN** the system SHALL return a 200 OK response
- **AND** the system SHALL NOT modify the execution status
- **AND** the system SHALL log that the execution was already completed

#### Scenario: Cancel non-existent execution

- **WHEN** user sends a POST request to `/api/executions/{execution_id}/stop` for a non-existent execution
- **THEN** the system SHALL return a 404 Not Found response
- **AND** the system SHALL return an error message indicating the execution was not found

### Requirement: System terminates child processes on cancellation

The system MUST terminate all running child processes when a workflow execution is cancelled. Termination SHALL use a two-phase approach: first send SIGTERM (terminate), wait up to 3 seconds, then send SIGKILL (kill) if the process is still running.

#### Scenario: Graceful termination with SIGTERM

- **WHEN** a child process receives SIGTERM during workflow cancellation
- **AND** the process exits within 3 seconds
- **THEN** the system SHALL NOT send SIGKILL
- **AND** the system SHALL log that the process was terminated gracefully

#### Scenario: Forced termination with SIGKILL

- **WHEN** a child process does not exit within 3 seconds after SIGTERM
- **THEN** the system SHALL send SIGKILL to force terminate the process
- **AND** the system SHALL log that the process was force killed

#### Scenario: Multiple processes terminated in parallel

- **WHEN** a workflow execution has multiple running nodes
- **AND** the user cancels the execution
- **THEN** the system SHALL attempt to terminate all running processes
- **AND** the system SHALL handle each process independently (one failing to terminate shall not affect others)

### Requirement: Cancellation updates node statuses

The system MUST update the status of all nodes in a workflow execution when the execution is cancelled. Nodes that are running SHALL be marked as "cancelled". Nodes that are pending, completed, or failed SHALL retain their current status.

#### Scenario: Running nodes marked as cancelled

- **WHEN** a workflow execution is cancelled
- **AND** a node is currently running (status = "running")
- **THEN** the system SHALL update the node status to "cancelled" in the database
- **AND** the system SHALL record the end_time for the node

#### Scenario: Completed nodes retain status

- **WHEN** a workflow execution is cancelled
- **AND** a node has already completed (status = "completed")
- **THEN** the system SHALL NOT modify the node status
- **AND** the node SHALL remain as "completed"

#### Scenario: Pending nodes retain status

- **WHEN** a workflow execution is cancelled
- **AND** a node has not yet started (status = "pending")
- **THEN** the system SHALL NOT modify the node status
- **AND** the node SHALL remain as "pending"

### Requirement: Executor cancel method implementation

The system SHALL implement the `cancel()` method on the `Executor` interface. `LocalExecutor` MUST use the process registry to locate and terminate processes. `MockExecutor` MUST return `True` to simulate successful cancellation.

#### Scenario: LocalExecutor cancels process

- **WHEN** `LocalExecutor.cancel(task_id)` is called
- **AND** the task_id is registered in the process registry
- **THEN** the executor SHALL retrieve the process from the registry
- **AND** the executor SHALL terminate the process using two-phase termination
- **AND** the executor SHALL return `True` on success

#### Scenario: LocalExecutor cancels unknown task

- **WHEN** `LocalExecutor.cancel(task_id)` is called
- **AND** the task_id is not found in the process registry
- **THEN** the executor SHALL return `False`
- **AND** the executor SHALL log that the task was not found

#### Scenario: MockExecutor simulates cancellation

- **WHEN** `MockExecutor.cancel(task_id)` is called
- **THEN** the executor SHALL return `True`
- **AND** the executor SHALL NOT perform any actual process termination
