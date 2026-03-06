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
          <el-form-item label="RT Axis">
            <el-select v-model="localConfig.axisMapping.rt" placeholder="Select" size="small" clearable @change="updateConfig">
              <el-option v-for="col in numericColumns" :key="col.id" :label="col.name" :value="col.id" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="m/z Axis">
            <el-select v-model="localConfig.axisMapping.mz" placeholder="Select" size="small" clearable @change="updateConfig">
              <el-option v-for="col in numericColumns" :key="col.id" :label="col.name" :value="col.id" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="Intensity">
            <el-select v-model="localConfig.axisMapping.intensity" placeholder="Select" size="small" clearable @change="updateConfig">
              <el-option v-for="col in numericColumns" :key="col.id" :label="col.name" :value="col.id" />
            </el-select>
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
    rt: string
    mz: string
    intensity?: string
  }
  colorScheme: string
  pointSize: number
  opacity: number
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

const localConfig = ref<FeatureMapConfig>({
  axisMapping: { rt: '', mz: '', intensity: '' },
  colorScheme: 'viridis',
  pointSize: 8,
  opacity: 0.7,
})

watch(() => props.config, (newConfig) => {
  if (newConfig) Object.assign(localConfig.value, newConfig)
}, { immediate: true, deep: true })

const colorSchemes = COLOR_SCHEMES
const originalPoints = computed(() => props.data?.rows.length || 0)
const samplingApplied = computed(() => renderedPoints.value < originalPoints.value)
const numericColumns = computed(() => props.data?.columns.filter(c => c.type === 'number') || [])

function getFeatureData() {
  if (!props.data || !localConfig.value.axisMapping.rt || !localConfig.value.axisMapping.mz) return []

  const rt = localConfig.value.axisMapping.rt
  const mz = localConfig.value.axisMapping.mz
  const intensity = localConfig.value.axisMapping.intensity

  const data = props.data.rows.map((row, index) => {
    const rtValue = typeof row[rt] === 'number'
      ? row[rt] as number
      : parseFloat(String(row[rt]))
    const mzValue = typeof row[mz] === 'number'
      ? row[mz] as number
      : parseFloat(String(row[mz]))
    const intensityValue = intensity
      ? (typeof row[intensity] === 'number'
          ? row[intensity] as number
          : parseFloat(String(row[intensity]))
      )
      : 1

    return { rt: rtValue, mz: mzValue, intensity: intensityValue, index }
  }).filter(d => !isNaN(d.rt) && !isNaN(d.mz))

  if (data.length > 10000) {
    const step = Math.ceil(data.length / 10000)
    renderedPoints.value = data.length
    return data.filter((_, i) => i % step === 0)
  }

  renderedPoints.value = data.length
  return data
}

function getColorForIntensity(intensity: number, min: number, max: number): string {
  const colors = colorSchemes.find(c => c.id === localConfig.value.colorScheme)?.colors || colorSchemes[0].colors
  if (min === max) return colors[Math.floor(colors.length / 2)]
  const normalized = (intensity - min) / (max - min)
  const idx = Math.min(Math.floor(normalized * colors.length), colors.length - 1)
  return colors[idx]
}

function getIntensityRange() {
  const intensityCol = localConfig.value.axisMapping.intensity
  if (!intensityCol) return null
  let min = Infinity, max = -Infinity
  props.data?.rows.forEach(row => {
    const val = row[intensityCol]
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
  if (!chartInstance?.value) return

  const chart = chartInstance.value
  const data = getFeatureData()
  if (data.length === 0) {
    chart.clear()
    return
  }


  const selectedIndices = baseViewer.value.getSelectedItems?.() || new Set<number>()
  const selectedData = data.filter(d => selectedIndices.has(d.index))
  const unselectedData = data.filter(d => !selectedIndices.has(d.index))
  const intensityRange = getIntensityRange()

  const option: EChartsOption = {
    grid: { left: 60, right: 40, top: 40, bottom: 60 },
    tooltip: {
      formatter: (params: any) => {
        const d = params.data
        let html = `RT: ${d.rt?.toFixed(2)} min<br/>m/z: ${d.mz?.toFixed(4)}`
        if (localConfig.value.axisMapping.intensity && d.intensity !== undefined) {
          html += `<br/>Intensity: ${d.intensity.toFixed(0)}`
        }
        return html
      },
    },
    xAxis: {
      type: 'value',
      name: 'Retention Time (min)',
      nameLocation: 'middle',
      nameGap: 30,
      scale: true,
    },
    yAxis: {
      type: 'value',
      name: 'm/z',
      nameLocation: 'middle',
      nameGap: 40,
      scale: true,
    },
    series: [
      {
        name: 'Selected',
        type: 'scatter',
        data: selectedData.map(d => ({ value: [d.rt, d.mz], ...d })),
        symbolSize: (params: any) => {
          const size = localConfig.value.pointSize || 8
          const intensity = params.data.intensity
          if (intensity !== undefined && intensityRange) {
            return size * (0.5 + 0.5 * (intensity - intensityRange.min) / (intensityRange.max - intensityRange.min))
          }
          return size
        },
        itemStyle: { color: '#e74c3c', borderColor: '#fff', borderWidth: 2 },
      },
      {
        name: 'Features',
        type: 'scatter',
        data: unselectedData.map(d => ({ value: [d.rt, d.mz], ...d })),
        symbolSize: (params: any) => {
          const size = localConfig.value.pointSize || 8
          const intensity = params.data.intensity
          if (intensity !== undefined && intensityRange) {
            return size * (0.5 + 0.5 * (intensity - intensityRange.min) / (intensityRange.max - intensityRange.min))
          }
          return size
        },
        itemStyle: {
          color: (params: any) => {
            if (localConfig.value.axisMapping.intensity && params.data.intensity !== undefined && intensityRange) {
              return getColorForIntensity(params.data.intensity, intensityRange.min, intensityRange.max)
            }
            return '#3498db'
          },
          opacity: localConfig.value.opacity
        } as any,
      },
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: 0, filterMode: 'none' },
      { type: 'inside', yAxisIndex: 0, filterMode: 'none' },
      { type: 'slider', xAxisIndex: 0, bottom: 10 },
    ],
  }

  chart.setOption(option, true)
}

function onChartReady(chart: any) {
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
      updateChart()
    }
  })

  updateChart()
}

function handleSelectionChange(selection: any) {
  emit('selectionChange', selection)
  updateChart()
}

function updateConfig() {
  emit('configChange', { ...localConfig.value })
  updateChart()
}

watch(() => props.data, () => updateChart(), { deep: true })
watch(() => props.selection, () => updateChart(), { deep: true })
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
