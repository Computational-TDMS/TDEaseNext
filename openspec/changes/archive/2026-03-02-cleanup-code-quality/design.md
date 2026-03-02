## Context

The TDEase-Backend codebase was originally built with Snakemake as its workflow engine. After decoupling from Snakemake and transitioning to FlowEngine, significant residual code remains. The codebase also evolved organically, resulting in duplicate implementations, inconsistent patterns, and technical debt.

**Current State:**
- Three separate `get_tool_registry()` implementations across different modules
- Two different FileInfo models with conflicting schemas
- Snakemake references scattered across database, models, services, and API layers
- Inconsistent error handling with hardcoded status codes
- Unused imports and potentially unused services

**Constraints:**
- Must maintain API compatibility (no breaking changes to external API)
- Database migration required for schema changes
- Tests must pass after refactoring

## Goals / Non-Goals

**Goals:**
- Eliminate all Snakemake references from codebase
- Consolidate duplicate implementations into single sources of truth
- Standardize error handling patterns across all API endpoints
- Reduce technical debt for improved maintainability
- Ensure all code follows established patterns (immutability, error handling, separation of concerns)

**Non-Goals:**
- Adding new features or capabilities
- Performance optimization (unless related to cleanup)
- Refactoring test suite structure (only updating for schema changes)
- Changing external API behavior

## Decisions

### 1. Tool Registry Consolidation

**Decision:** Use `app/services/tool_registry.py` as the single source of truth, implement dependency injection pattern via FastAPI's `Depends()`.

**Rationale:**
- Service layer is the appropriate location for business logic
- Dependency injection enables easier testing and loose coupling
- Eliminates duplicate code and ensures consistent behavior

**Alternatives Considered:**
- Keep multiple implementations (rejected - increases maintenance burden)
- Use global singleton (rejected - harder to test, creates implicit dependencies)

### 2. FileInfo Model Unification

**Decision:** Merge FileInfo models, keeping the more comprehensive version from `app/models/common.py` with additions from `app/models/files.py` (file_type, metadata).

**Rationale:**
- Single source of truth prevents schema drift
- Combined model provides richer file information

**Alternatives Considered:**
- Keep separate models for different contexts (rejected - creates confusion)
- Create base FileInfo with subclasses (rejected - over-engineering for current needs)

### 3. Database Migration Strategy

**Decision:** Create Alembic migration to rename `snakemake_args` → `engine_args` and remove `snakemake_status` field.

**Rationale:**
- Alembic provides versioned, reversible migrations
- Allows incremental deployment with rollback capability

**Migration Steps:**
1. Create migration file
2. Rename column `snakemake_args` → `engine_args`
3. Drop column `snakemake_status`
4. Update model definitions
5. Run migration

### 4. Error Handling Standardization

**Decision:** Use `from fastapi import status` and `status.HTTP_*` constants throughout all API endpoints.

**Rationale:**
- Standard FastAPI pattern
- Type-safe and self-documenting
- Easier to maintain than magic numbers

### 5. Service Cleanup

**Decision:** Review and potentially remove `cwl_exporter.py` and `engine_adapter.py` after verifying no active usage.

**Rationale:**
- Dead code increases maintenance burden
- Reduces confusion about available functionality

**Process:** Check import references, if unused for >30 days, remove with commit documenting reason.

## Risks / Trade-offs

### Risk 1: Database migration failure
**Risk**: Production database migration could fail or cause downtime
**Mitigation**:
- Test migration on staging database first
- Create rollback migration before deploying
- Schedule maintenance window for deployment

### Risk 2: Hidden dependencies on removed code
**Risk**: Removing Snakemake references or unused services may break unknown functionality
**Mitigation**:
- Comprehensive grep search for all references before removal
- Run full test suite after each change
- Deploy to staging environment before production

### Risk 3: Test failures from model changes
**Risk**: Database model changes may break existing tests
**Mitigation**:
- Update test fixtures and factories to match new schema
- Run tests incrementally during development
- Document migration steps for test data

### Trade-off: Refactoring scope vs. deployment time
**Trade-off**: Comprehensive cleanup takes longer but reduces long-term debt
**Decision**: Prioritize Critical/High fixes first, Medium/Low can follow

## Migration Plan

### Phase 1: Critical Fixes (Blocking)
1. Database migration for Snakemake field removal
2. FileInfo model consolidation
3. Tool registry unification

### Phase 2: High Priority
1. Error handling standardization
2. Remove unused imports
3. Update logging and WebSocket code

### Phase 3: Medium Priority
1. Complete empty schema files
2. Extract magic numbers to config
3. Remove confirmed unused services

### Rollback Strategy
- Database migration: Alembic `downgrade` command
- Code changes: Git revert to previous commit
- Keep feature branch until production verification complete

## Open Questions

1. **Is CWL export functionality still needed?** → Need product input before removing `cwl_exporter.py`
2. **Should we create a compatibility layer for the database migration?** → Not needed if we deploy all changes together
3. **Are there any scheduled workflows that depend on old field names?** → Check with operations team
