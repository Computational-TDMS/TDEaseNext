## Context

The execution pipeline supports multiple tool modes and currently converts command parts into shell strings before process launch in several paths. This behavior can be correct for many cases but is not the safest default and makes quoting behavior platform-dependent.

## Goals / Non-Goals

**Goals:**
- Execute tool commands without shell interpretation by default.
- Validate executable path, working directory, and launch contract before spawn.
- Prevent internal exception details from leaking in public API responses.

**Non-Goals:**
- Replacing all process-management abstractions.
- Introducing sandbox/container isolation in this change.
- Full threat-model coverage of every third-party tool binary.

## Decisions

1. **Use argument-vector process launch as default**
   - Decision: Launch subprocesses with explicit argument arrays and `shell=False` for standard execution paths.
   - Rationale: Eliminates shell expansion and reduces injection vectors.
   - Alternative considered: Keep shell launch with stronger quoting; rejected due to residual shell semantics risk.

2. **Pre-launch validation gate**
   - Decision: Validate executable resolution and workspace boundaries before spawn.
   - Rationale: Fails unsafe requests early with consistent diagnostics.
   - Alternative considered: Validate only at API boundary; rejected because internal calls can still bypass API paths.

3. **Error redaction policy**
   - Decision: Return stable error codes/messages externally; keep detailed trace in internal logs.
   - Rationale: Preserves debuggability without exposing implementation internals.
   - Alternative considered: Return raw exception details; rejected due to disclosure risk.

## Risks / Trade-offs

- [Some tools depend on shell-only syntax] -> Mitigation: isolate and explicitly mark exceptional launch paths.
- [Windows command behavior may differ after shell removal] -> Mitigation: add platform-specific tests for quoting and paths.
- [Less detailed API errors may slow debugging] -> Mitigation: include correlation ids and richer internal logs.

## Migration Plan

1. Introduce argument-vector launch path and validation utilities.
2. Migrate default local executor path to validated `shell=False` launches.
3. Add secure error mapping in API layer.
4. Add regression and security tests (injection, traversal, quoting).

Rollback:
- Temporarily re-enable shell mode behind explicit feature flag for blocked tools while fixes are prepared.

## Open Questions

- Which specific tools (if any) still require shell features and should be grandfathered?
- Should secure launch mode be configurable per tool or globally enforced?
