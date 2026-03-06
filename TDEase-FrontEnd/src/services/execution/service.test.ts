/**
 * Tests for ExecutionService
 * Feature: frontend-services, Property 7: Execution state transitions
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { ExecutionService } from './service'
import type { ExecutionStatus } from '../../types/api'

// Mock APIClient
class MockAPIClient {
  post = vi.fn().mockResolvedValue({ data: { executionId: 'exec_123' } })
  get = vi.fn().mockResolvedValue({ data: {} })
  put = vi.fn().mockResolvedValue({ data: {} })
  delete = vi.fn().mockResolvedValue({ data: {} })
}

// Mock WebSocketService
class MockWebSocketService {
  subscribe = vi.fn().mockReturnValue(() => {})
}

describe('ExecutionService', () => {
  let service: ExecutionService
  let mockApiClient: MockAPIClient
  let mockWsService: MockWebSocketService

  beforeEach(() => {
    mockApiClient = new MockAPIClient()
    mockWsService = new MockWebSocketService()
    service = new ExecutionService(mockApiClient as any, mockWsService as any)
  })

  describe('Property 7: 执行状态转换有效性', () => {
    it('should transition to paused state correctly', async () => {
      /**
       * Feature: frontend-services, Property 7: 执行状态转换有效性
       * Validates: Requirements 3.3
       *
       * For any execution state, after pause operation, state should become paused
       */
      // Start execution
      const executionId = await service.start({
        workflowId: 'workflow_123',
      })

      // Verify initial state
      let status = service.getExecutionState(executionId)
      expect(status?.status).toBe('running')

      // Pause execution
      await service.pause(executionId)

      // Verify paused state
      status = service.getExecutionState(executionId)
      expect(status?.status).toBe('paused')
    })

    it('should transition to running state after resume', async () => {
      /**
       * Feature: frontend-services, Property 7: 执行状态转换有效性
       * Validates: Requirements 3.4
       *
       * For any paused execution, after resume operation, state should become running
       */
      // Start execution
      const executionId = await service.start({
        workflowId: 'workflow_123',
      })

      // Pause execution
      await service.pause(executionId)
      let status = service.getExecutionState(executionId)
      expect(status?.status).toBe('paused')

      // Resume execution
      await service.resume(executionId)

      // Verify running state
      status = service.getExecutionState(executionId)
      expect(status?.status).toBe('running')
    })

    it('should transition to cancelled state', async () => {
      /**
       * Feature: frontend-services, Property 7: 执行状态转换有效性
       * Validates: Requirements 3.5
       */
      // Start execution
      const executionId = await service.start({
        workflowId: 'workflow_123',
      })

      // Cancel execution
      await service.cancel(executionId)

      // Verify cancelled state
      const status = service.getExecutionState(executionId)
      expect(status?.status).toBe('cancelled')
    })
  })

  describe('ExecutionService basic functionality', () => {
    it('should start execution', async () => {
      const executionId = await service.start({
        workflowId: 'workflow_123',
      })

      expect(executionId).toBe('exec_123')
      expect(mockApiClient.post).toHaveBeenCalledWith('/executions', {
        workflowId: 'workflow_123',
      })
    })

    it('should initialize execution state on start', async () => {
      const executionId = await service.start({
        workflowId: 'workflow_123',
      })

      const status = service.getExecutionState(executionId)

      expect(status).toBeDefined()
      expect(status?.executionId).toBe(executionId)
      expect(status?.status).toBe('running')
      expect(status?.progress).toBe(0)
      expect(status?.logs).toEqual([])
    })

    it('should pause execution', async () => {
      const executionId = await service.start({
        workflowId: 'workflow_123',
      })

      await service.pause(executionId)

      expect(mockApiClient.post).toHaveBeenCalledWith(`/executions/${executionId}/pause`, {})
    })

    it('should resume execution', async () => {
      const executionId = await service.start({
        workflowId: 'workflow_123',
      })

      await service.resume(executionId)

      expect(mockApiClient.post).toHaveBeenCalledWith(`/executions/${executionId}/resume`, {})
    })

    it('should cancel execution', async () => {
      const executionId = await service.start({
        workflowId: 'workflow_123',
      })

      await service.cancel(executionId)

      expect(mockApiClient.post).toHaveBeenCalledWith(`/executions/${executionId}/cancel`, {})
    })

    it('should get execution status', async () => {
      const mockStatus: ExecutionStatus = {
        executionId: 'exec_123',
        status: 'running',
        progress: 50,
        nodeStates: {},
        logs: [],
        startTime: Date.now(),
      }

      mockApiClient.get.mockResolvedValueOnce({ data: mockStatus })

      const status = await service.getStatus('exec_123')

      expect(status).toEqual(mockStatus)
      expect(mockApiClient.get).toHaveBeenCalledWith('/executions/exec_123')
    })

    it('should get execution logs', async () => {
      const mockLogs = [
        {
          timestamp: Date.now(),
          level: 'info' as const,
          message: 'Execution started',
        },
      ]

      mockApiClient.get.mockResolvedValueOnce({ data: { logs: mockLogs } })

      const logs = await service.getLogs('exec_123')

      expect(logs).toEqual(mockLogs)
      expect(mockApiClient.get).toHaveBeenCalledWith('/executions/exec_123/logs')
    })

    it('should subscribe to status changes', async () => {
      const executionId = await service.start({
        workflowId: 'workflow_123',
      })

      const statusChanges: ExecutionStatus[] = []
      const unsubscribe = service.onStatusChange((status) => {
        statusChanges.push(status)
      })

      // Pause to trigger status change
      await service.pause(executionId)

      expect(statusChanges.length).toBeGreaterThan(0)
      expect(statusChanges[0].status).toBe('paused')

      // Unsubscribe
      unsubscribe()
    })

    it('should subscribe to log events', async () => {
      const logs: any[] = []
      service.onLogReceived((log) => {
        logs.push(log)
      })

      // Simulate WebSocket log message
      const subscribeCall = mockWsService.subscribe.mock.calls.find(
        (call) => call[0] === 'log'
      )
      expect(subscribeCall).toBeDefined()
    })

    it('should clear execution states', async () => {
      await service.start({
        workflowId: 'workflow_123',
      })

      service.clearExecutionStates()

      // After clearing, should not have any execution states
      expect(service.getExecutionState('exec_123')).toBeUndefined()
    })

    it('should handle execution errors', async () => {
      mockApiClient.post.mockRejectedValueOnce(new Error('API Error'))

      await expect(
        service.start({
          workflowId: 'workflow_123',
        })
      ).rejects.toThrow('Failed to start execution')
    })
  })
})
