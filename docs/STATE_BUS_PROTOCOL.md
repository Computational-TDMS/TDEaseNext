# StateBus 协议文档

**版本**: 1.0
**更新日期**: 2025-03-05

## 概述

**StateBus** 是 TDEase 前端的事件总线，用于在交互式可视化节点之间传递**状态事件**（如选择事件）。

### 核心功能

- ✅ **事件发布/订阅**：节点可发布和订阅状态事件
- ✅ **基于边的路由**：只向有状态边连接的节点发送事件
- ✅ **类型验证**：验证事件类型兼容性
- ✅ **循环检测**：防止状态循环引用
- ✅ **事件日志**：调试和问题排查

---

## 事件类型

### state/selection_ids

**描述**: 行索引选择事件

**用途**:
- FeatureMap 画刷选择 → Spectrum/ Table 过滤
- 表格行选择 → HTML Viewer 加载

**数据结构**:
```typescript
{
  semanticType: "state/selection_ids",
  data: Set<number> | { selectedIndices: number[] },
  timestamp: number,
  sourceNodeId: string,
  portId: string
}
```

**示例**:
```typescript
// FeatureMap 中用户画刷选择 3 个特征点
stateBus.dispatch('featuremap_1', 'selection_out', {
  semanticType: 'state/selection_ids',
  data: new Set([0, 5, 12]),  // 行索引
  timestamp: Date.now(),
  sourceNodeId: 'featuremap_1',
  portId: 'selection_out'
})
```

### state/viewport

**描述**: 视口范围事件

**用途**:
- 传递缩放/平移状态
- 同步多个查看器的视图范围

**数据结构**:
```typescript
{
  semanticType: "state/viewport",
  data: { xMin?: number, xMax?: number, yMin?: number, yMax?: number },
  timestamp: number,
  sourceNodeId: string
}
```

### state/annotation

**描述**: 注释事件

**用途**:
- Fragment Match 结果
- 用户添加的标记

**数据结构**:
```typescript
{
  semanticType: "state/annotation",
  data: { sequence: string, matches: Match[] },
  timestamp: number,
  sourceNodeId: string
}
```

---

## API 参考

### dispatch()

发布事件到 StateBus。

**签名**:
```typescript
dispatch(
  nodeId: string,
  portId: string,
  payload: StatePayload
): ValidationResult
```

**参数**:
- `nodeId`: 发布事件的节点 ID
- `portId`: 端口 ID（通常是 `selection_out`, `viewport_out` 等）
- `payload`: 事件负载

**返回**:
```typescript
{ ok: true } | { ok: false, reason: string }
```

**示例**:
```typescript
// 发布选择事件
const result = stateBus.dispatch('featuremap_1', 'selection_out', {
  semanticType: 'state/selection_ids',
  data: new Set([0, 5, 12]),
  timestamp: Date.now(),
  sourceNodeId: 'featuremap_1',
  portId: 'selection_out'
})

if (!result.ok) {
  console.error('Failed to dispatch:', result.reason)
}
```

### subscribe()

订阅 StateBus 事件。

**签名**:
```typescript
subscribe(
  targetNodeId: string,
  portId: string,
  callback: (payload, context) => void
): () => void
```

**参数**:
- `targetNodeId`: 订阅事件的节点 ID
- `portId`: 端口 ID（通常是 `selection_in`, `viewport_in` 等）
- `callback`: 事件回调函数

**返回**: 取消订阅函数

**示例**:
```typescript
// 在 SpectrumViewer 中订阅选择事件
const unsubscribe = stateBus.subscribe('spectrum_1', 'selection_in', (payload, context) => {
  if (payload.semanticType === 'state/selection_ids') {
    const selectedIndices = Array.from(payload.data as Set<number>)
    console.log('Selected rows:', selectedIndices)
    // 更新可视化
    updateSpectrumHighlight(selectedIndices)
  }
})

// 组件卸载时取消订阅
onUnmounted(() => {
  unsubscribe()
})
```

### validateConnection()

验证两个端口是否可以连接。

**签名**:
```typescript
validateConnection(
  sourcePort: PortDefinition,
  targetPort: PortDefinition
): ValidationResult
```

**参数**:
- `sourcePort`: 源端口定义
- `targetPort`: 目标端口定义

**返回**:
```typescript
{ ok: true } | { ok: false, reason: string }
```

**规则**:
1. 数据端口可以连接数据端口
2. `state-out` 只能连接 `state-in`
3. `semanticType` 必须匹配

### detectCycle()

检测状态边是否会产生循环。

**签名**:
```typescript
detectCycle(
  sourceNodeId: string,
  targetNodeId: string,
  connections: ConnectionDefinition[]
): boolean
```

**返回**: `true` 如果会形成循环

---

## 端口定义

### 端口属性

**端口类型** (`portKind`):
- `data`: 默认数据端口
- `state-in`: 状态输入端口
- `state-out`: 状态输出端口

**语义类型** (`semanticType`):
- `state/selection_ids`: 行索引选择
- `state/viewport`: 视口范围
- `state/annotation`: 注释

### 端口配置示例

**StateEdge 输出端口**:
```json
{
  "id": "selection_out",
  "name": "Selection Out",
  "portKind": "state-out",
  "semanticType": "state/selection_ids"
}
```

**StateEdge 输入端口**:
```json
{
  "id": "selection_in",
  "name": "Selection In",
  "portKind": "state-in",
  "semanticType": "state/selection_ids"
}
```

---

## 工作流集成

### 在工作流 JSON 中定义状态边

```json
{
  "edges": [
    {
      "id": "edge_featuremap_spectrum",
      "source": "featuremap_1",
      "sourceHandle": "selection_out",
      "target": "spectrum_1",
      "targetHandle": "selection_in",
      "connectionKind": "state",
      "semanticType": "state/selection_ids"
    }
  ]
}
```

### 节点定义中的端口声明

**FeatureMap Viewer** (发布者):
```json
{
  "id": "featuremap_viewer",
  "ports": {
    "inputs": [
      {
        "id": "feature_data",
        "name": "Feature Data",
        "dataType": "feature"
      }
    ],
    "outputs": [
      {
        "id": "selection_out",
        "name": "Selection Out",
        "portKind": "state-out",
        "semanticType": "state/selection_ids"
      }
    ]
  }
}
```

**Spectrum Viewer** (订阅者):
```json
{
  "id": "spectrum_viewer",
  "ports": {
    "inputs": [
      {
        "id": "spectrum_data",
        "name": "Spectrum Data",
        "dataType": "ms2"
      },
      {
        "id": "selection_in",
        "name": "Selection In",
        "portKind": "state-in",
        "semanticType": "state/selection_ids"
      }
    ],
    "outputs": []
  }
}
```

---

## 事件传播流程

### 1. 用户交互

```
用户在 FeatureMap 中画刷选择
    ↓
```

### 2. 事件发布

```typescript
// FeatureMapViewer.vue
const selectedRows = new Set([0, 5, 12])
stateBus.dispatch(props.id, 'selection_out', {
  semanticType: 'state/selection_ids',
  data: selectedRows,
  timestamp: Date.now(),
  sourceNodeId: props.id,
  portId: 'selection_out'
})
```

### 3. StateBus 路由

```typescript
// StateBus 内部
function dispatch(nodeId, portId, payload) {
  const sourceKey = `${nodeId}:${portId}`
  const targets = stateConnections.get(sourceKey) || []

  for (const targetKey of targets) {
    const callbacks = subscriptions.get(targetKey) || []
    callbacks.forEach(cb => cb(payload, context))
  }
}
```

### 4. 订阅者接收

```typescript
// SpectrumViewer.vue
stateBus.subscribe('spectrum_1', 'selection_in', (payload, context) => {
  if (payload.semanticType === 'state/selection_ids') {
    const rows = Array.from(payload.data as Set<number>)
    fetchAndFilterRows(rows)  // 查询并过滤数据
  }
})
```

---

## 性能优化

### 事件节流

StateBus 会自动对事件进行**节流**（100ms）：

```typescript
// 防止高频事件导致性能问题
const THROTTLE_MS = 100
```

**效果**:
- 用户快速拖拽画刷 → 最多每 100ms 发送一次事件
- 避免过度渲染和 API 调用

### 缓存策略

**数据缓存**:
- 节点数据缓存在 `VisualizationStore`
- 状态事件不缓存，但数据查询结果会缓存

**LRU 缓存**:
- Schema 查询缓存
- 行数据查询缓存
- TTL: 5 分钟

---

## 调试

### 启用 StateBus 日志

在浏览器控制台中：

```javascript
// 查看所有事件历史
stateBus.nodeStates

// 查看订阅关系
stateBus.subscriptions

// 查看连接关系
stateBus.stateConnections
```

### 常见问题

**问题 1**: 事件没有接收到

**调试步骤**:
1. 检查边是否为状态边（虚线橙边）
2. 检查端口类型：`state-out` → `state-in`
3. 检查 `semanticType` 是否匹配
4. 打开控制台查看事件日志

**问题 2**: 性能问题（太慢）

**调试步骤**:
1. 检查事件频率（是否节流）
2. 检查数据查询次数（是否使用缓存）
3. 减少订阅者数量

**问题 3**: 循环引用

**症状**: 页面卡死，CPU 100%

**解决**:
- StateBus 会自动检测并阻止循环
- 检查工作流是否有状态边形成的闭环

---

## 类型定义

```typescript
// State Payload
interface StatePayload {
  semanticType: string
  data: unknown
  timestamp?: number
  sourceNodeId?: string
  portId?: string
}

// Selection Event
interface SelectionEvent extends StatePayload {
  semanticType: 'state/selection_ids'
  data: Set<number> | { selectedIndices: number[]; filterCriteria?: Filter[] }
}

// Viewport Event
interface ViewportEvent extends StatePayload {
  semanticType: 'state/viewport'
  data: { xMin?: number; xMax?: number; yMin?: number; yMax?: number }
}

// Event Context
interface EventContext {
  sourceNodeId: string
  sourcePortId: string
  targetNodeId: string
  targetPortId: string
}

// Validation Result
type ValidationResult =
  | { ok: true }
  | { ok: false; reason: string }
```

---

## 最佳实践

### 1. 事件设计

**DO**: 使用细粒度事件
```typescript
// ✅ Good: 细粒度
{ semanticType: 'state/selection_ids', data: Set<number> }

// ❌ Bad: 粗粒度（传输大量数据）
{ semanticType: 'state/filtered_data', data: FullDataFrame }
```

**DO**: 传递引用（ID）而非数据本身
```typescript
// ✅ Good: 传递 ID
{ semanticType: 'state/selection_ids', data: Set([0, 5, 12]) }

// ❌ Bad: 传递完整行数据
{ semanticType: 'state/selected_rows', data: [{row1}, {row2}, ...] }
```

### 2. 订阅管理

**DO**: 总是在组件卸载时取消订阅
```typescript
onUnmounted(() => {
  unsubscribeHandlers.forEach(unsub => unsub())
})
```

**DO**: 使用 `watch` 监听状态变化
```typescript
watch(
  () => inboundSelection.value,
  (newSelection) => {
    if (newSelection) {
      updateVisualization(newSelection)
    }
  }
)
```

### 3. 错误处理

**DO**: 验证事件数据
```typescript
subscribe('node_1', 'selection_in', (payload) => {
  if (!validateSelectionPayload(payload)) {
    console.error('Invalid selection payload')
    return
  }
  // 处理事件...
})
```

---

## 扩展性

### 添加新的事件类型

**步骤**:

1. **定义语义类型**:
   ```typescript
   const CUSTOM_EVENT_TYPE = 'state/custom_event'
   ```

2. **发布事件**:
   ```typescript
   stateBus.dispatch('node_id', 'custom_out', {
     semanticType: CUSTOM_EVENT_TYPE,
     data: customData,
     timestamp: Date.now()
   })
   ```

3. **订阅事件**:
   ```typescript
   stateBus.subscribe('target_node', 'custom_in', (payload) => {
     if (payload.semanticType === CUSTOM_EVENT_TYPE) {
       // 处理事件
     }
   })
   ```

4. **更新工具定义**:
   ```json
   {
     "ports": {
       "outputs": [{
         "id": "custom_out",
         "portKind": "state-out",
         "semanticType": "state/custom_event"
       }]
     }
   }
   ```

---

## 参考资料

- [StateBus 源代码](../../TDEase-FrontEnd/src/stores/state-bus.ts)
- [交互式节点用户指南](INTERACTIVE_NODES.md)
- [测试覆盖率报告](TEST_COVERAGE_FINAL_REPORT.md)

---

*最后更新: 2025-03-05*
