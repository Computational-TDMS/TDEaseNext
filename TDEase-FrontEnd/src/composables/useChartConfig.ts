import { reactive, watch } from 'vue'

export interface ConfigChangeOptions<T> {
  emitOnChange?: boolean
  deep?: boolean
  validator?: (config: T) => boolean
}

export interface UseChartConfigReturn<T> {
  config: T
  updateConfig: (updates: Partial<T>) => void
  resetConfig: () => void
  setConfig: (newConfig: T) => void
  onConfigChange: (callback: (config: T) => void) => void
}

export function useChartConfig<T extends object>(
  defaultConfig: T,
  initialConfig?: Partial<T>,
  options: ConfigChangeOptions<T> = {}
): UseChartConfigReturn<T> {
  const {
    emitOnChange = true,
    validator
  } = options

  // Create reactive config merged from defaults and initial values
  const config = reactive({
    ...defaultConfig,
    ...initialConfig
  } as T) as T

  const changeCallbacks: ((config: T) => void)[] = []

  const notifyChange = () => {
    if (emitOnChange) {
      changeCallbacks.forEach(callback => callback(config))
    }
  }

  const updateConfig = (updates: Partial<T>) => {
    const newConfig = { ...config, ...updates } as T

    if (validator && !validator(newConfig)) {
      console.warn('[useChartConfig] Config validation failed, not updating')
      return
    }

    Object.assign(config, updates)
    notifyChange()
  }

  const resetConfig = () => {
    Object.assign(config, defaultConfig)
    notifyChange()
  }

  const setConfig = (newConfig: T) => {
    if (validator && !validator(newConfig)) {
      console.warn('[useChartConfig] Config validation failed, not setting')
      return
    }

    Object.assign(config, newConfig)
    notifyChange()
  }

  const onConfigChange = (callback: (config: T) => void) => {
    changeCallbacks.push(callback)
  }

  return {
    config,
    updateConfig,
    resetConfig,
    setConfig,
    onConfigChange
  }
}

export interface UseChartConfigWithPropsReturn<T> {
  localConfig: T
  updateLocalConfig: (updates: Partial<T>) => void
  syncWithProps: (propsConfig?: Partial<T> | null) => void
}

export function useChartConfigWithProps<T extends object>(
  defaultConfig: T,
  propsConfig: { value: Partial<T> | null | undefined },
  emit: (event: 'configChange', config: Partial<T>) => void
): UseChartConfigWithPropsReturn<T> {
  const localConfig = reactive({
    ...defaultConfig,
    ...(propsConfig.value || {})
  } as T) as T

  // Watch for props changes and sync local config
  watch(
    () => propsConfig.value,
    (newConfig) => {
      if (newConfig && typeof newConfig === 'object') {
        Object.assign(localConfig, newConfig)
      }
    },
    { deep: true, immediate: true }
  )

  const updateLocalConfig = (updates: Partial<T>) => {
    Object.assign(localConfig, updates)
    emit('configChange', updates)
  }

  const syncWithProps = (propsConfigValue?: Partial<T> | null) => {
    if (propsConfigValue && typeof propsConfigValue === 'object') {
      Object.assign(localConfig, propsConfigValue)
    }
  }

  return {
    localConfig,
    updateLocalConfig,
    syncWithProps
  }
}
