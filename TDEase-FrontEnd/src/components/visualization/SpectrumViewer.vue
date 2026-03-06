<template>
  <BaseEChartsViewer
    ref="baseViewer"
    :edit-mode="false"
    :loading="loading"
    selection-label="peaks"
    @chart-ready="onChartReady"
    @selection-change="handleSelectionChange"
  >
    <template #toolbar>
      <div class="toolbar-left">
        <el-tag v-if="peakCount > 0" type="info" size="small">
          {{ peakCount }} peaks
        </el-tag>
        <el-tag v-if="selectedPeaks > 0" type="success" size="small">
          {{ selectedPeaks }} selected
        </el-tag>
      </div>
      <div class="toolbar-right">
        <el-switch v-model="showLabels" active-text="Labels" size="small" />
        <el-button size="small" :icon="Download" @click="$emit('export')" />
      </div>
    </template>
  </BaseEChartsViewer>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { EChartsOption } from 'echarts'
import { Download } from '@element-plus/icons-vue'
import type { TableData, SelectionState } from '@/types/visualization'
import BaseEChartsViewer from './BaseEChartsViewer.vue'

interface Props {
  data: TableData | null
  config?: Record<string, any>
  selection?: SelectionState | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  selectionChange: [selection: SelectionState]
  export: []
  peakClick: [peak: any]
}>()

const baseViewer = ref<InstanceType<typeof BaseEChartsViewer>>()
const loading = ref(false)
const showLabels = ref(false)

const mzColumn = computed(() => props.config?.mzColumn || 'mz')
const intensityColumn = computed(() => props.config?.intensityColumn || 'intensity')

const peakCount = computed(() => props.data?.rows.length || 0)
const selectedPeaks = computed(() => props.selection?.selectedIndices.size || 0)

function getSpectrumData() {
  if (!props.data) return []

  return props.data.rows.map((row, index) => {
    const mz = typeof row[mzColumn.value] === 'number'
      ? row[mzColumn.value] as number
      : parseFloat(String(row[mzColumn.value]))
    const intensity = typeof row[intensityColumn.value] === 'number'
      ? row[intensityColumn.value] as number
      : parseFloat(String(row[intensityColumn.value]))

    return {
      value: [mz, intensity],
      index,
      mz,
      intensity,
    }
  }).filter(d => !isNaN(d.value[0]) && !isNaN(d.value[1]))
}

function updateChart() {
  if (!baseViewer.value) return
  const chartInstance = baseViewer.value.chart
  if (!chartInstance) return

  const data = getSpectrumData()
  if (data.length === 0) {
    chartInstance.clear()
    return
  }

  const selectedIndices = baseViewer.value.getSelectedItems?.() || new Set<number>()
  const selectedData = data.filter(d => selectedIndices.has(d.index))
  const unselectedData = data.filter(d => !selectedIndices.has(d.index))

  const option: EChartsOption = {
    grid: { left: 60, right: 40, top: 40, bottom: 60 },
    tooltip: {
      formatter: (params: any) => {
        const d = params.data
        return `m/z: ${d.mz.toFixed(4)}<br/>Intensity: ${d.intensity.toFixed(0)}`
      },
    },
    xAxis: {
      type: 'value',
      name: 'm/z',
      nameLocation: 'middle',
      nameGap: 30,
      scale: true,
    },
    yAxis: {
      type: 'value',
      name: 'Intensity',
      nameLocation: 'middle',
      nameGap: 40,
      scale: true,
    },
    series: [
      {
        name: 'Selected',
        type: 'line',
        data: selectedData,
        itemStyle: { color: '#e74c3c' },
        lineStyle: { width: 2 },
        showSymbol: true,
        symbolSize: 6,
        label: {
          show: showLabels.value && selectedData.length < 50,
          formatter: (params: any) => params.data.mz.toFixed(2),
          fontSize: 9,
        },
      },
      {
        name: 'Peaks',
        type: 'line',
        data: unselectedData,
        itemStyle: { color: '#3498db' },
        lineStyle: { width: 1 },
        showSymbol: false,
      },
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: 0, filterMode: 'none' },
      { type: 'slider', xAxisIndex: 0, bottom: 10 },
    ],
  }

  chartInstance.setOption(option, true)
}

function onChartReady(chart: any) {
  chart.on('click', (params: any) => {
    if (params.data && typeof params.data.index === 'number') {
      emit('peakClick', params.data)
      const idx = params.data.index
      const selectedItems = baseViewer.value?.getSelectedItems?.() || new Set<number>()
      if (selectedItems.has(idx)) {
        baseViewer.value?.removeSelection?.(idx)
      } else {
        baseViewer.value?.addSelection?.(idx)
      }
      updateChart()
    }
  })

  updateChart()
}

function handleSelectionChange(selection: any) {
  emit('selectionChange', selection)
  updateChart()
}

watch(() => props.data, () => updateChart(), { deep: true })
watch(() => props.selection, () => updateChart(), { deep: true })
watch(showLabels, () => updateChart())
</script>

<script lang="ts">
export default {
  name: 'SpectrumViewer'
}
</script>

<style scoped>
.toolbar-left, .toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
