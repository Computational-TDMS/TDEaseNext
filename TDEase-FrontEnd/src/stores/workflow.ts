import { defineStore } from 'pinia'
import { useHistoryManager } from '@/composables/useHistoryManager'

export type Position = {
  x: number
  y: number
}

export interface NodeDefinition {
  id: string
  type: string
  position: Position
  data?: Record<string, unknown>
  displayProperties: {
    label?: string
    color?: string
    icon?: string
    width?: number
    height?: number
  }
  inputs: Array<{
    id: string
    name: string
    type: string
    required: boolean
    description?: string
    dataType?: string
    portKind?: 'data' | 'state-in' | 'state-out'
    semanticType?: string
  }>
  outputs: Array<{
    id: string
    name: string
    type: string
    required: boolean
    description?: string
    dataType?: string
    portKind?: 'data' | 'state-in' | 'state-out'
    semanticType?: string
  }>
  parameters?: Array<{
    id: string
    name: string
    type:
      | 'string'
      | 'number'
      | 'boolean'
      | 'select'
      | 'multiselect'
      | 'range'
      | 'int'
      | 'float'
      | 'slider'
      | 'radio'
      | 'checkbox'
    required: boolean
    default?: unknown
    description?: string
    options?: Array<{ label: string; value: unknown }>
  }>
  nodeConfig: Record<string, unknown>
  executionMode?: string  // 'interactive' | 'batch' | undefined
  visualizationConfig?: {
    type: string  // 'featuremap' | 'spectrum' | 'table'
    config?: Record<string, unknown>
  }
}

export interface ConnectionDefinition {
  id: string
  source: {
    nodeId: string
    portId: string
  }
  target: {
    nodeId: string
    portId: string
  }
  dataPath?: {
    s?: string
    t?: string
  }
  connectionKind?: 'data' | 'state'
  semanticType?: string
}

export interface WorkflowMetadata {
  id: string
  name: string
  version: string
  description?: string
  author?: string
  created: string
  modified: string
  tags?: string[]
  uuid?: string
  license?: string
  creator?: Array<Record<string, unknown>>
}

export interface WorkflowStepInput {
  source: string // Reference to step output (e.g., "step_name/output_name") or workflow input
}

export interface WorkflowStepOutput {
  outputSource?: string // Reference to step output (e.g., "step_name/output_name")
}

export interface WorkflowStep {
  id: string // Step ID (usually matches node ID)
  type: string // Step type: "tool", "data_input", "data_collection_input", "subworkflow", etc.
  tool_id?: string // Tool identifier for tool steps
  tool_state?: Record<string, unknown> // Tool parameter values
  inputs?: Record<string, unknown> // Step inputs mapping
  outputs?: Record<string, string> // Step outputs mapping
  position?: { x: number; y: number } // Step position in workflow
}

export interface WorkflowInput {
  id: string
  type: string // Usually "data"
  label?: string
}

export interface WorkflowOutput {
  id: string
  outputSource: string // Reference to step output (e.g., "step_name/output_name")
  label?: string
}

export interface WorkflowJSON {
  metadata: WorkflowMetadata
  format_version?: string // Galaxy format version, default "2.0"
  nodes: NodeDefinition[] // VueFlow UI nodes (for rendering)
  connections: ConnectionDefinition[] // VueFlow connections (for rendering)
  steps?: Record<string, WorkflowStep> // Galaxy format steps (for execution)
  inputs?: Record<string, WorkflowInput> // Galaxy format workflow inputs
  outputs?: Record<string, WorkflowOutput> // Galaxy format workflow outputs
  projectSettings: Record<string, unknown>
}

import { ref, computed } from 'vue'
import { useStateBusStore } from '@/stores/state-bus'

export const useWorkflowStore = defineStore('workflow', () => {
  // Current workflow state
  const currentWorkflow = ref<WorkflowJSON | null>(null)
  const selectedNodeId = ref<string | null>(null)
  const isLoading = ref<boolean>(false)

  // Node management
  const nodes = ref<NodeDefinition[]>([])
  const connections = ref<ConnectionDefinition[]>([])

  // 历史记录管理
  const historyManager = useHistoryManager()

  // Getters
  const selectedNode = computed(() => {
    if (!selectedNodeId.value) return null
    return nodes.value.find(node => node.id === selectedNodeId.value) || null
  })

  const workflowData = computed(() => {
    if (!currentWorkflow.value) return null
    return {
      ...currentWorkflow.value,
      nodes: nodes.value,
      connections: connections.value
    }
  })

  // Actions
  const createNewWorkflow = (name: string = 'New Workflow') => {
    const newWorkflow: WorkflowJSON = {
      metadata: {
        id: Date.now().toString(),
        name,
        version: '1.0.0',
        created: new Date().toISOString(),
        modified: new Date().toISOString(),
        tags: []
      },
      format_version: '2.0',
      nodes: [],
      connections: [],
      projectSettings: {}
    }

    currentWorkflow.value = newWorkflow
    nodes.value = []
    connections.value = []
    const stateBus = useStateBusStore()
    stateBus.setConnections([])
    selectedNodeId.value = null
  }

  const loadWorkflow = (workflow: WorkflowJSON) => {
    console.log('[workflowStore.loadWorkflow] Input:', { nodesCount: workflow.nodes?.length, connectionsCount: workflow.connections?.length })
    console.log('[workflowStore.loadWorkflow] Connections:', workflow.connections)
    currentWorkflow.value = workflow
    nodes.value = workflow.nodes
    connections.value = workflow.connections
    const stateBus = useStateBusStore()
    stateBus.setConnections(connections.value)
    console.log('[workflowStore.loadWorkflow] After load, connections.value:', connections.value)
    selectedNodeId.value = null
  }

  const addNode = (nodeDefinition: Omit<NodeDefinition, 'id'>) => {
    const uid = `${Date.now()}-${Math.random().toString(36).slice(2,8)}`
    const node: NodeDefinition = {
      ...nodeDefinition,
      id: uid
    }
    nodes.value.push(node)

    // 保存到历史记录
    historyManager.pushState({
      nodes: [...nodes.value],
      connections: [...connections.value]
    })

    return node
  }

  const updateNode = (nodeId: string, updates: Partial<NodeDefinition>) => {
    const nodeIndex = nodes.value.findIndex(node => node.id === nodeId)
    if (nodeIndex !== -1) {
      const oldNode = nodes.value[nodeIndex]
      nodes.value[nodeIndex] = { ...oldNode, ...updates }

      // 保存到历史记录
      historyManager.pushState({
        nodes: [...nodes.value],
        connections: [...connections.value]
      })
    }
  }

  const deleteNode = (nodeId: string) => {
    nodes.value = nodes.value.filter(node => node.id !== nodeId)
    connections.value = connections.value.filter(
      conn => conn.source.nodeId !== nodeId && conn.target.nodeId !== nodeId
    )
    const stateBus = useStateBusStore()
    stateBus.setConnections(connections.value)
    if (selectedNodeId.value === nodeId) {
      selectedNodeId.value = null
    }

    // 保存到历史记录
    historyManager.pushState({
      nodes: [...nodes.value],
      connections: [...connections.value]
    })
  }

  const addConnection = (connectionDefinition: Omit<ConnectionDefinition, 'id'>): ConnectionDefinition | null => {
    const stateBus = useStateBusStore()
    const sourceNode = nodes.value.find(node => node.id === connectionDefinition.source.nodeId)
    const targetNode = nodes.value.find(node => node.id === connectionDefinition.target.nodeId)
    const sourcePort = sourceNode?.outputs.find(port => port.id === connectionDefinition.source.portId)
    const targetPort = targetNode?.inputs.find(port => port.id === connectionDefinition.target.portId)

    if (!sourcePort || !targetPort) {
      console.warn('[workflowStore.addConnection] Missing port definitions')
      return null
    }

    const validation = stateBus.validateConnection(sourcePort as any, targetPort as any)
    if (!validation.ok) {
      console.warn('[workflowStore.addConnection] Connection rejected:', validation.reason)
      return null
    }

    const sourceKind = sourcePort.portKind ?? 'data'
    const targetKind = targetPort.portKind ?? 'data'
    const connectionKind: 'data' | 'state' =
      sourceKind === 'state-out' && targetKind === 'state-in' ? 'state' : 'data'
    const semanticType =
      connectionKind === 'state'
        ? sourcePort.semanticType || targetPort.semanticType
        : undefined

    if (connectionKind === 'state') {
      const hasCycle = stateBus.detectCycle(
        connectionDefinition.source.nodeId,
        connectionDefinition.target.nodeId,
        connections.value
      )
      if (hasCycle) {
        console.warn('[workflowStore.addConnection] Cycle detected')
        return null
      }
    }

    const connection: ConnectionDefinition = {
      ...connectionDefinition,
      id: Date.now().toString(),
      connectionKind,
      semanticType
    }
    connections.value.push(connection)
    stateBus.setConnections(connections.value)

    // 保存到历史记录
    historyManager.pushState({
      nodes: [...nodes.value],
      connections: [...connections.value]
    })

    return connection
  }

  const deleteConnection = (connectionId: string) => {
    connections.value = connections.value.filter(conn => conn.id !== connectionId)
    const stateBus = useStateBusStore()
    stateBus.setConnections(connections.value)

    // 保存到历史记录
    historyManager.pushState({
      nodes: [...nodes.value],
      connections: [...connections.value]
    })
  }

  const selectNode = (nodeId: string | null) => {
    selectedNodeId.value = nodeId
  }

  const moveNode = (nodeId: string, position: Position) => {
    updateNode(nodeId, { position })
  }

  // 撤销操作
  const undo = () => {
    const previousState = historyManager.undo()
    if (previousState) {
      nodes.value = [...previousState.nodes]
      connections.value = [...previousState.connections]
      return true
    }
    return false
  }

  // 重做操作
  const redo = () => {
    const nextState = historyManager.redo()
    if (nextState) {
      nodes.value = [...nextState.nodes]
      connections.value = [...nextState.connections]
      return true
    }
    return false
  }

  return {
    // State
    currentWorkflow,
    selectedNodeId,
    isLoading,
    nodes,
    connections,

    // Getters
    selectedNode,
    workflowData,

    // Actions
    createNewWorkflow,
    loadWorkflow,
    addNode,
    updateNode,
    deleteNode,
    addConnection,
    deleteConnection,
    selectNode,
    moveNode,

    // 历史记录管理
    historyManager: {
      canUndo: historyManager.canUndo,
      canRedo: historyManager.canRedo,
      getUndoDescription: historyManager.getUndoDescription,
      getRedoDescription: historyManager.getRedoDescription,
      clearHistory: historyManager.clearHistory,
      initializeHistory: historyManager.initializeHistory
    },
    undo,
    redo
  }
})
