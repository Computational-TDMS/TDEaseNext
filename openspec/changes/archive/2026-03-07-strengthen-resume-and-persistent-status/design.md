## Context

Execution APIs currently read state from an in-memory registry first, which is fast but fragile under restart or multi-instance deployment. Resume skip policy marks a node complete when any output path exists, which is too permissive for tools with required subsets of outputs.

## Goals / Non-Goals

**Goals:**
- Make execution and node status queryable after restart via persistent storage fallback.
- Enforce strict resume completion using required output definitions or explicit completion manifests.
- Keep cancellation/status transitions internally consistent between memory and storage.

**Non-Goals:**
- Building a distributed scheduler in this change.
- Replacing SQLite with a different persistence backend.
- Redesigning all execution API payload models.

## Decisions

1. **Status read-through fallback**
   - Decision: Query in-memory registry first, then persistent execution store when memory misses.
   - Rationale: Preserves fast path while supporting restart durability.
   - Alternative considered: DB-only reads; rejected for unnecessary overhead during active execution.

2. **Resume manifest/required-output policy**
   - Decision: Determine node resumability from required outputs (or node completion manifest), not from any existing artifact.
   - Rationale: Prevents false positives when only optional or partial files exist.
   - Alternative considered: keep any-output rule with exceptions; rejected due to complexity and hidden mis-skips.

3. **Consistent transition reconciliation**
   - Decision: Reconcile execution/node status transitions with persistent records as source of truth for terminal states.
   - Rationale: Avoids drift between in-memory and persisted statuses.
   - Alternative considered: memory authoritative model; rejected for restart fragility.

## Risks / Trade-offs

- [More DB reads can affect API latency] -> Mitigation: use fallback only on cache miss and index key queries.
- [Required-output metadata may be incomplete for some tools] -> Mitigation: provide explicit migration defaults and validation warnings.
- [State reconciliation can expose existing data inconsistencies] -> Mitigation: add repair path for malformed terminal states.

## Migration Plan

1. Add status fallback query path in execution APIs.
2. Introduce stricter resume completion evaluator using required outputs/manifest.
3. Backfill or validate tool metadata needed for required-output checks.
4. Add restart and partial-output regression tests.

Rollback:
- Revert resume policy to previous behavior behind temporary flag while preserving status fallback improvements.

## Open Questions

- Should node completion manifests be mandatory for tools with conditional outputs?
- Do we need a background reconciliation job for stale running states after unclean shutdown?
