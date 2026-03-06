<template>
  <BaseEChartsViewer
    ref="baseViewer"
    :edit-mode="editMode"
    :loading="loading"
    selection-label="features"
    @chart-ready="onChartReady"
    @selection-change="handleSelectionChange"
  >
    <template #toolbar>
      <div class="toolbar-left">
        <el-tag v-if="data?.totalRows" type="info" size="small">
          {{ data.totalRows }} features
        </el-tag>
        <el-tag v-if="selectedFeatures > 0" type="success" size="small">
          {{ selectedFeatures }} selected
        </el-tag>
        <el-tag v-if="samplingApplied" type="warning" size="small">
          Sampled: {{ renderedPoints }} / {{ originalPoints }}
        </el-tag>
      </div>
      <div class="toolbar-right">
        <el-select v-model="localConfig.colorScheme" size="small" style="width: 100px" @change="updateConfig">
          <el-option v-for="scheme in colorSchemes" :key="scheme.id" :label="scheme.name" :value="scheme.id" />
        </el-select>
        <el-button size="small" :icon="Download" @click="$emit('export')" />
      </div>
    </template>

    <template #config>
      <el-row :gutter="12">
        <el-col :span="8">
          <el-form-item label="Start Time">
            <el-select v-model="localConfig.axisMapping.startTime" placeholder="Select" size="small" clearable @change="updateConfig">
              <el-option v-for="col in numericColumns" :key="col.id" :label="col.name" :value="col.id" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="End Time">
            <el-select v-model="localConfig.axisMapping.endTime" placeholder="Select" size="small" clearable @change="updateConfig">
              <el-option v-for="col in numericColumns" :key="col.id" :label="col.name" :value="col.id" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="Mass">
            <el-select v-model="localConfig.axisMapping.mass" placeholder="Select" size="small" clearable @change="updateConfig">
              <el-option v-for="col in numericColumns" :key="col.id" :label="col.name" :value="col.id" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="12">
        <el-col :span="8">
          <el-form-item label="Intensity (Color)">
            <el-select v-model="localConfig.axisMapping.intensity" placeholder="Optional" size="small" clearable @change="updateConfig">
              <el-option v-for="col in numericColumns" :key="col.id" :label="col.name" :value="col.id" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="Max Traces">
            <el-input-number
              v-model="localConfig.maxTraces"
              :min="1000"
              :max="200000"
              :step="1000"
              size="small"
              @change="updateConfig"
            />
          </el-form-item>
        </el-col>
      </el-row>
    </template>
  </BaseEChartsViewer>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { EChartsOption } from 'echarts'
import { Download } from '@element-plus/icons-vue'
import type { TableData, SelectionState } from '@/types/visualization'
import { COLOR_SCHEMES } from '@/types/visualization'
import BaseEChartsViewer from './BaseEChartsViewer.vue'

interface FeatureMapConfig {
  axisMapping: {
    startTime: string
    endTime: string
    mass: string
    intensity?: string
  }
  colorScheme: string
  opacity: number
  maxTraces: number
}

interface Props {
  data: TableData | null
  config?: Partial<FeatureMapConfig>
  selection?: SelectionState | null
  editMode?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  selectionChange: [selection: SelectionState]
  configChange: [config: Partial<FeatureMapConfig>]
  export: []
  featureClick: [feature: any]
}>()

const baseViewer = ref<InstanceType<typeof BaseEChartsViewer>>()
const loading = ref(false)
const renderedPoints = ref(0)
const selectedFeatures = ref(0)
const isSyncingExternalSelection = ref(false)
const hasRenderedOnce = ref(false)

const localConfig = ref<FeatureMapConfig>({
  axisMapping: { startTime: '', endTime: '', mass: '', intensity: '' },
  colorScheme: 'viridis',
  opacity: 0.7,
  maxTraces: 10000,
})

watch(() => props.config, (newConfig) => {
  if (newConfig) Object.assign(localConfig.value, newConfig)
}, { immediate: true, deep: true })

const colorSchemes = COLOR_SCHEMES
const originalPoints = computed(() => props.data?.rows.length || 0)
const samplingApplied = computed(() => {
  return renderedPoints.value > 0 && renderedPoints.value < originalPoints.value
})
const numericColumns = computed(() => {
  const cols = props.data?.columns || []
  if (!props.data || cols.length === 0) return []

  const explicitNumeric = cols.filter(c => c.type === 'number')
  if (explicitNumeric.length > 0) return explicitNumeric

  // Fallback: infer numeric columns from row values when schema type is unavailable.
  return cols.filter((col) => {
    let checked = 0
    let numeric = 0
    for (const row of props.data!.rows) {
      const value = row[col.id]
      if (value === null || value === undefined || value === '') continue
      checked += 1
      if (!isNaN(parseFloat(String(value)))) numeric += 1
      if (checked >= 50) break
    }
    return checked > 0 && numeric / checked >= 0.8
  })
})

function autoDetectAxisMapping() {
  if (!props.data || props.data.columns.length === 0) return
  if (
    localConfig.value.axisMapping.startTime &&
    localConfig.value.axisMapping.endTime &&
    localConfig.value.axisMapping.mass
  ) {
    return
  }

  const candidates = numericColumns.value
  if (candidates.length === 0) return

  const byName = (patterns: string[]) => candidates.find((col) => {
    const lower = col.name.toLowerCase()
    return patterns.some((p) => lower.includes(p))
  })?.id

  const start = byName(['minelutiontime', 'start', 'min_time', 'retention', 'rt', 'time']) || candidates[0]?.id
  const end =
    byName(['maxelutiontime', 'end', 'max_time']) ||
    candidates.find((c) => c.id !== start)?.id ||
    start
  const mass =
    byName(['monomass', 'mass', 'mz']) ||
    candidates.find((c) => c.id !== start && c.id !== end)?.id ||
    candidates[0]?.id
  const intensity = byName(['apexintensity', 'intensity', 'abundance'])

  localConfig.value.axisMapping = {
    ...localConfig.value.axisMapping,
    startTime: localConfig.value.axisMapping.startTime || start || '',
    endTime: localConfig.value.axisMapping.endTime || end || '',
    mass: localConfig.value.axisMapping.mass || mass || '',
    intensity: localConfig.value.axisMapping.intensity || intensity || '',
  }
  emit('configChange', { ...localConfig.value })
}

function getFeatureData() {
  if (
    props.data &&
    (!localConfig.value.axisMapping.startTime ||
      !localConfig.value.axisMapping.endTime ||
      !localConfig.value.axisMapping.mass)
  ) {
    autoDetectAxisMapping()
  }

  if (
    !props.data ||
    !localConfig.value.axisMapping.startTime ||
    !localConfig.value.axisMapping.endTime ||
    !localConfig.value.axisMapping.mass
  ) {
    renderedPoints.value = 0
    return []
  }

  const startCol = localConfig.value.axisMapping.startTime
  const endCol = localConfig.value.axisMapping.endTime
  const massCol = localConfig.value.axisMapping.mass
  const intensity = localConfig.value.axisMapping.intensity

  const parsed = props.data.rows.map((row, index) => {
    const startTime = typeof row[startCol] === 'number'
      ? row[startCol] as number
      : parseFloat(String(row[startCol]))
    const endTime = typeof row[endCol] === 'number'
      ? row[endCol] as number
      : parseFloat(String(row[endCol]))
    const mass = typeof row[massCol] === 'number'
      ? row[massCol] as number
      : parseFloat(String(row[massCol]))
    const intensityValue = intensity
      ? (typeof row[intensity] === 'number'
          ? row[intensity] as number
          : parseFloat(String(row[intensity]))
      )
      : 1

    let s = startTime
    let e = endTime
    if (!isNaN(s) && !isNaN(e) && e < s) {
      const tmp = s
      s = e
      e = tmp
    }

    return { startTime: s, endTime: e, mass, intensity: intensityValue, index }
  }).filter(d => !isNaN(d.startTime) && !isNaN(d.endTime) && !isNaN(d.mass))

  const total = parsed.length
  if (total === 0) {
    renderedPoints.value = 0
    return []
  }

  const maxTraces = Math.max(1, localConfig.value.maxTraces || 10000)
  if (total > maxTraces) {
    const step = Math.ceil(total / maxTraces)
    const sampled = parsed.filter((_, i) => i % step === 0)
    renderedPoints.value = sampled.length
    return sampled
  }

  renderedPoints.value = total
  return parsed
}

function getIntensityRange() {
  const intensityCol = localConfig.value.axisMapping.intensity
  if (!intensityCol) return null
  let min = Infinity, max = -Infinity
  props.data?.rows.forEach(row => {
    const val = row[intensityCol]
    const numeric = typeof val === 'number' ? val : parseFloat(String(val))
    if (!isNaN(numeric)) {
      if (numeric < min) min = numeric
      if (numeric > max) max = numeric
    }
  })
  return min === Infinity ? null : { min, max }
}
function updateChart() {
  if (!baseViewer.value) return

  const chart = baseViewer.value.chart
  if (!chart) return
  const data = getFeatureData()
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
  const intensityRange = getIntensityRange()

  const hasIntensity = Boolean(localConfig.value.axisMapping.intensity && intensityRange)
  const option: EChartsOption = {
    grid: { left: 60, right: 40, top: 40, bottom: 60 },
    tooltip: {
      formatter: (params: any) => {
        const d = params.data
        if (!d) return ''
        const s = typeof d.startTime === 'number' ? d.startTime : d.value?.[0]
        const e = typeof d.endTime === 'number' ? d.endTime : d.value?.[1]
        const m = typeof d.mass === 'number' ? d.mass : d.value?.[2]
        const inten = typeof d.intensity === 'number' ? d.intensity : d.value?.[3]
        let html = `Start: ${Number(s).toFixed(2)}<br/>End: ${Number(e).toFixed(2)}<br/>Mass: ${Number(m).toFixed(4)}`
        if (hasIntensity && inten !== undefined && !isNaN(Number(inten))) {
          html += `<br/>Intensity: ${Number(inten).toFixed(0)}`
        }
        return html
      },
    },
    xAxis: {
      type: 'value',
      name: 'Time',
      nameLocation: 'middle',
      nameGap: 30,
      scale: true,
    },
    yAxis: {
      type: 'value',
      name: 'Mass',
      nameLocation: 'middle',
      nameGap: 40,
      scale: true,
    },
    visualMap: hasIntensity ? {
      type: 'continuous',
      min: intensityRange!.min,
      max: intensityRange!.max,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      top: 0,
      inRange: { color: colorSchemes.find(c => c.id === localConfig.value.colorScheme)?.colors || colorSchemes[0].colors },
    } : undefined,
    series: [
      {
        name: 'Selected',
        type: 'custom',
        coordinateSystem: 'cartesian2d',
        renderItem: (_params: any, api: any) => {
          const s = api.value(0)
          const e = api.value(1)
          const m = api.value(2)
          const p1 = api.coord([s, m])
          const p2 = api.coord([e, m])
          const style = {
            stroke: hasIntensity ? (api.visual('color') as string) : '#f56c6c',
            lineWidth: 3,
            opacity: 1,
            shadowBlur: 6,
            shadowColor: 'rgba(0,0,0,0.25)',
          }
          return { type: 'line', shape: { x1: p1[0], y1: p1[1], x2: p2[0], y2: p2[1] }, style }
        },
        data: selectedData.map(d => ({
          value: [d.startTime, d.endTime, d.mass, d.intensity, d.index],
          ...d,
        })),
        encode: { x: [0, 1], y: 2, tooltip: [0, 1, 2, 3], itemName: 4 },
      },
      {
        name: 'Features',
        type: 'custom',
        coordinateSystem: 'cartesian2d',
        renderItem: (_params: any, api: any) => {
          const s = api.value(0)
          const e = api.value(1)
          const m = api.value(2)
          const p1 = api.coord([s, m])
          const p2 = api.coord([e, m])
          const style = {
            stroke: hasIntensity ? (api.visual('color') as string) : '#409eff',
            lineWidth: 2,
            opacity: localConfig.value.opacity,
          }
          return { type: 'line', shape: { x1: p1[0], y1: p1[1], x2: p2[0], y2: p2[1] }, style }
        },
        data: unselectedData.map(d => ({
          value: [d.startTime, d.endTime, d.mass, d.intensity, d.index],
          ...d,
        })),
        encode: { x: [0, 1], y: 2, tooltip: [0, 1, 2, 3], itemName: 4 },
      },
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: 0, filterMode: 'none' },
      { type: 'inside', yAxisIndex: 0, filterMode: 'none' },
      { type: 'slider', xAxisIndex: 0, bottom: 10 },
    ],
    brush: {
      toolbox: ['rect', 'clear'],
      xAxisIndex: 'all',
      yAxisIndex: 'all',
      brushMode: 'single'
    }
  }

  chart.setOption(option, true)
  hasRenderedOnce.value = true
}

function onChartReady(chart: any) {
  chart.on('brushEnd', (params: any) => {
    const areas = params?.areas || []
    if (!areas.length) return
    const area = areas[0]
    const coordRange = area?.coordRange
    if (!coordRange || coordRange.length !== 2) return

    const xMin = Math.min(coordRange[0][0], coordRange[1][0])
    const xMax = Math.max(coordRange[0][0], coordRange[1][0])
    const yMin = Math.min(coordRange[0][1], coordRange[1][1])
    const yMax = Math.max(coordRange[0][1], coordRange[1][1])

    const data = getFeatureData()
    const nextSelected = new Set<number>()
    data.forEach((item) => {
      const inTime = item.startTime <= xMax && item.endTime >= xMin
      const inMass = item.mass >= yMin && item.mass <= yMax
      if (inTime && inMass) {
        nextSelected.add(item.index)
      }
    })

    baseViewer.value?.clearSelection?.()
    nextSelected.forEach((idx) => baseViewer.value?.addSelection?.(idx))
    selectedFeatures.value = nextSelected.size
    updateChart()
  })

  chart.on('dblclick', () => {
    baseViewer.value?.clearSelection?.()
    selectedFeatures.value = 0
    updateChart()
  })

  chart.on('click', (params: any) => {
    if (params.data && typeof params.data.index === 'number') {
      emit('featureClick', params.data)
      const idx = params.data.index
      const selectedItems = baseViewer.value?.getSelectedItems?.() || new Set<number>()
      if (selectedItems.has(idx)) {
        baseViewer.value?.removeSelection?.(idx)
      } else {
        baseViewer.value?.addSelection?.(idx)
      }
      selectedFeatures.value = baseViewer.value?.getSelectedItems?.().size || 0
      updateChart()
    }
  })

  updateChart()
}

function handleSelectionChange(selection: any) {
  if (isSyncingExternalSelection.value) {
    selectedFeatures.value = selection?.selectedIndices?.size || 0
    return
  }
  selectedFeatures.value = selection?.selectedIndices?.size || 0
  emit('selectionChange', selection)
  updateChart()
}

function updateConfig() {
  emit('configChange', { ...localConfig.value })
  updateChart()
}

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
  if (incoming.size) {
    selectedFeatures.value = incoming.size
  } else {
    selectedFeatures.value = 0
  }
  isSyncingExternalSelection.value = false
  updateChart()
}, { deep: true })
watch(
  () => props.data,
  () => {
    if (!props.data || (props.data.rows?.length || 0) === 0) {
      hasRenderedOnce.value = false
    }
    autoDetectAxisMapping()
    updateChart()
  },
  { deep: true, immediate: true }
)
</script>

<script lang="ts">
export default {
  name: 'FeatureMapViewer'
}
</script>

<style scoped>
.toolbar-left, .toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
