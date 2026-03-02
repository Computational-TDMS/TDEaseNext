## Why

当前 TDEase 系统存在三个关键问题导致占位符解析不稳定：

1. **危险的静默后备机制**：`workflow_service.py:47-55` 使用 `re.sub(r"\{\w+\}", "out")` 将任何未解析的占位符替换为 "out"，导致 `{sample}_proteoforms.tsv` 变成 `out_proteoforms.tsv` 而不报错

2. **样品定义混乱**：样品来源不统一 - 可能来自 `ExecutionRequest.samples`、`params.sample_context`、`data_loader.input_sources`，或魔法字符串 `["default"]`，缺乏单一数据源

3. **缺少工作区隔离**：所有用户共享同一工作空间，无法支持多用户多项目的并行开发与测试

## What Changes

### 核心架构变更

- **实现用户-工作区-样品层次结构**：
  - `data/users/{user_id}/workspaces/{workspace_id}/samples.json` - 样品定义
  - `data/users/{user_id}/workspaces/{workspace_id}/workflows/` - 工作流定义
  - `data/users/{user_id}/workspaces/{workspace_id}/executions/` - 执行记录
  - `data/users/{user_id}/workspaces/{workspace_id}/data/` - 共享数据文件

- **移除危险的占位符后备**：
  - **BREAKING**: 删除 `re.sub(r"\{\w+\}", "out")` 静默替换逻辑
  - 占位符缺失时抛出明确的 `ValueError` 异常
  - 在执行前验证所有必需占位符

- **统一样品上下文来源**：
  - 工作流执行时从工作区的 `samples.json` 加载样品上下文
  - 样品上下文包含所有占位符所需的值
  - 支持多样本并行执行

### 服务层重构

- **合并 WorkspaceManager 服务**：
  - 当前存在 `app/services/workspace_manager.py`（单一工作空间管理）
  - 新增 `app/services/user_workspace_manager.py`（层次化工作空间管理）
  - **需要重构**：统一为单一服务，避免服务矛盾

- **更新 WorkflowService**：
  - 执行时从 `UserWorkspaceManager` 加载样品上下文
  - 使用严格的占位符验证
  - 支持按样品隔离执行

### 测试迁移

- **迁移现有测试**到新工作区结构：
  - 创建测试用户 `test_user`
  - 创建测试工作区 `test_workspace`
  - 迁移测试数据文件到工作区 `data/` 目录
  - 更新测试用例使用新的路径结构

## Capabilities

### New Capabilities

- **user-workspace-hierarchy**: 实现用户、工作区、样品的层次化管理
  - 多用户支持：每个用户拥有独立的工作空间
  - 多工作区：每个用户可创建多个工作区（项目）
  - 工作区隔离：样品、工作流、执行记录完全隔离
  - 样品管理：在工作区级别定义和管理样品列表

- **placeholder-resolution**: 严格且安全的占位符解析系统
  - 占位符提取：从工具输出模式中自动提取必需占位符
  - 上下文验证：执行前验证样品上下文包含所有必需占位符
  - 明确错误：占位符缺失时抛出包含详细信息的异常
  - 上下文推导：自动推导常用值（basename、目录、扩展名）

- **sample-context-management**: 样品上下文管理
  - 样品定义：在 `samples.json` 中定义样品及其上下文
  - 上下文查询：按样品ID查询上下文
  - 上下文合并：合并显式定义和自动推导的值
  - 批量处理：支持多样本批量执行

### Modified Capabilities

- **workflow-execution**: 工作流执行
  - 从工作区加载样品上下文
  - 按样品隔离执行目录
  - 严格的占位符验证
  - 支持多样本并行执行

## Impact

### 代码影响

- **app/services/**
  - `workflow_service.py`: 更新以使用 `UserWorkspaceManager` 加载样品上下文
  - `user_workspace_manager.py`: 新增层次化工作区管理服务
  - `workspace_manager.py`: **需要重构** - 与 `UserWorkspaceManager` 合并或明确职责划分

- **app/api/**
  - 新增 `/api/users/{user_id}/workspaces` - 工作区管理端点
  - 新增 `/api/users/{user_id}/workspaces/{workspace_id}/samples` - 样品管理端点
  - 更新 `/api/workflows/execute` - 支持工作区路径和样品列表

- **app/schemas/**
  - 新增样品相关的 Pydantic 模型
  - 更新执行请求模型以支持工作区和样品

- **tests/**
  - 迁移现有测试到新工作区结构
  - 新增工作区和样品管理的测试用例

### API 影响

- **BREAKING**: 工作流执行请求格式变更
  - 旧: `workspace_path` + `samples` 数组
  - 新: `user_id` + `workspace_id` + `sample_ids` 数组

- **新增**: 样品管理 API
  - `GET /api/users/{user_id}/workspaces/{workspace_id}/samples`
  - `POST /api/users/{user_id}/workspaces/{workspace_id}/samples`
  - `PUT /api/users/{user_id}/workspaces/{workspace_id}/samples/{sample_id}`
  - `DELETE /api/users/{user_id}/workspaces/{workspace_id}/samples/{sample_id}`

### 数据影响

- **文件结构变更**:
  - 旧: `data/workflows/{workflow_id}/` - 扁平结构
  - 新: `data/users/{user_id}/workspaces/{workspace_id}/` - 层次结构

- **测试数据迁移**:
  - 测试文件从 `data/` 移至 `data/users/test_user/workspaces/test_workspace/data/`
  - 测试工作流移至工作区 `workflows/` 目录
