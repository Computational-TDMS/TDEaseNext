/**
 * Tests for WorkflowService
 * Feature: frontend-services, Properties 2-6: Workflow operations
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import fc from 'fast-check'
import { WorkflowService } from './service'
import type { WorkflowJSON, NodeDefinition, ConnectionDefinition } from '../../types/workflow'

// Mock APIClient
class MockAPIClient {
  post = vi.fn().mockResolvedValue({ data: {} })
  get = vi.fn().mockResolvedValue({ data: {} })
  put = vi.fn().mockResolvedValue({ data: {} })
  delete = vi.fn().mockResolvedValue({ data: {} })
}

describe('WorkflowService', () => {
  let service: WorkflowService
  let mockApiClient: MockAPIClient

  beforeEach(() => {
    mockApiClient = new MockAPIClient()
    service = new WorkflowService(mockApiClient as any)
  })

  describe('Property 2: 工作流 ID 唯一性', () => {
    it('should generate unique workflow IDs', async () => {
      /**
       * Feature: frontend-services, Property 2: 工作流 ID 唯一性
       * Validates: Requirements 2.1
       *
       * For any multiple workflows created, each workflow ID should be unique
       */
      await fc.assert(
        fc.asyncProperty(fc.integer({ min: 2, max: 10 }), async (count) => {
          const workflows: WorkflowJSON[] = []

          for (let i = 0; i < count; i++) {
            const workflow = service.createEmptyWorkflow(`Workflow ${i}`)
            workflows.push(workflow)
          }

          // Extract IDs
          const ids = workflows.map((w) => w.metadata.id)

          // Check uniqueness
          const uniqueIds = new Set(ids)
          expect(uniqueIds.size).toBe(ids.length)
        }),
        { numRuns: 20 }
      )
    })
  })

  describe('Property 3: 工作流保存加载往返一致性', () => {
    it('should preserve workflow data through save and load', async () => {
      /**
       * Feature: frontend-services, Property 3: 工作流保存加载往返一致性
       * Validates: Requirements 2.2, 2.3
       *
       * For any valid WorkflowJSON, saving and loading should produce equivalent data
       */
      const workflow = service.createEmptyWorkflow('Test Workflow', 'Test Description')

      // Mock the API responses
      mockApiClient.put.mockResolvedValueOnce({ data: { success: true } })
      mockApiClient.get.mockResolvedValueOnce({ data: workflow })

      // Save
      await service.save(workflow)

      // Load
      const loaded = await service.load(workflow.metadata.id)

      // Verify equivalence
      expect(loaded.metadata.id).toBe(workflow.metadata.id)
      expect(loaded.metadata.name).toBe(workflow.metadata.name)
      expect(loaded.metadata.description).toBe(workflow.metadata.description)
      expect(loaded.nodes).toEqual(workflow.nodes)
      expect(loaded.connections).toEqual(workflow.connections)
    })
  })

  describe('Property 4: 节点添加后工作流包含该节点', () => {
    it('should contain added node after addition', async () => {
      /**
       * Feature: frontend-services, Property 4: 节点添加后工作流包含该节点
       * Validates: Requirements 2.4
       *
       * For any valid node configuration, after adding to workflow,
       * the workflow node list should contain that node
       */
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            nodeId: fc.string({ minLength: 1 }),
            nodeType: fc.constantFrom('input', 'process', 'output'),
          }),
          async (data) => {
            const workflow = service.createEmptyWorkflow('Test')

            const node: NodeDefinition = {
              id: data.nodeId,
              type: data.nodeType,
              position: { x: 0, y: 0 },
              displayProperties: {},
              inputs: [],
              outputs: [],
              nodeConfig: {},
            }

            const updated = service.addNode(workflow, node)

            // Verify node is in the workflow
            expect(updated.nodes).toHaveLength(1)
            expect(updated.nodes[0].id).toBe(data.nodeId)
            expect(updated.nodes[0].type).toBe(data.nodeType)
          }
        ),
        { numRuns: 20 }
      )
    })
  })

  describe('Property 5: 端口类型兼容性验证', () => {
    it('should validate port type compatibility', async () => {
      /**
       * Feature: frontend-services, Property 5: 端口类型兼容性验证
       * Validates: Requirements 2.5
       *
       * For any two ports, connection validation should match port dataType compatibility
       */
      const workflow = service.createEmptyWorkflow('Test')

      // Create source node with output port
      const sourceNode: NodeDefinition = {
        id: 'source',
        type: 'process',
        position: { x: 0, y: 0 },
        displayProperties: {},
        inputs: [],
        outputs: [
          {
            id: 'out1',
            name: 'Output',
            dataType: 'number',
            required: false,
          },
        ],
        nodeConfig: {},
      }

      // Create target node with input port
      const targetNode: NodeDefinition = {
        id: 'target',
        type: 'process',
        position: { x: 100, y: 0 },
        displayProperties: {},
        inputs: [
          {
            id: 'in1',
            name: 'Input',
            dataType: 'number',
            required: true,
          },
        ],
        outputs: [],
        nodeConfig: {},
      }

      const workflowWithNodes = service.addNode(service.addNode(workflow, sourceNode), targetNode)

      // Create valid connection
      const connection: ConnectionDefinition = {
        id: 'conn1',
        source: { nodeId: 'source', portId: 'out1' },
        target: { nodeId: 'target', portId: 'in1' },
      }

      // Should succeed
      const updated = service.addConnection(workflowWithNodes, connection)
      expect(updated.connections).toHaveLength(1)
    })

    it('should reject incompatible port types', () => {
      /**
       * Feature: frontend-services, Property 5: 端口类型兼容性验证
       * Validates: Requirements 2.5
       */
      const workflow = service.createEmptyWorkflow('Test')

      const sourceNode: NodeDefinition = {
        id: 'source',
        type: 'process',
        position: { x: 0, y: 0 },
        displayProperties: {},
        inputs: [],
        outputs: [
          {
            id: 'out1',
            name: 'Output',
            dataType: 'file',
            required: false,
          },
        ],
        nodeConfig: {},
      }

      const targetNode: NodeDefinition = {
        id: 'target',
        type: 'process',
        position: { x: 100, y: 0 },
        displayProperties: {},
        inputs: [
          {
            id: 'in1',
            name: 'Input',
            dataType: 'number',
            required: true,
          },
        ],
        outputs: [],
        nodeConfig: {},
      }

      const workflowWithNodes = service.addNode(service.addNode(workflow, sourceNode), targetNode)

      const connection: ConnectionDefinition = {
        id: 'conn1',
        source: { nodeId: 'source', portId: 'out1' },
        target: { nodeId: 'target', portId: 'in1' },
      }

      // Should fail
      expect(() => service.addConnection(workflowWithNodes, connection)).toThrow()
    })
  })

  describe('Property 6: 节点删除同时删除相关连接', () => {
    it('should remove related connections when node is deleted', async () => {
      /**
       * Feature: frontend-services, Property 6: 节点删除同时删除相关连接
       * Validates: Requirements 2.6
       *
       * For any node in workflow, after deletion, all connections
       * with that node as source or target should be deleted
       */
      const workflow = service.createEmptyWorkflow('Test')

      // Create three nodes
      const node1: NodeDefinition = {
        id: 'node1',
        type: 'process',
        position: { x: 0, y: 0 },
        displayProperties: {},
        inputs: [],
        outputs: [{ id: 'out1', name: 'Output', dataType: 'any', required: false }],
        nodeConfig: {},
      }

      const node2: NodeDefinition = {
        id: 'node2',
        type: 'process',
        position: { x: 100, y: 0 },
        displayProperties: {},
        inputs: [{ id: 'in1', name: 'Input', dataType: 'any', required: true }],
        outputs: [{ id: 'out2', name: 'Output', dataType: 'any', required: false }],
        nodeConfig: {},
      }

      const node3: NodeDefinition = {
        id: 'node3',
        type: 'process',
        position: { x: 200, y: 0 },
        displayProperties: {},
        inputs: [{ id: 'in3', name: 'Input', dataType: 'any', required: true }],
        outputs: [],
        nodeConfig: {},
      }

      let updated = workflow
      updated = service.addNode(updated, node1)
      updated = service.addNode(updated, node2)
      updated = service.addNode(updated, node3)

      // Create connections: node1 -> node2 -> node3
      const conn1: ConnectionDefinition = {
        id: 'conn1',
        source: { nodeId: 'node1', portId: 'out1' },
        target: { nodeId: 'node2', portId: 'in1' },
      }

      const conn2: ConnectionDefinition = {
        id: 'conn2',
        source: { nodeId: 'node2', portId: 'out2' },
        target: { nodeId: 'node3', portId: 'in3' },
      }

      updated = service.addConnection(updated, conn1)
      updated = service.addConnection(updated, conn2)

      expect(updated.connections).toHaveLength(2)

      // Delete node2
      updated = service.removeNode(updated, 'node2')

      // Verify both connections are removed
      expect(updated.connections).toHaveLength(0)
      expect(updated.nodes).toHaveLength(2)
    })
  })

  describe('WorkflowService basic functionality', () => {
    it('should create empty workflow', () => {
      const workflow = service.createEmptyWorkflow('Test Workflow', 'Test Description')

      expect(workflow.metadata.name).toBe('Test Workflow')
      expect(workflow.metadata.description).toBe('Test Description')
      expect(workflow.nodes).toHaveLength(0)
      expect(workflow.connections).toHaveLength(0)
    })

    it('should add node to workflow', () => {
      const workflow = service.createEmptyWorkflow('Test')

      const node: NodeDefinition = {
        id: 'node1',
        type: 'process',
        position: { x: 0, y: 0 },
        displayProperties: {},
        inputs: [],
        outputs: [],
        nodeConfig: {},
      }

      const updated = service.addNode(workflow, node)

      expect(updated.nodes).toHaveLength(1)
      expect(updated.nodes[0].id).toBe('node1')
    })

    it('should prevent duplicate node IDs', () => {
      const workflow = service.createEmptyWorkflow('Test')

      const node: NodeDefinition = {
        id: 'node1',
        type: 'process',
        position: { x: 0, y: 0 },
        displayProperties: {},
        inputs: [],
        outputs: [],
        nodeConfig: {},
      }

      const updated = service.addNode(workflow, node)

      expect(() => service.addNode(updated, node)).toThrow()
    })

    it('should remove node from workflow', () => {
      let workflow = service.createEmptyWorkflow('Test')

      const node: NodeDefinition = {
        id: 'node1',
        type: 'process',
        position: { x: 0, y: 0 },
        displayProperties: {},
        inputs: [],
        outputs: [],
        nodeConfig: {},
      }

      workflow = service.addNode(workflow, node)
      expect(workflow.nodes).toHaveLength(1)

      workflow = service.removeNode(workflow, 'node1')
      expect(workflow.nodes).toHaveLength(0)
    })

    it('should update node in workflow', () => {
      let workflow = service.createEmptyWorkflow('Test')

      const node: NodeDefinition = {
        id: 'node1',
        type: 'process',
        position: { x: 0, y: 0 },
        displayProperties: {},
        inputs: [],
        outputs: [],
        nodeConfig: {},
      }

      workflow = service.addNode(workflow, node)

      workflow = service.updateNode(workflow, 'node1', {
        position: { x: 100, y: 100 },
      })

      expect(workflow.nodes[0].position.x).toBe(100)
      expect(workflow.nodes[0].position.y).toBe(100)
    })

    it('should generate unique IDs', () => {
      const id1 = service.generateId('test')
      const id2 = service.generateId('test')

      expect(id1).not.toBe(id2)
      expect(id1).toMatch(/^test_/)
      expect(id2).toMatch(/^test_/)
    })
  })
})
