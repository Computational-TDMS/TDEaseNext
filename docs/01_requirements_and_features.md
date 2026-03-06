# Section 1: 核心需求与全景功能 (Global Requirements & Features)

## 1.1 系统定位
TDEase 是一个集成了**重型后端计算**与**实时前端交互**的质谱数据分析中台。它不仅支持大规模、多步骤的生物信息学工作流编排，还提供了用于实时探索的交互式节点和轻量级计算代理。

## 1.2 全球功能矩阵 (Global Capabilities)
### A. 工作流编排与执行 (Core Engine)
- **多引擎支持**：内置本地 Shell/Conda 运行器，支持多阶段 DAG 调度。
- **标准化输出 (CWL)**：支持将图形化工作流导出为标准化 Common Workflow Language (CWL)，提升流程的可移植性与可复现性。
- **批量处理逻辑**：支持多样品并发执行，通过 `BatchConfig` 独立管理多样本间的参数差异。

### B. 交互式数据探索 (Interactive Visualization)
- **零延迟交互**：基于 v2.1 架构，通过 `VisContainer` 和 `StateBus` 实现多节点（Feature Map <-> Spectrum <-> Table）间的瞬间状态映射与交叉过滤。
- **报表模式 (Dashboard)**：一键将画布节点转化为线性报表，提升审阅效率。

### C. 实时计算代理 (Compute Proxy)
- **实时匹配**：提供亚秒级的 `fragment-match`（碎片匹配）与 `modification-search`（修饰搜索）API，无需启动完整工作流即可实时更新 UI 组件。
- **动态寻址**：通过 Port-Aware 寻址协议，精确提取多输出工具（如 TopFD）中的特定列数据。

## 1.3 核心业务路径
1.  **高通量处理路径**：原始 Raw 文件 -> 批量解析 (Batch) -> 数据导出 (CWL/TSV)。
2.  **深度探索路径**：特征提取 -> 基于画布的可视化交互 -> 全球筛选 -> 报告导出。
3.  **实时验证路径**：在 Spectrum 视图中框选峰位 -> 调用 Compute Proxy 进行修饰匹配 -> 即时标注。

## 1.4 技术约束与规范
- **Schema 强约束**：工具的所有输入、输出和参数均由统一的 JSON 定义，前端动态渲染 UI。
- **工作区隔离**：采用 `users/{u}/workspaces/{w}` 的三级隔离存储结构，支持多用户并发环境。
