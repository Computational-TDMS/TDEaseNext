<template>
  <div class="base-viewer" :class="{ fullscreen: isFullscreen }">
    <!-- Toolbar Slot -->
    <div v-if="$slots.toolbar" class="viewer-toolbar">
      <slot
        name="toolbar"
        :fullscreen="isFullscreen"
        :toggle-fullscreen="toggleFullscreen"
        :can-export="true"
      />
    </div>

    <!-- Configuration Panel Slot (only shown in edit mode) -->
    <div v-if="editMode && $slots.config" class="config-panel">
      <slot name="config" />
    </div>

    <!-- Chart Container -->
    <div ref="chartContainer" class="chart-container" />

    <!-- Selection Info Slot -->
    <div v-if="hasSelection && $slots.selection" class="selection-info">
      <slot
        name="selection"
        :selected-count="selectedCount"
        :clear-selection="clearSelection"
      />
    </div>

    <!-- Default Selection Info (if no slot provided) -->
    <div v-if="hasSelection && !$slots.selection" class="selection-info">
      <span>{{ selectedCount }} {{ selectionLabel }} selected</span>
      <el-button size="small" type="text" @click="clearSelection">
        Clear
      </el-button>
    </div>

    <!-- Loading Overlay -->
    <div v-if="loading" class="loading-overlay">
      <el-icon class="is-loading">
        <Loading />
      </el-icon>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { useECharts } from '@/composables/useECharts'
import { useFullscreen } from '@/composables/useFullscreen'
import { useChartSelectionIndex } from '@/composables/useChartSelection'

interface Props {
  editMode?: boolean
  loading?: boolean
  selectionLabel?: string
}

withDefaults(defineProps<Props>(), {
  editMode: false,
  loading: false,
  selectionLabel: 'items'
})

const emit = defineEmits<{
  chartReady: [chart: any]
  selectionChange: [selection: { selectedIndices: Set<number>; filterCriteria: any[]; brushRegion: any }]
}>()

// Refs
const chartContainer = ref<HTMLElement | null>(null)

// Composables
const { chart, isReady, setOption, resize } = useECharts(chartContainer)
const { isFullscreen, toggleFullscreen } = useFullscreen()
const { selectedItems, selectedCount, hasSelection, clearSelection, addSelection, removeSelection, setSelection, onSelectionChange } = useChartSelectionIndex()

// Expose methods for parent components
defineExpose({
  chart,
  isReady,
  setOption,
  resize,
  clearSelection,
  addSelection,
  removeSelection,
  setSelection,
  getSelectedItems: () => selectedItems.value
})

// Notify parent when chart is ready
watch(isReady, (ready) => {
  if (ready) {
    emit('chartReady', chart.value)
  }
})

// Handle selection changes
onSelectionChange((items) => {
  emit('selectionChange', {
    selectedIndices: new Set(items),
    filterCriteria: [],
    brushRegion: null
  })
})

// Handle fullscreen resize
watch(isFullscreen, () => {
  nextTick(() => {
    resize()
  })
})
</script>

<script lang="ts">
export default {
  name: 'BaseEChartsViewer'
}
</script>

<style scoped>
.base-viewer {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 8px;
  position: relative;
}

.base-viewer.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  background: white;
  padding: 16px;
}

.viewer-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px;
  background: #f5f7fa;
  border-radius: 4px;
  flex-shrink: 0;
}

.config-panel {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
  border: 1px solid #dcdfe6;
  flex-shrink: 0;
}

.config-panel :deep(.el-form-item) {
  margin-bottom: 0;
}

.config-panel :deep(.el-form-item__label) {
  font-size: 11px;
  color: #606266;
}

.chart-container {
  flex: 1;
  min-height: 200px;
  max-height: 100%;
  width: 100%;
  background: white;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  position: relative;
  overflow: hidden;
}

.selection-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #ecf5ff;
  border: 1px solid #b3d8ff;
  border-radius: 4px;
  font-size: 12px;
  color: #409eff;
  font-weight: 600;
  flex-shrink: 0;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  border-radius: 4px;
}

.loading-overlay .el-icon {
  font-size: 32px;
  color: #409eff;
}
</style>
