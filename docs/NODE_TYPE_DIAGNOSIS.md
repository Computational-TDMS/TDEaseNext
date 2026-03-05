# 节点类型和数据加载问题诊断与修复

## 🚨 当前问题

1. **featuremap 接收数据后变成常规节点样式**
2. **spectrum 节点显示为交互式样式，但提示"输出文件未找到"**
3. **节点类型判断混乱**

## 🔍 问题根因分析

### 问题 1: 节点类型判断逻辑混乱

**当前代码 (VueFlowCanvas.vue:88-102)**:
```typescript
let nodeType = node.type
if (node.executionMode === 'interactive' || ['custom','input','process','output','tool','filter'].includes(node.type)) {
  if (node.type === 'filter') {
    nodeType = 'filter'
  } else if (node.executionMode === 'interactive') {
    nodeType = 'interactive'  // ← 这个条件永远不会执行！
  } else if (['custom','input','process','output','tool','filter'].includes(node.type)) {
    nodeType = node.type  // ← 会先执行这里
  } else {
    nodeType = 'tool'
  }
} else {
  nodeType = 'tool'
}
```

**问题**:
- 如果 `node.type = 'featuremap_viewer'`，它不在 `['custom','input','process','output','tool','filter']` 中
- 但是第一个条件 `node.executionMode === 'interactive'` 为 true
- 然后进入 if-else 链，但 `node.type === 'filter'` 为 false
- 然后检查 `node.executionMode === 'interactive'`，应该设置为 'interactive' ✅
- **但是**，如果条件判断顺序或者逻辑有变化，可能会导致问题

### 问题 2: workflow-connector 连接优先级

**当前代码 (workflow-connector.ts:36-44)**:
```typescript
const incomingEdges = connections.filter((conn) => conn.target.nodeId === nodeId)
// ...
// For simplicity, we only handle the first incoming connection
const edge = incomingEdges[0]  // ← 只处理第一个连接！
```

**问题**:
- `spectrum_2` 有两个输入连接：
  1. `topfd_1 → spectrum_2` (数据连接)
  2. `featuremap_2 → spectrum_2` (状态连接)
- 如果状态连接排在前面，会使用 `featuremap_2` 作为源
- 而 `featuremap_2` 是交互式节点，会继续向上查找
- 最终可能导致找不到数据源

## ✅ 修复方案

### 修复 1: 优化节点类型判断逻辑

**替换 VueFlowCanvas.vue 第 87-102 行为**:

```typescript
// 从 store 获取数据并转换为 Vue Flow 格式
const nodes = computed<Node<any, any, string>[]>(() => workflowStore.nodes.map((node) => {
  // Determine node type based on executionMode
  let nodeType = node.type

  // Debug logging
  console.log(`[VueFlowCanvas] Processing node ${node.id}:`, {
    type: node.type,
    executionMode: node.executionMode,
    label: node.displayProperties?.label || node.data?.label
  })

  // Priority 1: Check executionMode first (most important)
  if (node.executionMode === 'interactive') {
    nodeType = 'interactive'
    console.log(`[VueFlowCanvas] Node ${node.id} is interactive (by executionMode)`)
  }
  // Priority 2: Check for specific node types
  else if (node.type === 'filter') {
    nodeType = 'filter'
  }
  // Priority 3: Check for other known types
  else if (['custom', 'input', 'process', 'output', 'tool'].includes(node.type)) {
    nodeType = node.type
  }
  // Default to tool node
  else {
    nodeType = 'tool'
  }

  console.log(`[VueFlowCanvas] Node ${node.id} resolved to type: ${nodeType}`)

  const resolvedToolId =
    (node as any).nodeConfig?.toolId ||
    (node as any).data?.toolId ||
    (node as any).data?.type ||
    (node.type !== 'tool' ? node.type : null)

  return {
    id: node.id,
    type: nodeType,
    position: node.position,
    data: {
      nodeId: node.id,
      label: node.displayProperties?.label || node.data?.label || node.type,
      color: node.displayProperties?.color || node.data?.color || '#409eff',
      icon: node.displayProperties?.icon,
      executionMode: node.executionMode,
      toolId: typeof resolvedToolId === 'string' ? resolvedToolId : node.type,
      visualizationConfig: node.visualizationConfig,
      nodeConfig: {
        inputs: node.inputs.map((p) => ({
          id: p.id,
          name: p.name,
          type: (p as any).dataType || (p as any).type || 'file',
          required: (p as any).required === true,
          accept: Array.isArray((p as any).accept) ? (p as any).accept : undefined,
          dataType: (p as any).dataType,
          portKind: (p as any).portKind,
          semanticType: (p as any).semanticType
        })),
        outputs: node.outputs.map((p) => ({
          id: p.id,
          name: p.name,
          type: (p as any).dataType || (p as any).type || 'file',
          pattern: (p as any).pattern,
          provides: Array.isArray((p as any).provides) ? (p as any).provides : undefined,
          dataType: (p as any).dataType,
          portKind: (p as any).portKind,
          semanticType: (p as any).semanticType
        }))
      }
    },
    style: {
      backgroundColor: 'transparent',
      border: 'none',
      padding: '0',
      width: 'auto',
      height: 'auto'
    },
    draggable: true,
    selectable: true
  }
}))
```

### 修复 2: 优化数据源解析逻辑

**替换 workflow-connector.ts 第 29-83 行为**:

```typescript
export function resolveNodeInputSource(
  nodeId: string,
  nodes: NodeDefinition[],
  connections: ConnectionDefinition[],
  tools: Record<string, ToolInfo>
): DataSource {
  // Find incoming connections to this node
  const incomingEdges = connections.filter((conn) => conn.target.nodeId === nodeId)

  if (incomingEdges.length === 0) {
    console.log(`[WorkflowConnector] Node ${nodeId} has no incoming connections`)
    return { type: 'none' }
  }

  console.log(`[WorkflowConnector] Node ${nodeId} has ${incomingEdges.length} incoming connections`)

  // Priority: Data connections > State connections
  const dataEdge = incomingEdges.find(conn => conn.connectionKind === 'data')
  const stateEdge = incomingEdges.find(conn => conn.connectionKind === 'state')

  console.log(`[WorkflowConnector] Node ${nodeId} - dataEdge: ${dataEdge?.id}, stateEdge: ${stateEdge?.id}`)

  // Use data edge if available, otherwise use first edge (for backward compatibility)
  const edge = dataEdge || incomingEdges[0]
  const sourceNodeId = edge.source.nodeId

  console.log(`[WorkflowConnector] Node ${nodeId} - Using source: ${sourceNodeId}`)

  // Find the source node
  const sourceNode = nodes.find((n) => n.id === sourceNodeId)
  if (!sourceNode) {
    console.warn(`[WorkflowConnector] Source node not found: ${sourceNodeId}`)
    return { type: 'none' }
  }

  // Get tool info for the source node
  const toolId = (sourceNode as any).nodeConfig?.toolId || sourceNode.type
  const toolInfo = tools[toolId]

  if (!toolInfo) {
    console.warn(`[WorkflowConnector] Tool not found: ${toolId}`)
    return { type: 'none' }
  }

  console.log(`[WorkflowConnector] Source tool: ${toolId}, executionMode: ${toolInfo.executionMode}`)

  // Check if source node is interactive
  if (toolInfo.executionMode === 'interactive') {
    // Traverse to find original file source
    const fileSourceId = findOriginalFileSource(
      sourceNodeId,
      nodes,
      connections,
      tools,
      new Set()
    )
    if (fileSourceId) {
      console.log(`[WorkflowConnector] Found file source: ${fileSourceId}`)
      return { type: 'file', sourceNodeId: fileSourceId }
    }
    console.log(`[WorkflowConnector] No file source, using state: ${sourceNodeId}`)
    return { type: 'state', sourceNodeId }
  }

  // Source is a processing node - data comes from file
  console.log(`[WorkflowConnector] Source is processing node: ${sourceNodeId}`)
  return {
    type: 'file',
    sourceNodeId,
  }
}
```

## 🛠️ 手动修复步骤

### 步骤 1: 修复 VueFlowCanvas.vue

1. 打开 `TDEase-FrontEnd/src/components/workflow/VueFlowCanvas.vue`
2. 找到第 87-102 行（节点类型判断逻辑）
3. 替换为上面的"修复 1"代码

### 步骤 2: 修复 workflow-connector.ts

1. 打开 `TDEase-FrontEnd/src/services/workflow-connector.ts`
2. 找到 `resolveNodeInputSource` 函数（第 29-83 行）
3. 替换为上面的"修复 2"代码

### 步骤 3: 重启服务

```bash
# 重启前端
cd D:\Projects\TDEase-Backend\TDEase-FrontEnd
pnpm run dev

# 重启后端
cd D:\Projects\TDEase-Backend
python -m app.main
```

### 步骤 4: 验证修复

打开浏览器控制台（F12），查看日志：

**预期日志**:
```
[VueFlowCanvas] Processing node featuremap_2: {
  type: "featuremap_viewer",
  executionMode: "interactive",
  label: "TopFD FeatureMap Viewer"
}
[VueFlowCanvas] Node featuremap_2 is interactive (by executionMode)
[VueFlowCanvas] Node featuremap_2 resolved to type: interactive

[WorkflowConnector] Node spectrum_2 has 2 incoming connections
[WorkflowConnector] Node spectrum_2 - dataEdge: e_topfd_spectrum2, stateEdge: e_featuremap2_spectrum2_selection
[WorkflowConnector] Node spectrum_2 - Using source: topfd_1
[WorkflowConnector] Source tool: topfd, executionMode: native
[WorkflowConnector] Source is processing node: topfd_1
```

## 📋 检查清单

- [ ] VueFlowCanvas.vue 节点类型判断已修复
- [ ] workflow-connector.ts 数据源解析已修复
- [ ] 前端服务已重启
- [ ] 浏览器控制台显示正确的日志
- [ ] featuremap_2 显示为大的交互式面板
- [ ] spectrum_2 显示为交互式样式
- [ ] spectrum_2 能正确加载 topfd_1 的数据

## 🔧 如果问题仍然存在

1. **检查工作流文件**:
   ```bash
   grep -A3 '"id": "featuremap_2"' workflows/wf_test_full_fixed.json
   grep -A3 '"id": "spectrum_2"' workflows/wf_test_full_fixed.json
   ```
   确保都有 `"executionMode": "interactive"`

2. **检查连接顺序**:
   ```bash
   grep -A2 '"target": "spectrum_2"' workflows/wf_test_full_fixed.json
   ```
   确保数据连接 (`e_topfd_spectrum2`) 在状态连接之前

3. **查看详细日志**:
   - 浏览器控制台日志
   - 后端日志 (`logs/app.log`)

4. **检查工具定义**:
   ```bash
   grep "executionMode" config/tools/*.json
   ```
   确保交互式工具都有 `"executionMode": "interactive"`
