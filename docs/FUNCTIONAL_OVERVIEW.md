# TDEase 功能目标与实现方式

**更新日期**: 2026-03-04
**版本**: 1.0

## 目录

- [项目概述](#项目概述)
- [核心功能目标](#核心功能目标)
- [实现架构](#实现架构)
- [关键设计决策](#关键设计决策)
- [功能模块详解](#功能模块详解)
- [开发路线图](#开发路线图)

---

## 项目概述

TDEase 是一个**质谱数据分析工作流平台**，旨在为蛋白质组学研究提供可视化、易用的工作流编排和执行环境。

### 核心价值主张

1. **节点式工作流设计**：通过拖拽节点构建分析流程，无需编写代码
2. **工具即插件**：统一的工具定义框架，轻松集成新工具
3. **交互式可视化**：前端加载数据，实时筛选和探索
4. **全流程追踪**：从原始数据到最终结果的完整审计
5. **多样化支持**：支持单样本、多样本、批量处理

---

## 核心功能目标

### 1. 工作流编排引擎

**目标**：提供一个直观的节点式工作流编辑器，让研究人员能够可视化地构建质谱数据分析流程。

**实现方式**：
- **前端**：基于 VueFlow 的可视化编辑器
  - 拖拽节点：工具节点 → 画布
  - 连接节点：定义数据流向
  - 配置参数：动态表单根据工具定义生成
  - 实时验证：连接合法性检查

- **后端**：FlowEngine DAG 调度器
  - 拓扑排序：确定执行顺序
  - 依赖管理：处理节点间的依赖关系
  - 状态追踪：每个节点的执行状态
  - 并发控制：支持并行执行独立节点

### 2. 工具定义与注册系统

**目标**：实现一个统一的工具定义框架，使质谱分析工具能够作为插件无缝集成到系统中。

**实现方式**：
- **Tool Definition Schema**（`config/tool-schema.json`）
  - JSON Schema 验证
  - 前后端共享单一数据源
  - 支持多种执行模式

- **工具定义示例**（`config/tools/*.json`）：
```json
{
  "id": "topfd",
  "name": "TopFD",
  "executionMode": "native",
  "command": {
    "executable": "topfd"
  },
  "ports": {
    "inputs": [{"id": "ms2_file", "dataType": "ms2", "required": true}],
    "outputs": [{"id": "ms1_file", "pattern": "{sample}_ms1.msalign"}]
  },
  "parameters": {
    "mass": {"flag": "-m", "type": "value", "default": "50000"}
  }
}
```

- **ToolRegistry**（`app/services/tool_registry.py`）
  - 自动扫描 `config/tools/` 目录
  - 加载和验证工具定义
  - 提供工具查询 API

### 3. 样品与工作区管理

**目标**：支持多样品、多工作区的层次化管理，方便组织不同的研究项目。

**实现方式**：
- **目录结构**：
```
data/
└── users/
    └── {user_id}/
        └── workspaces/
            └── {workspace_id}/
                ├── samples.json       # 样品定义
                ├── workflows/         # 工作流定义
                ├── executions/        # 执行记录
                └── data/              # 数据文件
                    ├── raw/
                    ├── fasta/
                    └── reference/
```

- **UnifiedWorkspaceManager**（`app/services/unified_workspace_manager.py`）
  - 管理用户工作区层级
  - 提供 `samples.json` 的读写接口
  - 自动推导占位符（`{sample}`, `{basename}` 等）

- **samples.json 格式**：
```json
{
  "samples": {
    "sample1": {
      "id": "sample1",
      "name": "Sample 1",
      "context": {
        "sample": "sample1",
        "fasta_filename": "UniProt_sorghum_focus1"
      },
      "data_paths": {
        "raw": "data/raw/Sorghum-Histone0810162L20.raw",
        "fasta": "data/fasta/UniProt_sorghum_focus1.fasta"
      }
    }
  }
}
```

### 4. 命令构建管道

**目标**：统一处理不同工具的命令行参数构建，消除硬编码和分支逻辑。

**实现方式**：
- **CommandPipeline**（`app/core/executor/command_pipeline.py`）

5 步管道流程：
1. **Filter**：移除空参数（null/empty/"none"）
2. **Executable**：解析可执行命令（native/script/docker）
3. **Output Flag**：添加输出标志（如果 `flagSupported`）
4. **Parameter Flags**：构建参数标志（value/boolean/choice）
5. **Positional Args**：添加位置参数（按 `positionalOrder`）

**优势**：
- 无类型分支逻辑
- 统一的参数过滤
- 易于扩展新的执行模式
- 支持复杂的参数组合

### 5. 工作流执行引擎

**目标**：可靠地执行工作流，提供完整的状态追踪和日志记录。

**实现方式**：
- **FlowEngine**（`app/core/engine/scheduler.py`）
  - DAG 拓扑排序
  - 节点状态机：PENDING → READY → RUNNING → COMPLETED/FAILED/SKIPPED
  - 支持断点续传（resume 模式）
  - 支持模拟执行（dryrun 模式）

- **WorkflowService**（`app/services/workflow_service.py`）
  - 工作流编排服务
  - 调用 CommandPipeline 构建命令
  - 协调 LocalExecutor 执行任务
  - 更新 ExecutionStore 状态

- **LocalExecutor**（`app/core/executor/local.py`）
  - 执行单个任务
  - 调用 ShellRunner 运行命令
  - 捕获输出和错误
  - 支持取消操作（通过 ProcessRegistry）

### 6. 工作流取消功能

**目标**：允许用户在执行过程中取消正在运行的工作流，实现真正的"令行禁止"。

**实现方式**：
- **ProcessRegistry**（`app/core/executor/process_registry.py`）
  - 全局单例，维护 `task_id → subprocess.Popen` 映射
  - 线程安全的操作（使用 `threading.Lock`）
  - 两阶段终止：SIGTERM（3秒）→ SIGKILL
  - 自动清理（finally 块保证注销）

- **ExecutionManager 增强**（`app/services/runner.py`）
  - 追踪运行中的节点（`running_nodes: Set[str]`）
  - `register_node_start()` / `register_node_complete()` 方法
  - `stop()` 方法：遍历运行中的节点并取消

- **API 端点**：
  - `POST /api/executions/{id}/stop`
  - 更新数据库状态为 "cancelled"

### 7. 执行状态持久化

**目标**：完整记录工作流执行过程，支持查询、审计和调试。

**实现方式**：
- **ExecutionStore**（`app/services/execution_store.py`）
  - SQLite 数据库存储
  - 三个核心表：workflows、executions、execution_nodes
  - 支持创建、查询、更新操作

- **数据表设计**：
  - `workflows`：工作流定义
  - `executions`：执行记录（状态、时间、进度）
  - `execution_nodes`：节点级别的执行状态

### 8. 实时通信

**目标**：为前端提供实时的执行状态和日志更新。

**实现方式**：
- **WebSocket 连接**（`app/core/websocket.py`）
  - `/ws/executions/{id}`：执行流端点
  - 消息类型：node_update、log、execution_complete
  - 自动降级为轮询（如果 WebSocket 不可用）

### 9. 交互式可视化（规划中）

**目标**：提供前端交互式数据可视化能力，让用户能够实时筛选和探索数据。

**设计**：
- **一次性加载**：节点激活时全量加载数据到前端
- **本地交互**：框选、筛选、排序等操作在前端完成
- **状态传递**：交互式节点之间传递选择状态（非文件）
- **节点类型**：FeatureMap Viewer、Spectrum Viewer、Table Viewer

**架构**：
```
处理节点 → 交互式节点：加载文件（通过 node-data-access API）
交互式节点 → 交互式节点：传递前端选择状态
交互式节点 → 处理节点：状态 → 临时文件（执行时）
```

---

## 实现架构

### 技术栈

#### 后端
- **FastAPI**：现代 Web 框架，自动生成 OpenAPI 文档
- **SQLite**：轻量级数据库
- **Pydantic**：数据验证
- **WebSocket**：实时通信

#### 前端
- **Vue.js**：渐进式前端框架
- **VueFlow**：工作流编辑器
- **Tauri**：桌面应用框架
- **TypeScript**：类型安全

#### 执行环境
- **Conda**：工具环境管理
- **Docker**：可选的容器化工具

### 架构分层

```
┌─────────────────────────────────────────────────────┐
│                    前端层                            │
│         Vue.js + VueFlow + Tauri                   │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│                    API层                            │
│            FastAPI + WebSocket                      │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│                    服务层                           │
│  WorkflowService | ExecutionManager | ToolRegistry  │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│                    核心层                           │
│  FlowEngine | CommandPipeline | ProcessRegistry     │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│                   执行层                            │
│      LocalExecutor | ShellRunner                    │
└─────────────────────────────────────────────────────┘
```

---

## 关键设计决策

### 1. Schema-Driven 设计

**决策**：使用 Tool Definition Schema 作为单一数据源。

**理由**：
- 前后端共享同一工具定义，消除不一致
- 前端可以动态渲染参数配置界面
- 易于添加新工具，只需修改 JSON 配置

### 2. 文件系统存储样品数据

**决策**：样品定义存储在 `samples.json` 文件中，而非数据库。

**理由**：
- 工作区级别的共享，无需查询数据库
- 便于版本控制和迁移
- 减少数据库查询压力

### 3. 两阶段进程终止

**决策**：先发送 SIGTERM（3秒超时），再发送 SIGKILL。

**理由**：
- 平衡优雅退出和响应速度
- 给工具机会清理临时文件
- 防止进程泄漏（强制终止保证）

### 4. Task ID 格式

**决策**：使用 `{execution_id}:{node_id}` 作为 task_id。

**理由**：
- 唯一性：执行ID + 节点ID保证全局唯一
- 可读性：自然反映父子关系
- 便于调试：可以直接追溯到具体执行和节点

### 5. 交互式节点数据加载

**决策**：节点激活时一次性全量加载数据到前端。

**理由**：
- 后续交互零延迟，提升用户体验
- 避免频繁请求后端
- 前端计算能力强，可以处理复杂筛选

---

## 功能模块详解

### 工作流管理模块

**功能**：
- 创建、编辑、删除工作流
- 保存工作流到数据库
- 查询工作流列表和详情

**API**：
- `POST /api/workflows` - 创建工作流
- `GET /api/workflows` - 列出工作流
- `GET /api/workflows/{id}` - 获取详情
- `PUT /api/workflows/{id}` - 更新工作流
- `DELETE /api/workflows/{id}` - 删除工作流

### 执行管理模块

**功能**：
- 执行工作流（单样本/多样本）
- 查询执行状态
- 取消正在执行的流程
- 查看执行日志

**API**：
- `POST /api/workflows/execute` - 执行工作流
- `GET /api/executions/{id}` - 获取状态
- `POST /api/executions/{id}/stop` - 取消执行
- `GET /api/executions/{id}/logs` - 获取日志

### 工具管理模块

**功能**：
- 获取工具定义 Schema
- 查询可用工具列表
- 获取单个工具详情

**API**：
- `GET /api/tools/schemas` - 获取 Schema 和工具列表
- `GET /api/tools/{id}` - 获取单个工具

### 工作区管理模块

**功能**：
- 创建工作区
- 列出样品
- 浏览工作区文件

**API**：
- `POST /api/workspaces` - 创建工作区
- `GET /api/workspaces/{user_id}/{workspace_id}/samples` - 列出样品
- `GET /api/workspaces/{user_id}/{workspace_id}/files` - 浏览文件

### 文件管理模块

**功能**：
- 上传数据文件
- 下载结果文件
- 预览表格数据

**API**：
- `POST /api/files/upload` - 上传文件
- `GET /api/files/download` - 下载文件
- `GET /api/nodes/{execution_id}/preview` - 预览数据

---

## 开发路线图

### Phase 1: 基础架构 ✅
- [x] FastAPI 后端框架
- [x] SQLite 数据库
- [x] 工具注册系统
- [x] CommandPipeline
- [x] FlowEngine DAG 调度器

### Phase 2: 执行功能 ✅
- [x] 单样本执行
- [x] 多样本执行
- [x] 执行状态追踪
- [x] 日志捕获
- [x] 工作流取消功能

### Phase 3: 前端集成 🔄
- [ ] VueFlow 编辑器完善
- [ ] 参数配置面板
- [ ] 执行监控界面
- [ ] 实时状态更新

### Phase 4: 可视化功能 📋
- [ ] 后端数据访问 API
- [ ] FeatureMap Viewer
- [ ] Spectrum Viewer
- [ ] Table Viewer

### Phase 5: 高级功能 📋
- [ ] 断点续传
- [ ] 参数扫描
- [ ] 结果比较
- [ ] AI Agent 集成

---

## 相关文档

- [系统架构](ARCHITECTURE.md) - 详细的技术架构说明
- [API 文档](api/endpoints.md) - RESTful API 端点
- [开发路线图](ROADMAP.md) - 开发计划和进度
- [OpenSpec 变更](../openspec/changes/) - 功能变更设计文档
