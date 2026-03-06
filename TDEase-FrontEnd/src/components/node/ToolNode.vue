<template>
  <div
    class="tool-node"
    :class="{
      'is-selected': selected,
      'is-dragging': dragging
    }"
    :style="{ borderColor: nodeColor }"
  >
    <div class="node-header" :style="{ backgroundColor: nodeColor }">
      <span class="header-title">{{ nodeLabel }}</span>
      <div v-if="nodeStatus === 'running'" class="status-pulse" />
    </div>
    <div class="node-content">
      <div class="inputs-column">
        <PortList side="left" :node-id="data.nodeId || ''" :ports="inputs" />
      </div>
      <div class="center-label">{{ nodeLabel }}</div>
      <div class="outputs-column">
        <PortList side="right" :node-id="data.nodeId || ''" :ports="outputs" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useWorkflowStore } from '@/stores/workflow'
import { storeToRefs } from 'pinia'
import PortList from '@/components/node/PortList.vue'

const props = defineProps<{
  data: {
    nodeId?: string
    label?: string
    color?: string
    status?: 'idle' | 'running' | 'success' | 'error'
    nodeConfig?: {
      inputs?: Array<{ id: string; name?: string; type?: string }>
      outputs?: Array<{ id: string; name?: string; type?: string; pattern?: string }>
    }
  }
  selected?: boolean
  dragging?: boolean
  resizing?: boolean
}>()

const nodeLabel = computed(() => props.data?.label || 'Tool')
const nodeColor = computed(() => props.data?.color || '#409eff')
const nodeStatus = computed(() => props.data?.status || 'idle')

const inputs = computed(() => {
  const cfg = props.data?.nodeConfig?.inputs
  if (cfg && cfg.length) return cfg as Array<{ id: string; name?: string; type?: string }>
  const nid = props.data?.nodeId
  const storeNode = nid ? nodes.value.find(n => n.id === nid) : undefined
  return (storeNode?.inputs || []) as Array<{ id: string; name?: string; type?: string }>
})

const outputs = computed(() => {
  const cfg = props.data?.nodeConfig?.outputs
  if (cfg && cfg.length) return cfg as Array<{ id: string; name?: string; type?: string; pattern?: string }>
  const nid = props.data?.nodeId
  const storeNode = nid ? nodes.value.find(n => n.id === nid) : undefined
  return (storeNode?.outputs || []) as Array<{ id: string; name?: string; type?: string; pattern?: string }>
})

const store = useWorkflowStore()
const { nodes } = storeToRefs(store)
</script>

<style scoped>
.tool-node {
  position: relative;
  background: color-mix(in srgb, var(--ctp-mantle) 95%, transparent);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 2px solid var(--ctp-mauve);
  border-radius: 8px;
  min-width: 240px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  overflow: hidden;
  transition: all 0.2s ease-in-out;
}

.tool-node:hover {
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.18);
  transform: translateY(-1px);
}

.tool-node.is-selected {
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--ctp-mauve) 40%, transparent), 0 6px 20px rgba(0, 0, 0, 0.18);
}

.tool-node.is-dragging {
  opacity: 0.9;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
}

.node-header {
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 12px;
  color: #fff;
  font-weight: 600;
  font-size: 14px;
  position: relative;
}

.header-title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-pulse {
  position: absolute;
  right: 10px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 0 6px 2px rgba(255, 255, 255, 0.8);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.6;
    transform: scale(1.1);
  }
}

.node-content {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 12px;
  padding: 12px;
  align-items: flex-start;
  min-height: 60px;
}

.inputs-column,
.outputs-column {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.center-label {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 40px;
  padding: 8px 0;
  font-weight: 600;
  font-size: 11px;
  color: var(--ctp-subtext0);
  writing-mode: vertical-rl;
  text-orientation: mixed;
  letter-spacing: 2px;
}
</style>