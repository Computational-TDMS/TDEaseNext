# Opus Redesign - Current Implementation Status

## Progress Summary

**Completed**: 18/44 tasks (41%)

### ✅ Phase 1: Tool Definition Schema (6/7 complete)

All tool definitions migrated to new Schema:
- ✅ `config/tool-schema.json` - JSON Schema validation template
- ✅ `config/tools/topfd.json` - Migrated to new format
- ✅ `config/tools/toppic.json` - Migrated to new format
- ✅ `config/tools/msconvert.json` - Migrated to new format
- ✅ `config/tools/data_loader.json` - Migrated to new format
- ✅ `config/tools/fasta_loader.json` - Migrated to new format
- ⏳ Update `app/services/tool_registry.py` - Pending

### ✅ Phase 2: Command Pipeline (7/9 complete)

New command pipeline implementation:
- ✅ `app/core/executor/command_pipeline.py` - Complete 5-step pipeline
  - Step 1: Filter empty parameters (null/empty/"none")
  - Step 2: Resolve executable (native/script/docker)
  - Step 3: Add output flag
  - Step 4: Build parameter flags (value/boolean/choice)
  - Step 5: Add positional arguments
- ✅ Shell quoting (Windows/Unix)
- ⏳ Replace old CommandBuilder in `local.py` - Pending
- ⏳ Keep old `command_builder.py` as deprecated fallback - Pending

### ✅ Phase 3: Sample Management (5/7 complete)

**Mostly completed by `implement-workspace-hierarchy`**:
- ✅ Sample structure in `samples.json`
- ✅ Sample context loading via `UnifiedWorkspaceManager`
- ✅ Placeholder resolution with auto-derivation
- ✅ Backward compatibility handled
- ✅ Fallback derivation removed
- ⏳ Update `app/api/workflow.py` to use `UnifiedWorkspaceManager` - Pending
- ⏳ Verify `workflow_service.py` uses new validation - Pending

### ⏳ Remaining Phases

- **Phase 4**: Normalizer adjustments (0/3)
- **Phase 5**: Frontend integration (0/5)
- **Phase 6**: API updates (0/3)
- **Phase 7**: Visualization design (0/3)
- **Phase 8**: Testing & cleanup (0/7)

## Key Design Decisions

### 1. Sample Management (Already Implemented)

The `samples.json` structure provides what Opus's "Sample Table" design needed:

```json
{
  "samples": {
    "sample1": {
      "id": "sample1",
      "context": {
        "sample": "sample1",
        "fasta_filename": "UniProt_sorghum_focus1"
      },
      "data_paths": {
        "raw": "data/raw/file.raw",
        "fasta": "data/fasta/db.fasta"
      }
    }
  }
}
```

**Benefits over original design**:
- More complete (includes metadata, file paths, context)
- Workspace-level (can be shared across workflows)
- Auto-derivation of common values (basename, dir, extension)

### 2. Command Pipeline Architecture

The 5-step pipeline replaces the old CommandBuilder:

```
Input: param_values, input_files, output_dir
  ↓
Step 1: Filter → remove null/empty/"none"
  ↓
Step 2: Executable → resolve based on executionMode
  ↓
Step 3: Output Flag → add if flagSupported
  ↓
Step 4: Parameters → build flags (value/boolean/choice)
  ↓
Step 5: Positional → add positional args in order
  ↓
Output: [cmd, arg1, arg2, ...]
```

**Key improvement**: Parameter filtering happens ONCE at the start, not scattered across normalizer/frontend/old CommandBuilder.

### 3. Placeholder Validation (Already Implemented)

Strict validation already in place from `implement-workspace-hierarchy`:
- `validate_placeholders()` - throws clear ValueError for missing placeholders
- Removed dangerous `re.sub(r"\{\w+\}", "out")` fallback
- Validation happens BEFORE execution

## Next Steps

### Immediate (Priority)
1. Update `tool_registry.py` to load new Schema (1.7)
2. Integrate `command_pipeline` into `local.py` (2.8)
3. Update `workflow.py` to use `UnifiedWorkspaceManager` (3.6)

### Short-term
4. Remove `_filter_empty_params` from normalizer (4.1)
5. Frontend integration (Phase 5)

### Long-term
6. Testing and cleanup (Phase 8)
7. Visualization nodes (Phase 7 - optional)

## Integration Points

### Where `command_pipeline` should be used:

```python
# In LocalExecutor or FlowEngine
from app.core.executor.command_pipeline import build_command

cmd_parts = build_command(
    tool_def=tool_definition,
    param_values=node_params,
    input_files=input_file_map,
    output_dir=workspace_path
)
```

### Where `UnifiedWorkspaceManager` should be used:

```python
# In workflow execution
from app.services.unified_workspace_manager import get_unified_workspace_manager

manager = get_unified_workspace_manager()
context = manager.get_sample_context(user_id, workspace_id, sample_id)
```

## Architecture Benefits

1. **Single Source of Truth**: Tool Definition Schema drives command building
2. **No tool_type branching**: CommandBuilder uses Schema, not if/else on tool type
3. **Unified parameter filtering**: One place to filter, not scattered
4. **Robust sample management**: Structured data in samples.json
5. **Strict placeholder validation**: Fail fast with clear errors

## Migration Notes

- **Backward compatibility**: Old workflow JSONs with inline `sample_context` still work temporarily
- **Tool Definition**: New Schema is backward compatible with old fields (marked as deprecated)
- **Breaking changes**: Will be documented once Phase 1-3 are fully integrated
