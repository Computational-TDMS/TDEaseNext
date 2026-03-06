<template>
  <div
    class="node-port"
    :class="[`side-${side}`, { 'is-connected': isConnected, 'is-hovered': isHovered, 'is-compatible': isCompatible }]"
    :style="portStyle"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
  >
    <div class="port-handle">
      <div v-if="showLabel" class="port-label">{{ label }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

type PortSide = 'left' | 'right' | 'top' | 'bottom'

const props = withDefaults(defineProps<{
  side?: PortSide
  label?: string
  type?: string
  color?: string
  isConnected?: boolean
  isCompatible?: boolean
  showLabel?: boolean
}>(), {
  side: 'left',
  label: '',
  type: 'data',
  isConnected: false,
  isCompatible: false,
  showLabel: false
})

const emit = defineEmits<{
  (e: 'hover', value: boolean): void
}>()

const isHovered = ref(false)

const portColor = computed(() => {
  const colorMap: Record<string, string> = {
    data: '#67c23a',
    file: '#409eff',
    string: '#e6a23c',
    number: '#f56c6c',
    boolean: '#909399',
    select: '#3742fa',
    multiselect: '#e6a23c'
  }
  return props.color || colorMap[props.type] || '#606266'
})

const portStyle = computed(() => ({
  '--port-color': portColor.value
}))

const handleMouseEnter = () => {
  isHovered.value = true
  emit('hover', true)
}

const handleMouseLeave = () => {
  isHovered.value = false
  emit('hover', false)
}
</script>

<style scoped>
.node-port {
  position: relative;
  display: flex;
  align-items: center;
}

.node-port.side-left {
  justify-content: flex-start;
}

.node-port.side-right {
  justify-content: flex-end;
}

.node-port.side-top {
  justify-content: center;
}

.node-port.side-bottom {
  justify-content: center;
}

.port-handle {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--port-color, #409eff);
  border: 2px solid rgba(255, 255, 255, 0.9);
  cursor: pointer;
  transition: all 0.2s ease-in-out;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
  position: relative;
}

.node-port.is-hovered .port-handle,
.node-port.is-compatible .port-handle {
  transform: scale(1.25);
  box-shadow: 0 0 10px 2px var(--port-color, #409eff), 0 2px 8px rgba(0, 0, 0, 0.25);
}

.node-port.is-connected .port-handle {
  background: var(--port-color, #409eff);
  border-width: 3px;
}

.port-label {
  position: absolute;
  font-size: 11px;
  color: #606266;
  background: rgba(255, 255, 255, 0.95);
  padding: 2px 6px;
  border-radius: 4px;
  white-space: nowrap;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  pointer-events: none;
  z-index: 100;
}

.node-port.side-left .port-label {
  left: 20px;
}

.node-port.side-right .port-label {
  right: 20px;
}

.node-port.is-hovered .port-label {
  opacity: 1;
}
</style>