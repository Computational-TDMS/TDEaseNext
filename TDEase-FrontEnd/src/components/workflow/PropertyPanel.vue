<template>
  <div class="property-panel">
    <template v-if="selectedNode">
      <el-form :model="form" :rules="rules" label-width="100px" @submit.prevent>
        <el-divider>基本属性</el-divider>
        <el-form-item label="名称">
          <el-input v-model="form.label" />
        </el-form-item>
        <el-form-item label="颜色">
          <el-color-picker v-model="form.color" />
        </el-form-item>

        <el-divider>参数配置</el-divider>
        <template v-for="(p, key) in parameters" :key="key">
          <el-form-item :label="p.label || key" :prop="`params.${key}`">
            <template v-if="p.type === 'choice'">
              <el-select v-model="form.params[key]">
                <el-option v-for="opt in p.choices || []" :key="String(opt)" :label="opt" :value="opt" />
              </el-select>
            </template>
            <template v-else-if="p.type === 'boolean'">
              <el-switch v-model="form.params[key]" />
            </template>
            <template v-else>
              <el-input v-model="form.params[key]" :type="getInputType(p)" />
            </template>
            <div class="help" v-if="p.description">{{ p.description }}</div>
            <div class="group-tag" v-if="p.group">{{ p.group }}</div>
          </el-form-item>
        </template>

        <el-divider>命令预览</el-divider>
        <el-input
          type="textarea"
          :rows="6"
          :model-value="finalPreview"
          :loading="serverPreviewLoading"
          readonly
        />
        <div v-if="serverPreviewError" class="preview-error">
          <el-text type="danger">{{ serverPreviewError }}</el-text>
        </div>
        <div v-if="serverPreview" class="preview-badge">
          <el-tag type="success" size="small">服务端预览</el-tag>
          <el-tooltip content="使用与实际执行相同的命令构建逻辑">
            <el-icon><QuestionFilled /></el-icon>
          </el-tooltip>
        </div>

        <el-divider>端口</el-divider>
        <div class="ports">
          <div class="port-group">
            <div class="group-title">输入 ({{ inputs.length }})</div>
            <div class="port-item" v-for="ip in inputs" :key="ip.id">
              <el-tag type="primary">{{ ip.name || ip.id }}</el-tag>
              <el-tag type="info" v-if="ip.dataType">{{ ip.dataType }}</el-tag>
              <el-tag type="success" v-if="ip.accept">{{ ip.accept.join(',') }}</el-tag>
              <el-tag type="warning" v-if="ip.positional">positional: {{ ip.positionalOrder }}</el-tag>
              <el-tag type="danger" v-if="ip.required">必需</el-tag>
            </div>
          </div>
          <div class="port-group">
            <div class="group-title">输出 ({{ outputs.length }})</div>
            <div class="port-item" v-for="op in outputs" :key="op.id">
              <el-tag type="primary">{{ op.name || op.id }}</el-tag>
              <el-tag type="info" v-if="op.dataType">{{ op.dataType }}</el-tag>
              <el-tag type="success" v-if="op.pattern">{{ op.pattern }}</el-tag>
            </div>
          </div>
        </div>

        <div class="actions">
          <el-button type="primary" @click="applyChanges">应用</el-button>
        </div>
      </el-form>
    </template>
    <div v-else class="empty-state">
      <div class="empty-icon">📝</div>
      <p>未选择节点</p>
      <p>请点击画布上的节点以编辑属性</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { NodeDefinition } from '@/stores/workflow'
import { useWorkflowStore } from '@/stores/workflow'
import { useToolsRegistry, ensureToolsLoaded } from '@/services/tools/registry'
import { ref, computed, watch, onMounted } from 'vue'
import axios from 'axios'
import { QuestionFilled } from '@element-plus/icons-vue'

const form = ref<any>({
  label: '',
  color: '#409eff',
  params: {}
})

const props = defineProps<{ selectedNode?: NodeDefinition | null }>()
const selectedNode = computed(() => props.selectedNode || null)
const workflowStore = useWorkflowStore()
const toolsRegistry = useToolsRegistry()

const serverPreview = ref<string>('')
const serverPreviewLoading = ref(false)
const serverPreviewError = ref<string>('')

const toolCfg = computed(() => {
  const node = selectedNode.value
  if (!node) return null as any
  const rawToolId =
    (node.nodeConfig as any)?.toolId ||
    (node.data as any)?.toolId ||
    (node.data as any)?.type ||
    (node.type !== 'tool' ? node.type : null)
  const toolId = typeof rawToolId === 'string' ? rawToolId.trim() : null
  return toolsRegistry.value.find((t) => t.id === toolId) || null
})

onMounted(async () => {
  await ensureToolsLoaded()
})

// 新 Schema: parameters 对象
const parameters = computed(() => toolCfg.value?.parameters || {})

// 新 Schema: ports.inputs 和 ports.outputs
const inputs = computed(() => toolCfg.value?.ports?.inputs || [])
const outputs = computed(() => toolCfg.value?.ports?.outputs || [])

watch(selectedNode, (node) => {
  if (!node) return
  form.value.label = node.displayProperties?.label || node.data?.label || ''
  form.value.color = node.displayProperties?.color || node.data?.color || '#409eff'
  const saved = (node.nodeConfig as any)?.paramValues || {}
  const params = parameters.value
  const nextVals: Record<string, any> = {}
  for (const [key, p] of Object.entries(params)) {
    const v = saved[key]
    const paramDef = p as any
    nextVals[key] = v !== undefined ? v : (paramDef.default !== undefined ? paramDef.default : null)
  }
  form.value.params = nextVals
}, { immediate: true })

// Fetch server preview when params change (debounced)
let previewTimeout: ReturnType<typeof setTimeout> | null = null
watch(() => form.value.params, () => {
  if (previewTimeout) clearTimeout(previewTimeout)
  previewTimeout = setTimeout(() => {
    fetchServerPreview()
  }, 300) // 300ms debounce
}, { deep: true })

const rules = {}

const getInputType = (p: any) => {
  if (p.type === 'number') return 'number'
  return 'text'
}

// Fetch server-side command preview
const fetchServerPreview = async () => {
  const node = selectedNode.value
  const tool = toolCfg.value
  if (!node || !tool) {
    serverPreview.value = ''
    return
  }

  serverPreviewLoading.value = true
  serverPreviewError.value = ''

  try {
    const response = await axios.post('/api/tools/preview', {
      tool_id: tool.id,
      param_values: form.value.params,
      input_files: {}, // Empty to use placeholders like <input_port>
      output_target: null // Null to use placeholder like <output_dir>
    })
    serverPreview.value = response.data.command
  } catch (error: any) {
    serverPreviewError.value = error.response?.data?.detail || 'Failed to load preview'
    serverPreview.value = ''
  } finally {
    serverPreviewLoading.value = false
  }
}

// Client-side preview (fallback)
const cliPreview = computed(() => {
  const node = selectedNode.value
  if (!node) return ''
  const tool = toolCfg.value
  if (!tool) return ''

  const parts: string[] = []

  // 命令前缀
  const executable = tool.command?.executable || tool.id || ''
  parts.push(executable)

  // 参数标志
  const params = parameters.value
  for (const [key, p] of Object.entries(params)) {
    const paramDef = p as any
    const v = form.value.params[key]
    const flag = paramDef.flag

    if (paramDef.type === 'boolean') {
      if (v) parts.push(flag)
    } else if (paramDef.type === 'choice') {
      if (v && paramDef.choices && paramDef.choices[v] != null) {
        parts.push(String(paramDef.choices[v]))
      } else if (v) {
        parts.push(flag)
        parts.push(String(v))
      }
    } else if (paramDef.type === 'value') {
      if (v !== undefined && v !== null && v !== '') {
        parts.push(flag)
        parts.push(String(v))
      }
    }
  }

  // 输出标志
  if (tool.output?.flagSupported && tool.output?.flag) {
    parts.push(tool.output.flag)
    parts.push(tool.output.flagValue || '<output_dir>')
  }

  // 位置参数
  const positionalInputs = inputs.value
    .filter((ip: any) => ip.positional)
    .sort((a: any, b: any) => (a.positionalOrder || 0) - (b.positionalOrder || 0))

  for (const ip of positionalInputs) {
    parts.push(`<${ip.id}>`)
  }

  return parts.join(' ')
})

// Final preview (server-side with client-side fallback)
const finalPreview = computed(() => {
  if (serverPreview.value) return serverPreview.value
  return cliPreview.value
})

const applyChanges = () => {
  if (!selectedNode.value) return
  // 新架构: 后端 CommandPipeline 会过滤空参数，前端直接传递所有值
  workflowStore.updateNode(selectedNode.value.id, {
    displayProperties: {
      label: form.value.label,
      color: form.value.color
    },
    nodeConfig: {
      ...(selectedNode.value.nodeConfig || {}),
      paramValues: form.value.params
    }
  })
}
</script>

<style scoped>
.property-panel {
  width: 100%;
  height: 100%;
  background: var(--ctp-mantle);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.property-panel :deep(.el-form) {
  padding: 16px;
  flex: 1;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--ctp-overlay0);
  text-align: center;
  padding: 32px;
  height: 100%;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
  color: var(--icon-muted);
}

.empty-state p {
  margin: 0;
  font-size: 14px;
}

.empty-state p:first-child {
  font-weight: 600;
  color: var(--ctp-text);
  margin-bottom: 8px;
}

.ports {
  display: flex;
  gap: 12px;
}

.port-group {
  flex: 1;
}

.group-title {
  font-weight: 600;
  margin-bottom: 8px;
}

.port-item {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.help {
  font-size: 12px;
  color: var(--ctp-subtext0);
  margin-top: 4px;
}

.group-tag {
  font-size: 11px;
  padding: 2px 6px;
  background: var(--ctp-surface0);
  border-radius: 4px;
  color: var(--ctp-blue);
  display: inline-block;
  margin-top: 4px;
}

.actions {
  padding: 16px;
  border-top: 1px solid var(--ctp-surface0);
}

.preview-error {
  margin-top: 8px;
  padding: 8px;
  background: color-mix(in srgb, var(--ctp-red) 20%, transparent);
  border-radius: 4px;
  font-size: 12px;
}

.preview-badge {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}
</style>
