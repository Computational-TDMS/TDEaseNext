## Context

The active execution stack uses `app/services/tool_registry.py` and FlowEngine-based execution, while legacy registry and adapter artifacts remain in the codebase. At the same time, some tool configs embed machine-local absolute paths, reducing portability and increasing onboarding/deployment friction.

## Goals / Non-Goals

**Goals:**
- Make tool execution configuration portable across environments using profiles/overrides.
- Enforce validation rules that prevent non-portable shared configuration.
- Remove or isolate legacy code paths that are not part of the active execution architecture.

**Non-Goals:**
- Replacing the entire tool schema format.
- Supporting every historical legacy adapter behavior.
- Building a centralized secret/config service.

## Decisions

1. **Profile-based tool resolution**
   - Decision: Resolve executable paths via environment/profile overlays instead of hardcoded shared absolute paths.
   - Rationale: Allows consistent promotion across dev/staging/prod.
   - Alternative considered: Keep absolute paths with per-machine edits; rejected due to operational drift.

2. **Portable-config enforcement**
   - Decision: Add validation checks that reject non-portable path patterns in shared config files.
   - Rationale: Fails bad configuration early and keeps repository defaults transportable.
   - Alternative considered: Documentation-only guidance; rejected because it does not prevent regressions.

3. **Legacy path cleanup**
   - Decision: Remove or archive duplicate unused registry/adapter logic from active code path.
   - Rationale: Reduces maintenance overhead and architectural ambiguity.
   - Alternative considered: Keep all legacy code indefinitely; rejected due to cognitive and testing cost.

## Risks / Trade-offs

- [Removing legacy paths can break undocumented workflows] -> Mitigation: inventory references and provide migration mapping before removal.
- [Profile layering adds configuration complexity] -> Mitigation: keep one canonical precedence order and provide examples.
- [Strict validation may block existing local setups] -> Mitigation: allow local override files outside version control.

## Migration Plan

1. Introduce profile/override resolution in tool registry loading.
2. Add config validation checks and migration warnings for non-portable paths.
3. Remove or isolate unused legacy registry/adapter entry points.
4. Update docs with environment profile examples and migration steps.

Rollback:
- Re-enable compatibility shim for specific legacy config patterns while migration is completed.

## Open Questions

- Should profile selection be explicit API input, environment variable, or both?
- Which legacy modules should be archived vs fully deleted in this cycle?
