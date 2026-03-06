<template>
  <BaseEChartsViewer
    ref="baseViewer"
    :edit-mode="editMode"
    :loading="loading"
    selection-label="points"
    @chart-ready="onChartReady"
    @selection-change="handleSelectionChange"
  >
    <template #toolbar>
      <div class="toolbar-left">
        <el-tag v-if="significantCount.up > 0" type="danger" size="small">
          {{ significantCount.up }} up-regulated
        </el-tag>
        <el-tag v-if="significantCount.down > 0" type="primary" size="small">
          {{ significantCount.down }} down-regulated
        </el-tag>
        <el-tag v-if="data?.totalRows" type="info" size="small">
          {{ data.totalRows }} total points
        </el-tag>
      </div>
      <div class="toolbar-right">
        <el-switch v-model="showThresholdLines" active-text="Show thresholds" size="small" />
        <el-button size="small" :icon="Download" @click="$emit('export')" />
      </div>
    </template>

    <template #config>
      <el-row :gutter="12">
        <el-col :span="8">
          <el-form-item label="X Axis (Fold Change)">
            <el-select v-model="localConfig.foldChangeColumn" placeholder="Select" size="small" @change="updateConfig">
              <el-option v-for="col in numericColumns" :key="col.id" :label="col.name" :value="col.id" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="Y Axis (P-value)">
            <el-select v-model="localConfig.pValueColumn" placeholder="Select" size="small" @change="updateConfig">
              <el-option v-for="col in numericColumns" :key="col.id" :label="col.name" :value="col.id" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="Name Column">
            <el-select v-model="localConfig.nameColumn" placeholder="Optional" size="small" clearable @change="updateConfig">
              <el-option v-for="col in allColumns" :key="col.id" :label="col.name" :value="col.id" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="12">
        <el-col :span="8">
          <el-form-item label="FC Threshold">
            <el-input-number v-model="localConfig.foldChangeThreshold" :min="0" :step="0.5" size="small" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="P-value Threshold">
            <el-input-number v-model="localConfig.pValueThreshold" :min="0" :max="1" :step="0.01" size="small" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="Colors">
            <div class="color-preview">
              <span class="up-color" :style="{ background: localConfig.upregulatedColor }">Up</span>
              <span class="down-color" :style="{ background: localConfig.downregulatedColor }">Down</span>
              <span class="neutral-color" :style="{ background: localConfig.neutralColor }">NS</span>
            </div>
          </el-form-item>
        </el-col>
      </el-row>
    </template>
  </BaseEChartsViewer>
</template>

<script setup lang="ts">
import { ref, computed, watch, reactive } from 'vue'
import type { EChartsOption } from 'echarts'
import { Download } from '@element-plus/icons-vue'
import type { TableData, SelectionState, VolcanoConfig, VolcanoPoint } from '@/types/visualization'
import BaseEChartsViewer from './BaseEChartsViewer.vue'

interface Props {
  data: TableData | null
  config?: Partial<VolcanoConfig>
  selection?: SelectionState | null
  editMode?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  selectionChange: [selection: SelectionState]
  configChange: [config: Partial<VolcanoConfig>]
  export: []
  pointClick: [point: VolcanoPoint]
}>()

const baseViewer = ref<InstanceType<typeof BaseEChartsViewer>>()
const loading = ref(false)
const showThresholdLines = ref(true)

const localConfig = reactive<Required<VolcanoConfig>>({
  foldChangeColumn: '',
  pValueColumn: '',
  nameColumn: '',
  foldChangeThreshold: 1,
  pValueThreshold: 0.05,
  upregulatedColor: '#e74c3c',
  downregulatedColor: '#3498db',
  neutralColor: '#95a5a6',
})

watch(() => props.config, (newConfig) => {
  if (newConfig) Object.assign(localConfig, newConfig)
}, { immediate: true, deep: true })

const numericColumns = computed(() => props.data?.columns.filter(c => c.type === 'number') || [])
const allColumns = computed(() => props.data?.columns || [])

const significantCount = computed(() => {
  if (!props.data) return { up: 0, down: 0, neutral: 0 }
  let up = 0, down = 0
  props.data.rows.forEach(row => {
    const fc = row[localConfig.foldChangeColumn]
    const pv = row[localConfig.pValueColumn]
    if (typeof fc === 'number' && typeof pv === 'number') {
      if (pv < localConfig.pValueThreshold) {
        if (Math.abs(fc) >= localConfig.foldChangeThreshold) {
          fc > 0 ? up++ : down++
        }
      }
    }
  })
  return { up, down, neutral: props.data.totalRows - up - down }
})

function getVolcanoData() {
  if (!props.data || !localConfig.foldChangeColumn || !localConfig.pValueColumn) return []

  return props.data.rows.map((row, index) => {
    const fc = typeof row[localConfig.foldChangeColumn] === 'number'
      ? row[localConfig.foldChangeColumn] as number
      : parseFloat(String(row[localConfig.foldChangeColumn]))
    const pv = typeof row[localConfig.pValueColumn] === 'number'
      ? row[localConfig.pValueColumn] as number
      : parseFloat(String(row[localConfig.pValueColumn]))
    const name = localConfig.nameColumn ? String(row[localConfig.nameColumn] || `Point${index}`) : `Point${index}`

    const isUpregulated = fc >= localConfig.foldChangeThreshold && pv < localConfig.pValueThreshold
    const isDownregulated = fc <= -localConfig.foldChangeThreshold && pv < localConfig.pValueThreshold

    return {
      name,
      value: [fc, -Math.log10(pv || 1)],
      index,
      isUpregulated,
      isDownregulated,
    }
  }).filter(d => !isNaN(d.value[0]) && !isNaN(d.value[1]))
}

function updateChart() {
  if (!baseViewer.value) return
  const chart = baseViewer.value.chart
  if (!chart) return

  const data = getVolcanoData()
  if (data.length === 0) {
    chart.clear()
    return
  }

  const selectedIndices = baseViewer.value.getSelectedItems?.() || new Set<number>()
  const upData = data.filter(d => !selectedIndices.has(d.index) && d.isUpregulated)
  const downData = data.filter(d => !selectedIndices.has(d.index) && d.isDownregulated)
  const neutralData = data.filter(d => !selectedIndices.has(d.index) && !d.isUpregulated && !d.isDownregulated)
  const selectedData = data.filter(d => selectedIndices.has(d.index))

  const option: EChartsOption = {
    tooltip: {
      formatter: (params: any) => {
        const d = params.data
        return `<b>${d.name}</b><br/>FC: ${d.value[0].toFixed(2)}<br/>-log10(p): ${d.value[1].toFixed(2)}`
      },
    },
    xAxis: {
      type: 'value',
      name: 'Fold Change',
      nameLocation: 'middle',
      nameGap: 30,
      scale: true,
    },
    yAxis: {
      type: 'value',
      name: '-log10(P-value)',
      nameLocation: 'middle',
      nameGap: 40,
      scale: true,
    },
    series: [
      {
        name: 'Selected',
        type: 'scatter',
        data: selectedData,
        itemStyle: { color: '#f39c12', borderColor: '#fff', borderWidth: 2 },
        symbolSize: 12,
      },
      {
        name: 'Up-regulated',
        type: 'scatter',
        data: upData,
        itemStyle: { color: localConfig.upregulatedColor, opacity: 0.7 },
        symbolSize: 8,
      },
      {
        name: 'Down-regulated',
        type: 'scatter',
        data: downData,
        itemStyle: { color: localConfig.downregulatedColor, opacity: 0.7 },
        symbolSize: 8,
      },
      {
        name: 'Not significant',
        type: 'scatter',
        data: neutralData,
        itemStyle: { color: localConfig.neutralColor, opacity: 0.5 },
        symbolSize: 6,
      },
    ],
    markLine: showThresholdLines.value ? {
      data: [
        { xAxis: localConfig.foldChangeThreshold, lineStyle: { color: '#e74c3c', type: 'dashed' } },
        { xAxis: -localConfig.foldChangeThreshold, lineStyle: { color: '#3498db', type: 'dashed' } },
      ],
    } : undefined,
  }

  chart.setOption(option, true)
}

function onChartReady(chart: any) {
  chart.on('click', (params: any) => {
    if (params.data && typeof params.data.index === 'number') {
      emit('pointClick', params.data)
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
  emit('configChange', { ...localConfig })
  updateChart()
}

watch(() => props.data, () => updateChart(), { deep: true })
watch(() => props.selection, () => updateChart(), { deep: true })
watch(showThresholdLines, () => updateChart())
</script>

<script lang="ts">
export default {
  name: 'VolcanoPlotViewer'
}
</script>

<style scoped>
.toolbar-left, .toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.color-preview {
  display: flex;
  gap: 4px;
}
.color-preview span {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: bold;
  color: white;
}
</style>
