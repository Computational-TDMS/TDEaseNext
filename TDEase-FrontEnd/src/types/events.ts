/**
 * Event and message types
 * Defines WebSocket messages and application events
 */

import type { ExecutionState, NodeState, ExecutionLog } from './workflow'

// WebSocket message types
export type WebSocketMessageType = 'status' | 'log' | 'error' | 'progress' | 'node-update' | 'connection'

// WebSocket message interface
export interface WebSocketMessage {
  type: WebSocketMessageType
  payload: unknown
  timestamp: number
  executionId?: string
}

// Status update message
export interface StatusUpdateMessage extends WebSocketMessage {
  type: 'status'
  payload: {
    executionId: string
    status: ExecutionState
    progress: number
    currentNode?: string
  }
}

// Log message
export interface LogMessage extends WebSocketMessage {
  type: 'log'
  payload: ExecutionLog
}

// Error message
export interface ErrorMessage extends WebSocketMessage {
  type: 'error'
  payload: {
    code: string
    message: string
    details?: unknown
  }
}

// Progress message
export interface ProgressMessage extends WebSocketMessage {
  type: 'progress'
  payload: {
    executionId: string
    nodeId: string
    progress: number
    total: number
  }
}

// Node update message
export interface NodeUpdateMessage extends WebSocketMessage {
  type: 'node-update'
  payload: {
    executionId: string
    nodeId: string
    state: NodeState
    output?: unknown
    error?: string
  }
}

// Connection message
export interface ConnectionMessage extends WebSocketMessage {
  type: 'connection'
  payload: {
    status: 'connected' | 'disconnected' | 'reconnecting'
    message: string
  }
}

// Union type for all WebSocket messages
export type AnyWebSocketMessage =
  | StatusUpdateMessage
  | LogMessage
  | ErrorMessage
  | ProgressMessage
  | NodeUpdateMessage
  | ConnectionMessage

// Message handler type
export type MessageHandler = (message: WebSocketMessage) => void

// Event emitter types
export interface EventEmitterOptions {
  maxListeners?: number
}

// Application event types
export type AppEventType =
  | 'workflow:created'
  | 'workflow:loaded'
  | 'workflow:saved'
  | 'workflow:deleted'
  | 'workflow:modified'
  | 'node:added'
  | 'node:removed'
  | 'node:updated'
  | 'connection:added'
  | 'connection:removed'
  | 'execution:started'
  | 'execution:paused'
  | 'execution:resumed'
  | 'execution:cancelled'
  | 'execution:completed'
  | 'execution:failed'
  | 'error:occurred'

// Application event payload
export interface AppEvent {
  type: AppEventType
  payload: unknown
  timestamp: number
}

// Specific app event payloads
export interface WorkflowCreatedEvent extends AppEvent {
  type: 'workflow:created'
  payload: {
    workflowId: string
    name: string
  }
}

export interface WorkflowModifiedEvent extends AppEvent {
  type: 'workflow:modified'
  payload: {
    workflowId: string
    changes: unknown
  }
}

export interface ExecutionStartedEvent extends AppEvent {
  type: 'execution:started'
  payload: {
    executionId: string
    workflowId: string
  }
}

export interface ExecutionCompletedEvent extends AppEvent {
  type: 'execution:completed'
  payload: {
    executionId: string
    duration: number
    result?: unknown
  }
}

export interface ExecutionFailedEvent extends AppEvent {
  type: 'execution:failed'
  payload: {
    executionId: string
    error: string
    nodeId?: string
  }
}

export interface ErrorOccurredEvent extends AppEvent {
  type: 'error:occurred'
  payload: {
    code: string
    message: string
    details?: unknown
  }
}

// Union type for all app events
export type AnyAppEvent =
  | WorkflowCreatedEvent
  | WorkflowModifiedEvent
  | ExecutionStartedEvent
  | ExecutionCompletedEvent
  | ExecutionFailedEvent
  | ErrorOccurredEvent
  | AppEvent
