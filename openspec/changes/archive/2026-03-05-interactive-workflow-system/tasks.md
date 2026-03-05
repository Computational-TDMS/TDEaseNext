## 1. 类型定义扩展（前端基础层）

- [x] 1.1 在 `src/types/workflow.ts` 中扩展 `PortDefinition`，新增 `portKind: 'data' | 'state-in' | 'state-out'`（默认 `'data'`）和 `semanticType?: string` 字段
- [x] 1.2 在 `src/types/workflow.ts` 中扩展 `ConnectionDefinition`，新增 `connectionKind?: 'data' | 'state'` 和 `semanticType?: string` 字段
- [x] 1.3 创建 `src/types/state-ports.ts`：定义 `SemanticType` 联合类型（`data/table`, `data/spectrum`, `state/selection_ids`, `state/range`, `state/viewport`, `state/annotation`, `state/sequence`）和 `StatePayload` 接口
- [x] 1.4 在 `src/types/visualization.ts` 中新增 `AnnotationData` 接口：`{ annotations: Array<{mz: number, type: string, error: number, matchedMz?: number}> }`

## 2. Tool Schema 扩展（后端配置）

- [x] 2.1 在 `config/tool-schema.json` 的 `ports.inputs[].properties` 和 `ports.outputs[].properties` 中新增 `portKind` 枚举字段和 `semanticType` 字符串字段
- [x] 2.2 在 `app/models/schemas.py` 的 `ToolPort` 中新增 `portKind: Optional[str] = "data"` 和 `semanticType: Optional[str] = None` 字段
- [x] 2.3 更新现有工具定义 JSON，为交互式工具的输出端口添加 `portKind: "state-out"` 和 `semanticType: "state/selection_ids"`
- [x] 2.4 创建新工具定义 `config/tools/filter_node.json`：`executionMode: "interactive"`，输入端口 `data_in`（`data`）+ `filter_in`（`state-in`），输出端口 `data_out`（`data`）

## 3. State Bus 核心（替代/增强现有 visualization Store）

- [x] 3.1 创建 `src/stores/state-bus.ts`：实现以 `Map<string, Map<string, StatePayload>>` 为核心的状态管理
- [x] 3.2 实现 `dispatch(nodeId, portId, payload)` action：验证 semanticType，存储状态，触发订阅
- [x] 3.3 实现 `subscribe(targetNodeId, portId, callback)` action：当上游状态变更时自动回调
- [x] 3.4 实现 `validateConnection(sourcePort, targetPort)` 函数：检查 portKind 兼容性 + semanticType 匹配
- [x] 3.5 实现 `detectCycle(sourceNodeId, targetNodeId, connections)` 函数：DFS 检测 state 连线中的循环依赖
- [x] 3.6 实现向后兼容层：`visualization.updateSelection()` 内部委托给 `stateBus.dispatch()`

## 4. 连线校验与渲染增强

- [x] 4.1 在 `src/stores/workflow.ts` 的 `addConnection()` 中接入 `stateBus.validateConnection()` 和 `stateBus.detectCycle()` 检查
- [x] 4.2 在 `VueFlowCanvas.vue` 中为 `state` 类型连线渲染虚线 + 橙色样式
- [x] 4.3 在 `VueFlowCanvas.vue` 的 `onConnect` handler 中展示连线拒绝原因（类型不兼容 / 循环依赖）
- [x] 4.4 在节点端口渲染中区分 data/state-in/state-out 的视觉样式（形状或颜色）

## 5. Compute Proxy 后端

- [x] 5.1 创建 `app/api/compute_proxy.py`：FastAPI 路由 `/api/compute-proxy/fragment-match` 和 `/api/compute-proxy/modification-search`
- [x] 5.2 创建 `app/services/fragment_matcher.py`：实现 b/y 离子理论 m/z 计算 + PPM 误差匹配
- [x] 5.3 创建 `app/services/modification_matcher.py`：实现修饰库（Unimod 格式）加载和 delta mass 匹配
- [x] 5.4 在 `main.py` 中注册 compute_proxy 路由

## 6. Compute Proxy 前端

- [x] 6.1 创建 `src/services/compute-proxy.ts`：封装后端 Compute Proxy API 调用（fragment-match, modification-search）
- [x] 6.2 实现请求缓存逻辑：基于参数哈希，5 分钟 TTL
- [x] 6.3 实现 State Bus 集成：Compute Proxy 返回结果后自动 `dispatch` 到对应节点的 `state/annotation` 端口

## 7. 原子化 Widget 组件

- [x] 7.1 从现有 `FeatureMapViewer.vue` 提炼 `src/components/widgets/ScatterPlotWidget.vue`：接收 `data` + `axisMapping` + `selectionState` props，可配置任意列映射
- [x] 7.2 从现有 `SpectrumViewer.vue` 提炼 `src/components/widgets/SpectrumWidget.vue`：接收 `data` + `selectionState` props
- [x] 7.3 从现有 `TableViewer.vue` 提炼 `src/components/widgets/TableWidget.vue`：接收 `data` + `selectionState` props
- [x] 7.4 创建 `src/components/widgets/AnnotationOverlay.vue`：接收 `annotationData` prop，在 ECharts 图表坐标系上渲染标注标签
- [x] 7.5 创建 `src/components/widgets/FilterPanel.vue`：通用过滤面板，发出 `state/range` 或 `state/selection_ids` 更新

## 8. InteractiveNode 容器增强

- [x] 8.1 修改 `InteractiveNode.vue`：支持 `visualization.components` 数组配置（多 Widget 组合）
- [x] 8.2 容器在挂载时注册 State Bus 订阅：根据 VueFlow connections 中的 state 连线自动 subscribe
- [x] 8.3 容器在卸载时清理 State Bus 订阅
- [x] 8.4 容器将所有 Widget 的交互事件统一代理为 `stateBus.dispatch()` 调用

## 9. FilterNode 节点

- [x] 9.1 创建 `src/components/nodes/FilterNode.vue`：紧凑型节点（小图标 + 标签 + 过滤计数 badge）
- [x] 9.2 实现 data-in + state-in → filtered data-out 的实时过滤逻辑
- [x] 9.3 在 VueFlowCanvas 的 `nodeTypes` 中注册 `filter` 类型

## 10. 端到端集成测试

- [x] 10.1 验证场景：FeatureMap 框选 → state 连线 → Spectrum 自动过滤显示
- [x] 10.2 验证场景：Spectrum 选峰 → Compute Proxy fragment-match → AnnotationOverlay 标注
- [x] 10.3 验证场景：多分支并行探索（Charge 2 / Charge 3 分别框选，互不干扰）
- [x] 10.4 验证场景：不兼容类型连线被画布阻止
- [x] 10.5 验证场景：循环依赖连线被画布阻止
- [x] 10.6 验证向后兼容：现有工具定义（无 portKind）仍正常工作
