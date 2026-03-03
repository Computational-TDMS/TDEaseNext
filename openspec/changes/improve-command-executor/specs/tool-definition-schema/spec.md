# Capability: Tool Definition Schema

**Delta Spec**: Sample Context Injection Support
**Base Version**: Existing tool-definition-schema spec
**Status**: Draft

---

## ADDED Requirements

### Requirement: Parameter injectFrom declaration

Tool definition parameters SHALL support an optional `injectFrom` field to specify that the parameter value should be injected from the sample context.

**Schema**:
```json
{
  "parameters": {
    "<param_id>": {
      "injectFrom": "context.<variable_name>",
      "required": true | false
    }
  }
}
```

#### Scenario: Declare sample_name injection
- **GIVEN** a tool that requires the sample name
- **WHEN** defining the tool's parameters
- **THEN** the tool definition MAY include:
```json
{
  "sample_name": {
    "injectFrom": "context.sample",
    "required": true
  }
}
```

#### Scenario: Declare optional context injection
- **GIVEN** a tool that optionally uses a context variable
- **WHEN** defining the tool's parameters
- **THEN** the tool definition MAY include:
```json
{
  "optional_param": {
    "injectFrom": "context.optional_var"
  }
}
```

#### Scenario: InjectFrom without required defaults to optional
- **GIVEN** a parameter with `"injectFrom": "context.sample"`
- **AND** the parameter does NOT specify `"required"`
- **WHEN** the parameter is processed
- **THEN** the system SHALL treat the parameter as optional
- **AND** missing context variables SHALL NOT cause an error

---

## MODIFIED Requirements

None. The existing tool definition schema remains unchanged. The `injectFrom` field is purely additive and optional.

---

## REMOVED Requirements

None.

---

## Notes

### Backward Compatibility

The `injectFrom` field is completely optional:
- Existing tool definitions without `injectFrom` continue to work unchanged
- Tools that don't need context injection simply don't declare `injectFrom`
- The field is ignored by CommandPipeline if not present

### Supported Context Variables

The following context variables are available for injection (from `UnifiedWorkspaceManager._build_sample_context`):

| Variable | Description | Example |
|----------|-------------|---------|
| `sample` | Sample ID | `"sample1"` |
| `input_basename` | Input file basename | `"Sorghum-Histone0810162L20"` |
| `input_ext` | Input file extension | `"raw"` |
| `input_dir` | Input file directory | `"data/raw"` |
| `raw_path` | Absolute path to raw file | `"/workspace/data/raw/file.raw"` |
| `fasta_path` | Absolute path to FASTA file | `"/workspace/data/fasta/db.fasta"` |

Additional variables can be added to sample context via `samples.json` explicit context.
