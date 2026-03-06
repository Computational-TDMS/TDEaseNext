/**
 * API response and request types
 * Defines all backend API communication interfaces
 */

import type {
  WorkflowJSON,
  WorkflowSummary,
  ExecutionLog,
  NodeStateInfo,
  ExecutionState,
  PortDefinition,
  ParameterDefinition,
} from './workflow'

// API Response wrapper
export interface APIResponse<T> {
  data: T
  status: number
  headers: Record<string, string>
}

// API Error response
export interface APIError {
  message: string
  status: number
  code: string
  details?: unknown
}

// Workflow API responses
export interface WorkflowListResponse {
  workflows: WorkflowSummary[]
  total: number
}

export interface WorkflowCreateRequest {
  name: string
  description?: string
}

export interface WorkflowCreateResponse {
  workflow: WorkflowJSON
}

export interface WorkflowLoadResponse {
  workflow: WorkflowJSON
}

export interface WorkflowSaveRequest {
  workflow: WorkflowJSON
}

export interface WorkflowSaveResponse {
  success: boolean
  message?: string
}

export interface WorkflowDeleteResponse {
  success: boolean
  message?: string
}

// Execution API responses
export interface ExecutionRequest {
  workflowId: string
  parameters?: Record<string, unknown>
}

export interface ExecutionResponse {
  executionId: string
  status: ExecutionState
  message?: string
}

export interface ExecutionStatus {
  executionId: string
  status: ExecutionState
  progress: number
  currentNode?: string
  nodeStates: Record<string, NodeStateInfo>
  logs: ExecutionLog[]
  startTime: number
  endTime?: number
}

export interface ExecutionControlResponse {
  success: boolean
  message?: string
}

export interface ExecutionLogsResponse {
  logs: ExecutionLog[]
  total: number
}

// Tool API responses
export interface ToolDefinition {
  id: string
  name: string
  category: string
  description: string
  inputs: PortDefinition[]
  outputs: PortDefinition[]
  parameters: ParameterDefinition[]
  executionType: 'cli' | 'python' | 'docker' | 'cloud'
}

export interface ToolListResponse {
  tools: ToolDefinition[]
  categories: string[]
}

export interface ToolDetailResponse {
  tool: ToolDefinition
}

// File upload/download responses
export interface FileUploadResponse {
  fileId: string
  path: string
  size: number
}

export interface FileUploadProgress {
  fileId: string
  loaded: number
  total: number
  percentage: number
}

export interface FileDownloadResponse {
  fileId: string
  url: string
  size: number
}

// Health check response
export interface HealthCheckResponse {
  status: 'ok' | 'error'
  message: string
  timestamp: number
}
