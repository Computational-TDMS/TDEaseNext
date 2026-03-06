<template>
  <div class="interactive-node" :class="{ selected: !!selected }">
    <div class="ports-column left">
      <PortList side="left" :node-id="nodeId" :ports="inputs" />
    </div>

    <VisContainer
      class="vis-main"
      :label="label"
      :visualization-type="visualizationType"
      :data="tableData"
      :schema="schema"
      :loading-state="loadingState"
      :has-upstream-connection="hasUpstreamConnection"
      :source-port-id="sourcePortId"
      :axis-mapping="axisMapping"
      :canvas-state="{
        selected: !!selected,
        resizing: !!resizing,
        dragging: !!dragging,
        positionX: positionAbsoluteX,
        positionY: positionAbsoluteY
      }"
      @reload="reloadData"
      @update:axis-mapping="handleAxisMappingChange"
    >
      <component
        :is="viewerComponent"
        v-if="viewerComponent && tableData"
        :data="tableData"
        :config="localConfig"
        :selection="selectionState"
        @selection-change="handleSelectionChange"
        @config-change="handleViewerConfigChange"
      />
    </VisContainer>

    <div class="ports-column right">
      <PortList side="right" :node-id="nodeId" :ports="outputs" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import type { StatePayload } from '@/types/state-ports'
import type { AxisMapping, SelectionState } from '@/types/visualization'
import { useWorkflowStore } from '@/stores/workflow'
import { useStateBusStore } from '@/stores/state-bus'
import { useVisualizationStore } from '@/stores/visualization'
import { useVisualizationData } from '@/composables/useVisualizationData'
import PortList from '@/components/node/PortList.vue'
import VisContainer from './VisContainer.vue'
import FeatureMapViewer from './FeatureMapViewer.vue'
import ScatterPlotViewer from './ScatterPlotViewer.vue'
import TableViewer from './TableViewer.vue'
import HeatmapViewer from './HeatmapViewer.vue'
import SpectrumViewer from './SpectrumViewer.vue'
import VolcanoPlotViewer from './VolcanoPlotViewer.vue'
import HtmlViewer from './HtmlViewer.vue'

interface NodePort {
  id: string
  name?: string
  type?: string
  dataType?: string
  pattern?: string
  required?: boolean
  accept?: string[]
  provides?: string[]
  portKind?: 'data' | 'state-in' | 'state-out'
  semanticType?: string
}

interface InteractiveNodeData {
  nodeId?: string
  label?: string
  toolId?: string
  visualizationConfig?: {
    type?: string
    config?: Record<string, unknown>
  }
  nodeConfig?: {
    inputs?: NodePort[]
    outputs?: NodePort[]
  }
}

interface Props {
  id: string
  data: InteractiveNodeData
  selected?: boolean
  dragging?: boolean
  resizing?: boolean
  positionAbsoluteX?: number
  positionAbsoluteY?: number
}

const props = defineProps<Props>()

const workflowStore = useWorkflowStore()
const { currentExecutionId } = storeToRefs(workflowStore)
const stateBus = useStateBusStore()
const visualizationStore = useVisualizationStore()

const nodeId = computed(() => props.data?.nodeId || props.id)
const label = computed(() => props.data?.label || 'Interactive Viewer')

const inputs = computed<NodePort[]>(() => {
  const configured = props.data?.nodeConfig?.inputs
  if (configured?.length) return configured
  const node = workflowStore.nodes.find((item) => item.id === nodeId.value)
  return ((node?.inputs || []) as NodePort[])
})

const outputs = computed<NodePort[]>(() => {
  const configured = props.data?.nodeConfig?.outputs
  if (configured?.length) return configured
  const node = workflowStore.nodes.find((item) => item.id === nodeId.value)
  return ((node?.outputs || []) as NodePort[])
})

const stateOutputPortId = computed(() => {
  const port = outputs.value.find((output) => output.portKind === 'state-out')
  return port?.id || 'selection_out'
})

const visualizationType = computed(() => {
  const configured = props.data?.visualizationConfig?.type
  if (configured) return configured
  const toolId = props.data?.toolId || ''
  if (toolId.includes('featuremap')) return 'featuremap'
  if (toolId.includes('scatter')) return 'scatter'
  if (toolId.includes('table')) return 'table'
  if (toolId.includes('heatmap')) return 'heatmap'
  if (toolId.includes('spectrum')) return 'spectrum'
  if (toolId.includes('volcano')) return 'volcano'
  if (toolId.includes('html')) return 'html'
  return 'table'
})

const viewerComponent = computed(() => {
  const typeMap: Record<string, unknown> = {
    featuremap: FeatureMapViewer,
    scatter: ScatterPlotViewer,
    table: TableViewer,
    heatmap: HeatmapViewer,
    spectrum: SpectrumViewer,
    volcano: VolcanoPlotViewer,
    html: HtmlViewer,
  }
  return typeMap[visualizationType.value] || TableViewer
})

const localConfig = ref<Record<string, unknown>>({})
const axisMapping = ref<AxisMapping>({})
const selectionState = ref<SelectionState | null>(null)

watch(
  () => props.data?.visualizationConfig?.config,
  (config) => {
    const normalized = (config || {}) as Record<string, unknown>
    localConfig.value = { ...normalized }
    const nextAxisMapping = (normalized.axisMapping || {}) as AxisMapping
    axisMapping.value = { ...nextAxisMapping }
  },
  { immediate: true, deep: true }
)

const {
  hasUpstreamConnection,
  sourcePortId,
  data: tableData,
  schema,
  loadingState,
  refreshData,
} = useVisualizationData(nodeId, currentExecutionId)

function persistVisualizationConfig(nextConfig: Record<string, unknown>, nextAxisMapping?: AxisMapping) {
  if (nextAxisMapping) {
    axisMapping.value = { ...nextAxisMapping }
  }
  const normalized = {
    ...nextConfig,
    axisMapping: { ...axisMapping.value },
  }
  localConfig.value = normalized
  workflowStore.updateNode(nodeId.value, {
    visualizationConfig: {
      type: visualizationType.value,
      config: normalized,
    } as any,
  } as any)
}

function handleAxisMappingChange(nextMapping: AxisMapping) {
  persistVisualizationConfig({ ...localConfig.value }, nextMapping)
}

function handleViewerConfigChange(nextConfig: Record<string, unknown>) {
  persistVisualizationConfig({
    ...localConfig.value,
    ...nextConfig,
  })
}

function normalizeSelectionPayload(payload: StatePayload): SelectionState | null {
  if (payload.semanticType !== 'state/selection_ids') return null

  const source = payload.data as any
  if (!source) return null

  if (source instanceof Set) {
    return {
      selectedIndices: source,
      filterCriteria: [],
      brushRegion: null,
    }
  }

  if (Array.isArray(source)) {
    return {
      selectedIndices: new Set(source.map((item) => Number(item))),
      filterCriteria: [],
      brushRegion: null,
    }
  }

  const selectedRaw = source.selectedIndices
  const selectedIndices = selectedRaw instanceof Set
    ? selectedRaw
    : Array.isArray(selectedRaw)
      ? new Set(selectedRaw.map((item: unknown) => Number(item)))
      : null
  if (!selectedIndices) return null

  return {
    selectedIndices,
    filterCriteria: Array.isArray(source.filterCriteria) ? source.filterCriteria : [],
    brushRegion: source.brushRegion || null,
  }
}

const unsubscribeHandlers = ref<Array<() => void>>([])

function clearStateSubscriptions() {
  unsubscribeHandlers.value.forEach((unsubscribe) => unsubscribe())
  unsubscribeHandlers.value = []
}

function setupStateSubscriptions() {
  clearStateSubscriptions()
  const stateInputPorts = inputs.value
    .filter((port) => port.portKind === 'state-in')
    .map((port) => port.id)
  for (const portId of stateInputPorts) {
    const unsubscribe = stateBus.subscribe(nodeId.value, portId, (payload) => {
      const normalized = normalizeSelectionPayload(payload)
      if (normalized) {
        selectionState.value = normalized
      }
    })
    unsubscribeHandlers.value.push(unsubscribe)
  }
}

watch(
  () => inputs.value.map((port) => `${port.id}:${port.portKind || 'data'}`),
  () => setupStateSubscriptions(),
  { immediate: true }
)

function handleSelectionChange(selection: SelectionState) {
  selectionState.value = selection
  visualizationStore.updateSelection(nodeId.value, selection, stateOutputPortId.value)
}

async function reloadData() {
  await refreshData()
}

onUnmounted(() => {
  clearStateSubscriptions()
})
</script>

<script lang="ts">
export default {
  name: 'InteractiveNode'
}
</script>

<style scoped>
.interactive-node {
  display: grid;
  grid-template-columns: 120px minmax(520px, 1fr) 120px;
  align-items: stretch;
  gap: 8px;
  min-height: 360px;
  width: 100%;
  background: transparent;
}

.interactive-node.selected {
  filter: saturate(1.02);
}

.ports-column {
  min-width: 0;
}

.ports-column.left {
  padding-top: 8px;
}

.ports-column.right {
  padding-top: 8px;
}

.vis-main {
  min-height: 360px;
}

@media (max-width: 960px) {
  .interactive-node {
    grid-template-columns: 100px minmax(420px, 1fr) 100px;
    min-height: 320px;
  }
}
</style>
