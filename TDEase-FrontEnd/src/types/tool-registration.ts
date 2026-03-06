/**
 * Tool registration system foundation (Section 9)
 *
 * 9.1 Extensible backend tool registration interface
 * 9.2 Dynamic node type loading
 * 9.3 Tool metadata management
 * 9.4 Configuration UI system for complex tools
 * 9.5 Plugin architecture for community tools
 */

import type { Component } from 'vue'

/** 9.1 Backend tool registration: minimal contract for a registered tool */
export interface IBackendToolRegistration {
  id: string
  name: string
  version?: string
  description?: string
  /** Tool schema from backend (inputs, outputs, parameters) */
  schema: Record<string, unknown>
  /** Optional: execution mode (native, script, docker, interactive) */
  executionMode?: string
}

/** 9.1 Interface that a backend tool registry adapter must implement */
export interface IToolRegistryAdapter {
  listTools(): Promise<IBackendToolRegistration[]>
  getTool(id: string): Promise<IBackendToolRegistration | null>
  refresh?(): Promise<void>
}

/** 9.2 Dynamic node type: mapping from tool/type id to Vue Flow node component */
export interface NodeTypeRegistration {
  type: string
  label: string
  component: Component
  /** Optional: default ports/layout for palette */
  defaultInputs?: Array<{ id: string; name: string; type: string }>
  defaultOutputs?: Array<{ id: string; name: string; type: string }>
}

/** 9.2 Node type loader: resolve node type to component (for dynamic loading) */
export interface INodeTypeLoader {
  getNodeType(typeId: string): NodeTypeRegistration | undefined
  register(reg: NodeTypeRegistration): void
  loadFromBackend?(): Promise<void>
}

/** 9.3 Tool metadata (extended beyond schema for UI and discovery) */
export interface ToolMetadata {
  id: string
  name: string
  version?: string
  description?: string
  author?: string
  tags?: string[]
  category?: string
  icon?: string
  schema: Record<string, unknown>
  /** UI hints for property panel */
  uiHints?: {
    group?: string
    order?: number
    advanced?: boolean
  }
}

/** 9.3 Tool metadata manager interface */
export interface IToolMetadataManager {
  getMetadata(toolId: string): ToolMetadata | undefined
  setMetadata(toolId: string, meta: Partial<ToolMetadata>): void
  listByCategory?(category: string): ToolMetadata[]
}

/** 9.4 Configuration UI: descriptor for complex tool parameter UI */
export interface ToolConfigUISection {
  id: string
  label: string
  fields: string[]
  collapsible?: boolean
  defaultOpen?: boolean
}

export interface ToolConfigUIDescriptor {
  toolId: string
  sections: ToolConfigUISection[]
  /** Custom component for full custom UI (optional) */
  customComponent?: Component
}

/** 9.4 Configuration UI registry */
export interface IConfigUIRegistry {
  getDescriptor(toolId: string): ToolConfigUIDescriptor | undefined
  register(descriptor: ToolConfigUIDescriptor): void
}

/** 9.5 Community plugin contract (foundation for future plugin system) */
export interface IWorkflowEditorPlugin {
  id: string
  name: string
  version: string
  /** Called when editor loads; can register node types, tools, visualizations */
  install(context: PluginContext): void | Promise<void>
  /** Optional: cleanup on unload */
  uninstall?(context: PluginContext): void
}

export interface PluginContext {
  registerNodeType(reg: NodeTypeRegistration): void
  registerTool?(registration: IBackendToolRegistration): void
  registerVisualization?(type: string, component: Component, options?: Record<string, unknown>): void
}
