## Why

Current workflow validation relies mostly on mock A/B/C tools and does not verify that the real compute chain can run in a controlled environment. Test collection is also unstable because transient runtime directories in the repository can trigger permission errors and non-deterministic failures.

## What Changes

- Add a production smoke test profile that executes a minimal real compute workflow with strict preconditions.
- Harden pytest discovery boundaries so transient directories and runtime artifacts are never collected as tests.
- Add explicit skip behavior for smoke tests when required executables or fixtures are unavailable.
- Update testing documentation and commands to separate fast mock checks from production readiness checks.

## Capabilities

### New Capabilities
- `workflow-production-smoke-testing`: Deterministic test collection and real-tool smoke validation for the compute workflow path.

### Modified Capabilities
- None.

## Impact

- `pytest.ini`, test collection filters, and fixture hygiene in `tests/`.
- New smoke test modules and helper utilities for executable/fixture gating.
- CI test commands and developer docs.
