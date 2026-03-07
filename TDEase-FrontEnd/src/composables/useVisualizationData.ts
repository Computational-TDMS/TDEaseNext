import { computed, onMounted, ref, toValue, watch, type MaybeRefOrGetter } from 'vue'
import { getAPIClient, type APIClientLike } from '@/services/api/client'
import { workspaceDataApi } from '@/services/api/workspace-data'
import { useVisualizationStore } from '@/stores/visualization'
import { useWorkflowStore } from '@/stores/workflow'
import { resolveNodeInputSource } from '@/services/workflow-connector'
import { ensureToolsLoaded, useToolsRegistry } from '@/services/tools/registry'
import type { LoadingState, TableData } from '@/types/visualization'
import type { ColumnSchema } from '@/types/workspace-data'

function emptyLoadingState(): LoadingState {
  return { status: 'idle' }
}

export function useVisualizationData(
  nodeIdInput: MaybeRefOrGetter<string>,
  executionIdInput?: MaybeRefOrGetter<string | null>
) {
  const workflowStore = useWorkflowStore()
  const visualizationStore = useVisualizationStore()
  const toolsRegistry = useToolsRegistry()

  const apiClient = ref<APIClientLike | null>(null)
  const executionId = ref<string | null>(null)
  const schema = ref<ColumnSchema[]>([])
  const lastSchemaRequestKey = ref<string | null>(null)
  const stableData = ref<TableData | null>(null)
  const providedExecutionId = computed(() => (executionIdInput ? toValue(executionIdInput) : null))
  const effectiveExecutionId = computed(() => providedExecutionId.value || executionId.value)

  const nodeId = computed(() => toValue(nodeIdInput))
  const workflowId = computed(() => workflowStore.currentWorkflow?.metadata?.id || null)

  const toolsMap = computed<Record<string, { executionMode?: string }>>(() => {
    const map: Record<string, { executionMode?: string }> = {}
    for (const tool of toolsRegistry.value || []) {
      map[tool.id] = { executionMode: tool.executionMode }
    }
    for (const node of workflowStore.nodes) {
      const toolId = (node as any).nodeConfig?.toolId || node.type
      if (typeof toolId === 'string' && !map[toolId]) {
        map[toolId] = { executionMode: node.executionMode }
      }
    }
    return map
  })

  const source = computed(() => {
    return resolveNodeInputSource(
      nodeId.value,
      workflowStore.nodes,
      workflowStore.connections,
      toolsMap.value
    )
  })

  const hasUpstreamConnection = computed(() => source.value.type !== 'none')
  const sourceNodeId = computed(() => {
    return source.value.type === 'file' ? source.value.sourceNodeId || null : null
  })
  const sourcePortId = computed(() => {
    return source.value.type === 'file' ? source.value.sourcePortId || null : null
  })
  const dataAddressNodeId = computed(() => sourceNodeId.value || nodeId.value)
  const currentNode = computed(() => workflowStore.nodes.find((node) => node.id === nodeId.value) || null)
  const visualizationType = computed(() => {
    const node = currentNode.value as any
    return (
      node?.visualizationConfig?.type ||
      node?.data?.visualizationConfig?.type ||
      node?.data?.type ||
      ''
    )
  })
  const allowNonTabularFallback = computed(() => {
    return visualizationType.value === 'topmsv_ms2' || visualizationType.value === 'topmsv_sequence'
  })

  const rawData = computed<TableData | null>(() => {
    if (!effectiveExecutionId.value) return null
    return visualizationStore.getNodeData(
      dataAddressNodeId.value,
      effectiveExecutionId.value,
      sourcePortId.value
    )
  })

  const data = computed<TableData | null>(() => rawData.value || stableData.value)

  const loadingState = computed<LoadingState>(() => {
    if (!effectiveExecutionId.value) {
      return hasUpstreamConnection.value
        ? { status: 'pending', message: 'Waiting for workflow execution to complete...' }
        : emptyLoadingState()
    }
    return visualizationStore.getLoadingState(
      dataAddressNodeId.value,
      effectiveExecutionId.value,
      sourcePortId.value
    )
  })

  async function resolveLatestExecutionId(): Promise<string | null> {
    if (providedExecutionId.value) return providedExecutionId.value
    if (!workflowId.value || !apiClient.value) return null
    try {
      const latest = await workspaceDataApi.getLatestExecution(apiClient.value, workflowId.value)
      executionId.value = latest.id
      return latest.id
    } catch (error) {
      console.warn('[useVisualizationData] Failed to resolve latest execution:', error)
      return null
    }
  }

  async function fetchSchema(targetExecutionId: string): Promise<void> {
    if (!apiClient.value || !sourceNodeId.value) {
      schema.value = []
      return
    }
    const requestKey = `${targetExecutionId}:${sourceNodeId.value}:${sourcePortId.value || ''}`
    if (lastSchemaRequestKey.value === requestKey) {
      return
    }
    lastSchemaRequestKey.value = requestKey

    try {
      const query: Record<string, unknown> = {}
      if (sourcePortId.value) {
        query.port_id = sourcePortId.value
      }
      const response = await apiClient.value.get<{ schema?: ColumnSchema[] }>(
        `/api/executions/${targetExecutionId}/nodes/${sourceNodeId.value}/data/schema`,
        query
      )
      schema.value = Array.isArray(response.data?.schema) ? response.data.schema : []
    } catch (error) {
      console.warn('[useVisualizationData] Failed to fetch schema:', error)
      schema.value = []
    }
  }

  async function loadData(targetExecutionId?: string): Promise<TableData | null> {
    const resolvedExecutionId =
      targetExecutionId ??
      providedExecutionId.value ??
      (await resolveLatestExecutionId())
    if (!resolvedExecutionId || !hasUpstreamConnection.value || !sourceNodeId.value) {
      return null
    }

    executionId.value = resolvedExecutionId
    let loaded = await visualizationStore.loadNodeData(
      nodeId.value,
      resolvedExecutionId,
      sourcePortId.value,
      sourceNodeId.value,
      { allowNonTabularFallback: allowNonTabularFallback.value }
    )

    if (!loaded && !providedExecutionId.value) {
      const latestExecutionId = await resolveLatestExecutionId()
      if (latestExecutionId && latestExecutionId !== resolvedExecutionId) {
        executionId.value = latestExecutionId
        loaded = await visualizationStore.loadNodeData(
          nodeId.value,
          latestExecutionId,
          sourcePortId.value,
          sourceNodeId.value,
          { allowNonTabularFallback: allowNonTabularFallback.value }
        )
        await fetchSchema(latestExecutionId)
        return loaded
      }
    }

    if (!loaded) {
      schema.value = []
      return null
    }

    await fetchSchema(executionId.value || resolvedExecutionId)
    return loaded
  }

  async function refreshData(): Promise<TableData | null> {
    return loadData(effectiveExecutionId.value || undefined)
  }

  watch(
    () => [sourceNodeId.value, sourcePortId.value] as const,
    async ([nextSourceNode, nextSourcePort], [prevSourceNode, prevSourcePort]) => {
      if (!effectiveExecutionId.value || !nextSourceNode) return
      if (nextSourceNode !== prevSourceNode || nextSourcePort !== prevSourcePort) {
        stableData.value = null
        lastSchemaRequestKey.value = null
        await loadData(effectiveExecutionId.value)
      }
    }
  )

  watch(
    () => providedExecutionId.value,
    async (next, prev) => {
      if (!next || next === prev) return
      if (!hasUpstreamConnection.value) return
      stableData.value = null
      lastSchemaRequestKey.value = null
      await loadData(next)
    }
  )

  watch(
    () => rawData.value,
    (next) => {
      if (next) {
        stableData.value = next
      }
    },
    { deep: true, immediate: true }
  )

  onMounted(async () => {
    await ensureToolsLoaded()
    try {
      apiClient.value = getAPIClient()
    } catch {
      apiClient.value = null
    }

    if (!hasUpstreamConnection.value || !apiClient.value) return
    await loadData()
  })

  return {
    executionId: effectiveExecutionId,
    hasUpstreamConnection,
    sourceNodeId,
    sourcePortId,
    data,
    schema,
    loadingState,
    loadData,
    refreshData,
    fetchSchema,
  }
}
