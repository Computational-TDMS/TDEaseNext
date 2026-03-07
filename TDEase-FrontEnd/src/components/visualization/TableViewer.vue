<template>
  <div class="table-viewer">
    <!-- Toolbar -->
    <div class="viewer-toolbar">
      <div class="toolbar-left">
        <el-tag v-if="selectedCount > 0" type="info" size="small">
          {{ selectedCount }} rows selected
        </el-tag>
        <el-tag v-else-if="data?.totalRows" type="info" size="small">
          {{ data.totalRows }} total rows
        </el-tag>
      </div>
      <div class="toolbar-right">
        <el-dropdown split-button type="primary" size="small" @click="exportCsv">
          Export
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="exportCsv">Export as CSV</el-dropdown-item>
              <el-dropdown-item @click="exportExcel">Export as Excel</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button size="small" :icon="Refresh" @click="clearSelection">Reset</el-button>
      </div>
    </div>

    <!-- AG Grid Container -->
    <div class="grid-container">
      <ag-grid-vue
        ref="gridRef"
        class="ag-theme-alpine"
        style="width: 100%; height: 100%"
        theme="legacy"
        :column-defs="columnDefs"
        :row-data="rowData"
        :default-col-def="defaultColDef"
        :row-selection="rowSelection"
        :pagination="true"
        :pagination-page-size="50"
        :enable-cell-text-selection="true"
        @selection-changed="onSelectionChanged"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import type { GridApi } from 'ag-grid-community'
import { Refresh } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import type { TableData, SelectionState } from '@/types/visualization'

// Register AG Grid Community Version
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'

interface Props {
  data: TableData | null
  config?: Record<string, unknown>
  selection?: SelectionState | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  selectionChange: [selection: SelectionState]
}>()

// Refs
const gridRef = ref<any>(null)
const gridApi = ref<GridApi | null>(null)

// State
const selectedIndices = ref<Set<number>>(new Set())
const isApplyingExternalSelection = ref(false)
const autoSelectionSignature = ref<string | null>(null)

// Computed
const selectedCount = computed(() => selectedIndices.value.size)
const selectionKeyField = computed<string | null>(() => {
  const cfg = props.config || {}
  const key = (cfg.selectionKeyField || cfg.selection_key_field) as string | undefined
  if (!key || typeof key !== 'string') return null
  const trimmed = key.trim()
  return trimmed || null
})

// Column definitions
const columnDefs = computed<any[]>(() => {
  if (!props.data?.columns) return []

  return props.data.columns.map(col => ({
    field: col.id,
    headerName: col.name,
    sortable: col.sortable ?? true,
    filter: col.filterable ?? true,
    resizable: true,
    flex: 1,
    minWidth: 100,
  }))
})

const defaultColDef: any = {
  sortable: true,
  filter: true,
  resizable: true,
  flex: 1,
}

const rowData = computed(() => {
  if (!props.data?.rows) return []
  return props.data.rows
})

const rowSelection = {
  mode: 'multiRow' as const,
  enableClickSelection: true,
  checkboxes: false,
  headerCheckbox: false,
}

// Methods
function toSelectionNumber(value: unknown, fallback: number | null = null): number | null {
  if (value === null || value === undefined || value === '') {
    return fallback
  }
  const parsed = Number(value)
  if (Number.isFinite(parsed)) return parsed
  return fallback
}

function resolveRowSelectionValue(rowData: Record<string, unknown>, rowIndex: number | null): number | null {
  if (selectionKeyField.value) {
    return toSelectionNumber(rowData[selectionKeyField.value], null)
  }
  return rowIndex === null ? null : rowIndex
}

function dataSignature(data: TableData | null): string {
  if (!data) return ''
  const firstColumn = data.columns?.[0]?.id || ''
  return `${data.sourceFile || ''}|${data.totalRows || 0}|${firstColumn}`
}

function applySelectionToGrid(selection: Set<number>) {
  if (!gridApi.value) return

  isApplyingExternalSelection.value = true
  gridApi.value.deselectAll()

  const nodes: any[] = []
  gridApi.value.forEachNode((node) => {
    const rowData = (node.data || {}) as Record<string, unknown>
    const selectionValue = resolveRowSelectionValue(rowData, node.rowIndex)
    if (selectionValue !== null && selection.has(selectionValue)) {
      nodes.push(node)
    }
  })

  if (nodes.length > 0) {
    gridApi.value.setNodesSelected({ nodes, newValue: true })
  }

  isApplyingExternalSelection.value = false
}

function applyDefaultSelection() {
  if (!props.data?.rows?.length) return
  const signature = dataSignature(props.data)
  if (autoSelectionSignature.value === signature) return

  // Respect upstream selections and existing local selections.
  if (props.selection?.selectedIndices?.size || selectedIndices.value.size) {
    autoSelectionSignature.value = signature
    return
  }

  const firstRow = props.data.rows[0] as Record<string, unknown>
  const firstSelectionValue = resolveRowSelectionValue(firstRow, 0)
  if (firstSelectionValue === null) {
    autoSelectionSignature.value = signature
    return
  }

  const nextSelection = new Set<number>([firstSelectionValue])
  selectedIndices.value = nextSelection
  applySelectionToGrid(nextSelection)
  emitSelectionChange()
  autoSelectionSignature.value = signature
}

function onSelectionChanged() {
  if (!gridApi.value) return
  if (isApplyingExternalSelection.value) return

  const selectedNodes = gridApi.value.getSelectedNodes()
  const newSelected = new Set<number>()

  selectedNodes.forEach(node => {
    const rowData = (node.data || {}) as Record<string, unknown>
    const selectionValue = resolveRowSelectionValue(rowData, node.rowIndex)
    if (selectionValue !== null) {
      newSelected.add(selectionValue)
    }
  })

  selectedIndices.value = newSelected
  if (props.data) {
    autoSelectionSignature.value = dataSignature(props.data)
  }
  emitSelectionChange()
}

function emitSelectionChange() {
  emit('selectionChange', {
    selectedIndices: selectedIndices.value,
    filterCriteria: [],
    brushRegion: null,
  })
}

function clearSelection() {
  if (gridApi.value) {
    gridApi.value.deselectAll()
  }
  selectedIndices.value = new Set()
  if (props.data) {
    autoSelectionSignature.value = dataSignature(props.data)
  }
  emitSelectionChange()
}

function exportCsv() {
  if (!gridApi.value) return

  const params = {
    fileName: 'table_export.csv',
    onlySelected: selectedCount.value > 0,
  }

  gridApi.value.exportDataAsCsv(params)
}

function exportExcel() {
  if (!props.data) return

  const isRowSelected = (row: Record<string, unknown>, idx: number): boolean => {
    if (selectionKeyField.value) {
      const keyValue = toSelectionNumber(row[selectionKeyField.value], null)
      return keyValue !== null && selectedIndices.value.has(keyValue)
    }
    return selectedIndices.value.has(idx)
  }

  // Get data to export (selected or all)
  const dataToExport = selectedCount.value > 0
    ? props.data.rows.filter((row, idx) => isRowSelected(row, idx))
    : props.data.rows

  // Create worksheet
  const ws = XLSX.utils.json_to_sheet(dataToExport, {
    header: props.data.columns.map(c => c.id),
  })

  // Create workbook
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'Sheet1')

  // Download
  XLSX.writeFile(wb, 'table_export.xlsx')
}

// Watch for data changes
watch(() => props.data, async () => {
  if (gridApi.value) {
    gridApi.value.setGridOption('rowData', rowData.value)
  }
  if (!props.data?.rows?.length) {
    autoSelectionSignature.value = null
    selectedIndices.value = new Set()
    return
  }
  await nextTick()
  applyDefaultSelection()
}, { deep: true })

// Watch for selection changes from props
watch(() => props.selection, (newSelection) => {
  if (!gridApi.value || !newSelection) return

  const incoming = new Set<number>()
  newSelection.selectedIndices.forEach((value) => {
    const parsed = toSelectionNumber(value, null)
    if (parsed !== null) incoming.add(parsed)
  })

  applySelectionToGrid(incoming)
  selectedIndices.value = incoming
  if (props.data) {
    autoSelectionSignature.value = dataSignature(props.data)
  }
}, { deep: true })

// Lifecycle
onMounted(() => {
  nextTick(() => {
    // Get grid API from ref
    if (gridRef.value) {
      const api = (gridRef.value as any).gridApi
      if (api) {
        gridApi.value = api
        applyDefaultSelection()
      }
    }
  })
})
</script>

<style scoped>
.table-viewer {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 8px;
}

.viewer-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px;
  background: #f5f7fa;
  border-radius: 4px;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.grid-container {
  flex: 1;
  min-height: 300px;
  background: white;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}

/* AG Grid theme customization */
:deep(.ag-theme-alpine) {
  font-size: 13px;
}

:deep(.ag-theme-alpine .ag-cell) {
  line-height: 32px;
}

:deep(.ag-theme-alpine .ag-header-cell) {
  font-weight: 600;
}

:deep(.ag-theme-alpine .ag-row-selected) {
  background-color: #ecf5ff !important;
}

:deep(.ag-theme-alpine .ag-cell-range-selected:not(.ag-cell-focus)) {
  background-color: #ecf5ff !important;
}
</style>
