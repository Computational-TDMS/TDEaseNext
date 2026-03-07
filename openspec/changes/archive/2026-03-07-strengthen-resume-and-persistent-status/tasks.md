## 1. Durable Status Retrieval

- [x] 1.1 Implement execution API read-through fallback from memory to persistent store.
- [x] 1.2 Add node status fallback retrieval for execution detail endpoints.
- [x] 1.3 Add tests for status queries after simulated process restart.

## 2. Resume Correctness

- [x] 2.1 Implement required-output or manifest-based resume completion evaluator.
- [x] 2.2 Replace permissive any-output skip logic in workflow execution path.
- [x] 2.3 Add tests for partial-output and conditional-output resume scenarios.

## 3. State Reconciliation and Docs

- [x] 3.1 Reconcile terminal state precedence between in-memory and persisted records.
- [x] 3.2 Add regression tests for cancelled/completed/failed terminal consistency.
- [x] 3.3 Update docs describing restart behavior and resume criteria.
