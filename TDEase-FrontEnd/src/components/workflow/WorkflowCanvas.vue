<template>
  <div
    ref="canvasRef"
    class="workflow-canvas"
    :class="{ 'pan-mode': panMode, 'dragging': isDragging }"
    @dragover.prevent="onDragOver"
    @drop.prevent="onDrop"
    @contextmenu.prevent="onContextMenu"
    @mousedown="startDrag"
  >
    <!-- 画布内容容器 -->
    <div class="canvas-viewport">
      <div
        class="canvas-content"
        :style="{
          transform: transformStyle,
          transformOrigin: '0 0'
        }"
      >
        <!-- 网格背景 -->
        <div class="canvas-grid" />

        <!-- 节点容器 -->
        <div class="nodes-container">
          <!-- 节点占位符 -->
          <div v-if="nodes.length === 0" class="canvas-placeholder">
            <div class="placeholder-content">
              <el-icon class="placeholder-icon" :size="48"><Operation /></el-icon>
              <p class="placeholder-text">从左侧拖拽节点到此处</p>
              <p class="placeholder-description">工作流画布开发中...</p>
            </div>
          </div>

          <!-- 渲染所有节点 -->
          <WorkflowNode
            v-for="node in nodes"
            :key="node.id"
            :node="node"
            :is-selected="selectedNodeId === node.id"
            @node-select="handleNodeSelect"
            @node-context-menu="handleNodeContextMenu"
            @node-mouse-down="handleNodeMouseDown"
          />

          <!-- 连接线容器 -->
          <svg class="connections-container" :width="scaledCanvasSize.width" :height="scaledCanvasSize.height">
            <!-- 渲染所有连接 -->
          <WorkflowConnection
            v-for="connection in connections"
            :key="connection.id"
            :connection="connection"
            :source-node="getSourceNode(connection)!"
            :target-node="getTargetNode(connection)!"
            :is-selected="selectedConnectionId === connection.id"
            @connection-select="handleConnectionSelect"
            @connection-context-menu="handleConnectionContextMenu"
            @connection-mouse-down="handleConnectionMouseDown"
          />
          </svg>
        </div>
      </div>
    </div>

    <!-- 画布控制组件 -->
    <CanvasControls
      :transform="transform"
      @zoom-in="zoomIn"
      @zoom-out="zoomOut"
      @zoom="zoomToScale"
      @reset-zoom="resetZoom"
      @fit-to-screen="fitToScreen"
      @reset-view="resetView"
      @toggle-pan-mode="togglePanMode"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Operation } from '@element-plus/icons-vue'
import { useCanvasControls } from '../../composables/useCanvasControls'
import { useWorkflowStore } from '../../stores/workflow'
import type { NodeDefinition, ConnectionDefinition } from '../../stores/workflow'
import CanvasControls from './CanvasControls.vue'
import WorkflowNode from './WorkflowNode.vue'
import WorkflowConnection from './WorkflowConnection.vue'

const emit = defineEmits<{
  (e: 'nodeDrop', event: DragEvent, position: { x: number, y: number }): void
  (e: 'nodeSelect', nodeId: string | null): void
  (e: 'contextMenu', event: MouseEvent): void
}>()

const canvasRef = ref<HTMLElement>()
const workflowStore = useWorkflowStore()

// 获取节点和连接数据
const nodes = computed(() => workflowStore.nodes)
const connections = computed(() => workflowStore.connections)

// 获取选中状态
const selectedNodeId = computed(() => workflowStore.selectedNodeId)
const selectedConnectionId = ref<string | null>(null)

// 获取源节点和目标节点
const getSourceNode = (connection: ConnectionDefinition): NodeDefinition | undefined => {
  return nodes.value.find((node: NodeDefinition) => node.id === connection.source.nodeId)
}

const getTargetNode = (connection: ConnectionDefinition): NodeDefinition | undefined => {
  return nodes.value.find((node: NodeDefinition) => node.id === connection.target.nodeId)
}

// 初始化画布控制
  const {
    transform,
    scaledCanvasSize,
    transformStyle,
    isDragging,
    zoomIn,
    zoomOut,
    resetZoom,
    fitToScreen,
    startDrag,
    drag,
    endDrag,
    getMousePosition,
    initCanvasControls
  } = useCanvasControls()

// 绝对缩放函数，适配 CanvasControls 的 @zoom 事件
const zoomToScale = (scale: number) => {
  const clamped = Math.max(0.1, Math.min(5, scale))
  transform.value.scale = clamped
}

// 拖拽模式
const panMode = ref(false)

const togglePanMode = () => {
  panMode.value = !panMode.value
}

const resetView = () => {
  resetZoom()
  panMode.value = false
}

// 节点事件处理
const handleNodeSelect = (nodeId: string | null) => {
  workflowStore.selectNode(nodeId)
}

const handleNodeContextMenu = (event: MouseEvent, _node: any) => {
  emit('contextMenu', event)
}

const handleNodeMouseDown = (event: MouseEvent, _node: NodeDefinition) => {
  event.stopPropagation()
  if (event.button === 2) {
    // 右键选择连接
    // TODO: 实现连接选择逻辑
  }
}

// 连接事件处理
const handleConnectionSelect = (connectionId: string | null) => {
  selectedConnectionId.value = connectionId
}

const handleConnectionContextMenu = (event: MouseEvent, _connection: ConnectionDefinition) => {
  event.stopPropagation()
  emit('contextMenu', event)
}

const handleConnectionMouseDown = (event: MouseEvent, _connection: ConnectionDefinition) => {
  event.stopPropagation()
}

// 拖拽事件处理
const handleMouseMove = (event: MouseEvent) => {
  drag(event)
}

const handleMouseUp = () => {
  endDrag()
}

// 拖放事件处理
const onDragOver = (event: DragEvent) => {
  event.dataTransfer!.dropEffect = 'move'
}

const onDrop = (event: DragEvent) => {
  if (canvasRef.value) {
    const position = getMousePosition(event)
    emit('nodeDrop', event, position)
  }
}

const onContextMenu = (event: MouseEvent) => {
  emit('contextMenu', event)
}

// 初始化画布控制
onMounted(() => {
  if (canvasRef.value) {
    const cleanup = initCanvasControls(canvasRef.value)
    onUnmounted(cleanup)
  }

  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
})

onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
})
</script>

<style scoped>
.workflow-canvas {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
  background: #f5f7fa;
  border-radius: 8px;
  cursor: grab;
}

.workflow-canvas.pan-mode {
  cursor: grab;
}

.workflow-canvas.pan-mode:active,
.workflow-canvas.dragging {
  cursor: grabbing;
}

.canvas-viewport {
  width: 100%;
  height: 100%;
  overflow: hidden;
  position: relative;
}

.canvas-content {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.canvas-grid {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image:
    linear-gradient(0deg, transparent 24%, rgba(0, 0, 0, 0.05) 25%, rgba(0, 0, 0, 0.05) 26%, transparent 27%, transparent 74%, rgba(0, 0, 0, 0.05) 75%, rgba(0, 0, 0, 0.05) 76%, transparent 77%, transparent),
    linear-gradient(90deg, transparent 24%, rgba(0, 0, 0, 0.05) 25%, rgba(0, 0, 0, 0.05) 26%, transparent 27%, transparent 74%, rgba(0, 0, 0, 0.05) 75%, rgba(0, 0, 0, 0.05) 76%, transparent 77%, transparent);
  background-size: 20px 20px;
}

.nodes-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.canvas-placeholder {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: #909399;
  background: white;
  border: 2px dashed #dcdfe6;
  border-radius: 12px;
  padding: 48px;
  min-width: 300px;
}

.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.placeholder-icon {
  color: #409eff;
  opacity: 0.6;
}

.placeholder-text {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  color: #303133;
}

.placeholder-description {
  font-size: 14px;
  margin: 0;
  color: #909399;
  line-height: 1.4;
}

.connections-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
</style>
