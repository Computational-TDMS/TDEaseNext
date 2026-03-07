## Context

The backend execution path supports real tools (TopFD/TopPIC), but most automated checks currently validate only mock tools. In parallel, local runtime artifact folders can be accidentally discovered by pytest, causing permission-related collection failures and reducing confidence in test outcomes.

## Goals / Non-Goals

**Goals:**
- Make repository-level pytest collection deterministic and immune to transient runtime directories.
- Introduce a production smoke lane that validates the real compute chain with minimal fixtures.
- Keep smoke execution optional and clearly gated so standard development loops remain fast.

**Non-Goals:**
- Full benchmark/performance testing of real tools.
- Replacing existing mock integration tests.
- Reworking the entire CI matrix in this change.

## Decisions

1. **Add an explicit smoke marker and lane**
   - Decision: Create a dedicated smoke suite for real-tool readiness.
   - Rationale: Separates readiness checks from fast regression checks.
   - Alternative considered: Merge into existing integration tests; rejected due to environment coupling and slower default runs.

2. **Enforce strict test collection boundaries**
   - Decision: Use discovery filters to ignore transient runtime directories and permission-sensitive artifact paths.
   - Rationale: Collection instability is a test infrastructure issue and should be fixed centrally.
   - Alternative considered: Developer-only cleanup scripts; rejected because it does not prevent CI noise.

3. **Use prerequisite-aware skips for smoke tests**
   - Decision: Skip smoke tests with explicit reason when executables or fixtures are missing.
   - Rationale: Keeps developer experience predictable while preserving visibility into readiness gaps.
   - Alternative considered: Hard fail on missing tools; rejected because not all environments are provisioned equally.

## Risks / Trade-offs

- [Smoke suite drifts from real deployment assumptions] -> Mitigation: Keep fixture/tool path assumptions documented and reviewed with deployment changes.
- [Marker overuse can hide gaps] -> Mitigation: Keep `prod_smoke` scope narrow and enforce one canonical command in docs/CI.
- [Collection filters hide unintended test files] -> Mitigation: Restrict ignore rules to known runtime artifact patterns and review periodically.

## Migration Plan

1. Introduce collection filters and validate that baseline test selection is unchanged for committed tests.
2. Add smoke tests and helper gating utilities.
3. Wire CI command for smoke lane in provisioned environments.
4. Update docs and announce commands to contributors.

Rollback:
- Remove smoke lane from CI and revert discovery filter changes if broad regressions appear.

## Open Questions

- Which environment(s) will be the canonical smoke execution target for CI?
- Should smoke fixtures be versioned in-repo or pulled from managed artifact storage?
