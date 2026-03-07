## Why

Workflow normalization currently strips or ignores edge semantic fields that distinguish data flow from state propagation. As a result, scheduler dependency construction can treat non-data edges as execution dependencies, reducing robustness for interactive and mixed-mode workflows.

## What Changes

- Preserve `connectionKind` and `semanticType` through normalization and internal workflow models.
- Build scheduler dependencies only from dependency-bearing edge kinds (`data` and optional `control`), excluding `state`.
- Keep state edge metadata available for APIs, tracing, and interaction systems.
- Add tests covering mixed data/state graphs to prevent regressions.

## Capabilities

### New Capabilities
- `typed-workflow-edge-semantics`: Preserve and enforce edge semantic types across normalization, graph construction, and scheduling.

### Modified Capabilities
- None.

## Impact

- `src/workflow/normalizer.py`, engine graph construction, and scheduler logic.
- Interactive workflow reliability for compute + viewer + state propagation layouts.
- Integration tests around connection semantics.
