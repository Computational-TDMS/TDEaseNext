<template>
  <div class="html-viewer">
    <!-- Toolbar -->
    <div class="viewer-toolbar">
      <div class="toolbar-left">
        <el-tag v-if="currentFeatureId" type="success" size="small">
          Feature ID: {{ currentFeatureId }}
        </el-tag>
        <el-tag v-else type="info" size="small">
          Select a feature to view HTML
        </el-tag>
      </div>
      <div class="toolbar-right">
        <el-button
          size="small"
          :icon="Refresh"
          @click="reload"
          :disabled="!currentFeatureId"
          circle
          title="Reload"
        />
        <el-button
          size="small"
          :icon="Download"
          @click="exportHtml"
          :disabled="!hasHtml"
          circle
          title="Export HTML"
        />
        <el-button
          size="small"
          :icon="FullScreen"
          @click="toggleFullscreen"
          circle
          title="Fullscreen"
        />
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <el-icon class="is-loading" :size="32"><Loading /></el-icon>
      <p>Loading HTML content...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <el-icon :size="32"><Warning /></el-icon>
      <p>{{ errorMessage }}</p>
      <el-button size="small" type="primary" @click="reload">Retry</el-button>
    </div>

    <!-- Empty State -->
    <div v-else-if="!currentFeatureId" class="empty-state">
      <el-icon :size="48"><Link /></el-icon>
      <p>Select a feature from the upstream viewer</p>
      <p class="hint">This viewer displays HTML fragments for selected features</p>
    </div>

    <!-- HTML Content Container -->
    <div
      v-else
      ref="htmlContainer"
      class="html-content"
      :class="{ 'fullscreen': isFullscreen }"
    >
      <iframe
        v-if="hasHtml"
        ref="iframeRef"
        class="html-iframe"
        sandbox="allow-downloads"
        :srcdoc="sanitizedHtml"
        @load="onIframeLoad"
      />
      <div v-else class="no-html">
        <el-icon :size="32"><DocumentDelete /></el-icon>
        <p>No HTML content available for this feature</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { Loading, Warning, Link, Download, FullScreen, Refresh, DocumentDelete } from '@element-plus/icons-vue'
import { getAPIClient } from '@/services/api/client'
import type { SelectionState } from '@/types/visualization'

interface Props {
  data?: {
    htmlFileId?: string
    sourceNodeId?: string
  }
  selection?: SelectionState | null
  upstreamSelection?: SelectionState | null
  editMode?: boolean
}

const props = defineProps<Props>()

// Refs
const htmlContainer = ref<HTMLElement>()
const iframeRef = ref<HTMLIFrameElement>()

// State
const loading = ref(false)
const error = ref(false)
const errorMessage = ref('')
const isFullscreen = ref(false)
const currentFeatureId = ref<string | null>(null)
const htmlContent = ref<string>('')
const iframeLoaded = ref(false)

// Computed
const activeSelection = computed(() => {
  return props.upstreamSelection || props.selection
})

const selectedFeatureId = computed(() => {
  if (!activeSelection.value?.selectedIndices) return null
  const indices = Array.from(activeSelection.value.selectedIndices)
  if (indices.length === 0) return null
  if (indices.length === 1) return indices[0].toString()
  // If multiple selected, use the first one
  return indices[0].toString()
})

const hasHtml = computed(() => {
  return htmlContent.value.trim().length > 0
})

function sanitizeHtmlContent(rawHtml: string): string {
  if (!rawHtml) {
    return ''
  }

  const parser = new DOMParser()
  const doc = parser.parseFromString(rawHtml, 'text/html')

  const blockedTags = ['script', 'iframe', 'object', 'embed', 'link', 'meta', 'base', 'form']
  for (const tag of blockedTags) {
    doc.querySelectorAll(tag).forEach((node) => node.remove())
  }

  doc.querySelectorAll('*').forEach((element) => {
    for (const attr of Array.from(element.attributes)) {
      const attrName = attr.name.toLowerCase()
      const attrValue = attr.value.trim().toLowerCase()
      if (attrName.startsWith('on')) {
        element.removeAttribute(attr.name)
        continue
      }
      if ((attrName === 'href' || attrName === 'src') && attrValue.startsWith('javascript:')) {
        element.removeAttribute(attr.name)
      }
    }
  })

  const csp = doc.createElement('meta')
  csp.setAttribute('http-equiv', 'Content-Security-Policy')
  csp.setAttribute('content', "default-src 'none'; img-src data: blob:; style-src 'unsafe-inline';")
  doc.head.prepend(csp)

  return `<!doctype html>\n${doc.documentElement.outerHTML}`
}

const sanitizedHtml = computed(() => {
  return sanitizeHtmlContent(htmlContent.value)
})

// Methods
async function loadHtmlForFeature(featureId: string) {
  if (!props.data?.htmlFileId && !props.data?.sourceNodeId) {
    console.warn('[HtmlViewer] No HTML file source configured')
    return
  }

  loading.value = true
  error.value = false
  errorMessage.value = ''
  iframeLoaded.value = false

  try {
    const apiClient = getAPIClient()

    // Determine the source node ID
    const sourceNodeId = props.data.sourceNodeId || props.data.htmlFileId

    // Fetch HTML content for the specific feature
    const response = await apiClient.get<{ html?: string }>(`/api/nodes/${sourceNodeId}/html/${featureId}`)

    if (response.data && response.data.html) {
      htmlContent.value = response.data.html
    } else {
      htmlContent.value = ''
    }
  } catch (err) {
    error.value = true
    errorMessage.value = err instanceof Error ? err.message : 'Failed to load HTML content'
    console.error('[HtmlViewer] Load error:', err)
    htmlContent.value = ''
  } finally {
    loading.value = false
  }
}

function reload() {
  if (currentFeatureId.value) {
    loadHtmlForFeature(currentFeatureId.value)
  }
}

function exportHtml() {
  if (!htmlContent.value) return

  const blob = new Blob([htmlContent.value], { type: 'text/html' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `feature_${currentFeatureId.value}.html`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value
  if (isFullscreen.value) {
    htmlContainer.value?.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}

function onIframeLoad() {
  iframeLoaded.value = true
}

function handleFullscreenChange() {
  isFullscreen.value = document.fullscreenElement === htmlContainer.value
}

// Watch for selection changes
watch(
  () => selectedFeatureId.value,
  (newFeatureId) => {
    if (newFeatureId && newFeatureId !== currentFeatureId.value) {
      currentFeatureId.value = newFeatureId
      loadHtmlForFeature(newFeatureId)
    } else if (!newFeatureId) {
      currentFeatureId.value = null
      htmlContent.value = ''
    }
  },
  { immediate: true }
)

// Lifecycle
onMounted(() => {
  document.addEventListener('fullscreenchange', handleFullscreenChange)

  // Load initial HTML if selection exists
  if (selectedFeatureId.value) {
    currentFeatureId.value = selectedFeatureId.value
    loadHtmlForFeature(selectedFeatureId.value)
  }
})

onUnmounted(() => {
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
})
</script>

<style scoped>
.html-viewer {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: white;
  border-radius: 4px;
  overflow: hidden;
}

.viewer-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;
  gap: 8px;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 12px;
  color: #606266;
  padding: 20px;
}

.hint {
  font-size: 12px;
  color: #909399;
  margin-top: -8px;
}

.html-content {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.html-content.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  background: white;
}

.html-iframe {
  width: 100%;
  height: 100%;
  border: none;
  background: white;
}

.no-html {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 12px;
  color: #909399;
}

:deep(.el-icon.is-loading) {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
