<template>
  <div class="filter-node">
    <div class="filter-icon">F</div>
    <div class="filter-content">
      <div class="filter-label">{{ label }}</div>
      <div class="filter-meta">
        <span class="filter-badge">{{ filteredCount }}/{{ totalCount }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useWorkflowStore } from '@/stores/workflow'
import { useVisualizationStore } from '@/stores/visualization'
import { useStateBusStore } from '@/stores/state-bus'
import type { StatePayload } from '@/types/state-ports'
import type { TableData } from '@/types/visualization'

interface Props {
  id: string
  data: {
    nodeId?: string
    label?: string
  }
}

const props = defineProps<Props>()
const workflowStore = useWorkflowStore()
const visualizationStore = useVisualizationStore()
const stateBus = useStateBusStore()

const label = computed(() => props.data.label || 'Filter')
const filteredCount = ref(0)
const totalCount = ref(0)
const filterPayload = ref<StatePayload | null>(null)
const unsubscribeHandlers = ref<Array<() => void>>([])

function getUpstreamData(): TableData | null {
  const nodeId = props.data.nodeId || props.id
  const incoming = workflowStore.connections.find(
    conn => conn.target.nodeId === nodeId && conn.target.portId === 'data_in'
  )
  if (!incoming) return null
  return visualizationStore.getNodeData(incoming.source.nodeId)
}

function applyFilter(data: TableData | null, payload: StatePayload | null): TableData | null {
  if (!data) return null
  totalCount.value = data.rows.length
  if (!payload) {
    filteredCount.value = data.rows.length
    return data
  }

  if (payload.semanticType === 'state/range' && payload.data && typeof payload.data === 'object') {
    const column = (payload.data as any).column
    const minVal = (payload.data as any).min
    const maxVal = (payload.data as any).max
    if (!column) {
      filteredCount.value = data.rows.length
      return data
    }
    const rows = data.rows.filter((row) => {
      const value = Number((row as any)[column])
      if (Number.isNaN(value)) return false
      if (minVal !== null && minVal !== undefined && value < minVal) return false
      if (maxVal !== null && maxVal !== undefined && value > maxVal) return false
      return true
    })
    filteredCount.value = rows.length
    return { ...data, rows, totalRows: rows.length }
  }

  if (payload.semanticType === 'state/selection_ids') {
    let indices: Set<number> | null = null
    if (payload.data instanceof Set) indices = payload.data
    if (Array.isArray(payload.data)) indices = new Set(payload.data.map(v => Number(v)))
    if (payload.data && typeof payload.data === 'object' && 'selectedIndices' in payload.data) {
      indices = (payload.data as any).selectedIndices
    }
    if (!indices) {
      filteredCount.value = data.rows.length
      return data
    }
    const rows = data.rows.filter((_, idx) => indices?.has(idx))
    filteredCount.value = rows.length
    return { ...data, rows, totalRows: rows.length }
  }

  filteredCount.value = data.rows.length
  return data
}

function refreshFilteredData() {
  const nodeId = props.data.nodeId || props.id
  const upstream = getUpstreamData()
  const filtered = applyFilter(upstream, filterPayload.value)
  if (filtered) {
    visualizationStore.setNodeData(nodeId, filtered)
  }
}

function setupSubscriptions() {
  unsubscribeHandlers.value.forEach(unsub => unsub())
  unsubscribeHandlers.value = []
  const nodeId = props.data.nodeId || props.id
  const unsub = stateBus.subscribe(nodeId, 'filter_in', (payload) => {
    filterPayload.value = payload
    refreshFilteredData()
  })
  unsubscribeHandlers.value.push(unsub)
}

watch(
  () => workflowStore.connections,
  () => refreshFilteredData(),
  { deep: true }
)

onMounted(() => {
  setupSubscriptions()
  refreshFilteredData()
})

onUnmounted(() => {
  unsubscribeHandlers.value.forEach(unsub => unsub())
  unsubscribeHandlers.value = []
})
</script>

<style scoped>
.filter-node {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  min-width: 140px;
  background: #fff7ed;
  border: 2px solid #fdba74;
  border-radius: 8px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.08);
}

.filter-icon {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: #fb923c;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
}

.filter-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.filter-label {
  font-size: 12px;
  font-weight: 600;
  color: #9a3412;
}

.filter-badge {
  font-size: 11px;
  color: #7c2d12;
  background: #ffedd5;
  padding: 2px 6px;
  border-radius: 10px;
}
</style>
