<template>
  <div class="visualization-export">
    <el-dropdown split-button type="primary" size="small" :icon="Download" @click="handleExport('png')">
      Export
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item @click="handleExport('png')">
            <el-icon><Picture /></el-icon>
            Export as PNG
          </el-dropdown-item>
          <el-dropdown-item @click="handleExport('svg')">
            <el-icon><Document /></el-icon>
            Export as SVG
          </el-dropdown-item>
          <el-dropdown-item @click="handleExport('pdf')">
            <el-icon><Document /></el-icon>
            Export as PDF
          </el-dropdown-item>
          <el-dropdown-item divided @click="handleDataExport('csv')">
            <el-icon><Files /></el-icon>
            Export Data as CSV
          </el-dropdown-item>
          <el-dropdown-item @click="handleDataExport('json')">
            <el-icon><Files /></el-icon>
            Export Data as JSON
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>

    <!-- Export Options Dialog -->
    <el-dialog v-model="showOptionsDialog" title="Export Options" width="400px">
      <el-form label-position="top" size="small">
        <el-form-item v-if="isImageFormat" label="Width">
          <el-input-number v-model="exportOptions.width" :min="100" :max="4096" :step="100" />
        </el-form-item>
        <el-form-item v-if="isImageFormat" label="Height">
          <el-input-number v-model="exportOptions.height" :min="100" :max="4096" :step="100" />
        </el-form-item>
        <el-form-item v-if="exportOptions.format === 'png'" label="Quality">
          <el-slider v-model="exportOptions.quality" :min="0.1" :max="1" :step="0.1" show-stops />
        </el-form-item>
        <el-form-item label="Include Metadata">
          <el-switch v-model="exportOptions.includeMetadata" />
        </el-form-item>
        <el-form-item v-if="exportOptions.includeMetadata" label="Title">
          <el-input v-model="exportOptions.title" placeholder="Visualization title" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showOptionsDialog = false">Cancel</el-button>
        <el-button type="primary" @click="confirmExport">Export</el-button>
      </template>
    </el-dialog>

    <!-- Success Message -->
    <el-dialog v-model="showSuccessDialog" title="Export Complete" width="300px" center>
      <div class="success-content">
        <el-icon color="#67c23a" :size="48"><CircleCheck /></el-icon>
        <p>File exported successfully!</p>
        <p class="file-path">{{ exportFilePath }}</p>
      </div>
      <template #footer>
        <el-button type="primary" @click="showSuccessDialog = false">OK</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { Download, Picture, Document, Files, CircleCheck } from '@element-plus/icons-vue'
import type { ExportConfig, ExportFormat } from '@/types/visualization'

interface Props {
  chartElement?: HTMLElement
  data?: any[]
  filename?: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  export: [config: ExportConfig]
  dataExport: [format: 'csv' | 'json', data: any[]]
}>()

// State
const showOptionsDialog = ref(false)
const showSuccessDialog = ref(false)
const exportFilePath = ref('')
const pendingFormat = ref<ExportFormat>('png')

const exportOptions = reactive<ExportConfig>({
  format: 'png',
  includeMetadata: true,
  title: '',
  width: 800,
  height: 600,
  quality: 0.92,
})

// Computed
const isImageFormat = computed(() => ['png', 'svg', 'pdf'].includes(exportOptions.format))

// Methods
function handleExport(format: ExportFormat) {
  pendingFormat.value = format
  exportOptions.format = format
  showOptionsDialog.value = true
}

function handleDataExport(format: 'csv' | 'json') {
  if (!props.data) return
  
  if (format === 'csv') {
    exportAsCsv(props.data)
  } else {
    exportAsJson(props.data)
  }
}

function confirmExport() {
  showOptionsDialog.value = false

  if (isImageFormat.value && props.chartElement) {
    exportImage(props.chartElement, exportOptions)
  } else if (!isImageFormat.value && props.data) {
    exportData(exportOptions.format as 'csv' | 'json', props.data)
  }

  const ext = exportOptions.format
  const defaultName = props.filename || 'visualization'
  exportFilePath.value = `${defaultName}_${Date.now()}.${ext}`
  showSuccessDialog.value = true

  emit('export', { ...exportOptions })
}

function exportImage(element: HTMLElement, options: ExportConfig) {
  const canvas = document.createElement('canvas')
  canvas.width = options.width || 800
  canvas.height = options.height || 600
  const ctx = canvas.getContext('2d')

  if (!ctx) return

  // Fill white background
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, canvas.width, canvas.height)

  // For ECharts, use the built-in export
  const echarts = (window as any).echarts
  if (echarts) {
    // Get chart instance from element
    const chart = echarts.getInstanceByDom(element)
    if (chart) {
      const url = chart.getDataURL({
        type: options.format,
        pixelRatio: 2,
        backgroundColor: '#ffffff',
        excludeComponents: ['toolbox', 'dataZoom'],
      })

      // Download
      const link = document.createElement('a')
      link.download = `${props.filename || 'chart'}.${options.format}`
      link.href = url
      link.click()
    }
  }
}

function exportData(format: 'csv' | 'json', data: any[]) {
  if (format === 'csv') {
    exportAsCsv(data)
  } else {
    exportAsJson(data)
  }
}

function exportAsCsv(data: any[]) {
  if (!data || data.length === 0) return

  const headers = Object.keys(data[0])
  const csvContent = [
    headers.join(','),
    ...data.map(row => headers.map(h => {
      const val = row[h]
      if (val === null || val === undefined) return ''
      if (typeof val === 'string' && val.includes(',')) return `"${val}"`
      return val
    }).join(','))
  ].join('\n')

  downloadFile(csvContent, 'csv', 'text/csv')
}

function exportAsJson(data: any[]) {
  let content = JSON.stringify(data, null, 2)

  if (exportOptions.includeMetadata && exportOptions.title) {
    const metadata = {
      title: exportOptions.title,
      exportedAt: new Date().toISOString(),
      data,
    }
    content = JSON.stringify(metadata, null, 2)
  }

  downloadFile(content, 'json', 'application/json')
}

function downloadFile(content: string, ext: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${props.filename || 'export'}_${Date.now()}.${ext}`
  link.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.visualization-export {
  display: inline-block;
}

.success-content {
  text-align: center;
  padding: 20px 0;
}

.success-content p {
  margin: 12px 0 0;
  color: #303133;
}

.success-content .file-path {
  font-size: 12px;
  color: #909399;
  word-break: break-all;
}
</style>