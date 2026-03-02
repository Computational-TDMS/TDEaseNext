# Design Update Needed for redesign-cmd-and-sample-management

## Context

`implement-workspace-hierarchy` has been completed, which affects some assumptions in the original `redesign-cmd-and-sample-management` design.

## Already Implemented (No Need to Redesign)

### 1. Sample Management Structure ✅

**Original Plan (D3)**:
```json
{
  "sample_table": {
    "sample1": {"raw": "file.raw", "fasta": "db.fasta"}
  }
}
```

**Current Implementation** (in `samples.json`):
```json
{
  "samples": {
    "sample1": {
      "id": "sample1",
      "context": {
        "sample": "sample1",
        "fasta_filename": "UniProt_sorghum_focus1",
        "input_basename": "Sorghum-Histone0810162L20"
      },
      "data_paths": {
        "raw": "data/raw/file.raw",
        "fasta": "data/fasta/db.fasta"
      }
    }
  }
}
```

**Impact**:
- ✅ Structure is MORE complete than planned
- ✅ Supports both `context` (placeholders) and `data_paths` (file locations)
- ✅ Auto-derivation of `input_basename`, `input_dir`, `input_ext` already implemented
- ✅ Managed by `UnifiedWorkspaceManager`

### 2. Placeholder Validation ✅

**Original Concern**:
> "_extract_sample_ctx_from_workflow 中的脆弱推导逻辑导致 `{fasta_filename}` 缺失"

**Current Implementation**:
- `validate_placeholders()` in `src/workflow/validator.py`
- Raises clear `ValueError` with missing placeholders
- Removed dangerous `re.sub(r"\{\w+\}", "out")` fallback

**Impact**:
- ✅ No need to redesign placeholder extraction
- ✅ Validation happens BEFORE execution
- ✅ Clear error messages

### 3. Sample Context Loading ✅

**Original Concern**:
> "遍历节点猜测 sample 和 fasta_filename，每增加一种关联文件就需要新增推导逻辑"

**Current Implementation**:
```python
# Direct loading from workspace
manager = get_unified_workspace_manager()
context = manager.get_sample_context(user_id, workspace_id, sample_id)
```

**Impact**:
- ✅ No fragile extraction logic needed
- ✅ Context loaded from `samples.json` (already validated)
- ✅ Supports auto-derivation of common values

## Design Updates Needed

### Update D3: Sample Table Resolution

**Old Design**:
```python
# Resolve from workflow metadata
sample_table = workflow_metadata.get("sample_table", {})
```

**New Design**:
```python
# Load from workspace via UnifiedWorkspaceManager
from app.services.unified_workspace_manager import get_unified_workspace_manager

manager = get_unified_workspace_manager()
samples_data = manager.load_samples(user_id, workspace_id)

# Build execution context for each sample
for sample_id, sample_def in samples_data["samples"].items():
    context = manager.get_sample_context(user_id, workspace_id, sample_id)
    # context contains both explicit values and auto-derived values
```

### Update CommandBuilder Integration

**Old Concern**:
> "_resolve_output_paths 和 _resolve_input_paths 中的占位符解析，基于 Sample Table"

**New Implementation**:
```python
# In workflow_service.py
def _resolve_output_paths(node_id, tool_id, tool_info, sample_ctx, workspace):
    # sample_ctx comes from UnifiedWorkspaceManager.get_sample_context()
    # Already validated with validate_placeholders()
    patterns = tool_info.get("output_patterns", [])
    for pattern_info in patterns:
        pattern = pattern_info.get("pattern", "")
        # Placeholder validation already done
        resolved = pattern.format(**sample_ctx)
        result.append(workspace / resolved)
    return result
```

### Update _extract_sample_ctx_from_workflow

**Old Function** (should be removed):
```python
def _extract_sample_ctx_from_workflow(wf_v2, params_ctx):
    # Fragile extraction logic
    #遍历节点猜测 sample 和 fasta_filename
```

**New Approach**:
```python
# DEPRECATED: Use UnifiedWorkspaceManager.get_sample_context() instead
# This function should be removed or simplified to a passthrough
def load_sample_context_for_execution(user_id, workspace_id, sample_ids):
    """Load sample contexts from workspace"""
    manager = get_unified_workspace_manager()
    contexts = {}
    for sample_id in sample_ids:
        ctx = manager.get_sample_context(user_id, workspace_id, sample_id)
        if ctx is None:
            raise ValueError(f"Sample '{sample_id}' not found in workspace")
        contexts[sample_id] = ctx
    return contexts
```

## Updated Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Updated Execution Flow                      │
└─────────────────────────────────────────────────────────────┘

Frontend Request
├─ user_id
├─ workspace_id
├─ workflow_id
└─ sample_ids

       ↓

UnifiedWorkspaceManager
├─ load_samples(user_id, workspace_id)
├─ get_sample_context(user_id, workspace_id, sample_id)
└─ Returns: {sample, fasta_filename, input_basename, ...}

       ↓

CommandBuilder (TO BE REFACTORED per Opus plan)
├─ Use Tool Definition Schema
├─ Build command with parameters
├─ Use sample_context for placeholders
└─ No tool_type branching needed

       ↓

Executor
└─ Run command
```

## Action Items

1. ✅ **COMPLETED**: Workspace-level sample management (implement-workspace-hierarchy)
2. ⏳ **TODO**: Refactor CommandBuilder (Opus D1, D2)
3. ⏳ **TODO**: Update Tool Definition Schema (Opus D1)
4. ⏳ **TODO**: Frontend PropertyPanel integration (Opus D4)
5. ⏳ **TODO**: Remove `_extract_sample_ctx_from_workflow`脆弱逻辑

## Migration Notes

- **Backward Compatibility**: Old workflow JSONs with inline `sample_context` still work
- **New Way**: Load from `samples.json` via UnifiedWorkspaceManager
- **Fallback**: If `sample_context` in request, use it directly (temporary)
- **Future**: Remove inline `sample_context` support after migration period

## Conclusion

The `implement-workspace-hierarchy` change provides a SOLID FOUNDATION for the command-line refactoring:
- Sample structure is MORE complete than originally planned
- Placeholder validation is ALREADY strict
- Context loading is ALREADY robust

Opus's refactoring can focus on:
1. CommandBuilder rewrite (D1, D2)
2. Tool Definition Schema (D1)
3. Frontend integration (D4)

WITHOUT redesigning sample management from scratch.
