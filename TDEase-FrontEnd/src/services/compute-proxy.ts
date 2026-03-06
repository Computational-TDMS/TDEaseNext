import apiClient from '@/services/api'
import { useStateBusStore } from '@/stores/state-bus'
import type { AnnotationData } from '@/types/visualization'

export interface SpectrumPeak {
  mz: number
  intensity: number
}

export interface FragmentMatchRequest {
  sequence: string
  spectrumData: SpectrumPeak[]
  ppmTolerance?: number
  dispatchTarget?: { nodeId: string; portId?: string }
}

export interface ModificationSearchRequest {
  selectedPeaks: SpectrumPeak[]
  modificationDb: string | Array<Record<string, unknown>>
  ppmTolerance?: number
  dispatchTarget?: { nodeId: string; portId?: string }
}

const CACHE_TTL_MS = 5 * 60 * 1000
const cache = new Map<string, { timestamp: number; value: any }>()

function stableStringify(value: any): string {
  if (Array.isArray(value)) {
    return `[${value.map(stableStringify).join(',')}]`
  }
  if (value && typeof value === 'object') {
    const keys = Object.keys(value).sort()
    return `{${keys.map((key) => `${JSON.stringify(key)}:${stableStringify(value[key])}`).join(',')}}`
  }
  return JSON.stringify(value)
}

function cacheKey(endpoint: string, payload: Record<string, unknown>): string {
  return `${endpoint}:${stableStringify(payload)}`
}

function getCached<T>(key: string): T | null {
  const entry = cache.get(key)
  if (!entry) return null
  if (Date.now() - entry.timestamp > CACHE_TTL_MS) {
    cache.delete(key)
    return null
  }
  return entry.value as T
}

function setCached<T>(key: string, value: T) {
  cache.set(key, { timestamp: Date.now(), value })
}

function dispatchAnnotation(
  nodeId: string,
  portId: string,
  annotationData: AnnotationData
) {
  const stateBus = useStateBusStore()
  stateBus.dispatch(nodeId, portId, {
    semanticType: 'state/annotation',
    data: annotationData,
    timestamp: Date.now(),
    sourceNodeId: nodeId,
    portId
  })
}

export async function fragmentMatch(request: FragmentMatchRequest): Promise<AnnotationData> {
  const payload = {
    sequence: request.sequence,
    spectrumData: request.spectrumData,
    ppmTolerance: request.ppmTolerance ?? 20
  }
  const key = cacheKey('/api/compute-proxy/fragment-match', payload)
  const cached = getCached<AnnotationData>(key)
  if (cached) {
    if (request.dispatchTarget) {
      dispatchAnnotation(request.dispatchTarget.nodeId, request.dispatchTarget.portId ?? 'annotation_out', cached)
    }
    return cached
  }

  const response = await apiClient.post('/api/compute-proxy/fragment-match', payload)
  const annotationData = response.data as AnnotationData
  setCached(key, annotationData)

  if (request.dispatchTarget) {
    dispatchAnnotation(request.dispatchTarget.nodeId, request.dispatchTarget.portId ?? 'annotation_out', annotationData)
  }

  return annotationData
}

export async function modificationSearch(request: ModificationSearchRequest): Promise<{ matches: any[] }> {
  const payload = {
    selectedPeaks: request.selectedPeaks,
    modificationDb: request.modificationDb,
    ppmTolerance: request.ppmTolerance ?? 20
  }
  const key = cacheKey('/api/compute-proxy/modification-search', payload)
  const cached = getCached<{ matches: any[] }>(key)
  if (cached) {
    if (request.dispatchTarget) {
      dispatchAnnotation(
        request.dispatchTarget.nodeId,
        request.dispatchTarget.portId ?? 'annotation_out',
        { annotations: cached.matches } as AnnotationData
      )
    }
    return cached
  }

  const response = await apiClient.post('/api/compute-proxy/modification-search', payload)
  const result = response.data as { matches: any[] }
  setCached(key, result)

  if (request.dispatchTarget) {
    dispatchAnnotation(
      request.dispatchTarget.nodeId,
      request.dispatchTarget.portId ?? 'annotation_out',
      { annotations: result.matches } as AnnotationData
    )
  }

  return result
}
