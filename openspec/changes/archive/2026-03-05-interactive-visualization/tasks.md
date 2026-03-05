## 1. 前端依赖安装

- [x] 1.1 在前端项目中安装 ECharts 及 Vue ECharts 适配器（`echarts` + `vue-echarts`）
- [x] 1.2 在前端项目中安装 AG Grid Community（`ag-grid-community` + `ag-grid-vue3`）

## 2. 工具定义（后端配置）

- [x] 2.1 更新 `config/tools/featuremap_viewer.json`：添加输出端口 `dataType: "selection"`
- [x] 2.2 创建 `config/tools/spectrum_viewer.json`：`executionMode: "interactive"`，`visualization.type: "spectrum"`，输入端口接受 `msalign/tsv`，输出端口 `dataType: "selection"`
- [x] 2.3 更新 `config/tools/table_viewer.json`：添加输出端口 `dataType: "selection"`

## 3. 后端执行引擎适配

- [x] 3.1 在 `app/services/workflow_service.py` 的 `build_task_spec()` 中，检测 `tool_info.get("executionMode") == "interactive"` 时返回 `None` 跳过该节点
- [x] 3.2 在 `execute_fn` 中处理 `None` TaskSpec：跳过执行，调用 `on_node_state(nid, "skipped")`
- [x] 3.3 在 `_resolve_input_paths` 中处理 interactive 节点的下游输入解析：穿越 interactive 节点找到更上游的真实文件输出

## 4. 前端类型定义

- [x] 4.1 在 `src/stores/workflow.ts` 中扩展 `NodeDefinition`，新增 `executionMode?: string` 和 `visualizationConfig?: { type: string; config?: Record<string, unknown> }` 字段
- [x] 4.2 创建 `src/types/visualization.ts`：定义 `TableData`, `ColumnDef`, `SelectionState`, `BrushRegion`, `FilterDef`, `DataSourceType`, `LoadingState` 等接口

## 5. Visualization Pinia Store

- [x] 5.1 创建 `src/stores/visualization.ts`：实现 `nodeData` Map、`nodeSelections` Map、`loadingStates` Map
- [x] 5.2 实现 `loadNodeData(nodeId, executionId, upstreamNodeId)` action：调用 P1 API，缓存结果
- [x] 5.3 实现 `updateSelection(nodeId, selection)` action：更新选择状态，触发 Vue 响应式更新
- [x] 5.4 实现 `clearAll()` action：清空所有缓存数据（工作流重新执行时调用）

## 6. 连接解析器

- [x] 6.1 创建 `src/services/workflow-connector.ts`：实现 `resolveNodeInputSource(nodeId, nodes, connections, tools)` 函数
- [x] 6.2 函数返回 `{ type: "file", sourceNodeId }` 或 `{ type: "state", sourceNodeId }` 或 `{ type: "none" }`
- [x] 6.3 判断逻辑：上游节点 `executionMode === "interactive"` → state 类型；否则 → file 类型

## 7. 交互式节点容器

- [x] 7.1 创建 `src/components/visualization/InteractiveNode.vue`：通用交互式节点容器，处理 loading/error/ready 状态，根据 `visualization.type` 动态渲染对应 Viewer
- [x] 7.2 容器在挂载时调用连接解析器，确定数据来源类型
- [x] 7.3 file 类型：调用 `visualization store.loadNodeData()`；state 类型：watch `nodeSelections[sourceNodeId]`
- [x] 7.4 在 `src/components/workflow/VueFlowCanvas.vue` 的 `nodeTypes` 中注册 `interactive: markRaw(InteractiveNode)`

## 8. FeatureMap Viewer 组件

- [x] 8.1 创建 `src/components/visualization/FeatureMapViewer.vue`：接受 `TableData` prop，使用 ECharts 渲染 RT vs Mass 散点图
- [x] 8.2 实现 TopN 渲染筛选：按 Intensity 排序，只渲染前 N 个点（通过 slider 调节 N）
- [x] 8.3 实现 ECharts `brush` 框选：监听 `brushEnd` 事件，提取框内数据点索引，调用 `updateSelection()`
- [x] 8.4 实现 RT/Mass/Intensity 范围筛选 UI（slider 或 input），更新 `SelectionState.filterCriteria`

## 9. Spectrum Viewer 组件

- [x] 9.1 创建 `src/components/visualization/SpectrumViewer.vue`：接受 `TableData` prop 和可选 `upstreamSelection` prop
- [x] 9.2 使用 ECharts 渲染 m/z vs Intensity 条形图/线图
- [x] 9.3 当 `upstreamSelection` 变化时，过滤数据并重新渲染
- [x] 9.4 实现峰选择：点击/框选峰后调用 `updateSelection()`

## 10. Table Viewer 组件

- [x] 10.1 创建 `src/components/visualization/TableViewer.vue`：接受 `TableData` prop，使用 AG Grid 渲染
- [x] 10.2 配置 AG Grid：启用虚拟滚动、列过滤、多行选择
- [x] 10.3 监听 AG Grid `selectionChanged` 事件，调用 `updateSelection()`
- [x] 10.4 实现前端导出：CSV 导出（AG Grid 内置 API）和 Excel 导出（`xlsx` 库）

## 11. 最新执行数据自动绑定

- [x] 11.1 在 `src/services/api/workspace-data.ts`（P1 产出）中确认 `getLatestExecution(workflowId)` API 已实现
- [x] 11.2 在 `InteractiveNode.vue` 挂载时，若当前无 executionId 上下文，调用 `getLatestExecution()` 获取最近执行 ID 用于数据加载
