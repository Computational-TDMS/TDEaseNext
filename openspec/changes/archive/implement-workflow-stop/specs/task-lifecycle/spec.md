# Task Lifecycle Management Specification

## ADDED Requirements

### Requirement: TaskSpec includes task identifier

The `TaskSpec` dataclass SHALL include a `task_id` field that uniquely identifies the task for process tracking and cancellation purposes.

#### Scenario: TaskSpec created with task_id

- **WHEN** a `TaskSpec` is created for node execution
- **THEN** the task_id field SHALL be populated as `{execution_id}:{node_id}`
- **AND** the task_id SHALL be a required field (not Optional)

#### Scenario: TaskSpec passed to executor

- **WHEN** `executor.execute(spec)` is called
- **THEN** the executor SHALL use `spec.task_id` for process registration
- **AND** the task_id SHALL be passed to ShellRunner for process tracking

### Requirement: WorkflowService generates task_id for nodes

The WorkflowService SHALL generate unique task identifiers when creating TaskSpec objects for each node in a workflow execution.

#### Scenario: Generate task_id during workflow execution

- **WHEN** WorkflowService executes a workflow
- **AND** a node is ready to execute
- **THEN** the service SHALL generate a task_id as `{execution_id}:{node_id}`
- **AND** the service SHALL create a TaskSpec with the task_id
- **AND** the service SHALL pass the TaskSpec to the executor

#### Scenario: Unique task_id for each node

- **WHEN** a workflow execution has multiple nodes
- **THEN** each node SHALL receive a unique task_id
- **AND** no two nodes SHALL share the same task_id
- **AND** all task_ids SHALL be traceable back to their execution

### Requirement: ExecutionManager tracks executors for cancellation

The ExecutionManager SHALL maintain a mapping from execution_id to Executor instances to enable cancellation of running workflows.

#### Scenario: Executor registered on execution start

- **WHEN** a workflow execution starts
- **THEN** the ExecutionManager SHALL store the Executor instance in `executors[execution_id]`
- **AND** the Executor SHALL remain available for the duration of the execution

#### Scenario: Executor retrieved for cancellation

- **WHEN** `ExecutionManager.stop(execution_id)` is called
- **AND** the execution has a registered executor
- **THEN** the manager SHALL retrieve the executor instance
- **AND** the manager SHALL call the executor's cancel method for each running node

#### Scenario: Executor unregistered on completion

- **WHEN** a workflow execution completes (success, failure, or cancellation)
- **THEN** the ExecutionManager SHALL remove the executor from the executors dictionary
- **AND** the memory SHALL be freed

### Requirement: Cancellation propagates to database

When a workflow execution is cancelled, the system MUST update the database to reflect the new status of the execution and its nodes.

#### Scenario: Execution status updated to cancelled

- **WHEN** `ExecutionManager.stop(execution_id)` successfully cancels an execution
- **THEN** the manager SHALL call `ExecutionStore.finish()` with status "cancelled"
- **AND** the database SHALL reflect the execution status as "cancelled"
- **AND** the end_time SHALL be recorded

#### Scenario: Running node statuses updated to cancelled

- **WHEN** a workflow execution is cancelled
- **AND** nodes are currently running
- **THEN** the system SHALL call `ExecutionStore.update_node_status()` with status "cancelled" for each running node
- **AND** the database SHALL reflect the node statuses as "cancelled"
- **AND** the end_time SHALL be recorded for each node

#### Scenario: Cancellation logged

- **WHEN** a workflow execution is cancelled
- **THEN** the system SHALL log a warning message indicating the execution was cancelled
- **AND** the log SHALL include the execution_id
- **AND** the log SHALL include a timestamp

### Requirement: Cancellation is idempotent

The cancellation operation SHALL be idempotent, meaning multiple calls to cancel the same execution SHALL be safe and produce the same result.

#### Scenario: Cancel already cancelled execution

- **WHEN** `stop(execution_id)` is called on an already cancelled execution
- **THEN** the system SHALL return success without error
- **AND** the system SHALL NOT modify the database status
- **AND** the system SHALL log that the execution was already cancelled

#### Scenario: Cancel completed execution

- **WHEN** `stop(execution_id)` is called on a completed execution
- **THEN** the system SHALL return success without error
- **AND** the system SHALL NOT modify the database status
- **AND** the system SHALL log that the execution was already completed

### Requirement: Task lifecycle states are consistent

The system MUST maintain consistency between the process registry, the ExecutionManager, and the database throughout the task lifecycle.

#### Scenario: Process registered, status running

- **WHEN** a task starts executing
- **THEN** the process SHALL be registered in the process registry
- **AND** the node status in the database SHALL be "running"
- **AND** the ExecutionManager SHALL have the executor instance

#### Scenario: Process unregistered, status completed

- **WHEN** a task completes successfully
- **THEN** the process SHALL be unregistered from the process registry
- **AND** the node status in the database SHALL be "completed"
- **AND** the executor instance SHALL remain in ExecutionManager until workflow completes

#### Scenario: Process cancelled, status cancelled

- **WHEN** a task is cancelled
- **THEN** the process SHALL be terminated
- **AND** the process SHALL be unregistered from the process registry
- **AND** the node status in the database SHALL be "cancelled"
- **AND** the execution status in the database SHALL be "cancelled" (if all nodes cancelled/failed/completed)
