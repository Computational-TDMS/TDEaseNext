# Workspace Architecture Design

## Overview

TDEase now supports a hierarchical workspace structure:
- **Users** can have multiple **workspaces**
- Each **workspace** has a **sample list**, multiple **workflows**, and **executions**

## Directory Structure

```
data/
├── users/
│   ├── {user_id}/
│   │   ├── user.json                   # User metadata
│   │   ├── workspaces/
│   │   │   ├── {workspace_id}/
│   │   │   │   ├── workspace.json      # Workspace config
│   │   │   │   ├── samples.json        # ★ Sample definitions
│   │   │   │   ├── workflows/          # Workflow definitions
│   │   │   │   │   ├── workflow1.json
│   │   │   │   │   └── workflow2.json
│   │   │   │   ├── executions/         # Execution records
│   │   │   │   │   ├── exec_001/
│   │   │   │   │   │   ├── execution.json
│   │   │   │   │   │   ├── inputs/
│   │   │   │   │   │   ├── outputs/
│   │   │   │   │   │   └── logs/
│   │   │   │   │   └── exec_002/
│   │   │   │   └── data/               # Shared data
│   │   │   │       ├── raw/
│   │   │   │       ├── fasta/
│   │   │   │       └── reference/
│   │   │   └── {workspace_id_2}/
│   │   │
│   └── {user_id_2}/
│
└── shared/                              # Global shared resources
    ├── databases/
    └── tools/
```

## Core Concepts

### 1. Samples.json - Sample Definition

**Purpose**: Define all samples available in a workspace with their context values.

**Structure**:
```json
{
  "version": "1.0",
  "workspace_id": "test_workspace",
  "created_at": "2025-03-02T10:00:00Z",
  "updated_at": "2025-03-02T10:00:00Z",
  "samples": {
    "sample1": {
      "id": "sample1",
      "name": "Display Name",
      "description": "Sample description",
      "context": {
        "sample": "sample1",
        "fasta_filename": "database_name",
        "input_basename": "raw_file_name",
        "input_ext": "raw"
      },
      "data_paths": {
        "raw": "data/raw/file.raw",
        "fasta": "data/fasta/db.fasta"
      },
      "metadata": {
        "organism": "Species",
        "tissue": "Tissue type"
      },
      "created_at": "2025-03-02T10:00:00Z"
    }
  }
}
```

**Key Fields**:
- `context`: Placeholder values for workflow execution
  - Used to resolve `{sample}`, `{fasta_filename}` in output patterns
- `data_paths`: File path templates (can use `{sample}`)
- `metadata`: Optional sample metadata

### 2. Placeholder Resolution

**Workflow tools use placeholders**:
```json
{
  "outputs": [
    { "pattern": "{sample}_proteoforms.tsv" }
  ]
}
```

**Resolution process**:
```
1. User selects samples: ["sample1", "sample2"]
2. Load samples.json → get context for each sample
3. For each sample:
   a. Build context: {sample: "sample1", fasta_filename: "db", ...}
   b. Resolve output patterns:
      - "{sample}_proteoforms.tsv" → "sample1_proteoforms.tsv"
   c. Execute workflow with resolved paths
4. Store results in execution directory
```

### 3. Workflow Execution Flow

```
User Request:
├─ workflow_id: "test_pipeline"
├─ workspace_path: "data/users/test_user/workspaces/test_workspace"
└─ samples: ["sample1", "sample2"]

Backend Processing:
├─ Load samples.json
├─ For each sample:
│  ├─ Get sample context
│  ├─ Resolve all placeholders
│  ├─ Create execution directory
│  ├─ Execute workflow
│  └─ Store results
└─ Return execution IDs
```

## API Design

### Workspace Management

```bash
# List user's workspaces
GET /api/users/{user_id}/workspaces

# Create workspace
POST /api/users/{user_id}/workspaces
{
  "workspace_id": "new_workspace",
  "name": "New Workspace",
  "description": "..."
}

# Get workspace info
GET /api/users/{user_id}/workspaces/{workspace_id}

# Delete workspace
DELETE /api/users/{user_id}/workspaces/{workspace_id}
```

### Sample Management

```bash
# List samples
GET /api/users/{user_id}/workspaces/{workspace_id}/samples

# Add sample
POST /api/users/{user_id}/workspaces/{workspace_id}/samples
{
  "id": "sample3",
  "name": "Sample 3",
  "context": {...},
  "data_paths": {...}
}

# Get sample
GET /api/users/{user_id}/workspaces/{workspace_id}/samples/{sample_id}

# Update sample
PUT /api/users/{user_id}/workspaces/{workspace_id}/samples/{sample_id}

# Delete sample
DELETE /api/users/{user_id}/workspaces/{workspace_id}/samples/{sample_id}
```

### Workflow Execution

```bash
# Execute workflow for samples
POST /api/workflows/execute
{
  "workflow_id": "test_pipeline",
  "workspace_path": "data/users/test_user/workspaces/test_workspace",
  "samples": ["sample1", "sample2"],
  "params": {
    "cores": 4,
    "dry_run": false
  }
}

# Response:
{
  "execution_id": "exec_20250302_001",
  "status": "running",
  "samples": ["sample1", "sample2"],
  "execution_dir": "data/users/test_user/workspaces/test_workspace/executions/exec_20250302_001"
}
```

## Implementation Changes

### 1. Remove Silent Placeholder Fallback

**Before** (DANGEROUS):
```python
try:
    resolved = pat.format(**context)
except KeyError:
    resolved = re.sub(r"\{\w+\}", "out", pat)  # Silent!
```

**After** (SAFE):
```python
missing = set(re.findall(r"\{(\w+)\}", pat)) - context.keys()
if missing:
    raise ValueError(
        f"Missing placeholders in pattern '{pat}': {missing}. "
        f"Available: {list(context.keys())}"
    )
return pat.format(**context)
```

### 2. Load Sample Context from Workspace

```python
def get_sample_context(user_id: str, workspace_id: str, sample_id: str) -> Dict[str, str]:
    """Load sample context from samples.json"""
    manager = get_workspace_manager()
    return manager.get_sample_context(user_id, workspace_id, sample_id)
```

### 3. Execute Workflow per Sample

```python
async def execute_workflow_for_samples(
    workflow_id: str,
    user_id: str,
    workspace_id: str,
    sample_ids: List[str],
    params: Dict[str, Any]
):
    """Execute workflow for each sample"""
    manager = get_workspace_manager()

    for sample_id in sample_ids:
        # Load sample context
        context = manager.get_sample_context(user_id, workspace_id, sample_id)

        # Create execution directory
        exec_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{sample_id}"
        exec_dir = manager.create_execution_dir(user_id, workspace_id, exec_id)

        # Execute workflow with context
        result = await execute_workflow(
            workflow_json=workflow,
            workspace_path=exec_dir,
            sample_context=context,
            **params
        )
```

## Testing

### Test Setup

```bash
# Test environment created at:
data/users/test_user/
├── user.json
└── workspaces/
    └── test_workspace/
        ├── workspace.json
        ├── samples.json
        ├── workflows/
        │   └── test_pipeline.json
        ├── executions/
        └── data/
            ├── raw/Sorghum-Histone0810162L20.raw
            └── fasta/UniProt_sorghum_focus1.fasta
```

### Test Sample

```json
{
  "sample1": {
    "context": {
      "sample": "sample1",
      "fasta_filename": "UniProt_sorghum_focus1",
      "input_basename": "Sorghum-Histone0810162L20",
      "input_ext": "raw"
    }
  }
}
```

## Migration Path

### Phase 1: Current (Testing)
- Hardcode samples in workflow JSON
- No workspace isolation
- Single user

### Phase 2: Next (Implementation)
- Implement workspace manager
- Load samples from samples.json
- Multi-user support
- Execution directories per run

### Phase 3: Future (Enhancement)
- Web UI for sample management
- Sample import/export
- Sample validation
- Metadata search

## Benefits

1. **Clear Separation**: Users → Workspaces → Samples
2. **Sample Reusability**: Define once, use in multiple workflows
3. **Execution Isolation**: Each execution in separate directory
4. **Parallel Processing**: Easy to execute multiple samples in parallel
5. **Data Organization**: Clear data file locations

## Next Steps

1. ✅ Create directory structure
2. ✅ Create test environment
3. ⏳ Implement UserWorkspaceManager
4. ⏳ Update WorkflowService to use sample context
5. ⏳ Add workspace API endpoints
6. ⏳ Update frontend to use workspace paths
7. ⏳ Add tests for workspace management
