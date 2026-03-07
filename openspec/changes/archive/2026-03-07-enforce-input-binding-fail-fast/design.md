## Context

The planner can bind edges using heuristics across handle/dataType/extension signals. This flexibility helps legacy flows but currently allows required ports to remain unbound without immediate hard failure, causing command construction to proceed with incomplete input maps.

## Goals / Non-Goals

**Goals:**
- Fail fast when required inputs are missing or ambiguous.
- Keep binding behavior deterministic and explainable.
- Preserve useful fallback behavior only for non-required or unambiguous cases.

**Non-Goals:**
- Replacing all existing heuristic scoring logic.
- Introducing a new workflow schema format in this change.
- Redesigning tool JSON authoring UX.

## Decisions

1. **Add a binding contract validation stage before TaskSpec execution**
   - Decision: Validate required input ports per target tool before command assembly.
   - Rationale: Prevents partial command execution attempts with predictable error codes.
   - Alternative considered: Let command pipeline detect missing inputs; rejected because errors appear too late and lack edge-level context.

2. **Treat ambiguous required bindings as errors**
   - Decision: If multiple candidate outputs compete for a single required non-multi input, fail with explicit ambiguity diagnostics.
   - Rationale: Avoids hidden winner selection that can differ by edge order.
   - Alternative considered: Highest-score auto-pick for all cases; rejected for required contracts.

3. **Persist binding decision traces**
   - Decision: Include accepted/rejected decisions with reasons in node execution trace payloads.
   - Rationale: Makes troubleshooting and test assertions straightforward.
   - Alternative considered: Log-only tracing; rejected because logs are harder to query and assert in API tests.

## Risks / Trade-offs

- [Stricter validation may break previously passing loose workflows] -> Mitigation: Return precise remediation guidance in errors and document required-port behavior.
- [More validation logic increases planner complexity] -> Mitigation: Keep validator as a focused stage with unit tests around edge cases.
- [Legacy tools lacking explicit port metadata may fail more often] -> Mitigation: provide transitional defaults only for non-required ports.

## Migration Plan

1. Add required-port validator and ambiguity checks in planner/service pipeline.
2. Wire structured binding diagnostics into execution trace storage.
3. Expand tests for missing-required-input and ambiguous binding scenarios.
4. Update docs to define strict input contract behavior.

Rollback:
- Revert validator enforcement and keep diagnostics-only mode if severe compatibility breakage appears.

## Open Questions

- Should tools explicitly declare `multiInput` semantics in schema, or infer from existing fields?
- Do we need compatibility flags for specific legacy workflow IDs during rollout?
