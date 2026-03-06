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

  // Getters
  const getNodeData = computed(() => (nodeId: string) => {
    return nodeData.value.get(nodeId)?.data || null
  })

  const getNodeSelection = computed(() => (nodeId: string) => {
    return nodeSelections.value.get(nodeId)?.selection || null
  })

  const getLoadingState = computed(() => (nodeId: string) => {
    return loadingStates.value.get(nodeId) || { status: 'idle' as const }
  })

  const isNodeLoading = computed(() => (nodeId: string) => {
    return loadingStates.value.get(nodeId)?.status === 'loading'
  })

  const hasNodeData = computed(() => (nodeId: string) => {
    return nodeData.value.has(nodeId) && nodeData.value.get(nodeId)?.data !== null
  })

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
    upstreamNodeId?: string
  ): Promise<TableData | null> {
    if (!apiClient.value) {
      console.error('[VisualizationStore] API client not set')
      return null
    }

    const actualNodeId = upstreamNodeId || nodeId
    const dataKey = getDataKey(nodeId, portId, executionId)

    console.log(`[VisualizationStore] Loading node data:`, {
      nodeId,
      executionId,
      portId,
      upstreamNodeId,
      actualNodeId,
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

      console.log(`[VisualizationStore] Output with data:`, outputWithData ? {
        port_id: outputWithData.port_id,
        file_name: outputWithData.file_name,
        rows: outputWithData.data?.rows?.length,
        columns: outputWithData.data?.columns
      } : null)

      if (!outputWithData || !outputWithData.data) {
        const hasOutputs = response.outputs && response.outputs.length > 0
        const allMissing = hasOutputs && response.outputs!.every(o => !o.exists)
        const message = allMissing
          ? '输出文件未找到，请运行工作流生成数据'
          : 'No parseable data available'
        console.warn(`[VisualizationStore] No parseable data found for node ${nodeId}`)
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
      // Check if this is a 404 error (node data not yet available)
      const is404 = error instanceof Error && (
        error.message.includes('404') ||
        (error as any).response?.status === 404 ||
        (error as any).statusCode === 404
      )

      if (is404) {
        // Node data not yet available - this is normal for unexecuted or running workflows
        console.log(`[VisualizationStore] Node ${nodeId} data not yet available (workflow not executed or node not complete)`)
        loadingStates.value.set(dataKey, {
          status: 'pending',
          message: 'Waiting for workflow execution to complete...',
        })

        nodeData.value.set(dataKey, {
          data: null,
          loadingState: { status: 'pending', message: 'Waiting for workflow execution' },
        })

        return null
      }

      // For other errors, log and set error state
      console.error(`[VisualizationStore] Failed to load data for node ${nodeId}:`, error)
      const errorMsg = error instanceof Error ? error.message : 'Unknown error'

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
  function updateSelection(nodeId: string, selection: SelectionState) {
    nodeSelections.value.set(nodeId, {
      selection,
      timestamp: Date.now(),
    })

    const stateBus = useStateBusStore()
    stateBus.dispatch(nodeId, 'selection_out', {
      semanticType: 'state/selection_ids',
      data: selection,
      timestamp: Date.now(),
      sourceNodeId: nodeId,
      portId: 'selection_out',
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
    const dataEntry = nodeData.value.get(nodeId)
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
    nodeData.value.delete(nodeId)
    nodeSelections.value.delete(nodeId)
    loadingStates.value.delete(nodeId)
  }

  function setNodeData(nodeId: string, data: TableData | null) {
    nodeData.value.set(nodeId, {
      data,
      loadingState: { status: data ? 'success' : 'idle' }
    })
    loadingStates.value.set(nodeId, { status: data ? 'success' : 'idle' })
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
