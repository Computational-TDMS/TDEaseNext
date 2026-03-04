# Proposal: Backend Workspace Data Access

## Why

前端交互式可视化节点需要访问后端处理后的数据才能进行渲染和分析。当前系统虽然能够执行工作流并生成输出文件，但前端无法直接访问这些文件的实际内容。

现有的 `app/api/visualization.py` 只提供：
- 文件列表查询（`/{execution_id}/data`）— 依赖脆弱的文件名模式匹配
- 文件预览（`/{execution_id}/preview`）— 仅前 100 行

这些功能不足以支持交互式可视化和工作区浏览，因为：
1. 前端交互式节点需要**全量结构化数据**加载到内存 buffer 进行用户交互
2. 节点输出文件路径可通过**工具定义的 `ports.outputs.pattern`** + `sample_context` 推导，无需额外持久化
3. 用户需要一个**文件浏览侧边栏**查看工作区文件结构和预览文件内容

此变更为后续的交互式可视化节点（FeatureMap、Spectrum Viewer、Table Viewer）提供必要的数据访问基础设施。

## What Changes

### 1. 节点输出数据 API（核心）

**重构现有端点**，基于工具定义推导输出路径（而非文件名匹配）：

```
GET /api/executions/{execution_id}/nodes/{node_id}/data
```
- 从 `executions` 表查 `workflow_snapshot` + `workspace_path` + `sample_id`
- 从 snapshot 中找 node 的 `tool_id`
- 查 `tool_registry` 得到 `ports.outputs[].pattern`
- 代入 `sample_context` 推导实际文件路径
- 解析文件返回结构化数据（columns, rows, totalRows）

### 2. 工作区文件浏览 API

**完善现有端点**并新增文件内容读取：

```
GET /api/workspaces/{user_id}/{workspace_id}/files         — 目录树（已有，完善）
GET /api/workspaces/{user_id}/{workspace_id}/file-content  — 文件内容预览
```

文件侧边栏是独立的浏览功能，与节点数据加载分离：
- 侧边栏：轻量预览（前 N 行），用于浏览
- 节点数据：全量加载，用于交互式可视化

### 3. 最新执行查询

```
GET /api/workflows/{workflow_id}/latest-execution
```
- 获取工作流的最新成功执行记录
- 用于工作流编辑模式下的数据预览

### 4. API 路由整理

重组 `visualization.py` 的路由前缀，消除混乱的 `/nodes/...` 嵌套：
- 节点数据端点移至 `/api/executions/` 下（与现有 execution API 一致）
- 工作区文件端点移至 `/api/workspaces/` 下（与现有 workspace API 一致）

## Capabilities

### New Capabilities

- **`node-data-access`**: 节点输出数据访问
  - 基于工具定义推导输出文件路径
  - 解析 TSV/CSV 返回结构化表格数据
  - 支持全量数据传输到前端

- **`workspace-file-browser`**: 工作区文件浏览
  - 目录树结构展示
  - 文件内容预览（前 N 行）
  - 文件元信息（大小、修改时间、类型）

### Modified Capabilities

- 无（现有端点将被重构替换）

## Impact

### 后端代码（修改）
- `app/api/visualization.py` → 重构为 `workspace_data.py`，整理路由
- `app/api/execution.py` — 新增节点数据端点
- `app/api/workflow.py` — 新增最新执行查询端点
- `app/services/execution_store.py` — 新增执行查询方法
- `app/services/workflow_service.py` — 复用 `_resolve_output_paths` 逻辑

### 后端代码（新增）
- `app/services/node_data_service.py` — 节点数据推导与解析服务
- `app/services/file_parser.py` — TSV/CSV/feature 等格式解析器

### 前端代码（新增，仅类型定义和 API 客户端）
- `src/services/api/workspace-data.ts` — 数据访问 API 客户端
- `src/types/workspace-data.ts` — 响应类型定义

### 数据库
- 仅查询现有表，无 schema 变更
- `executions` 表：查询 workflow_snapshot + workspace_path + sample_id
- `samples` 表：查询 sample_context

### 依赖关系
- 此变更是 `interactive-visualization` 的前置依赖
- 为交互式可视化节点提供数据访问层
- 为前端文件侧边栏提供后端 API
