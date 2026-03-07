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
        <el-tag v-if="peakCount > 0" type="info" size="small">
          {{ mzColumn }} / {{ intensityColumn }}
        </el-tag>
        <el-tag v-if="isFilteredBySelection" type="warning" size="small">
          Filtered: {{ visiblePeakCount }} / {{ peakCount }}
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
const localSelectedCount = ref(0)
const isSyncingExternalSelection = ref(false)
const hasRenderedOnce = ref(false)

const resolvedColumns = computed(() => {
  const cols = props.data?.columns || []
  const findByName = (patterns: string[]) => cols.find((col) => {
    const name = col.name.toLowerCase()
    return patterns.some((p) => name.includes(p))
  })?.id

  const mzCandidate =
    props.config?.mzColumn ||
    findByName(['mz', 'm/z', 'mass', 'monomass']) ||
    cols[0]?.id ||
    'mz'
  const intensityCandidate =
    props.config?.intensityColumn ||
    findByName(['intensity', 'apexintensity', 'abundance', 'height']) ||
    cols[1]?.id ||
    cols[0]?.id ||
    'intensity'

  return {
    mz: mzCandidate,
    intensity: intensityCandidate,
  }
})
const mzColumn = computed(() => resolvedColumns.value.mz)
const intensityColumn = computed(() => resolvedColumns.value.intensity)

const peakCount = computed(() => props.data?.rows.length || 0)
const selectedPeaks = computed(() => localSelectedCount.value)
const upstreamSelection = computed(() => props.selection?.selectedIndices || new Set<number>())
const isFilteredBySelection = computed(() => upstreamSelection.value.size > 0)

function getSpectrumData() {
  if (!props.data) return []

  const allData = props.data.rows.map((row, index) => {
    const mz = typeof row[mzColumn.value] === 'number'
      ? row[mzColumn.value] as number
      : parseFloat(String(row[mzColumn.value]))
    const intensity = typeof row[intensityColumn.value] === 'number'
      ? row[intensityColumn.value] as number
      : parseFloat(String(row[intensityColumn.value]))

    return {
      index,
      mz,
      intensity,
    }
  }).filter(d => !isNaN(d.mz) && !isNaN(d.intensity))

  if (!isFilteredBySelection.value) {
    return allData
  }

  const filtered = allData.filter((d) => upstreamSelection.value.has(d.index))
  // Upstream and local row indices may diverge for some file formats; avoid blank canvas.
  return filtered.length > 0 ? filtered : allData
}
const visiblePeakCount = computed(() => getSpectrumData().length)

function updateChart() {
  if (!baseViewer.value) return
  const chart = baseViewer.value.chart
  if (!chart) return

  const data = getSpectrumData()
  if (data.length === 0) {
    // Guard against transient empty updates after successful render.
    if (hasRenderedOnce.value && (props.data?.rows?.length || 0) > 0) {
      return
    }
    chart.clear()
    return
  }

  const selectedIndices = baseViewer.value.getSelectedItems?.() || new Set<number>()
  const selectedData = data.filter(d => selectedIndices.has(d.index))
  const unselectedData = data.filter(d => !selectedIndices.has(d.index))

  const series: any[] = [
    {
      name: 'Selected',
      type: 'custom',
      coordinateSystem: 'cartesian2d',
      renderItem: (_params: any, api: any) => {
        const mz = api.value(0)
        const inten = api.value(1)
        const p1 = api.coord([mz, 0])
        const p2 = api.coord([mz, inten])
        const style = {
          stroke: '#f56c6c',
          lineWidth: 2,
          opacity: 1,
        }
        return { type: 'line', shape: { x1: p1[0], y1: p1[1], x2: p2[0], y2: p2[1] }, style }
      },
      data: selectedData.map(d => ({ ...d, value: [d.mz, d.intensity, d.index] })),
      encode: { x: 0, y: 1, tooltip: [0, 1], itemName: 2 },
    },
    {
      name: 'Peaks',
      type: 'custom',
      coordinateSystem: 'cartesian2d',
      renderItem: (_params: any, api: any) => {
        const mz = api.value(0)
        const inten = api.value(1)
        const p1 = api.coord([mz, 0])
        const p2 = api.coord([mz, inten])
        const style = {
          stroke: '#409eff',
          lineWidth: 1,
          opacity: 0.85,
        }
        return { type: 'line', shape: { x1: p1[0], y1: p1[1], x2: p2[0], y2: p2[1] }, style }
      },
      data: unselectedData.map(d => ({ ...d, value: [d.mz, d.intensity, d.index] })),
      encode: { x: 0, y: 1, tooltip: [0, 1], itemName: 2 },
    },
  ]

  if (showLabels.value && selectedData.length > 0 && selectedData.length < 200) {
    series.push({
      name: 'Labels',
      type: 'scatter',
      data: selectedData.map(d => ({ ...d, value: [d.mz, d.intensity] })),
      symbolSize: 4,
      itemStyle: { color: '#f56c6c' },
      label: {
        show: true,
        formatter: (p: any) => Number(p.data?.mz).toFixed(2),
        fontSize: 9,
        position: 'top',
      },
    })
  }

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
      min: 0,
    },
    series: series as any,
    dataZoom: [
      { type: 'inside', xAxisIndex: 0, filterMode: 'none' },
      { type: 'slider', xAxisIndex: 0, bottom: 10 },
    ],
  }

  chart.setOption(option, true)
  hasRenderedOnce.value = true
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
  if (isSyncingExternalSelection.value) {
    localSelectedCount.value = selection?.selectedIndices?.size || 0
    return
  }
  localSelectedCount.value = selection?.selectedIndices?.size || 0
  emit('selectionChange', selection)
  updateChart()
}

watch(() => props.data, () => {
  if (!props.data || (props.data.rows?.length || 0) === 0) {
    hasRenderedOnce.value = false
  }
  updateChart()
}, { deep: true })
watch(() => props.selection, (s) => {
  if (!baseViewer.value) return
  isSyncingExternalSelection.value = true
  const current = baseViewer.value.getSelectedItems?.() || new Set<number>()
  const incoming = s?.selectedIndices || new Set<number>()
  const sameSize = current.size === incoming.size
  const sameItems = sameSize && Array.from(incoming).every((idx) => current.has(idx))
  if (!sameItems) {
    baseViewer.value.setSelection?.(Array.from(incoming))
  }
  localSelectedCount.value = incoming.size
  isSyncingExternalSelection.value = false
  updateChart()
}, { deep: true })
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
