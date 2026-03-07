# Section 5: 全局 API 文档 (Global API Documentation)

## 5.1 工作流与执行 (Execution Engine)
### 执行单样本工作流
- **POST** `/api/workflows/execute`
- **Payload**: `{ workflow_id, user_id, workspace_id, sample_ids: ["sample1"] }`

### 多样本批量执行
- **POST** `/api/workflows/{id}/execute-batch`
- **说明**：自动将任务分发至 `sample1`, `sample2` 等。

## 5.2 实时计算代理 (Compute Proxy API)
这些端点用于处理无需持久化到磁盘的轻量级计算。
### 碎片匹配
- **POST** `/api/compute-proxy/fragment-match`
- **功能**：计算给定序列的理论碎片并与观测峰对比，返回标注。
### 修饰搜索
- **POST** `/api/compute-proxy/modification-search`
- **功能**：在数据库中检索匹配特定质量差值的修饰。

## 5.3 批量配置管理 (Batch Config API)
- **POST** `/api/batch-configs/`：创建批量参数模板。
- **GET** `/api/batch-configs/`：列出当前用户的所有批量配置。
- **说明**：批量配置独立于工作流存储，允许用户将同一份配置应用于不同的流程实例。

## 5.4 数据交互 API (Interactive Data API)
### 获取节点 Schema
- **GET** `/api/executions/{id}/nodes/{node_id}/data/schema`
### 分片数据寻址 (Port-Aware)
- **GET** `/api/nodes/{node_id}/data?port_id={port_id}`
- **说明**：通过 `port_id` 在同一个节点下区分不同的输出产物。
### 通用选择驱动数据 (Interactive Data Provider)
- **GET** `/api/executions/{execution_id}/nodes/{node_id}/interactive-data/{selection_key}?resolver=...&port_id=...&spectrum_id=...`
- **说明**：根据上游选择键（如 PrSM ID）加载详细 payload；`resolver` 指定解析器名称（如 `topmsv_prsm`），路径等由工具定义 subResources 驱动。
### TopMSV 专用（兼容别名）
- **GET** `/api/executions/{execution_id}/nodes/{node_id}/topmsv/prsm/{prsm_id}?spectrum_id=...&port_id=...`
- **说明**：等价于 `interactive-data/{prsm_id}?resolver=topmsv_prsm`，保留用于向后兼容。

## 5.5 资源与工作区管理
### 工作区文件浏览
- **GET** `/api/files/browse`：实时查看工作区各个层级（raw, executions, outputs）的文件树。
### 样品管理
- **POST** `/api/users/{u}/workspaces/{w}/samples`：添加或自动推导新样品的上下文。
### 工具自检
- **GET** `/api/tools/`：获取注册到系统中的所有工具定义及 JSON Schema。
- **GET** `/api/executions/{id}/nodes/{node_id}/trace`：获取命令最终拼接结果的详尽链路追踪。

## 5.6 执行错误响应（脱敏）
- 执行相关 API 在内部异常时返回稳定结构，不直接暴露原始异常文本：
  - `code`: 稳定错误码（例如 `WORKSPACE_INVALID`, `EXECUTABLE_NOT_FOUND`, `EXECUTION_INTERNAL_ERROR`）
  - `message`: 脱敏后的用户可读消息
  - `correlation_id`: 日志关联 ID（用于定位服务端详细堆栈）
- 调试建议：提交 `correlation_id` 给后端维护者，通过服务端日志检索完整上下文。
