
# TODO

1. 还是没有实现点击后直接进入页面然后展示其内容! 这需要

需要使用Gemini来对前端的节点的美观度继续进行重新设计!

其余部分的兼容性, 我们则可以使用其他模型来进行微调!




for claude code to do:

我的前端正在搭建 @openspec/specs/interactive-visualization-nodes\
  @TDEase-FrontEnd\openspec\changes\add-visualization-nodes 提案,
  那么后端是否还有需要调整的地方?  我们或许会需要更新我们的测试工作流,
  在toppic的后面加入featuremap 与spectrum! 

- 序列可视化! 很重要!



看到Galaxy 压力很大, 毕竟是老前辈, 不过我们这个时代最注重安全, 容易部署将会成为最大的卖点! 尤其是我们的windows系统原生运行!


对于ToppicR这样的体系 我们该如何对其功能进行拆分? 然后如何搭建出重新组合的体系?


- 有时候有些工具是条件输出, 这时候该怎么做呢? 
- 1. 给出提示
2. 用户可以自行标注不可见
3. 我们完全没有必要为每个工具专门添加条件判断逻辑!


- 如何实现不同的工具体系之间的杂交?
- 输出文件给定一个标注, 而非严格按照其后缀

- 如果识别到进行杂交, 那么就自动修改文件名字(复制然后修改), 或者修改列名, 总之进行对齐, 从而完成调整!

或者直接简单添加几个翻译节点!(成本更低! 也更符合原生设计理念!)


- 之后完成前端交互可视化部分开发后, 需要在添加节点的过程中逐步进行整个体系的螺旋迭代!


- ! immediate:  对可视化节点的交互设计还需要优化:

1. 编辑哪些参数?
2. 文件传入接口? 还是设计成特定文件的特定列的传入?


后端依旧无法停止工作流, 无法优雅中止!


# TDEase 开发日志 (DevLog)

> **项目定位**: 基于节点的质谱数据分析工作流平台
> **核心理念**: 让 it works first，而非过度设计架构
> **开发方式**: AI 辅助开发，无固定时间预期

---

## 快速导航

- [当前状态](#当前状态) - 我们现在在哪里
- [已完成](#已完成) - 已经实现的功能
- [进行中](#进行中) - 当前正在处理的问题
- [待探索](#待探索) - 想法与笔记
- [技术决策记录](#技术决策记录) - 重要的架构选择

---

## 当前状态

**架构**: 已从 Snakemake 编译模式迁移到直接 Shell 执行模式 , 并且使用codex来对后端进行鲁棒性优化, 从而实现了对pbfgen等工具的支持!
**核心**: Node-based 工作流，通过 VueFlow JSON 直接驱动
**执行**: LocalExecutor + ShellRunner + ProcessRegistry
**数据**: SQLite 持久化 + WebSocket 实时推送

### 可运行的完整流程

```
data_loader → msconvert → topfd → toppic → promex
```

### 核心能力

✅ 工作流编排 (VueFlow → FlowEngine)
✅ 工具注册系统 (JSON Schema 驱动)
✅ 命令构建管道 (5步: Filter → Executable → Output → Parameters → Positional)
✅ 文件追踪 (输入路径解析 + 输出路径推导)
✅ 执行状态管理 (节点级状态追踪)
✅ 工作流取消 (SIGTERM → SIGKILL 两阶段终止)
✅ 实时日志推送 (WebSocket + 轮询降级)

---

## 已完成

### 基础设施

- [X] 环境配置简化
- [X] 基础节点系统
- [X] 工具定义 Schema
- [X] Docker 工具支持 (MSConvert, TopPIC)
- [X] Python 脚本工具支持
- [X] 跨平台路径管理

### 执行引擎

- [X] 从 Snakemake 迁移到 Shell 执行
- [X] FlowEngine DAG 调度器
- [X] LocalExecutor 任务执行
- [X] CommandPipeline 命令构建
- [X] 命令预览 API (POST /api/tools/preview)
  - 前端参数面板使用服务端预览
  - 确保预览与实际执行完全一致
- [X] WorkflowService 编排服务
- [X] ExecutionStore 状态持久化
- [X] 模拟执行工具 (MockExecutor)
- [X] 全流程跑通 (raw → toppic → promex)

### 工作流取消

- [X] ProcessRegistry 全局进程注册表
- [X] 两阶段终止机制 (SIGTERM → SIGKILL)
- [X] ExecutionManager 增强 (运行中节点追踪)
- [X] API 兼容性 (POST /api/executions/{id}/stop)
- [X] 线程安全支持

### 兼容性修复

- [X] 移除不必要的文件格式限制
- [X] 修复 data_loader 执行问题
- [X] 工具注册灵活性改进
- [X] JSON Schema 验证增强

###  文档建设

- [X] 系统架构文档 (ARCHITECTURE.md)
- [X] 功能目标与实现 (FUNCTIONAL_OVERVIEW.md)
- [X] 工作流执行机制 (WORKFLOW_EXECUTION.md)
- [X] 节点连接与数据传递 (About_node_connection.md)
- [X] 开发路线图 (ROADMAP.md)


### 前端基础交互

- [X] 基础工作流编辑器 (FlowEditor)
- [X] 后端工作区文件目录的浏览



---

## 进行中

### 🎯 工作区数据访问功能

**状态**: 设计阶段 (见 `openspec/changes/backend-workspace-access/`)

**目标**: 为前端交互式可视化节点提供后端数据访问支持

**待实现**:
- [ ] 节点输出数据 API
- [ ] 工作区文件浏览 API
- [ ] 最新执行查询 API
- [ ] 文件内容预览和解析服务

### 🎯 交互式可视化节点

**状态**: 设计阶段 (见 `openspec/changes/interactive-visualization/`)

**目标**: 实现前端交互式数据可视化能力

**待实现**:
- [ ] FeatureMap Viewer 节点
- [ ] Spectrum Viewer 节点
- [ ] Table Viewer 节点
- [ ] 节点间状态传递机制
- [ ] Pinia Store 数据管理

### 


---

## 待探索

### 前端优化

**想法**: 后端数据读取 → 前端可视化流程

**问题**:
1. 结果数据前后端传递机制
2. 结果数据在前端的读取与可视化处理
3. 多级别数据读取与传递能力
4. 用户自定义数据筛选功能
5. 前端直接编辑 FASTA 文件

### 样品管理

**想法**: 样品是核心抽象，需要更好的管理

**问题**:
- [ ] 多样品管理
- [ ] 样品比对
- [ ] 同步运行
- [ ] 样品上下文推导自动化

### 工作流功能

**想法**: 增强工作流的可用性和灵活性

**问题**:
- [ ] Hot Run 模式 (修改节点后立即执行)
- [ ] 断点续传完善
- [ ] 工作流版本管理
- [ ] 工作流导入导出 (CWL, Nextflow)
- [ ] 工作流模板系统

### 可视化增强

**想法**: 嵌入常见的数据可视化组件

**参考**:
- TOPMSV 的峰谱图可视化
- 商业化论文中的序列可视化

**核心**: 输入输出数据 IO 的处理应对

### 用户自定义

**想法**: 让用户能够扩展系统能力

**问题**:
- [ ] 用户自定义工具注册
- [ ] 这里的工具参数的编辑交互上需要询问使用者的意见, 从而实现真正高效的交互, 当然了, 我自己也得eat dogfood02
- [ ] 自定义节点类型
- [ ] PTMs 筛选接入数据库
- [ ] 结果数据回滚



### Agent 集成

**想法**: AI Agent 辅助工作流设计

**问题**:
- [ ] 自然语言生成工作流
- [ ] 智能推荐工具组合
- [ ] 参数优化建议
- [ ] 错误诊断和修复
- [ ] Agent 权限管理
- [ ] 通知机制 (OpenClaw?)

### 更好的用户交互 (low)

1. 不再全量输出log, 而是将进程转化为进度条, 直接在节点上以动画的方式进行呈现


### 部署与性能

**想法**: 系统的稳定性和可扩展性

**问题**:
- [ ] 部署方案
- [ ] 压力测试
- [ ] 性能优化
- [ ] 缓存机制
- [ ] API 速率限制

### 多用户协作

**想法**: 团队使用场景

**问题**:
- [ ] 用户认证和授权
- [ ] 工作流共享
- [ ] 团队工作空间
- [ ] 审计日志

---

## 技术决策记录

### 2025-XX-XX: 从 Snakemake 迁移到 Shell 执行

**决策原因**:
- Snakemake 远程功能不完善
- 过度设计，增加复杂度
- Shell 执行足够满足当前需求
- 不影响未来远程功能扩展

**影响**:
- 简化了架构
- 提高了可维护性
- 需要自己实现 DAG 调度 (FlowEngine)

### 2025-XX-XX: JSON Schema 驱动的工具定义

**决策原因**:
- 前后端共享单一数据源
- 动态生成参数配置界面
- 易于添加新工具

**影响**:
- 需要维护 Schema 版本
- 工具定义文件在 `config/tools/*.json`

### 2026-03-04: 两阶段进程终止

**决策原因**:
- 平衡优雅退出和响应速度
- 给工具清理临时文件的机会
- 防止进程泄漏

**实现**:
- SIGTERM (3秒超时) → SIGKILL
- ProcessRegistry 全局单例

### 2026-03-04: 文件系统存储样品数据

**决策原因**:
- 工作区级别的共享
- 便于版本控制和迁移
- 减少数据库查询压力

**影响**:
- `samples.json` 文件格式
- UnifiedWorkspaceManager 管理层

---

## 开发笔记

### 核心原则

1. **Make it work first**: 功能优先于架构
2. **渐进式增强**: 不过度设计未来需求
3. **Schema-driven**: 单一数据源，消除不一致
4. **可测试性**: MockExecutor 支持后端测试

### 重要提醒

- [ ] 不要一开始就想设计完美的文件架构
- [ ] 有初步的功能与信息传递架构即可
- [ ] 工作流运行与停止应当做到令行禁止
- [ ] 文件传递和路径识别管理需要保证普适性
- [ ] 样品管理是核心抽象

### 下一步行动

1. 实现工作区数据访问 API
2. 开发交互式可视化节点
3. 完善样品管理功能
4. 增强前端工作流编辑器

---

## 参考资源

### 内部文档
- [系统架构](ARCHITECTURE.md)
- [功能目标与实现](FUNCTIONAL_OVERVIEW.md)
- [工作流执行机制](WORKFLOW_EXECUTION.md)
- [节点连接与数据传递](About_node_connection.md)
- [开发路线图](ROADMAP.md)

### 外部参考
- TOPMSV (峰谱图可视化)
- 商业化论文 (序列可视化)
- CWL (Common Workflow Language)
- Nextflow

---

*最后更新: 2026-03-04*
