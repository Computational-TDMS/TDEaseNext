## Why

当前的命令行构建（CommandBuilder）和 sample 管理机制存在系统性缺陷，导致工作流执行频繁失败：空参数被传递为 `-f None`、不支持输出路径的工具被错误添加 `-o` 标志、`sample_context` 占位符提取逻辑不完整导致 `{fasta_filename}` 缺失。这些问题的根源在于工具定义（tool definition）、命令构建（command building）、sample 上下文（sample context）三者之间缺乏统一的契约和清晰的数据流。随着后续需要接入更多工具（Python 脚本、Docker 容器、R 脚本等）以及多样本批量处理能力，当前的打补丁方式无法持续，必须从架构层面重新设计。

## What Changes

- **BREAKING** 重新设计 `config/tools/*.json` 的工具定义 Schema，建立前后端统一的契约，明确区分「参数类型」（CLI flag / positional / boolean / choice）、「输入/输出端口」（类型、模式、handle 语义）、「工具执行模式」（native command / script / docker）
- **BREAKING** 重写 `CommandBuilder`，以工具定义为唯一驱动源，消除对 tool_type 的分支硬编码；参数过滤（空值/None）作为管线的第一步而非散落在多处
- **BREAKING** 重新设计 sample 管理体系：sample 不再是单一的 `{sample: string}` 上下文，而是一个结构化的 Sample Table（sample_id → 关联文件映射），支持 raw 文件、fasta 数据库等多种关联文件，支持多样本批量处理
- 重构 `_resolve_output_paths` 和 `_resolve_input_paths` 中的占位符解析，基于 Sample Table 而非 flat dict，消除 `_extract_sample_ctx_from_workflow` 中的脆弱推导逻辑
- 统一前端 `PropertyPanel` 和后端 `WorkflowNormalizer` 的参数序列化逻辑，前端根据工具定义 Schema 渲染参数表单，仅序列化用户实际填写的值
- 为未来交互式可视化节点（数据筛选、图表展示）预留节点类型扩展点

## Capabilities

### New Capabilities

- `command-execution`: 基于工具定义驱动的命令构建管线，统一处理参数过滤、flag 映射、positional 参数排序、输出路径策略，消除 tool_type 分支硬编码
- `sample-management`: 结构化的 Sample Table 设计，支持多样本、多关联文件（raw + fasta + 其他），占位符解析基于 Sample Table，替代当前 flat dict 方案；支持批量处理和增量执行
- `tool-node-contract`: 前后端统一的工具定义 Schema 契约，明确端口定义（输入/输出/handle）、参数类型与 UI 元数据、执行模式声明，确保前端渲染与后端执行的一致性
- `visualization-node-design`: 交互式可视化/数据筛选节点的类型扩展设计，支持后端数据处理完成后前端进行交互式筛选与可视化展示

### Modified Capabilities

（当前 `openspec/specs/` 无已有 spec，不涉及修改）

## Impact

**后端代码**:
- `app/core/executor/command_builder.py` — 完全重写
- `app/services/workflow_service.py` — 重构 `_resolve_output_paths`、`_resolve_input_paths`，引入 Sample Table
- `app/api/workflow.py` — 重构 `_extract_sample_ctx_from_workflow`，移除脆弱推导逻辑，改为 Sample Table 驱动
- `src/workflow/normalizer.py` — 调整参数过滤和节点标准化逻辑
- `config/tools/*.json` — 全部工具定义按新 Schema 迁移

**前端代码**:
- `TDEase-FrontEnd/src/components/workflow/PropertyPanel.vue` — 基于工具定义 Schema 渲染参数表单
- `TDEase-FrontEnd/src/services/workflow.ts` — 统一参数序列化逻辑
- `TDEase-FrontEnd/config/tools/*.json` — 同步更新为新 Schema

**数据库**:
- `workflows` 表可能需要新增 `sample_table` 列或在 `metadata` 中扩展 sample 定义结构

**测试**:
- `tests/test.json` — 按新 Schema 更新
- 需要新增针对 CommandBuilder 的测试用例，覆盖各类工具类型

**API 兼容性**:
- `/api/workflows/execute` 的 `parameters.sample_context` 参数格式将变更为 Sample Table 结构（BREAKING）
- `/api/workflows/{id}/execute-batch` 的批量执行逻辑将简化，统一基于 Sample Table
