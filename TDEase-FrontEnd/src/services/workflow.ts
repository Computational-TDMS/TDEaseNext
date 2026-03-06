import { ElMessage, ElMessageBox } from 'element-plus'
import apiClient, { workflowApi, dataProcessingApi, type WorkflowExecutionResponse } from './api'
import type { WorkflowJSON } from '@/stores/workflow'
import { useToolsRegistry } from '@/services/tools/registry'
import type { ToolConfig } from '@/services/tools/registry'
import { selectToolsForWorkflow } from '@/services/tools/select'
import { importRawWorkflow } from '@/utils/workflow-import'

import type { BatchConfig } from '@/types/workflow'

// 注意: 参数过滤已移至后端 CommandPipeline，前端直接传递所有参数值

// WebSocket message types
interface WebSocketMessage {
  type: 'log' | 'status' | 'connected' | 'error' | 'pong'
  data?: any
  status?: string
  progress?: number
  execution_id?: string
  timestamp?: string
}

// WebSocket connection state
class ExecutionWebSocket {
  private ws: WebSocket | null = null
  private executionId: string
  private url: string
  private messageHandlers: Map<string, (data: any) => void>
  private reconnectAttempts = 0
  private maxReconnectAttempts = 3
  private reconnectDelay = 1000
  private isManualClose = false

  constructor(executionId: string, wsUrl: string) {
    this.executionId = executionId
    this.url = `${wsUrl}/ws/executions/${executionId}`
    this.messageHandlers = new Map()
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url)
        this.isManualClose = false

        this.ws.onopen = () => {
          console.log(`WebSocket connected for execution: ${this.executionId}`)
          this.reconnectAttempts = 0
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data)
            this.handleMessage(message)
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error)
          }
        }

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          reject(error)
        }

        this.ws.onclose = (_event) => {
          if (!this.isManualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
            console.log(`WebSocket closed, reconnecting... (attempt ${this.reconnectAttempts + 1})`)
            setTimeout(() => {
              this.reconnectAttempts++
              this.connect().catch(() => {
                // Trigger fallback to polling
                this.messageHandlers.get('error')?.({ type: 'connection_lost' })
              })
            }, this.reconnectDelay * this.reconnectAttempts)
          }
        }
      } catch (error) {
        reject(error)
      }
    })
  }

  private handleMessage(message: WebSocketMessage) {
    const handler = this.messageHandlers.get(message.type)
    if (handler) {
      handler(message.data || message)
    }

    // Special handling for status updates
    if (message.type === 'status') {
      const statusHandler = this.messageHandlers.get('status')
      if (statusHandler) {
        statusHandler(message)
      }
    }
  }

  on(event: string, handler: (data: any) => void) {
    this.messageHandlers.set(event, handler)
  }

  off(event: string) {
    this.messageHandlers.delete(event)
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }

  close() {
    this.isManualClose = true
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  get isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN
  }
}

export class WorkflowService {
  // 工作流管理
  static async loadWorkflows(page: number = 1, pageSize: number = 20) {
    try {
      const response = await workflowApi.getWorkflows(page, pageSize)
      // Backend returns WorkflowListResponse directly
      if (response && (response as any).workflows) {
        return response as any
      } else if ((response as any).success && (response as any).data) {
        // Fallback for wrapped response
        return (response as any).data
      } else {
        throw new Error('加载工作流列表失败')
      }
    } catch (error) {
      console.error('Failed to load workflows:', error)
      ElMessage.error('加载工作流列表失败')
      throw error
    }
  }

  static async loadWorkflow(id: string): Promise<WorkflowJSON> {
    try {
      const response = await workflowApi.getWorkflow(id)
      console.log('loadWorkflow response:', response)
      
      let rawData: any = null;
      // Backend returns WorkflowResponse directly
      if (response && (response as any).vueflow_data) {
        rawData = (response as any).vueflow_data;
      } else if ((response as any).success && (response as any).data && (response as any).data.vueflow_data) {
        rawData = (response as any).data.vueflow_data;
      }

      if (rawData) {
          console.log('[loadWorkflow] rawData structure:', { hasEdges: !!rawData.edges, hasConnections: !!rawData.connections, edgesCount: rawData.edges?.length, connectionsCount: rawData.connections?.length })
          // If it has edges but no connections (or empty connections array), convert it
          const hasEdges = Array.isArray(rawData.edges) && rawData.edges.length > 0
          const hasValidConnections = Array.isArray(rawData.connections) && rawData.connections.length > 0

          if (hasEdges && !hasValidConnections) {
              const registry = await loadToolRegistry()
              const converted = importRawWorkflow(rawData, registry)
              console.log('[loadWorkflow] Converted workflow:', { connectionsCount: converted.connections?.length })
              return await mergeToolConfigsToWorkflow(converted, registry)
          }
          // If it has valid connections, assume it's already WorkflowJSON
          // But still need to merge tool registry configs (executionMode, visualizationConfig)
          if (hasValidConnections) {
              const registry = await loadToolRegistry()
              return await mergeToolConfigsToWorkflow(rawData as WorkflowJSON, registry)
          }
          // Fallback: try to import anyway
          const registry = await loadToolRegistry()
          return await mergeToolConfigsToWorkflow(importRawWorkflow(rawData, registry), registry)
      }
      
      console.error('Invalid workflow response structure (missing vueflow_data):', response)
      throw new Error('加载工作流失败: Invalid structure')
    } catch (error) {
      console.error('Failed to load workflow:', error)
      // ElMessage.error('加载工作流失败') // Suppress ElMessage
      throw error
    }
  }

  static async saveWorkflow(workflow: WorkflowJSON, silent: boolean = false): Promise<void> {
    try {
      const workflowId = workflow.metadata.id
      if (!workflowId) {
        throw new Error('工作流ID不能为空')
      }

      // 检查工作流是否存在
      let workflowExists = false
      try {
        await workflowApi.getWorkflow(workflowId)
        workflowExists = true
      } catch (error: any) {
        // 如果返回404，说明工作流不存在
        if (error?.response?.status === 404 || error?.status === 404) {
          workflowExists = false
        } else {
          // 其他错误，可能是网络问题等，仍然尝试创建
          console.warn('检查工作流是否存在时出错，将尝试创建新工作流:', error)
          workflowExists = false
        }
      }

      const vueflow_data = {
        metadata: {
          id: workflow.metadata.id,
          name: workflow.metadata.name,
          version: workflow.metadata.version,
          description: workflow.metadata.description,
          author: workflow.metadata.author,
          created: workflow.metadata.created,
          modified: workflow.metadata.modified,
          tags: workflow.metadata.tags || []
        },
        format_version: workflow.format_version || "2.0",
        nodes: workflow.nodes.map(n => ({
          id: n.id,
          type: (n as any).nodeConfig?.toolId || n.type,
          position: n.position,
          data: {
            type: (n as any).nodeConfig?.toolId || n.type,
            params: (n as any).nodeConfig?.paramValues || {}
          }
        })),
        edges: workflow.connections.map(c => ({
          id: c.id,
          source: c.source.nodeId,
          target: c.target.nodeId,
          sourceHandle: `output-${c.source.portId}`,
          targetHandle: `input-${c.target.portId}`
        })),
        projectSettings: workflow.projectSettings || {}
      }
      const payload = {
        name: workflow.metadata.name,
        description: workflow.metadata.description || '',
        workspace_path: 'data',
        vueflow_data,
        samples: (vueflow_data as any)?.metadata?.samples || []
      }

      let response
      if (workflowExists) {
        // 更新现有工作流
        response = await workflowApi.updateWorkflow(workflowId, payload as any)
        if (!silent) {
          ElMessage.success('工作流更新成功')
        }
      } else {
        // 创建新工作流（后端生成 workflow_id，前端需采纳）
        response = await workflowApi.createWorkflow(payload as any)
        const backendId = (response as any)?.id
        if (backendId && backendId !== workflowId) {
          workflow.metadata.id = backendId
        }
        if (!silent) {
          ElMessage.success('工作流保存成功')
        }
      }

      // 验证响应
      if (response && (response as any).id) {
        // 响应有效
      } else if ((response as any).success) {
        // 响应有效
      } else {
        throw new Error('保存工作流失败：无效的响应')
      }
    } catch (error) {
      console.error('Failed to save workflow:', error)
      if (!silent) {
        ElMessage.error('保存工作流失败')
      }
      throw error
    }
  }

  static async updateWorkflow(id: string, workflow: WorkflowJSON): Promise<void> {
    try {
      const vueflow_data = {
        metadata: {
          id: workflow.metadata.id,
          name: workflow.metadata.name,
          version: workflow.metadata.version,
          description: workflow.metadata.description,
          created: workflow.metadata.created,
          modified: workflow.metadata.modified
        },
        nodes: workflow.nodes.map(n => ({
          id: n.id,
          type: (n as any).nodeConfig?.toolId || n.type,
          position: n.position,
          data: {
            type: (n as any).nodeConfig?.toolId || n.type,
            params: (n as any).nodeConfig?.paramValues || {}
          }
        })),
        edges: workflow.connections.map(c => ({
          id: c.id,
          source: c.source.nodeId,
          target: c.target.nodeId,
          sourceHandle: `output-${c.source.portId}`,
          targetHandle: `input-${c.target.portId}`
        })),
        projectSettings: workflow.projectSettings || {}
      }
      const payload = {
        name: workflow.metadata.name,
        description: workflow.metadata.description || '',
        workspace_path: 'data',
        vueflow_data
      }
      const response = await workflowApi.updateWorkflow(id, payload as any)
      if (response && (response as any).id) {
        ElMessage.success('工作流更新成功')
      } else if ((response as any).success) {
        ElMessage.success('工作流更新成功')
      } else {
        throw new Error('更新工作流失败')
      }
    } catch (error) {
      console.error('Failed to update workflow:', error)
      ElMessage.error('更新工作流失败')
      throw error
    }
  }

  static async deleteWorkflow(id: string): Promise<void> {
    try {
      await ElMessageBox.confirm(
        '确定要删除此工作流吗？此操作不可撤销。',
        '删除工作流',
        {
          confirmButtonText: '确定删除',
          cancelButtonText: '取消',
          type: 'warning',
          confirmButtonClass: 'el-button--danger'
        }
      )

      const response = await workflowApi.deleteWorkflow(id)
      // SuccessResponse has .success field
      if ((response as any).success) {
        ElMessage.success('工作流删除成功')
      } else {
        throw new Error((response as any).message || '删除工作流失败')
      }
    } catch (error) {
      console.error('Failed to delete workflow:', error)
      ElMessage.error('删除工作流失败')
      // 用户取消时不显示错误
    }
  }

  // 工作流执行
  static async executeWorkflow(id: string, parameters?: Record<string, any>): Promise<WorkflowExecutionResponse> {
    try {
      const response = await workflowApi.executeWorkflow(id, parameters)
      // Backend returns WorkflowExecutionResponse directly
      if (response && (response as any).executionId) {
        ElMessage.success('工作流执行启动成功')
        return response as any
      } else if ((response as any).success && (response as any).data) {
        ElMessage.success('工作流执行启动成功')
        return (response as any).data
      } else {
        throw new Error('启动工作流执行失败')
      }
    } catch (error) {
      console.error('Failed to execute workflow:', error)
      ElMessage.error('启动工作流执行失败')
      throw error
    }
  }

  static async executeCompiled(
    workflow: WorkflowJSON,
    tools?: ToolConfig[],
    parameters?: Record<string, any>,
    silent: boolean = false
  ): Promise<WorkflowExecutionResponse> {
    try {
      const registry = useToolsRegistry().value
      const selected = tools && tools.length ? tools : selectToolsForWorkflow(workflow, registry)
      const response = await workflowApi.executeCompiledWorkflow(workflow, selected, parameters)
      
      if (response && (response as any).executionId) {
        if (!silent) {
          ElMessage.success('工作流执行启动成功')
        }
        return response as any
      } else if ((response as any).success && (response as any).data) {
        if (!silent) {
          ElMessage.success('工作流执行启动成功')
        }
        return (response as any).data
      } else {
        throw new Error('执行工作流失败')
      }
    } catch (error) {
      console.error('Failed to execute workflow:', error)
      if (!silent) {
        ElMessage.error('执行工作流失败')
      }
      throw error
    }
  }

  static async importWorkflowFromObject(workflowRaw: any): Promise<string> {
    try {
      const response = await workflowApi.createWorkflow(workflowRaw)
      // Check for direct response or wrapped
      let workflowId;
      if (response && (response as any).id) {
          workflowId = (response as any).id;
      } else if ((response as any).success && (response as any).data) {
          const data = (response as any).data;
          workflowId = data?.id || data?.workflow?.id;
      }

      if (!workflowId) {
        throw new Error('后端未返回工作流ID')
      }
      
      ElMessage.success('工作流导入成功')
      return String(workflowId)
    } catch (error) {
      console.error('Failed to import workflow:', error)
      ElMessage.error('导入工作流失败')
      throw error
    }
  }

  static async runWorkflowFromObject(workflowRaw: any, parameters?: Record<string, any>): Promise<WorkflowExecutionResponse> {
    const workflowId = await this.importWorkflowFromObject(workflowRaw)
    return await this.executeWorkflow(workflowId, parameters)
  }

  static async getExecutionStatus(executionId: string): Promise<WorkflowExecutionResponse> {
    try {
      const response = await workflowApi.getExecutionStatus(executionId)
      if ((response as any)?.executionId) return response as any
      if ((response as any)?.success && (response as any)?.data) return (response as any).data
      throw new Error('获取执行状态失败')
    } catch (error) {
      console.error('Failed to get execution status:', error)
      throw error
    }
  }

  static async stopExecution(executionId: string): Promise<void> {
    try {
      const response = await workflowApi.stopExecution(executionId)
      if (response.success) {
        ElMessage.success('工作流执行已停止')
      } else {
        throw new Error(response.message || '停止工作流执行失败')
      }
    } catch (error) {
      console.error('Failed to stop execution:', error)
      ElMessage.error('停止工作流执行失败')
      throw error
    }
  }

  // 文件上传
  static async uploadFile(file: File, workflowId?: string): Promise<any> {
    try {
      const response = await dataProcessingApi.uploadFile(file, workflowId)
      if (response.success) {
        ElMessage.success('文件上传成功')
        return response.data
      } else {
        throw new Error(response.message || '文件上传失败')
      }
    } catch (error) {
      console.error('Failed to upload file:', error)
      ElMessage.error('文件上传失败')
      throw error
    }
  }

  static async downloadResults(executionId: string, format: string = 'json'): Promise<void> {
    try {
      const blob = await dataProcessingApi.downloadResults(executionId, format)
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `workflow-results-${executionId}.${format}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      ElMessage.success('结果下载成功')
    } catch (error) {
      console.error('Failed to download results:', error)
      ElMessage.error('结果下载失败')
      throw error
    }
  }

  // 获取执行日志
  static async getExecutionLogs(executionId: string, level?: string): Promise<any[]> {
    try {
      const response = await workflowApi.getExecutionLogs(executionId, level)
      // Backend returns { logs: [...] }, extract the logs array
      if (response && (response as any).logs && Array.isArray((response as any).logs)) {
        return (response as any).logs
      }
      if (Array.isArray(response)) {
        return response
      }
      if ((response as any)?.success && (response as any)?.data?.logs) {
        return (response as any).data.logs
      }
      // Return empty array if no logs found
      return []
    } catch (error) {
      console.error('Failed to get execution logs:', error)
      ElMessage.error('获取执行日志失败')
      return []
    }
  }

  // 获取数据源
  static async getDataSources(): Promise<any[]> {
    try {
      const response = await dataProcessingApi.getDataSources()
      if (response.success) {
        return response.data || []
      } else {
        throw new Error(response.message || '获取数据源失败')
      }
    } catch (error) {
      console.error('Failed to get data sources:', error)
      ElMessage.error('获取数据源失败')
      return []
    }
  }

  // 批量处理配置
  static async saveBatchConfig(workflowId: string, batchConfig: BatchConfig): Promise<void> {
    try {
      const response = await workflowApi.saveBatchConfig(workflowId, batchConfig)
      if ((response as any).success) {
        ElMessage.success('批量配置保存成功')
      } else {
        throw new Error((response as any).message || '保存批量配置失败')
      }
    } catch (error) {
      console.error('Failed to save batch config:', error)
      ElMessage.error('保存批量配置失败')
      throw error
    }
  }

  static async getBatchConfig(workflowId: string): Promise<BatchConfig> {
    try {
      const response = await workflowApi.getBatchConfig(workflowId)
      return response as any
    } catch (error) {
      console.error('Failed to get batch config:', error)
      ElMessage.error('获取批量配置失败')
      throw error
    }
  }

  static async executeBatch(
    workflowId: string,
    batchConfig?: BatchConfig
  ): Promise<WorkflowExecutionResponse[]> {
    try {
      const response = await workflowApi.executeBatch(workflowId, batchConfig)
      ElMessage.success('批量执行启动成功')
      return response as any
    } catch (error) {
      console.error('Failed to execute batch:', error)
      ElMessage.error('批量执行失败')
      throw error
    }
  }

  // WebSocket 实时日志监控
  static connectExecutionWebSocket(
    executionId: string,
    onLog: (log: any) => void,
    onStatus: (status: string, progress?: number) => void,
    onError?: (error: any) => void
  ): ExecutionWebSocket {
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
    const ws = new ExecutionWebSocket(executionId, wsUrl)

    ws.on('log', onLog)
    ws.on('status', onStatus)

    if (onError) {
      ws.on('error', onError)
    }

    // Connect with timeout fallback
    const connectTimeout = setTimeout(() => {
      if (!ws.isConnected) {
        console.log('WebSocket connection timeout, falling back to polling')
        onError?.({ type: 'connection_timeout' })
        ws.close()
      }
    }, 3000)

    ws.connect()
      .then(() => clearTimeout(connectTimeout))
      .catch((error) => {
        clearTimeout(connectTimeout)
        console.error('WebSocket connection failed:', error)
        onError?.(error)
      })

    return ws
  }

  // 开始执行监控（WebSocket + 轮询降级）
  static startExecutionMonitoring(
    executionId: string,
    options: {
      onLog?: (log: any) => void
      onStatus?: (status: string, progress?: number) => void
      onComplete?: () => void
      onError?: (error: any) => void
      usePollingFallback?: boolean
    } = {}
  ): { stop: () => void; ws: ExecutionWebSocket | null } {
    const {
      onLog = () => {},
      onStatus = () => {},
      onComplete = () => {},
      onError = () => {},
      usePollingFallback = true
    } = options

    let pollingTimer: ReturnType<typeof setInterval> | null = null
    let ws: ExecutionWebSocket | null = null

    // 轮询函数（降级方案）
    const startPolling = () => {
      console.log('Starting polling fallback for execution:', executionId)
      let consecutiveErrors = 0

      pollingTimer = setInterval(async () => {
        try {
          const resp = await this.getExecutionStatus(executionId)
          consecutiveErrors = 0
          const currentStatus = resp?.status ?? resp
          onStatus(currentStatus, resp?.progress)

          // 获取日志
          const logs = await this.getExecutionLogs(executionId)
          logs.forEach(log => onLog(log))

          // 检查是否完成 -> 立即停止轮询
          if (['completed', 'failed', 'cancelled'].includes(String(currentStatus || ''))) {
            stopMonitoring()
            onComplete()
          }
        } catch (error: any) {
          consecutiveErrors++
          console.error('Polling error:', error)
          onError(error)
          // 404 表示执行已不存在；连续 5 次错误则停止，避免无限轮询
          if (error?.response?.status === 404 || consecutiveErrors >= 5) {
            stopMonitoring()
          }
        }
      }, 2000) // 每2秒轮询一次
    }

    // 停止监控
    const stopMonitoring = () => {
      if (ws) {
        ws.close()
        ws = null
      }
      if (pollingTimer) {
        clearInterval(pollingTimer)
        pollingTimer = null
      }
    }

    // 尝试 WebSocket 连接
    ws = this.connectExecutionWebSocket(
      executionId,
      onLog,
      (data: any) => {
        const status = data.status || data
        const progress = data.progress
        onStatus(status, progress)

        // 检查是否完成
        if (['completed', 'failed', 'cancelled'].includes(status)) {
          stopMonitoring()
          onComplete()
        }
      },
      (error: any) => {
        // WebSocket 连接失败或超时，使用轮询降级
        if (usePollingFallback) {
          console.log('WebSocket unavailable, using polling fallback')
          startPolling()
        } else {
          onError(error)
        }
      }
    )

    return { stop: stopMonitoring, ws }
  }
}

/**
 * Merge tool registry configs (executionMode, visualizationConfig) to workflow nodes.
 * This ensures that interactive visualization nodes have the necessary configuration
 * to render properly, even when loading from a saved workflow that may be missing
 * these fields.
 */
async function loadToolRegistry(): Promise<Record<string, any>> {
  try {
    const json = await apiClient.get<{ registry?: Record<string, unknown> }>('/api/tools/schemas')
    return (json as any)?.registry || {}
  } catch (e) {
    console.warn('[loadToolRegistry] Failed to load tool registry:', e)
  }
  return {}
}

async function mergeToolConfigsToWorkflow(workflow: WorkflowJSON, registryPreloaded?: Record<string, any>): Promise<WorkflowJSON> {
  const registry = registryPreloaded ?? await loadToolRegistry()
  console.log('[mergeToolConfigsToWorkflow] Registry loaded:', Object.keys(registry))

  const nodes = workflow.nodes.map(node => {
    const rawToolId =
      (node as any).nodeConfig?.toolId ||
      (node as any).data?.toolId ||
      (node as any).data?.type ||
      (node.type !== 'tool' ? node.type : null)
    const toolId = typeof rawToolId === 'string' ? rawToolId.trim() : null
    const toolCfg = toolId ? registry[toolId] : undefined

    if (!toolCfg) {
      return node
    }

    console.log(`[mergeToolConfigsToWorkflow] Node ${node.id}: toolId=${toolId}, hasExecutionMode=${!!toolCfg.executionMode}`)

    return {
      ...node,
      // Merge executionMode if not already present
      executionMode: node.executionMode || toolCfg.executionMode || toolCfg.execution_mode || undefined,
      // Merge visualizationConfig if not already present
      visualizationConfig: node.visualizationConfig || (toolCfg.visualization ? {
        type: toolCfg.visualization.type,
        config: toolCfg.visualization.config,
        components: toolCfg.visualization.components
      } : undefined),
      // Update inputs with portKind and semanticType if missing
      inputs: node.inputs.map(input => {
        const portDef = (toolCfg.ports?.inputs || toolCfg.inputs || []).find(
          (p: any) => p.id === input.id
        )
        if (!portDef) return input
        return {
          ...input,
          portKind: (input as any).portKind || (portDef as any).portKind || undefined,
          semanticType: (input as any).semanticType || (portDef as any).semanticType || undefined
        }
      }),
      // Update outputs with portKind and semanticType if missing
      outputs: node.outputs.map(output => {
        const portDef = (toolCfg.ports?.outputs || toolCfg.outputs || []).find(
          (p: any) => (p.handle || p.id) === output.id
        )
        if (!portDef) return output
        return {
          ...output,
          portKind: (output as any).portKind || (portDef as any).portKind || undefined,
          semanticType: (output as any).semanticType || (portDef as any).semanticType || undefined
        }
      })
    }
  })

  return {
    ...workflow,
    nodes
  }
}

export default WorkflowService
