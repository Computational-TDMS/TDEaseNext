// 节点类型判断修复方案

// 问题 1: 节点类型判断逻辑需要优先检查 executionMode
// 当前逻辑（有问题）:
// if (node.executionMode === 'interactive' || [...].includes(node.type))
// 这个条件会在 executionMode 为 interactive 时进入，但后续的 if-else 链可能覆盖

// 修复后逻辑（正确）:
const nodes = computed<Node<any, any, string>[]>(() => workflowStore.nodes.map((node) => {
  // Determine node type based on executionMode
  let nodeType = node.type

  // Debug logging
  console.log(`[VueFlowCanvas] Processing node ${node.id}:`, {
    type: node.type,
    executionMode: node.executionMode,
    label: node.displayProperties?.label || node.data?.label
  })

  // Priority 1: Check executionMode first
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

  // ... rest of the mapping logic
}))

// 问题 2: workflow-connector.ts 需要优先选择数据连接
// 当前逻辑只处理第一个连接，但交互式节点有多个输入（数据 + 状态）

// 修复 resolveNodeInputSource 函数
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
