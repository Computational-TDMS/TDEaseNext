<template>
  <BaseEChartsViewer
    ref="baseViewer"
    :edit-mode="false"
    :loading="loading"
    selection-label="cells"
    @chart-ready="onChartReady"
    @selection-change="handleSelectionChange"
  >
    <!-- Toolbar -->
    <template #toolbar="{ toggleFullscreen }">
      <div class="toolbar-left">
        <el-tag v-if="data?.totalRows" type="info" size="small">
          {{ data.totalRows }} rows × {{ columnCount }} columns
        </el-tag>
        <el-tag v-if="samplingApplied" type="warning" size="small">
          Sampled: {{ renderedPoints }} / {{ originalPoints }}
        </el-tag>
      </div>
      <div class="toolbar-right">
        <el-button
          size="small"
          :icon="FullScreen"
          @click="toggleFullscreen"
          circle
        />
        <el-button
          size="small"
          :icon="Download"
          @click="$emit('export')"
        />
      </div>
    </template>
  </BaseEChartsViewer>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { EChartsOption } from 'echarts'
import { FullScreen, Download } from '@element-plus/icons-vue'
import type { TableData, SelectionState, HeatmapConfig } from '@/types/visualization'
import { COLOR_SCHEMES } from '@/types/visualization'
import BaseEChartsViewer from './BaseEChartsViewer.vue'

interface Props {
  data: TableData | null
  config?: Partial<HeatmapConfig>
  selection?: SelectionState | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  selectionChange: [selection: SelectionState]
  export: []
}>()

// Refs
const baseViewer = ref<InstanceType<typeof BaseEChartsViewer>>()
const loading = ref(false)
const selectedCells = ref<{ row: string; column: string }[]>([])
const renderedPoints = ref(0)

// Config with defaults
const config = computed(() => ({
  rowColumn: props.config?.rowColumn || 'row',
  columnColumn: props.config?.columnColumn || 'column',
  valueColumn: props.config?.valueColumn || 'value',
  colorScheme: props.config?.colorScheme || 'viridis',
  showRowLabels: props.config?.showRowLabels ?? true,
  showColumnLabels: props.config?.showColumnLabels ?? true,
  clusteringEnabled: props.config?.clusteringEnabled ?? false,
  missingValueColor: props.config?.missingValueColor || '#d3d3d3',
}))

// Computed
const originalPoints = computed(() => props.data?.rows.length || 0)
const samplingApplied = computed(() => renderedPoints.value < originalPoints.value)

const columnCount = computed(() => {
  if (!props.data) return 0
  const colSet = new Set<string>()
  props.data.rows.forEach(row => {
    const colVal = row[config.value.columnColumn]
    if (typeof colVal === 'string') colSet.add(colVal)
  })
  return colSet.size || 1
})

// Get color scheme colors
function getColorList(): string[] {
  const scheme = COLOR_SCHEMES.find(c => c.id === config.value.colorScheme)
  return scheme?.colors || COLOR_SCHEMES[0].colors
}

// Process data into heatmap format
function getHeatmapData(): { name: string; value: [string, string, number | null] }[] {
  if (!props.data || props.data.rows.length === 0) return []

  const data = props.data.rows.map((row, index) => {
    const rowLabel = String(row[config.value.rowColumn] || `Row${index}`)
    const colLabel = props.config?.columnColumn
      ? String(row[props.config.columnColumn] || `Col${index}`)
      : `Col${index}`
    const cellValue = row[config.value.valueColumn]

    let numericValue: number | null = null
    if (typeof cellValue === 'number') {
      numericValue = cellValue
    } else if (typeof cellValue === 'string') {
      const parsed = parseFloat(cellValue)  
      numericValue = isNaN(parsed) ? null : parsed
    }

    return {
      name: `${rowLabel}-${colLabel}`,
      value: [rowLabel, colLabel, numericValue] as [string, string, number | null],
    }
  })

  renderedPoints.value = data.length
  return data
}

// Get unique row and column labels
function getAxisLabels() {
  const rows = new Set<string>()
  const columns = new Set<string>()

  props.data?.rows.forEach(row => {
    const rowLabel = String(row[config.value.rowColumn] || '')
    const colLabel = props.config?.columnColumn
      ? String(row[props.config.columnColumn] || '')
      : ''
    if (rowLabel) rows.add(rowLabel)
    if (colLabel) columns.add(colLabel)
  })

  return {
    rows: Array.from(rows).sort(),
    columns: Array.from(columns).sort(),
  }
}

// Get value range for color scale
function getValueRange() {
  let min = Infinity
  let max = -Infinity
  let hasValue = false

  props.data?.rows.forEach(row => {
    const value = row[config.value.valueColumn]
    if (typeof value === 'number') {
      hasValue = true
      if (value < min) min = value
      if (value > max) max = value
    } else if (typeof value === 'string') {
      const parsed = parseFloat(value)
      if (!isNaN(parsed)) {
        hasValue = true
        if (parsed < min) min = parsed
        if (parsed > max) max = parsed
      }
    }
  })

  if (!hasValue) return { min: 0, max: 1 }
  return { min, max }
}

function updateChart() {
  if (!baseViewer.value) return

  const chartInstance = baseViewer.value.chart
  if (!chartInstance) return
  // Already handled above

  const heatmapData = getHeatmapData()
  const { rows, columns } = getAxisLabels()
  const { min, max } = getValueRange()
  const colors = getColorList()

  if (heatmapData.length === 0) {
    if (baseViewer.value?.chart) {
      baseViewer.value.chart.clear()
    }
    return
  }
  const option: EChartsOption = {
    xAxis: {
      type: 'category',
      data: columns,
      splitArea: { show: true },
      name: config.value.showColumnLabels ? undefined : '',
      nameLocation: 'middle',
      nameGap: 30,
      axisLabel: {
        rotate: config.value.showColumnLabels ? 45 : 0,
        fontSize: 10,
      },
    },
    yAxis: {
      type: 'category',
      data: rows,
      splitArea: { show: true },
      name: config.value.showRowLabels ? undefined : '',
      nameLocation: 'middle',
      nameGap: 80,
      axisLabel: {
        fontSize: 10,
      },
    },
    visualMap: {
      show: true,
      min: min,
      max: max,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      top: 0,
      inRange: {
        color: colors,
      },
      text: ['High', 'Low'],
    },
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: 0,
        filterMode: 'none',
      },
      {
        type: 'inside',
        yAxisIndex: 0,
        filterMode: 'none',
      },
    ],
    series: [
      {
        name: 'Heatmap',
        type: 'heatmap',
        data: heatmapData,
        label: {
          show: heatmapData.length < 100,
          fontSize: 9,
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
        itemStyle: {
          color: (params: any) => {
            const value = params.data?.value?.[2]
            if (value === null || value === undefined) {
              return config.value.missingValueColor
            }
            return '' as string // 让 ECharts 使用默认颜色
          },
        },
      },
    ],
  }

  baseViewer.value.setOption(option, true)
}

function onChartReady(chart: any) {
  // Handle cell click for selection
  chart.on('click', (params: any) => {
    if (params.data) {
      const [row, col] = params.data.value
      const cellKey = `${row}-${col}`

      const existingIdx = selectedCells.value.findIndex(
        c => `${c.row}-${c.column}` === cellKey
      )

      if (existingIdx >= 0) {
        selectedCells.value.splice(existingIdx, 1)
      } else {
        selectedCells.value.push({ row, column: col })
      }

      emitSelectionChange()
      updateChart()
    }
  })

  // Initial render
  updateChart()
}

function emitSelectionChange() {
  // Convert cell selection to row indices
  const rowLabels = getAxisLabels().rows
  const indices = new Set<number>()

  selectedCells.value.forEach(cell => {
    const rowIdx = rowLabels.indexOf(cell.row)
    if (rowIdx >= 0) {
      // Find all rows matching this label
      props.data?.rows.forEach((row, idx) => {
        if (String(row[config.value.rowColumn]) === cell.row) {
          indices.add(idx)
        }
      })
    }
  })

  emit('selectionChange', {
    selectedIndices: indices,
    filterCriteria: [],
    brushRegion: null,
  })
}

function handleSelectionChange(selection: any) {
  emit('selectionChange', selection)
}

// Watch for data changes
watch(() => props.data, () => {
  updateChart()
}, { deep: true })

watch(() => props.config, () => {
  updateChart()
}, { deep: true })

watch(() => props.selection, (newSelection) => {
  if (newSelection && baseViewer.value) {
    updateChart()
  }
}, { deep: true })
</script>

<script lang="ts">
export default {
  name: 'HeatmapViewer'
}
</script>

<style scoped>
.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
