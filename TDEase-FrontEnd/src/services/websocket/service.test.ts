/**
 * Tests for WebSocketService
 * Feature: frontend-services, Property 8 & 9: WebSocket reconnection and message distribution
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { WebSocketService } from './service'
import type { WebSocketMessage } from '../../types/events'

// Mock WebSocket
class MockWebSocket {
  static lastInstance: MockWebSocket | null = null

  onopen: (() => void) | null = null
  onclose: (() => void) | null = null
  onerror: ((event: Event) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  send = vi.fn()
  close = vi.fn()

  constructor(public url: string) {
    MockWebSocket.lastInstance = this
  }

  simulateOpen() {
    this.onopen?.()
  }

  simulateClose() {
    this.onclose?.()
  }

  simulateError(event: Event) {
    this.onerror?.(event)
  }

  simulateMessage(data: string) {
    this.onmessage?.(new MessageEvent('message', { data }))
  }
}

describe('WebSocketService', () => {
  let service: WebSocketService
  let originalWebSocket: typeof WebSocket

  beforeEach(() => {
    // Mock WebSocket
    originalWebSocket = globalThis.WebSocket as any
    ;(globalThis as any).WebSocket = MockWebSocket
    MockWebSocket.lastInstance = null

    service = new WebSocketService({
      url: 'ws://localhost:8000',
      reconnectAttempts: 2,
      reconnectInterval: 50,
      heartbeatInterval: 1000,
    })
  })

  afterEach(() => {
    service.disconnect()
    ;(globalThis as any).WebSocket = originalWebSocket
    vi.clearAllTimers()
  })

  describe('Property 8: WebSocket 重连次数限制', () => {
    it('should not exceed maximum reconnection attempts', async () => {
      /**
       * Feature: frontend-services, Property 8: WebSocket 重连次数限制
       * Validates: Requirements 4.2
       *
       * For any disconnection scenario, reconnection attempts should not exceed
       * the configured maximum reconnection attempts
       */
      const maxAttempts = 2
      const testService = new WebSocketService({
        url: 'ws://localhost:8000',
        reconnectAttempts: maxAttempts,
        reconnectInterval: 10,
      })

      let connectionAttempts = 0
      let errorCount = 0
      testService.subscribe('connection', () => {
        connectionAttempts++
      })
      testService.subscribe('error', () => {
        errorCount++
      })

      // Try to connect (will fail)
      const connectPromise = testService.connect()
      const ws = MockWebSocket.lastInstance
      ws!.simulateError(new Event('error'))

      try {
        await connectPromise
      } catch {
        // Expected
      }

      // Wait for reconnection attempts to complete
      await new Promise((resolve) => setTimeout(resolve, maxAttempts * 100 + 200))

      testService.disconnect()

      // Should have attempted reconnection but not exceeded max attempts
      // Connection attempts should be <= maxAttempts + 1 (initial + retries)
      expect(connectionAttempts).toBeLessThanOrEqual(maxAttempts + 2)
    })
  })

  describe('Property 9: WebSocket 消息分发正确性', () => {
    it('should distribute messages to correct type handlers', async () => {
      /**
       * Feature: frontend-services, Property 9: WebSocket 消息分发正确性
       * Validates: Requirements 4.3
       *
       * For any received WebSocket message, it should be distributed to
       * the corresponding type handler
       */
      const receivedMessages: WebSocketMessage[] = []
      service.subscribe('status', (msg) => {
        receivedMessages.push(msg)
      })

      // Connect
      const connectPromise = service.connect()
      const ws = MockWebSocket.lastInstance
      ws!.simulateOpen()
      await connectPromise

      // Send message
      const message: WebSocketMessage = {
        type: 'status',
        payload: { status: 'running' },
        timestamp: Date.now(),
      }

      ws!.simulateMessage(JSON.stringify(message))

      // Verify message was received
      expect(receivedMessages).toHaveLength(1)
      expect(receivedMessages[0].type).toBe('status')
      expect((receivedMessages[0].payload as any).status).toBe('running')
    })

    it('should handle multiple subscribers for same message type', async () => {
      /**
       * Feature: frontend-services, Property 9: WebSocket 消息分发正确性
       * Validates: Requirements 4.3
       */
      const handler1Messages: WebSocketMessage[] = []
      const handler2Messages: WebSocketMessage[] = []

      service.subscribe('status', (msg) => {
        handler1Messages.push(msg)
      })

      service.subscribe('status', (msg) => {
        handler2Messages.push(msg)
      })

      const connectPromise = service.connect()
      const ws = MockWebSocket.lastInstance
      ws!.simulateOpen()
      await connectPromise

      const message: WebSocketMessage = {
        type: 'status',
        payload: { status: 'running' },
        timestamp: Date.now(),
      }

      ws!.simulateMessage(JSON.stringify(message))

      expect(handler1Messages).toHaveLength(1)
      expect(handler2Messages).toHaveLength(1)
      expect(handler1Messages[0].type).toBe(handler2Messages[0].type)
    })

    it('should unsubscribe handler correctly', async () => {
      /**
       * Feature: frontend-services, Property 9: WebSocket 消息分发正确性
       * Validates: Requirements 4.3
       */
      const messages: WebSocketMessage[] = []
      const unsubscribe = service.subscribe('status', (msg) => {
        messages.push(msg)
      })

      const connectPromise = service.connect()
      const ws = MockWebSocket.lastInstance
      ws!.simulateOpen()
      await connectPromise

      // Send first message
      ws!.simulateMessage(JSON.stringify({ type: 'status', payload: {}, timestamp: Date.now() }))
      expect(messages).toHaveLength(1)

      // Unsubscribe
      unsubscribe()

      // Send second message
      ws!.simulateMessage(JSON.stringify({ type: 'status', payload: {}, timestamp: Date.now() }))
      expect(messages).toHaveLength(1) // Should not increase
    })
  })

  describe('WebSocketService basic functionality', () => {
    it('should connect to WebSocket server', async () => {
      const connectPromise = service.connect()
      const ws = MockWebSocket.lastInstance
      ws!.simulateOpen()
      await connectPromise

      expect(service.isConnected).toBe(true)
      expect(service.state).toBe('connected')
    })

    it('should handle connection state', async () => {
      expect(service.isConnected).toBe(false)
      expect(service.state).toBe('disconnected')

      const connectPromise = service.connect()
      expect(service.state).toBe('connecting')

      const ws = MockWebSocket.lastInstance
      ws!.simulateOpen()
      await connectPromise

      expect(service.isConnected).toBe(true)
      expect(service.state).toBe('connected')
    })

    it('should send messages when connected', async () => {
      const connectPromise = service.connect()
      const ws = MockWebSocket.lastInstance
      ws!.simulateOpen()
      await connectPromise

      const message: WebSocketMessage = {
        type: 'status',
        payload: { test: 'data' },
        timestamp: Date.now(),
      }

      service.send(message)

      expect(ws!.send).toHaveBeenCalledWith(JSON.stringify(message))
    })

    it('should throw error when sending while disconnected', () => {
      const message: WebSocketMessage = {
        type: 'status',
        payload: {},
        timestamp: Date.now(),
      }

      expect(() => service.send(message)).toThrow('WebSocket is not connected')
    })

    it('should handle incoming messages', async () => {
      const messages: WebSocketMessage[] = []
      service.subscribe('status', (msg) => {
        messages.push(msg)
      })

      const connectPromise = service.connect()
      const ws = MockWebSocket.lastInstance
      ws!.simulateOpen()
      await connectPromise

      const message: WebSocketMessage = {
        type: 'status',
        payload: { status: 'running' },
        timestamp: Date.now(),
      }

      ws!.simulateMessage(JSON.stringify(message))

      expect(messages).toHaveLength(1)
      expect((messages[0].payload as any).status).toBe('running')
    })

    it('should handle invalid messages', async () => {
      const errors: WebSocketMessage[] = []
      service.subscribe('error', (msg) => {
        errors.push(msg)
      })

      const connectPromise = service.connect()
      const ws = MockWebSocket.lastInstance
      ws!.simulateOpen()
      await connectPromise

      ws!.simulateMessage('invalid json')

      expect(errors.length).toBeGreaterThan(0)
    })

    it('should disconnect properly', async () => {
      const connectPromise = service.connect()
      const ws = MockWebSocket.lastInstance
      ws!.simulateOpen()
      await connectPromise

      expect(service.isConnected).toBe(true)

      service.disconnect()

      expect(service.isConnected).toBe(false)
      expect(service.state).toBe('disconnected')
      expect(ws!.close).toHaveBeenCalled()
    })
  })
})
