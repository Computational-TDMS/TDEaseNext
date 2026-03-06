import { ref, watch, type Ref } from 'vue'
import type { TableData, SelectionState } from '@/types/visualization'

export interface NodeState {
  loading: boolean
  error: boolean
  pendingExecution: boolean
  hasData: boolean
  hasUpstreamConnection: boolean
}

export interface UseNodeStateManagerOptions {
  nodeId?: string
}

export interface UseNodeStateManagerReturn {
  // State
  nodeState: Ref<string>
  loading: Ref<boolean>
  error: Ref<boolean>
  pendingExecution: Ref<boolean>
  hasData: Ref<boolean>
  hasUpstreamConnection: Ref<boolean>

  // Data
  tableData: Ref<TableData | null>
  schema: Ref<any[] | null>
  selectedIndices: Ref<Set<number>>
  selectionState: Ref<SelectionState | null>

  // Config
  axisMapping: Ref<Record<string, string>>
  config: Ref<Record<string, any>>
  colorScheme: Ref<string>

  // Methods
  setLoading: (loading: boolean) => void
  setError: (error: boolean) => void
  setPendingExecution: (pending: boolean) => void
  setHasData: (hasData: boolean) => void
  setHasUpstreamConnection: (hasConnection: boolean) => void
  setTableData: (data: TableData | null) => void
  setSchema: (schema: any[] | null) => void
  setSelectedIndices: (indices: Set<number>) => void
  updateAxisMapping: (mapping: Record<string, string>) => void
  updateConfig: (config: Record<string, any>) => void
  updateColorScheme: (scheme: string) => void

  // Computed helpers
  availableColumns: Ref<any[]>
  numericColumns: Ref<any[]>
}

export function useNodeStateManager(_options: UseNodeStateManagerOptions = {}): UseNodeStateManagerReturn {
  // State refs
  const loading = ref(false)
  const error = ref(false)
  const pendingExecution = ref(false)
  const hasData = ref(false)
  const hasUpstreamConnection = ref(false)

  // Data refs
  const tableData = ref<TableData | null>(null)
  const schema = ref<any[] | null>(null)
  const selectedIndices = ref<Set<number>>(new Set())
  const selectionState = ref<SelectionState | null>(null)

  // Config refs
  const axisMapping = ref<Record<string, string>>({})
  const config = ref<Record<string, any>>({})
  const colorScheme = ref('viridis')

  // Computed node state
  const nodeState = ref('empty')

  // Update node state based on other refs
  watch([error, loading, pendingExecution, hasData], () => {
    if (error.value) nodeState.value = 'error'
    else if (loading.value) nodeState.value = 'loading'
    else if (pendingExecution.value) nodeState.value = 'pending'
    else if (hasData.value) nodeState.value = 'ready'
    else nodeState.value = 'empty'
  })

  // Computed helpers
  const availableColumns = ref<any[]>([])
  const numericColumns = ref<any[]>([])

  // Update available columns when table data changes
  watch(tableData, (data) => {
    availableColumns.value = data?.columns || []
    numericColumns.value = availableColumns.value.filter(c => c.type === 'number')
  })

  // Methods
  const setLoading = (value: boolean) => {
    loading.value = value
  }

  const setError = (value: boolean) => {
    error.value = value
  }

  const setPendingExecution = (value: boolean) => {
    pendingExecution.value = value
  }

  const setHasData = (value: boolean) => {
    hasData.value = value
  }

  const setHasUpstreamConnection = (value: boolean) => {
    hasUpstreamConnection.value = value
  }

  const setTableData = (data: TableData | null) => {
    tableData.value = data
    hasData.value = data !== null && data.rows.length > 0
  }

  const setSchema = (data: any[] | null) => {
    schema.value = data
  }

  const setSelectedIndices = (indices: Set<number>) => {
    selectedIndices.value = indices
    selectionState.value = {
      selectedIndices: indices,
      filterCriteria: [],
      brushRegion: null
    }
  }

  const updateAxisMapping = (mapping: Record<string, string>) => {
    axisMapping.value = { ...mapping }
  }

  const updateConfig = (newConfig: Record<string, any>) => {
    config.value = { ...newConfig }
  }

  const updateColorScheme = (scheme: string) => {
    colorScheme.value = scheme
  }

  // Watch for selection changes to update state
  watch(selectedIndices, (indices) => {
    selectionState.value = {
      selectedIndices: indices,
      filterCriteria: [],
      brushRegion: null
    }
  })

  return {
    // State
    nodeState,
    loading,
    error,
    pendingExecution,
    hasData,
    hasUpstreamConnection,

    // Data
    tableData,
    schema,
    selectedIndices,
    selectionState,

    // Config
    axisMapping,
    config,
    colorScheme,

    // Methods
    setLoading,
    setError,
    setPendingExecution,
    setHasData,
    setHasUpstreamConnection,
    setTableData,
    setSchema,
    setSelectedIndices,
    updateAxisMapping,
    updateConfig,
    updateColorScheme,

    // Computed helpers
    availableColumns,
    numericColumns,
  }
}
