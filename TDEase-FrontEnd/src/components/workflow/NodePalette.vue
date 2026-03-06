<template>
  <div class="node-palette">
    <h3>节点工具箱</h3>

    <div class="palette-search">
      <el-input
        v-model="searchQuery"
        placeholder="搜索节点名称或描述..."
        clearable
        size="small"
        :prefix-icon="Search"
      />
    </div>

    <div class="palette-section">
      <div class="section-title">基础节点</div>
      <div class="tool-list">
        <div
          v-for="basic in filteredBasicNodes"
          :key="basic.type"
          class="tool-item"
          :class="basic.type"
          draggable="true"
          @dragstart="(e) => onDragStartBasic(e, basic.type)"
        >
          <div class="tool-icon" />
          <div class="tool-info">
            <div class="tool-name">{{ basic.name }}</div>
            <div class="tool-desc">{{ basic.desc }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="palette-section">
      <div class="section-title">工具注册</div>
      <div class="tool-list">
        <div
          v-for="tool in filteredRegistryEntries"
          :key="tool.id"
          class="tool-item command"
          draggable="true"
          @dragstart="(e) => onDragStart(e, tool)"
          title="拖拽到画布以创建节点"
        >
          <div class="tool-icon" />
          <div class="tool-info">
            <div class="tool-name">{{ tool.name }}</div>
            <div class="tool-desc">{{ tool.description }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
  </template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { useToolsRegistry, ensureToolsLoaded } from '@/services/tools/registry'
import type { ToolConfig, ToolPort } from '@/services/tools/registry'

const emit = defineEmits<{
  dragStart: [event: DragEvent]
}>()

type PaletteTool = ToolConfig

const searchQuery = ref('')
const tools = useToolsRegistry()
const registryEntries = computed<PaletteTool[]>(() => tools.value)

onMounted(async () => {
  await ensureToolsLoaded()
})

const BASIC_NODES: { type: 'input' | 'process' | 'output'; name: string; desc: string }[] = [
  { type: 'input', name: '输入节点', desc: '提供数据源，右侧输出' },
  { type: 'process', name: '处理节点', desc: '左侧输入，右侧输出' },
  { type: 'output', name: '输出节点', desc: '左侧输入，汇聚结果' }
]

const filteredBasicNodes = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return BASIC_NODES
  return BASIC_NODES.filter(
    (n) => n.name.toLowerCase().includes(q) || n.desc.toLowerCase().includes(q)
  )
})

const filteredRegistryEntries = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return registryEntries.value
  return registryEntries.value.filter(
    (t) =>
      (t.name && t.name.toLowerCase().includes(q)) ||
      (t.description && t.description.toLowerCase().includes(q)) ||
      (t.id && t.id.toLowerCase().includes(q))
  )
})

const colorByKind = (kind?: 'script' | 'command') => kind === 'script' ? '#4CAF50' : '#2196F3'

const onDragStart = (event: DragEvent, tool: PaletteTool) => {
  if (!event.dataTransfer) return

  const ins: ToolPort[] = tool.inputs ? [...tool.inputs] : []
  const inputs = ins.map((p) => ({
    id: p.id,
    name: p.name,
    type: p.type || 'file',
    required: !!p.required,
    accept: Array.isArray((p as any).accept) ? (p as any).accept : undefined,
    dataType: (p as any).dataType
  }))

  const outs: ToolPort[] = tool.outputs ? [...tool.outputs] : []
  const outputs = outs.map((o) => ({
    id: o.id,
    name: o.name,
    type: o.type || 'file',
    required: !!o.required,
    pattern: (o as any).pattern,
    provides: Array.isArray((o as any).provides) ? (o as any).provides : undefined,
    dataType: (o as any).dataType
  }))

  const payload = {
    type: 'tool',
    name: tool.name,
    displayProperties: {
      label: tool.name,
      color: colorByKind(tool.kind)
    },
    inputs,
    outputs,
    nodeConfig: {
      toolId: tool.id,
      executionMode: tool.executionMode,
      toolPath: tool.toolPath,
      inputs,
      outputs,
      params: tool.params || []
    }
  }

  event.dataTransfer.setData('text/plain', JSON.stringify(payload))
  event.dataTransfer.effectAllowed = 'move'
  emit('dragStart', event)
}

const onDragStartBasic = (event: DragEvent, type: 'input' | 'process' | 'output') => {
  if (!event.dataTransfer) return
  const payload = {
    type,
    name: type,
    displayProperties: {
      label: type === 'input' ? '输入' : type === 'process' ? '处理' : '输出',
      color: type === 'input' ? '#4CAF50' : type === 'process' ? '#2196F3' : '#FF9800'
    },
    inputs: type === 'input' ? [] : [{ id: 'input', name: '输入', type: 'file', required: false }],
    outputs: type === 'output' ? [] : [{ id: 'output', name: '输出', type: 'file', required: false }],
    nodeConfig: {}
  }
  event.dataTransfer.setData('text/plain', JSON.stringify(payload))
  event.dataTransfer.effectAllowed = 'move'
  emit('dragStart', event)
}
</script>

<style scoped>
.node-palette {
  width: 280px;
  height: 100%;
  background: var(--ctp-mantle);
  border-right: 1px solid var(--ctp-surface0);
  overflow-y: auto;
  padding: 16px;
}

.node-palette h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--ctp-text);
}

.palette-search {
  margin-bottom: 12px;
}

.palette-search :deep(.el-input__wrapper) {
  border-radius: 8px;
}

.palette-section {
  margin-bottom: 20px;
}

.section-title {
  font-size: 13px;
  color: var(--ctp-subtext0);
  margin-bottom: 8px;
}

.tool-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tool-item {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--ctp-base);
  border: 1px solid var(--ctp-surface0);
  border-radius: 8px;
  padding: 10px;
  cursor: grab;
  transition: background 0.2s, border-color 0.2s;
}

.tool-item:hover {
  background: var(--ctp-surface0);
  border-color: var(--ctp-surface1);
}

.tool-item:active {
  cursor: grabbing;
}

.tool-item.script {
  border-left: 4px solid var(--ctp-green);
}

.tool-item.command {
  border-left: 4px solid var(--ctp-blue);
}

.tool-icon {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  background: color-mix(in srgb, var(--ctp-blue) 15%, transparent);
  color: var(--icon-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.tool-info {
  flex: 1;
}

.tool-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--ctp-text);
}

.tool-desc {
  font-size: 12px;
  color: var(--ctp-subtext0);
}
</style>
