/**
 * Execution Service for managing workflow execution
 * Handles execution control, status tracking, and log management
 */

import type { APIClient } from '../api/client'
import type { WebSocketService } from '../websocket/service'
import type {
  ExecutionState,
  NodeState,
  ExecutionLog,
} from '../../types/workflow'
import type { ExecutionRequest, ExecutionStatus } from '../../types/api'
import { createError, ErrorCode } from '../../types/errors'

type ExecutionStatusHandler = (status: ExecutionStatus) => void
type ExecutionLogHandler = (log: ExecutionLog) => void

/**
 * ExecutionService class for managing workflow execution
 */
export class ExecutionService {
  private statusHandlers: Set<ExecutionStatusHandler> = new Set()
  private logHandlers: Set<ExecutionLogHandler> = new Set()
  private executionStates: Map<string, ExecutionStatus> = new Map()
  private wsUnsubscribers: Map<string, () => void> = new Map()

  constructor(
    private apiClient: APIClient,
    private wsService: WebSocketService
  ) {
    this.setupWebSocketListeners()
  }

  /**
   * Start a workflow execution
   */
  async start(request: ExecutionRequest): Promise<string> {
    try {
      const response = await this.apiClient.post<{ executionId: string }>(
        '/executions',
        request
      )

      const executionId = response.data.executionId

      // Initialize execution state
      this.executionStates.set(executionId, {
        executionId,
        status: 'running',
        progress: 0,
        nodeStates: {},
        logs: [],
        startTime: Date.now(),
      })

      return executionId
    } catch (error) {
      throw createError(
        ErrorCode.EXECUTION_FAILED,
        `Failed to start execution: ${error instanceof Error ? error.message : String(error)}`,
        undefined,
        { error, request }
      )
    }
  }

  /**
   * Pause a workflow execution
   */
  async pause(executionId: string): Promise<void> {
    try {
      await this.apiClient.post(`/executions/${executionId}/pause`, {})

      // Update local state
      const status = this.executionStates.get(executionId)
      if (status) {
        status.status = 'paused'
        this.notifyStatusHandlers(status)
      }
    } catch (error) {
      throw createError(
        ErrorCode.EXECUTION_FAILED,
        `Failed to pause execution: ${error instanceof Error ? error.message : String(error)}`,
        undefined,
        { error, executionId }
      )
    }
  }

  /**
   * Resume a workflow execution
   */
  async resume(executionId: string): Promise<void> {
    try {
      await this.apiClient.post(`/executions/${executionId}/resume`, {})

      // Update local state
      const status = this.executionStates.get(executionId)
      if (status) {
        status.status = 'running'
        this.notifyStatusHandlers(status)
      }
    } catch (error) {
      throw createError(
        ErrorCode.EXECUTION_FAILED,
        `Failed to resume execution: ${error instanceof Error ? error.message : String(error)}`,
        undefined,
        { error, executionId }
      )
    }
  }

  /**
   * Cancel a workflow execution
   */
  async cancel(executionId: string): Promise<void> {
    try {
      await this.apiClient.post(`/executions/${executionId}/cancel`, {})

      // Update local state
      const status = this.executionStates.get(executionId)
      if (status) {
        status.status = 'cancelled'
        this.notifyStatusHandlers(status)
      }

      // Clean up WebSocket listeners
      this.cleanupExecution(executionId)
    } catch (error) {
      throw createError(
        ErrorCode.EXECUTION_FAILED,
        `Failed to cancel execution: ${error instanceof Error ? error.message : String(error)}`,
        undefined,
        { error, executionId }
      )
    }
  }

  /**
   * Get execution status
   */
  async getStatus(executionId: string): Promise<ExecutionStatus> {
    try {
      const response = await this.apiClient.get<ExecutionStatus>(
        `/executions/${executionId}`
      )

      // Update local state
      this.executionStates.set(executionId, response.data)

      return response.data
    } catch (error) {
      throw createError(
        ErrorCode.EXECUTION_NOT_FOUND,
        `Failed to get execution status: ${error instanceof Error ? error.message : String(error)}`,
        undefined,
        { error, executionId }
      )
    }
  }

  /**
   * Get execution logs
   */
  async getLogs(executionId: string): Promise<ExecutionLog[]> {
    try {
      const response = await this.apiClient.get<{ logs: ExecutionLog[] }>(
        `/executions/${executionId}/logs`
      )

      return response.data.logs
    } catch (error) {
      throw createError(
        ErrorCode.EXECUTION_NOT_FOUND,
        `Failed to get execution logs: ${error instanceof Error ? error.message : String(error)}`,
        undefined,
        { error, executionId }
      )
    }
  }

  /**
   * Subscribe to status changes
   */
  onStatusChange(handler: ExecutionStatusHandler): () => void {
    this.statusHandlers.add(handler)

    // Return unsubscribe function
    return () => {
      this.statusHandlers.delete(handler)
    }
  }

  /**
   * Subscribe to log events
   */
  onLogReceived(handler: ExecutionLogHandler): () => void {
    this.logHandlers.add(handler)

    // Return unsubscribe function
    return () => {
      this.logHandlers.delete(handler)
    }
  }

  /**
   * Setup WebSocket listeners for real-time updates
   */
  private setupWebSocketListeners(): void {
    // Listen for status updates
    this.wsService.subscribe('status', (message) => {
      const payload = message.payload as any
      const executionId = payload.executionId

      if (executionId) {
        const status = this.executionStates.get(executionId)
        if (status) {
          status.status = payload.status as ExecutionState
          status.progress = payload.progress ?? status.progress
          status.currentNode = payload.currentNode

          this.notifyStatusHandlers(status)
        }
      }
    })

    // Listen for log messages
    this.wsService.subscribe('log', (message) => {
      const log = message.payload as ExecutionLog

      const executionId = message.executionId
      if (executionId) {
        const status = this.executionStates.get(executionId)
        if (status) {
          status.logs.push(log)
        }
      }

      this.notifyLogHandlers(log)
    })

    // Listen for node updates
    this.wsService.subscribe('node-update', (message) => {
      const payload = message.payload as any
      const executionId = payload.executionId

      if (executionId) {
        const status = this.executionStates.get(executionId)
        if (status) {
          status.nodeStates[payload.nodeId] = {
            nodeId: payload.nodeId,
            state: payload.state as NodeState,
            progress: payload.progress,
            error: payload.error,
            startTime: payload.startTime,
            endTime: payload.endTime,
          }

          this.notifyStatusHandlers(status)
        }
      }
    })

    // Listen for progress updates
    this.wsService.subscribe('progress', (message) => {
      const payload = message.payload as any
      const executionId = payload.executionId

      if (executionId) {
        const status = this.executionStates.get(executionId)
        if (status) {
          status.progress = payload.progress ?? status.progress

          this.notifyStatusHandlers(status)
        }
      }
    })
  }

  /**
   * Notify all status handlers
   */
  private notifyStatusHandlers(status: ExecutionStatus): void {
    this.statusHandlers.forEach((handler) => {
      try {
        handler(status)
      } catch (error) {
        console.error('Error in status handler:', error)
      }
    })
  }

  /**
   * Notify all log handlers
   */
  private notifyLogHandlers(log: ExecutionLog): void {
    this.logHandlers.forEach((handler) => {
      try {
        handler(log)
      } catch (error) {
        console.error('Error in log handler:', error)
      }
    })
  }

  /**
   * Clean up execution resources
   */
  private cleanupExecution(executionId: string): void {
    // Remove WebSocket unsubscriber if exists
    const unsubscriber = this.wsUnsubscribers.get(executionId)
    if (unsubscriber) {
      unsubscriber()
      this.wsUnsubscribers.delete(executionId)
    }

    // Keep execution state for history
    // Don't delete from executionStates
  }

  /**
   * Clear all execution states
   */
  clearExecutionStates(): void {
    this.executionStates.clear()
    this.wsUnsubscribers.forEach((unsubscriber) => unsubscriber())
    this.wsUnsubscribers.clear()
  }

  /**
   * Get execution state
   */
  getExecutionState(executionId: string): ExecutionStatus | undefined {
    return this.executionStates.get(executionId)
  }
}

/**
 * Create a singleton instance of ExecutionService
 */
let executionServiceInstance: ExecutionService | null = null

export function createExecutionService(
  apiClient: APIClient,
  wsService: WebSocketService
): ExecutionService {
  executionServiceInstance = new ExecutionService(apiClient, wsService)
  return executionServiceInstance
}

export function getExecutionService(): ExecutionService {
  if (!executionServiceInstance) {
    throw new Error('ExecutionService not initialized. Call createExecutionService first.')
  }
  return executionServiceInstance
}
