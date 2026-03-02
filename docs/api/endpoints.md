# TDEase Backend API 文档

## 概述

TDEase 后端提供了完整的 RESTful API 体系来管理工作流和执行。API 采用直接集成 Snakemake 引擎的方式，从前端接收工作流 JSON，直接构建并执行 Snakemake Workflow 对象，无需生成中间文件。

## 1. 工作流管理 API

### 核心工作流操作

#### 列出工作流
- **端点**: `GET /api/workflows`
- **参数**:
  - `page` (int, 可选): 页码，默认 1
  - `page_size` (int, 可选): 每页数量，默认 20
- **响应**: `WorkflowListResponse` - 包含工作流列表、总数和分页信息

#### 获取工作流详情
- **端点**: `GET /api/workflows/{workflow_id}`
- **响应**: `WorkflowResponse` - 包含完整的工作流信息

#### 创建工作流
- **端点**: `POST /api/workflows`
- **请求体**: `WorkflowCreate`
- **响应**: `WorkflowResponse` - 创建的工作流信息

#### 更新工作流
- **端点**: `PUT /api/workflows/{workflow_id}`
- **请求体**: `WorkflowUpdate`
- **响应**: `WorkflowResponse` - 更新后的工作流信息

#### 删除工作流
- **端点**: `DELETE /api/workflows/{workflow_id}`
- **响应**: `SuccessResponse` - 删除结果

#### 导入工作流
- **端点**: `POST /api/workflows/import`
- **请求体**: `WorkflowImportRequest` - 支持 Galaxy 工作流格式（GA、Format2）或 VueFlow JSON
- **响应**: `WorkflowResponse` - 导入的工作流信息

#### 获取工作流状态
- **端点**: `GET /api/workflows/{workflow_id}/status`
- **响应**: `WorkflowStatus` - 工作流状态信息

#### 导出工作流为 CWL
- **端点**: `GET /api/workflows/{workflow_id}/export/cwl`
- **响应**: CWL 格式的工作流文档 (YAML)

## 2. 工作流执行 API

### 直接执行工作流（推荐方式）

#### 执行工作流
- **端点**: `POST /api/workflows/execute`
- **请求体**:
  ```json
  {
    "workflow": {
      // VueFlow JSON 格式的工作流定义
      "metadata": {...},
      "nodes": [...],
      "edges": [...]
    },
    "tools": [
      // 工具配置数组
      {
        "id": "tool_id",
        "toolPath": "...",
        "inputs": [...],
        "outputs": [...],
        ...
      }
    ],
    "parameters": {
      "cores": 4,
      "useConda": true
    }
  }
  ```
- **响应**: `WorkflowExecutionResponse`
  ```json
  {
    "executionId": "execution_id",
    "status": "pending|running|completed|failed|cancelled",
    "startTime": "ISO8601 timestamp",
    "endTime": "ISO8601 timestamp or null",
    "progress": 0-100,
    "logs": [],
    "nodes": [],
    "results": null
  }
  ```

**说明**: 此端点直接从前端 JSON 构建 Snakemake Workflow 对象并执行，无需生成 Snakefile 或 config.yaml 文件。

### 批量执行工作流

#### 保存批量配置
- **端点**: `POST /api/workflows/{workflow_id}/batch-config`
- **请求体**: `BatchConfig`
  ```json
  {
    "samples": [
      {
        "sample_id": "sample1",
        "placeholder_values": {
          "sample": "sample1",
          "fasta_file": "/path/to/sample1.fasta",
          "input_file": "/path/to/sample1.mzML"
        }
      }
    ],
    "global_params": {
      "cores": 4,
      "useConda": true
    }
  }
  ```
- **响应**: `SuccessResponse`

#### 获取批量配置
- **端点**: `GET /api/workflows/{workflow_id}/batch-config`
- **响应**: `BatchConfig` - 批量配置信息

#### 批量执行
- **端点**: `POST /api/workflows/{workflow_id}/execute-batch`
- **请求体**: `BatchConfig` (可选，如果不提供则使用已保存的配置)
- **响应**: `WorkflowExecutionResponse[]` - 每个样品的执行响应数组

**说明**: 批量执行会为每个样品创建独立的execution，替换工作流中的占位符变量（如 `{sample}`, `{fasta_file}`）为实际值，然后并行或串行执行多个样品的工作流。

## 3. 执行管理 API

### 执行状态和日志

#### 获取执行状态
- **端点**: `GET /api/executions/{execution_id}`
- **响应**: `WorkflowExecutionResponse` - 包含执行状态、进度、节点状态等

#### 获取执行日志
- **端点**: `GET /api/executions/{execution_id}/logs`
- **参数**:
  - `level` (string, 可选): 日志级别过滤 (info, warning, error)
- **响应**: 日志条目数组

#### 获取执行节点列表
- **端点**: `GET /api/executions/{execution_id}/nodes`
- **响应**: 节点执行状态数组

#### 获取特定节点状态
- **端点**: `GET /api/executions/{execution_id}/nodes/{node_id}`
- **响应**: 节点执行详细信息，包括状态、日志、时间戳等

#### 停止执行
- **端点**: `POST /api/executions/{execution_id}/stop`
- **响应**: `SuccessResponse` - 停止结果

#### 下载执行结果
- **端点**: `GET /api/executions/{execution_id}/download`
- **参数**:
  - `format` (string, 可选): 下载格式
- **响应**: 文件流

## 4. API 架构

### 执行流程

1. **前端发送工作流 JSON** → `POST /api/workflows/execute`
2. **后端规范化验证** → 使用 `WorkflowNormalizer` 和 `WorkflowValidator`
3. **构建 Snakemake Workflow** → 使用 `SnakemakeWorkflowBuilder` 直接构建 Workflow 对象
4. **执行工作流** → 使用 Snakemake Python API (`Workflow.execute()`) 执行
5. **实时状态更新** → 通过 `SnakemakeLogHandler` 捕获日志并更新数据库
6. **前端轮询状态** → `GET /api/executions/{execution_id}` 获取最新状态

### 关键组件

- **WorkflowNormalizer**: 规范化前端工作流 JSON
- **WorkflowValidator**: 验证工作流的有效性
- **RuleBuilder**: 将前端节点转换为 Snakemake Rule 对象
- **SnakemakeWorkflowBuilder**: 构建完整的 Snakemake Workflow
- **SnakemakeExecutor**: 执行 Snakemake Workflow
- **ExecutionStore**: 持久化执行状态和节点状态

### 数据库表

- **workflows**: 存储工作流定义
- **executions**: 存储执行记录
- **execution_nodes**: 存储节点级别的执行状态（支持逐节点执行跟踪）

## 5. 数据模型

### WorkflowJSON (前端格式)
```typescript
interface WorkflowJSON {
  metadata: {
    id?: string
    name: string
    description?: string
  }
  nodes: Array<{
    id: string
    type: string
    data: {
      type: string  // tool_id
      params: Record<string, any>
    }
    position: { x: number, y: number }
  }>
  edges: Array<{
    id: string
    source: string
    target: string
    sourceHandle?: string
    targetHandle?: string
  }>
}
```

### ExecutionResponse
```typescript
interface WorkflowExecutionResponse {
  executionId: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  startTime: string  // ISO8601
  endTime: string | null  // ISO8601
  progress: number  // 0-100
  logs: Array<{
    timestamp: string
    level: string
    message: string
  }>
  nodes: Array<{
    nodeId: string
    status: string
    progress: number
  }>
  results: any | null
}
```

## 6. 批量处理

批量处理支持多样品批量执行工作流，通过JSON格式的配置表格定义每个样品的占位符变量值。

### 批量配置格式

```json
{
  "samples": [
    {
      "sample_id": "sample1",
      "placeholder_values": {
        "sample": "sample1",
        "fasta_file": "/path/to/sample1.fasta"
      }
    }
  ],
  "global_params": {
    "cores": 4,
    "useConda": true
  }
}
```

### 占位符替换

在执行时，工作流中的占位符会被替换为对应样品的实际值：
- `{sample}` → 样品的sample_id
- `{fasta_file}` → 样品的fasta_file路径
- 其他占位符按照`placeholder_values`中的键值对进行替换

## 7. 注意事项

- 所有 API 端点返回 JSON 格式
- 执行是异步的，需要通过轮询获取状态
- 工作流直接从前端 JSON 执行，无需编译步骤
- 支持节点级别的执行状态跟踪
- CORS 已配置，支持跨域请求
- 执行日志实时更新到数据库，可通过 API 查询
- 批量执行会为每个样品创建独立的execution，可以单独跟踪每个样品的执行状态

## 7. 错误处理

所有 API 端点遵循统一的错误响应格式：

```json
{
  "error": "Error message",
  "detail": "Detailed error information"
}
```

常见错误码：
- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误
