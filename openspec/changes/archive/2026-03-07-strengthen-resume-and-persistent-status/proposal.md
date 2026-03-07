## Why

Execution lifecycle visibility currently depends heavily on in-memory state, so status lookup can fail after process restarts or across multiple instances. Resume behavior also treats any existing output as completion, which can incorrectly skip nodes with partial artifacts.

## What Changes

- Add durable execution-status lookup behavior that falls back to persistent storage.
- Replace permissive resume checks with required-output/manifest-based completion logic.
- Ensure node-level status transitions remain consistent across restart scenarios.
- Add regression tests for restart-aware status queries and partial-output resume cases.

## Capabilities

### New Capabilities
- `durable-execution-state-and-resume`: Persistent execution status retrieval and strict resume correctness for partial outputs.

### Modified Capabilities
- None.

## Impact

- `app/services/runner.py`, execution APIs, and `app/services/workflow_service.py` resume checks.
- Execution/node persistence interactions in `ExecutionStore`.
- Integration tests covering restart and partial-output edge cases.
