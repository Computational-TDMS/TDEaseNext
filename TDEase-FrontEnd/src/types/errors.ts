/**
 * Error types and definitions
 * Defines all error codes and custom error classes
 */

// Error code enumeration
export enum ErrorCode {
  // Network errors
  NETWORK_ERROR = 'NETWORK_ERROR',
  TIMEOUT_ERROR = 'TIMEOUT_ERROR',
  CONNECTION_REFUSED = 'CONNECTION_REFUSED',
  CONNECTION_RESET = 'CONNECTION_RESET',

  // API errors
  API_ERROR = 'API_ERROR',
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  NOT_FOUND = 'NOT_FOUND',
  UNAUTHORIZED = 'UNAUTHORIZED',
  FORBIDDEN = 'FORBIDDEN',
  CONFLICT = 'CONFLICT',
  RATE_LIMITED = 'RATE_LIMITED',

  // Workflow errors
  WORKFLOW_INVALID = 'WORKFLOW_INVALID',
  WORKFLOW_NOT_FOUND = 'WORKFLOW_NOT_FOUND',
  CONNECTION_INVALID = 'CONNECTION_INVALID',
  NODE_INVALID = 'NODE_INVALID',
  PORT_MISMATCH = 'PORT_MISMATCH',

  // Execution errors
  EXECUTION_FAILED = 'EXECUTION_FAILED',
  EXECUTION_NOT_FOUND = 'EXECUTION_NOT_FOUND',
  NODE_FAILED = 'NODE_FAILED',
  EXECUTION_TIMEOUT = 'EXECUTION_TIMEOUT',

  // File errors
  FILE_NOT_FOUND = 'FILE_NOT_FOUND',
  FILE_READ_ERROR = 'FILE_READ_ERROR',
  FILE_WRITE_ERROR = 'FILE_WRITE_ERROR',
  FILE_PERMISSION_DENIED = 'FILE_PERMISSION_DENIED',
  FILE_SIZE_EXCEEDED = 'FILE_SIZE_EXCEEDED',

  // WebSocket errors
  WEBSOCKET_CONNECTION_FAILED = 'WEBSOCKET_CONNECTION_FAILED',
  WEBSOCKET_DISCONNECTED = 'WEBSOCKET_DISCONNECTED',
  WEBSOCKET_MESSAGE_ERROR = 'WEBSOCKET_MESSAGE_ERROR',

  // Tauri errors
  TAURI_COMMAND_FAILED = 'TAURI_COMMAND_FAILED',
  TAURI_NOT_AVAILABLE = 'TAURI_NOT_AVAILABLE',

  // Generic errors
  UNKNOWN_ERROR = 'UNKNOWN_ERROR',
  INTERNAL_ERROR = 'INTERNAL_ERROR',
}

// Error severity levels
export enum ErrorSeverity {
  INFO = 'info',
  WARNING = 'warning',
  ERROR = 'error',
  CRITICAL = 'critical',
}

// Custom error class
export class TDEaseError extends Error {
  public readonly code: ErrorCode
  public readonly severity: ErrorSeverity
  public readonly details?: unknown
  public readonly timestamp: number

  constructor(
    code: ErrorCode,
    message: string,
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    details?: unknown
  ) {
    super(message)
    this.name = 'TDEaseError'
    this.code = code
    this.severity = severity
    this.details = details
    this.timestamp = Date.now()

    // Maintain proper prototype chain
    Object.setPrototypeOf(this, TDEaseError.prototype)
  }

  toJSON() {
    return {
      name: this.name,
      code: this.code,
      message: this.message,
      severity: this.severity,
      details: this.details,
      timestamp: this.timestamp,
    }
  }
}

// Network error class
export class NetworkError extends TDEaseError {
  constructor(message: string, details?: unknown) {
    super(ErrorCode.NETWORK_ERROR, message, ErrorSeverity.ERROR, details)
    this.name = 'NetworkError'
    Object.setPrototypeOf(this, NetworkError.prototype)
  }
}

// Timeout error class
export class TimeoutError extends TDEaseError {
  constructor(message: string, details?: unknown) {
    super(ErrorCode.TIMEOUT_ERROR, message, ErrorSeverity.ERROR, details)
    this.name = 'TimeoutError'
    Object.setPrototypeOf(this, TimeoutError.prototype)
  }
}

// Validation error class
export class ValidationError extends TDEaseError {
  constructor(message: string, details?: unknown) {
    super(ErrorCode.VALIDATION_ERROR, message, ErrorSeverity.WARNING, details)
    this.name = 'ValidationError'
    Object.setPrototypeOf(this, ValidationError.prototype)
  }
}

// Workflow error class
export class WorkflowError extends TDEaseError {
  constructor(code: ErrorCode, message: string, details?: unknown) {
    super(code, message, ErrorSeverity.ERROR, details)
    this.name = 'WorkflowError'
    Object.setPrototypeOf(this, WorkflowError.prototype)
  }
}

// Execution error class
export class ExecutionError extends TDEaseError {
  constructor(code: ErrorCode, message: string, details?: unknown) {
    super(code, message, ErrorSeverity.ERROR, details)
    this.name = 'ExecutionError'
    Object.setPrototypeOf(this, ExecutionError.prototype)
  }
}

// File error class
export class FileError extends TDEaseError {
  constructor(code: ErrorCode, message: string, details?: unknown) {
    super(code, message, ErrorSeverity.ERROR, details)
    this.name = 'FileError'
    Object.setPrototypeOf(this, FileError.prototype)
  }
}

// Error factory function
export function createError(
  code: ErrorCode,
  message: string,
  severity?: ErrorSeverity,
  details?: unknown
): TDEaseError {
  // Route to specific error classes based on code
  if (code === ErrorCode.NETWORK_ERROR || code === ErrorCode.CONNECTION_REFUSED || code === ErrorCode.CONNECTION_RESET) {
    return new NetworkError(message, details)
  }

  if (code === ErrorCode.TIMEOUT_ERROR || code === ErrorCode.EXECUTION_TIMEOUT) {
    return new TimeoutError(message, details)
  }

  if (code === ErrorCode.VALIDATION_ERROR) {
    return new ValidationError(message, details)
  }

  if (
    code === ErrorCode.WORKFLOW_INVALID ||
    code === ErrorCode.WORKFLOW_NOT_FOUND ||
    code === ErrorCode.CONNECTION_INVALID ||
    code === ErrorCode.NODE_INVALID ||
    code === ErrorCode.PORT_MISMATCH
  ) {
    return new WorkflowError(code, message, details)
  }

  if (
    code === ErrorCode.EXECUTION_FAILED ||
    code === ErrorCode.EXECUTION_NOT_FOUND ||
    code === ErrorCode.NODE_FAILED
  ) {
    return new ExecutionError(code, message, details)
  }

  if (
    code === ErrorCode.FILE_NOT_FOUND ||
    code === ErrorCode.FILE_READ_ERROR ||
    code === ErrorCode.FILE_WRITE_ERROR ||
    code === ErrorCode.FILE_PERMISSION_DENIED ||
    code === ErrorCode.FILE_SIZE_EXCEEDED
  ) {
    return new FileError(code, message, details)
  }

  return new TDEaseError(code, message, severity, details)
}

// Error handler type
export type ErrorHandler = (error: TDEaseError) => void

// Error context for debugging
export interface ErrorContext {
  operation: string
  timestamp: number
  userId?: string
  workflowId?: string
  executionId?: string
  [key: string]: unknown
}
