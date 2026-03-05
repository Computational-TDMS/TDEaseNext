## Context

当前项目已通过 `interactive-visualization` change 完成了基础交互式可视化节点的第一阶段：
- **三种 Viewer**：FeatureMapViewer、SpectrumViewer、TableViewer
- **Visualization Store**（Pinia）：管理 `nodeData`、`nodeSelections`、`loadingStates`
- **连接解析器**：区分 `file` 和 `state` 数据源
- **后端适配**：`executionMode: "interactive"` 的节点在执行时跳过

现有系统的核心局限：
1. 每个 Viewer 是巨石组件，渲染/过滤/选择/交互逻辑混在一起
2. 节点间仅能传递 `SelectionState`（选中索引集合），无法表达丰富的交互语义
3. 纯前端状态流无法集成需要后端算力的交互（碎片匹配、修饰搜索）
4. 用户无法自由组装交互规则，只能使用开发者预设的联动

前端核心依赖：
- Vue 3 + Pinia + VueFlow + ECharts + AG Grid（已引入）
- Element Plus（UI 库）

## Goals / Non-Goals

**Goals:**

1. 引入三端口模型（Data Port / State In / State Out），让用户通过连线定义交互规则
2. 建立语义类型系统，画布自动校验端口兼容性
3. 升级 `visualization` Store 为 State Bus，支持中心化状态分发、循环检测、上下文隔离
4. 实现 Compute Proxy 机制，交互式节点可触发后端轻量 API 进行即时计算
5. 重构现有 Viewer 为原子化组件架构，支持组合和扩展
6. 支持多分支并行工作流中的状态隔离与聚合

**Non-Goals:**

- 不拆除现有 Viewer 组件；基于现有组件渐进式重构
- 不实现可视化插件的热加载/社区分发系统
- 不实现跨 Tab/跨窗口的协同交互
- 不实现 3D 可视化或 VR 数据探索
- 不实现自动布局（Auto-layout）算法

## Decisions

### Decision 1: 三端口模型与端口分类

**选择**：扩展现有 `PortDefinition`，新增 `portKind` 字段区分三类端口

```typescript
// types/workflow.ts 扩展
export interface PortDefinition {
  id: string
  name: string
  dataType: DataType
  required: boolean
  description?: string
  portKind: 'data' | 'state-in' | 'state-out'  // NEW
  semanticType?: string                          // NEW: e.g. 'state/selection_ids'
}
```

**连线规则**：
- `data` → `data`：传递文件路径/表格数据（已有行为）
- `state-out` → `state-in`：前端实时传递交互状态
- `state-out` → `data`：❌ 类型不兼容，画布阻止连接
- `data` → `state-in`：❌ 类型不兼容

**替代方案**：用完全独立的连线类型（不共享 VueFlow edges）
**理由**：复用 VueFlow 的连线基础设施，只需在连线验证层增加 `portKind` 检查，改动最小

### Decision 2: 语义类型系统

**选择**：在 `PortDefinition` 上增加 `semanticType` 字符串字段

```typescript
// 语义类型定义
type SemanticType =
  | 'data/table'              // 通用表格 (columns + rows)
  | 'data/spectrum'           // [mz, intensity] 数组
  | 'data/sequence'           // 氨基酸序列字符串
  | 'state/selection_ids'     // Set<number> 选中行索引
  | 'state/range'             // { column, min, max }
  | 'state/viewport'          // { xMin, xMax, yMin, yMax }
  | 'state/annotation'        // 标注数据数组
  | 'state/sequence'          // 序列字符串 (用于触发计算代理)
```

**连线校验**：`ConnectionDefinition` 创建时，比较 source 端口的 `semanticType` 和 target 端口可接受的类型列表。

**替代方案**：不做类型校验，运行时报错
**理由**：类型校验在连线时即刻反馈，防止用户连出无意义的拓扑

### Decision 3: State Bus 设计

**选择**：将现有 `visualization` Store 升级为 State Bus 模式

```typescript
// stores/state-bus.ts
interface StateBusState {
  nodeData: Map<string, NodeDataEntry>
  nodeStates: Map<string, Map<string, StatePayload>>  // nodeId → portId → payload
  loadingStates: Map<string, LoadingState>
  subscriptions: Map<string, StateSubscription[]>      // nodeId → 订阅列表
}

interface StatePayload {
  semanticType: string
  data: unknown   // 具体值由 semanticType 决定
  timestamp: number
}
```

**核心 API**：
- `dispatch(sourceNodeId, portId, payload)` — 发布状态更新
- `subscribe(targetNodeId, portId, callback)` — 订阅上游状态
- `validateConnection(sourcePort, targetPort)` — 校验连线兼容性
- `detectCycle(newConnection)` — 循环依赖检测

**循环检测**：在 `dispatch` 前运行 DFS，如果发现当前 dispatch 链中已包含 sourceNodeId，则拒绝并报错。

**替代方案**：保持现有的 props/emit 直连模式
**理由**：
- 中心化管理使循环检测成为可能
- 多分支隔离可通过总线的 context scope 实现
- 不影响已有的 `visualization` Store 接口，可渐进迁移

### Decision 4: Compute Proxy 机制

**选择**：新增后端 API 端点 + 前端代理服务

```
前端 State Bus dispatch (序列变更)
  ↓
ComputeProxy Service 拦截
  ↓
POST /api/compute-proxy/fragment-match
  Body: { sequence, spectrumData, ppmTolerance }
  ↓
后端 FragmentMatcher 计算
  ↓
Response: { annotations: [{mz, type, error}] }
  ↓
State Bus dispatch (annotation 数据)
  ↓
SpectrumNode AnnotationOverlay 渲染标签
```

**后端路由**：
- `POST /api/compute-proxy/fragment-match` — 碎片离子匹配
- `POST /api/compute-proxy/modification-search` — 修饰库搜索
- `POST /api/compute-proxy/ppm-filter` — PPM 误差过滤

**缓存策略**：相同参数的请求结果缓存 5 分钟，避免重复计算。

**替代方案**：在前端用 Web Worker 做计算
**理由**：
- 修饰库/序列数据库通常很大（Unimod 数十 MB），不适合前端持有
- 后端已有 Python 生态的生物信息学库，复用成本更低
- Web Worker 线程通信开销在大数据量时不可忽略

### Decision 5: 原子化组件架构

**选择**：保留 `InteractiveNode.vue` 容器，内部组件支持组合

```
InteractiveNode.vue (容器, 已存在)
  ├── 根据 visualization.type 和 visualization.components 渲染:
  │   ├── ScatterPlotWidget.vue    (从 FeatureMapViewer 提炼)
  │   ├── SpectrumWidget.vue       (从 SpectrumViewer 提炼)
  │   ├── TableWidget.vue          (从 TableViewer 提炼)
  │   ├── AnnotationOverlay.vue    (NEW: 标注覆盖层)
  │   └── FilterPanel.vue          (NEW: 通用过滤面板)
  ├── NodeHeader (标题+状态)
  └── NodeToolbar (导出+全屏+刷新)
```

**渲染策略**：
- 简单节点（如纯散点图）：`visualization.type = "scatter"` 直接渲染单个 Widget
- 复合节点（如带标注的谱图）：`visualization.components` 数组定义多个 Widget 的组合

**替代方案**：完全拆分为独立 VueFlow 节点（每个 Widget 一个节点）
**理由**：
- 散点图+过滤面板作为一个"逻辑节点"更符合用户心智
- 在同一节点内的组件共享 Data Context，通信无延迟
- 如果全拆，画布会变得极其拥挤

### Decision 6: 多分支状态隔离与聚合

**选择**：基于 VueFlow 拓扑计算自动推导 Context Scope

**隔离规则**：
- State Bus 在 `dispatch` 时只沿 connections 定义的路径传播
- 不存在连线的节点间，状态天然隔离
- 多分支的汇聚节点（接收多路 state-in）自动等待所有上游 ready

**聚合模式**：
- `Aggregator` 节点接收多路 `state/selection_ids`
- 内部提供交集/并集/差集运算
- 输出新的 `state/selection_ids`

**替代方案**：显式定义 Context Scope ID
**理由**：利用已有拓扑信息自动推导，用户无需感知"上下文"概念

### Decision 7: ConnectionDefinition 扩展

**选择**：在现有 `ConnectionDefinition` 上新增字段

```typescript
export interface ConnectionDefinition {
  id: string
  source: { nodeId: string; portId: string }
  target: { nodeId: string; portId: string }
  dataPath?: { s?: string; t?: string }
  connectionKind?: 'data' | 'state'     // NEW: 连线类型
  semanticType?: string                  // NEW: 传递的语义类型
}
```

**前端渲染**：
- `data` 连线：实线，使用当前样式
- `state` 连线：虚线，使用不同颜色（如橙色），表示前端实时联动

## Risks / Trade-offs

### [Risk] State Bus 循环检测的性能开销
- **场景**：大型工作流中每次 dispatch 都要 DFS
- **缓解**：缓存拓扑关系，仅在连线增删时重建；DFS 深度有限（典型工作流 ~20 节点）

### [Risk] Compute Proxy 延迟破坏交互体验
- **场景**：碎片匹配计算耗时 1-2 秒，用户感知到明显延迟
- **缓解**：显示 Loading Skeleton + 进度条；结果缓存避免重复计算；debounce 频繁触发

### [Risk] 现有 Viewer 重构引入 Regression
- **场景**：提炼 Widget 过程中破坏已有的框选/过滤功能
- **缓解**：渐进式重构——先增加 Widget 封装，保留旧 Viewer 作为兼容层，验证后再替换

### [Risk] 语义类型定义不完备
- **场景**：后续出现难以归类的新交互模式
- **缓解**：语义类型支持 `custom/<name>` 扩展命名空间，不做硬编码枚举

### [Risk] Tool Schema 变更的向后兼容
- **场景**：新增 `portKind` 和 `semanticType` 字段后，旧工具定义无法加载
- **缓解**：所有新字段设为 optional，默认值 `portKind: 'data'`；旧工具定义自动降级为纯 data 端口
