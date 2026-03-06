<template>
  <BaseEChartsViewer
    ref="baseViewer"
    :edit-mode="editMode"
    :loading="loading"
    selection-label="points"
    @chart-ready="onChartReady"
    @selection-change="handleSelectionChange"
  >
    <!-- Toolbar -->
    <template #toolbar="{ fullscreen, toggleFullscreen }">
      <div class="toolbar-left">
        <el-tag v-if="samplingApplied" type="warning" size="small">
          Sampled: {{ renderedPoints }} / {{ originalPoints }}
        </el-tag>
        <el-tag v-else-if="data?.totalRows" type="info" size="small">
          {{ data.totalRows }} points
        </el-tag>
      </div>
      <div class="toolbar-right">
        <el-select
          v-model="localConfig.colorScheme"
          size="small"
          style="width: 100px"
          @change="updateConfig"
        >
          <el-option
            v-for="scheme in colorSchemes"
            :key="scheme.id"
            :label="scheme.name"
            :value="scheme.id"
          />
        </el-select>
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

    <!-- Configuration Panel (Edit Mode) -->
    <template #config>
      <el-row :gutter="12">
        <el-col :span="6">
          <el-form-item label="X Axis">
            <el-select
              v-model="localConfig.axisMapping.x"
              placeholder="Select"
              size="small"
              clearable
              @change="updateConfig"
            >
              <el-option
                v-for="col in numericColumns"
                :key="col.id"
                :label="col.name"
                :value="col.id"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="Y Axis">
            <el-select
              v-model="localConfig.axisMapping.y"
              placeholder="Select"
              size="small"
              clearable
              @change="updateConfig"
            >
              <el-option
                v-for="col in numericColumns"
                :key="col.id"
                :label="col.name"
                :value="col.id"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="Color By">
            <el-select
              v-model="localConfig.axisMapping.color"
              placeholder="None"
              size="small"
              clearable
              @change="updateConfig"
            >
              <el-option
                v-for="col in allColumns"
                :key="col.id"
                :label="col.name"
                :value="col.id"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="Size By">
            <el-select
              v-model="localConfig.axisMapping.size"
              placeholder="None"
              size="small"
              clearable
              @change="updateConfig"
            >
              <el-option
                v-for="col in numericColumns"
                :key="col.id"
                :label="col.name"
                :value="col.id"
              />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
    </template>

    <!-- Chart will be rendered by BaseEChartsViewer -->
  </BaseEChartsViewer>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { EChartsOption } from 'echarts'
import { FullScreen, Download } from '@element-plus/icons-vue'
import type { TableData, SelectionState, ScatterConfig } from '@/types/visualization'
import { COLOR_SCHEMES } from '@/types/visualization'
import BaseEChartsViewer from './BaseEChartsViewer.vue'

interface Props {
  data: TableData | null
  config?: Partial<ScatterConfig>
  selection?: SelectionState | null
  editMode?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  selectionChange: [selection: SelectionState]
  configChange: [config: Partial<ScatterConfig>]
  export: []
}>()

// Refs
const baseViewer = ref<InstanceType<typeof BaseEChartsViewer>>()
const chartContainer = ref<HTMLElement>()

// State
const loading = ref(false)
const renderedPoints = ref(0)

// Local config with defaults
const localConfig = ref<Required<ScatterConfig>>({
  axisMapping: { x: '', y: '', z: '', color: '', size: '' },
  colorScheme: 'viridis',
  showLegend: true,
  symbolSize: 8,
  symbolType: 'circle',
})

const colorSchemes = COLOR_SCHEMES

// Initialize config from props
watch(() => props.config, (newConfig) => {
  if (newConfig) {
    if (newConfig.axisMapping) {
      Object.assign(localConfig.value.axisMapping, newConfig.axisMapping)
    }
    if (newConfig.colorScheme) localConfig.value.colorScheme = newConfig.colorScheme
    if (newConfig.showLegend !== undefined) localConfig.value.showLegend = newConfig.showLegend
    if (newConfig.symbolSize) localConfig.value.symbolSize = newConfig.symbolSize
    if (newConfig.symbolType) localConfig.value.symbolType = newConfig.symbolType
  }
}, { immediate: true, deep: true })

// Auto-detect columns if not set
watch(() => props.data, (newData) => {
  if (newData && newData.columns.length > 0 && !localConfig.value.axisMapping.x) {
    const numericCols = newData.columns.filter(c => c.type === 'number')
    if (numericCols.length >= 2) {
      localConfig.value.axisMapping.x = numericCols[0].id
      localConfig.value.axisMapping.y = numericCols[1].id
    }
  }
}, { immediate: true })

// Computed
const originalPoints = computed(() => props.data?.rows.length || 0)
const samplingApplied = computed(() => renderedPoints.value < originalPoints.value)

const numericColumns = computed(() => props.data?.columns.filter(c => c.type === 'number') || [])
const allColumns = computed(() => props.data?.columns || [])

// Get color for value
function getColorForValue(value: number, min: number, max: number): string {
  const colors = colorSchemes.find(c => c.id === localConfig.value.colorScheme)?.colors || colorSchemes[0].colors
  if (min === max) return colors[Math.floor(colors.length / 2)]
  const normalized = (value - min) / (max - min)
  const idx = Math.min(Math.floor(normalized * colors.length), colors.length - 1)
  return colors[idx]
}

// Get color list for visualMap
function getColorList(): string[] {
  return colorSchemes.find(c => c.id === localConfig.value.colorScheme)?.colors || colorSchemes[0].colors
}

// Get scatter data
function getScatterData(): { x: number; y: number; colorValue?: number; sizeValue?: number; index: number }[] {
  if (!props.data || !localConfig.value.axisMapping.x || !localConfig.value.axisMapping.y) return []

  const xCol = localConfig.value.axisMapping.x
  const yCol = localConfig.value.axisMapping.y
  const colorCol = localConfig.value.axisMapping.color
  const sizeCol = localConfig.value.axisMapping.size

  const data = props.data.rows
    .map((row, index) => {
      const x = typeof row[xCol] === 'number' ? row[xCol] as number : parseFloat(String(row[xCol]))
      const y = typeof row[yCol] === 'number' ? row[yCol] as number : parseFloat(String(row[yCol]))
      if (isNaN(x) || isNaN(y)) return null

      const colorValue = colorCol ? (typeof row[colorCol] === 'number' ? row[colorCol] as number : parseFloat(String(row[colorCol]))) : undefined
      const sizeValue = sizeCol ? (typeof row[sizeCol] === 'number' ? row[sizeCol] as number : parseFloat(String(row[sizeCol]))) : undefined

      return { x, y, colorValue: colorValue && !isNaN(colorValue) ? colorValue : undefined, sizeValue: sizeValue && !isNaN(sizeValue) ? sizeValue : undefined, index }
    })
    .filter((d): d is NonNullable<typeof d> => d !== null)

  // Apply sampling for large datasets
  if (data.length > 10000) {
    const step = Math.ceil(data.length / 10000)
    renderedPoints.value = data.length
    return data.filter((_, i) => i % step === 0)
  }

  renderedPoints.value = data.length
  return data
}

// Get color column range
function getColorRange() {
  if (!localConfig.value.axisMapping.color) return null
  let min = Infinity, max = -Infinity
  props.data?.rows.forEach(row => {
    const val = row[localConfig.value.axisMapping.color!]
    if (typeof val === 'number' && !isNaN(val)) {
      if (val < min) min = val
      if (val > max) max = val
    }
  })
  return min === Infinity ? null : { min, max }
}

function updateChart() {
  if (!baseViewer.value) return

  const chartInstance = baseViewer.value.chart
  const chart = chartInstance.value
  if (!chart) return

  const data = getScatterData()

  if (data.length === 0) {
    chart.clear()
    return
  }

  const selectedItems = baseViewer.value.getSelectedItems?.() || new Set<number>()
  const selectedData = data.filter(p => selectedItems.has(p.index))
  const unselectedData = data.filter(p => !selectedItems.has(p.index))
  const colorRange = getColorRange()

  const series: any[] = [
    {
      name: 'Selected',
      type: 'scatter',
      data: selectedData.map(p => ({
        ...p,
        value: [p.x, p.y],
      })),
      symbolSize: (params: any) => {
        if (localConfig.value.axisMapping.size && params.sizeValue !== undefined) {
          const max = Math.max(...data.map(d => d.sizeValue || 1))
          const min = Math.min(...data.map(d => d.sizeValue || 1))
          const size = localConfig.value.axisMapping.size ? Math.max(3, Math.min(20, ((params.sizeValue - min) / (max - min || 1)) * 15 + 5)) : localConfig.value.symbolSize
          return typeof localConfig.value.symbolSize === 'number' ? localConfig.value.symbolSize : size
        }
        return typeof localConfig.value.symbolSize === 'number' ? localConfig.value.symbolSize : 8
      },
      itemStyle: { color: '#f56c6c', borderColor: '#fff', borderWidth: 1 },
    },
    {
      name: 'Points',
      type: 'scatter',
      data: unselectedData.map(p => ({
        ...p,
        value: [p.x, p.y],
      })),
      symbolSize: (params: any) => {
        if (localConfig.value.axisMapping.size && params.sizeValue !== undefined) {
          const max = Math.max(...data.map(d => d.sizeValue || 1))
          const min = Math.min(...data.map(d => d.sizeValue || 1))
          const size = localConfig.value.axisMapping.size ? Math.max(3, Math.min(20, ((params.sizeValue - min) / (max - min || 1)) * 15 + 5)) : localConfig.value.symbolSize
          return typeof localConfig.value.symbolSize === 'number' ? localConfig.value.symbolSize : size
        }
        return typeof localConfig.value.symbolSize === 'number' ? localConfig.value.symbolSize : 8
      },
      itemStyle: (params: any) => {
        if (localConfig.value.axisMapping.color && params.colorValue !== undefined && colorRange) {
          return { color: getColorForValue(params.colorValue, colorRange.min, colorRange.max) }
        }
        return { color: '#409eff', opacity: 0.7 }
      },
    },
  ]

  const visualMapConfig: any = {
    show: false,
  }
  if (localConfig.value.axisMapping.color && colorRange) {
    visualMapConfig.show = true
    visualMapConfig.min = colorRange.min
    visualMapConfig.max = colorRange.max
    visualMapConfig.calculable = true
    visualMapConfig.orient = 'horizontal'
    visualMapConfig.left = 'center'
    visualMapConfig.top = 0
    visualMapConfig.inRange = { color: getColorList() }
  }

  const option: EChartsOption = {
    grid: { left: 60, right: 50, top: localConfig.value.axisMapping.color && colorRange ? 50 : 20, bottom: 60 },
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        const d = params.data
        if (!d) return ''
        let html = `X: ${d.x?.toFixed(2)}<br/>Y: ${d.y?.toFixed(2)}`
        if (localConfig.value.axisMapping.color && d.colorValue !== undefined) html += `<br/>Color: ${d.colorValue.toFixed(2)}`
        if (localConfig.value.axisMapping.size && d.sizeValue !== undefined) html += `<br/>Size: ${d.sizeValue.toFixed(2)}`
        return html
      },
    },
    legend: localConfig.value.showLegend ? { data: ['Selected', 'Points'], top: 0, right: 0 } : undefined,
    xAxis: { type: 'value', name: localConfig.value.axisMapping.x || 'X', nameLocation: 'middle', nameGap: 30, scale: true },
    yAxis: { type: 'value', name: localConfig.value.axisMapping.y || 'Y', nameLocation: 'middle', nameGap: 40, scale: true },
    visualMap: Object.keys(visualMapConfig).length > 1 ? visualMapConfig : undefined,
    brush: { toolbox: ['rect', 'polygon'], brushLink: 'all' },
    dataZoom: [
      { type: 'inside', xAxisIndex: 0, filterMode: 'none' },
      { type: 'inside', yAxisIndex: 0, filterMode: 'none' },
    ],
    series,
  }

  chart.setOption(option, true)
}

function onChartReady(chart: any) {
  // Set up event handlers
  chart.on('brushEnd', (params: any) => {
    if (params.areas.length === 0) return
    const area = params.areas[0]
    const coordRange = area.coordRange
    if (!coordRange || coordRange.length !== 2) return

    const xMin = coordRange[0][0], xMax = coordRange[1][0]
    const yMin = coordRange[0][1], yMax = coordRange[1][1]

    const data = getScatterData()
    const newSelected = new Set<number>()
    data.forEach(p => {
      if (p.x >= xMin && p.x <= xMax && p.y >= yMin && p.y <= yMax) {
        newSelected.add(p.index)
      }
    })

    // Update base viewer selection
    if (baseViewer.value) {
      baseViewer.value.clearSelection?.()
      newSelected.forEach(idx => {
        baseViewer.value.addSelection?.(idx)
      })
    }
  })

  chart.on('click', (params: any) => {
    if (params.data && typeof params.data.index === 'number') {
      // Toggle selection
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

  // Initial render
  updateChart()
}

function handleSelectionChange(selection: any) {
  emit('selectionChange', selection)
  updateChart()
}

function updateConfig() {
  emit('configChange', {
    axisMapping: { ...localConfig.value.axisMapping },
    colorScheme: localConfig.value.colorScheme,
    showLegend: localConfig.value.showLegend,
    symbolSize: localConfig.value.symbolSize,
    symbolType: localConfig.value.symbolType,
  })
  updateChart()
}

// Watch for data changes
watch(() => props.data, () => {
  updateChart()
}, { deep: true })

watch(() => props.selection, (s) => {
  if (s && baseViewer.value) {
    baseViewer.value.clearSelection?.()
    s.selectedIndices.forEach(idx => {
      baseViewer.value.addSelection?.(idx)
    })
    updateChart()
  }
}, { deep: true })
</script>

<script lang="ts">
export default {
  name: 'ScatterPlotViewer'
}
</script>

<style scoped>
.toolbar-left, .toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
