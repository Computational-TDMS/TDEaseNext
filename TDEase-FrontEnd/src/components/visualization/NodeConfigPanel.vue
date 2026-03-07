<template>
  <div class="node-config-panel">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="Data Mapping" name="mapping">
        <ColumnConfigPanel
          v-if="shouldShowColumnConfig"
          v-model="localAxisMapping"
          :columns="availableColumns"
          @change="$emit('configChange', $event)"
        />
        <div v-else-if="visualizationType === 'heatmap'" class="config-info">
          <el-form-item label="Row Column">
            <el-select v-model="localConfig.rowColumn" placeholder="Select" size="small" @change="emitConfigChange">
              <el-option v-for="col in availableColumns" :key="col.id" :label="col.name" :value="col.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="Column Column">
            <el-select v-model="localConfig.columnColumn" placeholder="Select" size="small" @change="emitConfigChange">
              <el-option v-for="col in availableColumns" :key="col.id" :label="col.name" :value="col.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="Value Column">
            <el-select v-model="localConfig.valueColumn" placeholder="Select" size="small" @change="emitConfigChange">
              <el-option v-for="col in numericColumns" :key="col.id" :label="col.name" :value="col.id" />
            </el-select>
          </el-form-item>
        </div>
        <div v-else-if="visualizationType === 'volcano'" class="config-info">
          <el-form-item label="Fold Change Column">
            <el-select v-model="localConfig.foldChangeColumn" placeholder="Select" size="small" @change="emitConfigChange">
              <el-option v-for="col in numericColumns" :key="col.id" :label="col.name" :value="col.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="P-value Column">
            <el-select v-model="localConfig.pValueColumn" placeholder="Select" size="small" @change="emitConfigChange">
              <el-option v-for="col in numericColumns" :key="col.id" :label="col.name" :value="col.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="Name Column">
            <el-select v-model="localConfig.nameColumn" placeholder="Optional" size="small" clearable @change="emitConfigChange">
              <el-option v-for="col in availableColumns" :key="col.id" :label="col.name" :value="col.id" />
            </el-select>
          </el-form-item>
        </div>
      </el-tab-pane>

      <el-tab-pane label="Appearance" name="appearance">
        <ColorSchemeConfig
          v-if="visualizationType !== 'table'"
          v-model="localColorScheme"
          @change="$emit('configChange', { colorScheme: $event })"
        />
        <div v-else class="config-info">
          <p class="info-text">Table appearance options coming soon</p>
        </div>
      </el-tab-pane>

      <el-tab-pane label="Export" name="export">
        <VisualizationExport
          :export-formats="availableFormats"
          @export="$emit('export', $event)"
        />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { ExportConfig } from '@/types/visualization'
import ColumnConfigPanel from './ColumnConfigPanel.vue'
import ColorSchemeConfig from './ColorSchemeConfig.vue'
import VisualizationExport from './VisualizationExport.vue'

interface Props {
  visualizationType?: string
  axisMapping?: Record<string, string>
  config?: Record<string, any>
  colorScheme?: string
  availableColumns: any[]
  availableFormats?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  availableFormats: () => ['png', 'svg', 'csv']
})

const emit = defineEmits<{
  configChange: [config: any]
  export: [config: ExportConfig]
}>()

const activeTab = ref('mapping')
const localAxisMapping = ref<Record<string, string>>(props.axisMapping || {})
const localConfig = ref<Record<string, any>>(props.config || {})
const localColorScheme = ref(props.colorScheme || 'viridis')

watch(() => props.axisMapping, (val) => { localAxisMapping.value = val || {} }, { deep: true })
watch(() => props.config, (val) => { localConfig.value = val || {} }, { deep: true })
watch(() => props.colorScheme, (val) => { localColorScheme.value = val || 'viridis' })

const shouldShowColumnConfig = computed(() => {
  return !['table', 'heatmap', 'volcano'].includes(props.visualizationType || '')
})

const numericColumns = computed(() => {
  return props.availableColumns.filter(c => c.type === 'number')
})

function emitConfigChange() {
  emit('configChange', {
    axisMapping: localAxisMapping.value,
    ...localConfig.value,
    colorScheme: localColorScheme.value
  })
}
</script>

<script lang="ts">
export default {
  name: 'NodeConfigPanel'
}
</script>

<style scoped>
.node-config-panel {
  padding: 16px;
  background: #f5f7fa;
  border: 1px solid #dcdfe6;
}

.config-info {
  padding: 12px;
}

.info-text {
  color: #909399;
  font-size: 14px;
  text-align: center;
  margin: 20px 0;
}
</style>
