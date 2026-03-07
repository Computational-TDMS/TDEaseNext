<template>
  <div class="topmsv-sequence-viewer">
    <div class="viewer-toolbar">
      <div class="toolbar-left">
        <el-tag v-if="selectedPrsmId !== null" type="info" size="small">
          PrSM {{ selectedPrsmId }}
        </el-tag>
        <el-tag v-if="proteinAccession" type="success" size="small">
          {{ proteinAccession }}
        </el-tag>
        <el-tag v-if="breakpoints.length" type="warning" size="small">
          {{ breakpoints.length }} breakpoints
        </el-tag>
      </div>
    </div>

    <div v-if="!sourceMeta" class="state-pane">
      Missing TopPIC HTML source metadata.
    </div>
    <div v-else-if="selectedPrsmId === null" class="state-pane">
      Select a PrSM row in the table to inspect sequence details.
    </div>
    <div v-else-if="loading" class="state-pane">
      Loading sequence details...
    </div>
    <div v-else-if="errorMessage" class="state-pane error-pane">
      {{ errorMessage }}
    </div>
    <div v-else-if="!payload" class="state-pane">
      No sequence data available.
    </div>
    <div v-else class="sequence-content">
      <div class="sequence-block">
        <div class="block-title">Proteoform Sequence</div>
        <div class="sequence-text annotated-sequence">
          <span
            v-for="residue in annotatedSequence"
            :key="residue.position"
            class="aa"
            :class="{
              modified: residue.modLabels.length > 0,
              breakpoint: residue.hasBreakpointAfter,
            }"
            :title="residue.modLabels.length ? residue.modLabels.join(', ') : `Position ${residue.position}`"
          >
            {{ residue.char }}
          </span>
        </div>
      </div>

      <div class="mods-block">
        <div class="block-title">Modifications</div>
        <div v-if="modifications.length === 0" class="mod-note">No PTM/mass-shift annotation.</div>
        <div v-else class="mod-list">
          <div
            v-for="(mod, index) in modifications"
            :key="`${mod.kind}-${mod.left_position}-${mod.right_position}-${index}`"
            class="mod-line"
          >
            <span class="label">
              {{ mod.kind === 'mass_shift' ? 'Shift' : 'PTM' }}
            </span>
            <span>[{{ mod.left_position ?? '?' }}-{{ mod.right_position ?? '?' }}]</span>
            <span>{{ mod.label }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { getAPIClient } from '@/services/api/client'
import { workspaceDataApi } from '@/services/api/workspace-data'
import type { TopMSVPrsmDataResponse } from '@/types/workspace-data'
import type { SelectionState, TableData } from '@/types/visualization'
import { useWorkflowStore } from '@/stores/workflow'

interface Props {
  data: TableData | null
  config?: Record<string, unknown>
  selection?: SelectionState | null
}

interface SourceMeta {
  workflowId: string
  nodeId: string
  portId: string
  executionId?: string
  sample?: string
}

interface ResidueView {
  position: number
  char: string
  modLabels: string[]
  hasBreakpointAfter: boolean
}

const props = defineProps<Props>()
const workflowStore = useWorkflowStore()

defineEmits<{
  selectionChange: [selection: SelectionState]
  configChange: [config: Record<string, unknown>]
}>()

const loading = ref(false)
const errorMessage = ref('')
const payload = ref<TopMSVPrsmDataResponse | null>(null)
let currentRequestToken = 0

function toNumericId(value: unknown): number | null {
  if (value === null || value === undefined || value === '') return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

const selectedPrsmId = computed<number | null>(() => {
  const indices = props.selection?.selectedIndices
  if (!indices || indices.size === 0) return null
  for (const value of indices) {
    const parsed = toNumericId(value)
    if (parsed !== null) return parsed
  }
  return null
})

const sourceMeta = computed<SourceMeta | null>(() => {
  const row = (props.data?.rows?.[0] || null) as Record<string, unknown> | null
  if (!row) return null
  const workflowId = String(row.__workflow_id || workflowStore.currentWorkflow?.metadata?.id || '').trim()
  const nodeId = String(row.__node_id || '').trim()
  const portId = String(row.__port_id || '').trim() || 'html_folder'
  const executionId = String(row.__execution_id || '').trim()
  const sample = String(row.__sample || '').trim()
  if (!nodeId || (!workflowId && !executionId)) return null
  return {
    workflowId,
    nodeId,
    portId,
    executionId: executionId || undefined,
    sample: sample || undefined,
  }
})

async function loadTopMSVData() {
  if (!sourceMeta.value || selectedPrsmId.value === null) {
    payload.value = null
    errorMessage.value = ''
    return
  }

  let apiClient
  try {
    apiClient = getAPIClient()
  } catch (error) {
    payload.value = null
    errorMessage.value = error instanceof Error ? error.message : 'API client is not initialized.'
    return
  }
  const requestToken = ++currentRequestToken
  loading.value = true
  errorMessage.value = ''

  try {
    const response = await workspaceDataApi.getTopMSVPrsmData(apiClient, {
      workflow_id: sourceMeta.value.workflowId || undefined,
      execution_id: sourceMeta.value.executionId,
      node_id: sourceMeta.value.nodeId,
      port_id: sourceMeta.value.portId,
      prsm_id: selectedPrsmId.value,
      sample: sourceMeta.value.sample,
    })
    if (requestToken !== currentRequestToken) return
    payload.value = response
  } catch (error) {
    if (requestToken !== currentRequestToken) return
    payload.value = null
    errorMessage.value = error instanceof Error ? error.message : 'Failed to load TopMSV sequence data.'
  } finally {
    if (requestToken === currentRequestToken) {
      loading.value = false
    }
  }
}

watch(
  () => [sourceMeta.value?.executionId, sourceMeta.value?.nodeId, sourceMeta.value?.portId, selectedPrsmId.value],
  () => {
    void loadTopMSVData()
  },
  { immediate: true }
)

const proteinAccession = computed(() => payload.value?.protein_accession || '')
const sequence = computed(() => payload.value?.sequence?.value || '')
const breakpoints = computed(() => payload.value?.sequence?.breakpoints || [])
const modifications = computed(() => payload.value?.sequence?.modifications || [])

const annotatedSequence = computed<ResidueView[]>(() => {
  const seq = sequence.value
  if (!seq) return []
  const breakpointSet = new Set<number>(breakpoints.value)

  return Array.from(seq).map((char, idx) => {
    const position = idx + 1
    const labels = modifications.value
      .filter((mod) => {
        const left = mod.left_position ?? Number.MIN_SAFE_INTEGER
        const right = mod.right_position ?? left
        return position >= left && position <= right
      })
      .map((mod) => mod.label)

    return {
      position,
      char,
      modLabels: labels,
      hasBreakpointAfter: breakpointSet.has(position),
    }
  })
})
</script>

<script lang="ts">
export default {
  name: 'TopMSVSequenceViewer',
}
</script>

<style scoped>
.topmsv-sequence-viewer {
  display: flex;
  flex-direction: column;
  gap: 8px;
  height: 100%;
}

.viewer-toolbar {
  display: flex;
  justify-content: space-between;
}

.toolbar-left {
  display: flex;
  gap: 8px;
  align-items: center;
}

.state-pane {
  border: 1px dashed #dcdfe6;
  border-radius: 6px;
  padding: 16px;
  color: #606266;
  background: #fafafa;
}

.error-pane {
  color: #f56c6c;
}

.sequence-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.sequence-block,
.mods-block {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 10px;
  background: #fff;
}

.block-title {
  font-size: 12px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.sequence-text {
  margin: 0;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  white-space: pre-wrap;
  word-break: break-all;
  color: #303133;
}

.annotated-sequence {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  line-height: 1.5;
}

.aa {
  display: inline-flex;
  min-width: 0.7em;
  justify-content: center;
}

.aa.modified {
  background: #fdf6ec;
  color: #e6a23c;
  border-radius: 2px;
  font-weight: 600;
}

.aa.breakpoint {
  border-right: 2px solid #67c23a;
  margin-right: 1px;
  padding-right: 1px;
}

.mod-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.mod-line {
  display: grid;
  grid-template-columns: 54px 90px 1fr;
  gap: 8px;
  font-size: 12px;
}

.label {
  color: #606266;
  font-weight: 600;
}

.mod-note {
  font-size: 12px;
  color: #909399;
}
</style>
