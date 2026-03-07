## Why

Execution currently composes command strings and relies on shell interpretation in key paths, which expands the attack surface for command injection and inconsistent quoting behavior. Security-sensitive systems need argument-safe process execution and sanitized external error responses.

## What Changes

- Replace shell-string execution paths with argument-vector execution where feasible.
- Enforce executable and workspace validation before process launch.
- Standardize secure logging/redaction for execution errors returned through APIs.
- Add security-focused tests for injection, quoting, and path traversal cases.

## Capabilities

### New Capabilities
- `secure-command-execution`: Enforce shell-safe command execution, launch-time validation, and sanitized error exposure.

### Modified Capabilities
- None.

## Impact

- `app/core/executor/local.py`, `app/core/executor/shell_runner.py`, and related process-launch logic.
- API exception handling and error payload formatting.
- Test coverage for malicious parameter and path edge cases.
