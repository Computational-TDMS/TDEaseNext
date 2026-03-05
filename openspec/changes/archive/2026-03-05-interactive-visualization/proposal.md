# Proposal: Interactive Data Visualization Nodes

## Why

用户需要对质谱数据进行交互式分析和筛选，而非仅查看静态结果。当前系统虽然能够处理数据并生成文件，但缺乏交互式可视化能力，导致用户无法：

1. **可视化探索数据**：无法直观查看 FeatureMap（质谱特征分布）和 Spectrum（质谱图）
2. **交互式筛选**：无法通过框选、点击等方式选择感兴趣的数据子集
3. **多节点联动**：无法在一个节点中选择数据并传递到下游节点进行进一步分析
4. **快速迭代分析**：每次筛选都需要重新执行后端处理，效率低下

此变更引入前端交互式可视化节点，将分析重心从"处理"转移到"交互"，让用户能够：
- 节点激活时一次性全量加载数据到前端，后续交互零延迟
- 通过可视化界面框选、筛选数据
- 节点间传递选择状态（纯前端状态流转，不触发后端）
- 仅在用户确认后执行下游后端计算

## What Changes

### 核心架构：数据加载一次，交互全本地

```
节点激活 → 一次性 API 加载全量数据 → 缓存到前端 Store
                                        ↓
                            框选 / 筛选 / 渲染 → 全本地计算
                            下游节点联动 → Store 状态传播
                            ↑ 零延迟
```

所有交互操作（框选、过滤、TopN 渲染、节点状态联动）在前端完成，不请求后端。

### 交互式节点定义

1. **FeatureMap Viewer 节点**
   - 可视化：质谱特征分布散点图（RT vs Mass, 点大小/颜色映射 Intensity）
   - 交互：框选区域、点击数据点
   - 筛选：TopN（前端渲染筛选，数据仍全量持有）、强度范围、RT/Mass 范围
   - 输出：选定特征的状态（传递给下游节点）

2. **Spectrum Viewer 节点**
   - 可视化：质谱图（m/z vs Intensity）
   - 数据来源：由 VueFlow 连接决定（连接什么格式的文件就读什么）
   - 交互：框选峰、点击峰
   - 输出：选定峰的状态

3. **Table Viewer 节点**
   - 可视化：ag-grid 高性能表格
   - 交互：排序、列过滤、搜索、行选择
   - 功能：前端直接导出 CSV/Excel
   - 输出：选定行的状态

### 节点连接与数据流

**核心设计**：交互式节点之间传递**状态**而非**文件**

| 连接类型 | 传递内容 | 时机 |
|----------|---------|------|
| 处理节点 → 交互式节点 | 文件（通过 P1 的 node-data-access API） | 节点激活时一次性加载 |
| 交互式节点 → 交互式节点 | 前端选择状态 | 用户操作后实时传播 |
| 交互式节点 → 处理节点 | 选择状态→临时文件（执行时） | 用户触发执行时 |

数据来源由 VueFlow 连接决定，连接解析器分析上游节点类型和端口来判断是加载文件还是订阅状态。

### 前端状态管理

- **`visualization` Store**（Pinia）：管理节点数据和选择状态
  - `nodeData`: Map<nodeId, TableData> — 全量数据缓存
  - `nodeSelections`: Map<nodeId, SelectionState> — 用户选择状态
  - watch 机制自动通知下游节点重新渲染

- **连接解析器**：
  - 分析 VueFlow connections 判断数据源类型（file vs state）
  - 构建节点的输入数据源映射

### 工具定义

新增交互式工具配置（`executionMode: "interactive"`）：
- `config/tools/featuremap_viewer.json`
- `config/tools/spectrum_viewer.json`
- `config/tools/table_viewer.json`

交互式工具在后端执行时被跳过（`executionMode === "interactive"` 的节点不产生 TaskSpec）。

## Capabilities

### New Capabilities

- **`interactive-visualization-nodes`**: 交互式可视化节点
  - 前端交互式可视化组件（FeatureMap、Spectrum、Table）
  - 节点间状态传递机制
  - 用户交互事件处理（框选、点击、筛选）
  - 数据一次性加载到前端缓存

- **`node-state-management`**: 节点状态管理
  - Pinia Store 管理节点数据和选择状态
  - 连接解析和数据源类型判断
  - 下游节点自动更新通知

### Modified Capabilities

- **`workflow-execution`**: 扩展执行引擎以支持交互式节点
  - `executionMode: "interactive"` 的节点在执行时跳过
  - 交互式节点 → 处理节点的连接：执行时从前端状态生成临时输入文件

## Impact

### 前端代码（新增）
- `src/stores/visualization.ts` — 可视化数据管理 Store
- `src/services/workflow-connector.ts` — 连接解析器
- `src/components/visualization/FeatureMapViewer.vue` — FeatureMap 组件
- `src/components/visualization/SpectrumViewer.vue` — Spectrum 组件
- `src/components/visualization/TableViewer.vue` — Table 组件
- `src/components/visualization/InteractiveNode.vue` — 通用交互式节点容器

### 前端代码（修改）
- `src/stores/workflow.ts` — 扩展 NodeDefinition 支持交互式节点
- `src/components/workflow/VueFlowCanvas.vue` — 注册交互式节点类型到 nodeTypes

### 后端代码（新增）
- `config/tools/featuremap_viewer.json` — 工具定义
- `config/tools/spectrum_viewer.json` — 工具定义
- `config/tools/table_viewer.json` — 工具定义

### 后端代码（修改）
- `app/services/workflow_service.py` — 执行时跳过 interactive 节点
- `app/core/engine/` — FlowEngine 识别 interactive executionMode

### 依赖关系
- **依赖** `backend-workspace-access`（数据访问 API，用于一次性全量加载数据）
- 为后续高级分析节点（如修饰库搜索）提供交互式前端

### 性能考虑
- 数据量级评估（基于实际文件）：
  - `.feature` 文件 ~6500 行 ≈ 3-5MB → 秒级加载
  - `.msalign` 文件 ~10000 条 ≈ 20-50MB → 数秒
  - Protein 结果表 ~500 行 ≈ 几百KB → 极快
- FeatureMap 渲染筛选（TopN）在前端完成，数据仍全量持有
- 使用 gzip 压缩传输减少网络时间
