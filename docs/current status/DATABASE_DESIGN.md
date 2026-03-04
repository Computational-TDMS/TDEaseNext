# TDEase 数据库设计文档

## 📋 概述

本文档描述了 TDEase FastAPI 后端层的当前数据库架构实现状态。

**架构特点**:
- **混合存储**: SQLite (元数据) + 文件系统 (数据和日志)
- **分层设计**: 用户 → 工作空间 → 执行 的层级结构
- **样本数据库化**: 样本数据已从 `samples.json` 迁移到数据库存储
- **节点级跟踪**: 支持工作流执行时每个节点的状态跟踪

## 🗄️ 核心数据实体

### 1. 工作流 (Workflows)
存储工作流定义和元数据。

**数据库字段**:
- `id` (TEXT PRIMARY KEY): 工作流唯一标识符
- `name` (TEXT): 工作流名称
- `description` (TEXT): 工作流描述
- `vueflow_data` (TEXT): VueFlow JSON 数据结构
- `workspace_path` (TEXT): 工作空间路径
- `status` (TEXT): 工作流状态
- `created_at` (TEXT): 创建时间
- `updated_at` (TEXT): 更新时间
- `metadata` (TEXT): 扩展元数据 (JSON)
- `workflow_format` (TEXT): 工作流格式 (vueflow/galaxy)
- `workflow_document` (TEXT): 原始工作流文档
- `batch_config` (TEXT): 批配置关联

**状态值**: `created` → `compiling` → `compiled` → `executing` → `completed`|`failed`|`error`

### 2. 样本 (Samples)
样本数据已从 `samples.json` 迁移到数据库存储。

**数据库字段**:
- `id` (TEXT PRIMARY KEY): 样本唯一标识符
- `workspace_id` (TEXT): 关联的工作空间ID
- `name` (TEXT): 样本名称
- `description` (TEXT): 样本描述
- `context` (TEXT): 样本上下文/placeholder值 (JSON)
- `data_paths` (TEXT): 数据文件路径映射 (JSON, 使用绝对路径)
- `metadata` (TEXT): 扩展元数据 (JSON)
- `created_at` (TEXT): 创建时间
- `updated_at` (TEXT): 更新时间

**关键变化**:
- 旧版本使用 `workspace/samples.json` 文件存储
- 新版本使用数据库存储,支持更高效的查询和管理

### 3. 执行记录 (Executions)
跟踪工作流执行的完整生命周期。

**数据库字段**:
- `id` (TEXT PRIMARY KEY): 执行唯一标识符
- `workflow_id` (TEXT): 关联的工作流ID
- `sample_id` (TEXT): 关联的样本ID (可选)
- `status` (TEXT): 执行状态
- `start_time` (TEXT): 开始执行时间
- `end_time` (TEXT): 结束时间
- `engine_args` (TEXT): 引擎参数 (JSON)
- `config_overrides` (TEXT): 配置覆盖 (JSON)
- `environment` (TEXT): 环境变量 (JSON)
- `workspace_path` (TEXT): 工作空间路径
- `workflow_snapshot` (TEXT): 工作流快照 (JSON)
- `created_at` (TEXT): 创建时间

**状态值**: `pending` → `starting` → `running` → `completed`|`failed`|`cancelled`|`paused`

### 4. 执行节点 (Execution Nodes)
节点级别的执行状态跟踪。

**数据库字段**:
- `id` (TEXT PRIMARY KEY): 节点记录唯一标识符
- `execution_id` (TEXT): 关联的执行ID (FK)
- `node_id` (TEXT): 前端节点ID
- `rule_name` (TEXT): 引擎规则名称
- `status` (TEXT): 节点执行状态
- `start_time` (TEXT): 节点开始时间
- `end_time` (TEXT): 节点结束时间
- `progress` (INTEGER): 节点执行进度 (0-100)
- `log_path` (TEXT): 节点日志路径
- `error_message` (TEXT): 错误信息
- `created_at` (TEXT): 创建时间

**状态值**: `pending` → `running` → `completed`|`failed`

### 5. 工具 (Tools)
工具注册和可用性管理。

**数据库字段**:
- `name` (TEXT PRIMARY KEY): 工具名称
- `version` (TEXT): 工具版本
- `description` (TEXT): 工具描述
- `category` (TEXT): 工具分类
- `executable_path` (TEXT): 可执行文件路径
- `is_available` (INTEGER): 是否可用
- `platform_info` (TEXT): 平台信息 (JSON)
- `metadata` (TEXT): 扩展元数据 (JSON)
- `created_at` (TEXT): 创建时间
- `updated_at` (TEXT): 更新时间

**分类**: converter, processor, analyzer, visualizer, utility, other

### 6. 文件 (Files)
文件上传和跟踪记录。

**数据库字段**:
- `id` (INTEGER PRIMARY KEY): 文件记录ID
- `filename` (TEXT): 原始文件名
- `safe_filename` (TEXT): 安全文件名
- `file_path` (TEXT UNIQUE): 完整文件路径
- `workspace_path` (TEXT): 所在的工作空间
- `subdirectory` (TEXT): 子目录路径
- `size` (INTEGER): 文件大小(字节)
- `mime_type` (TEXT): MIME类型
- `uploaded_at` (TEXT): 上传时间

### 7. 批配置 (Batch Configs)
批处理配置管理,独立于工作流存储。

**数据库字段**:
- `id` (TEXT PRIMARY KEY): 配置唯一标识符
- `user_id` (TEXT): 用户ID
- `name` (TEXT): 配置名称
- `description` (TEXT): 配置描述
- `config_data` (TEXT): 配置数据 (JSON)
- `created_at` (TEXT): 创建时间
- `updated_at` (TEXT): 更新时间
- `is_shared` (INTEGER): 是否共享

### 8. 架构迁移 (Schema Migrations)
数据库版本和迁移跟踪。

**数据库字段**:
- `version` (TEXT PRIMARY KEY): 版本号
- `applied_at` (TEXT): 应用时间
- `description` (TEXT): 迁移描述

**当前版本**: 1.0.0 (包含 samples 表)

## 📊 数据库表结构

### 当前实现的表结构

#### 1. workflows 表
```sql
CREATE TABLE workflows (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    vueflow_data TEXT NOT NULL,
    workspace_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'created',
    created_at TEXT NOT NULL,
    updated_at TEXT,
    metadata TEXT,
    workflow_format TEXT,
    workflow_document TEXT,
    batch_config TEXT
);
```

#### 2. samples 表 (已从文件迁移到数据库)
```sql
CREATE TABLE samples (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    context TEXT NOT NULL,      -- JSON: placeholder 值
    data_paths TEXT NOT NULL,    -- JSON: 绝对路径映射
    metadata TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

#### 3. executions 表
```sql
CREATE TABLE executions (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    sample_id TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    start_time TEXT NOT NULL,
    end_time TEXT,
    engine_args TEXT,            -- JSON: 引擎参数
    config_overrides TEXT,       -- JSON: 配置覆盖
    environment TEXT,            -- JSON: 环境变量
    workspace_path TEXT NOT NULL,
    workflow_snapshot TEXT,      -- JSON: 工作流快照
    created_at TEXT NOT NULL,
    FOREIGN KEY (workflow_id) REFERENCES workflows (id) ON DELETE CASCADE,
    FOREIGN KEY (sample_id) REFERENCES samples (id) ON DELETE SET NULL
);
```

#### 4. execution_nodes 表 (节点级跟踪)
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

#### 5. tools 表
```sql
CREATE TABLE tools (
    name TEXT PRIMARY KEY,
    version TEXT,
    description TEXT,
    category TEXT,
    executable_path TEXT,
    is_available INTEGER DEFAULT 0,
    platform_info TEXT,          -- JSON: 平台信息
    metadata TEXT,               -- JSON: 扩展元数据
    created_at TEXT NOT NULL,
    updated_at TEXT
);
```

#### 6. files 表
```sql
CREATE TABLE files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    safe_filename TEXT NOT NULL,
    file_path TEXT UNIQUE NOT NULL,
    workspace_path TEXT NOT NULL,
    subdirectory TEXT,
    size INTEGER NOT NULL,
    mime_type TEXT,
    uploaded_at TEXT NOT NULL
);
```

#### 7. batch_configs 表 (批配置管理)
```sql
CREATE TABLE batch_configs (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    config_data TEXT NOT NULL,   -- JSON: 配置数据
    created_at TEXT NOT NULL,
    updated_at TEXT,
    is_shared INTEGER DEFAULT 0
);
```

#### 8. schema_migrations 表 (迁移跟踪)
```sql
CREATE TABLE schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL,
    description TEXT
);
```

## 🗄️ 索引设计

### 已实现的索引
```sql
-- 工作流索引
CREATE INDEX idx_workflows_status ON workflows (status);
CREATE INDEX idx_workflows_created_at ON workflows (created_at);
CREATE INDEX idx_workflows_format ON workflows (workflow_format);

-- 样本索引
CREATE INDEX idx_samples_workspace_id ON samples (workspace_id);
CREATE INDEX idx_samples_name ON samples (name);
CREATE INDEX idx_samples_created_at ON samples (created_at);

-- 执行记录索引
CREATE INDEX idx_executions_workflow_id ON executions (workflow_id);
CREATE INDEX idx_executions_sample_id ON executions (sample_id);
CREATE INDEX idx_executions_workflow_sample ON executions (workflow_id, sample_id);
CREATE INDEX idx_executions_status ON executions (status);
CREATE INDEX idx_executions_created_at ON executions (created_at);

-- 执行节点索引
CREATE INDEX idx_execution_nodes_execution_id ON execution_nodes (execution_id);
CREATE INDEX idx_execution_nodes_node_id ON execution_nodes (node_id);
CREATE INDEX idx_execution_nodes_status ON execution_nodes (status);

-- 工具索引
CREATE INDEX idx_tools_category ON tools (category);
CREATE INDEX idx_tools_is_available ON tools (is_available);

-- 文件索引
CREATE INDEX idx_files_workspace_path ON files (workspace_path);
CREATE INDEX idx_files_uploaded_at ON files (uploaded_at);

-- 批配置索引
CREATE INDEX idx_batch_configs_user_id ON batch_configs (user_id);
CREATE INDEX idx_batch_configs_created_at ON batch_configs (created_at);
```

## 🏗️ 存储架构

### 混合存储策略

TDEase 使用 **数据库 + 文件系统** 的混合存储架构:

```
data/
├── tdease.db                    # SQLite 数据库 (元数据)
└── users/
    └── {user_id}/
        ├── user.json            # 用户元数据
        └── workspaces/
            └── {workspace_id}/
                ├── workspace.json   # 工作空间元数据
                ├── workflows/       # 工作流定义文件
                ├── executions/
                │   └── {exec_id}/   # 执行隔离目录
                │       ├── execution.json
                │       ├── inputs/
                │       ├── outputs/
                │       └── logs/
                └── data/            # 共享数据文件
                    ├── raw/
                    ├── fasta/
                    └── reference/
```

**数据库存储**:
- 工作流元数据
- 样本定义和上下文
- 执行记录和状态
- 节点级执行跟踪
- 工具注册信息
- 文件上传记录

**文件系统存储**:
- 执行输入/输出文件
- 日志文件
- 工作流定义文件
- 用户和工作空间元数据
- 数据文件 (raw/fasta/reference)

## 📦 服务层架构

### 核心服务模块

| 服务模块 | 职责 | 文件 |
|---------|------|------|
| `WorkflowStore` | 工作流数据库操作 | `workflow_store.py` |
| `ExecutionStore` | 执行记录和节点跟踪 | `execution_store.py` |
| `SampleStore` | 样本数据库操作 | `sample_store.py` |
| `UnifiedWorkspaceManager` | 工作空间和文件操作 | `unified_workspace_manager.py` |
| `ToolRegistry` | 工具注册和验证 | `tool_registry.py` |
| `NodeDataService` | 节点输出数据推导与解析 | `node_data_service.py` |

### NodeDataService (新增)

节点输出数据服务，基于工具定义推导输出文件路径，无需额外持久化。

**核心功能**:
- `resolve_node_outputs()`: 解析节点输出文件路径并返回文件元信息
- `parse_tabular_file()`: 解析表格文件（TSV/CSV/TXT等）
- `_get_output_patterns()`: 从工具定义获取输出模式（从 workflow_service.py 提取）
- `_resolve_output_paths()`: 解析输出路径（从 workflow_service.py 提取）

**路径推导流程**:
1. 查询 `executions` 表获取 `workflow_snapshot`, `workspace_path`, `sample_id`
2. 解析 `workflow_snapshot` 找到节点的 `tool_id`
3. 查询 `tool_registry` 获取工具定义的 `ports.outputs[].pattern`
4. 查询 `samples` 表获取 `sample_context`
5. 使用 `sample_context` 格式化 `pattern` 得到实际文件路径

**支持的文件格式**:
- 表格文件: `.tsv`, `.csv`, `.txt`, `.ms1ft`, `.feature`
- 二进制文件: `.pbf`, `.raw`, `.mzml`, `.png`, `.jpg`

### 样本数据迁移

**重要变更**: 样本数据已从 `samples.json` 迁移到数据库。

**旧方式** (已弃用):
```json
// workspace/samples.json
{
  "version": "1.0",
  "samples": {
    "sample1": {
      "name": "Sample 1",
      "context": {"raw_path": "/data/raw/file.mzML"},
      "data_paths": {"raw": "/data/raw/file.mzML"}
    }
  }
}
```

**新方式** (数据库存储):
```sql
-- samples 表
INSERT INTO samples (id, workspace_id, name, context, data_paths, ...)
VALUES ('sample1', 'ws1', 'Sample 1',
        '{"raw_path": "/data/raw/file.mzML"}',
        '{"raw": "/data/raw/file.mzML"}', ...);
```

**迁移工具**: `scripts/migrate_samples_to_db.py`

## 🔄 数据生命周期

### 工作流状态流转
```
created → compiling → compiled → executing → completed
                                  ↓         ↓
                              failed     error
```

### 执行状态流转
```
pending → starting → running → completed
                           ↓         ↓
                        failed  cancelled
```

### 节点状态流转
```
pending → running → completed
                    ↓         ↓
                  failed  cancelled
```

## 🔧 性能优化

### 数据库配置
- **Foreign Keys**: 启用 (`PRAGMA foreign_keys = ON`)
- **Row Factory**: 启用字典式访问 (`sqlite3.Row`)
- **Connection**: 池化管理,复用连接

### 查询优化
- 所有 `WHERE` 子句都有索引支持
- 使用 `LIMIT` 和 `OFFSET` 进行分页
- JSON 字段存储为 TEXT,按需解析

### 数据迁移支持
- 自动检测并创建缺失的表
- 列添加迁移 (`ALTER TABLE ADD COLUMN`)
- 列重命名迁移 (`snakemake_args` → `engine_args`)

## 🛡️ 安全措施

### 输入验证
- 所有输入使用 Pydantic 模型验证
- 样本 ID 格式验证 (`[a-zA-Z0-9_-]+`)
- 路径验证防止目录遍历

### SQL 注入防护
- 全部使用参数化查询
- 不使用字符串拼接 SQL

### 权限控制
- 基于 `user_id` 和 `workspace_id` 的隔离
- 文件系统操作前检查权限

## 📊 API 数据模型

### 核心请求/响应模型

**工作流** (`app/models/workflow.py`):
- `WorkflowCreate`: 创建工作流
- `WorkflowResponse`: 工作流响应
- `WorkflowUpdate`: 更新工作流
- `WorkflowValidation`: 验证结果

**执行** (`app/models/execution.py`):
- `ExecutionRequest`: 执行请求
- `ExecutionResponse`: 执行响应
- `ExecutionStatus`: 详细状态
- `LogRequest/Response`: 日志查询

**工作空间** (`app/schemas/workspace.py`):
- `WorkspaceCreate`: 创建工作空间
- `SampleCreate/Update`: 样本操作
- `SamplesFile`: 样本集合

### 新增 API 端点 (节点数据访问)

**节点输出数据** (`app/api/execution.py`):
```
GET /api/executions/{execution_id}/nodes/{node_id}/data
  Query参数: include_data (bool), max_rows (int)
  返回: 节点输出端口列表，包含文件元信息和可选的解析数据

GET /api/executions/{execution_id}/nodes/{node_id}/files
  返回: 节点输出端口列表（不含数据内容）
```

**最新执行查询** (`app/api/workflow.py`):
```
GET /api/workflows/{workflow_id}/latest-execution
  返回: 最新完成的执行元信息
```

**工作区文件浏览** (`app/api/workspace.py`):
```
GET /api/users/{user_id}/workspaces/{workspace_id}/files
  返回: 目录树结构

GET /api/users/{user_id}/workspaces/{workspace_id}/file-content
  Query参数: path (str), max_rows (int)
  返回: 文件内容预览（表格/文本/二进制）
```

### 前端类型定义 (新增)

**类型定义** (`TDEase-FrontEnd/src/types/workspace-data.ts`):
- `NodeOutputResponse`: 节点输出数据响应
- `OutputEntry`: 输出端口条目
- `TableData`: 表格数据结构
- `FileTreeNode`: 文件树节点
- `FileContentResponse`: 文件内容响应
- `LatestExecutionResponse`: 最新执行响应

**API 客户端** (`TDEase-FrontEnd/src/services/api/workspace-data.ts`):
- `getNodeData()`: 获取节点输出数据
- `getNodeFiles()`: 获取节点输出文件列表
- `getLatestExecution()`: 获取最新执行
- `getWorkspaceFiles()`: 获取工作区文件树
- `getFileContent()`: 获取文件内容预览

## 🚀 运维工具

### 数据库健康检查
```bash
# 使用内置健康检查
python -m app.database.init_db
```

### 数据库备份
```python
from app.database.init_db import backup_database
backup_database("data/backup/tdease_backup_20260303.db")
```

### 数据库迁移
当前版本: **1.0.0** (包含 samples 表)

## 📝 架构演进历史

| 版本 | 变更 |
|------|------|
| 1.0.0 | 初始架构 + samples 表迁移 |
| - | 添加 batch_configs 表 |
| - | 添加 workflow_format/workflow_document 字段 |
| - | 添加 schema_migrations 表 |
| - | 重命名 snakemake_args → engine_args |
| 2026-03-03 | **节点数据访问 API** (backend-workspace-access) |
| | - 新增 `NodeDataService` 用于节点输出路径推导和文件解析 |
| | - 从 `workflow_service.py` 提取 `_get_output_patterns()` 和 `_resolve_output_paths()` 到 `node_data_service.py` |
| | - 新增 `GET /api/executions/{id}/nodes/{node_id}/data` 端点（获取节点输出数据） |
| | - 新增 `GET /api/executions/{id}/nodes/{node_id}/files` 端点（获取节点输出文件列表） |
| | - 新增 `GET /api/workflows/{id}/latest-execution` 端点（获取最新执行） |
| | - 新增 `GET /api/users/{user_id}/workspaces/{workspace_id}/files` 端点（工作区文件浏览） |
| | - 新增 `GET /api/users/{user_id}/workspaces/{workspace_id}/file-content` 端点（文件内容预览） |
| | - 移除 `app/api/visualization.py`（功能已迁移到 execution.py 和 workspace.py） |
| | - 添加前端 TypeScript 类型定义 (`src/types/workspace-data.ts`) |
| | - 添加前端 API 客户端 (`src/services/api/workspace-data.ts`) |
| 2026-03-04 | **工作流取消功能** (implement-workflow-stop) |
| | - 新增 `ProcessRegistry` 类 (`app/core/executor/process_registry.py`) 用于管理运行中的子进程 |
| | - 实现 `LocalExecutor.cancel()` 方法，通过进程注册表终止子进程 |
| | - 实现两阶段终止策略：SIGTERM（优雅终止）→ SIGKILL（强制终止，3秒超时） |
| | - `TaskSpec` 新增 `task_id` 字段，格式为 `{execution_id}:{node_id}` |
| | - `ExecutionManager` 增强：支持追踪运行中的节点，实现真正的取消操作 |
| | - `WorkflowService` 集成：生成 task_id 并注册节点状态到 ExecutionManager |
| | - `ShellRunner` 修改：注册进程到注册表，退出时自动注销 |
| | - `POST /api/executions/{id}/stop` 现在会真正终止底层进程 |
| | - 支持线程安全的并发执行取消操作 |
| | - 取消操作会更新数据库状态为 "cancelled"（执行和节点级别） |

## 🔄 工作流取消功能

### 概述

TDEase 后端支持在运行中取消工作流执行。当用户点击"停止"按钮时，系统会：
1. 终止所有运行中的子进程
2. 更新执行状态为 "cancelled"
3. 更新所有运行中的节点状态为 "cancelled"

### 进程注册表 (ProcessRegistry)

全局单例类，用于追踪运行中的子进程：
- **注册**: 进程启动时使用 `task_id` 注册
- **注销**: 进程退出时自动注销（使用 try-finally 确保执行）
- **取消**: 通过 `task_id` 查找并终止进程

```python
# API 示例
from app.core.executor.process_registry import process_registry

# 注册进程
process_registry.register(task_id="{execution_id}:{node_id}", process=proc)

# 取消进程（两阶段终止）
process_registry.cancel(task_id, timeout=3)

# 列出活跃进程
active_tasks = process_registry.list_active()
```

### 取消流程

```
用户点击停止按钮
    ↓
POST /api/executions/{id}/stop
    ↓
ExecutionManager.stop()
    ↓
获取运行中的节点列表
    ↓
对每个节点调用 ProcessRegistry.cancel(task_id)
    ↓
SIGTERM (优雅终止)
    ↓
等待 3 秒
    ↓
如果仍在运行 → SIGKILL (强制终止)
    ↓
更新数据库状态：execution.status = "cancelled"
    ↓
更新节点状态：node.status = "cancelled"
```

### 线程安全

进程注册表使用 `threading.Lock` 保护所有操作：
- 并发注册：支持多个工作流同时执行
- 并发取消：支持同时取消多个工作流
- 竞态条件处理：自动清理已退出的进程

### 使用方式

**API 调用**:
```bash
POST /api/executions/{execution_id}/stop
```

**前端调用**:
```typescript
const response = await apiClient.post(`/api/executions/${executionId}/stop`);
```

### 状态流转

**执行级别**:
- `running` → `cancelled`

**节点级别**:
- `running` → `cancelled`
- `pending/completed/failed` → 保持不变