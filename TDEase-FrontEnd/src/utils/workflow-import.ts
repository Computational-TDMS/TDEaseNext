import type { WorkflowJSON, NodeDefinition, ConnectionDefinition } from '@/stores/workflow'

type RawNode = {
  id: string
  type: string
  position: { x: number; y: number }
  data: { label?: string; type?: string; params?: Record<string, any> }
}

type RawEdge = {
  id: string
  source: string
  target: string
  sourceHandle?: string
  targetHandle?: string
  dataPath?: { s?: string; t?: string }
  connectionKind?: 'data' | 'state'
  semanticType?: string
}

type RawWorkflow = {
  nodes: RawNode[]
  edges: RawEdge[]
  metadata?: any
  projectSettings?: Record<string, unknown>
}

function inferConnectionKind(
  declaredKind: 'data' | 'state' | undefined,
  sourcePort: any,
  targetPort: any
): 'data' | 'state' {
  const sourceKind = sourcePort?.portKind || 'data'
  const targetKind = targetPort?.portKind || 'data'
  if (sourceKind === 'state-out' && targetKind === 'state-in') {
    return 'state'
  }
  return declaredKind || 'data'
}

export function importRawWorkflow(raw: RawWorkflow, registryPreloaded?: Record<string, any>): WorkflowJSON {
  console.log('[importRawWorkflow] Input:', { nodesCount: raw.nodes?.length, edgesCount: raw.edges?.length })
  console.log('[importRawWorkflow] Edges:', raw.edges)
  let registry: Record<string, any> = registryPreloaded ?? {}
  if (Object.keys(registry).length === 0) {
    const modules = {
      ...import.meta.glob('/config/tools/**/*.json', { eager: true }) as Record<string, any>,
      ...import.meta.glob('/config/tools_registry.json', { eager: true }) as Record<string, any>,
      ...import.meta.glob('/src/config/tools/**/*.json', { eager: true }) as Record<string, any>,
      ...import.meta.glob('/src/config/tools_registry.json', { eager: true }) as Record<string, any>
    }
    for (const path of Object.keys(modules)) {
      const data = (modules[path]?.default ?? modules[path]) || {}
      const id = data.id || path.split('/').pop()!.replace(/\.json$/, '')
      registry[id] = data
    }
  }
  console.log('[importRawWorkflow] Registry loaded:', Object.keys(registry))
  const portSets: Record<string, { inputs: Set<string>; outputs: Set<string> }> = {}
  const normalizeHandle = (h?: string) => (h ? h.replace(/^output-/, '').replace(/^input-/, '') : undefined)
  const parseSuffix = (h?: string) => {
    if (!h) return undefined
    const base = h.replace(/^output-/, '').replace(/^input-/, '')
    const parts = base.split('__')
    return parts.length > 1 ? parts[1] : undefined
  }
  for (const e of raw.edges) {
    portSets[e.source] ||= { inputs: new Set(), outputs: new Set() }
    portSets[e.target] ||= { inputs: new Set(), outputs: new Set() }
    const sh = normalizeHandle(e.sourceHandle)
    const th = normalizeHandle(e.targetHandle)
    if (sh) portSets[e.source].outputs.add(sh)
    if (th) portSets[e.target].inputs.add(th)
  }

  const nodes: NodeDefinition[] = raw.nodes.map((n) => {
    const toolId = n.data?.type || n.type
    const toolCfg = toolId ? registry[toolId] : undefined
    console.log(`[importRawWorkflow] Node ${n.id}: toolId=${toolId}, toolCfg found=${!!toolCfg}`)

    // Extract ports configuration from tool definition (supports new schema with ports.inputs/ports.outputs)
    const portsDefinition = toolCfg?.ports
    const inputParams = portsDefinition?.inputs || toolCfg?.inputs || toolCfg?.input_params || []
    const outputPatterns = portsDefinition?.outputs || toolCfg?.outputs || toolCfg?.output_patterns || []

    const inputs = Array.from(portSets[n.id]?.inputs || [])
    const outputs = Array.from(portSets[n.id]?.outputs || [])

    // Merge registry-defined ports to ensure completeness
    for (const p of inputParams) {
      const pid = typeof p === 'string' ? p : p.id
      if (!inputs.includes(pid)) inputs.push(pid)
    }
    for (const op of outputPatterns) {
      const hid = op.handle || op.id || op.pattern || 'output'
      if (!outputs.includes(hid)) outputs.push(hid)
    }

    console.log(`[importRawWorkflow] Node ${n.id}: inputs=${inputs.length}, outputs=${outputs.length}`)

    // Samples from params (first array param or specific known keys)
    const params = n.data?.params || {}
    let samples: string[] | undefined
    for (const key of Object.keys(params)) {
      const val = params[key]
      if (Array.isArray(val) && val.length && typeof val[0] === 'string') {
        samples = val as string[]
        break
      }
    }
    if (!samples && Array.isArray((raw as any)?.metadata?.samples) && (raw as any).metadata.samples.length) {
      samples = ((raw as any).metadata.samples as string[]).slice()
    }
    return {
      id: n.id,
      type: n.type || toolId, // Preserve original type or use toolId
      position: n.position,
      displayProperties: {
        label: n.data?.label || n.type,
        color: '#409eff'
      },
      // Extract executionMode and visualizationConfig from tool definition for interactive nodes
      executionMode: toolCfg?.executionMode || toolCfg?.execution_mode || undefined,
      visualizationConfig: toolCfg?.visualization ? {
        type: toolCfg.visualization.type,
        config: toolCfg.visualization.config,
        components: toolCfg.visualization.components
      } : undefined,
      inputs: inputs.map((id) => {
        const pdef = inputParams.find((p: any) => (typeof p === 'string' ? p === id : p.id === id))
        const name = typeof pdef === 'string' ? id : (pdef?.name || id)
        const type = typeof pdef === 'string' ? 'file' : ((pdef as any)?.dataType || (pdef as any)?.type || 'file')
        const required = typeof pdef === 'string' ? false : (pdef?.required === true)
        const accept = typeof pdef === 'string' ? undefined : (Array.isArray((pdef as any)?.accept) ? (pdef as any).accept : undefined)
        const portKind = typeof pdef === 'string' ? undefined : ((pdef as any)?.portKind || undefined)
        const semanticType = typeof pdef === 'string' ? undefined : ((pdef as any)?.semanticType || undefined)
        return accept
          ? { id, name, type, required, accept, portKind, semanticType } as any
          : { id, name, type, required, portKind, semanticType } as any
      }),
      outputs: outputs.map((id) => {
        const op = outputPatterns.find((o: any) => (o.handle || o.id) === id)
        const name = op?.name || id
        const type = (op as any)?.dataType || op?.type || 'file'
        const required = op?.required === true
        const provides = Array.isArray((op as any)?.provides) ? (op as any).provides : undefined
        const portKind = (op as any)?.portKind || undefined
        const semanticType = (op as any)?.semanticType || undefined
        return provides
          ? { id, name, type, required, provides, portKind, semanticType } as any
          : { id, name, type, required, portKind, semanticType } as any
      }),
      nodeConfig: {
        toolId: toolId,
        params: paramsFromRaw(n.data?.params),
        paramValues: { ...(n.data?.params || {}) },
        inputs: inputs.map((id) => {
          const pdef = inputParams.find((p: any) => (typeof p === 'string' ? p === id : p.id === id))
          const name = typeof pdef === 'string' ? id : (pdef?.name || id)
          const type = typeof pdef === 'string' ? 'file' : ((pdef as any)?.dataType || (pdef as any)?.type || 'file')
          const accept = typeof pdef === 'string' ? undefined : (Array.isArray((pdef as any)?.accept) ? (pdef as any).accept : undefined)
          const portKind = typeof pdef === 'string' ? undefined : ((pdef as any)?.portKind || undefined)
          const semanticType = typeof pdef === 'string' ? undefined : ((pdef as any)?.semanticType || undefined)
          return accept
            ? { id, name, type, accept, portKind, semanticType } as any
            : { id, name, type, portKind, semanticType } as any
        }),
        outputs: outputs.map((id) => {
          // attach pattern from registry if matched by handle/id
          const op = outputPatterns.find((o: any) => (o.handle || o.id) === id)
          const pattern = op?.pattern
          const name = op?.name || id
          const type = (op as any)?.dataType || op?.type || 'file'
          const provides = Array.isArray((op as any)?.provides) ? (op as any).provides : undefined
          const portKind = (op as any)?.portKind || undefined
          const semanticType = (op as any)?.semanticType || undefined
          return pattern
            ? (provides ? { id, name, type, pattern, provides, portKind, semanticType } as any : { id, name, type, pattern, portKind, semanticType } as any)
            : (provides ? { id, name, type, provides, portKind, semanticType } as any : { id, name, type, portKind, semanticType } as any)
        }),
        samples
      }
    }
  })

  const connectionsRaw: ConnectionDefinition[] = raw.edges.map((e) => {
    const sPortRaw = normalizeHandle(e.sourceHandle) || 'output'
    const tPortRaw = normalizeHandle(e.targetHandle) || 'input'
    const sPort = sPortRaw.split('__')[0]
    const tPort = tPortRaw.split('__')[0]
    const sSuffix = parseSuffix(e.sourceHandle)
    const tSuffix = parseSuffix(e.targetHandle)
    return {
      id: e.id,
      source: { nodeId: e.source, portId: sPort },
      target: { nodeId: e.target, portId: tPort },
      dataPath: e.dataPath || { s: sSuffix, t: tSuffix },
      connectionKind: e.connectionKind,
      semanticType: e.semanticType,
    }
  })

  const connections: ConnectionDefinition[] = connectionsRaw.map((connection) => {
    const sourceNode = nodes.find((node) => node.id === connection.source.nodeId)
    const targetNode = nodes.find((node) => node.id === connection.target.nodeId)
    const sourcePort = sourceNode?.outputs.find((port: any) => port.id === connection.source.portId)
    const targetPort = targetNode?.inputs.find((port: any) => port.id === connection.target.portId)
    const inferredKind = inferConnectionKind(
      connection.connectionKind,
      sourcePort,
      targetPort
    )
    const semanticType =
      inferredKind === 'state'
        ? connection.semanticType || (sourcePort as any)?.semanticType || (targetPort as any)?.semanticType
        : undefined

    return {
      ...connection,
      connectionKind: inferredKind,
      semanticType,
    }
  })

  console.log('[importRawWorkflow] Generated connections:', connections)
  return {
    metadata: {
      id: raw.metadata?.id || String(Date.now()),
      name: raw.metadata?.name || 'Imported Workflow',
      version: raw.metadata?.version || '1.0.0',
      description: raw.metadata?.description,
      author: raw.metadata?.author,
      created: raw.metadata?.created || new Date().toISOString(),
      modified: raw.metadata?.modified || new Date().toISOString(),
      tags: raw.metadata?.tags || []
    },
    nodes,
    connections,
    projectSettings: raw.projectSettings || {}
  }
}

function paramsFromRaw(params?: Record<string, any>) {
  if (!params) return []
  return Object.keys(params).map((k) => ({ id: k, name: k, type: guessType(params[k]), default: params[k] }))
}

function guessType(v: any): 'string' | 'number' | 'boolean' {
  if (typeof v === 'number') return 'number'
  if (typeof v === 'boolean') return 'boolean'
  return 'string'
}

/**
 * 从工作流中提取 sample 和 fasta_filename，用于执行时传递给后端
 */
export function extractSampleContextFromWorkflow(wf: any): Record<string, string> {
  const ctx: Record<string, string> = {}
  const nodes = wf?.nodes ?? []
  for (const n of nodes) {
    const data = n?.data ?? {}
    const nodeConfig = n?.nodeConfig ?? {}
    const toolId = data?.type ?? nodeConfig?.toolId ?? n?.type
    const params = data?.params ?? nodeConfig?.paramValues ?? {}
    if (toolId === 'data_loader') {
      const srcs = params?.input_sources
      if (Array.isArray(srcs) && srcs.length) {
        const first = String(srcs[0])
        ctx.sample = first.replace(/\.[^/.]+$/, '').split(/[/\\]/).pop() ?? first
        break
      }
      if (typeof srcs === 'string') {
        const first = srcs
        ctx.sample = first.replace(/\.[^/.]+$/, '').split(/[/\\]/).pop() ?? first
        break
      }
    } else if (toolId === 'fasta_loader') {
      const ff = params?.fasta_file
      if (ff) {
        const s = String(ff)
        ctx.fasta_filename = s.replace(/\.[^/.]+$/, '').split(/[/\\]/).pop() ?? s
      }
    }
  }
  if (!ctx.sample && Array.isArray(wf?.metadata?.samples) && wf.metadata.samples.length) {
    ctx.sample = String(wf.metadata.samples[0])
  }
  return ctx
}
