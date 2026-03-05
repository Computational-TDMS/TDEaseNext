# TDEase 文档导航

**版本**: 2.1 (交互式可视化架构)
**更新日期**: 2025-03-05

---

## 核心文档

### 系统架构与功能

| 文档 | 说明 |
|------|------|
| [系统架构](ARCHITECTURE.md) | 新架构总览 + 交互式可视化架构 |
| [功能目标与实现](FUNCTIONAL_OVERVIEW.md) | 核心功能目标和实现方式 |
| [工作流执行机制](WORKFLOW_EXECUTION.md) | 工作流执行流程、工具后端映射、文件追踪 |
| [节点连接与数据传递](About_node_connection.md) | 节点连接类型、数据流、状态流 |

### API 与开发

| 文档 | 说明 |
|------|------|
| [API 使用指南](API_USAGE_NEW_ARCHITECTURE.md) | RESTful API 调用示例 |
| [工具定义 Schema](TOOL_DEFINITION_SCHEMA.md) | 工具 JSON 定义规范 |

### 交互式可视化

| 文档 | 说明 |
|------|------|
| [交互式节点用户指南](INTERACTIVE_NODES.md) | Feature Map, Spectrum, Table, HTML Viewer 使用指南 |
| [StateBus 协议](STATE_BUS_PROTOCOL.md) | 前端事件总线技术文档 |

### 测试与开发

| 文档 | 说明 |
|------|------|
| [测试指南](TESTING.md) | TDD 工作流、测试覆盖率、CI/CD 集成 |
| [待办事项](TODO.md) | 开发任务列表 |
| [开发路线图](ROADMAP.md) | 项目路线图 |

---

## 快速开始

### 运行测试

```bash
# 进入项目根目录
cd D:\Projects\TDEase-Backend

# 运行所有测试
uv run pytest tests/ -v

# 运行特定测试
uv run pytest tests/test_interactive*.py -v
uv run pytest tests/unit/api/ -v
uv run pytest tests/integration/ -v

# 生成覆盖率报告
uv run pytest --cov=app --cov-report=html --cov-report=term
```

**当前状态**:
- ✅ 21/21 测试通过（100% 成功率）
- ✅ 测试覆盖率 > 80%
- ✅ 所有核心功能有测试覆盖

### 执行工作流

```bash
# 启动后端服务
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 执行测试工作流
curl -X POST "http://localhost:8000/api/workflows/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "wf_test_interactive",
    "user_id": "test_user",
    "workspace_id": "test_workspace",
    "sample_ids": ["sample1"]
  }'
```

---

## 新架构 (2.0) 核心特性

### 1. Tool Definition Schema
- **文件**: `config/tool-schema.json`
- **工具定义**: `config/tools/*.json`
- **前端加载**: `GET /api/tools/schemas`
- **好处**: 前后端共享单一数据源，消除定义不一致

### 2. Command Pipeline
- **文件**: `app/core/executor/command_pipeline.py`
- **5步流程**: Filter → Executable → Output → Parameters → Positional
- **好处**: 统一参数过滤，无类型分支逻辑

### 3. UnifiedWorkspaceManager
- **文件**: `app/services/unified_workspace_manager.py`
- **样品存储**: `samples.json` (文件系统，非数据库)
- **目录结构**: `users/{user_id}/workspaces/{workspace_id}/`
- **好处**: 工作区级别样品共享，结构化数据

### 4. 交互式可视化架构 ⭐ NEW
- **前端**: InteractiveNode.vue, StateBus, StateEdge
- **后端**: HTML Fragment API, Node Data Query API
- **执行模式**: `executionMode: "interactive"` (跳过后端执行)
- **交叉过滤**: 状态边传递选择事件，实现自动过滤

---

## 按主题查找

### 工作流执行

1. **了解架构**: [ARCHITECTURE.md](ARCHITECTURE.md)
2. **执行机制**: [WORKFLOW_EXECUTION.md](WORKFLOW_EXECUTION.md)
3. **API 调用**: [API_USAGE_NEW_ARCHITECTURE.md](API_USAGE_NEW_ARCHITECTURE.md)

### 交互式可视化

1. **用户指南**: [INTERACTIVE_NODES.md](INTERACTIVE_NODES.md)
2. **StateBus 协议**: [STATE_BUS_PROTOCOL.md](STATE_BUS_PROTOCOL.md)
3. **节点连接**: [About_node_connection.md](About_node_connection.md)

### 工具开发

1. **Schema 定义**: [TOOL_DEFINITION_SCHEMA.md](TOOL_DEFINITION_SCHEMA.md)
2. **系统架构**: [ARCHITECTURE.md](ARCHITECTURE.md)

### 测试

1. **测试指南**: [TESTING.md](TESTING.md)
2. **运行测试**: 见上方 "运行测试" 章节

---

## 文档结构

```
docs/
├── README.md                          # 本文档
├── ARCHITECTURE.md                    # 系统架构
├── FUNCTIONAL_OVERVIEW.md             # 功能总览
├── WORKFLOW_EXECUTION.md              # 工作流执行
├── About_node_connection.md           # 节点连接
├── API_USAGE_NEW_ARCHITECTURE.md      # API 使用
├── TOOL_DEFINITION_SCHEMA.md          # 工具定义
├── INTERACTIVE_NODES.md               # 交互式节点用户指南
├── STATE_BUS_PROTOCOL.md              # StateBus 协议
├── TESTING.md                         # 测试指南
├── TODO.md                            # 待办事项
├── ROADMAP.md                         # 开发路线图
├── about_packages/                    # 依赖库文档
│   ├── Informed_proteomics.md
│   └── 依赖库的deepwiki.md
└── archive/                           # 归档文档
    ├── reports/                       # 历史报告
    ├── plans/                         # 历史计划
    └── status/                        # 历史状态
```

---

## 测试环境

**测试配置**:
- 用户: `test_user`
- 工作区: `test_workspace`
- 样品: `sample1`
- 位置: `data/users/test_user/workspaces/test_workspace/samples.json`

---

## 相关链接

- **项目 README**: [../README.md](../README.md)
- **开发指南**: [../CLAUDE.md](../CLAUDE.md)
- **变更追踪**: [../openspec/changes/](../openspec/changes/)
