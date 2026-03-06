<template>
  <svg
    class="workflow-connection"
    :width="connectionWidth"
    :height="connectionHeight"
    @mousedown="handleMouseDown"
    @contextmenu.prevent="handleContextMenu"
  >
    <!-- 连接线主体 -->
    <path
      :d="pathData"
      :stroke="connectionColor"
      :stroke-width="strokeWidth"
      fill="none"
      class="connection-path"
    />

    <!-- 起始点 -->
    <circle
      :cx="startPos.x"
      :cy="startPos.y"
      :r="portRadius"
      :fill="getPortColor(sourcePortType)"
      class="connection-port"
    />

    <!-- 结束点 -->
    <circle
      :cx="endPos.x"
      :cy="endPos.y"
      :r="portRadius"
      :fill="getPortColor(targetPortType)"
      class="connection-port"
    />

    <!-- 箭头 -->
    <polygon
      :points="arrowPoints"
      :fill="connectionColor"
      class="connection-arrow"
    />
  </svg>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ConnectionDefinition, NodeDefinition } from '@/stores/workflow'
import type { Position } from '@/stores/workflow'

interface Props {
  connection: ConnectionDefinition
  sourceNode: NodeDefinition
  targetNode: NodeDefinition
  isSelected?: boolean
  isHovered?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isSelected: false,
  isHovered: false
})

const emit = defineEmits<{
  connectionSelect: [connectionId: string]
  connectionContextMenu: [event: MouseEvent, connection: ConnectionDefinition]
  connectionMouseDown: [event: MouseEvent, connection: ConnectionDefinition]
}>()

const connectionWidth = computed(() => {
  const dx = props.targetNode.position.x - props.sourceNode.position.x
  const dy = props.targetNode.position.y - props.sourceNode.position.y
  return Math.sqrt(dx * dx + dy * dy)
})

const connectionHeight = 50

const strokeWidth = computed(() => {
  return props.isSelected ? 3 : 2
})

const connectionColor = computed(() => {
  return props.isSelected ? '#409eff' : props.isHovered ? '#67c23a' : '#909399'
})

// 端口位置计算
const startPos = computed((): Position => {
  const outputPort = props.sourceNode.outputs.find(port => port.id === props.connection.source.portId)
  if (outputPort) {
    return {
      x: props.sourceNode.position.x + (props.sourceNode.displayProperties?.width || 180),
      y: props.sourceNode.position.y + (props.sourceNode.displayProperties?.height || 120) / 2
    }
  }
  return { x: 0, y: 0 }
})

const endPos = computed((): Position => {
  const inputPort = props.targetNode.inputs.find(port => port.id === props.connection.target.portId)
  if (inputPort) {
    return {
      x: props.targetNode.position.x,
      y: props.targetNode.position.y + (props.targetNode.displayProperties?.height || 120) / 2
    }
  }
  return { x: 0, y: 0 }
})

// 连接线路径
const pathData = computed(() => {
  const dx = endPos.value.x - startPos.value.x
  const dy = endPos.value.y - startPos.value.y

  // 创建弯曲的连接线 - 使用正确的三次贝塞尔曲线格式
  // C 命令格式: C cx1,cy1 cx2,cy2 x,y (两个控制点 + 终点)
  const ctrlX1 = startPos.value.x + dx * 0.25
  const ctrlY1 = startPos.value.y + dy * 0.25
  const ctrlX2 = startPos.value.x + dx * 0.75
  const ctrlY2 = startPos.value.y + dy * 0.75

  // 修复: 使用单个 C 命令，包含两个控制点和终点
  return `M ${startPos.value.x},${startPos.value.y} C ${ctrlX1},${ctrlY1} ${ctrlX2},${ctrlY2} ${endPos.value.x},${endPos.value.y}`
})

// 箭头
const arrowPoints = computed(() => {
  const angle = Math.atan2(endPos.value.y - startPos.value.y, endPos.value.x - startPos.value.x)
  const arrowLength = 10
  const arrowAngle = angle + Math.PI / 6

  const x1 = endPos.value.x - arrowLength * Math.cos(arrowAngle)
  const y1 = endPos.value.y - arrowLength * Math.sin(arrowAngle)
  const x2 = endPos.value.x - arrowLength * Math.cos(arrowAngle - Math.PI / 6)
  const y2 = endPos.value.y - arrowLength * Math.sin(arrowAngle - Math.PI / 6)

  return `${endPos.value.x},${endPos.value.y} ${x1},${y1} ${x2},${y2}`
})

const portRadius = 4

// 端口类型颜色
const getPortColor = (portType: string): string => {
  const colorMap: Record<string, string> = {
    'data': '#67c23a',
    'file': '#e6a23c',
    'number': '#56c6c6',
    'string': '#e6a23c',
    'boolean': '#909399',
    'select': '#3742fa',
    'multiselect': '#3742fa'
  }
  return colorMap[portType] || '#909399'
}

const sourcePortType = computed(() => {
  const outputPort = props.sourceNode.outputs.find(port => port.id === props.connection.source.portId)
  return outputPort?.type || 'file'
})

const targetPortType = computed(() => {
  const inputPort = props.targetNode.inputs.find(port => port.id === props.connection.target.portId)
  return inputPort?.type || 'file'
})

const handleMouseDown = (event: MouseEvent) => {
  event.stopPropagation()
  emit('connectionMouseDown', event, props.connection)
}

const handleContextMenu = (event: MouseEvent) => {
  event.stopPropagation()
  emit('connectionContextMenu', event, props.connection)
}
</script>

<style scoped>
.workflow-connection {
  position: absolute;
  pointer-events: all;
  z-index: 1;
}

.workflow-connection:hover .connection-path {
  stroke-width: 3;
}

.connection-path {
  transition: stroke-width 0.2s ease, stroke 0.2s ease;
  cursor: pointer;
}

.connection-port {
  stroke-width: 2;
  stroke: white;
  cursor: pointer;
  transition: all 0.2s ease;
}

.connection-port:hover {
  stroke-width: 3;
  transform: scale(1.2);
}

.connection-arrow {
  cursor: pointer;
  transition: all 0.2s ease;
}

.connection-arrow:hover {
  transform: scale(1.2);
}
</style>
