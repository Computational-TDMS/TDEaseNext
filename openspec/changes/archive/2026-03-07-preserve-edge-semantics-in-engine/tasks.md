## 1. Normalization Semantics

- [x] 1.1 Preserve `connectionKind` and `semanticType` in normalized edge objects.
- [x] 1.2 Implement backward-compatible defaults for workflows that omit semantic fields.

## 2. Graph and Scheduler Behavior

- [x] 2.1 Refactor graph dependency construction to use typed-edge filtering.
- [x] 2.2 Exclude `state` edges from readiness predecessor checks.
- [x] 2.3 Ensure non-dependency edges remain available in graph metadata/traces.

## 3. Validation and Regression Tests

- [x] 3.1 Add unit tests for normalizer semantic preservation.
- [x] 3.2 Add integration tests for mixed data/state workflow execution order.
- [x] 3.3 Update architecture docs with typed-edge dependency rules.
