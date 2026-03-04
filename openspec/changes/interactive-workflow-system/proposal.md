# Proposal: Interactive Workflow System — 状态驱动的交互式节点架构

## Why

当前 TDEase 已完成基础的交互式可视化节点（`interactive-visualization` change），具备 FeatureMap、Spectrum、Table 三种查看器和简单的选择状态传递。但现有系统存在以下核心局限：

1. **节点架构固化**：每个 Viewer 是一个巨石组件（Monolith），内含渲染、过滤、交互逻辑，难以复用和扩展
2. **联动能力有限**：节点间仅传递简单的 `SelectionState`（选中索引集合），无法表达复杂的过滤链、数据投影、范围约束
3. **前后端边界模糊**：纯前端状态流无法处理需要后端算力的交互（如碎片离子匹配、修饰搜索）
4. **缺少用户自定义能力**：非专业用户无法自由组装交互规则，必须由开发者预设联动逻辑
5. **无法支撑多级数据挖掘**：FeatureMap → Spectrum → MS2 → 修饰标注的渐进式漏斗无法通过现有架构表达

此变更引入**状态端口驱动（State-Port Driven）**的交互式节点体系，将现有的"单体可视化节点"拆分为可组合的原子单元，实现：
- 非专业用户通过**连线**自定义交互规则
- 前端状态流与后端计算代理（Compute Proxy）无缝融合
- 多分支并行的探索工作流

## What Changes

### 核心架构：三端口模型

每个交互式节点从只有 data-in/data-out 演进为**三类端口**：

```
┌─────────────────────────────────────────────────────┐
│              Interactive Node                        │
│                                                     │
│  ■ Data Ports                                       │
│    ── data_in:  接收上游数据（文件/表格）              │
│    ── data_out: 输出转换后数据                        │
│                                                     │
│  ▣ State Input Ports                                │
│    ── filter_in:    接收外部过滤条件                  │
│    ── highlight_in: 接收外部高亮 ID 集合              │
│                                                     │
│  ▲ State Output Ports                               │
│    ── selection_out: 广播用户框选/点击的选中项         │
│    ── viewport_out:  广播当前视野范围                 │
│                                                     │
└─────────────────────────────────────────────────────┘
```

用户通过在画布上连线 State Output → State Input，就完成了交互规则的定义。

### 节点拆分为原子化可视化组件

| 旧架构（Monolith）           | 新架构（Atomic）                           |
|-----------------------------|-----------------------------------------|
| `FeatureMapViewer` 包含渲染+过滤+选择 | `ScatterPlotNode` + 内嵌 Filter/Brush 组件 |
| `SpectrumViewer` 包含峰标注逻辑       | `SpectrumNode` + `AnnotationOverlay` 组件  |
| `TableViewer` 包含排序+过滤           | `TableNode` + `ColumnFilter` 组件          |

### 后端计算代理 (Compute Proxy)

对于需要后端算力的交互（如给定序列，自动在 MS2 谱图标注 b/y 碎片离子）：

```
前端触发 → 后端轻量 API → 返回标注数据 → Viewer 渲染标签
         (状态变更)   (WebSocket/REST)
```

新增 `compute-proxy` API 端点，允许交互式节点在收到特定 State Input 后向后端请求即时计算。

### 语义类型系统 (Semantic Type System)

端口兼容性由语义类型决定，而非文件扩展名：

| 语义类型                     | 含义                                   | 示例端口                |
|-----------------------------|---------------------------------------|------------------------|
| `data/table`                | 任何表格化数据（包含 columns/rows）       | ScatterPlot.data_in     |
| `data/spectrum`             | 质谱数据 [mz, intensity] 数组           | SpectrumNode.data_in    |
| `state/selection_ids`       | 选中行 ID 集合 `Set<number>`            | *.selection_out          |
| `state/range`               | 数值范围 `{min, max, column}`           | FilterNode.range_out    |
| `state/sequence`            | 氨基酸序列字符串                        | SequenceInput.seq_out   |
| `state/annotation_request`  | 标注请求 (序列+谱图数据)                 | → 触发 Compute Proxy    |

画布在连线时自动校验类型兼容性。

### 状态总线 (State Bus) 增强

现有 `visualization` Store 将升级为 **State Bus**：
- 节点不直接 `emit`，而是向总线 `dispatch` 状态更新
- 总线校验循环依赖（防死锁）后再分发
- 支持多分支的上下文隔离（Context Scope）

### 多分支并行支持

```
        [全局 FeatureMap]
         ↙           ↘
[分支A: Charge=2]   [分支B: Charge=3]    ← 独立的交互上下文
    ↓                    ↓
[Spectrum A]         [Spectrum B]
         ↘           ↙
      [汇聚: 比较表格]                    ← Aggregator 节点求交/并/差集
```

## Capabilities

### New Capabilities

- **`state-port-system`**: 状态端口与交互连线
  - 三端口模型（Data / State In / State Out）
  - 语义类型校验的连线规则
  - 用户通过画布连线定义交互规则

- **`compute-proxy`**: 后端计算代理
  - 交互式节点触发后端轻量 API 的能力
  - 碎片离子匹配、修饰搜索等计算密集型操作
  - Loading 状态管理与结果回填

- **`state-bus`**: 状态总线
  - 中心化的状态分发与校验
  - 循环依赖检测
  - 多分支上下文隔离

- **`atomic-viewer-components`**: 原子化可视化组件
  - 通用 ScatterPlotNode（可配置轴映射）
  - 通用 SpectrumNode（支持标注覆盖层）
  - 通用 TableNode（支持列级交互筛选）
  - FilterNode（纯逻辑，无 UI 占用画布空间）

### Modified Capabilities

- **`interactive-visualization-nodes`**: 重构现有 3 个 Viewer 为原子化架构
  - FeatureMapViewer → ScatterPlotNode + 配置预设
  - SpectrumViewer → SpectrumNode + AnnotationOverlay
  - TableViewer → TableNode + ColumnFilter

- **`node-state-management`**: Store 升级为 State Bus
  - 增加状态广播与订阅机制
  - 增加循环依赖检测
  - 增加 Compute Proxy 的异步状态管理

- **`workflow-execution`**: 执行引擎适配
  - 识别 State Port 连线（执行时跳过，纯前端处理）
  - Compute Proxy 节点的执行路径

## Impact

### 前端代码（新增）
- `src/types/state-ports.ts` — 状态端口与语义类型定义
- `src/stores/state-bus.ts` — 状态总线 Store（替代/增强 visualization Store）
- `src/services/compute-proxy.ts` — 后端计算代理客户端
- `src/components/nodes/ScatterPlotNode.vue` — 原子化散点图节点
- `src/components/nodes/SpectrumNode.vue` — 原子化质谱图节点
- `src/components/nodes/TableNode.vue` — 原子化表格节点
- `src/components/nodes/FilterNode.vue` — 过滤器节点
- `src/components/overlays/AnnotationOverlay.vue` — 标注覆盖层

### 前端代码（修改）
- `src/types/workflow.ts` — 扩展 `PortDefinition` 和 `ConnectionDefinition` 支持状态端口
- `src/types/visualization.ts` — 增加语义类型定义
- `src/stores/workflow.ts` — 连线校验逻辑，区分 data/state 连线
- `src/stores/visualization.ts` — 升级为 State Bus 模式
- `src/components/workflow/VueFlowCanvas.vue` — 注册新的节点类型，渲染状态连线

### 后端代码（新增）
- `app/api/compute_proxy.py` — 计算代理 API 路由
- `app/services/fragment_matcher.py` — 碎片离子匹配服务
- `app/services/modification_matcher.py` — 修饰库匹配服务

### 后端代码（修改）
- `config/tool-schema.json` — 增加 `interactivity` 和 `statePorts` 定义
- `app/models/schemas.py` — 扩展 `ToolPort` 支持 `isInteractionPort` 和 `semanticType`
- `app/core/engine/` — FlowEngine 识别 state 连线并跳过

### 配置文件（新增/修改）
- `config/tools/scatter_plot.json` — 通用散点图工具定义
- `config/tools/spectrum_viewer.json` — 修改为原子化架构
- `config/tools/table_viewer.json` — 修改为原子化架构
- `config/tools/filter_node.json` — 过滤器节点工具定义

### 依赖关系
- **依赖** `interactive-visualization` change（基础可视化节点和 Store）
- **依赖** `backend-workspace-access`（数据访问 API）
- 为后续 MS2 深度分析、修饰库搜索、XIC 图表提供交互基座

### 性能考虑
- State Bus 使用 `shallowRef` 和精细化 `watch` 避免不必要的重渲染
- Compute Proxy 请求结果缓存，相同参数不重复请求
- 多分支工作流使用 Barrier 机制确保聚合节点在所有上游就绪后才渲染
