import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  TableData,
  SelectionState,
  LoadingState,
  NodeDataEntry,
  NodeSelectionEntry,
  BrushRegion,
  FilterDef,
} from '@/types/visualization'
import { workspaceDataApi } from '@/services/api/workspace-data'
import type { APIClientLike } from '@/services/api/client'
import { useStateBusStore } from '@/stores/state-bus'
import { useWorkflowStore } from '@/stores/workflow'

interface LoadNodeDataOptions {
  allowNonTabularFallback?: boolean
}

/**
 * Visualization Pinia Store
 *
 * Manages interactive node data and selection states independently from workflow topology.
 */
export const useVisualizationStore = defineStore('visualization', () => {
  // State
  const nodeData = ref<Map<string, NodeDataEntry>>(new Map())
  const nodeSelections = ref<Map<string, NodeSelectionEntry>>(new Map())
  const loadingStates = ref<Map<string, LoadingState>>(new Map())
  const apiClient = ref<APIClientLike | null>(null)
  const workflowStore = useWorkflowStore()

  /**
   * Generate composite key for data storage
   * Uses (nodeId, portId, executionId) triplet
   */
  function getDataKey(nodeId: string, portId: string | null, executionId: string): string {
    if (portId) {
      return `${nodeId}:${portId}:${executionId}`
    }
    return `${nodeId}::${executionId}`
  }

  function findDataEntryByNode(
    nodeId: string,
    executionId?: string,
    portId: string | null = null
  ): NodeDataEntry | null {
    if (executionId) {
      const exact = nodeData.value.get(getDataKey(nodeId, portId, executionId))
      if (exact) return exact
    }
    const withPortPrefix = `${nodeId}:`
    const withoutPortPrefix = `${nodeId}::`
    for (const [key, entry] of nodeData.value.entries()) {
      if (key.startsWith(withPortPrefix) || key.startsWith(withoutPortPrefix)) {
        return entry
      }
    }
    return null
  }

  function findLoadingStateByNode(
    nodeId: string,
    executionId?: string,
    portId: string | null = null
  ): LoadingState | null {
    if (executionId) {
      const exact = loadingStates.value.get(getDataKey(nodeId, portId, executionId))
      if (exact) return exact
    }
    const withPortPrefix = `${nodeId}:`
    const withoutPortPrefix = `${nodeId}::`
    for (const [key, entry] of loadingStates.value.entries()) {
      if (key.startsWith(withPortPrefix) || key.startsWith(withoutPortPrefix)) {
        return entry
      }
    }
    return null
  }

  // Getters
  const getNodeData = computed(() => (
    nodeId: string,
    executionId?: string,
    portId: string | null = null
  ) => {
    return findDataEntryByNode(nodeId, executionId, portId)?.data || null
  })

  const getNodeSelection = computed(() => (nodeId: string) => {
    return nodeSelections.value.get(nodeId)?.selection || null
  })

  const getLoadingState = computed(() => (
    nodeId: string,
    executionId?: string,
    portId: string | null = null
  ) => {
    return findLoadingStateByNode(nodeId, executionId, portId) || { status: 'idle' as const }
  })

  const isNodeLoading = computed(() => (
    nodeId: string,
    executionId?: string,
    portId: string | null = null
  ) => {
    return findLoadingStateByNode(nodeId, executionId, portId)?.status === 'loading'
  })

  const hasNodeData = computed(() => (
    nodeId: string,
    executionId?: string,
    portId: string | null = null
  ) => {
    const entry = findDataEntryByNode(nodeId, executionId, portId)
    return !!entry && entry.data !== null
  })

  function extractErrorStatus(error: unknown): number | null {
    const candidateValues = [
      (error as any)?.status,
      (error as any)?.statusCode,
      (error as any)?.response?.status,
      (error as any)?.details?.status,
      (error as any)?.details?.response?.status,
      (error as any)?.details?.details?.status,
    ]
    for (const value of candidateValues) {
      if (typeof value === 'number' && Number.isFinite(value)) {
        return value
      }
    }
    return null
  }

  function extractErrorMessage(error: unknown): string {
    const messages: string[] = []
    if (error instanceof Error && error.message) {
      messages.push(error.message)
    }

    const details = [
      (error as any)?.detail,
      (error as any)?.details?.detail,
      (error as any)?.details?.message,
      (error as any)?.details?.details?.detail,
      (error as any)?.details?.details?.message,
    ]
    for (const detail of details) {
      if (typeof detail === 'string' && detail.trim()) {
        messages.push(detail.trim())
      }
    }

    return Array.from(new Set(messages)).join(' | ')
  }

  function isStaleExecutionMessage(message: string): boolean {
    const normalized = message.toLowerCase()
    return (
      normalized.includes('older workflow revision') ||
      normalized.includes('not part of execution') ||
      normalized.includes('workflow snapshot is empty') ||
      normalized.includes('execution not found') ||
      normalized.includes('node not found in workflow snapshot')
    )
  }

  // Actions

  /**
   * Set API client for data fetching
   */
  function setApiClient(client: APIClientLike) {
    apiClient.value = client
  }

  /**
   * Load node data from backend API
   *
   * @param nodeId - Node identifier
   * @param executionId - Execution identifier
   * @param portId - Output port identifier (for multi-output tools)
   * @param upstreamNodeId - Upstream node identifier (for state-based data)
   */
  async function loadNodeData(
    nodeId: string,
    executionId: string,
    portId: string | null = null,
    upstreamNodeId?: string,
    options: LoadNodeDataOptions = {}
  ): Promise<TableData | null> {
    if (!apiClient.value) {
      console.error('[VisualizationStore] API client not set')
      return null
    }

    const actualNodeId = upstreamNodeId || nodeId
    const dataAddressNodeId = actualNodeId
    const dataKey = getDataKey(dataAddressNodeId, portId, executionId)

    console.log(`[VisualizationStore] Loading node data:`, {
        nodeId,
        executionId,
        portId,
        upstreamNodeId,
        actualNodeId,
        dataAddressNodeId,
        dataKey
      })

    // Set loading state
    loadingStates.value.set(dataKey, { status: 'loading' })

    try {
      console.log(`[VisualizationStore] Calling API: /api/executions/${executionId}/nodes/${actualNodeId}/data`)
      const response = await workspaceDataApi.getNodeData(apiClient.value, {
        execution_id: executionId,
        node_id: actualNodeId,
        port_id: portId || undefined,
        include_data: true,
      })

      console.log(`[VisualizationStore] API response:`, response)
      console.log(`[VisualizationStore] Number of outputs: ${response.outputs?.length || 0}`)

      // Log each output for debugging
      response.outputs?.forEach((output, idx) => {
        console.log(`[VisualizationStore] Output [${idx}]:`, {
          port_id: output.port_id,
          file_name: output.file_name,
          file_path: output.file_path,
          exists: output.exists,
          parseable: output.parseable,
          has_data: output.data !== null,
          data_rows: output.data?.rows?.length || 0,
          data_columns: output.data?.columns || []
        })
      })

      // API returns NodeOutputResponse with outputs array
      // Find the first output with parsed data
      const outputWithData = response.outputs?.find(
        (output) => output.parseable && output.data !== null
      )
      const outputForFallback = options.allowNonTabularFallback
        ? response.outputs?.find((output) => output.exists && !!output.file_path)
        : undefined

      console.log(`[VisualizationStore] Output with data:`, outputWithData ? {
        port_id: outputWithData.port_id,
        file_name: outputWithData.file_name,
        rows: outputWithData.data?.rows?.length,
        columns: outputWithData.data?.columns
      } : null)

      if (!outputWithData || !outputWithData.data) {
        if (outputForFallback) {
          const fallbackRow: Record<string, unknown> = {
            __execution_id: executionId,
            __workflow_id: workflowStore.currentWorkflow?.metadata?.id || '',
            __node_id: actualNodeId,
            __port_id: outputForFallback.port_id || '',
            __data_type: outputForFallback.data_type || '',
            __file_path: outputForFallback.file_path || '',
            __relative_path: outputForFallback.relative_path || '',
            __file_name: outputForFallback.file_name || '',
            __is_directory: Boolean(outputForFallback.is_directory),
            __sample:
              ((workflowStore.currentWorkflow?.metadata as any)?.sample_context?.sample as string | undefined) || '',
          }

          const fallbackColumns = Object.keys(fallbackRow).map((name) => ({
            id: name,
            name,
            type: typeof fallbackRow[name] === 'boolean' ? 'boolean' as const : 'text' as const,
            visible: false,
            sortable: false,
            filterable: false,
          }))

          const fallbackData: TableData = {
            columns: fallbackColumns,
            rows: [fallbackRow],
            totalRows: 1,
            sourceFile: outputForFallback.file_path || '',
          }

          nodeData.value.set(dataKey, {
            data: fallbackData,
            loadingState: { status: 'success' },
          })
          loadingStates.value.set(dataKey, { status: 'success' })
          return fallbackData
        }

        const hasOutputs = response.outputs && response.outputs.length > 0
        const allMissing = hasOutputs && response.outputs!.every(o => !o.exists)
        const message = allMissing
          ? '输出文件未找到，请运行工作流生成数据'
          : 'No parseable data available'
        console.warn(`[VisualizationStore] No parseable data found for node ${dataAddressNodeId}`)
        console.warn(`[VisualizationStore] Has outputs: ${hasOutputs}, All missing: ${allMissing}`)
        loadingStates.value.set(dataKey, {
          status: allMissing ? 'pending' : 'error',
          message: allMissing ? message : undefined,
          error: allMissing ? undefined : message,
        })
        return null
      }

      // Convert API response format (workspace-data TableData) to visualization TableData format
      // API returns: { columns: string[], rows: Record<string, string>[], total_rows: number }
      // Visualization expects: { columns: ColumnDef[], rows: Record<string, unknown>[], totalRows: number, sourceFile: string }
      const apiData = outputWithData.data
      const columnDefs = apiData.columns.map((colName: string) => ({
        id: colName,
        name: colName,
        type: 'text' as const,
        visible: true,
        sortable: true,
        filterable: true,
      }))

      const visualizationTableData: TableData = {
        columns: columnDefs,
        rows: apiData.rows as Record<string, unknown>[],
        totalRows: apiData.total_rows || 0,
        sourceFile: outputWithData.file_path || '',
      }

      // Cache the data
      nodeData.value.set(dataKey, {
        data: visualizationTableData,
        loadingState: { status: 'success' },
      })

      loadingStates.value.set(dataKey, { status: 'success' })

      return visualizationTableData
    } catch (error) {
      const statusCode = extractErrorStatus(error)
      const errorMsg = extractErrorMessage(error) || 'Unknown error'
      const is404 = statusCode === 404 || errorMsg.includes('404')
      const isStaleExecution = isStaleExecutionMessage(errorMsg)

      if (is404 || isStaleExecution) {
        const pendingMessage = isStaleExecution
          ? 'Execution data is from an older workflow revision. Please re-run and switch to the latest execution.'
          : 'Waiting for workflow execution to complete...'

        console.warn(
          `[VisualizationStore] Node ${dataAddressNodeId} data pending/unavailable:`,
          { statusCode, errorMsg }
        )

        loadingStates.value.set(dataKey, {
          status: 'pending',
          message: pendingMessage,
        })

        nodeData.value.set(dataKey, {
          data: null,
          loadingState: { status: 'pending', message: pendingMessage },
        })

        return null
      }

      // For other errors, log and set error state
      console.error(`[VisualizationStore] Failed to load data for node ${dataAddressNodeId}:`, error)

      loadingStates.value.set(dataKey, {
        status: 'error',
        error: errorMsg,
      })

      nodeData.value.set(dataKey, {
        data: null,
        loadingState: { status: 'error', error: errorMsg },
      })

      return null
    }
  }

  /**
   * Update selection state for a node
   *
   * @param nodeId - Node identifier
   * @param selection - Selection state
   */
  function updateSelection(
    nodeId: string,
    selection: SelectionState,
    outputPortId: string = 'selection_out'
  ) {
    nodeSelections.value.set(nodeId, {
      selection,
      timestamp: Date.now(),
    })

    const stateBus = useStateBusStore()
    stateBus.dispatch(nodeId, outputPortId, {
      semanticType: 'state/selection_ids',
      data: selection,
      timestamp: Date.now(),
      sourceNodeId: nodeId,
      portId: outputPortId,
    })
  }

  /**
   * Clear selection for a node
   *
   * @param nodeId - Node identifier
   */
  function clearSelection(nodeId: string) {
    nodeSelections.value.delete(nodeId)
  }

  /**
   * Update brush region for a node
   *
   * @param nodeId - Node identifier
   * @param brushRegion - Brush region
   */
  function updateBrushRegion(nodeId: string, brushRegion: BrushRegion | null) {
    const current = nodeSelections.value.get(nodeId)?.selection
    if (current) {
      updateSelection(nodeId, {
        ...current,
        brushRegion,
      })
    } else {
      updateSelection(nodeId, {
        selectedIndices: new Set<number>(),
        filterCriteria: [],
        brushRegion,
      })
    }
  }

  /**
   * Update filter criteria for a node
   *
   * @param nodeId - Node identifier
   * @param filterCriteria - Filter criteria
   */
  function updateFilterCriteria(nodeId: string, filterCriteria: FilterDef[]) {
    const current = nodeSelections.value.get(nodeId)?.selection
    if (current) {
      updateSelection(nodeId, {
        ...current,
        filterCriteria,
      })
    } else {
      updateSelection(nodeId, {
        selectedIndices: new Set<number>(),
        filterCriteria,
        brushRegion: null,
      })
    }
  }

  /**
   * Get filtered rows based on selection state
   *
   * @param nodeId - Node identifier
   * @returns Filtered rows
   */
  function getFilteredRows(nodeId: string): Record<string, unknown>[] {
    const dataEntry = findDataEntryByNode(nodeId)
    if (!dataEntry?.data) return []

    const selectionEntry = nodeSelections.value.get(nodeId)
    const selection = selectionEntry?.selection

    if (!selection) return dataEntry.data.rows

    let rows = [...dataEntry.data.rows]

    // Apply filter criteria
    if (selection.filterCriteria.length > 0) {
      rows = rows.filter((row) => {
        return selection.filterCriteria.every((filter) => {
          const value = row[filter.columnId]
          return applyFilter(value, filter)
        })
      })
    }

    // Apply selected indices
    if (selection.selectedIndices.size > 0) {
      const indexSet = selection.selectedIndices
      rows = rows.filter((_, index) => indexSet.has(index))
    }

    return rows
  }

  /**
   * Apply a single filter to a value
   */
  function applyFilter(value: unknown, filter: FilterDef): boolean {
    switch (filter.operator) {
      case 'eq':
        return value === filter.value
      case 'ne':
        return value !== filter.value
      case 'gt':
        return typeof value === 'number' && value > (filter.value as number)
      case 'lt':
        return typeof value === 'number' && value < (filter.value as number)
      case 'gte':
        return typeof value === 'number' && value >= (filter.value as number)
      case 'lte':
        return typeof value === 'number' && value <= (filter.value as number)
      case 'contains':
        return typeof value === 'string' && value.includes(filter.value as string)
      default:
        return true
    }
  }

  /**
   * Clear all cached data and selections
   */
  function clearAll() {
    nodeData.value.clear()
    nodeSelections.value.clear()
    loadingStates.value.clear()
  }

  /**
   * Remove data for a specific node
   *
   * @param nodeId - Node identifier
   */
  function removeNode(nodeId: string) {
    const withPortPrefix = `${nodeId}:`
    const withoutPortPrefix = `${nodeId}::`
    for (const key of nodeData.value.keys()) {
      if (key.startsWith(withPortPrefix) || key.startsWith(withoutPortPrefix)) {
        nodeData.value.delete(key)
      }
    }
    nodeSelections.value.delete(nodeId)
    for (const key of loadingStates.value.keys()) {
      if (key.startsWith(withPortPrefix) || key.startsWith(withoutPortPrefix)) {
        loadingStates.value.delete(key)
      }
    }
  }

  function setNodeData(
    nodeId: string,
    data: TableData | null,
    executionId: string = 'local',
    portId: string | null = null
  ) {
    const dataKey = getDataKey(nodeId, portId, executionId)
    nodeData.value.set(dataKey, {
      data,
      loadingState: { status: data ? 'success' : 'idle' }
    })
    loadingStates.value.set(dataKey, { status: data ? 'success' : 'idle' })
  }

  return {
    // State
    nodeData,
    nodeSelections,
    loadingStates,

    // Getters
    getNodeData,
    getNodeSelection,
    getLoadingState,
    isNodeLoading,
    hasNodeData,

    // Actions
    setApiClient,
    loadNodeData,
    updateSelection,
    clearSelection,
    updateBrushRegion,
    updateFilterCriteria,
    getFilteredRows,
    clearAll,
    removeNode,
    setNodeData,
  }
})
