<template>
  <div class="io-column" :class="sideClass">
    <div class="io-title">{{ title }}</div>
  <ul class="io-list">
    <component
        v-for="(row, idx) in rows"
        :is="isLeft ? Filein : Fileout"
        :key="row.port.id + ':' + idx"
        :row="row"
        :node-id="nodeId"
      />
  </ul>
  </div>
</template>

<script setup lang="ts">
import { computed, watch, nextTick } from 'vue'
import { useVueFlow } from '@vue-flow/core'
import { useWorkflowStore } from '@/stores/workflow'
import { storeToRefs } from 'pinia'
import Filein from '@/components/node/Filein.vue'
import Fileout from '@/components/node/Fileout.vue'

type Port = {
  id: string
  name?: string
  type?: string
  pattern?: string
  required?: boolean
  accept?: string[]
  provides?: string[]
  portKind?: 'data' | 'state-in' | 'state-out'
  semanticType?: string
}
export type PortRow = { port: Port; samples?: string[]; expected?: string[]; source: 'conn' | 'local'; file?: boolean; connected?: boolean }

const props = defineProps<{
  side: 'left' | 'right'
  nodeId: string
  ports: Port[]
}>()

const isLeft = computed(() => props.side === 'left')
const title = computed(() => (isLeft.value ? '输入' : '输出'))
const sideClass = computed(() => (isLeft.value ? 'io-left' : 'io-right'))

const store = useWorkflowStore()
const { connections, nodes } = storeToRefs(store)
const currentNode = computed(() => nodes.value.find((n) => n.id === props.nodeId) as any)
const { updateNodeInternals } = useVueFlow()

const inputRows = computed<PortRow[]>(() => {
  return props.ports.map((p) => {
    const files: string[] = []
    let fromConn = false
    let hasFileConn = false
    let isConnected = false
    for (const conn of connections.value) {
      if (conn.target.nodeId === props.nodeId && conn.target.portId === p.id) {
        isConnected = true
        if (typeof conn.dataPath?.t === 'string' && conn.dataPath.t !== '') {
          hasFileConn = true
        }
        const src = nodes.value.find((n) => n.id === conn.source.nodeId) as any
        const cfg = src?.nodeConfig || {}
        const srcOutputs = Array.isArray(cfg.outputs) ? cfg.outputs : []
        const srcSamples = Array.isArray(cfg.samples) ? cfg.samples : []
        const srcPort = srcOutputs.find((o: any) => o.id === conn.source.portId)
        const pattern = srcPort?.pattern || ''
        const provides = Array.isArray(srcPort?.provides) ? srcPort.provides : []
        if (pattern && srcSamples.length) {
          const sIdx = typeof conn.dataPath?.s === 'string' && conn.dataPath?.s !== '' ? Number(conn.dataPath?.s) : null
          if (sIdx !== null && !Number.isNaN(sIdx) && srcSamples[sIdx] !== undefined) {
            files.push(pattern.replace('{sample}', String(srcSamples[sIdx])))
          } else {
            for (const s of srcSamples) files.push(pattern.replace('{sample}', String(s)))
          }
          fromConn = true
        } else {
          const sIdx = typeof conn.dataPath?.s === 'string' && conn.dataPath?.s !== '' ? Number(conn.dataPath?.s) : null
          if (sIdx !== null && !Number.isNaN(sIdx) && srcSamples[sIdx] !== undefined) {
            files.push(String(srcSamples[sIdx]))
            fromConn = true
          } else if (srcSamples.length) {
            for (const s of srcSamples) files.push(String(s))
            fromConn = true
          } else if (hasFileConn) {
            // 已存在文件级连接但缺少样本，使用源端口名占位以确保句柄索引一致
            if (srcPort?.name) files.push(String(srcPort.name))
            else files.push(String(conn.source.portId))
            fromConn = true
          }
        }
        if (provides.length) {
        }
      }
    }
    if (files.length === 0) {
      const localSamples = Array.isArray(currentNode.value?.nodeConfig?.samples) ? currentNode.value.nodeConfig.samples : []
      for (const s of localSamples) files.push(String(s))
      // 若端口为必需但仍无样本，也不要渲染调试占位；交由右侧 FileOut 的 pattern 进行预期提示
    }
    return { port: p, samples: files, expected: [], source: fromConn ? 'conn' : 'local', file: hasFileConn, connected: isConnected }
  })
})

const outputRows = computed<PortRow[]>(() => {
  let samplesAll = inputRows.value.flatMap((r) => r.samples || [])
  if (!samplesAll.length) {
    const localSamples = Array.isArray(currentNode.value?.nodeConfig?.samples) ? currentNode.value.nodeConfig.samples : []
    samplesAll = localSamples.map((s: any) => String(s))
  }
  // 收集当前节点每个输出端口已存在的文件级连接索引
  const indexMap: Record<string, number[]> = {}
  for (const conn of connections.value) {
    if (conn.source.nodeId === props.nodeId) {
      const pid = conn.source.portId
      const sIdxRaw = conn.dataPath?.s
      if (typeof sIdxRaw === 'string' && sIdxRaw !== '') {
        const n = Number(sIdxRaw)
        if (!Number.isNaN(n)) {
          indexMap[pid] ||= []
          if (!indexMap[pid].includes(n)) indexMap[pid].push(n)
        }
      }
    }
  }
  return props.ports.map((p) => {
    const expected: string[] = []
    const pattern = p.pattern || ''
    if (pattern && samplesAll.length) {
      for (const s of samplesAll) expected.push(pattern.replace('{sample}', s))
    }
    // 如果没有 pattern 展开，但存在文件级连接索引，则为这些索引创建占位文件名以渲染文件级 Handle
    if (!expected.length && Array.isArray(indexMap[p.id]) && indexMap[p.id].length) {
      for (const idx of indexMap[p.id]) {
        expected.push(`${p.name || p.id}#${idx}`)
      }
    }
    return { port: p, samples: samplesAll, expected, source: 'conn' }
  })
})

const rows = computed<PortRow[]>(() => (isLeft.value ? inputRows.value : outputRows.value))
watch(rows, async () => {
  await nextTick()
  updateNodeInternals([props.nodeId])
})
</script>

<style scoped>
.io-column { position: relative; }
.io-title { font-size: 12px; color: #606266; margin-bottom: 6px; }
.io-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 6px; }
</style>
