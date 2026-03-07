## 1. Contract Validation

- [x] 1.1 Implement required-port validation in the input planning pipeline.
- [x] 1.2 Add deterministic ambiguity detection for required single-input ports.
- [x] 1.3 Standardize planner error payloads for missing and ambiguous bindings.

## 2. Execution Integration

- [x] 2.1 Ensure workflow execution fails node before command assembly on contract violations.
- [x] 2.2 Persist binding diagnostics into execution/node trace records.
- [x] 2.3 Expose contract-validation errors consistently through execution APIs.

## 3. Tests and Documentation

- [x] 3.1 Add unit tests for missing-required-input and ambiguity scenarios.
- [x] 3.2 Add integration tests proving no command execution occurs after contract failure.
- [x] 3.3 Document strict required-input behavior and migration guidance for legacy workflows.
