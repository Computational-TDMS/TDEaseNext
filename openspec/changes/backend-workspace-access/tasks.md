## 1. 服务层：提取与新建

- [x] 1.1 从 `workflow_service.py` 提取 `_get_output_patterns()` 和 `_resolve_output_paths()` 到新文件 `app/services/node_data_service.py`，`workflow_service.py` 改为 import 这些函数（保持向后兼容）
- [x] 1.2 在 `node_data_service.py` 中实现 `resolve_node_outputs(execution_id, node_id, db)` 方法：查 executions 表 → 解析 workflow_snapshot 找 tool_id → 查 tool_registry → 查 sample_context → 调用 `_resolve_output_paths()` → 返回每个 port 的文件元信息列表
- [x] 1.3 在 `node_data_service.py` 中实现 `parse_tabular_file(file_path, max_rows=None)` 方法：按扩展名选择分隔符（.csv 用逗号，其余用 tab），解析为 `{"columns": [...], "rows": [...], "total_rows": int}` 格式
- [x] 1.4 在 `execution_store.py` 中新增 `get_latest_completed_execution(workflow_id)` 方法：查询指定 workflow 最新一条 status="completed" 的执行记录

## 2. API 端点：节点数据访问

- [x] 2.1 在 `app/api/execution.py` 中新增 `GET /{execution_id}/nodes/{node_id}/data` 端点：调用 `NodeDataService.resolve_node_outputs()`，支持 `include_data` query param 控制是否内联解析数据
- [x] 2.2 在 `app/api/execution.py` 中新增 `GET /{execution_id}/nodes/{node_id}/files` 端点：调用 `NodeDataService.resolve_node_outputs()` 返回文件列表（不含数据）
- [x] 2.3 在 `app/api/workflow.py` 中新增 `GET /{workflow_id}/latest-execution` 端点：调用 `ExecutionStore.get_latest_completed_execution()`，返回执行元信息

## 3. API 端点：工作区文件浏览

- [x] 3.1 在 `app/api/workspace.py` 中新增 `GET /users/{user_id}/workspaces/{workspace_id}/files` 端点：从现有 `visualization.py` 的 `list_workspace_files` 迁移并完善（添加路径安全校验）
- [x] 3.2 在 `app/api/workspace.py` 中新增 `GET /users/{user_id}/workspaces/{workspace_id}/file-content` 端点：接受 `path` 和 `max_rows` query params，校验路径不越界（`..` 检查），调用 `parse_tabular_file` 或返回原始文本/二进制元信息

## 4. 路由清理

- [x] 4.1 从 `app/main.py` 中移除 `visualization.visualization_router` 的 include_router
- [x] 4.2 移除或归档 `app/api/visualization.py`（其功能已被 execution.py 和 workspace.py 的新端点替代）

## 5. 前端类型定义与 API 客户端

- [x] 5.1 创建 `src/types/workspace-data.ts`：定义 `NodeOutputResponse`, `OutputEntry`, `TableData`, `FileTreeNode`, `FileContentResponse` 等 TypeScript 接口
- [x] 5.2 创建 `src/services/api/workspace-data.ts`：实现 `getNodeData()`, `getNodeFiles()`, `getLatestExecution()`, `getWorkspaceFiles()`, `getFileContent()` 等 API 调用函数
