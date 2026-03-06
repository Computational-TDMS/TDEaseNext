/**
 * Core workflow data types and interfaces
 * Defines the structure of WorkflowJSON and related types
 */

import type { SemanticType } from './state-ports'

// Data type definitions
export type DataType = 'file' | 'table' | 'json' | 'number' | 'string' | 'boolean' | 'any'

// Execution state definitions
export type ExecutionState = 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled'

// Node state definitions
export type NodeState = 'idle' | 'waiting' | 'running' | 'completed' | 'failed' | 'skipped'

// Position interface for node placement
export interface Position {
  x: number
  y: number
}

export type PortKind = 'data' | 'state-in' | 'state-out'

// Display properties for UI rendering
export interface DisplayProperties {
  label?: string
  color?: string
  icon?: string
  width?: number
  height?: number
}

// Port definition for node inputs/outputs
export interface PortDefinition {
  id: string
  name: string
  dataType: DataType
  required: boolean
  description?: string
  portKind?: PortKind
  semanticType?: SemanticType | string
}

// Parameter definition for node configuration
export interface ParameterDefinition {
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
  default?: unknown
  description?: string
  options?: Array<{ label: string; value: unknown }>
}

// Node core configuration
export interface NodeCoreConfig {
  [key: string]: unknown
}

// Node definition
export interface NodeDefinition {
  id: string
  type: string
  position: Position
  data?: Record<string, unknown>
  displayProperties: DisplayProperties
  inputs: PortDefinition[]
  outputs: PortDefinition[]
  parameters?: ParameterDefinition[]
  nodeConfig: NodeCoreConfig
}

// Connection definition
export interface ConnectionDefinition {
  id: string
  source: {
    nodeId: string
    portId: string
  }
  connectionKind?: 'data' | 'state'
  semanticType?: SemanticType | string
  target: {
    nodeId: string
    portId: string
  }
  dataPath?: {
    s?: string
    t?: string
  }
}

// Project settings
export interface ProjectSettings {
  [key: string]: unknown
}

// Workflow metadata
export interface WorkflowMetadata {
  id: string
  name: string
  version: string
  description?: string
  author?: string
  created: string
  modified: string
  tags?: string[]
  uuid?: string
  license?: string
  creator?: Array<Record<string, unknown>>
}

// Galaxy format step definitions
export interface WorkflowStep {
  id: string
  type: string
  tool_id?: string
  tool_state?: Record<string, unknown>
  inputs?: Record<string, unknown>
  outputs?: Record<string, string>
  position?: { x: number; y: number }
}

export interface WorkflowInput {
  id: string
  type: string
  label?: string
}

export interface WorkflowOutput {
  id: string
  outputSource: string
  label?: string
}

// Main WorkflowJSON interface
export interface WorkflowJSON {
  metadata: WorkflowMetadata
  format_version?: string
  nodes: NodeDefinition[]
  connections: ConnectionDefinition[]
  steps?: Record<string, WorkflowStep>
  inputs?: Record<string, WorkflowInput>
  outputs?: Record<string, WorkflowOutput>
  projectSettings: ProjectSettings
}

// Batch processing types
export interface BatchSample {
  sample_id: string
  placeholder_values: Record<string, unknown>
}

export interface BatchConfig {
  samples: BatchSample[]
  global_params?: Record<string, unknown>
}

// Workflow summary for list views
export interface WorkflowSummary {
  id: string
  name: string
  description?: string
  created: string
  modified: string
}

// Execution log entry
export interface ExecutionLog {
  timestamp: number
  level: 'info' | 'warning' | 'error' | 'debug'
  message: string
  nodeId?: string
  details?: unknown
}

// Node state tracking
export interface NodeStateInfo {
  nodeId: string
  state: NodeState
  progress?: number
  error?: string
  startTime?: number
  endTime?: number
}

// Column definition for table data
export interface ColumnDefinition {
  name: string
  type: 'string' | 'number' | 'boolean' | 'date'
  description?: string
}

// Table data structure
export interface TableData {
  columns: ColumnDefinition[]
  rows: Record<string, unknown>[]
  totalRows: number
}

// Data mapping for visualization
export interface DataMapping {
  xAxis?: string
  yAxis?: string
  series?: string
  [key: string]: unknown
}
