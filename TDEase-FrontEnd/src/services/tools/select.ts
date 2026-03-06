import type { WorkflowJSON } from '@/stores/workflow'
import type { ToolConfig } from './registry'

export function selectToolsForWorkflow(workflow: WorkflowJSON, registry: ToolConfig[]): ToolConfig[] {
  const usedIds = new Set<string>()
  for (const node of workflow.nodes) {
    const cfg = node.nodeConfig as any
    const toolId: string | undefined = cfg?.toolId || (cfg?.tool?.id as string | undefined)
    if (toolId) usedIds.add(toolId)
  }
  return registry.filter((t) => usedIds.has(t.id))
}

