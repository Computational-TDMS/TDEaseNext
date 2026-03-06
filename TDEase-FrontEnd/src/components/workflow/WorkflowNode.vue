<template>
  <div
    class="workflow-node"
    :class="{
      'selected': isSelected,
      'dragging': isDragging
    }"
    :style="{
      left: node.position.x + 'px',
      top: node.position.y + 'px',
      width: (node.displayProperties?.width || 180) + 'px',
      height: (node.displayProperties?.height || 120) + 'px'
    }"
    @mousedown="handleMouseDown"
    @contextmenu.prevent="handleContextMenu"
  >
    <!-- 节点头部 -->
    <div class="node-header" :style="{ backgroundColor: resolveHeaderColor() }">
      <div class="node-icon">
        <el-icon v-if="node.displayProperties?.icon" :size="20">
          <component :is="node.displayProperties.icon" />
        </el-icon>
        <div v-else class="node-type-icon">
          {{ node.type?.charAt(0).toUpperCase() }}
        </div>
      </div>
      <div class="node-label">{{ node.displayProperties?.label || node.data?.label || node.type }}</div>

      <!-- 节点操作按钮 -->
      <div class="node-actions">
        <el-button
          circle
          size="small"
          :icon="Setting"
          @click.stop="$emit('nodeSelect', node.id)"
          title="配置节点"
        />
      </div>
    </div>

    <!-- 输入端口 -->
    <div class="node-ports node-inputs" v-if="node.inputs?.length">
      <div
        v-for="input in node.inputs"
        :key="input.id"
        class="port input-port"
        :style="{ backgroundColor: getPortColor(input.type) }"
        :title="`${input.name} (${input.type})`"
      >
        <div class="port-label">{{ input.name }}</div>
      </div>
    </div>

    <!-- 输出端口 -->
    <div class="node-ports node-outputs" v-if="node.outputs?.length">
      <div
        v-for="output in node.outputs"
        :key="output.id"
        class="port output-port"
        :style="{ backgroundColor: getPortColor(output.type) }"
        :title="`${output.name} (${output.type})`"
      >
        <div class="port-label">{{ output.name }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Setting } from '@element-plus/icons-vue'
import type { NodeDefinition } from '@/stores/workflow'

interface Props {
  node: NodeDefinition
  isSelected?: boolean
  isDragging?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isSelected: false,
  isDragging: false
})

const emit = defineEmits<{
  (e: 'nodeSelect', nodeId: string): void
  (e: 'nodeContextMenu', event: MouseEvent, node: NodeDefinition): void
  (e: 'nodeMouseDown', event: MouseEvent, node: NodeDefinition): void
  (e: 'nodeMouseUp', event: MouseEvent, node: NodeDefinition): void
  (e: 'nodeDragStart', event: DragEvent, node: NodeDefinition): void
}>()

// 端口类型颜色映射
const getPortColor = (type: string): string => {
  const colorMap: Record<string, string> = {
    'data': '#67c23a',
    'file': '#409eff',
    'string': '#e6a23c',
    'number': '#f56c6c',
    'boolean': '#909399',
    'select': '#3742fa',
    'multiselect': '#e6a23c'
  }
  return colorMap[type] || '#606266'
}

const resolveHeaderColor = (): string => {
  const color = props.node.displayProperties?.color ?? (props.node.data as any)?.color
  return typeof color === 'string' ? color : '#409eff'
}



const handleMouseDown = (event: MouseEvent) => {
  event.stopPropagation()
  emit('nodeMouseDown', event, props.node)
}

const handleContextMenu = (event: MouseEvent) => {
  event.stopPropagation()
  emit('nodeContextMenu', event, props.node)
}
</script>

<style scoped>
.workflow-node {
  position: absolute;
  border-radius: 8px;
  background: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  cursor: grab;
  user-select: none;
  transition: all 0.2s ease;
  z-index: 10;
}

.workflow-node:hover {
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
  transform: translateY(-2px);
}

.workflow-node.selected {
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.3);
}

.workflow-node.dragging {
  cursor: grabbing;
  opacity: 0.8;
}

.node-header {
  height: 32px;
  border-radius: 8px 8px 0 0;
  display: flex;
  align-items: center;
  padding: 0 12px;
  color: white;
  font-size: 12px;
  font-weight: 600;
}

.node-icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

.node-type-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  font-size: 10px;
  font-weight: bold;
}

.node-label {
  flex: 1;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.node-actions {
  position: absolute;
  top: -6px;
  right: -6px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.workflow-node:hover .node-actions {
  opacity: 1;
}

.ports {
  display: flex;
  gap: 8px;
}

.node-inputs {
  justify-content: flex-start;
}

.node-outputs {
  justify-content: flex-end;
}

.port {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 8px;
  color: white;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.port:hover {
  transform: scale(1.2);
}

.port-label {
  display: none;
}

.port:hover .port-label {
  display: block;
  position: absolute;
  bottom: -20px;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  white-space: nowrap;
  z-index: 1000;
}
</style>
