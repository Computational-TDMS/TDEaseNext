<template>
  <div class="interactive-node" :class="[`node-${nodeState}`, { 'edit-mode': isEditMode }]">
    <!-- Node Header -->
    <NodeHeader
      :label="label"
      :visualization-type="visualizationType"
      :loading="loading"
      :error="error"
      :pending-execution="pendingExecution"
      :is-edit-mode="isEditMode"
      @toggle-edit-mode="toggleEditMode"
      @retry="handleRetry"
      @toggle-fullscreen="toggleFullscreen"
    />

    <!-- Configuration Panel (Edit Mode) -->
    <NodeConfigPanel
      v-if="isEditMode && (hasData || hasUpstreamConnection)"
      v-model:axis-mapping="axisMapping"
      v-model:config="config"
      v-model:color-scheme="colorScheme"
      :visualization-type="visualizationType"
      :available-columns="availableColumns"
      @config-change="handleConfigChange"
      @export="handleExport"
    />

    <!-- Visualization Content -->
    <div class="node-content">
      <component
        :is="viewerComponent"
        v-if="hasData && viewerComponent"
        ref="viewerRef"
        :data="tableData"
        :config="config"
        :selection="selectionState"
        :edit-mode="isEditMode"
        @selection-change="handleSelectionChange"
        @config-change="handleConfigChange"
        @export="handleExport"
      />

      <!-- Empty State -->
      <div v-else-if="!hasData && !loading" class="empty-state">
        <el-icon :size="48"><Document /></el-icon>
        <p>{{ emptyStateMessage }}</p>
        <el-button
          v-if="hasUpstreamConnection"
          type="primary"
          :icon="Refresh"
          @click="loadData"
        >
          Load Data
        </el-button>
      </div>

      <!-- Loading State -->
      <div v-else-if="loading" class="loading-state">
        <el-icon class="is-loading" :size="48"><Loading /></el-icon>
        <p>{{ loadingMessage }}</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="error-state">
        <el-icon :size="48"><Warning /></el-icon>
        <p>{{ errorMessage }}</p>
        <el-button type="primary" :icon="Refresh" @click="handleRetry">
          Retry
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Document, Loading, Warning, Refresh } from '@element-plus/icons-vue'
import NodeHeader from './NodeHeader.vue'
import NodeConfigPanel from './NodeConfigPanel.vue'
import ScatterPlotViewer from './ScatterPlotViewer.vue'
import HeatmapViewer from './HeatmapViewer.vue'
import VolcanoPlotViewer from './VolcanoPlotViewer.vue'
import SpectrumViewer from './SpectrumViewer.vue'
import FeatureMapViewer from './FeatureMapViewer.vue'
import TableViewer from './TableViewer.vue'
import HtmlViewer from './HtmlViewer.vue'
import { useNodeStateManager } from '@/composables/useNodeStateManager'
import type { SelectionState, ExportConfig } from '@/types/visualization'

interface Props {
  nodeId: string
  label: string
  visualizationType?: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  selectionChange: [nodeId: string, selection: SelectionState]
  configChange: [nodeId: string, config: any]
  export: [nodeId: string, format: string]
}>()

// Use node state manager
const {
  nodeState,
  loading,
  error,
  pendingExecution,
  hasData,
  hasUpstreamConnection,
  tableData,
  schema,
  selectedIndices,
  selectionState,
  axisMapping,
  config,
  colorScheme,
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
  availableColumns,
} = useNodeStateManager({ nodeId: props.nodeId })

// Local state
const isEditMode = ref(false)
const viewerRef = ref()

// Computed
const viewerComponent = computed(() => {
  const typeMap: Record<string, any> = {
    scatter: ScatterPlotViewer,
    heatmap: HeatmapViewer,
    volcano: VolcanoPlotViewer,
    spectrum: SpectrumViewer,
    featuremap: FeatureMapViewer,
    table: TableViewer,
    html: HtmlViewer,
  }
  return typeMap[props.visualizationType || ''] || null
})

const emptyStateMessage = computed(() => {
  if (hasUpstreamConnection.value) {
    return 'No data loaded. Click the button below to load data from upstream.'
  }
  return 'Connect a data source to this node to visualize data.'
})

const loadingMessage = computed(() => {
  if (pendingExecution.value) {
    return 'Waiting for upstream execution to complete...'
  }
  return 'Loading data...'
})

const errorMessage = ref('')

// Methods
function toggleEditMode() {
  isEditMode.value = !isEditMode.value
}

function toggleFullscreen() {
  // Fullscreen logic
  const element = document.querySelector('.interactive-node')
  if (element) {
    if (document.fullscreenElement) {
      document.exitFullscreen()
    } else {
      element.requestFullscreen()
    }
  }
}

function handleSelectionChange(selection: SelectionState) {
  setSelectedIndices(selection.selectedIndices)
  emit('selectionChange', props.nodeId, selection)
}

function handleConfigChange(newConfig: any) {
  updateConfig(newConfig)
  emit('configChange', props.nodeId, newConfig)
}

function handleExport(format: string) {
  emit('export', props.nodeId, format)
}

function handleRetry() {
  setError(false)
  loadData()
}

async function loadData() {
  setLoading(true)
  errorMessage.value = ''

  try {
    // Load data from API
    const response = await fetch(`/api/nodes/${props.nodeId}/data`)
    if (!response.ok) {
      throw new Error('Failed to load data')
    }
    const data = await response.json()
    setTableData(data)

    // Load schema
    const schemaResponse = await fetch(`/api/nodes/${props.nodeId}/data/schema`)
    if (schemaResponse.ok) {
      const schemaData = await schemaResponse.json()
      setSchema(schemaData)
    }

    setError(false)
  } catch (e) {
    console.error('Error loading data:', e)
    errorMessage.value = e instanceof Error ? e.message : 'Unknown error'
    setError(true)
  } finally {
    setLoading(false)
  }
}

// Lifecycle
onMounted(() => {
  // Auto-load data if we have an upstream connection
  if (hasUpstreamConnection.value) {
    loadData()
  }
})
</script>

<script lang="ts">
export default {
  name: 'InteractiveNode'
}
</script>

<style scoped>
.interactive-node {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: white;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  overflow: hidden;
}

.interactive-node.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  border-radius: 0;
}

.node-content {
  flex: 1;
  position: relative;
  min-height: 400px;
}

.empty-state,
.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 40px;
  text-align: center;
}

.empty-state p,
.loading-state p,
.error-state p {
  margin: 16px 0 24px;
  font-size: 14px;
  color: #606266;
}

.error-state {
  color: #f56c6c;
}

.node-loading .node-content,
.node-error .node-content {
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
