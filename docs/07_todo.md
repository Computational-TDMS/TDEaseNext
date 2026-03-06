# Section 7: 待办事项 (TODO)

> [!NOTE]
> 本文档保留原始 `TODO.md` 的所有内容，仅作为文档体系的一部分进行逻辑归类。

# TDEase 开发路线图

**更新日期**: 2026-03-06
**项目定位**: 基于节点的质谱数据分析工作流平台
**核心理念**: Make it work first，渐进式增强

---

## 当前状态

### ✅ 已完成的核心功能

**执行引擎**:
- ✅ FlowEngine DAG 调度器
- ✅ LocalExecutor + ShellRunner
- ✅ CommandPipeline 5步命令构建
- ✅ ProcessRegistry 进程管理
- ✅ 工作流取消 (SIGTERM → SIGKILL)
- ✅ 实时日志推送 (WebSocket)

**工具系统**:
- ✅ JSON Schema 驱动的工具定义
- ✅ 命令预览 API
- ✅ 跨平台路径管理
- ✅ Docker/Python 脚本工具支持

**可视化**:
- ✅ 交互式可视化节点 (FeatureMap, Spectrum, Table, HTML)
- ✅ StateBus 状态总线
- ✅ Composables-First 架构
- ✅ 单元测试 58/58 通过 (100%)

**数据访问**:
- ✅ 节点输出数据 API
- ✅ 工作区文件浏览
- ✅ HTML 片段 API
- ✅ LRU 缓存机制

**可运行的完整流程**:
```
data_loader → msconvert → topfd → toppic → promex
```

---

## 🎯 短期目标 (1-2周)

### 1. 修复剩余类型错误
**优先级**: 高
**状态**: 进行中

- [ ] InteractiveNode.vue - handleExport 类型不匹配
- [ ] FeatureMapViewer.vue - EChartsType 使用问题
- [ ] ScatterPlotViewer.vue - EChartsType 使用问题
- [ ] 清理未使用的变量和导入

**预期结果**: 编译零错误

### 2. 性能优化
**优先级**: 中

- [ ] WebGL 加速 (50k+ 数据点)
- [ ] 虚拟滚动优化
- [ ] 按需加载策略

### 3. E2E 测试
**优先级**: 中

- [ ] Playwright 测试套件
- [ ] 关键用户流程覆盖
- [ ] 视觉回归测试

---

## 🚀 中期目标 (1-2个月)

### 1. AI Agent 集成
**优先级**: 高

**目标**: 使用 AI Agent 辅助工作流设计和数据查询

**功能**:
- [ ] 自然语言生成工作流
- [ ] 智能推荐工具组合
- [ ] 参数优化建议
- [ ] 错误诊断和修复
- [ ] UniProt 数据库查询集成

### 2. 序列可视化
**优先级**: 高

**功能**:
- [ ] 氨基酸序列渲染
- [ ] PTM 位点标注
- [ ] 序列比对视图
- [ ] 蛋白质结构可视化

### 3. 多样品管理
**优先级**: 中

**功能**:
- [ ] 样品比对界面
- [ ] 批量执行
- [ ] 结果汇总
- [ ] 样品上下文自动推导

---

## 🔭 长期目标 (3-6个月)

### 1. 用户自定义扩展
**优先级**: 中

- [ ] 用户自定义工具注册
- [ ] 自定义节点类型
- [ ] 插件系统
- [ ] 工作流模板市场

### 2. 协作功能
**优先级**: 低

- [ ] 用户认证和授权
- [ ] 工作流共享
- [ ] 团队工作空间
- [ ] 审计日志

### 3. 高级工作流功能
**优先级**: 中

- [ ] Hot Run 模式
- [ ] 断点续传
- [ ] 工作流版本管理
- [ ] 导入导出 (CWL, Nextflow)

---

## 💡 想法与探索

### 前端优化
- 节点进度条动画（替代全量日志）
- 更美观的节点设计（使用 AI 辅助）
- 响应式布局优化

### 工具生态
- 条件输出工具处理
- 工具间数据格式对齐
- 翻译节点（数据格式转换）

### 部署与性能
- Windows 原生运行（已完成 ✅）
- Docker 容器化
- 压力测试
- API 速率限制

---

## 🛠️ 技术债务

### 代码质量
- [ ] 提升测试覆盖率到 80%+
- [ ] 代码审查流程
- [ ] 性能基准测试
- [ ] 文档自动生成

### 架构优化
- [ ] 组件进一步拆分
- [ ] 状态管理优化
- [ ] 错误处理统一
- [ ] 日志系统完善

---

## 📚 参考资源

### 内部文档
- [系统架构](ARCHITECTURE.md)
- [功能目标与实现](FUNCTIONAL_OVERVIEW.md)
- [工作流执行机制](WORKFLOW_EXECUTION.md)
- [交互式节点](INTERACTIVE_NODES.md)
- [StateBus 协议](STATE_BUS_PROTOCOL.md)

### 外部参考
- TOPMSV (峰谱图可视化)
- Galaxy 工作流系统
- CWL (Common Workflow Language)
- Nextflow

---

## 📝 开发原则

1. **Make it work first**: 功能优先于架构
2. **渐进式增强**: 不过度设计未来需求
3. **Schema-driven**: 单一数据源，消除不一致
4. **可测试性**: MockExecutor 支持后端测试
5. **用户反馈**: Eat your own dog food
