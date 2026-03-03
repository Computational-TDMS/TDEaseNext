# Tasks: Sample-Based Path Mapping System

**Change**: `improve-command-executor`
**Status**: Ready for Implementation

---

## 1. Core Data Structure Changes

- [ ] 1.1 Extend TaskSpec with sample_context field
  - File: `app/core/executor/base.py`
  - Add `sample_context: Dict[str, str] = field(default_factory=dict)` to TaskSpec dataclass
  - Verify: TaskSpec can be instantiated without sample_context (defaults to empty dict)

- [ ] 1.2 Update CommandPipeline constructor to accept sample_context
  - File: `app/core/executor/command_pipeline.py`
  - Add `sample_context` parameter to `__init__` with default None
  - Store as `self.sample_context = sample_context or {}`
  - Verify: CommandPipeline can be instantiated without sample_context

- [ ] 1.3 Implement _inject_context_params method in CommandPipeline
  - File: `app/core/executor/command_pipeline.py`
  - Create method to process `injectFrom` declarations in tool definitions
  - Extract variable name from `context.variable_name` format
  - Inject values from sample_context into param_values
  - Handle missing required variables (raise ValueError)
  - Handle missing optional variables (skip injection)
  - Verify: Method correctly injects parameters when sample_context is provided

- [ ] 1.4 Integrate _inject_context_params into build() method
  - File: `app/core/executor/command_pipeline.py`
  - Call `_inject_context_params(param_values)` at the start of `build()`
  - Use the returned param_values for rest of the build process
  - Verify: Parameters with injectFrom are injected before command building

## 2. Executor Integration

- [ ] 2.1 Update LocalExecutor to pass sample_context to CommandPipeline
  - File: `app/core/executor/local.py`
  - Modify `execute()` method to pass `spec.sample_context` when creating CommandPipeline
  - Change: `pipeline = CommandPipeline(tool_info)` → `pipeline = CommandPipeline(tool_info, sample_context=spec.sample_context)`
  - Verify: CommandPipeline receives sample_context from TaskSpec

- [ ] 2.2 Update WorkflowService to include sample_context in TaskSpec
  - File: `app/services/workflow_service.py`
  - Modify `build_task_spec()` to include `sample_context=c.sample_context` in TaskSpec creation
  - Verify: TaskSpec created with sample_context from ExecutionContext

- [ ] 2.3 Verify existing hardcoded data_loader handling still works
  - File: `app/services/workflow_service.py` (line 207-208)
  - Ensure existing `if tool_id == "data_loader"` code remains functional
  - This is a compatibility layer during migration
  - Verify: data_loader still receives sample_name via existing code path

## 3. Tool Definition Updates

- [ ] 3.1 Add injectFrom declaration to data_loader.json
  - File: `config/tools/data_loader.json`
  - Add to parameters section:
  ```json
  "sample_name": {
    "injectFrom": "context.sample",
    "required": true
  }
  ```
  - Verify: Tool definition declares sample_name injection from context

- [ ] 3.2 Test new injection mechanism with data_loader
  - Create test workflow with data_loader node
  - Execute workflow and verify sample_name is correctly injected
  - Verify: Output file uses sample_name from sample_context

- [ ] 3.3 Remove hardcoded data_loader handling (after verification)
  - File: `app/services/workflow_service.py`
  - Remove lines 207-208: `if tool_id == "data_loader": ...`
  - Verify: data_loader works via injectFrom mechanism only

## 4. Testing

- [ ] 4.1 Write unit tests for TaskSpec.sample_context
  - File: `tests/core/executor/test_base.py` (create if needed)
  - Test: TaskSpec with sample_context
  - Test: TaskSpec without sample_context (defaults to empty dict)
  - Verify: All tests pass

- [ ] 4.2 Write unit tests for CommandPipeline._inject_context_params
  - File: `tests/core/executor/test_command_pipeline.py`
  - Test: Inject sample_name from context
  - Test: Inject multiple parameters from context
  - Test: Missing required variable raises ValueError
  - Test: Missing optional variable is skipped
  - Test: User parameter overrides injected value
  - Verify: All tests pass

- [ ] 4.3 Write integration test for complete workflow
  - File: `tests/integration/test_sample_context_integration.py`
  - Create workflow: data_loader → msconvert
  - Execute with sample from samples.json
  - Verify: Output files use correct sample names
  - Verify: All tests pass

- [ ] 4.4 Test backward compatibility
  - File: `tests/integration/test_backward_compat.py`
  - Test: Existing tools without injectFrom still work
  - Test: Tools without sample_context in TaskSpec still work
  - Verify: No regressions in existing functionality

## 5. Documentation

- [ ] 5.1 Update tool definition documentation
  - File: `docs/guides/tool-registration.md` (or equivalent)
  - Document: injectFrom field usage
  - Document: Available context variables
  - Document: Examples of common patterns
  - Verify: Documentation is clear and complete

- [ ] 5.2 Add migration guide for tool developers
  - File: `docs/guides/sample-context-migration.md`
  - Explain: How to update existing tools to use injectFrom
  - Explain: Benefits of using injectFrom over hardcoded handling
  - Provide: Before/after examples
  - Verify: Guide is easy to follow

## 6. Cleanup

- [ ] 6.1 Remove useParamsJson from data_loader if no longer needed
  - File: `config/tools/data_loader.json`
  - Check if useParamsJson is still required for other parameters
  - If only used for sample_name, remove it (now handled by injectFrom)
  - Verify: data_loader still works correctly

- [ ] 6.2 Update CHANGELOG and version history
  - Document new sample-context-injection capability
  - Document changes to TaskSpec and CommandPipeline
  - Document tool definition schema changes
  - Verify: Changes are properly documented

---

## Verification Checklist

Before marking this change complete:

- [ ] All tasks in this checklist are completed
- [ ] Unit tests pass with >80% coverage
- [ ] Integration tests pass for complete workflows
- [ ] Existing tools continue to work without modification
- [ ] New tools can use injectFrom without code changes
- [ ] Documentation is complete and accurate
- [ ] No regressions in existing functionality
