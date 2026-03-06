import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { StatePayload } from '@/types/state-ports'
import type { PortDefinition, ConnectionDefinition } from '@/types/workflow'

type StateCallback = (
  payload: StatePayload,
  context: {
    sourceNodeId: string
    sourcePortId: string
    targetNodeId: string
    targetPortId: string
  }
) => void

type ValidationResult = { ok: true } | { ok: false; reason: string }

const KEY_SEPARATOR = '::'

function makeKey(nodeId: string, portId: string): string {
  return `${nodeId}${KEY_SEPARATOR}${portId}`
}

function splitKey(key: string): { nodeId: string; portId: string } {
  const [nodeId, portId] = key.split(KEY_SEPARATOR)
  return { nodeId, portId }
}

function normalizePayload(nodeId: string, portId: string, payload: StatePayload): StatePayload {
  return {
    ...payload,
    timestamp: payload.timestamp || Date.now(),
    sourceNodeId: payload.sourceNodeId ?? nodeId,
    portId: payload.portId ?? portId,
  }
}

function isSelectionPayload(payload: StatePayload): boolean {
  if (payload.semanticType !== 'state/selection_ids') return false
  const data = payload.data as unknown
  if (data instanceof Set || Array.isArray(data)) return true
  if (data && typeof data === 'object' && 'selectedIndices' in data) return true
  return false
}

export const useStateBusStore = defineStore('stateBus', () => {
  const nodeStates = ref<Map<string, Map<string, StatePayload>>>(new Map())
  const subscriptions = ref<Map<string, Set<StateCallback>>>(new Map())
  const stateConnections = ref<Map<string, string[]>>(new Map())

  function getState(nodeId: string, portId: string): StatePayload | null {
    return nodeStates.value.get(nodeId)?.get(portId) || null
  }

  function setConnections(connections: ConnectionDefinition[]) {
    const next = new Map<string, string[]>()
    for (const connection of connections) {
      if (connection.connectionKind !== 'state') continue
      const sourceKey = makeKey(connection.source.nodeId, connection.source.portId)
      const targetKey = makeKey(connection.target.nodeId, connection.target.portId)
      const existing = next.get(sourceKey) || []
      existing.push(targetKey)
      next.set(sourceKey, existing)
    }
    stateConnections.value = next
  }

  function subscribe(targetNodeId: string, portId: string, callback: StateCallback) {
    const key = makeKey(targetNodeId, portId)
    const existing = subscriptions.value.get(key) || new Set<StateCallback>()
    existing.add(callback)
    subscriptions.value.set(key, existing)

    return () => {
      const current = subscriptions.value.get(key)
      if (!current) return
      current.delete(callback)
      if (current.size === 0) {
        subscriptions.value.delete(key)
      }
    }
  }

  function validateConnection(sourcePort: PortDefinition, targetPort: PortDefinition): ValidationResult {
    const sourceKind = sourcePort.portKind ?? 'data'
    const targetKind = targetPort.portKind ?? 'data'

    if (sourceKind === 'data' && targetKind === 'data') {
      return { ok: true }
    }

    if (sourceKind === 'state-out' && targetKind === 'state-in') {
      const sourceType = sourcePort.semanticType
      const targetType = targetPort.semanticType
      if (!sourceType || !targetType) {
        return { ok: false, reason: 'Missing semantic type for state connection' }
      }
      if (sourceType !== targetType) {
        return {
          ok: false,
          reason: `Incompatible types: ${sourceType} -> ${targetType}`,
        }
      }
      return { ok: true }
    }

    return { ok: false, reason: 'Cannot connect state port to data port' }
  }

  function validatePayload(payload: StatePayload): ValidationResult {
    if (!payload.semanticType) {
      return { ok: false, reason: 'Missing semanticType in payload' }
    }
    if (payload.semanticType === 'state/selection_ids' && !isSelectionPayload(payload)) {
      return { ok: false, reason: 'Invalid selection payload' }
    }
    return { ok: true }
  }

  function dispatch(nodeId: string, portId: string, payload: StatePayload): ValidationResult {
    const normalized = normalizePayload(nodeId, portId, payload)
    const validation = validatePayload(normalized)
    if (!validation.ok) return validation

    const nodeEntry = nodeStates.value.get(nodeId) || new Map<string, StatePayload>()
    nodeEntry.set(portId, normalized)
    nodeStates.value.set(nodeId, nodeEntry)

    const sourceKey = makeKey(nodeId, portId)
    const targets = stateConnections.value.get(sourceKey) || []

    for (const targetKey of targets) {
      const callbacks = subscriptions.value.get(targetKey)
      if (!callbacks || callbacks.size === 0) continue
      const { nodeId: targetNodeId, portId: targetPortId } = splitKey(targetKey)
      callbacks.forEach((callback) => {
        callback(normalized, {
          sourceNodeId: nodeId,
          sourcePortId: portId,
          targetNodeId,
          targetPortId,
        })
      })
    }

    return { ok: true }
  }

  function detectCycle(
    sourceNodeId: string,
    targetNodeId: string,
    connections: ConnectionDefinition[]
  ): boolean {
    const adjacency = new Map<string, Set<string>>()
    const addEdge = (from: string, to: string) => {
      const edges = adjacency.get(from) || new Set<string>()
      edges.add(to)
      adjacency.set(from, edges)
    }

    for (const connection of connections) {
      if (connection.connectionKind !== 'state') continue
      addEdge(connection.source.nodeId, connection.target.nodeId)
    }

    addEdge(sourceNodeId, targetNodeId)

    const visited = new Set<string>()
    const stack = new Set<string>()

    const dfs = (nodeId: string): boolean => {
      if (stack.has(nodeId)) return true
      if (visited.has(nodeId)) return false
      visited.add(nodeId)
      stack.add(nodeId)
      const neighbors = adjacency.get(nodeId) || new Set<string>()
      for (const neighbor of neighbors) {
        if (dfs(neighbor)) return true
      }
      stack.delete(nodeId)
      return false
    }

    return dfs(targetNodeId)
  }

  function clearAll() {
    nodeStates.value.clear()
    subscriptions.value.clear()
    stateConnections.value.clear()
  }

  return {
    nodeStates,
    subscriptions,
    stateConnections,
    getState,
    setConnections,
    subscribe,
    dispatch,
    validateConnection,
    detectCycle,
    clearAll,
  }
})
