# Process Registry Specification

## ADDED Requirements

### Requirement: Process registry tracks running child processes

The system SHALL provide a global process registry that maintains a mapping from task identifiers to running child processes. The registry MUST be thread-safe to support concurrent workflow executions.

#### Scenario: Register a new process

- **WHEN** a child process is started using `subprocess.Popen`
- **THEN** the system SHALL register the process in the registry using the task_id
- **AND** the registry SHALL store the mapping from task_id to the Popen object
- **AND** the registration operation MUST be thread-safe

#### Scenario: Unregister a process on exit

- **WHEN** a child process exits (normally or terminated)
- **THEN** the system SHALL remove the process from the registry
- **AND** the unregistration operation MUST be thread-safe
- **AND** the system SHALL use a try-finally block to ensure unregistration always occurs

#### Scenario: Concurrent registrations

- **WHEN** multiple threads attempt to register processes simultaneously
- **THEN** the registry SHALL handle all registrations without race conditions
- **AND** all processes SHALL be correctly registered
- **AND** no registrations SHALL be lost

### Requirement: Process registry provides cancellation capability

The process registry SHALL provide a method to cancel a registered process. The cancellation MUST use a two-phase approach: SIGTERM followed by SIGKILL if needed.

#### Scenario: Cancel registered process

- **WHEN** `registry.cancel(task_id)` is called
- **AND** the task_id exists in the registry
- **THEN** the registry SHALL retrieve the associated process
- **AND** the registry SHALL call `process.terminate()` (SIGTERM)
- **AND** the registry SHALL wait up to 3 seconds for the process to exit
- **AND** if the process is still running after 3 seconds, the registry SHALL call `process.kill()` (SIGKILL)
- **AND** the registry SHALL return `True`

#### Scenario: Cancel unregistered task

- **WHEN** `registry.cancel(task_id)` is called
- **AND** the task_id does not exist in the registry
- **THEN** the registry SHALL return `False`
- **AND** the registry SHALL NOT raise an exception

#### Scenario: Cancel already exited process

- **WHEN** `registry.cancel(task_id)` is called
- **AND** the process has already exited (poll() returns not None)
- **THEN** the registry SHALL return `True`
- **AND** the registry SHALL NOT attempt to terminate the process
- **AND** the registry SHALL log that the process was already exited

### Requirement: Process registry prevents memory leaks

The system MUST ensure that processes are properly unregistered to prevent memory leaks. The registry SHALL provide cleanup mechanisms and handle edge cases.

#### Scenario: Process exits before unregistration

- **WHEN** a process exits naturally
- **AND** the code attempts to unregister the process
- **THEN** the registry SHALL successfully remove the entry
- **AND** the registry SHALL NOT raise an exception for missing keys

#### Scenario: Double unregistration

- **WHEN** a process is unregistered twice
- **THEN** the second unregistration SHALL succeed silently
- **AND** the registry SHALL NOT raise an exception

#### Scenario: List active processes

- **WHEN** `registry.list_active()` is called
- **THEN** the registry SHALL return a list of all currently registered task_ids
- **AND** the list SHALL only contain processes that are still running
- **AND** the operation MUST be thread-safe

### Requirement: Process registry uses unique task identifiers

The system MUST use unique task identifiers to register processes. The task_id SHALL be a combination of execution_id and node_id in the format `{execution_id}:{node_id}`.

#### Scenario: Generate task_id for node execution

- **WHEN** a node is executed within a workflow
- **THEN** the system SHALL generate a task_id as `{execution_id}:{node_id}`
- **AND** the task_id SHALL be unique across all executions
- **AND** the task_id SHALL be human-readable for debugging purposes

#### Scenario: Multiple nodes in same execution

- **WHEN** a workflow execution has multiple nodes running concurrently
- **THEN** each node SHALL have a unique task_id
- **AND** all task_ids SHALL share the same execution_id prefix
- **AND** the registry SHALL correctly track each process independently

### Requirement: Process registry integrates with ShellRunner

The ShellRunner module MUST integrate with the process registry to automatically register and unregister processes.

#### Scenario: ShellRunner registers process on start

- **WHEN** `_run_with_capture()` creates a subprocess.Popen object
- **THEN** the function SHALL immediately register the process using the provided task_id
- **AND** the registration SHALL occur before the process starts executing

#### Scenario: ShellRunner unregisters process on exit

- **WHEN** the subprocess exits in `_run_with_capture()`
- **THEN** the function SHALL unregister the process in a finally block
- **AND** the unregistration SHALL occur regardless of how the function exits (normal return, exception, etc.)
