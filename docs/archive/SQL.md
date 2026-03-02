
一、前后端数据库交互总览
┌─────────────────┐      HTTP (REST API)      ┌─────────────────┐      SQL      ┌─────────────────┐│    前端 Vue     │  ◀──────────────────────▶  │  FastAPI 后端   │  ◀──────────▶  │  SQLite 数据库  ││  (TDEase-FrontEnd)│   JSON 请求/响应          │  (app/api)      │  原生 SQL      │  data/tdease.db │└─────────────────┘                            └─────────────────┘               └─────────────────┘        │                                              │        │  workflowApi.createWorkflow(payload)          │  save_workflow_to_database()        │  workflowApi.getWorkflow(id)                  │  get_workflow_from_database()        │  workflowApi.updateWorkflow(id, payload)      │  json.dumps() / json.loads()        │  workflowApi.executeCompiledWorkflow(...)     │  ExecutionStore.create() / update_node_status()        ▼                                              ▼
前端通过 Axios 调用 REST API，后端用 sqlite3 执行 SQL，JSON 以字符串形式写入 TEXT 列，读写时用 json.dumps / json.loads 做序列化。
二、JSON 在 SQLite 中的存储方式
SQLite 本身没有 JSON 类型，所以用 TEXT 列 + Python json 存储：
表	JSON 相关列	存储方式	示例内容
workflows	vueflow_data	json.dumps(obj)	{"nodes":[...],"edges":[...],"metadata":{}}
workflows	metadata	json.dumps(obj)	{"tags":[],"author":"..."}
workflows	workflow_document	原始字符串	导入的原始文档
workflows	batch_config	json.dumps(obj)	批量配置
executions	snakemake_args	可为 JSON	保留兼容
executions	config_overrides	可为 JSON	执行参数
batch_configs	config_data	json.dumps(obj)	批量配置数据
写入示例（来自 app/api/workflow.py:546）：
json.dumps(workflow_data.get("vueflow_data", {}))   # Python dict → JSON 字符串
读取示例（来自 app/api/workflow.py:582）：
"vueflow_data": json.loads(row[3])   # JSON 字符串 → Python dict
三、API 与数据库的对应关系
工作流相关
API 端点	方法	数据库操作	涉及的 JSON 字段
GET /api/workflows	列表	SELECT id, name, description, status...	不返回 vueflow_data
POST /api/workflows	创建	INSERT INTO workflows	写入 vueflow_data、metadata
GET /api/workflows/{id}	详情	SELECT ... vueflow_data ...	读取 vueflow_data 并 json.loads
PUT /api/workflows/{id}	更新	INSERT OR REPLACE / UPDATE	更新 vueflow_data
DELETE /api/workflows/{id}	删除	DELETE FROM workflows	-
POST /api/workflows/execute	直接执行	可能创建 execution	使用 request_data.workflow 中的 JSON
POST /api/workflows/{id}/batch-config	保存批量配置	UPDATE workflows SET batch_config=?	写入 batch_config
GET /api/workflows/{id}/batch-config	获取批量配置	SELECT batch_config	读取并 json.loads
执行相关
API 端点	方法	数据库操作	数据流
POST /api/workflows/execute	执行	ExecutionStore.create() → execution_nodes	创建 execution，按节点创建 execution_nodes
GET /api/executions/{id}	执行状态	ExecutionStore.get_nodes()	从 execution_nodes 读取状态
POST /api/executions/{id}/stop	停止	内存状态 + 可选 DB 更新	-
四、前后端数据流示例
1. 保存工作流
前端 WorkflowJSON (nodes, connections, metadata)       │       ▼ WorkflowService.saveWorkflow()    vueflow_data = { metadata, nodes, edges, format_version, projectSettings }       │       ▼ workflowApi.createWorkflow(payload)  或  updateWorkflow(id, payload)    POST/PUT /api/workflows[/{id}]       │       ▼ FastAPI 路由 → create_workflow() 或 update_workflow()    save_workflow_to_database(db, { ..., "vueflow_data": {...} })       │       ▼    INSERT/REPLACE workflows (..., vueflow_data=json.dumps(vueflow_data), ...)
2. 加载工作流
GET /api/workflows/{id}       │       ▼ get_workflow_from_database(db, workflow_id)    SELECT vueflow_data FROM workflows WHERE id=?       │       ▼ row[3] 是 JSON 字符串    json.loads(row[3])  →  Python dict       │       ▼ WorkflowResponse(vueflow_data=...)    JSON 响应返回给前端       │       ▼ WorkflowService.loadWorkflow()    importRawWorkflow(rawData)  →  WorkflowJSON (VueFlow 格式)
3. 直接执行（不先入库）
POST /api/workflows/executeBody: { "workflow": { nodes, edges, ... }, "tools": [...], "parameters": {...} }       │       ▼ execute() 端点    workflow_raw = request_data["workflow"]  # 前端直接传的 JSON    WorkflowNormalizer().normalize(workflow_raw)  # 规范化    WorkflowService.execute_workflow(wf_v2, ...)       │       ▼ 如需入库    save_workflow_to_database()  # 可能写入 workflows 表    ExecutionStore.create()      # 写入 executions    ExecutionStore.create_node() # 写入 execution_nodes
五、重要实现点
vueflow_data 结构：由前端 VueFlow 的 nodes、edges、metadata 等组成，后端只做存储与规范化，不解析业务逻辑。
双写：/import 时既写入 workflows 表，也可能在 data/workflows/{id}/workflow.json 写一份。
事务：save_workflow_to_database 中执行 db.commit()，单次请求内完成提交。
直接执行：/execute 可接收前端传来的完整 workflow JSON，不要求该工作流已存在数据库中，执行时再决定是否落库。
