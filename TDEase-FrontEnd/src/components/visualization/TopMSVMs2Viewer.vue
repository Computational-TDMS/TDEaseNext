<template>
  <div class="topmsv-ms2-viewer">
    <div class="viewer-toolbar">
      <div class="toolbar-left">
        <el-tag v-if="selectedPrsmId !== null" type="info" size="small">
          PrSM {{ selectedPrsmId }}
        </el-tag>
        <el-tag v-if="currentSpectrumId !== null" type="success" size="small">
          Spectrum {{ currentSpectrumId }}
        </el-tag>
        <el-tag v-if="rawPeakCount > 0" type="info" size="small">
          {{ rawPeakCount }} raw peaks
        </el-tag>
        <el-tag v-if="matchedPeaks.length > 0" type="warning" size="small">
          {{ matchedPeaks.length }} deconvoluted peaks
        </el-tag>
      </div>
      <div class="toolbar-right">
        <el-select
          v-if="spectrumOptions.length > 1"
          v-model="selectedSpectrumId"
          size="small"
          style="width: 140px"
        >
          <el-option
            v-for="specId in spectrumOptions"
            :key="specId"
            :label="`Spectrum ${specId}`"
            :value="specId"
          />
        </el-select>
      </div>
    </div>

    <div v-if="!sourceMeta" class="state-pane">
      Missing TopPIC HTML source metadata.
    </div>
    <div v-else-if="selectedPrsmId === null" class="state-pane">
      Select a PrSM row in the table to inspect MS2 details.
    </div>
    <div v-else-if="loading" class="state-pane">
      Loading MS2 data...
    </div>
    <div v-else-if="errorMessage" class="state-pane error-pane">
      {{ errorMessage }}
    </div>
    <div v-else-if="!payload || !spectrumData" class="state-pane">
      No MS2 spectrum data available.
    </div>
    <div v-else class="viewer-content">
      <div class="spectrum-panel">
        <SpectrumViewer
          :data="spectrumData"
          :config="spectrumConfig"
          :selection="null"
          @selection-change="handleSpectrumSelectionChange"
        />
      </div>
      <div class="table-panel">
        <el-table :data="matchedPeaks" size="small" height="100%" stripe>
          <el-table-column prop="peak_id" label="Peak ID" min-width="90" />
          <el-table-column prop="monoisotopic_mass" label="Mono Mass" min-width="140">
            <template #default="{ row }">
              {{ formatNumber(row.monoisotopic_mass, 4) }}
            </template>
          </el-table-column>
          <el-table-column prop="monoisotopic_mz" label="Mono m/z" min-width="130">
            <template #default="{ row }">
              {{ formatNumber(row.monoisotopic_mz, 4) }}
            </template>
          </el-table-column>
          <el-table-column prop="intensity" label="Intensity" min-width="130">
            <template #default="{ row }">
              {{ formatNumber(row.intensity, 0) }}
            </template>
          </el-table-column>
          <el-table-column prop="charge" label="Charge" min-width="90" />
          <el-table-column prop="matched_ion_labels" label="Matched Ions" min-width="200" />
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { getAPIClient } from '@/services/api/client'
import { workspaceDataApi } from '@/services/api/workspace-data'
import type { TopMSVMatchedPeak, TopMSVPrsmDataResponse } from '@/types/workspace-data'
import type { SelectionState, TableData } from '@/types/visualization'
import { useWorkflowStore } from '@/stores/workflow'
import SpectrumViewer from './SpectrumViewer.vue'

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

const props = defineProps<Props>()
const workflowStore = useWorkflowStore()

defineEmits<{
  selectionChange: [selection: SelectionState]
  configChange: [config: Record<string, unknown>]
}>()

const loading = ref(false)
const errorMessage = ref('')
const payload = ref<TopMSVPrsmDataResponse | null>(null)
const selectedSpectrumId = ref<number | null>(null)
const suppressSpectrumWatcher = ref(false)
let currentRequestToken = 0

function toNumericId(value: unknown): number | null {
  if (value === null || value === undefined || value === '') return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

function formatNumber(value: unknown, digits: number): string {
  const parsed = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(parsed)) return ''
  return parsed.toFixed(digits)
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

async function loadTopMSVData(overrideSpectrumId: number | null = null) {
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
      spectrum_id: overrideSpectrumId === null ? undefined : overrideSpectrumId,
      sample: sourceMeta.value.sample,
    })
    if (requestToken !== currentRequestToken) return
    payload.value = response

    suppressSpectrumWatcher.value = true
    selectedSpectrumId.value = response.ms2.selected_spectrum_id
    suppressSpectrumWatcher.value = false
  } catch (error) {
    if (requestToken !== currentRequestToken) return
    payload.value = null
    errorMessage.value = error instanceof Error ? error.message : 'Failed to load TopMSV MS2 data.'
  } finally {
    if (requestToken === currentRequestToken) {
      loading.value = false
    }
  }
}

watch(
  () => [sourceMeta.value?.executionId, sourceMeta.value?.nodeId, sourceMeta.value?.portId, selectedPrsmId.value],
  () => {
    suppressSpectrumWatcher.value = true
    selectedSpectrumId.value = null
    suppressSpectrumWatcher.value = false
    void loadTopMSVData(null)
  },
  { immediate: true }
)

watch(
  () => selectedSpectrumId.value,
  (nextSpectrumId) => {
    if (suppressSpectrumWatcher.value) return
    if (nextSpectrumId === null) return
    if (nextSpectrumId === payload.value?.ms2?.selected_spectrum_id) return
    void loadTopMSVData(nextSpectrumId)
  }
)

const currentSpectrumId = computed(() => payload.value?.ms2?.selected_spectrum_id ?? null)
const spectrumOptions = computed(() => payload.value?.ms2?.available_spectrum_ids || [])
const rawPeakCount = computed(() => payload.value?.ms2?.raw_peak_count || 0)

const matchedPeaks = computed<TopMSVMatchedPeak[]>(() => {
  const rows = payload.value?.ms2?.matched_peaks || []
  const spectrumId = currentSpectrumId.value
  if (spectrumId === null) return rows
  return rows.filter((row) => row.spec_id === null || row.spec_id === spectrumId)
})

const spectrumData = computed<TableData | null>(() => {
  const rawPeaks = payload.value?.ms2?.raw_peaks || []
  if (rawPeaks.length === 0) return null

  const rows = rawPeaks.map((peak) => ({
    index: peak.index,
    mz: peak.mz,
    intensity: peak.intensity,
  }))

  return {
    columns: [
      { id: 'mz', name: 'm/z', type: 'number', visible: true, sortable: true, filterable: true },
      { id: 'intensity', name: 'Intensity', type: 'number', visible: true, sortable: true, filterable: true },
    ],
    rows,
    totalRows: rows.length,
    sourceFile: payload.value?.source?.spectrum_file || `prsm-${selectedPrsmId.value ?? 'unknown'}-ms2`,
  }
})

const spectrumConfig = computed(() => ({
  mzColumn: 'mz',
  intensityColumn: 'intensity',
}))

function handleSpectrumSelectionChange(_selection: SelectionState) {
  // Keep table selection as the source of truth for cross-node state.
}
</script>

<script lang="ts">
export default {
  name: 'TopMSVMs2Viewer',
}
</script>

<style scoped>
.topmsv-ms2-viewer {
  display: flex;
  flex-direction: column;
  gap: 8px;
  height: 100%;
}

.viewer-toolbar {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.toolbar-left,
.toolbar-right {
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

.viewer-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 0;
  height: 100%;
}

.spectrum-panel {
  min-height: 220px;
  flex: 0 0 52%;
}

.table-panel {
  min-height: 180px;
  flex: 1 1 auto;
}
</style>
