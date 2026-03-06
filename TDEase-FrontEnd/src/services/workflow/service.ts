/**
 * Workflow Service for managing workflow lifecycle
 * Handles CRUD operations, node management, and connection validation
 */

import type {
  WorkflowJSON,
  NodeDefinition,
  ConnectionDefinition,
  WorkflowSummary,
} from '../../types/workflow'
import type { APIClient } from '../api/client'
import { createError, ErrorCode } from '../../types/errors'

/**
 * WorkflowService class for managing workflows
 */
export class WorkflowService {
  constructor(private apiClient: APIClient) {}

  /**
   * Create a new workflow
   */
  async create(name: string, description?: string): Promise<WorkflowJSON> {
    try {
      const response = await this.apiClient.post<WorkflowJSON>('/workflows', {
        name,
        description,
      })

      return response.data
    } catch (error) {
      throw createError(
        ErrorCode.WORKFLOW_INVALID,
        `Failed to create workflow: ${error instanceof Error ? error.message : String(error)}`,
        undefined,
        { error, name, description }
      )
    }
  }

  /**
   * Load a workflow by ID
   */
  async load(workflowId: string): Promise<WorkflowJSON> {
    try {
      const response = await this.apiClient.get<WorkflowJSON>(`/workflows/${workflowId}`)
      return response.data
    } catch (error) {
      throw createError(
        ErrorCode.WORKFLOW_NOT_FOUND,
        `Failed to load workflow: ${error instanceof Error ? error.message : String(error)}`,
        undefined,
        { error, workflowId }
      )
    }
  }

  /**
   * Save a workflow
   */
  async save(workflow: WorkflowJSON): Promise<void> {
    try {
      await this.apiClient.put(`/workflows/${workflow.metadata.id}`, {
        workflow,
      })
    } catch (error) {
      throw createError(
        ErrorCode.WORKFLOW_INVALID,
        `Failed to save workflow: ${error instanceof Error ? error.message : String(error)}`,
        undefined,
        { error, workflowId: workflow.metadata.id }
      )
    }
  }

  /**
   * Delete a workflow
   */
  async delete(workflowId: string): Promise<void> {
    try {
      await this.apiClient.delete(`/workflows/${workflowId}`)
    } catch (error) {
      throw createError(
        ErrorCode.WORKFLOW_NOT_FOUND,
        `Failed to delete workflow: ${error instanceof Error ? error.message : String(error)}`,
        undefined,
        { error, workflowId }
      )
    }
  }

  /**
   * List all workflows
   */
  async list(): Promise<WorkflowSummary[]> {
    try {
      const response = await this.apiClient.get<{ workflows: WorkflowSummary[] }>('/workflows')
      return response.data.workflows
    } catch (error) {
      throw createError(
        ErrorCode.API_ERROR,
        `Failed to list workflows: ${error instanceof Error ? error.message : String(error)}`,
        undefined,
        { error }
      )
    }
  }

  /**
   * Add a node to the workflow
   */
  addNode(workflow: WorkflowJSON, node: NodeDefinition): WorkflowJSON {
    // Validate node
    if (!node.id || !node.type) {
      throw createError(
        ErrorCode.NODE_INVALID,
        'Node must have id and type',
        undefined,
        { node }
      )
    }

    // Check if node already exists
    if (workflow.nodes.some((n) => n.id === node.id)) {
      throw createError(
        ErrorCode.NODE_INVALID,
        `Node with id ${node.id} already exists`,
        undefined,
        { nodeId: node.id }
      )
    }

    // Create new workflow with added node
    return {
      ...workflow,
      nodes: [...workflow.nodes, node],
      metadata: {
        ...workflow.metadata,
        modified: new Date().toISOString(),
      },
    }
  }

  /**
   * Remove a node from the workflow
   */
  removeNode(workflow: WorkflowJSON, nodeId: string): WorkflowJSON {
    // Find the node
    const nodeIndex = workflow.nodes.findIndex((n) => n.id === nodeId)
    if (nodeIndex === -1) {
      throw createError(
        ErrorCode.NODE_INVALID,
        `Node with id ${nodeId} not found`,
        undefined,
        { nodeId }
      )
    }

    // Remove all connections related to this node
    const updatedConnections = workflow.connections.filter(
      (conn) => conn.source.nodeId !== nodeId && conn.target.nodeId !== nodeId
    )

    // Create new workflow with removed node
    const updatedNodes = workflow.nodes.filter((n) => n.id !== nodeId)

    return {
      ...workflow,
      nodes: updatedNodes,
      connections: updatedConnections,
      metadata: {
        ...workflow.metadata,
        modified: new Date().toISOString(),
      },
    }
  }

  /**
   * Update a node in the workflow
   */
  updateNode(
    workflow: WorkflowJSON,
    nodeId: string,
    updates: Partial<NodeDefinition>
  ): WorkflowJSON {
    // Find the node
    const nodeIndex = workflow.nodes.findIndex((n) => n.id === nodeId)
    if (nodeIndex === -1) {
      throw createError(
        ErrorCode.NODE_INVALID,
        `Node with id ${nodeId} not found`,
        undefined,
        { nodeId }
      )
    }

    // Update the node
    const updatedNodes = [...workflow.nodes]
    updatedNodes[nodeIndex] = {
      ...updatedNodes[nodeIndex],
      ...updates,
      id: nodeId, // Ensure id doesn't change
    }

    return {
      ...workflow,
      nodes: updatedNodes,
      metadata: {
        ...workflow.metadata,
        modified: new Date().toISOString(),
      },
    }
  }

  /**
   * Add a connection between two nodes
   */
  addConnection(workflow: WorkflowJSON, connection: ConnectionDefinition): WorkflowJSON {
    // Validate connection
    if (!connection.id || !connection.source.nodeId || !connection.target.nodeId) {
      throw createError(
        ErrorCode.CONNECTION_INVALID,
        'Connection must have id, source nodeId, and target nodeId',
        undefined,
        { connection }
      )
    }

    // Check if nodes exist
    const sourceNode = workflow.nodes.find((n) => n.id === connection.source.nodeId)
    const targetNode = workflow.nodes.find((n) => n.id === connection.target.nodeId)

    if (!sourceNode || !targetNode) {
      throw createError(
        ErrorCode.CONNECTION_INVALID,
        'Source or target node not found',
        undefined,
        { connection }
      )
    }

    // Validate port compatibility
    if (!this.validateConnection(sourceNode, targetNode, connection)) {
      throw createError(
        ErrorCode.PORT_MISMATCH,
        'Port types are not compatible',
        undefined,
        { connection }
      )
    }

    // Check if connection already exists
    if (workflow.connections.some((c) => c.id === connection.id)) {
      throw createError(
        ErrorCode.CONNECTION_INVALID,
        `Connection with id ${connection.id} already exists`,
        undefined,
        { connectionId: connection.id }
      )
    }

    // Create new workflow with added connection
    return {
      ...workflow,
      connections: [...workflow.connections, connection],
      metadata: {
        ...workflow.metadata,
        modified: new Date().toISOString(),
      },
    }
  }

  /**
   * Remove a connection from the workflow
   */
  removeConnection(workflow: WorkflowJSON, connectionId: string): WorkflowJSON {
    // Find the connection
    const connectionIndex = workflow.connections.findIndex((c) => c.id === connectionId)
    if (connectionIndex === -1) {
      throw createError(
        ErrorCode.CONNECTION_INVALID,
        `Connection with id ${connectionId} not found`,
        undefined,
        { connectionId }
      )
    }

    // Create new workflow with removed connection
    return {
      ...workflow,
      connections: workflow.connections.filter((c) => c.id !== connectionId),
      metadata: {
        ...workflow.metadata,
        modified: new Date().toISOString(),
      },
    }
  }

  /**
   * Validate if a connection is valid based on port types
   */
  private validateConnection(
    sourceNode: NodeDefinition,
    targetNode: NodeDefinition,
    connection: ConnectionDefinition
  ): boolean {
    // Find source port
    const sourcePort = sourceNode.outputs.find((p) => p.id === connection.source.portId)
    if (!sourcePort) {
      return false
    }

    // Find target port
    const targetPort = targetNode.inputs.find((p) => p.id === connection.target.portId)
    if (!targetPort) {
      return false
    }

    // Check type compatibility
    return this.areTypesCompatible(sourcePort.dataType, targetPort.dataType)
  }

  /**
   * Check if two data types are compatible
   */
  private areTypesCompatible(sourceType: string, targetType: string): boolean {
    // 'any' type is compatible with everything
    if (sourceType === 'any' || targetType === 'any') {
      return true
    }

    // Same types are compatible
    if (sourceType === targetType) {
      return true
    }

    // Define type compatibility rules
    const compatibilityMap: Record<string, string[]> = {
      number: ['string', 'json'],
      string: ['json'],
      boolean: ['json'],
      file: ['table', 'json'],
      table: ['json'],
      json: [],
    }

    const compatible = compatibilityMap[sourceType] || []
    return compatible.includes(targetType)
  }

  /**
   * Generate a unique ID
   */
  generateId(prefix: string = 'id'): string {
    return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  /**
   * Create a new workflow JSON structure
   */
  createEmptyWorkflow(name: string, description?: string): WorkflowJSON {
    const now = new Date().toISOString()
    return {
      metadata: {
        id: this.generateId('workflow'),
        name,
        version: '1.0.0',
        description,
        created: now,
        modified: now,
      },
      nodes: [],
      connections: [],
      projectSettings: {},
    }
  }
}

/**
 * Create a singleton instance of WorkflowService
 */
let workflowServiceInstance: WorkflowService | null = null

export function createWorkflowService(apiClient: APIClient): WorkflowService {
  workflowServiceInstance = new WorkflowService(apiClient)
  return workflowServiceInstance
}

export function getWorkflowService(): WorkflowService {
  if (!workflowServiceInstance) {
    throw new Error('WorkflowService not initialized. Call createWorkflowService first.')
  }
  return workflowServiceInstance
}
