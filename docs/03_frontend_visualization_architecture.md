# Section 3: 前端交互可视化架构 (Frontend Visualization Architecture)

## 3.1 核心理念：解耦与实时反馈
TDEase 的前端架构致力于将“节点”转变为“视口”，在高通量计算的基础上提供亚秒级的响应体验。

| 组件类型 | 职责 | 实现技术 |
|------|------------|----------|
| **查看器 (Viewer)** | 专注于特定数据维度的渲染 | ECharts, Ag-Grid, WebGL |
| **容器 (VisContainer)** | 提供通用的工具栏、布局切换、Loading 骨架屏 | Vue 3 Component |
| **总线 (StateBus)** | 管理跨节点的状态同步（虚线橙边逻辑） | RxJS/Reactive State |
| **计算代理 (Compute Proxy)**| 实时处理前端请求的小型运算 | FastAPI Proxy Endpoint |

## 3.2 节点类型与连接语义
系统区分了物理数据的流转与逻辑状态的同步：
- **数据流 (Data Flow)**：实线蓝边，表示文件的逻辑依赖及 Port-Aware 寻址。
- **状态流 (State Flow)**：虚线橙边，决定了 `selection_ids`（选中行索引）或 `viewport`（缩放视口）的路由路径。

## 3.3 StateBus 协议设计 (v1.0)
StateBus 是整个交互架构的“神经系统”，支持：
- **语义化事件**：采用统一编码（如 `state/selection_ids`），使得 FeatureMap 的点击能直接触发 Spectrum 的刷新。
- **循环检测**：自动拦截由状态边组成的有向闭环，确保系统稳定性。

## 3.4 实时计算集成 (Compute Proxy Integration)
为了支持深度的生物信息互动，前端不再仅仅从后端读取文件，还可以实时“提问”：
- **碎片匹配 (Fragment Matching)**：当用户在 Spectrum Viewer 中点击某峰位时，前端调用 `/api/compute-proxy/fragment-match`，后端实时计算理论碎片并返回标注，响应时间通常 < 100ms。
- **动态寻址加载**：通过 API 层的 `port_id` 参数，前端可以从同一个节点的多个物理输出文件中精确拉取目标列，实现真正的多维视图联动。

## 3.5 交互工作流生命周期
1.  **加载态 (Initial Load)**：通过 Port-Aware API 拉取数据 Schema 并渲染基础视图。
2.  **互动态 (Interaction)**：用户进行“画刷”或“点击”操作。
3.  **分派态 (Dispatching)**：StateBus 捕获事件并路由至逻辑相关的下游节点。
4.  **代理计算态 (Proxy Compute)**：针对复杂的验证操作（如 PTM 修饰搜索），实时请求 Compute Proxy。

## 3.6 维护性约束（2026-03-06）
- **连接类型推断以端口语义为准**：当端口组合为 `state-out -> state-in` 时，前端导入与 Store 归一化阶段必须强制识别为 `state`，即便旧工作流 JSON 中 `connectionKind` 被写成 `data`。
- **FeatureMap 映射自动补全**：当后端未提供稳定列类型或节点首次加载时，FeatureMap 需基于列名与样本值自动推断 `startTime/endTime/mass/intensity`，避免出现“总行数正常但渲染点为 0”的假异常。
- **采样标识只反映真实采样**：`Sampled x/y` 仅在 `x > 0 且 x < y` 时显示，防止未配置映射场景被误判为采样导致的空图。
