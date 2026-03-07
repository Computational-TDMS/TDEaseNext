## Context

The system supports interactive viewers and state propagation (`state/selection_ids`) in parallel with compute execution. However, normalization currently narrows edge shape to source/target/handles, and graph dependency construction does not consistently account for semantic edge kind.

## Goals / Non-Goals

**Goals:**
- Preserve edge semantic fields end-to-end in normalized workflow representations.
- Ensure scheduler dependency logic uses only dependency-bearing edge kinds.
- Maintain state edge visibility for APIs and downstream interaction logic.

**Non-Goals:**
- Implementing a new front-end graph editor protocol.
- Changing the meaning of existing `state/selection_ids` payloads.
- Adding new state transport infrastructure.

## Decisions

1. **Normalize with semantic field retention**
   - Decision: Keep `connectionKind` and `semanticType` in normalized edges.
   - Rationale: Semantic data must survive transformation boundaries.
   - Alternative considered: Re-derive semantics from handles; rejected as brittle and lossy.

2. **Type-aware dependency graph construction**
   - Decision: Include only `data` and `control` edges as scheduler predecessors; exclude `state`.
   - Rationale: State edges convey interaction context, not compute prerequisites.
   - Alternative considered: Keep all edges as dependencies; rejected because it can block or deadlock mixed workflows.

3. **Preserve non-dependency edges for traceability**
   - Decision: Keep state edges in graph metadata and execution traces even when excluded from scheduling dependencies.
   - Rationale: APIs and debugging still need full topology context.
   - Alternative considered: Drop state edges after scheduling; rejected due to observability loss.

## Risks / Trade-offs

- [Legacy workflows missing `connectionKind` could be misclassified] -> Mitigation: define backward-compatible default (`data`) when absent.
- [More edge metadata handling increases model complexity] -> Mitigation: centralize typed-edge helpers and add focused tests.
- [Control edge semantics may evolve] -> Mitigation: reserve extension points and document behavior explicitly.

## Migration Plan

1. Update normalizer to preserve semantic fields with backward-compatible defaults.
2. Refactor graph dependency construction to consume typed-edge semantics.
3. Add integration tests for mixed data/state topologies.
4. Update docs describing dependency-bearing edge kinds.

Rollback:
- Revert typed-edge dependency filtering while keeping metadata retention if regressions appear.

## Open Questions

- Should `control` edges be enabled immediately or staged behind a feature flag?
- Do we need API-level validation that blocks unknown edge kinds?
