# Proposal: Sample-Based Path Mapping System

**Change**: `improve-command-executor`
**Date**: 2026-03-03
**Status**: Draft

---

## Why

TDEase FlowEngine 当前的命令执行系统在 **Sample-Based Execution** 的路径映射上存在断裂，导致工具无法正确获取 sample 信息和生成正确的输出文件名。

### 核心问题诊断

**问题 1：`sample_name` 传递依赖 `useParamsJson`**

当前流程：
```
workflow_service.py:208
  → 注入 sample_name 到 spec.params
  → CommandPipeline Step 4b 放入 --params JSON
  → 只有 useParamsJson=true 的工具才能拿到
```

**断裂点**：
- `data_loader.py` 依赖 `--params` 中的 `sample_name`
- 但大部分工具（toppic, topfd, msconvert）**没有** `useParamsJson=true`
- 导致这些工具**无法获取 sample 信息**

**问题 2：工具输出 pattern 和实际输出不一致**

工具定义的 pattern（如 `{sample}_ms2.msalign`）在 `_resolve_output_paths` 中解析，但：
- **TopPIC/TopFD 等工具自己控制输出文件名**
- 工具不接受 `--output` 参数（`flagSupported: false`）
- 导致系统预期输出 `{sample}_ms2.msalign`，但实际工具输出可能不同

**问题 3：Sample Context 变量在命令构建时不可用**

`_build_sample_context` 自动推导：
- `sample`, `input_basename`, `input_ext`, `raw_path` 等
- 但这些变量**只在 workflow_service.py 使用**，CommandPipeline 看不到
- 无法在命令模板中使用这些变量

**问题 4：输入路径映射硬编码**

`_resolve_input_paths` 依赖：
- `positional` + `positionalOrder` 硬编码顺序
- 没有灵活的端口到参数映射
- 无法处理工具特定的路径需求

### 为什么现在需要修复

1. **data_loader.py 要求 `sample_name` 必需**（line 32-33），但大部分工具无法传递
2. **Sample-Based Execution 是 TDEase 的核心特色**，但路径映射系统不完整
3. **用户无法自定义 sample 名**并期望工具正确使用
4. **输入输出链路不透明**，用户不知道文件会生成在哪里

---

## What Changes

### 核心设计原则

**由 FlowEngine 控制一切，工具只管执行**

- FlowEngine 负责路径解析、sample 上下文注入、输出文件名预期
- 工具节点只需要按预期路径输出文件即可
- 如果工具自己命名文件，FlowEngine 负责重命名/验证

### 变更 1：统一 Sample Context 注入

**新增**：`TaskSpec` 增加 `sample_context: Dict[str, str]` 字段

**变更**：
- `WorkflowService` 构建完整 `sample_context`（包含所有推导变量）
- 传递给 `LocalExecutor.execute(spec: TaskSpec)`
- `CommandPipeline` 可访问 `sample_context` 进行变量替换

**示例**：
```python
# workflow_service.py
spec = TaskSpec(
    node_id=node_id,
    tool_id=tool_id,
    params=params,
    sample_context=sample_context,  # 新增
    ...
)

# command_pipeline.py
class CommandPipeline:
    def __init__(self, tool_def, sample_context=None):
        self.sample_context = sample_context or {}

    def _resolve_variable(self, value):
        if isinstance(value, str) and value.startswith("${"):
            var_name = value[2:-1]
            return self.sample_context.get(var_name, value)
        return value
```

### 变更 2：强制 `sample_name` 注入到所有工具

**方案 A**：修改 CommandPipeline，无条件注入 `sample_name`

**变更点**：
- `CommandPipeline.build()` 中，将 `sample_context["sample"]` 注入到 `param_values["sample_name"]`
- 不再依赖 `useParamsJson`
- 所有工具都可以通过 `--params` 或参数标志获取 sample_name

**示例**：
```python
def build(self, param_values, input_files, output_dir, sample_context=None):
    # 强制注入 sample_name
    if sample_context and "sample" in sample_context:
        param_values["sample_name"] = sample_context["sample"]

    # 继续原有流程...
```

**方案 B**：在工具定义中明确声明 sample 参数

**工具定义扩展**：
```json
{
  "parameters": {
    "sample_name": {
      "type": "value",
      "flag": "--sample-name",
      "injectFrom": "context.sample",
      "required": true
    }
  }
}
```

**推荐**：方案 A（更简单，向后兼容）

### 变更 3：输出文件验证与重命名

**新增**：`OutputValidator` 服务

**职责**：
1. 执行前：计算预期输出路径（基于 pattern + sample_context）
2. 执行后：检查实际输出文件
3. 如果工具自己命名文件，自动重命名为预期名称
4. 如果文件不存在或命名不匹配，报错

**示例**：
```python
class OutputValidator:
    def validate_and_rename(self, tool_id, actual_dir, expected_outputs):
        expected_paths = [...]
        actual_files = os.listdir(actual_dir)

        # 简单情况：工具按预期命名
        if all(p.exists() for p in expected_paths):
            return

        # 复杂情况：工具自己命名，需要重命名
        if len(actual_files) == len(expected_paths):
            for actual, expected in zip(actual_files, expected_paths):
                shutil.move(actual, expected)
        else:
            raise FileNotFoundError(f"Expected {expected_paths}, found {actual_files}")
```

### 变更 4：输入端口到参数的灵活映射

**新增**：工具定义中的 `paramMapping` 字段

**配置示例**：
```json
{
  "ports": {
    "inputs": [
      {
        "id": "ms2_file",
        "paramKey": "input",  # 映射到 parameters.input
        "positional": true,
        "positionalOrder": 0
      }
    ]
  }
}
```

**变更点**：
- `_resolve_input_paths` 使用 `paramKey` 而非硬编码端口 ID
- 支持一个端口映射到多个参数（如 `--input`, `--input-format`）

### 变更 5：工具定义 Schema 清理

**移除**：对已废弃字段的依赖

**明确**：
- `output_patterns` vs `ports.outputs[].pattern`：统一使用后者
- `positional_params` vs `ports.inputs[].positional`：统一使用后者
- `outputs` vs `ports.outputs`：统一使用后者

---

## Capabilities

### New Capabilities

#### `sample-context-injection`
统一的 Sample Context 注入系统

**覆盖范围**：
- TaskSpec 扩展（sample_context 字段）
- CommandPipeline 访问 sample_context
- 自动推导变量（sample, input_basename, input_ext, raw_path, fasta_path）
- 变量替换机制（${var} 语法）

#### `output-validation`
输出文件验证与重命名

**覆盖范围**：
- 预期输出路径计算
- 实际输出检测
- 自动重命名机制
- 错误报告

#### `param-mapping`
输入端口到参数的灵活映射

**覆盖范围**：
- paramKey 配置
- 一个端口多参数映射
- 位置参数顺序控制

### Modified Capabilities

#### `tool-definition-schema` (Modified)
清理工具定义 Schema

**变更内容**：
- 明确使用 `ports.outputs[].pattern`
- 明确使用 `ports.inputs[].positional`
- 新增 `paramMapping` 支持
- 移除废弃字段

---

## Impact

### 受影响的代码模块

**核心变更**：
1. `app/core/executor/base.py` - TaskSpec 增加 sample_context 字段
2. `app/core/executor/command_pipeline.py` - 访问 sample_context，强制注入 sample_name
3. `app/core/executor/local.py` - 传递 sample_context 到 CommandPipeline
4. `app/services/workflow_service.py` - 构建完整 sample_context 并传递
5. `app/services/unified_workspace_manager.py` - _build_sample_context 已有，无需修改

**新增模块**：
1. `app/core/executor/output_validator.py` - 输出验证与重命名

### 向后兼容

**保持兼容**：
- 现有工具定义继续工作
- `useParamsJson` 仍然有效（但不再是必需）
- 现有的参数构建逻辑保持不变

**迁移路径**：
- 旧工具无需修改
- 新工具可以使用新的 sample_context 功能
- 逐步迁移到新的 paramMapping 机制

---

## Migration Strategy

### 阶段 1：Sample Context 注入（Week 1）
- 扩展 TaskSpec（sample_context）
- 修改 LocalExecutor 传递 sample_context
- 修改 CommandPipeline 访问 sample_context
- 强制注入 sample_name

### 阶段 2：输出验证（Week 2）
- 实现 OutputValidator
- 集成到 LocalExecutor（execute 后验证）
- 支持自动重命名

### 阶段 3：参数映射（Week 3）
- 扩展工具定义 Schema（paramMapping）
- 修改 _resolve_input_paths 使用 paramMapping
- 更新工具定义文档

### 阶段 4：测试与文档（Week 4）
- 单元测试
- 集成测试
- 迁移指南
- 用户文档

---

## Success Criteria

1. ✅ 所有工具都能获取 `sample_name`（不依赖 useParamsJson）
2. ✅ Sample context 变量可在命令构建中使用
3. ✅ 输出文件验证正确工作
4. ✅ 工具自己命名文件时能正确重命名
5. ✅ 现有工具无需修改即可运行
6. ✅ 测试覆盖率 > 80%
7. ✅ 文档完整

---

## References

- **TDEase 现状**: Sample-Based Execution, samples.json, _build_sample_context
- **问题点**: CommandPipeline 缺少 sample_context，sample_name 传递断裂
- **参考**: Snakemake {wildcards} 变量系统
