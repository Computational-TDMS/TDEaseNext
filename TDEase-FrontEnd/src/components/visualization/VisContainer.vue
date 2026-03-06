<template>
  <div class="vis-container" :class="{ 'is-resizing': canvasState?.resizing, 'is-selected': canvasState?.selected }">
    <header class="vis-header">
      <div class="header-meta">
        <span class="title">{{ label }}</span>
        <el-tag size="small" type="info">{{ visualizationType }}</el-tag>
        <el-tag v-if="sourcePortId" size="small" type="success">{{ sourcePortId }}</el-tag>
      </div>
      <div class="header-actions">
        <el-button size="small" :icon="Refresh" @click="$emit('reload')">Reload</el-button>
        <el-button size="small" :icon="Setting" @click="configDrawerVisible = true">Config</el-button>
      </div>
    </header>

    <div class="vis-toolbar">
      <div class="toolbar-left">
        <el-tag v-if="data" size="small" type="warning">{{ data.totalRows }} rows</el-tag>
        <el-tag v-if="loadingState.status === 'pending'" size="small" type="warning">Pending</el-tag>
        <el-tag v-if="loadingState.status === 'error'" size="small" type="danger">Error</el-tag>
      </div>
      <div class="toolbar-right">
        <slot name="toolbar" />
      </div>
    </div>

    <div class="vis-body">
      <div v-if="loadingState.status === 'loading' && !data" class="state-pane">
        <el-icon class="is-loading" :size="26"><Loading /></el-icon>
        <span>Loading data...</span>
      </div>

      <div v-else-if="loadingState.status === 'pending' && !data" class="state-pane">
        <el-icon :size="26"><Clock /></el-icon>
        <span>{{ loadingState.message || 'Waiting for workflow execution to complete...' }}</span>
      </div>

      <div v-else-if="loadingState.status === 'error' && !data" class="state-pane error">
        <el-icon :size="26"><Warning /></el-icon>
        <span>{{ loadingState.error || 'Failed to load visualization data.' }}</span>
      </div>

      <div v-else-if="!data" class="state-pane">
        <el-icon :size="26"><Document /></el-icon>
        <span>
          {{
            hasUpstreamConnection
              ? 'No parsed data is currently available for this source.'
              : 'Connect an upstream data edge to this node first.'
          }}
        </span>
      </div>

      <slot v-else />
    </div>

    <el-drawer
      v-model="configDrawerVisible"
      title="Visualization Mapping"
      size="360px"
      append-to-body
      :destroy-on-close="false"
    >
      <ColumnConfigPanel
        :model-value="axisMapping"
        :columns="mappingColumns"
        :mapping-spec="mappingSpec || undefined"
        @update:model-value="onAxisMappingChange"
      />
      <slot name="drawer" />
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Clock, Document, Loading, Refresh, Setting, Warning } from '@element-plus/icons-vue'
import ColumnConfigPanel from './ColumnConfigPanel.vue'
import type { AxisMapping, ColumnDef, LoadingState, TableData, VisualizationType } from '@/types/visualization'
import type { ColumnSchema } from '@/types/workspace-data'
import { getMappingSpec } from '@/services/visualization/mappingSpecs'

interface CanvasState {
  selected?: boolean
  resizing?: boolean
  dragging?: boolean
  positionX?: number
  positionY?: number
}

interface Props {
  label: string
  visualizationType: string
  data: TableData | null
  loadingState: LoadingState
  hasUpstreamConnection: boolean
  sourcePortId?: string | null
  schema?: ColumnSchema[]
  axisMapping?: AxisMapping
  canvasState?: CanvasState
}

const props = withDefaults(defineProps<Props>(), {
  sourcePortId: null,
  schema: () => [],
  axisMapping: () => ({}),
  canvasState: () => ({}),
})

const emit = defineEmits<{
  reload: []
  'update:axisMapping': [mapping: AxisMapping]
}>()

const configDrawerVisible = ref(false)

const mappingSpec = computed(() => {
  return getMappingSpec(props.visualizationType as VisualizationType)
})

const mappingColumns = computed<ColumnDef[]>(() => {
  if (props.data?.columns?.length) return props.data.columns
  if (!props.schema?.length) return []
  return props.schema.map((col) => ({
    id: col.name,
    name: col.name,
    type: col.type === 'number' ? 'number' : 'text',
    visible: true,
    sortable: true,
    filterable: true,
  }))
})

function onAxisMappingChange(mapping: AxisMapping) {
  emit('update:axisMapping', mapping)
}
</script>

<style scoped>
.vis-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 320px;
  background: #ffffff;
  border: 1px solid #d5dae2;
  border-radius: 10px;
  overflow: hidden;
}

.vis-container.is-selected {
  border-color: #409eff;
  box-shadow: 0 0 0 1px rgba(64, 158, 255, 0.35);
}

.vis-container.is-resizing {
  user-select: none;
}

.vis-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 12px;
  border-bottom: 1px solid #ebeef5;
  background: linear-gradient(180deg, #f8fbff 0%, #f3f7fb 100%);
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.vis-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid #f0f2f5;
  background: #fafcff;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.vis-body {
  flex: 1;
  min-height: 220px;
  position: relative;
}

.state-pane {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 10px;
  color: #606266;
  text-align: center;
  padding: 16px;
}

.state-pane.error {
  color: #f56c6c;
}
</style>
