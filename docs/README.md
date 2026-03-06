# TDEase 系统全局文档 (Version 2.1)

欢迎使用 TDEase 文档中心。为了提供更全面的视角，本基准文档已全面升级，不仅涵盖了最新的**交互式可视化架构 (v2.1)**，还详细描述了系统的**全局后端引擎、批量执行逻辑与工作区隔离机制**。

---

## 📚 核心文档导航

### [1. 需求与全局功能一览](01_requirements_and_features.md)
项目全景矩阵：包含重型后端计算、实时前端交互与 Compute Proxy 实时代理的功能定义。

### [2. 全局数据处理与运行架构](02_workflow_execution_architecture.md)
深度解析 Unified Workspace Manager、5 步命令管道 (Command Pipeline) 以及 CWL 导出机制。

### [3. 前端交互可视化架构](03_frontend_visualization_architecture.md)
探讨 VisContainer 设计、StateBus 状态同步以及如何通过 Compute Proxy 实现亚秒级的生信验证。

### [4. 总体交互架构与生命周期](04_overall_interaction_architecture.md)
对比“高通量批量处理”与“深度探索发现”两种不同的生命周期范式及 Dashboard 模式。

### [5. 全局 API 文档](05_api_documentation.md)
包含执行引擎、实时计算代理 (Fragment Match)、批量配置 (Batch Config) 及资源寻址的全量接口参考。

### [6. 全向测试指南](06_end_to_end_testing.md)
从底层核心、API 集成到 E2E 交互的全方位测试策略与 TDD 实践。

### [7. 待办事项 (TODO)](07_todo.md)
项目里程碑、近期目标与技术债清单。

### [8. 优先测试工作流架构](08_priority_test_workflow.md)
针对 `wf_test_full.json` 基准用例的深度解析，作为流程连接的最佳实践参考。

---

## 🛠️ 快速链接
- **[归档文档中心](archive/README.md)**：查看历史版本的遗留文档。
- **[后端核心代码](file:///d:/Projects/TDEase-Backend/app/core/)**
- **[实时服务代码](file:///d:/Projects/TDEase-Backend/app/api/compute_proxy.py)**
- **[工具定义目录](file:///d:/Projects/TDEase-Backend/config/tools/)**

---

*文档维护者: Antigravity AI*
*更新日期: 2026-03-06*
