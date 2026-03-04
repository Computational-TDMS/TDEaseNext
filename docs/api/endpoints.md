# TDEase Backend API 文档

**版本**: 2.0 (新架构)
**更新日期**: 2026-03-02

## 概述

TDEase 后端提供了完整的 RESTful API 体系来管理工作流和执行。新架构采用 Schema-Driven 设计，通过 Tool Definition Schema 统一工具定义，使用 UnifiedWorkspaceManager 管理工作区和样品。

---

## 1. 工作流管理 API

### 获取所有工作流
- **端点**: `GET /api/workflows`
- **参数**:
  - `page` (int, 可选): 页码，默认 1
  - `page_size` (int, 可选): 每页数量，默认 20
- **响应**:
```json
{
  "workflows": [...],
  "total": 20,
  "page": 1,
  "page_size": 20
}
```

### 获取工作流详情
- **端点**: `GET /api/workflows/{workflow_id}`
- **响应**:
```json
{
  "id": "workflow_id",
  "name": "Workflow Name",
  "description": "...",
  "vueflow_data": "{...}",
  "status": "active",
  "created_at": "2026-03-02T...",
  "updated_at": "2026-03-02T..."
}
```

### 创建工作流
- **端点**: `POST /api/workflows`
- **请求体**:
```json
{
  "id": "workflow_id",
  "name": "Workflow Name",
  "description": "Description",
  "vueflow_data": "{...}",
  "workspace_path": "path/to/workspace"
}
```
- **响应**: 创建的工作流信息

### 更新工作流
- **端点**: `PUT /api/workflows/{workflow_id}`
- **请求体**: 同创建
- **响应**: 更新后的工作流信息

### 删除工作流
- **端点**: `DELETE /api/workflows/{workflow_id}`
- **响应**:
```json
{
  "success": true,
  "message": "Workflow deleted"
}
```

---

## 2. 工作流执行 API (新架构)

### 执行工作流 - 单样本

- **端点**: `POST /api/workflows/execute`
- **请求体**:
```json
{
  "workflow_id": "wf_test_full",
  "user_id": "test_user",
  "workspace_id": "test_workspace",
  "sample_ids": ["sample1"]
}
```
- **参数说明**:
  - `workflow_id`: 工作流ID（从数据库加载）
  - `user_id`: 用户ID
  - `workspace_id`: 工作区ID
  - `sample_ids`: 样品ID列表

- **响应**:
```json
{
  "executionId": "exec_20260302_123456",
  "status": "pending",
  "startTime": "2026-03-02T12:34:56Z",
  "endTime": null,
  "progress": 0,
  "nodes": [],
  "results": null
}
```

**说明**：
- 后端从 `samples.json` 加载样品上下文
- 自动解析占位符（`{sample}`, `{fasta_filename}` 等）
- 使用 CommandPipeline 构建命令

### 执行工作流 - 批量多样本

- **端点**: `POST /api/workflows/{workflow_id}/execute-batch`
- **URL 参数**:
  - `workflow_id`: 工作流ID

- **请求体**:
```json
{
  "user_id": "test_user",
  "workspace_id": "test_workspace",
  "sample_ids": ["sample1", "sample2", "sample3"]
}
```

- **响应**:
```json
{
  "executionIds": ["exec_1", "exec_2", "exec_3"],
  "total": 3,
  "success": 3,
  "failed": 0
}
```

**说明**：
- 为每个样品创建独立的 execution
- 串行执行（未来可改为并行）
- 每个样品有自己的输出目录

### 获取执行状态

- **端点**: `GET /api/executions/{execution_id}`
- **响应**:
```json
{
  "id": "exec_20260302_123456",
  "workflow_id": "wf_test_full",
  "status": "running",
  "startTime": "2026-03-02T12:34:56Z",
  "endTime": null,
  "progress": 45,
  "nodes": [
    {
      "id": "data_loader_1",
      "status": "completed",
      "startTime": "12:34:56",
      "endTime": "12:35:10",
      "progress": 100
    },
    {
      "id": "msconvert_1",
      "status": "running",
      "progress": 60
    }
  ]
}
```

### 取消执行

- **端点**: `POST /api/executions/{execution_id}/cancel`
- **响应**:
```json
{
  "success": true,
  "message": "Execution cancelled"
}
```

### 获取执行日志

- **端点**: `GET /api/executions/{execution_id}/logs`
- **参数**:
  - `level` (可选): 日志级别 (info, warning, error)
- **响应**:
```json
{
  "logs": [
    {
      "timestamp": "2026-03-02T12:34:56Z",
      "level": "info",
      "message": "Starting workflow execution"
    }
  ]
}
```

---

## 3. 工具管理 API

### 获取所有工具 Schema

- **端点**: `GET /api/tools/schemas`
- **响应**:
```json
{
  "schema": {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Tool Definition",
    "type": "object",
    "properties": {...}
  },
  "tools": [
    {
      "id": "topfd",
      "name": "TopFD",
      "version": "1.0.0",
      "executionMode": "native",
      "command": {...},
      "ports": {...},
      "parameters": {...}
    }
  ]
}
```

**说明**：
- 返回 Tool Definition Schema
- 返回所有工具的定义
- 前端使用此接口动态渲染工具配置面板

### 获取单个工具定义

- **端点**: `GET /api/tools/{tool_id}`
- **响应**: 单个工具的完整定义

### 预览工具命令 (新增)

- **端点**: `POST /api/tools/preview`
- **请求体**:
```json
{
  "tool_id": "topfd",
  "param_values": {
    "mass": "50000",
    "mz": "0.02"
  },
  "input_files": {},
  "output_target": null
}
```

**注意**: `input_files` 为空对象、`output_target` 为 null 时，返回的命令将使用占位符（如 `<ms2_file>`、`<output_dir>`），而不是实际文件路径。

- **响应**:
```json
{
  "tool_id": "topfd",
  "command": "topfd -m 50000 -o <output_dir> <ms2_file>",
  "command_parts": ["topfd", "-m", "50000", "-o", "<output_dir>", "<ms2_file>"],
  "trace": {
    "tool_id": "topfd",
    "execution_mode": "native",
    "executable": "topfd",
    "filtered_params": {
      "mass": "50000",
      "mz": "0.02"
    },
    "input_files": {},
    "output_target": null,
    "output_flag": {
      "flag": "-o",
      "value": "<output_dir>"
    },
    "parameter_flags": ["-m", "50000"],
    "input_flags": [],
    "positional_args": ["<ms2_file>"],
    "cmd_parts": ["topfd", "-m", "50000", "-o", "<output_dir>", "<ms2_file>"]
  }
}
```

**说明**：
- 使用与实际执行相同的 `CommandPipeline` 逻辑
- 自动过滤空参数（null/空字符串/"none"）
- 支持所有执行模式（native/script/docker/interactive）
- 返回详细 trace 信息用于调试
- 前端参数面板应使用此 API，传入空的 `input_files` 和 `null` 的 `output_target` 获取占位符预览

---

## 4. 可视化 API (新增)

### 获取节点输出数据

- **端点**: `GET /api/nodes/{execution_id}/data`
- **参数**:
  - `node_id` (可选): 节点ID，如果不指定则返回所有节点输出

- **响应**:
```json
{
  "execution_id": "exec_123",
  "node_id": "topfd_1",
  "workspace_path": "data/users/test_user/workspaces/test_workspace",
  "results_dir": ".../executions/exec_123/results",
  "files": [
    {
      "name": "sample_ms1.msalign",
      "path": "/full/path/to/sample_ms1.msalign",
      "size": 1234567,
      "extension": ".msalign",
      "relative_path": "executions/exec_123/results/sample_ms1.msalign"
    }
  ],
  "total_files": 1
}
```

### 预览表格数据

- **端点**: `GET /api/nodes/{execution_id}/preview`
- **查询参数**:
  - `file_path`: 相对路径（相对于 results 目录）
  - `max_rows`: 最大行数，默认 100

- **响应**:
```json
{
  "execution_id": "exec_123",
  "file_path": "sample_ms1.msalign",
  "file_name": "sample_ms1.msalign",
  "file_size": 1234567,
  "file_type": "tabular",
  "columns": ["Sequence", "Proteoform", "EValue"],
  "row_count": 50,
  "preview_rows": [
    {"Sequence": "1", "Proteoform": "...", "EValue": "0.001"},
    ...
  ],
  "max_rows_limit": 100
}
```

### 浏览工作区文件

- **端点**: `GET /api/nodes/workspaces/{user_id}/{workspace_id}/files`
- **响应**:
```json
{
  "user_id": "test_user",
  "workspace_id": "test_workspace",
  "workspace_path": "data/users/test_user/workspaces/test_workspace",
  "tree": [
    {
      "name": "executions",
      "type": "directory",
      "path": "executions",
      "children": [...]
    },
    {
      "name": "data",
      "type": "directory",
      "path": "data",
      "children": [...]
    }
  ]
}
```

---

## 5. 工作区管理 API

### 创建工作区

- **端点**: `POST /api/workspaces`
- **请求体**:
```json
{
  "user_id": "test_user",
  "workspace_id": "new_workspace",
  "name": "New Workspace",
  "description": "Description"
}
```
- **响应**: 创建的工作区信息

### 列出工作区的样品

- **端点**: `GET /api/workspaces/{user_id}/{workspace_id}/samples`
- **响应**:
```json
{
  "user_id": "test_user",
  "workspace_id": "test_workspace",
  "samples": [
    {
      "id": "sample1",
      "name": "Sample 1",
      "context": {...}
    }
  ]
}
```

---

## 6. 文件管理 API

### 上传文件

- **端点**: `POST /api/files/upload`
- **请求**: multipart/form-data
- **参数**:
  - `file`: 文件
  - `user_id`: 用户ID
  - `workspace_id`: 工作区ID
  - `target_path`: 目标路径（可选）

- **响应**:
```json
{
  "success": true,
  "file_path": "data/users/test_user/workspaces/test_workspace/data/raw/file.raw"
}
```

### 下载文件

- **端点**: `GET /api/files/download`
- **查询参数**:
  - `file_path`: 文件路径
- **响应**: 文件内容

---

## API 使用示例

### Python 示例

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. 执行工作流
response = requests.post(f"{BASE_URL}/api/workflows/execute", json={
    "workflow_id": "wf_test_full",
    "user_id": "test_user",
    "workspace_id": "test_workspace",
    "sample_ids": ["sample1"]
})
execution = response.json()
print(f"Execution ID: {execution['executionId']}")

# 2. 查询执行状态
exec_id = execution['executionId']
response = requests.get(f"{BASE_URL}/api/executions/{exec_id}")
status = response.json()
print(f"Status: {status['status']}, Progress: {status['progress']}%")

# 3. 获取节点输出数据
response = requests.get(f"{BASE_URL}/api/nodes/{exec_id}/data", params={
    "node_id": "topfd_1"
})
data = response.json()
print(f"Output files: {len(data['files'])}")

# 4. 预览表格数据
if data['files']:
    response = requests.get(f"{BASE_URL}/api/nodes/{exec_id}/preview", params={
        "file_path": data['files'][0]['relative_path'],
        "max_rows": 50
    })
    preview = response.json()
    print(f"Columns: {preview['columns']}")
    print(f"Rows: {preview['row_count']}")
```

### cURL 示例

```bash
# 1. 执行工作流
curl -X POST "http://localhost:8000/api/workflows/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "wf_test_full",
    "user_id": "test_user",
    "workspace_id": "test_workspace",
    "sample_ids": ["sample1"]
  }'

# 2. 查询执行状态
curl "http://localhost:8000/api/executions/{execution_id}"

# 3. 获取工具定义
curl "http://localhost:8000/api/tools/schemas"

# 4. 预览数据文件
curl "http://localhost:8000/api/nodes/{execution_id}/preview?file_path=output.tsv&max_rows=100"
```

---

## 错误响应

所有错误响应遵循统一格式：

```json
{
  "error": "Error Type",
  "detail": "Detailed error message",
  "request_id": "uuid"
}
```

常见 HTTP 状态码：
- `400`: 请求参数错误
- `404`: 资源不存在
- `422`: 数据验证失败
- `500`: 服务器内部错误

---

## WebSocket API

### 连接到执行流

- **端点**: `ws://localhost:8000/ws/executions/{execution_id}`
- **消息格式**:
```json
{
  "type": "node_update",
  "data": {
    "node_id": "topfd_1",
    "status": "running",
    "progress": 50
  }
}
```

消息类型：
- `node_update`: 节点状态更新
- `log`: 日志输出
- `execution_complete`: 执行完成

---

## 相关文档

- [架构文档](../ARCHITECTURE.md) - 系统架构说明
- [API 使用示例](../API_USAGE_NEW_ARCHITECTURE.md) - 详细调用示例
- [工作流格式说明](../guides/workflow-format.md) - VueFlow JSON 格式
- [工作空间管理](../guides/workspace-management.md) - 文件和路径管理
