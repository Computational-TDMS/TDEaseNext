import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useStateBusStore } from '@/stores/state-bus'
import type { ConnectionDefinition } from '@/types/workflow'

function stateConnection(): ConnectionDefinition {
  return {
    id: 'state-edge-1',
    source: { nodeId: 'featuremap_1', portId: 'selection_out' },
    target: { nodeId: 'table_1', portId: 'selection_in' },
    connectionKind: 'state',
    semanticType: 'state/selection_ids',
  }
}

describe('state-bus store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('activates pulse state for state edges when dispatching and clears after timeout', () => {
    vi.useFakeTimers()
    const store = useStateBusStore()
    store.setConnections([stateConnection()])

    const result = store.dispatch('featuremap_1', 'selection_out', {
      semanticType: 'state/selection_ids',
      data: [1, 3, 5],
      timestamp: Date.now(),
    })

    expect(result.ok).toBe(true)
    expect(
      store.isConnectionActive('featuremap_1', 'selection_out', 'table_1', 'selection_in')
    ).toBe(true)

    vi.advanceTimersByTime(1300)
    expect(
      store.isConnectionActive('featuremap_1', 'selection_out', 'table_1', 'selection_in')
    ).toBe(false)
    vi.useRealTimers()
  })

  it('delivers payload and source/target context to subscribers', () => {
    const store = useStateBusStore()
    store.setConnections([stateConnection()])

    const callback = vi.fn()
    store.subscribe('table_1', 'selection_in', callback)

    store.dispatch('featuremap_1', 'selection_out', {
      semanticType: 'state/selection_ids',
      data: [2, 4],
      timestamp: Date.now(),
    })

    expect(callback).toHaveBeenCalledTimes(1)
    const [payload, context] = callback.mock.calls[0]
    expect(payload.semanticType).toBe('state/selection_ids')
    expect(context.sourceNodeId).toBe('featuremap_1')
    expect(context.sourcePortId).toBe('selection_out')
    expect(context.targetNodeId).toBe('table_1')
    expect(context.targetPortId).toBe('selection_in')
  })
})

