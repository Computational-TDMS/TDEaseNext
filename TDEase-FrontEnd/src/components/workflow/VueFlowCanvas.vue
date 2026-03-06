<template>
  <div class="vue-flow-container">
    <VueFlow
      :nodes="nodes"
      :edges="edges"
      :node-types="nodeTypes"
      :edge-types="edgeTypesRaw"
      :fit-view-on-init="true"
      :snap-to-grid="true"
      :snap-grid="[20, 20]"
      :connection-mode="ConnectionMode.Strict"
      :connection-line-type="ConnectionLineType.SmoothStep"
      @dragover="onDragOver"
      @node-drag-start="onNodeDragStart"
      @node-drag-stop="onNodeDragStop"
      @node-click="onNodeClick"
      @node-context-menu="onNodeContextMenu"
      @connect="onConnect"
      @edge-click="onEdgeClick"
      @edge-context-menu="onEdgeContextMenu"
      @drop="onDrop"
      class="vue-flow-editor"
    >
      <!-- 背景组件 -->
      <Background
        :gap="20"
        :pattern-size="1"
      />

      <!-- 控制组件 -->
      <Controls
        :show-zoom="true"
        :show-fit-view="true"
        :show-interactive="true"
      />

      <!-- 小地图组件 -->
      <MiniMap />

      <!-- 空状态提示 -->
      <div v-if="nodes.length === 0" class="empty-state">
        <div class="empty-content">
          <el-icon class="empty-icon" :size="48">
            <Operation />
          </el-icon>
          <h3>拖拽节点到画布</h3>
          <p>从左侧面板拖拽节点到此处开始构建工作流</p>
        </div>
      </div>
    </VueFlow>
  </div>
</template>

<script setup lang="ts">
import { computed, markRaw, nextTick } from 'vue'
import { VueFlow, Position, Handle, ConnectionMode, ConnectionLineType, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'
import '@vue-flow/minimap/dist/style.css'
import dagre from 'dagre'

import type { Node, Edge, NodeMouseEvent, NodeDragEvent, EdgeMouseEvent, Connection } from '@vue-flow/core'
import { ElMessage } from 'element-plus'
import { useWorkflowStore } from '@/stores/workflow'
import { useStateBusStore } from '@/stores/state-bus'
import { Operation, Setting } from '@element-plus/icons-vue'
// removed unused specific node components in favor of ToolNode-only rendering
import ToolNode from '@/components/node/ToolNode.vue'
import InteractiveNode from '@/components/visualization/InteractiveNode.vue'
import FilterNode from '@/components/nodes/FilterNode.vue'
import { edgeTypes } from './edges'

const emit = defineEmits<{
  nodeSelect: [nodeId: string | null]
  contextMenu: [event: MouseEvent | TouchEvent, context: string, data: any]
}>()

const workflowStore = useWorkflowStore()
const stateBus = useStateBusStore()
const { onPaneReady, fitView, zoomIn, zoomOut } = useVueFlow()

// 从 store 获取数据并转换为 Vue Flow 格式
const nodes = computed<Node<any, any, string>[]>(() => workflowStore.nodes.map((node) => {
  // Determine node type based on executionMode
  let nodeType = node.type

  // Debug logging
  console.log(`[VueFlowCanvas] Processing node ${node.id}:`, {
    type: node.type,
    executionMode: node.executionMode,
    label: node.displayProperties?.label || node.data?.label
  })

  // Priority 1: Check executionMode first (most important)
  if (node.executionMode === 'interactive') {
    nodeType = 'interactive'
    console.log(`[VueFlowCanvas] Node ${node.id} is interactive (by executionMode)`)
  }
  // Priority 2: Check for specific node types
  else if (node.type === 'filter') {
    nodeType = 'filter'
  }
  // Priority 3: Check for other known types
  else if (['custom', 'input', 'process', 'output', 'tool'].includes(node.type)) {
    nodeType = node.type
  }
  // Default to tool node
  else {
    nodeType = 'tool'
  }

  console.log(`[VueFlowCanvas] Node ${node.id} resolved to type: ${nodeType}`)

  const resolvedToolId =
    (node as any).nodeConfig?.toolId ||
    (node as any).data?.toolId ||
    (node as any).data?.type ||
    (node.type !== 'tool' ? node.type : null)

  return {
    id: node.id,
    type: nodeType,
    position: node.position,
    data: {
      nodeId: node.id,
      label: node.displayProperties?.label || node.data?.label || node.type,
      color: node.displayProperties?.color || node.data?.color || '#409eff',
      icon: node.displayProperties?.icon,
      executionMode: node.executionMode,
      toolId: typeof resolvedToolId === 'string' ? resolvedToolId : node.type,
      visualizationConfig: node.visualizationConfig,
      nodeConfig: {
        inputs: node.inputs.map((p) => ({
          id: p.id,
          name: p.name,
          type: (p as any).dataType || (p as any).type || 'file',
          required: (p as any).required === true,
          accept: Array.isArray((p as any).accept) ? (p as any).accept : undefined,
          dataType: (p as any).dataType,
          portKind: (p as any).portKind,
          semanticType: (p as any).semanticType
        })),
        outputs: node.outputs.map((p) => ({
          id: p.id,
          name: p.name,
          type: (p as any).dataType || (p as any).type || 'file',
          pattern: (p as any).pattern,
          provides: Array.isArray((p as any).provides) ? (p as any).provides : undefined,
          dataType: (p as any).dataType,
          portKind: (p as any).portKind,
          semanticType: (p as any).semanticType
        }))
      }
    },
    style: {
      backgroundColor: 'transparent',
      border: 'none',
      padding: '0',
      width: 'auto',
      height: 'auto'
    },
    draggable: true,
    selectable: true
  }
}))

const edges = computed<Edge<any, any, string>[]>(() => workflowStore.connections.map((conn) => {
  const sSuffix = conn.dataPath?.s || ''
  const tSuffix = conn.dataPath?.t || ''
  const isState = conn.connectionKind === 'state'
  return {
    id: conn.id,
    source: conn.source.nodeId,
    target: conn.target.nodeId,
    sourceHandle: `output-${conn.source.portId}` + (sSuffix ? `__${sSuffix}` : ''),
    targetHandle: `input-${conn.target.portId}` + (tSuffix ? `__${tSuffix}` : ''),
    type: isState ? 'state' : 'data',
    animated: false,
    selectable: true,
    data: {
      semanticType: conn.semanticType,
      dataType: isState ? undefined : 'file',
      active: false
    }
  }
}))

// 自定义节点类型
const CustomNode = markRaw({
  components: { Handle, Setting },
  template: `
    <div
      class="custom-workflow-node"
      :style="{
        backgroundColor: node.data.color,
        borderColor: node.data.color
      }"
    >
      <div class="node-header">
        <div class="node-icon">
          <el-icon v-if="node.data.icon" :size="16" color="white">
            <component :is="node.data.icon" />
          </el-icon>
          <span v-else class="node-type-icon">{{ node.type.charAt(0).toUpperCase() }}</span>
        </div>
        <div class="node-label">{{ node.data.label }}</div>
        <div class="node-settings">
          <el-button circle size="small" type="primary" @click="$emit('nodeSettings', node)">
            <el-icon :size="12"><Setting /></el-icon>
          </el-button>
        </div>
      </div>

      <!-- 输入端口 -->
      <div class="node-inputs" v-if="hasInputs">
        <Handle
          v-for="input in inputs"
          :key="input.id"
          type="target"
          :position="Position.Left"
          :id="input-\${input.id}"
          :style="getPortStyle(input)"
        />
        <div class="port-label">{{ input.name }}</div>
      </div>

      <!-- 输出端口 -->
      <div class="node-outputs" v-if="hasOutputs">
        <Handle
          v-for="output in outputs"
          :key="output.id"
          type="source"
          :position="Position.Right"
          :id="output-\${output.id}"
          :style="getPortStyle(output)"
        />
        <div class="port-label">{{ output.name }}</div>
      </div>
    </div>
  `,
  setup(props: any) {
    const { node } = props

    const inputs = computed(() => {
      // 从节点数据中获取输入端口配置
      return node.data.nodeConfig?.inputs || []
    })

    const outputs = computed(() => {
      // 从节点数据中获取输出端口配置
      return node.data.nodeConfig?.outputs || []
    })

    const hasInputs = computed(() => inputs.value.length > 0)
    const hasOutputs = computed(() => outputs.value.length > 0)

    const getPortColor = (type: string) => {
      const colorMap: Record<string, string> = {
        data: '#67c23a',
        file: '#409eff',
        string: '#e6a23c',
        number: '#f56c6c',
        boolean: '#909399',
        select: '#3742fa'
      }
      return colorMap[type] || '#606266'
    }

    const getPortStyle = (port: any) => {
      const portKind = port?.portKind || 'data'
      if (portKind === 'state-in') {
        return {
          backgroundColor: '#fff6e6',
          border: '2px solid #f59f00',
          borderRadius: '3px'
        }
      }
      if (portKind === 'state-out') {
        return {
          backgroundColor: '#f59f00',
          border: '2px solid #f59f00',
          borderRadius: '3px'
        }
      }
      return {
        backgroundColor: getPortColor(port.type),
        border: '2px solid #fff',
        borderRadius: '50%'
      }
    }

    return {
      inputs,
      outputs,
      hasInputs,
      hasOutputs,
      getPortColor,
      getPortStyle,
      Position
    }
  }
})

const nodeTypes = {
  custom: CustomNode,
  input: markRaw(ToolNode),
  process: markRaw(ToolNode),
  output: markRaw(ToolNode),
  tool: markRaw(ToolNode),
  interactive: markRaw(InteractiveNode),
  filter: markRaw(FilterNode)
} as any

// Wrap edge types with markRaw to prevent Vue reactivity overhead
const edgeTypesRaw = {
  state: markRaw(edgeTypes.state),
  data: markRaw(edgeTypes.data)
}


onPaneReady((instance) => {
  instance.fitView()
})

// 自动布局函数 - 使用 dagre 算法，根据节点实际尺寸自动调整间距
const autoLayout = async () => {
  const currentNodes = nodes.value
  const currentEdges = edges.value
  
  if (currentNodes.length === 0) {
    ElMessage.info('没有节点需要布局')
    return
  }

  // 等待 DOM 更新，确保节点已渲染
  await nextTick()
  
  // 对于包含图表的节点（如 interactive 节点），需要额外等待图表渲染
  // 检查是否有 interactive 节点
  const hasInteractiveNodes = currentNodes.some(node => node.type === 'interactive')
  if (hasInteractiveNodes) {
    // 等待图表组件完全渲染（ECharts 等需要时间）
    await new Promise(resolve => setTimeout(resolve, 300))
  }
  
  // 获取节点的实际尺寸
  const nodeDimensions = new Map<string, { width: number; height: number }>()
  const minNodeWidth = 180  // 最小节点宽度
  const minNodeHeight = 100 // 最小节点高度
  const basePadding = 10    // 基础间距
  
  // 对于 interactive 节点，使用更大的默认尺寸和间距
  const interactiveNodeDefaultWidth = 600
  const interactiveNodeDefaultHeight = 500
  const interactivePadding = 70  // interactive 节点需要稍大的间距

  currentNodes.forEach((node) => {
    // 尝试多种方式查找节点元素
    let nodeElement: HTMLElement | null = null
    
    // 方法1: 通过 data-id 属性查找
    nodeElement = document.querySelector(`[data-id="${node.id}"]`) as HTMLElement
    
    // 方法2: 如果找不到，尝试通过 Vue Flow 的节点 class 和 id 查找
    if (!nodeElement) {
      nodeElement = document.querySelector(`.vue-flow__node[data-id="${node.id}"]`) as HTMLElement
    }
    
    // 方法3: 通过 id 属性查找
    if (!nodeElement) {
      nodeElement = document.getElementById(`vue-flow-node-${node.id}`) as HTMLElement
    }
    
    if (nodeElement) {
      const rect = nodeElement.getBoundingClientRect()
      // 确保尺寸有效且不小于最小值
      let width = rect.width > 0 ? rect.width : minNodeWidth
      let height = rect.height > 0 ? rect.height : minNodeHeight
      
      // 对于 interactive 节点，如果检测到的尺寸太小，使用默认尺寸
      if (node.type === 'interactive') {
        if (width < interactiveNodeDefaultWidth) {
          width = interactiveNodeDefaultWidth
        }
        if (height < interactiveNodeDefaultHeight) {
          height = interactiveNodeDefaultHeight
        }
      }
      
      nodeDimensions.set(node.id, {
        width: Math.max(width, node.type === 'interactive' ? interactiveNodeDefaultWidth : minNodeWidth),
        height: Math.max(height, node.type === 'interactive' ? interactiveNodeDefaultHeight : minNodeHeight)
      })
    } else {
      // 如果找不到元素，根据节点类型使用不同的默认尺寸
      if (node.type === 'interactive') {
        nodeDimensions.set(node.id, {
          width: interactiveNodeDefaultWidth,
          height: interactiveNodeDefaultHeight
        })
      } else {
        nodeDimensions.set(node.id, {
          width: minNodeWidth,
          height: minNodeHeight
        })
      }
    }
  })

  // 计算最大节点尺寸（而不是平均），用于设置更保守的布局参数
  const maxWidth = Math.max(...Array.from(nodeDimensions.values()).map(dim => dim.width))
  const maxHeight = Math.max(...Array.from(nodeDimensions.values()).map(dim => dim.height))
  
  // 检查是否有 interactive 节点
  const hasInteractive = currentNodes.some(node => node.type === 'interactive')
  const padding = hasInteractive ? interactivePadding : basePadding

  // 创建 dagre 图
  const g = new dagre.graphlib.Graph()
  g.setDefaultEdgeLabel(() => ({}))
  
  // 使用最大节点尺寸 + 间距，确保不会重叠
  g.setGraph({ 
    rankdir: 'LR', // 从左到右布局
    nodesep: Math.max(maxWidth + padding, 10),  // 节点水平间距（基于最大宽度 + 间距）
    ranksep: Math.max(maxHeight + padding, 10),  // 层级垂直间距（基于最大高度 + 间距）
    marginx: 5,   // 左右边距
    marginy: 5    // 上下边距
  })

  // 添加节点到 dagre 图，使用实际尺寸加上安全边距
  currentNodes.forEach((node) => {
    const dim = nodeDimensions.get(node.id) || { 
      width: node.type === 'interactive' ? interactiveNodeDefaultWidth : minNodeWidth, 
      height: node.type === 'interactive' ? interactiveNodeDefaultHeight : minNodeHeight 
    }
    // 为每个节点添加小的安全边距（特别是 interactive 节点）
    const safetyMargin = node.type === 'interactive' ? 4 : 2
    g.setNode(node.id, { 
      width: dim.width + safetyMargin, 
      height: dim.height + safetyMargin 
    })
  })

  // 添加边到 dagre 图
  currentEdges.forEach((edge) => {
    if (edge.source && edge.target) {
      g.setEdge(edge.source, edge.target)
    }
  })

  // 计算布局
  dagre.layout(g)

  // 更新节点位置到 store（使用每个节点的实际尺寸）
  currentNodes.forEach((node) => {
    const nodeWithPosition = g.node(node.id)
    const dim = nodeDimensions.get(node.id) || { 
      width: node.type === 'interactive' ? interactiveNodeDefaultWidth : minNodeWidth, 
      height: node.type === 'interactive' ? interactiveNodeDefaultHeight : minNodeHeight 
    }
    if (nodeWithPosition) {
      const newPosition = {
        x: nodeWithPosition.x - dim.width / 2,
        y: nodeWithPosition.y - dim.height / 2
      }
      workflowStore.moveNode(node.id, newPosition)
    }
  })

  // 调整视口以适应新布局
  setTimeout(() => {
    fitView({ padding: 0.2, duration: 400 })
  }, 100)

  ElMessage.success('自动布局完成')
}

// 暴露方法给父组件
defineExpose({
  fitView,
  zoomIn,
  zoomOut,
  autoLayout
})

// 事件处理函数
const onNodeDragStart = (_evt: NodeDragEvent) => {}

const onNodeDragStop = (evt: NodeDragEvent) => {
  workflowStore.moveNode(evt.node.id, evt.node.position)
}

const onNodeClick = (evt: NodeMouseEvent) => {
  emit('nodeSelect', evt.node.id)
}

const onNodeContextMenu = (evt: NodeMouseEvent) => {
  evt.event.preventDefault()
  emit('contextMenu', evt.event, 'node', evt.node)
}

const onConnect = (connection: Connection) => {
  const sourceId = connection.source
  const targetId = connection.target
  if (sourceId === targetId) {
    ElMessage.error('不能连接到自身')
    return false
  }
  const parseHandle = (h: string | null | undefined, kind: 'input' | 'output') => {
    const base = (h || '').replace(kind + '-', '')
    const [port, suffix] = base.split('__')
    return { port: port || (kind === 'output' ? 'output' : 'input'), suffix: suffix || '' }
  }
  const { port: sPort, suffix: sSuffix } = parseHandle(connection.sourceHandle ?? undefined, 'output')
  const { port: tPort, suffix: tSuffix } = parseHandle(connection.targetHandle ?? undefined, 'input')
  const sNode = workflowStore.nodes.find(n => n.id === sourceId)
  const tNode = workflowStore.nodes.find(n => n.id === targetId)
  if (!sNode || !tNode) return false
  const sDef = sNode.outputs.find(o => o.id === sPort)
  const tDef = tNode.inputs.find(i => i.id === tPort)
  if (!sDef || !tDef) {
    ElMessage.error('端口不存在或已变更')
    return false
  }
  const fmt = (def: any) => {
    const base = String(def?.id || def?.name || '').toLowerCase()
    const cleaned = base
      .replace(/^input-/, '')
      .replace(/^output-/, '')
      .replace(/(_files|_file|_paths|_path|_dir|_tsv|_csv|_json|_txt)$/, '')
      .replace(/[\-\s]/g, '')
    return cleaned
  }
  const compatible = (sd: any, td: any) => {
    const a = String(sd?.type || '')
    const b = String(td?.type || '')
    if (a === b && a !== 'file') return true
    if (a === 'file' && b === 'file') {
      const targetPort = ((tNode as any)?.nodeConfig?.inputs || []).find((i: any) => i.id === td.id) as any
      const accept = Array.isArray(targetPort?.accept) ? targetPort.accept : undefined
      const sourcePort = ((sNode as any)?.nodeConfig?.outputs || []).find((o: any) => o.id === sd.id) as any
      const sourceProvides = Array.isArray(sourcePort?.provides) ? sourcePort.provides : undefined
      // 若任一端未声明 accept/provides，则不限制，允许全部连接
      if (!Array.isArray(accept) || !Array.isArray(sourceProvides)) return true

      const sa = fmt(sd)
      const tb = fmt(td)
      if (!sa || !tb) return true
      if (sa === tb) return true
      const alias: Record<string, string[]> = {
        fasta: ['fa', 'fna'],
        mzml: ['mzml'],
        msalign: ['msalign'],
        txt: ['txt'],
        raw: ['raw']
      }
      const ok1 = (alias[sa] || []).includes(tb)
      const ok2 = (alias[tb] || []).includes(sa)
      if (ok1 || ok2) return true
      if (accept.map((x: string) => x.toLowerCase()).includes(sa)) return true
      const prov = sourceProvides.map((x: string) => x.toLowerCase())
      if (prov.includes(tb)) return true
      if (prov.some(p => (alias[p] || []).includes(tb))) return true
      const acc = accept.map((x: string) => x.toLowerCase())
      if (prov.some(p => acc.includes(p))) return true
      return false
    }
    return false
  }
  const stateValidation = stateBus.validateConnection(sDef as any, tDef as any)
  if (!stateValidation.ok) {
    ElMessage.error(stateValidation.reason)
    return false
  }
  const sourceKind = (sDef as any).portKind || 'data'
  const targetKind = (tDef as any).portKind || 'data'
  const isStateConnection = sourceKind === 'state-out' && targetKind === 'state-in'

  if (!isStateConnection && !compatible(sDef, tDef)) {
    ElMessage.error('文件类型不匹配')
    return false
  }
  // 检查重复连接（包括文件级别的连接）
  const dup = workflowStore.connections.find(c => {
    const sameNodes = c.source.nodeId === sourceId && c.target.nodeId === targetId
    const samePorts = c.source.portId === sPort && c.target.portId === tPort
    const sameFileSource = (c.dataPath?.s || '') === (sSuffix || '')
    const sameFileTarget = (c.dataPath?.t || '') === (tSuffix || '')
    return sameNodes && samePorts && sameFileSource && sameFileTarget
  })
  if (dup) {
    ElMessage.warning('重复连接')
    return false
  }
  if (isStateConnection) {
    const hasCycle = stateBus.detectCycle(sourceId, targetId, workflowStore.connections as any)
    if (hasCycle) {
      ElMessage.error('This connection would create a circular dependency')
      return false
    }
  }

  workflowStore.addConnection({
    source: { nodeId: sourceId, portId: sPort },
    target: { nodeId: targetId, portId: tPort },
    dataPath: { s: sSuffix || undefined, t: tSuffix || undefined }
  })
}

const onEdgeClick = (_evt: EdgeMouseEvent) => {
  emit('nodeSelect', null)
}

const onEdgeContextMenu = (evt: EdgeMouseEvent) => {
  evt.event.preventDefault()
  emit('contextMenu', evt.event, 'edge', evt.edge)
}

const onDragOver = (event: DragEvent) => {
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move'
  }
}

const onDrop = (event: any) => {
  event.preventDefault()

  // 获取拖拽的数据
  const nodeData = JSON.parse(event.dataTransfer.getData('text/plain'))

  // 获取鼠标在画布中的位置
  const rect = (event.target as HTMLElement).getBoundingClientRect()
  const position = {
    x: event.clientX - rect.left,
    y: event.clientY - rect.top
  }

  // 添加新节点到 store
  const newNode = workflowStore.addNode({
    type: nodeData.type || 'custom',
    position,
    displayProperties: {
      label: nodeData.name || '新节点',
      color: nodeData.displayProperties?.color || '#409eff',
      icon: nodeData.displayProperties?.icon
      // 不设置固定宽高，让节点根据内容自适应
    },
    inputs: nodeData.inputs || [],
    outputs: nodeData.outputs || [],
    nodeConfig: nodeData.nodeConfig || {}
  })

  // 选中新创建的节点
  emit('nodeSelect', newNode.id)
}
</script>

<style scoped>
.vue-flow-container {
  width: 100%;
  height: 100%;
  min-width: 400px;
  min-height: 400px;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
}

.vue-flow-editor {
  background: var(--ctp-base);
  border-radius: 8px;
}

.custom-workflow-node {
  background: var(--ctp-mantle);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 180px;
  min-height: 120px;
  position: relative;
  border-width: 2px;
  border-style: solid;
  transition: all 0.2s ease;
}

.custom-workflow-node:hover {
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
  transform: translateY(-2px);
}

.node-header {
  display: flex;
  align-items: center;
  padding: 12px;
  border-radius: 6px 6px 0 0;
  color: white;
  gap: 8px;
}

.node-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
}

.node-type-icon {
  font-size: 12px;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
}

.node-label {
  flex: 1;
  font-weight: 600;
  font-size: 14px;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.node-settings {
  position: absolute;
  top: -6px;
  right: -6px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.custom-workflow-node:hover .node-settings {
  opacity: 1;
}

.node-inputs,
.node-outputs {
  position: absolute;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-between;
  padding: 0 12px;
}

.node-inputs {
  top: 40px;
}

.node-outputs {
  bottom: 40px;
}

.port-label {
  font-size: 12px;
  color: var(--ctp-text);
  background: var(--ctp-base);
  padding: 2px 6px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.input-node,
.output-node {
  background: var(--ctp-mantle);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 120px;
  height: 60px;
  position: relative;
  border-width: 2px;
  border-style: solid;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 16px;
  transition: all 0.2s ease;
}

.input-node:hover,
.output-node:hover {
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
  transform: translateY(-2px);
}

.input-content,
.output-content {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.input-label,
.output-label {
  font-weight: 600;
  font-size: 14px;
  color: var(--ctp-text);
}

.empty-state {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  pointer-events: none;
}

.empty-content {
  background: var(--ctp-mantle);
  border: 2px dashed var(--ctp-surface0);
  border-radius: 12px;
  padding: 48px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.empty-icon {
  color: var(--icon-accent);
  opacity: 0.6;
}

.empty-content h3 {
  margin: 0;
  color: var(--ctp-text);
  font-size: 18px;
  font-weight: 600;
}

.empty-content p {
  margin: 0;
  color: var(--ctp-subtext0);
  font-size: 14px;
  line-height: 1.4;
}

/* Vue Flow Handle 样式覆盖 */
:deep(.vue-flow__handle) {
  width: 12px;
  height: 12px;
  border: 2px solid var(--ctp-base);
  border-radius: 50%;
  background: var(--ctp-overlay1);
  transition: all 0.2s ease;
}

:deep(.vue-flow__handle:hover) {
  transform: scale(1.2);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  background: var(--ctp-blue);
}

:deep(.vue-flow__handle.source) {
  right: -6px;
}

:deep(.vue-flow__handle.target) {
  left: -6px;
}

/* Vue Flow Edge 样式覆盖 */
:deep(.vue-flow__edge.selected) {
  stroke: var(--ctp-mauve) !important;
  stroke-width: 3 !important;
}

:deep(.vue-flow__edge.selected .vue-flow__edge-path) {
  stroke: var(--ctp-mauve) !important;
  stroke-width: 3 !important;
}

/* Vue Flow Controls 样式覆盖 */
:deep(.vue-flow__controls) {
  bottom: 20px;
  left: 20px;
}

/* Vue Flow MiniMap 样式覆盖 */
:deep(.vue-flow__minimap) {
  bottom: 20px;
  right: 20px;
  background: var(--ctp-mantle);
  border: 1px solid var(--ctp-surface0);
  border-radius: 8px;
}

/* Vue Flow 节点样式覆盖 - 确保高度自适应内容 */
:deep(.vue-flow__node) {
  height: auto !important;
  min-height: unset !important;
  padding: 0 !important;
  border: none !important;
  background: transparent !important;
}

:deep(.vue-flow__node.selected) {
  box-shadow: none !important;
}
</style>
