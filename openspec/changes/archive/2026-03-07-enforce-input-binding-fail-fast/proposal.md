## Why

Input binding currently relies on permissive fallback behavior, which can silently skip unresolved inputs and push failures into late execution stages. This creates unclear errors, non-deterministic behavior, and avoidable reruns.

## What Changes

- Introduce strict pre-execution validation for required input ports.
- Add deterministic ambiguity detection when multiple upstream edges compete for a single required input.
- Promote structured binding decisions to first-class execution diagnostics.
- Keep heuristic matching as a controlled fallback only when it cannot violate required contracts.

## Capabilities

### New Capabilities
- `input-binding-contract-validation`: Enforce required input contracts before command execution and produce deterministic binding diagnostics.

### Modified Capabilities
- None.

## Impact

- `app/services/input_binding_planner.py` and `app/services/workflow_service.py`.
- Validation and error propagation in execution APIs and logs.
- Tests for missing-required-input and ambiguous-binding paths.
