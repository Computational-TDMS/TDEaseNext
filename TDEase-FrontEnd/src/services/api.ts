import axios, { AxiosInstance, type InternalAxiosRequestConfig, type AxiosResponse } from 'axios'
import type { WorkflowJSON } from '@/stores/workflow'
import type { ToolConfig } from '@/services/tools/registry'

// API 基础配置
// If we are in dev mode, we rely on Vite proxy (configured in vite.config.ts) to forward /api requests to backend.
// So we can set base URL to empty or just use the relative path.
// However, if VITE_API_BASE_URL is set, we use it.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '' 

// 确保 baseURL 不会包含 HMR 端口 (1421)
// 如果 baseURL 包含 1421，说明配置错误，应该使用空字符串
const safeBaseURL = API_BASE_URL && !API_BASE_URL.includes('1421') ? API_BASE_URL : ''

// 创建 axios 实例
const apiClient: AxiosInstance = axios.create({
  baseURL: safeBaseURL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 确保 baseURL 不包含错误的端口（优先处理）
    if (config.baseURL && (config.baseURL.includes('1421') || config.baseURL.includes(':1421'))) {
      console.warn('[API] Detected baseURL with port 1421, resetting to empty', config.baseURL)
      config.baseURL = ''
    }
    
    // 确保完整 URL 不包含错误的端口
    const fullUrl = config.url || ''
    if (fullUrl.includes('localhost:1421') || fullUrl.includes('127.0.0.1:1421')) {
      console.warn('[API] Detected request URL with port 1421, fixing...', fullUrl)
      config.url = fullUrl.replace(/https?:\/\/[^\/]+:1421/, '').replace(/localhost:1421/, '').replace(/127\.0\.0\.1:1421/, '')
    }
    
    // 确保最终的完整URL是正确的
    const finalUrl = (config.baseURL || '') + (config.url || '')
    if (finalUrl.includes(':1421') && !finalUrl.includes(':8000')) {
      console.error('[API] Final URL still contains 1421!', { baseURL: config.baseURL, url: config.url, finalUrl })
      // 强制修复：如果仍然包含 1421，移除所有端口信息，让代理处理
      if (config.url && config.url.includes(':1421')) {
        config.url = config.url.replace(/:\d+/, '').replace(/localhost:1421/, 'localhost').replace(/127\.0\.0\.1:1421/, '127.0.0.1')
      }
      if (config.baseURL && config.baseURL.includes(':1421')) {
        config.baseURL = ''
      }
    }
    
    // 调试日志：记录所有请求
    console.log('[API] Request:', { method: config.method, url: config.url, baseURL: config.baseURL, fullUrl: finalUrl })
    
    return config
  },
  (error) => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  (error) => {
    // 只记录非404错误（404是正常的，表示资源不存在）
    if (error.response?.status !== 404) {
      console.error('Response error:', error)
    }
    if (error.response?.status === 401) {
      // 处理认证错误
      localStorage.removeItem('auth_token')
      // 可以在这里重定向到登录页
    }
    return Promise.reject(error)
  }
)

// API 响应类型定义
export interface ApiResponse<T = any> {
  data: T
  message: string
  status: number
  success: boolean
}

export interface WorkflowListResponse {
  workflows: Array<{
    id: string
    name: string
    description?: string
    version: string
    created: string
    modified: string
    author?: string
  }>
  total: number
  page: number
  pageSize: number
}

export interface WorkflowExecutionResponse {
  executionId: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  startTime?: string
  endTime?: string
  progress: number
  logs: Array<{
    timestamp: string
    level: 'info' | 'warning' | 'error'
    message: string
  }>
  results?: Record<string, any>
}

export interface NodeTemplateResponse {
  templates: Array<{
    id: string
    name: string
    type: string
    category: string
    description: string
    icon?: string
    color?: string
    inputs: Array<{
      id: string
      name: string
      type: string
      required: boolean
      description?: string
    }>
    outputs: Array<{
      id: string
      name: string
      type: string
      required: boolean
      description?: string
    }>
    parameters: Array<{
      id: string
      name: string
      type:
        | 'string'
        | 'number'
        | 'boolean'
        | 'select'
        | 'multiselect'
        | 'range'
        | 'int'
        | 'float'
        | 'slider'
        | 'radio'
        | 'checkbox'
      required: boolean
      default?: any
      description?: string
      options?: Array<{ label: string; value: any }>
    }>
  }>
}

// 工作流 API
export const workflowApi = {
  // 获取工作流列表
  getWorkflows: (page: number = 1, pageSize: number = 20): Promise<ApiResponse<WorkflowListResponse>> => {
    return apiClient.get('/api/workflows', {
      params: { page, pageSize }
    })
  },

  // 获取工作流详情
  getWorkflow: (id: string): Promise<ApiResponse<any>> => {
    return apiClient.get(`/api/workflows/${id}`)
  },

  // 创建工作流
  createWorkflow: (workflow: any): Promise<ApiResponse<any>> => {
    return apiClient.post('/api/workflows', workflow)
  },

  // 更新工作流
  updateWorkflow: (id: string, workflow: any): Promise<ApiResponse<any>> => {
    return apiClient.put(`/api/workflows/${id}`, workflow)
  },

  // 删除工作流
  deleteWorkflow: (id: string): Promise<ApiResponse<any>> => {
    return apiClient.delete(`/api/workflows/${id}`)
  },

  // 执行工作流（新架构格式）
  executeWorkflow: (id: string, parameters?: Record<string, any>): Promise<ApiResponse<WorkflowExecutionResponse>> => {
    // 新架构：使用 workflow_id + user_id/workspace_id/sample_ids 格式
    const executeParams = {
      workflow_id: id,
      user_id: parameters?.user_id || 'test_user',
      workspace_id: parameters?.workspace_id || 'test_workspace',
      sample_ids: parameters?.sample_ids || ['sample1']
    }
    return apiClient.post(`/api/workflows/execute`, executeParams)
  },

  // 直接执行工作流（从前端 JSON 直接构建并执行）
  executeCompiledWorkflow: (
    workflow: WorkflowJSON,
    _tools: ToolConfig[],
    parameters?: Record<string, any>
  ): Promise<ApiResponse<WorkflowExecutionResponse>> => {
    // 新架构：从 workflow metadata 提取 ID，然后使用新格式
    const workflowId = workflow.metadata?.id
    if (!workflowId) {
      throw new Error('Workflow ID is required for execution')
    }

    const executeParams = {
      workflow_id: workflowId,
      user_id: parameters?.user_id || 'test_user',
      workspace_id: parameters?.workspace_id || 'test_workspace',
      sample_ids: parameters?.sample_ids || ['sample1']
    }
    return apiClient.post(`/api/workflows/execute`, executeParams)
  },

  // 获取执行状态
  getExecutionStatus: (executionId: string): Promise<ApiResponse<WorkflowExecutionResponse>> => {
    return apiClient.get(`/api/executions/${executionId}`)
  },

  // 停止执行
  stopExecution: (executionId: string): Promise<ApiResponse<any>> => {
    return apiClient.post(`/api/executions/${executionId}/stop`)
  },

  // 批量处理配置
  saveBatchConfig: (workflowId: string, batchConfig: any): Promise<ApiResponse<any>> => {
    return apiClient.post(`/api/workflows/${workflowId}/batch-config`, batchConfig)
  },

  getBatchConfig: (workflowId: string): Promise<ApiResponse<any>> => {
    return apiClient.get(`/api/workflows/${workflowId}/batch-config`)
  },

  executeBatch: (workflowId: string, batchConfig?: any): Promise<ApiResponse<WorkflowExecutionResponse[]>> => {
    // 新架构格式
    const params = {
      user_id: batchConfig?.user_id || 'test_user',
      workspace_id: batchConfig?.workspace_id || 'test_workspace',
      sample_ids: batchConfig?.sample_ids || ['sample1']
    }
    return apiClient.post(`/api/workflows/${workflowId}/execute-batch`, params)
  },

  // 获取执行日志
  getExecutionLogs: (executionId: string, level?: string): Promise<ApiResponse<any>> => {
    return apiClient.get(`/api/executions/${executionId}/logs`, {
      params: level ? { level } : {}
    })
  }
}

// 节点模板 API
export const nodeTemplateApi = {
  // 获取节点模板
  getNodeTemplates: (category?: string): Promise<ApiResponse<NodeTemplateResponse>> => {
    return apiClient.get('/api/node-templates', {
      params: category ? { category } : {}
    })
  },

  // 获取节点模板详情
  getNodeTemplate: (id: string): Promise<ApiResponse<any>> => {
    return apiClient.get(`/api/node-templates/${id}`)
  }
}

// 数据处理 API
export const dataProcessingApi = {
  // 获取数据源
  getDataSources: (): Promise<ApiResponse<any>> => {
    return apiClient.get('/api/data-sources')
  },

  // 上传文件
  uploadFile: (file: File, workflowId?: string): Promise<ApiResponse<any>> => {
    const formData = new FormData()
    formData.append('file', file)
    if (workflowId) {
      formData.append('workflowId', workflowId)
    }

    return apiClient.post('/api/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },

  // 获取处理结果
  getProcessingResults: (executionId: string): Promise<ApiResponse<any>> => {
    return apiClient.get(`/api/executions/${executionId}/results`)
  },

  // 下载结果
  downloadResults: async (executionId: string, format: string = 'json'): Promise<Blob> => {
    const response = await axios.get(`/api/executions/${executionId}/download`, {
      baseURL: safeBaseURL,
      responseType: 'blob',
      params: { format }
    })
    return response.data as Blob
  }
}

export default apiClient
