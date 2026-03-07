# Section 4: 总体交互架构与生命周期 (Overall Interaction & Lifecycle)

## 4.1 双管线生命周期 (Dual-Pipeline Lifecycle)
TDEase 的全局设计兼容了两种完全不同的科研工作流范式：

### A. 宽口径、高通量管线 (High-Throughput Pipeline)
- **目标**：对海量数据进行批处理。
- **流程**：`Batch Config 设计 -> 执行分派 (Batch Dispatcher) -> 后端集群/本地并发执行 -> 产物规档 (Execution Store) -> (可选) 导出 CWL`。
- **前端角色**：监控进度、展示全量日志、输出统计图表。

### B. 窄口径、深度探索管线 (Deep Discovery Pipeline)
- **目标**：对特定样本进行精细化的交互验证。
- **流程**：`画布设计 -> 触发执行 -> 获取 Interactive 节点挂载 -> 使用 Viewer 钻取数据 -> 调用 Compute Proxy 进行修饰验证 -> 保存交互快照`。
- **前端角色**：核心交互空间、StateBus 同步、实时可视化渲染。

## 4.2 全局交互模式：三位一体
1.  **画布设计模式 (Design Mode)**：
    - 在 VueFlow 空间进行逻辑编排。
    - 定义数据流（实线）与状态流（虚线）。
2.  **本地/报表审阅模式 (Dashboard Mode)**：
    - 将交互节点从画布中剥离，形成线性的报告视图。
    - **Headless 渲染**：`VisContainer` 自动切换为受限的“只读/审阅”布局，适用于快速审阅实验结果。
3.  **实时操作模式 (Live Action)**：
    - 针对单个 Viewer 进行极限操作（如超大表格滚动、质谱图局部缩放）。
    - 结合 **Compute Proxy** 进行理论匹配。

## 4.3 状态持久化与快照机制
- **Interaction Snapshots**：系统会将用户在交互阶段的选择、过滤条件和自定义轴映射保存。
- **可分享的 Execution Record**：执行记录不仅包含物理输出，还嵌入了交互状态。通过共享快照 ID，其他研究人员可以瞬间复现当时的视觉分片。

## 4.4 通用交互数据协议 (Interactive Data Provider)
- **DataResolverRegistry**：按名称注册 resolver（如 `topmsv_prsm`），实现“根据选择键加载详细数据”的通用协议。
- **通用 API**：`GET /api/executions/{eid}/nodes/{nid}/interactive-data/{selection_key}?resolver=...` 统一入口，避免为每种查看器新增专属端点。
- **工具定义驱动**：resolver 从源节点的工具定义中读取 `subResources` 等配置解析路径，保证普适性与可扩展性。
- **Interactive 节点语义**：工具定义中的 `interactiveBehavior.dataPassthrough` 显式控制输入绑定规划时的“穿透”行为，替代隐式约定。

## 4.5 架构演进方向
- **AI-Agent 介入**：支持通过自然语言直接下达“展示质量大于 3000 的所有特征”等指令，Agent 将自动修改 StateBus 的过滤状态或更新 `data-query` 参数。
- **分布式执行**：未来支持将 Batch 任务卸载至云端或 Kubernetes 集群，而本地仅保留 Interactive 计算代理。
