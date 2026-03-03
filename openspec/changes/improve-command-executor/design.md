# Design: Sample-Based Path Mapping System

**Change**: `improve-command-executor`
**Date**: 2026-03-03
**Status**: Draft

---

## Context

### 当前状态

TDEase FlowEngine 已经实现了 **Sample-Based Execution** 的基础架构：

1. **Sample Context 构建**：`UnifiedWorkspaceManager._build_sample_context` 自动推导变量
2. **路径解析**：`_resolve_output_paths` 使用 `pat.format(**sample_ctx)` 解析通配符
3. **特殊处理**：`workflow_service.py:207-208` 对 `data_loader` 硬编码注入 `sample_name`

### 约束条件

1. **不涉及容器化**：移除原 proposal 中的容器化相关内容
2. **不需要输出验证**：工具输出不符合预期就找不到文件，这是正常行为
3. **工具命名规则不可控**：TopFD/TopPIC 等工具自己控制输出文件名

### 核心问题

**当前硬编码 `tool_id == "data_loader"` 不可扩展**：
- 如果添加新的需要 sample 的工具（如 `custom_loader`）
- 需要修改代码添加新的 `if` 判断

---

## Goals / Non-Goals

**Goals:**
1. 建立通用的 sample 参数注入机制，不依赖硬编码 `tool_id`
2. 保持现有工具定义向后兼容
3. 确保 data_loader 等工具能正确接收 sample_name

**Non-Goals:**
1. 不实现输出文件验证或重命名（工具输出不符合预期 = 找不到文件）
2. 不涉及容器化执行
3. 不修改现有工具定义 Schema

---

## Decisions

### 决策 1：使用工具定义中的 `injectFrom` 声明参数注入

**选择**：在工具定义中明确声明需要从 context 注入的参数

**方案**：
```json
{
  "parameters": {
    "sample_name": {
      "injectFrom": "context.sample",
      "required": true
    }
  }
}
```

**rationale**：
- **声明式**：工具定义中明确说明需要什么参数
- **可扩展**：添加新工具无需修改 executor 代码
- **向后兼容**：没有 `injectFrom` 的工具不受影响

**替代方案**：
- 无条件注入 `sample_name` 到所有工具
  - ❌ 不必要地污染不需要 sample 的工具（如 TopFD）
  - ❌ 可能与工具现有参数冲突

### 决策 2：扩展 TaskSpec 包含 sample_context

**选择**：在 `TaskSpec` 中增加 `sample_context` 字段

**代码**：
```python
@dataclass
class TaskSpec:
    sample_context: Dict[str, str] = field(default_factory=dict)
```

**rationale**：
- **显式传递**：sample_context 作为明确的数据传递
- **可追溯**：执行时可以查看完整的 context
- **分离关注点**：WorkflowService 负责构建 context，CommandPipeline 负责使用

### 决策 3：在 CommandPipeline.build() 中实现参数注入

**选择**：在命令构建时处理 `injectFrom` 声明

**流程**：
```python
def build(self, param_values, sample_context=None):
    # 处理 injectFrom 声明
    for param_id, param_def in self.parameters.items():
        inject_from = param_def.get("injectFrom", "")
        if inject_from.startswith("context."):
            var_name = inject_from.split(".", 1)[1]
            if var_name in sample_context:
                param_values[param_id] = sample_context[var_name]
```

**rationale**：
- **统一处理**：所有参数注入在同一位置
- **可配置**：通过工具定义控制行为
- **无侵入**：不修改现有参数处理流程

### 决策 4：保持硬编码对 data_loader 的兼容

**选择**：保留 `workflow_service.py:207-208` 的特殊处理，移除 data_loader 的 `useParamsJson`

**代码**：
```python
# 兼容旧代码：data_loader 已有特殊处理
if tool_id == "data_loader":
    params_node = {**params_node, "sample_name": c.sample_context.get("sample", "")}

# 新机制：通过工具定义的 injectFrom
# data_loader.json 添加：
# "parameters": {
#   "sample_name": {
#     "injectFrom": "context.sample",
#     "required": true
#   }
# }
```

**rationale**：
- **渐进迁移**：先保留旧代码，确认新机制工作后移除
- **零风险**：不影响现有功能

---

## Architecture

### 组件关系

```
┌─────────────────────────────────────────────────────────┐
│                  WorkflowService                        │
│  构建 sample_context (from UnifiedWorkspaceManager)     │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                    TaskSpec                             │
│  - params: 用户参数                                      │
│  - sample_context: {"sample": "sample1", ...}            │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                LocalExecutor                            │
│  传递 TaskSpec 到 CommandPipeline                       │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              CommandPipeline.build()                    │
│  1. 读取工具定义中的 injectFrom 声明                     │
│  2. 从 sample_context 提取变量                           │
│  3. 注入到 param_values                                  │
│  4. 继续原有的命令构建流程                               │
└─────────────────────────────────────────────────────────┘
```

### 数据流

```
samples.json
  ↓
UnifiedWorkspaceManager.get_sample_context()
  ↓ {"sample": "sample1", "input_basename": "...", "input_ext": "raw"}
  ↓
WorkflowService.build_task_spec()
  ↓ TaskSpec(sample_context={...})
  ↓
LocalExecutor.execute(spec)
  ↓ CommandPipeline.build(param_values, sample_context)
  ↓ 检查 injectFrom 声明，注入参数
  ↓ ["python", "data_loader.py", "--params", '{"sample_name": "sample1"}', ...]
```

---

## Implementation Details

### 修改 1：扩展 TaskSpec

**文件**：`app/core/executor/base.py`

```python
@dataclass
class TaskSpec:
    """单次任务规格"""
    node_id: str
    tool_id: str
    params: Dict[str, Any]
    input_paths: List[Path]
    output_paths: List[Path]
    workspace_path: Path
    sample_context: Dict[str, str] = field(default_factory=dict)  # 新增
    conda_env: Optional[str] = None
    cmd: Optional[str] = None
    log_callback: Optional[Callable[[str, str], None]] = None
```

### 修改 2：CommandPipeline 支持参数注入

**文件**：`app/core/executor/command_pipeline.py`

```python
class CommandPipeline:
    def __init__(self, tool_def: Dict[str, Any], sample_context: Dict[str, str] = None):
        self.tool_def = tool_def
        self.sample_context = sample_context or {}
        # ... 现有初始化

    def build(self, param_values: Dict[str, Any], input_files: Dict[str, str], output_dir: Optional[str] = None) -> List[str]:
        # 新增：处理 injectFrom 声明
        param_values = self._inject_context_params(param_values)

        # Step 1: Filter empty parameters
        filtered_params = self._filter_empty_params(param_values)
        # ... 继续原有流程

    def _inject_context_params(self, param_values: Dict[str, Any]) -> Dict[str, Any]:
        """从 sample_context 注入声明为 injectFrom 的参数"""
        result = dict(param_values)  # 复制避免修改原字典

        for param_id, param_def in self.parameters.items():
            inject_from = param_def.get("injectFrom", "")
            if not inject_from or not inject_from.startswith("context."):
                continue

            var_name = inject_from.split(".", 1)[1]
            if var_name in self.sample_context:
                result[param_id] = self.sample_context[var_name]
            elif param_def.get("required"):
                raise ValueError(f"Required context variable '{var_name}' not found for parameter '{param_id}'")

        return result
```

### 修改 3：LocalExecutor 传递 sample_context

**文件**：`app/core/executor/local.py`

```python
async def execute(self, spec: TaskSpec) -> None:
    tool_info = self.tools_registry.get(spec.tool_id, {})

    if spec.cmd:
        cmd_parts = [spec.cmd]
    else:
        # 传递 sample_context 到 CommandPipeline
        pipeline = CommandPipeline(tool_info, sample_context=spec.sample_context)
        # ... 继续原有流程
```

### 修改 4：WorkflowService 传递 sample_context

**文件**：`app/services/workflow_service.py`

```python
return TaskSpec(
    node_id=nid,
    tool_id=tool_id,
    params=params_node,
    sample_context=c.sample_context,  # 新增：传递完整 context
    # ... 其他字段
)
```

### 修改 5：更新 data_loader 工具定义

**文件**：`config/tools/data_loader.json`

```json
{
  "parameters": {
    "sample_name": {
      "injectFrom": "context.sample",
      "required": true
    }
  }
}
```

---

## Risks / Trade-offs

### 风险 1：参数命名冲突

**风险**：`injectFrom` 注入的参数可能与用户提供的参数冲突

**缓解**：
- 优先级：用户参数 > injectFrom（显式 > 隐式）
- 如果工具定义标记为 `required`，而用户也提供了值，使用用户值

### 风险 2：向后兼容性

**风险**：修改 TaskSpec 可能破坏现有代码

**缓解**：
- `sample_context` 提供默认值 `field(default_factory=dict)`
- 现有代码不传递 sample_context 时使用空字典
- CommandPipeline 兼容 None sample_context

### 风险 3：性能影响

**风险**：额外的参数注入逻辑可能影响性能

**缓解**：
- 注入逻辑仅在命令构建时执行一次
- 时间复杂度 O(n)，n 为参数数量，通常很小（< 10）

---

## Migration Plan

### 阶段 1：实现新机制（Week 1）

1. 扩展 TaskSpec（sample_context 字段）
2. 修改 CommandPipeline（_inject_context_params）
3. 修改 LocalExecutor（传递 sample_context）
4. 修改 WorkflowService（构建 TaskSpec 时传递 sample_context）

### 阶段 2：更新工具定义（Week 2）

1. 更新 `data_loader.json` 添加 `injectFrom` 声明
2. 测试新机制是否工作
3. 移除 `workflow_service.py:207-208` 的硬编码处理

### 阶段 3：清理与文档（Week 3）

1. 移除 `data_loader.json` 的 `useParamsJson`（如果不再需要）
2. 更新工具定义文档
3. 添加示例：如何为新工具添加 sample 参数

### 回滚策略

- 保留原有代码路径（hardcoded if tool_id == "data_loader"）
- 如果新机制有问题，可以通过配置开关回滚
- Git 历史保留，可以快速 revert

---

## Open Questions

1. **Q**: 是否需要支持嵌套的 context 访问（如 `context.user.workspace`）？
   - **A**: 当前不需要，`sample_context` 是扁平字典

2. **Q**: 是否需要支持多个 injectFrom 源？
   - **A**: 当前不需要，一个参数只从一个源注入

3. **Q**: 如果 sample_context 和用户参数都提供了同一个值，优先使用哪个？
   - **A**: 用户参数优先（显式 > 隐式）

---

## Success Criteria

1. ✅ data_loader 能通过新机制接收 sample_name
2. ✅ 添加新工具（如 custom_loader）无需修改 executor 代码
3. ✅ 现有工具无需修改即可正常运行
4. ✅ 单元测试覆盖率 > 80%
5. ✅ 集成测试通过（完整工作流执行）

---

## References

- **Proposal**: `proposal.md` - 问题分析和变更概述
- **Current Code**: `app/services/workflow_service.py:207-208` - 现有硬编码处理
- **Sample Context**: `app/services/unified_workspace_manager.py:_build_sample_context`
