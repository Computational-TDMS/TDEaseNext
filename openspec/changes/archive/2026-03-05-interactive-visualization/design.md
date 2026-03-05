## Context

当前前端使用 VueFlow 构建工作流编辑器，节点通过 `ToolNode.vue` 统一渲染，所有节点都是"处理节点"——用户配置参数后提交后端执行。前端没有任何数据展示或交互能力。

现有前端架构：
- **Pinia Store** (`workflow.ts`)：管理 `NodeDefinition[]` 和 `ConnectionDefinition[]`
- **VueFlowCanvas.vue**：渲染 VueFlow 画布，通过 `nodeTypes` 注册节点组件
- **ToolNode.vue**：所有节点的统一渲染组件（展示端口 + 参数面板入口）

后端已具备：
- 工具定义 schema 支持 `executionMode: "interactive"` 枚举值
- `visualization` 配置块（`type`, `dataSource`, `columns`, `config`）
- P1 (`backend-workspace-access`) 提供节点数据访问 API

前端核心依赖：
- Vue 3 + Pinia + VueFlow
- Element Plus（UI 库）
- 待引入：可视化渲染库

## Goals / Non-Goals

**Goals:**

1. 实现三种交互式可视化节点（FeatureMap、Spectrum、Table），在 VueFlow 画布中与处理节点共存
2. 建立前端数据缓存层（visualization Store），一次加载、本地交互
3. 实现节点间状态传递机制，交互式节点之间通过前端状态联动
4. 后端执行引擎跳过 `executionMode: "interactive"` 的节点
5. 连接解析器自动判断上游数据源类型（文件 vs 状态）

**Non-Goals:**

- 不实现实时协作（多用户同时编辑）
- 不实现 3D 可视化
- 不实现自定义可视化插件系统（仅内置三种类型）
- 不处理超大数据集的 LOD（Level of Detail）分层渲染——TopN 前端渲染筛选足够
- 不实现"交互式节点 → 处理节点"的自动状态转文件（第一阶段仅做交互式节点间联动）

## Decisions

### Decision 1: 可视化渲染库选择

**选择**：FeatureMap/Spectrum 使用 **echart**，Table 使用 **AG Grid Community**

**替代方案**：
- D3.js：灵活但需要大量手写代码，开发成本高
- Chart.js：不适合大数据量散点图

**理由**：
- ECharts 散点图支持 10 万级数据点渲染（通过 `large: true` 模式），框选 API 原生支持（`brush` 组件）
- ECharts 体积 ~800KB（可 tree-shake），Vue 集成成熟（`vue-echarts`）
- AG Grid Community 免费，支持虚拟滚动、列过滤、排序，是 Table 场景的标准选择
- Spectrum 图（m/z vs Intensity 柱状/线图）ECharts 直接支持

### Decision 2: 交互式节点组件架构

**选择**：`InteractiveNode.vue` 容器 + 具体可视化组件的组合模式

```
VueFlowCanvas
  └── nodeTypes: { interactive: InteractiveNode }
        └── InteractiveNode.vue (通用容器)
              ├── 根据 visualization.type 动态渲染:
              │   ├── FeatureMapViewer.vue
              │   ├── SpectrumViewer.vue
              │   └── TableViewer.vue
              ├── 节点头部（标题、状态指示）
              ├── 数据加载状态（loading / error / ready）
              └── 工具栏（导出、全屏、刷新）
```

**理由**：
- `InteractiveNode` 处理通用逻辑（数据加载、状态管理、连接解析）
- 具体 Viewer 只关心渲染和交互事件
- 新增可视化类型只需添加 Viewer 组件，不改容器逻辑
- VueFlow 的 `nodeTypes` 只需注册一个 `interactive` 类型

### Decision 3: 数据缓存与状态管理方案

**选择**：独立的 `visualization` Pinia Store

```typescript
// stores/visualization.ts
interface VisualizationState {
  nodeData: Map<string, TableData>           // nodeId → 全量数据
  nodeSelections: Map<string, SelectionState> // nodeId → 选择状态
  loadingStates: Map<string, LoadingState>   // nodeId → 加载状态
}

interface TableData {
  columns: ColumnDef[]
  rows: Record<string, unknown>[]
  totalRows: number
  sourceFile: string
}

interface SelectionState {
  selectedIndices: Set<number>   // 选中行的索引
  filterCriteria: FilterDef[]   // 活跃的筛选条件
  brushRegion: BrushRegion | null  // 框选区域（FeatureMap 用）
}
```

**替代方案**：在 `workflow` Store 中扩展节点数据

**理由**：
- 分离关注点：workflow Store 管理拓扑结构，visualization Store 管理运行时数据
- 数据量大：全量表格数据不应与轻量的节点定义混在一起
- 生命周期不同：数据缓存需要独立的加载/清理策略

### Decision 4: 节点间状态传递机制

**选择**：通过 visualization Store 的 watch + connections 解析实现

```
用户在 FeatureMap 框选
  ↓
visualization.updateSelection(nodeId, newSelection)
  ↓
Store 更新 nodeSelections[nodeId]
  ↓
下游节点（Spectrum）watch nodeSelections[upstreamNodeId]
  ↓
Spectrum 重新过滤数据并渲染
```

**连接解析逻辑**：
```typescript
function resolveNodeInput(nodeId: string): DataSource {
  const incomingEdges = connections.filter(c => c.target.nodeId === nodeId)
  for (const edge of incomingEdges) {
    const sourceNode = nodes.find(n => n.id === edge.source.nodeId)
    if (sourceNode.type === 'interactive') {
      return { type: 'state', sourceNodeId: edge.source.nodeId }
    } else {
      return { type: 'file', executionId, nodeId: edge.source.nodeId }
    }
  }
}
```

**理由**：
- 利用 Vue 的响应式系统自动传播变更，无需手动事件总线
- 连接信息已在 `workflow` Store 中，不需要额外数据结构
- 下游节点通过 `computed` 自动获取上游数据子集

### Decision 5: 后端执行引擎适配

**选择**：在 FlowEngine 的 `output_check_fn` 和 `execute_fn` 中跳过 interactive 节点

**具体实现**：
- `workflow_service.py` 的 `build_task_spec()` 中，检查 `tool_info.get("executionMode") == "interactive"`，如果是则跳过
- FlowEngine 将 interactive 节点视为"已完成"（不产生 TaskSpec，直接标记为 completed）
- interactive 节点的下游处理节点照常执行，其输入来源回溯到更上游的处理节点输出

**理由**：
- 最小改动：不改 FlowEngine 核心调度逻辑，只在 task 构建层面过滤
- interactive 节点在执行图中是"透传"的——下游节点穿越它找到真实的文件来源

### Decision 6: VueFlow 节点类型注册

**选择**：在 `VueFlowCanvas.vue` 的 `nodeTypes` 中添加 `interactive` 类型

```typescript
const nodeTypes = {
  tool: markRaw(ToolNode),
  interactive: markRaw(InteractiveNode),
}
```

前端根据工具定义的 `executionMode` 决定节点渲染为 `tool` 还是 `interactive` 类型。

**理由**：
- VueFlow 原生支持多种 nodeType，添加新类型是标准做法
- 不侵入现有 ToolNode 代码

## Risks / Trade-offs

### [Risk] ECharts 大数据量散点图渲染卡顿
- **场景**：FeatureMap 10 万点全部渲染
- **缓解**：ECharts `large: true` 模式 + TopN 前端渲染筛选（用户可调 N 值），数据仍全量保留在内存中

### [Risk] 全量数据占用浏览器内存
- **场景**：同时打开多个交互式节点，每个持有数 MB 数据
- **缓解**：非活跃节点的数据可延迟加载/释放；典型工作流中交互节点不超过 3-5 个

### [Risk] 交互式节点 → 处理节点的状态转文件
- **场景**：用户在 FeatureMap 筛选后想执行下游处理节点
- **缓解**：第一阶段标记为 Non-Goal，暂不实现自动转文件；用户需手动导出再配置

### [Risk] 前端数据格式与后端不一致
- **场景**：P1 返回的 `columns/rows` 格式与 Viewer 组件期望不一致
- **缓解**：P1 的响应格式在 design 中已标准化，前端 TypeScript 接口直接对应；visualization Store 做一层适配

### [Risk] VueFlow 节点尺寸与交互式内容冲突
- **场景**：交互式节点需要较大画布（如 FeatureMap），但 VueFlow 节点默认较小
- **缓解**：InteractiveNode 支持展开/收起模式——收起时显示缩略状态，展开时显示完整可视化；或支持弹出独立面板
