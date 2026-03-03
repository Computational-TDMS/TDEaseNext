# Capability: Sample Context Injection

**Version**: 1.0.0
**Status**: Draft

---

## ADDED Requirements

### Requirement: TaskSpec contains sample context

The TaskSpec data structure SHALL include a `sample_context` field containing a dictionary of sample-specific variables derived from the samples.json file.

#### Scenario: TaskSpec includes sample context
- **GIVEN** a workflow execution for sample "sample1"
- **AND** the sample context contains `{"sample": "sample1", "input_basename": "raw_data", "input_ext": "raw"}`
- **WHEN** TaskSpec is created by WorkflowService
- **THEN** `spec.sample_context` SHALL equal the sample context dictionary
- **AND** the field SHALL default to an empty dict if not provided

### Requirement: Tool definitions can declare parameter injection from sample context

Tool definition JSON SHALL support the `injectFrom` field in parameter definitions to specify that a parameter value should be injected from the sample context.

**Format**:
```json
{
  "parameters": {
    "param_id": {
      "injectFrom": "context.variable_name"
    }
  }
}
```

#### Scenario: Tool declares sample_name injection
- **GIVEN** a tool definition for "data_loader"
- **AND** the tool requires a sample_name parameter
- **WHEN** the parameter definition includes `"injectFrom": "context.sample"`
- **THEN** the system SHALL inject `sample_context["sample"]` as the parameter value

#### Scenario: Missing required context variable
- **GIVEN** a tool parameter with `"injectFrom": "context.sample"`
- **AND** the parameter is marked as `"required": true`
- **AND** `sample_context` does NOT contain the key "sample"
- **WHEN** CommandPipeline builds the command
- **THEN** the system SHALL raise a ValueError
- **AND** the error message SHALL indicate which context variable is missing

#### Scenario: Optional context variable missing
- **GIVEN** a tool parameter with `"injectFrom": "context.optional_var"`
- **AND** the parameter is NOT marked as required
- **AND** `sample_context` does NOT contain the key "optional_var"
- **WHEN** CommandPipeline builds the command
- **THEN** the system SHALL skip injection for this parameter
- **AND** the command SHALL build successfully without this parameter

### Requirement: CommandPipeline processes injectFrom declarations

CommandPipeline.build() SHALL process all `injectFrom` declarations before building parameter flags, injecting values from sample_context into param_values.

#### Scenario: Inject sample_name into params
- **GIVEN** a tool definition with `sample_name` parameter declaring `"injectFrom": "context.sample"`
- **AND** `sample_context = {"sample": "my_sample"}`
- **WHEN** CommandPipeline.build() is called with `param_values={}`
- **THEN** the system SHALL set `param_values["sample_name"] = "my_sample"`
- **AND** the parameter SHALL be included in the --params JSON if useParamsJson is true

#### Scenario: Inject multiple context parameters
- **GIVEN** a tool definition with two parameters:
  - `sample_name` with `"injectFrom": "context.sample"`
  - `input_ext` with `"injectFrom": "context.input_ext"`
- **AND** `sample_context = {"sample": "s1", "input_ext": "raw"}`
- **WHEN** CommandPipeline.build() is called
- **THEN** `param_values["sample_name"]` SHALL equal "s1"
- **AND** `param_values["input_ext"]` SHALL equal "raw"

### Requirement: User-provided parameters take precedence over injected values

If a user provides a value for a parameter that also has an `injectFrom` declaration, the user-provided value SHALL be used.

#### Scenario: User parameter overrides injection
- **GIVEN** a tool parameter with `"injectFrom": "context.sample"`
- **AND** `sample_context = {"sample": "auto_sample"}`
- **AND** the user provides `param_values = {"sample_name": "user_override"}`
- **WHEN** CommandPipeline.build() is called
- **THEN** `param_values["sample_name"]` SHALL equal "user_override"
- **AND** the injected value SHALL be ignored

### Requirement: CommandPipeline accepts sample_context in constructor

CommandPipeline SHALL accept an optional `sample_context` parameter in its constructor, defaulting to None.

#### Scenario: Initialize with sample context
- **GIVEN** a tool definition
- **AND** a sample context dictionary
- **WHEN** CommandPipeline is instantiated with `CommandPipeline(tool_def, sample_context=context)`
- **THEN** `pipeline.sample_context` SHALL equal the provided context

#### Scenario: Initialize without sample context
- **GIVEN** a tool definition
- **WHEN** CommandPipeline is instantiated without sample_context
- **THEN** `pipeline.sample_context` SHALL equal an empty dictionary
- **AND** the pipeline SHALL function normally for tools without injectFrom declarations

### Requirement: LocalExecutor passes sample_context to CommandPipeline

LocalExecutor.execute() SHALL pass the `sample_context` from TaskSpec to CommandPipeline when building commands.

#### Scenario: Pass context to CommandPipeline
- **GIVEN** a TaskSpec with `sample_context = {"sample": "test"}`
- **AND** the tool does NOT have a pre-built cmd
- **WHEN** LocalExecutor.execute() is called
- **THEN** CommandPipeline SHALL be instantiated with the sample_context
- **AND** the command SHALL be built with context variables injected

### Requirement: WorkflowService includes sample_context in TaskSpec

WorkflowService.build_task_spec() SHALL include the sample_context from ExecutionContext when creating TaskSpec instances.

#### Scenario: Build TaskSpec with sample context
- **GIVEN** an ExecutionContext with `sample_context = {"sample": "sample1"}`
- **WHEN** WorkflowService creates a TaskSpec
- **THEN** `spec.sample_context` SHALL equal the ExecutionContext's sample_context
- **AND** the context SHALL contain all derived variables (sample, input_basename, input_ext, etc.)

---

## MODIFIED Requirements

None. This is a new capability.

---

## REMOVED Requirements

None.
