<template>
  <el-dialog
    v-model="visible"
    :title="fileContent?.file_name || '文件预览'"
    width="80%"
    :close-on-click-modal="false"
    class="file-preview-dialog"
    destroy-on-close
  >
    <!-- Header Info -->
    <div class="dialog-header">
      <div class="file-info">
        <span class="file-path" :title="fileContent?.file_path">
          {{ fileContent?.file_path }}
        </span>
        <span class="file-size">{{ formatFileSize(fileContent?.file_size || 0) }}</span>
        <el-tag :type="getFileTypeTagType(fileContent?.file_type || '')" size="small">
          {{ fileContent?.file_type }}
        </el-tag>
      </div>
    </div>

    <!-- Content Area -->
    <div class="dialog-content">
      <!-- Loading State -->
      <div v-if="loading" class="loading-state">
        <el-icon class="is-loading" :size="32"><Loading /></el-icon>
        <span>加载中...</span>
      </div>

      <!-- Error State -->
      <el-alert
        v-else-if="error"
        :title="error"
        type="error"
        :closable="false"
        show-icon
      />

      <!-- Empty State -->
      <div v-else-if="!fileContent" class="empty-state">
        <el-icon :size="48"><Document /></el-icon>
        <span>请选择要预览的文件</span>
      </div>

      <!-- Tabular Content -->
      <div v-else-if="fileContent.file_type === 'tabular' && isTableData(fileContent.content)" class="tabular-content">
        <div class="table-toolbar">
          <div class="table-info">
            <span>共 {{ fileContent.content.total_rows }} 行</span>
            <span v-if="fileContent.content.preview_rows">
              (预览前 {{ fileContent.content.preview_rows }} 行)
            </span>
          </div>
          <el-button size="small" type="primary" :icon="Download" @click="exportTableData">
            导出 CSV
          </el-button>
        </div>
        <el-table
          :data="fileContent.content.rows"
          stripe
          border
          max-height="500"
          style="width: 100%"
          :header-cell-style="{ background: '#f5f7fa', color: '#303133' }"
        >
          <el-table-column
            v-for="(column, index) in fileContent.content.columns"
            :key="index"
            :prop="column"
            :label="column"
            min-width="120"
            show-overflow-tooltip
          />
        </el-table>
      </div>

      <!-- Text Content -->
      <div v-else-if="fileContent.file_type === 'text' && typeof fileContent.content === 'string'" class="text-content">
        <div class="text-toolbar">
          <el-button size="small" :icon="DocumentCopy" @click="copyTextContent">
            复制内容
          </el-button>
        </div>
        <pre class="text-preview">{{ fileContent.content }}</pre>
      </div>

      <!-- Binary Content -->
      <div v-else-if="fileContent.file_type === 'binary'" class="binary-content">
        <el-empty description="二进制文件无法预览">
          <template #image>
            <el-icon :size="64"><Document /></el-icon>
          </template>
          <div class="binary-info">
            <p>文件大小: {{ formatFileSize(fileContent.file_size) }}</p>
            <p>文件类型: {{ fileContent.file_name.split('.').pop()?.toUpperCase() }}</p>
          </div>
        </el-empty>
      </div>

      <!-- Unknown Content -->
      <div v-else class="unknown-content">
        <el-alert
          title="无法预览此文件"
          :description="`文件类型: ${fileContent.file_type}`"
          type="warning"
          :closable="false"
          show-icon
        />
      </div>
    </div>

    <!-- Footer -->
    <template #footer>
      <div class="dialog-footer">
        <span class="workspace-path">工作区: {{ workspaceStore.currentWorkspaceId }}</span>
        <el-button @click="visible = false">关闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import { Document, Loading, Download, DocumentCopy } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useWorkspaceStore } from '@/stores/workspace'
import type { TableData } from '@/types/workspace-data'

const workspaceStore = useWorkspaceStore()

// Computed
const visible = computed({
  get: () => workspaceStore.selectedFilePath !== null,
  set: (val: boolean) => {
    if (!val) {
      workspaceStore.clearSelection()
    }
  }
})

const fileContent = computed(() => workspaceStore.fileContent)
const loading = computed(() => workspaceStore.loading)
const error = computed(() => workspaceStore.error)

// Watch for file selection and load content
watch(() => workspaceStore.selectedFilePath, async (newPath) => {
  if (newPath) {
    // Content is already loaded by selectFile in store
  }
})

// Methods
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`
}

function getFileTypeTagType(type: string): 'success' | 'info' | 'warning' {
  switch (type) {
    case 'tabular':
      return 'success'
    case 'text':
      return 'info'
    case 'binary':
      return 'warning'
    default:
      return 'info'
  }
}

function isTableData(content: TableData | string | null): content is TableData {
  return content !== null && typeof content === 'object' && 'columns' in content && 'rows' in content
}

function copyTextContent() {
  if (fileContent.value && typeof fileContent.value.content === 'string') {
    navigator.clipboard.writeText(fileContent.value.content)
    ElMessage.success('已复制到剪贴板')
  }
}

function exportTableData() {
  if (!fileContent.value || !isTableData(fileContent.value.content)) return

  const data = fileContent.value.content
  const headers = data.columns.join(',')
  const rows = data.rows.map((row: Record<string, string>) =>
    data.columns.map((col: string) => {
      const val = row[col] || ''
      // Escape quotes and wrap in quotes if contains comma
      return val.includes(',') ? `"${val.replace(/"/g, '""')}"` : val
    }).join(',')
  )
  const csv = [headers, ...rows].join('\n')

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = fileContent.value.file_name.replace(/\.[^.]+$/, '.csv')
  link.click()
  URL.revokeObjectURL(url)

  ElMessage.success('导出成功')
}
</script>

<style scoped>
.file-preview-dialog :deep(.el-dialog__body) {
  padding: 0;
  max-height: 70vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.dialog-header {
  padding: 12px 20px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-path {
  font-family: monospace;
  font-size: 12px;
  color: #606266;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  font-size: 12px;
  color: #909399;
}

.dialog-content {
  flex: 1;
  overflow: auto;
  padding: 16px 20px;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #909399;
  gap: 12px;
}

.loading-state .el-icon {
  font-size: 32px;
}

.empty-state .el-icon {
  font-size: 64px;
}

.tabular-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.table-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-info {
  font-size: 12px;
  color: #606266;
}

.text-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.text-toolbar {
  display: flex;
  justify-content: flex-end;
}

.text-preview {
  margin: 0;
  padding: 16px;
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  font-family: 'Courier New', Consolas, monospace;
  font-size: 12px;
  line-height: 1.6;
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 400px;
}

.binary-content {
  padding: 20px;
}

.binary-info {
  text-align: center;
  color: #606266;
}

.binary-info p {
  margin: 8px 0;
}

.unknown-content {
  padding: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.workspace-path {
  font-size: 12px;
  color: #909399;
}
</style>