import { shallowRef } from 'vue'
import apiClient from '@/services/api'

export type ToolParamType =
  | 'string'
  | 'number'
  | 'boolean'
  | 'select'
  | 'multiselect'
  | 'range'
  | 'int'
  | 'float'
  | 'slider'
  | 'radio'
  | 'checkbox'
  | 'value'    // 新 Schema 类型
  | 'choice'   // 新 Schema 类型

export type ToolParam = {
  id: string
  name: string
  type: ToolParamType
  default?: unknown
  options?: Array<{ label: string; value: unknown }>
  choices?: string[]  // 新 Schema: 简化的选项数组
  min?: number
  max?: number
  step?: number
  precision?: number
  description?: string
  flag?: string       // 新 Schema: 命令行标志
  group?: string      // 新 Schema: 参数分组
  advanced?: boolean  // 新 Schema: 是否为高级参数
}

export type ToolPort = {
  id: string
  name: string
  type: string
  required?: boolean
  description?: string
  pattern?: string
  handle?: string
  accept?: string[]
  provides?: string[]
  dataType?: string
  positional?: boolean     // 新 Schema: 是否为位置参数
  positionalOrder?: number  // 新 Schema: 位置参数顺序
}

// 新 Schema: ports 结构
export type ToolPorts = {
  inputs?: ToolPort[]
  outputs?: ToolPort[]
}

// 新 Schema: command 结构
export type ToolCommand = {
  executable?: string
  interpreter?: string
  useUv?: boolean
  dockerImage?: string
}

// 新 Schema: output 配置
export type ToolOutput = {
  flagSupported: boolean
  flag?: string
  flagValue?: string
}

export type ToolConfig = {
  id: string
  name: string
  version?: string       // 新 Schema
  description?: string
  kind?: 'script' | 'command'  // 保留兼容
  executionMode?: 'native' | 'script' | 'docker' | 'interactive'  // 新 Schema
  command?: ToolCommand  // 新 Schema
  ports?: ToolPorts      // 新 Schema
  parameters?: Record<string, {    // 新 Schema: parameters 对象
    flag?: string
    type: ToolParamType
    label?: string
    description?: string
    group?: string
    advanced?: boolean
    default?: unknown
    choices?: string[] | Record<string, string>
  }>
  output?: ToolOutput    // 新 Schema

  // 兼容旧字段（自动从新字段生成）
  params?: ToolParam[]
  inputs?: ToolPort[]
  outputs?: ToolPort[]
  positionalParams?: string[]
  paramMapping?: Record<string, any>
  outputFlag?: string
  outputFlagSupported?: boolean
  toolPath?: string
  docker?: { image?: string; commandPrefix?: string; volumeMountStrategy?: string; volumeMountTemplate?: string; workingDir?: string }
}

const registry = shallowRef<ToolConfig[]>([])

const parseToolEntry = (id: string, data: any): ToolConfig => {
  const tool: ToolConfig = {
    id: data.id || id,
    name: data.name || id,
    version: data.version,
    description: data.description || '',
    executionMode: data.executionMode || data.execution_mode || 'native',
    command: data.command || {},
    ports: data.ports || { inputs: [], outputs: [] },
    parameters: data.parameters || {},
    output: data.output || { flagSupported: false },
  }

  // 从新格式生成旧格式（向后兼容前端现有代码）
  if (data.ports) {
    tool.inputs = data.ports.inputs || []
    tool.outputs = data.ports.outputs || []

    // 生成 positionalParams
    const positionalInputs = (data.ports.inputs || [])
      .filter((i: any) => i.positional)
      .sort((a: any, b: any) => (a.positionalOrder || 0) - (b.positionalOrder || 0))
    tool.positionalParams = positionalInputs.map((i: any) => i.id)

    // 生成 params 数组用于 UI 渲染
    if (data.parameters) {
      tool.params = Object.entries(data.parameters).map(([key, p]: [string, any]) => ({
        id: key,
        name: p.label || key,
        type: p.type,
        default: p.default,
        options: p.choices ? (Array.isArray(p.choices) ? p.choices.map((c: string) => ({ label: c, value: c })) : Object.keys(p.choices).map((k) => ({ label: k, value: k }))) : undefined,
        description: p.description,
        group: p.group,
        advanced: p.advanced
      }))
    }
  }

  // 从新格式生成旧 paramMapping
  if (data.parameters) {
    tool.paramMapping = {}
    for (const [key, p] of Object.entries(data.parameters)) {
      const paramDef = p as any
      tool.paramMapping![key] = {
        flag: paramDef.flag,
        type: paramDef.type,
        choices: paramDef.choices
      }
    }
  }

  // 从新格式生成旧 outputFlag
  if (data.output) {
    tool.outputFlag = data.output.flag
    tool.outputFlagSupported = data.output.flagSupported
  }

  // 兼容旧格式字段
  if (data.toolPath) tool.toolPath = data.toolPath
  if (data.docker) tool.docker = data.docker

  return tool
}

let loadPromise: Promise<void> | null = null

const load = async () => {
  try {
    // Axios 响应拦截器已返回 response.data，这里直接按任意对象处理
    const json = await apiClient.get('/api/tools/schemas') as any
    const toolsMap: Record<string, any> = json?.registry || {}
    const entries = Object.keys(toolsMap).map(id => parseToolEntry(id, toolsMap[id]))
    registry.value = entries
    console.log("Tools loaded:", entries.length)
  } catch (e) {
    console.error("Error loading tools:", e)
  }
}

loadPromise = load()

/** 确保工具注册表已加载（可 await） */
export const ensureToolsLoaded = async (forceReload: boolean = false) => {
  if (forceReload || registry.value.length === 0) {
    if (!loadPromise || forceReload) {
      loadPromise = load()
    }
    await loadPromise

    // 首次请求失败时允许自动重试一次，避免 registry 永远为空
    if (registry.value.length === 0) {
      loadPromise = load()
      await loadPromise
    }
  } else if (loadPromise) {
    await loadPromise
  }
}

export const useToolsRegistry = () => registry
