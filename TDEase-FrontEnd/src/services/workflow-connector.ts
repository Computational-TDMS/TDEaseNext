/**
 * Workflow Connector Service
 *
 * Resolves data source types for interactive nodes by analyzing VueFlow connections.
 * Determines whether each node's data comes from a file (upstream processing node)
 * or from state (upstream interactive node).
 */

import type { ConnectionDefinition, NodeDefinition } from '@/stores/workflow'
import type { DataSource } from '@/types/visualization'

/**
 * Tool info interface (from tool registry)
 */
interface ToolInfo {
  executionMode?: string
  [key: string]: unknown
}

interface FileSourceResult {
  nodeId: string
  portId?: string
}

/**
 * Resolve node input source type
 *
 * @param nodeId - Target node ID
 * @param nodes - All nodes in the workflow
 * @param connections - All connections in the workflow
 * @param tools - Tool registry (tool_id -> tool_info mapping)
 * @returns Data source resolution result
 */
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

  console.log(
    `[WorkflowConnector] Node ${nodeId} - dataEdge: ${dataEdge?.id}, stateEdge: ${stateEdge?.id}`
  )

  // Use data edge if available, otherwise use first edge (for backward compatibility)
  const edge = dataEdge || incomingEdges[0]
  const sourceNodeId = edge.source.nodeId
  const sourcePortId = edge.source.portId

  console.log(`[WorkflowConnector] Node ${nodeId} - Using source port: ${sourcePortId}`)
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
    const fileSource = findOriginalFileSourceWithPort(
      sourceNodeId,
      nodes,
      connections,
      tools,
      new Set()
    )
    if (fileSource) {
      console.log(`[WorkflowConnector] Found file source: ${fileSource.nodeId}`)
      return {
        type: 'file',
        sourceNodeId: fileSource.nodeId,
        sourcePortId: fileSource.portId || sourcePortId,
      }
    }
    console.log(`[WorkflowConnector] No file source, using state: ${sourceNodeId}`)
    return { type: 'state', sourceNodeId }
  }

  // Source is a processing node - data comes from file
  console.log(`[WorkflowConnector] Source is processing node: ${sourceNodeId}`)
  return {
    type: 'file',
    sourceNodeId,
    sourcePortId,
  }
}

/**
 * Resolve the file source node ID for loading data into an interactive node.
 * Prefers data connections; when connected to interactive upstream, traverses to compute node.
 */
export function resolveNodeFileSourceForData(
  nodeId: string,
  nodes: NodeDefinition[],
  connections: ConnectionDefinition[],
  tools: Record<string, ToolInfo>
): string | null {
  const source = resolveNodeInputSource(nodeId, nodes, connections, tools)
  if (source.type === 'file') return source.sourceNodeId || null
  if (source.type === 'state') {
    return findOriginalFileSource(nodeId, nodes, connections, tools, new Set())
  }
  return null
}

/**
 * Find the original file source node for an interactive node
 *
 * Traverses upstream through interactive nodes to find the first
 * non-interactive (processing) node that produces actual output files.
 *
 * @param nodeId - Starting node ID (usually an interactive node)
 * @param nodes - All nodes in the workflow
 * @param connections - All connections in the workflow
 * @param tools - Tool registry
 * @returns The ID of the first processing node upstream, or null if none found
 */
export function findOriginalFileSource(
  nodeId: string,
  nodes: NodeDefinition[],
  connections: ConnectionDefinition[],
  tools: Record<string, ToolInfo>,
  visited: Set<string> = new Set()
): string | null {
  const result = findOriginalFileSourceWithPort(nodeId, nodes, connections, tools, visited)
  return result?.nodeId || null
}

function findOriginalFileSourceWithPort(
  nodeId: string,
  nodes: NodeDefinition[],
  connections: ConnectionDefinition[],
  tools: Record<string, ToolInfo>,
  visited: Set<string> = new Set()
): FileSourceResult | null {
  // Prevent infinite loops
  if (visited.has(nodeId)) {
    console.warn(`[WorkflowConnector] Circular dependency detected at node: ${nodeId}`)
    return null
  }
  visited.add(nodeId)

  // Find incoming connections
  const incomingEdges = connections.filter((conn) => conn.target.nodeId === nodeId)

  if (incomingEdges.length === 0) {
    return null
  }

  // Prioritize data connections; state connections are fallback only
  const sortedEdges = [...incomingEdges].sort((left, right) => {
    const leftRank = left.connectionKind === 'data' ? 0 : 1
    const rightRank = right.connectionKind === 'data' ? 0 : 1
    return leftRank - rightRank
  })

  for (const edge of sortedEdges) {
    const sourceNodeId = edge.source.nodeId
    const sourceNode = nodes.find((n) => n.id === sourceNodeId)
    if (!sourceNode) continue

    const toolId = (sourceNode as any).nodeConfig?.toolId || sourceNode.type
    const toolInfo = tools[toolId]
    if (!toolInfo) continue

    // If upstream is interactive, continue traversing
    if (toolInfo.executionMode === 'interactive') {
      const nested = findOriginalFileSourceWithPort(sourceNodeId, nodes, connections, tools, visited)
      if (nested) return nested
      continue
    }

    // Found the processing node and source output port
    return {
      nodeId: sourceNodeId,
      portId: edge.source.portId,
    }
  }

  return null
}

/**
 * Get all downstream nodes for a given node
 *
 * @param nodeId - Starting node ID
 * @param connections - All connections in the workflow
 * @returns Array of downstream node IDs
 */
export function getDownstreamNodes(nodeId: string, connections: ConnectionDefinition[]): string[] {
  const downstream = connections
    .filter((conn) => conn.source.nodeId === nodeId)
    .map((conn) => conn.target.nodeId)

  return downstream
}

/**
 * Check if a node has any interactive downstream nodes
 *
 * @param nodeId - Node ID to check
 * @param nodes - All nodes in the workflow
 * @param connections - All connections in the workflow
 * @param tools - Tool registry
 * @returns True if there are interactive nodes downstream
 */
export function hasInteractiveDownstream(
  nodeId: string,
  nodes: NodeDefinition[],
  connections: ConnectionDefinition[],
  tools: Record<string, ToolInfo>
): boolean {
  const downstream = getDownstreamNodes(nodeId, connections)

  for (const downstreamId of downstream) {
    const node = nodes.find((n) => n.id === downstreamId)
    if (!node) continue

    const toolInfo = tools[node.type]
    if (toolInfo?.executionMode === 'interactive') {
      return true
    }
  }

  return false
}

/**
 * Workflow connector service interface
 */
export const workflowConnectorService = {
  resolveNodeInputSource,
  resolveNodeFileSourceForData,
  findOriginalFileSource,
  getDownstreamNodes,
  hasInteractiveDownstream,
} as const
