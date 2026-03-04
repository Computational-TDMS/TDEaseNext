# TDEase 文档导航

**版本**: 2.0 (新架构)
**更新日期**: 2026-03-02

## 快速开始

### 核心文档

| 文档 | 说明 |
|------|------|
| [系统架构](ARCHITECTURE.md) | 新架构总览 - Command Pipeline, UnifiedWorkspaceManager, Tool Definition Schema |
| [功能目标与实现](FUNCTIONAL_OVERVIEW.md) | 核心功能目标和实现方式 - 工作流编排、工具注册、样品管理、执行引擎 |
| [工作流执行机制](WORKFLOW_EXECUTION.md) | 工作流执行流程、工具后端映射、文件追踪详解 |
| [节点连接与数据传递](About_node_connection.md) | 节点连接类型、数据流、输入输出路径解析 |
| [API 文档](api/endpoints.md) | RESTful API 端点 - 工作流执行、工具管理、可视化 API |
| [API 使用示例](API_USAGE_NEW_ARCHITECTURE.md) | 新架构 API 调用示例（Python/cURL） |
| **交互式工作流需求** | **用户工作流交互目标，为架构设计提供需求输入** |
| [工作流需求文档](WORKFLOW_REQUIREMENTS.md) | 交互式工作流的核心需求、参考工具设计、待实现功能 |

### 使用指南

| 文档 | 说明 |
|------|------|
| [工作流格式](guides/workflow-format.md) | VueFlow 工作流 JSON 格式 |
| [工作空间管理](guides/workspace-management.md) | 文件传递和路径管理 |
| [工具注册](guides/tool-registration.md) | 如何添加新工具 |

---

## 新架构 (2.0) 核心变化

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

### 4. 新 API 格式
```json
// 旧格式（已弃用）
{
  "workflow": {...},
  "parameters": {
    "sample_context": {"sample": "sample1"}
  }
}

// 新格式
{
  "workflow_id": "wf_test_full",
  "user_id": "test_user",
  "workspace_id": "test_workspace",
  "sample_ids": ["sample1"]
}
```

---

## 按主题查找

### 工作流执行

1. **了解架构**: [ARCHITECTURE.md](ARCHITECTURE.md)
2. **调用 API**: [api/endpoints.md](api/endpoints.md) - 工作流执行 API
3. **使用示例**: [API_USAGE_NEW_ARCHITECTURE.md](API_USAGE_NEW_ARCHITECTURE.md)
4. **格式说明**: [guides/workflow-format.md](guides/workflow-format.md)

### 工具开发

1. **Schema 定义**: [ARCHITECTURE.md](ARCHITECTURE.md#1-tool-definition-schema-d1)
2. **注册工具**: [guides/tool-registration.md](guides/tool-registration.md)
3. **工具 API**: [api/endpoints.md](api/endpoints.md#3-工具管理-api)

### 样品管理

1. **架构说明**: [ARCHITECTURE.md](ARCHITECTURE.md#3-structured-samples-d3)
2. **工作区管理**: [guides/workspace-management.md](guides/workspace-management.md)
3. **Workspace API**: [api/endpoints.md](api/endpoints.md#5-工作区管理-api)

### 可视化

1. **可视化节点**: [ARCHITECTURE.md](ARCHITECTURE.md#5-可视化节点扩展点-d5)
2. **数据 API**: [api/endpoints.md](api/endpoints.md#4-可视化-api-新增)

---

## 测试环境

**测试配置**:
- 用户: `test_user`
- 工作区: `test_workspace`
- 样品: `sample1`
- 位置: `data/users/test_user/workspaces/test_workspace/samples.json`

**快速测试**:
```bash
# 启动后端
cd D:/Projects/TDEase-Backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 执行测试工作流
curl -X POST "http://localhost:8000/api/workflows/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "wf_test_full",
    "user_id": "test_user",
    "workspace_id": "test_workspace",
    "sample_ids": ["sample1"]
  }'
```

---

## 文档结构

```
docs/
├── README.md                          # 本文档
├── ARCHITECTURE.md                    # 系统架构（新架构）
├── API_USAGE_NEW_ARCHITECTURE.md      # API 使用示例
├── api/
│   └── endpoints.md                   # API 端点（新架构）
├── guides/
│   ├── workflow-format.md             # 工作流格式
│   ├── workspace-management.md        # 工作空间管理
│   └── tool-registration.md           # 工具注册
├── ROADMAP.md                         # 开发路线图
└── archive/                           # 归档文档
```

---

## 相关链接

- **项目 README**: [../README.md](../README.md)
- **开发指南**: [../CLAUDE.md](../CLAUDE.md)
- **变更追踪**: [../openspec/changes/redesign-cmd-and-sample-management/](../openspec/changes/redesign-cmd-and-sample-management/)
