import { describe, expect, it } from 'vitest'
import { resolveNodeInputSource } from '@/services/workflow-connector'
import type { ConnectionDefinition, NodeDefinition } from '@/stores/workflow'

function makeNode(id: string, type: string): NodeDefinition {
  return {
    id,
    type,
    position: { x: 0, y: 0 },
    displayProperties: {},
    inputs: [],
    outputs: [],
    nodeConfig: { toolId: type },
  }
}

describe('workflow-connector', () => {
  it('returns sourcePortId for direct data-edge sources', () => {
    const nodes: NodeDefinition[] = [
      makeNode('topfd_1', 'topfd'),
      makeNode('table_1', 'table_viewer'),
    ]
    const connections: ConnectionDefinition[] = [
      {
        id: 'edge-1',
        source: { nodeId: 'topfd_1', portId: 'ms1feature' },
        target: { nodeId: 'table_1', portId: 'data_file' },
        connectionKind: 'data',
      },
    ]

    const source = resolveNodeInputSource('table_1', nodes, connections, {
      topfd: { executionMode: 'native' },
      table_viewer: { executionMode: 'interactive' },
    })

    expect(source.type).toBe('file')
    expect(source.sourceNodeId).toBe('topfd_1')
    expect(source.sourcePortId).toBe('ms1feature')
  })

  it('keeps original file source port when traversing through interactive upstream nodes', () => {
    const nodes: NodeDefinition[] = [
      makeNode('topfd_1', 'topfd'),
      makeNode('featuremap_1', 'featuremap_viewer'),
      makeNode('table_1', 'table_viewer'),
    ]
    const connections: ConnectionDefinition[] = [
      {
        id: 'edge-data',
        source: { nodeId: 'topfd_1', portId: 'ms1feature' },
        target: { nodeId: 'featuremap_1', portId: 'topfd_feature' },
        connectionKind: 'data',
      },
      {
        id: 'edge-state',
        source: { nodeId: 'featuremap_1', portId: 'selection_out' },
        target: { nodeId: 'table_1', portId: 'selection_in' },
        connectionKind: 'state',
        semanticType: 'state/selection_ids',
      },
    ]

    const source = resolveNodeInputSource('table_1', nodes, connections, {
      topfd: { executionMode: 'native' },
      featuremap_viewer: { executionMode: 'interactive' },
      table_viewer: { executionMode: 'interactive' },
    })

    expect(source.type).toBe('file')
    expect(source.sourceNodeId).toBe('topfd_1')
    expect(source.sourcePortId).toBe('ms1feature')
  })
})

