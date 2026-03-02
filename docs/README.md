# TDEase 文档

## 📚 文档导航

欢迎来到 TDEase 质谱数据分析工作流平台文档！

### 快速开始

- [项目 README](../README.md) - 项目概述和快速开始指南
- [开发指南](../CLAUDE.md) - AI 和开发者核心参考文档
- [架构文档](ARCHITECTURE.md) - 系统架构总览
- [开发路线图](ROADMAP.md) - 项目进度和规划

### 核心文档

#### 📖 [系统架构](ARCHITECTURE.md)
完整的系统架构说明，包括：
- 架构概述和演进历史
- 技术栈介绍
- 系统架构图和数据流
- 核心组件说明
- 执行流程详解

#### 🗺️ [开发路线图](ROADMAP.md)
项目发展计划，包括：
- 已完成功能列表
- 进行中的工作
- 短期/中期/长期计划
- 发布计划和时间表
- 技术债务清单

#### 🔌 [API 文档](api/)
- [端点文档](api/endpoints.md) - RESTful API 端点说明
  - 工作流管理 API
  - 执行管理 API
  - 工具管理 API
  - 文件管理 API
  - 批量配置 API

#### 📖 [使用指南](guides/)
- [工作流格式说明](guides/workflow-format.md) - VueFlow 工作流 JSON 格式
- [工作空间管理](guides/workspace-management.md) - 文件传递和路径管理
- [工具注册指南](guides/tool-registration.md) - 如何添加新工具

### 详细文档

#### 数据库设计
- [DATABASE_DESIGN](current%20status/DATABASE_DESIGN.md) - 数据库架构和表结构

#### 前后端交互
- [前后端交互分析](current%20status/%E5%89%8D%E5%90%8E%E7%AB%AF%E4%BA%A4%E4%BA%92%E5%88%86%E6%9E%90.md) - 前后端交互逻辑和已知问题

#### 实现计划
- [节点执行与同步](plan/node_execution_and_sync.md) - Hot Run 模式和实时同步方案

#### 归档文档
- [phase3 计划](archive/phase3.md) - 旧的开发计划（已整合到 ROADMAP.md）
- [phase4 计划](archive/phase4.md) - 旧的开发计划（已整合到 ROADMAP.md）
- [后端重构](archive/%E5%90%8E%E7%AB%AF%E9%87%8D%E6%9E%84.md) - 后端重构文档（已完成）

---

## 🎯 按主题查找

### 工作流相关
- [工作流格式说明](guides/workflow-format.md) - JSON 格式定义
- [工作流管理 API](api/endpoints.md#工作流管理-api) - CRUD 操作
- [工作流执行 API](api/endpoints.md#工作流执行-api) - 执行和监控

### 工具相关
- [工具注册指南](guides/tool-registration.md) - 添加新工具
- [工具管理 API](api/endpoints.md#工具管理-api) - 工具 CRUD 操作
- [工具定义示例](guides/tool-registration.md#工具示例) - 参考配置

### 执行相关
- [执行流程](ARCHITECTURE.md#执行流程) - 如何执行工作流
- [执行管理 API](api/endpoints.md#执行管理-api) - 状态查询和控制
- [节点执行与同步](plan/node_execution_and_sync.md) - Hot Run 模式

### 文件相关
- [工作空间管理](guides/workspace-management.md) - 路径和文件传递
- [文件管理 API](api/endpoints.md#文件管理-api) - 上传下载操作

---

## 🚀 快速链接

### 新手入门
1. 阅读 [项目 README](../README.md) 了解项目
2. 查看 [系统架构](ARCHITECTURE.md) 理解设计
3. 学习 [工具注册指南](guides/tool-registration.md) 添加工具
4. 参考 [API 文档](api/endpoints.md) 开发集成

### 开发者
1. 查看 [开发指南](../CLAUDE.md) 了解代码规范
2. 阅读 [开发路线图](ROADMAP.md) 了解任务优先级
3. 研究 [架构文档](ARCHITECTURE.md#核心组件) 理解组件
4. 参考 [数据库设计](current%20status/DATABASE_DESIGN.md) 设计数据模型

### 贡献者
1. 查看 [开发路线图](ROADMAP.md#贡献指南) 了解贡献流程
2. 查看 [TODO.md](../TODO.md) 寻找任务
3. 阅读 [前后端交互分析](current%20status/%E5%89%8D%E5%90%8E%E7%AB%AF%E4%BA%A4%E4%BA%92%E5%88%86%E6%9E%90.md#%E5%B7%B2%E7%9F%A5%E9%97%AE%E9%A2%98) 找到问题
4. 参考 [已知问题](../CLAUDE.md#%F0%9F%90%9B-known-issues--solutions) 解决 Bug

---

## 📝 文档结构

```
docs/
├── README.md                      # 本文档 - 文档导航
├── ARCHITECTURE.md                # 系统架构总览
├── ROADMAP.md                     # 开发路线图
├── api/                           # API 文档
│   └── endpoints.md               # API 端点说明
├── guides/                        # 使用指南
│   ├── workflow-format.md         # 工作流格式
│   ├── workspace-management.md    # 工作空间管理
│   └── tool-registration.md       # 工具注册
├── current status/                # 当前实现状态
│   ├── backend.md                 # 后端架构详细说明
│   ├── DATABASE_DESIGN.md         # 数据库设计
│   ├── workflowjson_define.md     # 工作流JSON格式
│   ├── 前后端交互分析.md           # 前后端交互
│   ├── api.md                     # API文档（已移至api/endpoints.md）
│   └── workspace.md               # 工作空间（已移至guides/）
├── plan/                          # 实施计划
│   └── node_execution_and_sync.md # 节点执行与同步
└── archive/                       # 归档文档
    ├── phase3.md                  # 旧计划文档
    ├── phase4.md                  # 旧计划文档
    └── 后端重构.md                 # 重构文档
```

---

## 🔍 搜索提示

### 我想...

- **了解项目**: 从 [项目 README](../README.md) 和 [系统架构](ARCHITECTURE.md) 开始
- **添加新工具**: 阅读 [工具注册指南](guides/tool-registration.md)
- **调用 API**: 查看 [API 文档](api/endpoints.md)
- **理解执行流程**: 参考 [执行流程](ARCHITECTURE.md#执行流程) 和 [节点执行与同步](plan/node_execution_and_sync.md)
- **设计工作流**: 学习 [工作流格式说明](guides/workflow-format.md)
- **管理文件**: 查看 [工作空间管理](guides/workspace-management.md)
- **查找已知问题**: 参考 [已知问题](../CLAUDE.md#%F0%9F%90%9B-known-issues--solutions)
- **贡献代码**: 查看 [开发路线图](ROADMAP.md#贡献指南) 和 [开发指南](../CLAUDE.md)

---

## 📧 获取帮助

- 提交 Issue: [GitHub Issues](https://github.com/your-org/TDEase-Backend/issues)
- 查看文档: 在线文档（本站点）
- 讨论交流: [GitHub Discussions](https://github.com/your-org/TDEase-Backend/discussions)

---

## 📄 许可证

MIT License - 详见 [LICENSE](../LICENSE) 文件
