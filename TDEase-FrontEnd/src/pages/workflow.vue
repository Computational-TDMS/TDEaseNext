<template>
  <div class="workflow-page">
    <!-- Toolbar: VSCode-style minimal toolbar -->
    <div class="toolbar">
      <!-- Left: View controls -->
      <div class="toolbar-left">
        <div class="view-controls">
          <el-button text size="small" @click="togglePrimarySidebar" title="切换侧边栏">
            <CatppuccinIcon name="Grid" />
          </el-button>
          <el-button text size="small" @click="togglePanel" title="切换日志面板">
            <CatppuccinIcon name="Document" />
          </el-button>
        </div>
        <el-divider direction="vertical" />
        <div class="action-group">
          <el-button size="small" @click="handleUndo" :disabled="!workflowStore.historyManager.canUndo" title="撤销">
            <CatppuccinIcon name="RefreshLeft" />
          </el-button>
          <el-button size="small" @click="handleRedo" :disabled="!workflowStore.historyManager.canRedo" title="重做">
            <CatppuccinIcon name="RefreshRight" />
          </el-button>
          <el-button size="small" @click="handleAutoLayout" title="自动布局">
            <CatppuccinIcon name="Grid" />
          </el-button>
        </div>
      </div>

      <!-- Center: Workflow info -->
      <div class="toolbar-center">
        <div class="workflow-info">
          <span class="info-item">
            <CatppuccinIcon name="Connection" />
            {{ workflowStore.nodes.length }} 节点
          </span>
          <span class="info-item">
            <CatppuccinIcon name="Link" />
            {{ workflowStore.connections.length }} 连接
          </span>
        </div>
      </div>

      <!-- Right: Primary action + menu -->
      <div class="toolbar-right">
        <ThemeSwitcher />
        <el-dropdown trigger="click" @command="handleToolbarCommand">
          <el-button size="small" text>
            <CatppuccinIcon name="Menu" />
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="new">
                <CatppuccinIcon name="Plus" />新建工作流
              </el-dropdown-item>
              <el-dropdown-item command="open">
                <CatppuccinIcon name="Folder" />打开工作流
              </el-dropdown-item>
              <el-dropdown-item command="save">
                <CatppuccinIcon name="Document" />保存工作流
              </el-dropdown-item>
              <el-dropdown-item command="duplicate">
                <CatppuccinIcon name="CopyDocument" />复制工作流
              </el-dropdown-item>
              <el-dropdown-item command="export">
                <CatppuccinIcon name="Download" />导出
              </el-dropdown-item>
              <el-dropdown-item command="import">
                <CatppuccinIcon name="Upload" />导入
              </el-dropdown-item>
              <el-dropdown-item command="template">
                <CatppuccinIcon name="DocumentCopy" />从模板创建
              </el-dropdown-item>
              <el-dropdown-item command="example">
                <CatppuccinIcon name="Files" />加载示例
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button type="primary" size="small" @click="executeWorkflow" :loading="isExecuting">
          <CatppuccinIcon name="VideoPlay" />
          执行
        </el-button>
      </div>
    </div>

    <!-- Workspace: Main content area with VS Code-style layout -->
    <div class="workspace">
      <!-- Editor Row: Canvas and sidebars in horizontal flex -->
      <div class="editor-row">
        <!-- Left Sidebar: VSCode-style panel with tabs -->
        <div
          class="node-palette-container primary-sidebar"
          :class="{ collapsed: !primarySidebarVisible }"
          :style="{ width: primarySidebarWidth + 'px' }"
        >
          <el-tabs v-model="leftSidebarTab" type="border-card" class="left-sidebar-tabs">
            <el-tab-pane label="节点" name="nodes">
              <NodePalette @drag-start="onNodeDragStart" />
            </el-tab-pane>
            <el-tab-pane label="属性" name="properties">
              <PropertyPanel :selected-node="selectedNodeRef" />
            </el-tab-pane>
            <el-tab-pane label="文件" name="files">
              <div class="file-browser-container">
                <FileExplorer />
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>

        <!-- Left Sidebar Resizer -->
        <div
          v-if="primarySidebarVisible"
          class="resizer-handle"
          @mousedown="onPrimaryResizerMouseDown"
        ></div>

        <!-- Main column: canvas + bottom panel (constrained by left sidebar) -->
        <div class="main-column">
          <!-- Canvas Container: Workflow canvas in center -->
          <div class="canvas-container" v-loading="loadingWorkflow && !initialLoadDone" element-loading-text="加载工作流...">
            <VueFlowCanvas
              ref="canvasRef"
              @node-select="onNodeSelect"
              @context-menu="onContextMenu"
            />
          </div>

          <!-- Panel Container: Bottom panel for logs -->
          <div
            class="panel-container"
            :class="{ collapsed: !panelVisible }"
            :style="{ height: panelHeight + 'px' }"
          >
            <div class="panel-resizer" @mousedown="onPanelResizerMouseDown"></div>
            <div class="logs-panel">
              <div class="logs-header">
                <el-radio-group v-model="logsPanelTab" size="small">
                  <el-radio-button label="current">当前执行</el-radio-button>
                  <el-radio-button label="history">执行历史</el-radio-button>
                </el-radio-group>
                <div v-if="logsPanelTab === 'current'" class="logs-header-current">
                  <span>执行ID: {{ executionId || '未开始' }}</span>
                  <span>状态: {{ executionStatus || '未知' }}</span>
                  <CatppuccinIcon v-if="isExecuting" name="Loading" :size="16" style="margin-right: 8px;" class="is-loading" />
                  <el-button size="small" @click="stopCurrentExecution" :disabled="!executionId">停止</el-button>
                </div>
              </div>
              <div class="logs-body" v-if="logsPanelTab === 'current'">
                <div class="log-line" v-for="(l, idx) in executionLogs" :key="idx">{{ l.timestamp }} [{{ l.level }}] {{ l.message }}</div>
                <div v-if="executionLogs.length === 0 && !executionId" class="logs-empty">暂无执行日志，点击「执行工作流」开始运行</div>
              </div>
              <div class="logs-body logs-history" v-else>
                <div class="history-item" v-for="h in executionHistory" :key="h.id">
                  <span class="history-id">{{ h.id.slice(0, 8) }}…</span>
                  <span class="history-name">{{ h.workflowName }}</span>
                  <el-tag :type="h.status === 'completed' ? 'success' : h.status === 'failed' ? 'danger' : h.status === 'cancelled' ? 'info' : 'warning'" size="small">{{ h.status }}</el-tag>
                  <span class="history-time">{{ formatExecutionTime(h.startedAt) }}{{ h.endedAt ? ` – ${formatExecutionTime(h.endedAt)}` : '' }}</span>
                </div>
                <div v-if="executionHistory.length === 0" class="logs-empty">暂无执行历史</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Context Menu -->
    <ContextMenu
      :visible="contextMenu.visible.value"
      :position="contextMenu.position.value"
      :menu-items="contextMenu.menuItems.value"
      @close="contextMenu.hideContextMenu"
    />

    <!-- File Preview Dialog -->
    <FilePreviewDialog />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'
import { CopyDocument, Delete, Edit } from '@element-plus/icons-vue'
import { CatppuccinIcon } from '@/components/icons'
// import { useRouter } from 'vue-router'

import VueFlowCanvas from '@/components/workflow/VueFlowCanvas.vue'
import NodePalette from '@/components/workflow/NodePalette.vue'
import PropertyPanel from '@/components/workflow/PropertyPanel.vue'
import ContextMenu from '@/components/workflow/ContextMenu.vue'
import FileExplorer from '@/components/workspace/FileExplorer.vue'
import FilePreviewDialog from '@/components/workspace/FilePreviewDialog.vue'
import ThemeSwitcher from '@/components/theme/ThemeSwitcher.vue'
import { useKeyboardShortcuts, type KeyboardShortcut } from '../composables/useKeyboardShortcuts'
import { useContextMenu } from '../composables/useContextMenu'
import { useWorkflowStore } from '../stores/workflow'
import type { WorkflowJSON } from '../stores/workflow'
import { WorkflowService } from '../services/workflow'
import { useToolsRegistry, ensureToolsLoaded } from '@/services/tools/registry'

const contextMenu = useContextMenu()
const canvasRef = ref<InstanceType<typeof VueFlowCanvas> | null>(null)
const workflowStore = useWorkflowStore()
const { workflowData, currentWorkflow, selectedNode } = storeToRefs(workflowStore)
const selectedNodeRef = computed(() => selectedNode.value)

// Layout state management - VS Code style collapsible layout
const primarySidebarVisible = ref(true)
const panelVisible = ref(true)
const primarySidebarWidth = ref(320)
const panelHeight = ref(300)
const windowWidth = ref(window.innerWidth)
const leftSidebarTab = ref<'nodes' | 'properties' | 'files'>('nodes')

// Execution state
const executionId = ref<string | null>(null)
const executionLogs = ref<any[]>([])
const executionStatus = ref<string>('pending')
let logsTimer: any = null

// Execution history (7.3) - last N runs for listing
interface ExecutionHistoryItem {
  id: string
  workflowName: string
  status: string
  startedAt: string
  endedAt?: string
}
const executionHistory = ref<ExecutionHistoryItem[]>([])
const MAX_EXECUTION_HISTORY = 50
const logsPanelTab = ref<'current' | 'history'>('current')

function formatExecutionTime(iso: string): string {
  try {
    const d = new Date(iso)
    return d.toLocaleTimeString('zh-CN', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return iso
  }
}

// Loading states for UX (5.5)
const savingWorkflow = ref(false)
const loadingWorkflow = ref(false)
const initialLoadDone = ref(false)
const isExecuting = computed(() => Boolean(executionId.value) && !['completed', 'failed', 'cancelled'].includes(executionStatus.value))

// Resizer state
const resizing = ref<'primary' | 'secondary' | 'panel' | null>(null)
const resizeStartX = ref(0)
const resizeStartY = ref(0)
const resizeStartWidth = ref(0)
const resizeStartHeight = ref(0)

// localStorage keys
const STORAGE_PREFIX = 'tdease-workflow.'
const STORAGE_KEYS = {
  primarySidebarVisible: `${STORAGE_PREFIX}primarySidebarVisible`,
  panelVisible: `${STORAGE_PREFIX}panelVisible`,
  primarySidebarWidth: `${STORAGE_PREFIX}primarySidebarWidth`,
  panelHeight: `${STORAGE_PREFIX}panelHeight`,
}

// Layout persistence functions
const saveLayoutState = (key: string, value: any) => {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch (e) {
    // Graceful degradation for private mode or quota exceeded
    console.warn('Failed to save layout state:', e)
  }
}

const loadLayoutState = <T,>(key: string, defaultValue: T): T => {
  try {
    const stored = localStorage.getItem(key)
    if (stored !== null) {
      return JSON.parse(stored) as T
    }
  } catch (e) {
    console.warn('Failed to load layout state:', e)
  }
  return defaultValue
}

// Initialize layout state from localStorage
const initializeLayoutState = () => {
  primarySidebarVisible.value = loadLayoutState(STORAGE_KEYS.primarySidebarVisible, true)
  panelVisible.value = loadLayoutState(STORAGE_KEYS.panelVisible, true)
  primarySidebarWidth.value = loadLayoutState(STORAGE_KEYS.primarySidebarWidth, 320)
  panelHeight.value = loadLayoutState(STORAGE_KEYS.panelHeight, 300)
}

// Toggle functions
const togglePrimarySidebar = () => {
  primarySidebarVisible.value = !primarySidebarVisible.value
  saveLayoutState(STORAGE_KEYS.primarySidebarVisible, primarySidebarVisible.value)
}

const togglePanel = () => {
  panelVisible.value = !panelVisible.value
  saveLayoutState(STORAGE_KEYS.panelVisible, panelVisible.value)
}

// Resizer handlers
const onPrimaryResizerMouseDown = (e: MouseEvent) => {
  e.preventDefault()
  resizing.value = 'primary'
  resizeStartX.value = e.clientX
  resizeStartWidth.value = primarySidebarWidth.value
  document.addEventListener('mousemove', onResizerMouseMove)
  document.addEventListener('mouseup', onResizerMouseUp)
}

const onPanelResizerMouseDown = (e: MouseEvent) => {
  e.preventDefault()
  resizing.value = 'panel'
  resizeStartY.value = e.clientY
  resizeStartHeight.value = panelHeight.value
  document.addEventListener('mousemove', onResizerMouseMove)
  document.addEventListener('mouseup', onResizerMouseUp)
}

const onResizerMouseMove = (e: MouseEvent) => {
  if (!resizing.value) return

  if (resizing.value === 'primary') {
    const deltaX = e.clientX - resizeStartX.value
    primarySidebarWidth.value = Math.min(500, Math.max(200, resizeStartWidth.value + deltaX))
  } else if (resizing.value === 'panel') {
    const deltaY = resizeStartY.value - e.clientY
    panelHeight.value = Math.min(window.innerHeight * 0.6, Math.max(150, resizeStartHeight.value + deltaY))
  }
}

const onResizerMouseUp = () => {
  if (resizing.value === 'primary') {
    saveLayoutState(STORAGE_KEYS.primarySidebarWidth, primarySidebarWidth.value)
  } else if (resizing.value === 'panel') {
    saveLayoutState(STORAGE_KEYS.panelHeight, panelHeight.value)
  }
  resizing.value = null
  document.removeEventListener('mousemove', onResizerMouseMove)
  document.removeEventListener('mouseup', onResizerMouseUp)
}

// Window resize handler for responsive breakpoints
const onWindowResize = () => {
  windowWidth.value = window.innerWidth
}

// Responsive breakpoint handling
watch(windowWidth, (newWidth, oldWidth) => {
  // Auto-collapse primary sidebar at 768px breakpoint
  if (newWidth < 768 && oldWidth >= 768) {
    primarySidebarVisible.value = false
    saveLayoutState(STORAGE_KEYS.primarySidebarVisible, false)
  } else if (newWidth >= 768 && oldWidth < 768) {
    // Restore user preference when going above breakpoint
    primarySidebarVisible.value = loadLayoutState(STORAGE_KEYS.primarySidebarVisible, true)
  }
})

// Cleanup on unmount
onUnmounted(() => {
  document.removeEventListener('mousemove', onResizerMouseMove)
  document.removeEventListener('mouseup', onResizerMouseUp)
  window.removeEventListener('resize', onWindowResize)
})


// Workflow templates (6.2)
const workflowTemplates: { id: string; name: string; workflow: WorkflowJSON }[] = [
  {
    id: 'linear',
    name: '线性流程（输入→处理→输出）',
    workflow: {
      metadata: {
        id: 'template-linear',
        name: '线性流程模板',
        version: '1.0.0',
        created: new Date().toISOString(),
        modified: new Date().toISOString(),
        tags: ['template']
      },
      format_version: '2.0',
      nodes: [
        {
          id: 't-input',
          type: 'input',
          position: { x: 80, y: 120 },
          displayProperties: { label: '输入', color: '#4CAF50' },
          inputs: [],
          outputs: [{ id: 'output', name: '输出', type: 'file', required: false }],
          nodeConfig: {}
        },
        {
          id: 't-process',
          type: 'process',
          position: { x: 280, y: 120 },
          displayProperties: { label: '处理', color: '#2196F3' },
          inputs: [{ id: 'input', name: '输入', type: 'file', required: false }],
          outputs: [{ id: 'output', name: '输出', type: 'file', required: false }],
          nodeConfig: {}
        },
        {
          id: 't-output',
          type: 'output',
          position: { x: 480, y: 120 },
          displayProperties: { label: '输出', color: '#FF9800' },
          inputs: [{ id: 'input', name: '输入', type: 'file', required: false }],
          outputs: [],
          nodeConfig: {}
        }
      ],
      connections: [
        { id: 'c1', source: { nodeId: 't-input', portId: 'output' }, target: { nodeId: 't-process', portId: 'input' } },
        { id: 'c2', source: { nodeId: 't-process', portId: 'output' }, target: { nodeId: 't-output', portId: 'input' } }
      ],
      projectSettings: {}
    }
  },
  {
    id: 'empty',
    name: '空白画布',
    workflow: {
      metadata: {
        id: 'template-empty',
        name: '空白模板',
        version: '1.0.0',
        created: new Date().toISOString(),
        modified: new Date().toISOString(),
        tags: ['template']
      },
      format_version: '2.0',
      nodes: [],
      connections: [],
      projectSettings: {}
    }
  }
]

const applyTemplate = (templateId: string) => {
  const t = workflowTemplates.find((x) => x.id === templateId)
  if (!t) return
  const now = Date.now().toString()
  const idMap = new Map<string, string>()
  t.workflow.nodes.forEach((n) => {
    idMap.set(n.id, `${n.id}-${now}`)
  })
  const newNodes = t.workflow.nodes.map((n) => ({ ...n, id: idMap.get(n.id)! }))
  const newConnections = t.workflow.connections.map((c) => ({
    ...c,
    id: `${c.id}-${now}`,
    source: { ...c.source, nodeId: idMap.get(c.source.nodeId) ?? c.source.nodeId },
    target: { ...c.target, nodeId: idMap.get(c.target.nodeId) ?? c.target.nodeId }
  }))
  const workflow: WorkflowJSON = {
    ...t.workflow,
    metadata: {
      ...t.workflow.metadata,
      id: now,
      name: t.workflow.metadata.name + ' (新建)',
      created: new Date().toISOString(),
      modified: new Date().toISOString()
    },
    nodes: newNodes,
    connections: newConnections
  }
  workflowStore.loadWorkflow(workflow)
  ElMessage.success(`已应用模板: ${t.name}`)
}

// Export workflow as JSON file (6.4)
const exportWorkflow = () => {
  const wf = workflowData.value
  if (!wf) {
    ElMessage.warning('没有可导出的工作流')
    return
  }
  const blob = new Blob([JSON.stringify(wf, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `workflow-${wf.metadata.name || wf.metadata.id}-${Date.now()}.json`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('工作流已导出')
}

// Import workflow from JSON file (6.4)
const triggerImportFile = () => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json,application/json'
  input.onchange = (e) => {
    void onImportFileChange(e)
  }
  input.click()
}

const onImportFileChange = async (e: Event) => {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  try {
    const text = await file.text()
    const wf = JSON.parse(text) as WorkflowJSON
    if (!wf.metadata || !Array.isArray(wf.nodes) || !Array.isArray(wf.connections)) {
      ElMessage.error('无效的工作流文件格式')
      return
    }
    workflowStore.loadWorkflow(wf)
    ElMessage.success(`已导入工作流: ${wf.metadata.name || '未命名'}`)
  } catch (err) {
    console.error('Import workflow error:', err)
    ElMessage.error('导入失败，请检查文件格式')
  }
  input.value = ''
}

// Duplicate current workflow (6.5) - clone with new IDs
const duplicateWorkflow = () => {
  const wf = workflowData.value
  if (!wf) {
    ElMessage.warning('没有可复制的工作流')
    return
  }
  const now = Date.now().toString()
  const idMap = new Map<string, string>()
  wf.nodes.forEach((n) => {
    idMap.set(n.id, `${n.id}-${now}`)
  })
  const newNodes = wf.nodes.map((n) => ({
    ...n,
    id: idMap.get(n.id)!
  }))
  const newConnections = wf.connections.map((c) => ({
    ...c,
    id: `${c.id}-${now}`,
    source: { ...c.source, nodeId: idMap.get(c.source.nodeId) ?? c.source.nodeId },
    target: { ...c.target, nodeId: idMap.get(c.target.nodeId) ?? c.target.nodeId }
  }))
  const cloned: WorkflowJSON = {
    ...wf,
    metadata: {
      ...wf.metadata,
      id: now,
      name: (wf.metadata.name || '工作流') + ' (副本)',
      created: new Date().toISOString(),
      modified: new Date().toISOString()
    },
    nodes: newNodes,
    connections: newConnections
  }
  workflowStore.loadWorkflow(cloned)
  ElMessage.success('已复制工作流')
}

// Basic workflow page functionality
const createNewWorkflow = async () => {
  try {
    await ElMessageBox.confirm('确定要创建新的工作流吗？当前未保存的更改将丢失。', '确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    // 创建新的工作流
    workflowStore.createNewWorkflow('新工作流')
    ElMessage.success('新工作流已创建')
  } catch {
    // User cancelled
  }
}

const openWorkflow = async () => {
  try {
    const { value: workflowId } = await ElMessageBox.prompt('请输入工作流ID', '打开工作流', {
      confirmButtonText: '打开',
      cancelButtonText: '取消',
      inputPattern: /^[a-zA-Z0-9_-]+$/
    })

    if (workflowId) {
      loadingWorkflow.value = true
      try {
        const workflow = await WorkflowService.loadWorkflow(workflowId)
        workflowStore.loadWorkflow(workflow)
        ElMessage.success(`工作流 "${workflow.metadata.name}" 已打开`)
      } finally {
        loadingWorkflow.value = false
      }
    }
  } catch {
    // User cancelled
    loadingWorkflow.value = false
  }
}

const saveWorkflow = async (workflow?: any, silent: boolean = false) => {
  const wf = workflow || workflowData.value
  if (!wf) {
    if (!silent) ElMessage.warning('没有可保存的工作流')
    return
  }
  if (!silent) savingWorkflow.value = true
  try {
    await WorkflowService.saveWorkflow(wf, silent)
    if (currentWorkflow.value) {
      currentWorkflow.value.metadata.modified = new Date().toISOString()
    }
  } catch (error) {
    console.error('Save workflow error:', error)
    if (!silent) throw error
  } finally {
    if (!silent) savingWorkflow.value = false
  }
}

const executeWorkflow = async (silent: boolean = false) => {
  try {
    const wf = workflowData.value
    if (!wf) {
      if (!silent) {
        ElMessage.warning('没有可执行的工作流')
      }
      return
    }

    // 检查是否有未保存的更改（如果不是静默模式）
    // 在静默模式下也保存，确保工作流ID正确
      try {
      await saveWorkflow(wf, silent)
      } catch (saveError) {
      // 在静默模式下忽略保存错误，但记录日志
        if (!silent) {
          throw saveError
      } else {
        console.warn('保存工作流失败（静默模式）:', saveError)
      }
    }

    // 新架构：使用 user_id/workspace_id/sample_ids 格式
    // 后端从 samples.json 加载样品上下文
    const parameters = {
      user_id: 'test_user',      // TODO: 从配置或用户选择获取
      workspace_id: 'test_workspace',  // TODO: 从配置或用户选择获取
      sample_ids: ['sample1']    // TODO: 从用户选择获取
    } as Record<string, any>

    // 直接发送工作流 ID 给后端执行（新架构）
    const exec = await WorkflowService.executeCompiled(wf, undefined, parameters, silent)
    const execId = (exec as any).executionId as string
    executionId.value = execId
    executionStatus.value = (exec as any).status || 'pending'
    executionLogs.value = []

    // 7.3 执行历史：记录本次执行
    const historyItem: ExecutionHistoryItem = {
      id: execId,
      workflowName: wf.metadata.name || '未命名',
      status: 'running',
      startedAt: new Date().toISOString()
    }
    executionHistory.value = [historyItem, ...executionHistory.value].slice(0, MAX_EXECUTION_HISTORY)

    // 清理旧的轮询定时器
    if (logsTimer) {
      clearInterval(logsTimer)
      logsTimer = null
    }

    // 使用 WebSocket + 轮询降级监控执行状态
    const monitoring = WorkflowService.startExecutionMonitoring(execId, {
      onLog: (log) => {
        // 实时添加日志（避免重复）
        const logKey = `${log.timestamp}-${log.message}`
        if (!executionLogs.value.some(l => `${l.timestamp}-${l.message}` === logKey)) {
          executionLogs.value.push(log)
        }
      },
      onStatus: (status, _progress) => {
        executionStatus.value = status
      },
      onComplete: () => {
        const status = executionStatus.value
        const item = executionHistory.value.find((h) => h.id === execId)
        if (item) {
          item.status = status
          item.endedAt = new Date().toISOString()
        }
        if (!silent) {
          const statusMsg = status === 'completed' ? '执行完成' : status === 'failed' ? '执行失败' : '已取消'
          ElMessage.success(statusMsg)
          // 7.5 执行结果通知：使用 ElNotification 更醒目
          const notifType = status === 'completed' ? 'success' : status === 'failed' ? 'error' : 'info'
          ElNotification({
            type: notifType,
            title: status === 'completed' ? '工作流执行完成' : status === 'failed' ? '工作流执行失败' : '工作流已取消',
            message: `工作流「${wf.metadata.name}」${statusMsg}`,
            duration: status === 'failed' ? 0 : 4500
          })
        }
      },
      onError: (error) => {
        console.error('Execution monitoring error:', error)
      },
      usePollingFallback: true
    })

    // 保存监控停止函数
    if ((window as any).__currentMonitoring) {
      (window as any).__currentMonitoring.stop()
    }
    (window as any).__currentMonitoring = monitoring

    if (!silent) {
      ElMessage.success(`工作流 "${wf.metadata.name}" 开始执行`)
    } else {
      console.log(`工作流 "${wf.metadata.name}" 开始自动执行 (Execution ID: ${executionId.value})`)
    }

    // 可以在这里导航到执行监控页面
    // router.push(`/executions/${exec.executionId}`)
  } catch (error) {
    console.error('Execute workflow error:', error)
    if (!silent) {
      // 在静默模式下不显示错误消息
    }
  }
}
const stopCurrentExecution = async () => {
  const id = executionId.value
  if (!id) return
  try {
    await WorkflowService.stopExecution(id)
    executionStatus.value = 'cancelled'
    const item = executionHistory.value.find((h) => h.id === id)
    if (item) {
      item.status = 'cancelled'
      item.endedAt = new Date().toISOString()
    }
    // 停止监控
    if ((window as any).__currentMonitoring) {
      (window as any).__currentMonitoring.stop()
      (window as any).__currentMonitoring = null
    }
    if (logsTimer) clearInterval(logsTimer)
  } catch {}
}

const importExampleWorkflow = async () => {
  try {
    // 测试模式：从后端获取测试工作流，并根据其中的工具访问注册的工具列表来组成工作流渲染
    console.log('测试模式：从后端加载测试工作流和工具列表...')
    
    // 1. 确保工具注册表已加载（显式等待 API 完成）
    await ensureToolsLoaded()
    const toolsRegistry = useToolsRegistry()
    console.log(`工具注册表已就绪，共 ${toolsRegistry.value.length} 个工具`)
    
    // 2. 从后端获取测试工作流
    let wf: any = null
    try {
        wf = await WorkflowService.loadWorkflow("wf_test_full")
        if (wf) {
        console.log('测试工作流已从后端加载 (Live)')
        console.log('工作流包含节点:', wf.nodes?.length || 0)
        
        // 3. 根据工作流中的工具，从工具注册表中获取工具配置
        // 检查工作流中使用的工具是否在注册表中
        const workflowTools = new Set<string>()
        wf.nodes?.forEach((node: any) => {
          // 优先从 nodeConfig.toolId 获取（这是 importRawWorkflow 转换后的结构）
          // 其次从 data.type 获取（这是原始 vueflow_data 的结构）
          // 最后从 type 获取（但 type 可能是 'tool'，不是实际工具ID）
          const rawToolId =
            (node as any).nodeConfig?.toolId ||
            node.data?.toolId ||
            node.data?.type ||
            (node.type !== 'tool' ? node.type : null)
          const toolId = typeof rawToolId === 'string' ? rawToolId.trim() : null
          if (toolId && toolId !== 'tool') {
            workflowTools.add(toolId)
          }
        })
        
        console.log('工作流使用的工具:', Array.from(workflowTools))
        
        // 检查工具是否在注册表中
        const registryIds = new Set(toolsRegistry.value.map(t => String(t.id).trim()))
        const missingTools: string[] = []
        workflowTools.forEach(toolId => {
          if (!registryIds.has(toolId)) {
            missingTools.push(toolId)
          } else {
            const tool = toolsRegistry.value.find(t => String(t.id).trim() === toolId)
            if (tool) {
              console.log(`工具 "${toolId}" 已在注册表中找到:`, tool.name)
            }
          }
        })
        
        if (missingTools.length > 0) {
          console.warn('以下工具未在注册表中找到:', missingTools)
        }
        
        // 加载工作流到store
        workflowStore.loadWorkflow(wf)
        }
    } catch (e) {
      console.error('从后端加载测试工作流失败:', e)
      ElMessage.warning('无法加载工作流，请确保后端已启动且已执行 seed 脚本初始化数据')
      return
    }

    // 工作流已从后端加载，无需再次保存
  } catch (e) {
    console.error('Import workflow error:', e)
    // ElMessage.error('导入工作流失败')
  }
}

onMounted(() => {
  // Initialize layout state from localStorage
  initializeLayoutState()

  // Add window resize listener for responsive behavior
  window.addEventListener('resize', onWindowResize)

  // 异步加载工作流，不阻塞UI渲染
  loadingWorkflow.value = true
  importExampleWorkflow()
    .catch((e) => {
      console.error('Failed to import example workflow:', e)
    })
    .finally(() => {
      loadingWorkflow.value = false
      initialLoadDone.value = true
    })
})
const onNodeDragStart = () => {}

const onNodeSelect = (nodeId: string | null) => {
  workflowStore.selectNode(nodeId)
  if (nodeId) {
    // 当选中节点时，自动打开左侧侧边栏并切换到属性面板
    if (!primarySidebarVisible.value) {
      primarySidebarVisible.value = true
      saveLayoutState(STORAGE_KEYS.primarySidebarVisible, true)
    }
    leftSidebarTab.value = 'properties'
  }
}

// 上下文菜单处理函数
const onContextMenu = (event: MouseEvent | TouchEvent, context: string, data?: any) => {
  const items = (() => {
    if (context === 'canvas') {
      return [
        {
          key: 'paste',
          label: '粘贴节点',
          description: '从剪贴板粘贴节点',
          icon: CopyDocument,
          shortcut: 'Ctrl+V',
          action: () => {
            ElMessage.info('粘贴功能开发中...')
          }
        },
        {
          key: 'clear',
          label: '清空画布',
          description: '删除画布上的所有节点',
          icon: Delete,
          action: async () => {
            try {
              await ElMessageBox.confirm('确定要清空画布吗？此操作不可撤销。', '清空画布', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
              })
              ElMessage.success('画布已清空')
            } catch {
              // User cancelled
            }
          }
        },
        {
          key: 'settings',
          label: '画布设置',
          description: '配置画布选项',
          icon: Edit,
          action: () => {
            ElMessage.info('画布设置功能开发中...')
          }
        }
      ]
    }

    if (context === 'node' && data) {
      return [
        {
          key: 'configure',
          label: '配置节点',
          description: '打开节点属性面板',
          icon: Edit,
          action: () => {
            workflowStore.selectNode(data.id)
            ElMessage.info('节点配置面板开发中...')
          }
        },
        {
          key: 'copy',
          label: '复制节点',
          description: '复制选中节点',
          icon: CopyDocument,
          shortcut: 'Ctrl+C',
          action: () => {
            ElMessage.info('复制节点功能开发中...')
          }
        },
        {
          key: 'delete',
          label: '删除节点',
          description: '从画布移除此节点',
          icon: Delete,
          shortcut: 'Delete',
          action: () => {
            workflowStore.deleteNode(data.id)
            ElMessage.success('已删除节点')
          }
        }
      ]
    }

    if (context === 'edge' && data) {
      return [
        {
          key: 'delete-edge',
          label: '删除连接',
          description: '移除此连线',
          icon: Delete,
          shortcut: 'Delete',
          action: () => {
            workflowStore.deleteConnection(data.id)
            ElMessage.success('已删除连接')
          }
        }
      ]
    }

    return []
  })()

  if (items.length > 0) {
    contextMenu.showContextMenu(event, items)
  } else {
    contextMenu.hideContextMenu()
  }
}

// 删除选中节点
const deleteSelectedNode = () => {
  const id = workflowStore.selectedNode?.id ?? null
  if (id) {
    workflowStore.deleteNode(id)
    ElMessage.success('已删除节点')
  } else {
    ElMessage.info('请先选中要删除的节点')
  }
}

// 撤销处理函数
const handleUndo = () => {
  if (workflowStore.undo()) {
    ElMessage.success('撤销成功')
  } else {
    ElMessage.info('无法撤销')
  }
}

// 重做处理函数
const handleRedo = () => {
  if (workflowStore.redo()) {
    ElMessage.success('重做成功')
  } else {
    ElMessage.info('无法重做')
  }
}

// 自动布局处理函数
const handleAutoLayout = () => {
  if (canvasRef.value && typeof canvasRef.value.autoLayout === 'function') {
    canvasRef.value.autoLayout()
  } else {
    ElMessage.warning('布局功能暂不可用')
  }
}

// Handle toolbar menu commands
const handleToolbarCommand = async (command: string) => {
  switch (command) {
    case 'new':
      createNewWorkflow()
      break
    case 'open':
      openWorkflow()
      break
    case 'save':
      saveWorkflow()
      break
    case 'duplicate':
      duplicateWorkflow()
      break
    case 'export':
      exportWorkflow()
      break
    case 'import':
      triggerImportFile()
      break
    case 'template':
      applyTemplate('default')
      break
    case 'example':
      importExampleWorkflow()
      break
  }
}

// 定义键盘快捷键
const shortcuts: KeyboardShortcut[] = [
  {
    key: 's',
    ctrlKey: true,
    description: '保存工作流',
    action: saveWorkflow
  },
  {
    key: 'n',
    ctrlKey: true,
    description: '新建工作流',
    action: createNewWorkflow
  },
  {
    key: 'o',
    ctrlKey: true,
    description: '打开工作流',
    action: openWorkflow
  },
  {
    key: 'z',
    ctrlKey: true,
    description: '撤销',
    action: () => {
      if (workflowStore.undo()) {
        ElMessage.success('撤销成功')
      } else {
        ElMessage.info('无法撤销')
      }
    }
  },
  {
    key: 'y',
    ctrlKey: true,
    description: '重做',
    action: () => {
      if (workflowStore.redo()) {
        ElMessage.success('重做成功')
      } else {
        ElMessage.info('无法重做')
      }
    }
  },
  {
    key: 'Delete',
    description: '删除选中节点',
    action: deleteSelectedNode
  },
  {
    key: '0',
    ctrlKey: true,
    description: '重置视图',
    action: () => {
      canvasRef.value?.fitView?.()
    }
  },
  {
    key: '=',
    ctrlKey: true,
    description: '放大画布',
    action: () => {
      canvasRef.value?.zoomIn?.()
    }
  },
  {
    key: '+',
    ctrlKey: true,
    description: '放大画布 (Shift+Ctrl++)',
    action: () => {
      canvasRef.value?.zoomIn?.()
    }
  },
  {
    key: '-',
    ctrlKey: true,
    description: '缩小画布',
    action: () => {
      canvasRef.value?.zoomOut?.()
    }
  },
  {
    key: 'F5',
    description: '执行工作流',
    action: executeWorkflow
  }
]

// Register keyboard shortcuts
useKeyboardShortcuts(shortcuts)
</script>

<style scoped>
.workflow-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--ctp-base);
}

.toolbar {
  flex-shrink: 0;
  flex-grow: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 12px;
  background: var(--ctp-mantle);
  border-bottom: 1px solid var(--ctp-surface0);
}

.toolbar-left,
.toolbar-center,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 4px;
}

.toolbar-center {
  flex: 1;
  justify-content: center;
}

.view-controls {
  display: flex;
  align-items: center;
  gap: 2px;
}

.action-group {
  display: flex;
  align-items: center;
  gap: 2px;
}

.workflow-info {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: var(--ctp-subtext1);
  white-space: nowrap;
}

.workflow-info .el-icon {
  color: var(--icon-muted);
}

.info-item {
  display: flex;
  align-items: center;
  gap: 4px;
  align-items: center;
  gap: 4px;
}

.info-item:not(:last-child)::after {
  content: '';
  width: 1px;
  height: 12px;
  background: var(--ctp-surface1);
  margin-left: 8px;
}

/* Workspace: Main content area with VS Code-style layout */
.workspace {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

/* Editor Row: Horizontal flex for canvas and sidebars */
.editor-row {
  flex: 1;
  display: flex;
  flex-direction: row;
  overflow: hidden;
  min-height: 0;
}

.main-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
}

/* Primary Sidebar: Node Palette */
.node-palette-container.primary-sidebar {
  width: 280px;
  flex-shrink: 0;
  transition: width 0.2s ease;
  will-change: width;
  overflow: hidden;
}

.node-palette-container.primary-sidebar.collapsed {
  width: 0;
  display: none;
}

.left-sidebar-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.left-sidebar-tabs :deep(.el-tabs__content) {
  flex: 1;
  overflow: auto;
}

.left-sidebar-tabs :deep(.el-tab-pane) {
  height: 100%;
  overflow: auto;
}

/* Canvas Container: Center area */
.canvas-container {
  flex: 1;
  background: var(--ctp-base);
  margin: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  min-width: 300px;
  min-height: 0;
  overflow: hidden;
  position: relative;
}

/* Secondary Sidebar: Property Panel */
.file-browser-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

/* Resizer handles */
.resizer-handle {
  width: 4px;
  background: transparent;
  cursor: col-resize;
  transition: background 0.2s;
  flex-shrink: 0;
}

.resizer-handle:hover {
  background: var(--ctp-blue);
}

/* Panel Container: Bottom panel for logs */
.panel-container {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--ctp-mantle);
  border-top: 1px solid var(--ctp-surface0);
  transition: height 0.2s ease;
  will-change: height;
  overflow: hidden;
}

.panel-container.collapsed {
  height: 0 !important;
}

.panel-resizer {
  height: 4px;
  background: transparent;
  cursor: row-resize;
  transition: background 0.2s;
  flex-shrink: 0;
}

.panel-resizer:hover {
  background: var(--ctp-blue);
}

/* Logs Panel */
.logs-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--ctp-mantle);
  overflow: hidden;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--ctp-surface0);
  font-size: 12px;
  color: var(--ctp-subtext1);
  flex-shrink: 0;
}

.logs-header-current {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
}

.logs-body {
  flex: 1;
  padding: 8px 12px;
  overflow: auto;
  font-family: monospace;
  font-size: 12px;
  line-height: 1.6;
  min-height: 0;
  color: var(--ctp-text);
}

.log-line {
  white-space: pre-wrap;
}

.logs-empty {
  color: var(--ctp-overlay0);
  font-style: italic;
  padding: 8px 0;
}

.logs-history {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.logs-history .history-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  background: var(--ctp-surface0);
  border-radius: 4px;
  font-size: 12px;
}

.logs-history .history-id {
  font-family: monospace;
  color: var(--ctp-overlay0);
  min-width: 72px;
}

.logs-history .history-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.logs-history .history-time {
  color: var(--ctp-subtext1);
  font-size: 11px;
}

/* Responsive breakpoints */
@media (max-width: 1024px) {
  .secondary-sidebar {
    position: absolute;
    right: 0;
    top: 0;
    bottom: 0;
    z-index: 100;
    box-shadow: -2px 0 8px rgba(0, 0, 0, 0.1);
  }
}

@media (max-width: 768px) {
  .node-palette-container.primary-sidebar {
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 100;
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
  }

  .canvas-container {
    margin: 8px;
  }
}
</style>
