/**
 * WebSocket Service for real-time communication
 * Handles connection, reconnection, message subscription and distribution
 */

import type { WebSocketMessage, MessageHandler } from '../../types/events'
import { createError, ErrorCode } from '../../types/errors'

export interface WebSocketConfig {
  url: string
  reconnectAttempts?: number
  reconnectInterval?: number
  heartbeatInterval?: number
}

type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'reconnecting'

const DEFAULT_RECONNECT_ATTEMPTS = 5
const DEFAULT_RECONNECT_INTERVAL = 3000
const DEFAULT_HEARTBEAT_INTERVAL = 30000

/**
 * WebSocketService class for handling real-time communication
 */
export class WebSocketService {
  private url: string
  private reconnectAttempts: number
  private reconnectInterval: number
  private heartbeatInterval: number
  private ws: WebSocket | null = null
  private connectionState: ConnectionState = 'disconnected'
  private reconnectCount = 0
  private messageHandlers: Map<string, Set<MessageHandler>> = new Map()
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null

  constructor(config: WebSocketConfig) {
    this.url = config.url
    this.reconnectAttempts = config.reconnectAttempts ?? DEFAULT_RECONNECT_ATTEMPTS
    this.reconnectInterval = config.reconnectInterval ?? DEFAULT_RECONNECT_INTERVAL
    this.heartbeatInterval = config.heartbeatInterval ?? DEFAULT_HEARTBEAT_INTERVAL
  }

  /**
   * Connect to WebSocket server
   */
  async connect(): Promise<void> {
    if (this.connectionState === 'connected' || this.connectionState === 'connecting') {
      return
    }

    this.connectionState = 'connecting'

    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url)

        this.ws.onopen = () => {
          this.connectionState = 'connected'
          this.reconnectCount = 0
          this.startHeartbeat()
          this.notifyHandlers('connection', {
            type: 'connection',
            payload: { status: 'connected', message: 'Connected to server' },
            timestamp: Date.now(),
          })
          resolve()
        }

        this.ws.onmessage = (event) => {
          this.handleMessage(event.data)
        }

        this.ws.onerror = (event) => {
          const error = createError(
            ErrorCode.WEBSOCKET_CONNECTION_FAILED,
            'WebSocket connection error',
            undefined,
            { event }
          )
          reject(error)
        }

        this.ws.onclose = () => {
          this.connectionState = 'disconnected'
          this.stopHeartbeat()
          this.notifyHandlers('connection', {
            type: 'connection',
            payload: { status: 'disconnected', message: 'Disconnected from server' },
            timestamp: Date.now(),
          })
          this.attemptReconnect()
        }
      } catch (error) {
        this.connectionState = 'disconnected'
        reject(
          createError(
            ErrorCode.WEBSOCKET_CONNECTION_FAILED,
            `Failed to create WebSocket: ${error instanceof Error ? error.message : String(error)}`,
            undefined,
            { error }
          )
        )
      }
    })
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.stopHeartbeat()
    this.clearReconnectTimer()

    if (this.ws) {
      this.ws.close()
      this.ws = null
    }

    this.connectionState = 'disconnected'
  }

  /**
   * Subscribe to messages of a specific type
   */
  subscribe(type: string, handler: MessageHandler): () => void {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, new Set())
    }

    const handlers = this.messageHandlers.get(type)!
    handlers.add(handler)

    // Return unsubscribe function
    return () => {
      handlers.delete(handler)
      if (handlers.size === 0) {
        this.messageHandlers.delete(type)
      }
    }
  }

  /**
   * Send a message to the server
   */
  send(message: WebSocketMessage): void {
    if (this.connectionState !== 'connected' || !this.ws) {
      throw createError(
        ErrorCode.WEBSOCKET_DISCONNECTED,
        'WebSocket is not connected',
        undefined,
        { connectionState: this.connectionState }
      )
    }

    try {
      this.ws.send(JSON.stringify(message))
    } catch (error) {
      throw createError(
        ErrorCode.WEBSOCKET_MESSAGE_ERROR,
        `Failed to send message: ${error instanceof Error ? error.message : String(error)}`,
        undefined,
        { error, message }
      )
    }
  }

  /**
   * Get current connection state
   */
  get isConnected(): boolean {
    return this.connectionState === 'connected'
  }

  /**
   * Get connection state
   */
  get state(): ConnectionState {
    return this.connectionState
  }

  /**
   * Handle incoming message
   */
  private handleMessage(data: string): void {
    try {
      const message = JSON.parse(data) as WebSocketMessage

      // Validate message structure
      if (!message.type || !message.payload) {
        throw new Error('Invalid message structure')
      }

      // Distribute to handlers
      this.notifyHandlers(message.type, message)
    } catch (error) {
      const wsError = createError(
        ErrorCode.WEBSOCKET_MESSAGE_ERROR,
        `Failed to parse message: ${error instanceof Error ? error.message : String(error)}`,
        undefined,
        { error, data }
      )

      // Notify error handlers
      this.notifyHandlers('error', {
        type: 'error',
        payload: {
          code: wsError.code,
          message: wsError.message,
          details: wsError.details,
        },
        timestamp: Date.now(),
      })
    }
  }

  /**
   * Notify all handlers for a message type
   */
  private notifyHandlers(type: string, message: WebSocketMessage): void {
    const handlers = this.messageHandlers.get(type)
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          handler(message)
        } catch (error) {
          console.error(`Error in message handler for type ${type}:`, error)
        }
      })
    }
  }

  /**
   * Attempt to reconnect
   */
  private attemptReconnect(): void {
    if (this.reconnectCount >= this.reconnectAttempts) {
      const error = createError(
        ErrorCode.WEBSOCKET_DISCONNECTED,
        `Failed to reconnect after ${this.reconnectAttempts} attempts`,
        undefined,
        { reconnectCount: this.reconnectCount, maxAttempts: this.reconnectAttempts }
      )

      this.notifyHandlers('error', {
        type: 'error',
        payload: {
          code: error.code,
          message: error.message,
          details: error.details,
        },
        timestamp: Date.now(),
      })

      return
    }

    this.reconnectCount++
    this.connectionState = 'reconnecting'

    this.notifyHandlers('connection', {
      type: 'connection',
      payload: {
        status: 'reconnecting',
        message: `Attempting to reconnect (${this.reconnectCount}/${this.reconnectAttempts})`,
      },
      timestamp: Date.now(),
    })

    this.reconnectTimer = setTimeout(() => {
      this.connect().catch((error) => {
        console.error('Reconnection failed:', error)
      })
    }, this.reconnectInterval)
  }

  /**
   * Start heartbeat to keep connection alive
   */
  private startHeartbeat(): void {
    this.stopHeartbeat()

    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected && this.ws) {
        try {
          this.ws.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }))
        } catch (error) {
          console.error('Failed to send heartbeat:', error)
        }
      }
    }, this.heartbeatInterval)
  }

  /**
   * Stop heartbeat
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  /**
   * Clear reconnect timer
   */
  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
  }
}

/**
 * Create a singleton instance of WebSocketService
 */
let wsServiceInstance: WebSocketService | null = null

export function createWebSocketService(config: WebSocketConfig): WebSocketService {
  wsServiceInstance = new WebSocketService(config)
  return wsServiceInstance
}

export function getWebSocketService(): WebSocketService {
  if (!wsServiceInstance) {
    throw new Error('WebSocketService not initialized. Call createWebSocketService first.')
  }
  return wsServiceInstance
}
