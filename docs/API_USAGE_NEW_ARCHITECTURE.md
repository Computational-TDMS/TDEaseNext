# 新架构 API 调用示例

## 测试环境配置

- **用户ID**: `test_user`
- **工作区ID**: `test_workspace`
- **样品ID**: `sample1`

样品定义位于: `data/users/test_user/workspaces/test_workspace/samples.json`

## 1. 单样本执行

### API 端点
```
POST /api/workflows/execute
```

### 请求体
```json
{
  "workflow_id": "wf_test_full",
  "user_id": "test_user",
  "workspace_id": "test_workspace",
  "sample_ids": ["sample1"]
}
```

### cURL 示例
```bash
curl -X POST "http://localhost:8000/api/workflows/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "wf_test_full",
    "user_id": "test_user",
    "workspace_id": "test_workspace",
    "sample_ids": ["sample1"]
  }'
```

### Python 示例
```python
import requests
import json

url = "http://localhost:8000/api/workflows/execute"
payload = {
    "workflow_id": "wf_test_full",
    "user_id": "test_user",
    "workspace_id": "test_workspace",
    "sample_ids": ["sample1"]
}

response = requests.post(url, json=payload)
result = response.json()

print(f"Execution ID: {result.get('executionId')}")
print(f"Status: {result.get('status')}")
```

## 2. 批量执行

### API 端点
```
POST /api/workflows/{workflow_id}/execute-batch
```

### URL 参数
- `workflow_id`: 工作流ID

### 请求体
```json
{
  "user_id": "test_user",
  "workspace_id": "test_workspace",
  "sample_ids": ["sample1", "sample2", "sample3"]
}
```

### cURL 示例
```bash
curl -X POST "http://localhost:8000/api/workflows/wf_test_full/execute-batch" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "workspace_id": "test_workspace",
    "sample_ids": ["sample1"]
  }'
```

### Python 示例
```python
import requests

workflow_id = "wf_test_full"
url = f"http://localhost:8000/api/workflows/{workflow_id}/execute-batch"
payload = {
    "user_id": "test_user",
    "workspace_id": "test_workspace",
    "sample_ids": ["sample1"]
}

response = requests.post(url, json=payload)
results = response.json()

for result in results:
    print(f"Sample: {result.get('sample_id')}, Status: {result.get('status')}, Execution ID: {result.get('executionId')}")
```

## 3. 查询执行状态

### API 端点
```
GET /api/executions/{execution_id}/status
```

### cURL 示例
```bash
curl -X GET "http://localhost:8000/api/executions/{execution_id}/status"
```

## 4. 实时日志 (WebSocket)

### WebSocket URL
```
ws://localhost:8000/ws/executions/{execution_id}
```

### JavaScript 示例
```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/executions/${executionId}`);

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  if (message.type === 'log') {
    console.log(`[${message.level}] ${message.message}`);
  } else if (message.type === 'status') {
    console.log(`Status: ${message.status}, Progress: ${message.progress}%`);
  }
};
```

## 5. 创建新样品

### API 端点
```
POST /api/users/{user_id}/workspaces/{workspace_id}/samples
```

### 请求体
```json
{
  "id": "sample2",
  "name": "New Test Sample",
  "description": "Another test sample",
  "context": {
    "sample": "sample2",
    "fasta_filename": "UniProt_sorghum_focus1",
    "input_basename": "AnotherSample",
    "input_ext": "raw"
  },
  "data_paths": {
    "raw": "data/raw/AnotherSample.raw",
    "fasta": "data/fasta/UniProt_sorghum_focus1.fasta"
  },
  "metadata": {
    "organism": "Sorghum bicolor",
    "tissue": "Leaf",
    "date": "2026-03-02"
  }
}
```

## 关键变化

### 旧架构 ❌
```json
{
  "parameters": {
    "sample_context": {
      "sample": "sample1",
      "fasta_filename": "db"
    },
    "samples": ["sample1"]
  }
}
```

### 新架构 ✅
```json
{
  "user_id": "test_user",
  "workspace_id": "test_workspace",
  "sample_ids": ["sample1"]
}
```

样品上下文现在从 `samples.json` 加载，不需要在请求中传递！

## 错误处理

### 样品不存在
```json
{
  "detail": "Sample 'sample999' not found in workspace 'test_workspace'. Available samples: ['sample1']"
}
```

### 缺少必需参数
```json
{
  "detail": "Missing required parameters: user_id, workspace_id, and sample_ids are required. Please provide workspace and sample information from samples.json."
}
```

### 占位符验证失败
```json
{
  "detail": "Cannot resolve placeholders in pattern '{sample}_ms2.msalign': missing ['sample']. Available: ['fasta_filename']"
}
```

## 获取节点命令追踪

### API 端点
```
GET /api/executions/{execution_id}/nodes/{node_id}/trace
```

### 响应示例
```json
{
  "execution_id": "exec-abc-123",
  "node_id": "pbfgen_1",
  "command_trace": {
    "tool_id": "pbfgen",
    "filtered_params": {},
    "input_files": {"input_file": "demo.raw"},
    "input_flags": ["-i", "demo.raw"],
    "positional_args": [],
    "cmd_parts": ["python.exe", "mock_pbfgen.py", "-i", "demo.raw"],
    "output_flag": {"flag": "-o", "value": "workspace/demo.pbf"}
  }
}
```

使用该 endpoint 可直接获取每个节点最终的 CLI 构建结果，无需解析日志。
