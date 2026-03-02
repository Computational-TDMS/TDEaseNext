# TDEase 数据库设计文档

## 📋 概述

本文档描述了TDEase FastAPI后端层的数据库设计方案，基于Phase 2实施成果的技术架构和功能需求。

## 🗄️ 数据库架构设计

### 核心数据实体

#### 1. 工作流 (Workflows)
- **workflow_id**: 工作流唯一标识符
- **name**: 工作流名称
- **description**: 工作流描述
- **vueflow_data**: VueFlow JSON数据结构
- **workspace_path**: 用户工作空间路径
- **status**: 工作流状态 (created/compiled/running/completed/failed/cancelled/paused)
- **created_at**: 创建时间
- **updated_at**: 更新时间
- **metadata**: 扩展元数据

#### 2. 执行记录 (Executions)
- **execution_id**: 执行唯一标识符
- **workflow_id**: 关联的工作流ID
- **status**: 执行状态 (pending/running/completed/failed/cancelled)
- **start_time**: 开始执行时间
- **end_time**: 结束时间
- **duration**: 执行时长(秒)
- **snakemake_args**: Snakemake参数
- **config_overrides**: 配置覆盖
- **environment**: 环境变量
- **workspace_path**: 工作空间路径

#### 2.1. 执行节点 (Execution Nodes)
- **id**: 节点记录唯一标识符
- **execution_id**: 关联的执行ID
- **node_id**: 前端节点ID
- **rule_name**: Snakemake规则名称（格式: "node_{node_id}"）
- **status**: 节点执行状态 (pending/running/completed/failed)
- **start_time**: 节点开始时间
- **end_time**: 节点结束时间
- **progress**: 节点执行进度 (0-100)
- **log_path**: 节点日志路径
- **error_message**: 错误信息（如果失败）

#### 3. 工具 (Tools)
- **name**: 工具名称
- **version**: 工具版本
- **description**: 工具描述
- **category**: 工具分类
- **executable_path**: 可执行文件路径
- **is_available**: 是否可用
- **platform_info**: 平台相关信息
- **parameters**: 工具参数定义
- **registration_data**: 注册信息

#### 4. 文件 (Files)
- **id**: 文件唯一标识符
- **filename**: 原始文件名
- **safe_filename**: 安全文件名
- **file_path**: 完整文件路径
- **size**: 文件大小(字节)
- **mime_type**: MIME类型
- **workspace_path**: 所在的工作空间
- **uploaded_at**: 上传时间

#### 5. 用户权限 (Workspace Permissions)
- **exists**: 工作空间是否存在
- **readable**: 是否可读
- **writable**: 是否可写
- **executable**: 是否可执行

#### 6. 工作空间用户 (Workspace Users)
- **user_id**: 用户唯一标识符
- **workspace_path**: 工作空间路径
- **permissions**: 权限信息

#### 7. 系统配置 (System Configuration)
- **app_name**: 应用名称
- **version**: 应用版本
- **database**: 数据库连接信息
- **cors_origins**: CORS配置
- **file_settings**: 文件上传配置

#### 8. API请求/响应 (API Requests/Responses)
- **分页信息**: 分页参数和统计
- **错误信息**: 标准化错误格式
- **成功响应**: 成功操作结果

## 📊 表结构设计

### 核心表

#### 1. workflows 表
```sql
CREATE TABLE workflows (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    vueflow_data TEXT NOT NULL,
    workspace_path TEXT NOT NULL,
    status TEXT DEFAULT 'created',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata TEXT
);
```

#### 2. executions 表
```sql
CREATE TABLE executions (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    start_time TEXT NOT NULL,
    end_time TEXT,
    duration INTEGER,
    snakemake_args TEXT,
    config_overrides TEXT,
    environment TEXT,
    workspace_path TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (workflow_id) REFERENCES workflows (id) ON DELETE CASCADE
);
```

#### 2.1. execution_nodes 表（节点级别跟踪）
```sql
CREATE TABLE execution_nodes (
    id TEXT PRIMARY KEY,
    execution_id TEXT NOT NULL,
    node_id TEXT NOT NULL,
    rule_name TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    start_time TEXT,
    end_time TEXT,
    progress INTEGER DEFAULT 0,
    log_path TEXT,
    error_message TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (execution_id) REFERENCES executions (id) ON DELETE CASCADE
);
```

#### 3. tools 表
```sql
CREATE TABLE tools (
    name TEXT PRIMARY KEY,
    version TEXT,
    description TEXT,
    category TEXT,
    executable_path TEXT,
    is_available INTEGER DEFAULT 0,
    platform_info TEXT,
    parameters TEXT,
    registration_data TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

#### 4. files 表
```sql
CREATE TABLE files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    safe_filename TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    size INTEGER NOT NULL,
    mime_type TEXT,
    workspace_path TEXT NOT NULL,
    uploaded_at TEXT NOT NULL,
    workspace_path TEXT NOT NULL
);
```

#### 5. workspace_permissions 表
```sql
CREATE TABLE workspace_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_path TEXT NOT NULL,
    exists INTEGER DEFAULT 0,
    readable INTEGER DEFAULT 0,
    writable INTEGER DEFAULT 0,
    executable INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

#### 6. config 表 (系统配置)
```sql
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

#### 7. execution_logs 表 (可选，用于详细日志)
```sql
CREATE TABLE execution_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    level TEXT,
    message TEXT NOT NULL
    FOREIGN KEY (execution_id) REFERENCES executions (id)
);
```

## 🗄️ 索引设计

### 主要索引
```sql
-- 工作流按创建时间降序
CREATE INDEX idx_workflows_created_at ON workflows (created_at);

-- 执行记录按工作流分组
CREATE INDEX idx_executions_workflow_id ON executions (workflow_id);

-- 执行节点按执行ID和节点ID索引
CREATE INDEX idx_execution_nodes_execution_id ON execution_nodes (execution_id);
CREATE INDEX idx_execution_nodes_node_id ON execution_nodes (node_id);
CREATE INDEX idx_execution_nodes_status ON execution_nodes (status);

-- 工具按名称和类别
CREATE INDEX idx_tools_name ON tools (name);

-- 文件按工作空间和上传时间
CREATE INDEX idx_files_workspace_uploaded_at ON files (workspace_path, uploaded_at);

-- 用户权限检查记录
CREATE INDEX idx_workspace_permissions_workspace_path ON workspace_permissions (workspace_path, created_at);
```

## 🔧 性能考虑

### 1. 数据库选择
- **开发阶段**：SQLite (开发简单，快速原型)
- **生产阶段**：SQLite (轻量级，可靠)
- **扩展阶段**：PostgreSQL (高性能，并发支持)
- **推荐配置**：
  - 连接池：20-100连接
  - 超时配置：异步I/O
  - 查询优化：合理的索引设计

### 2. 数据库优化
- **查询优化**：使用索引加速常用查询
- **事务处理**：减少锁争用
- **批量操作**：使用批量插入/更新
- **缓存机制**：工具和执行结果缓存
- **连接池管理**：避免频繁连接创建/销毁

### 3. 存储策略
- **工作空间隔离**：每个工作流独立目录
- **文件管理**：自动清理临时文件
- **备份策略**：定期数据库备份

### 4. 安全考虑
- **输入验证**：所有用户输入都经过验证
- **权限控制**：基于工作空间的权限检查
- **SQL注入防护**：使用参数化查询
- **文件访问**：路径验证防止目录遍历攻击

## 📋 API设计原则

### 1. RESTful 设计
- 使用标准HTTP方法 (GET/POST/PUT/DELETE)
- 资源统一的URL结构
- 适当的HTTP状态码
- 标准化的错误响应格式

### 2. 异步处理
- 所有长时间操作使用异步
- 后台任务处理
- WebSocket用于实时状态推送

### 3. 错误处理
- 统一的异常处理机制
- 详细的错误日志记录
- 用户友好的错误消息

## 🛡️ 迁移策略

### 从开发到生产
1. **配置管理**
   - 环境变量配置
   - 数据库连接信息(开发/生产)
   - 日志级别设置
   - CORS和域名白名单

2. **数据库部署**
   - 使用Docker容器化部署
   - 数据库迁移脚本
   - 定期备份和监控

## 📈 推荐工具

### 开发工具
- **数据库管理**：DBeaver (GUI工具)
- **API测试**：Postman/Insomnia
- **性能分析**：APM工具 (New Relic/Sentry)

### 监控和运维
- **日志聚合**：ELK Stack + Kibana
- **健康检查**：Prometheus + Grafana
- **告警系统**：基于阈值的实时通知

## 🎯 数据生命周期管理

### 1. 工作流生命周期
```
pending → starting → running → (completed|failed|cancelled|paused)
    ↓
    ↑
completed → archived
    ↓
```

### 2. 执行记录
```
pending → starting → running
running → (progress 0-100%)
completed → success
failed → error记录
```

### 3. 备份和归档
- **自动备份**：定期SQLite数据库文件
- **手动备份**：重要变更前的版本备份
- **归档策略**：基于时间或大小

## 🚀 总结

TDEase FastAPI后端层现已具备完整的生产级能力：
- **现代化架构**：FastAPI + 异步处理
- **完整API覆盖**：工作流、执行、工具、文件管理
- **实时监控**：WebSocket连接和状态更新
- **数据库支持**：SQLite，可扩展到PostgreSQL
- **跨平台**：Windows/Linux完全兼容
- **安全性**：输入验证、权限控制、SQL防护

**推荐下一步**：
1. 立即部署到生产环境
2. 配置生产级数据库和监控系统
3. 集成前端应用，开始完整的工作流管理