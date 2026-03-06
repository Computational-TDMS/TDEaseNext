/**
 * Tests for ToolService
 * Feature: frontend-services, Property 11: Tool configuration to node template conversion
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { ToolService } from './service'
import type { ToolDefinition } from '../../types/api'

// Mock APIClient
class MockAPIClient {
  get = vi.fn().mockResolvedValue({ data: {} })
}

describe('ToolService', () => {
  let service: ToolService
  let mockApiClient: MockAPIClient

  const mockTool: ToolDefinition = {
    id: 'tool_1',
    name: 'Test Tool',
    category: 'process',
    description: 'A test tool',
    inputs: [
      {
        id: 'input_1',
        name: 'Input Data',
        dataType: 'file',
        required: true,
      },
    ],
    outputs: [
      {
        id: 'output_1',
        name: 'Output Data',
        dataType: 'table',
        required: false,
      },
    ],
    parameters: [
      {
        id: 'param_1',
        name: 'Threshold',
        type: 'number',
        required: false,
        default: 0.5,
      },
    ],
    executionType: 'python',
  }

  beforeEach(() => {
    mockApiClient = new MockAPIClient()
    service = new ToolService(mockApiClient as any)
  })

  describe('Property 11: 工具配置到节点模板转换', () => {
    it('should convert tool definition to node with all ports', () => {
      /**
       * Feature: frontend-services, Property 11: 工具配置到节点模板转换
       * Validates: Requirements 7.2
       *
       * For any valid ToolDefinition, the generated NodeDefinition should contain
       * all input and output ports from the tool definition
       */
      const position = { x: 100, y: 100 }
      const node = service.createNodeFromTool(mockTool, position)

      // Verify node structure
      expect(node.type).toBe(mockTool.id)
      expect(node.position).toEqual(position)

      // Verify inputs are preserved
      expect(node.inputs).toHaveLength(mockTool.inputs.length)
      expect(node.inputs[0].id).toBe('input_1')
      expect(node.inputs[0].dataType).toBe('file')

      // Verify outputs are preserved
      expect(node.outputs).toHaveLength(mockTool.outputs.length)
      expect(node.outputs[0].id).toBe('output_1')
      expect(node.outputs[0].dataType).toBe('table')

      // Verify parameters are preserved
      expect(node.parameters).toHaveLength(mockTool.parameters.length)
      expect(node.parameters![0].id).toBe('param_1')
    })

    it('should include tool metadata in node config', () => {
      /**
       * Feature: frontend-services, Property 11: 工具配置到节点模板转换
       * Validates: Requirements 7.2
       */
      const node = service.createNodeFromTool(mockTool, { x: 0, y: 0 })

      expect(node.nodeConfig.toolId).toBe(mockTool.id)
      expect(node.nodeConfig.executionType).toBe(mockTool.executionType)
    })

    it('should generate unique node IDs', async () => {
      /**
       * Feature: frontend-services, Property 11: 工具配置到节点模板转换
       * Validates: Requirements 7.2
       */
      const node1 = service.createNodeFromTool(mockTool, { x: 0, y: 0 })
      
      // Wait a bit to ensure different timestamp
      await new Promise((resolve) => setTimeout(resolve, 10))
      
      const node2 = service.createNodeFromTool(mockTool, { x: 100, y: 100 })

      expect(node1.id).not.toBe(node2.id)
      expect(node1.id).toMatch(/^node_tool_1_/)
      expect(node2.id).toMatch(/^node_tool_1_/)
    })
  })

  describe('ToolService basic functionality', () => {
    it('should get all tools', async () => {
      mockApiClient.get.mockResolvedValueOnce({
        data: {
          tools: [mockTool],
          categories: ['process'],
        },
      })

      const tools = await service.getTools()

      expect(tools).toHaveLength(1)
      expect(tools[0].id).toBe('tool_1')
      expect(mockApiClient.get).toHaveBeenCalledWith('/tools')
    })

    it('should cache tools', async () => {
      mockApiClient.get.mockResolvedValueOnce({
        data: {
          tools: [mockTool],
          categories: ['process'],
        },
      })

      // First call
      await service.getTools()
      expect(mockApiClient.get).toHaveBeenCalledTimes(1)

      // Second call should use cache
      await service.getTools()
      expect(mockApiClient.get).toHaveBeenCalledTimes(1)
    })

    it('should get tool by ID', async () => {
      mockApiClient.get.mockResolvedValueOnce({
        data: {
          tool: mockTool,
        },
      })

      const tool = await service.getToolById('tool_1')

      expect(tool.id).toBe('tool_1')
      expect(mockApiClient.get).toHaveBeenCalledWith('/tools/tool_1')
    })

    it('should get tools by category', async () => {
      mockApiClient.get.mockResolvedValueOnce({
        data: {
          tools: [mockTool],
          categories: ['process'],
        },
      })

      const tools = await service.getToolsByCategory('process')

      expect(tools).toHaveLength(1)
      expect(tools[0].category).toBe('process')
    })

    it('should get all categories', async () => {
      mockApiClient.get.mockResolvedValueOnce({
        data: {
          tools: [mockTool],
          categories: ['process'],
        },
      })

      const categories = await service.getCategories()

      expect(categories).toContain('process')
    })

    it('should refresh tools cache', async () => {
      mockApiClient.get.mockResolvedValue({
        data: {
          tools: [mockTool],
          categories: ['process'],
        },
      })

      // First call
      await service.getTools()
      expect(mockApiClient.get).toHaveBeenCalledTimes(1)

      // Refresh
      await service.refreshTools()
      expect(mockApiClient.get).toHaveBeenCalledTimes(2)
    })

    it('should clear cache', async () => {
      mockApiClient.get.mockResolvedValueOnce({
        data: {
          tools: [mockTool],
          categories: ['process'],
        },
      })

      await service.getTools()
      expect(service.getCacheSize()).toBe(1)

      service.clearCache()
      expect(service.getCacheSize()).toBe(0)
    })

    it('should create node from tool', () => {
      const position = { x: 50, y: 50 }
      const node = service.createNodeFromTool(mockTool, position)

      expect(node.type).toBe(mockTool.id)
      expect(node.position).toEqual(position)
      expect(node.inputs).toEqual(mockTool.inputs)
      expect(node.outputs).toEqual(mockTool.outputs)
    })

    it('should handle API errors', async () => {
      mockApiClient.get.mockRejectedValueOnce(new Error('API Error'))

      await expect(service.getTools()).rejects.toThrow('Failed to get tools')
    })
  })
})
