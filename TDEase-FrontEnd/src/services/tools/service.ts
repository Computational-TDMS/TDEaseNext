/**
 * Tool Service for managing tool registry
 * Handles tool discovery, caching, and node template generation
 */

import type { APIClient } from '../api/client'
import type { NodeDefinition, Position } from '../../types/workflow'
import type { ToolDefinition, ToolListResponse } from '../../types/api'
import { createError, ErrorCode } from '../../types/errors'

/**
 * ToolService class for managing tools
 */
export class ToolService {
  private toolsCache: Map<string, ToolDefinition> = new Map()
  private categoriesCache: Set<string> = new Set()
  private cacheExpiry: number = 5 * 60 * 1000 // 5 minutes
  private lastCacheTime: number = 0

  constructor(private apiClient: APIClient) {}

  /**
   * Get all available tools
   */
  async getTools(): Promise<ToolDefinition[]> {
    try {
      // Check cache validity
      if (this.isCacheValid()) {
        return Array.from(this.toolsCache.values())
      }

      const response = await this.apiClient.get<ToolListResponse>('/tools')

      // Update cache
      this.toolsCache.clear()
      this.categoriesCache.clear()

      response.data.tools.forEach((tool) => {
        this.toolsCache.set(tool.id, tool)
        this.categoriesCache.add(tool.category)
      })

      this.lastCacheTime = Date.now()

      return response.data.tools
    } catch (error) {
      throw createError(
        ErrorCode.API_ERROR,
        `Failed to get tools: ${error instanceof Error ? error.message : String(error)}`,
        undefined,
        { error }
      )
    }
  }

  /**
   * Get tool by ID
   */
  async getToolById(toolId: string): Promise<ToolDefinition> {
    try {
      // Check cache first
      if (this.toolsCache.has(toolId)) {
        return this.toolsCache.get(toolId)!
      }

      const response = await this.apiClient.get<{ tool: ToolDefinition }>(
        `/tools/${toolId}`
      )

      // Update cache
      this.toolsCache.set(toolId, response.data.tool)
      this.categoriesCache.add(response.data.tool.category)

      return response.data.tool
    } catch (error) {
      throw createError(
        ErrorCode.NOT_FOUND,
        `Failed to get tool: ${error instanceof Error ? error.message : String(error)}`,
        undefined,
        { error, toolId }
      )
    }
  }

  /**
   * Get tools by category
   */
  async getToolsByCategory(category: string): Promise<ToolDefinition[]> {
    try {
      // Ensure cache is populated
      if (this.toolsCache.size === 0) {
        await this.getTools()
      }

      const tools = Array.from(this.toolsCache.values()).filter(
        (tool) => tool.category === category
      )

      return tools
    } catch (error) {
      throw createError(
        ErrorCode.API_ERROR,
        `Failed to get tools by category: ${error instanceof Error ? error.message : String(error)}`,
        undefined,
        { error, category }
      )
    }
  }

  /**
   * Get all categories
   */
  async getCategories(): Promise<string[]> {
    try {
      // Ensure cache is populated
      if (this.categoriesCache.size === 0) {
        await this.getTools()
      }

      return Array.from(this.categoriesCache)
    } catch (error) {
      throw createError(
        ErrorCode.API_ERROR,
        `Failed to get categories: ${error instanceof Error ? error.message : String(error)}`,
        undefined,
        { error }
      )
    }
  }

  /**
   * Create a node from a tool definition
   */
  createNodeFromTool(tool: ToolDefinition, position: Position): NodeDefinition {
    return {
      id: `node_${tool.id}_${Date.now()}`,
      type: tool.id,
      position,
      displayProperties: {
        label: tool.name,
        color: this.getCategoryColor(tool.category),
      },
      inputs: tool.inputs,
      outputs: tool.outputs,
      parameters: tool.parameters,
      nodeConfig: {
        toolId: tool.id,
        executionType: tool.executionType,
      },
    }
  }

  /**
   * Refresh tool cache
   */
  async refreshTools(): Promise<void> {
    try {
      this.toolsCache.clear()
      this.categoriesCache.clear()
      this.lastCacheTime = 0

      await this.getTools()
    } catch (error) {
      throw createError(
        ErrorCode.API_ERROR,
        `Failed to refresh tools: ${error instanceof Error ? error.message : String(error)}`,
        undefined,
        { error }
      )
    }
  }

  /**
   * Check if cache is still valid
   */
  private isCacheValid(): boolean {
    if (this.toolsCache.size === 0) {
      return false
    }

    return Date.now() - this.lastCacheTime < this.cacheExpiry
  }

  /**
   * Get color for category
   */
  private getCategoryColor(category: string): string {
    const colors: Record<string, string> = {
      input: '#4CAF50',
      process: '#2196F3',
      output: '#FF9800',
      analysis: '#9C27B0',
      visualization: '#F44336',
      utility: '#607D8B',
    }

    return colors[category] || '#757575'
  }

  /**
   * Clear cache
   */
  clearCache(): void {
    this.toolsCache.clear()
    this.categoriesCache.clear()
    this.lastCacheTime = 0
  }

  /**
   * Get cache size
   */
  getCacheSize(): number {
    return this.toolsCache.size
  }
}

/**
 * Create a singleton instance of ToolService
 */
let toolServiceInstance: ToolService | null = null

export function createToolService(apiClient: APIClient): ToolService {
  toolServiceInstance = new ToolService(apiClient)
  return toolServiceInstance
}

export function getToolService(): ToolService {
  if (!toolServiceInstance) {
    throw new Error('ToolService not initialized. Call createToolService first.')
  }
  return toolServiceInstance
}
