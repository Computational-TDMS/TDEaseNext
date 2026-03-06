import { describe, it, expect, vi } from 'vitest'
import { ref, nextTick } from 'vue'
import { useChartConfig, useChartConfigWithProps } from '@/composables/useChartConfig'

describe('useChartConfig', () => {
  interface TestConfig {
    title: string
    color: string
    size: number
    enabled: boolean
  }

  const defaultConfig: TestConfig = {
    title: 'Default',
    color: '#000',
    size: 10,
    enabled: true
  }

  it('should initialize with default config', () => {
    const { config } = useChartConfig(defaultConfig)

    expect(config.title).toBe('Default')
    expect(config.color).toBe('#000')
    expect(config.size).toBe(10)
    expect(config.enabled).toBe(true)
  })

  it('should merge initial config with defaults', () => {
    const initialConfig = { title: 'Custom', size: 20 }
    const { config } = useChartConfig(defaultConfig, initialConfig)

    expect(config.title).toBe('Custom')
    expect(config.color).toBe('#000') // default
    expect(config.size).toBe(20) // override
    expect(config.enabled).toBe(true) // default
  })

  it('should update config partially', () => {
    const { config, updateConfig } = useChartConfig(defaultConfig)

    updateConfig({ title: 'Updated', size: 30 })

    expect(config.title).toBe('Updated')
    expect(config.color).toBe('#000') // unchanged
    expect(config.size).toBe(30)
    expect(config.enabled).toBe(true) // unchanged
  })

  it('should reset config to defaults', () => {
    const { config, updateConfig, resetConfig } = useChartConfig(defaultConfig)

    updateConfig({ title: 'Modified', color: '#fff', size: 50, enabled: false })
    expect(config.title).toBe('Modified')

    resetConfig()

    expect(config.title).toBe('Default')
    expect(config.color).toBe('#000')
    expect(config.size).toBe(10)
    expect(config.enabled).toBe(true)
  })

  it('should set config to new values', () => {
    const { config, setConfig } = useChartConfig(defaultConfig)

    const newConfig: TestConfig = {
      title: 'New',
      color: '#f00',
      size: 100,
      enabled: false
    }

    setConfig(newConfig)

    expect(config.title).toBe('New')
    expect(config.color).toBe('#f00')
    expect(config.size).toBe(100)
    expect(config.enabled).toBe(false)
  })

  it('should call change callback on update', () => {
    const callback = vi.fn()
    const { updateConfig, onConfigChange } = useChartConfig(defaultConfig)

    onConfigChange(callback)

    updateConfig({ title: 'Changed' })

    expect(callback).toHaveBeenCalledWith(
      expect.objectContaining({ title: 'Changed' })
    )
  })

  it('should validate config before update', () => {
    const validator = vi.fn((config: TestConfig) => config.size > 0)
    const { updateConfig } = useChartConfig(defaultConfig, {}, { validator })

    // Valid update
    updateConfig({ size: 20 })
    expect(validator).toHaveBeenCalled()

    // Invalid update
    updateConfig({ size: -1 })
    expect(validator).toHaveBeenCalled()
  })

  it('should not update if validation fails', () => {
    const validator = (config: TestConfig) => config.size > 0
    const { config, updateConfig } = useChartConfig(defaultConfig, {}, { validator })

    updateConfig({ size: -1 })

    expect(config.size).toBe(10) // unchanged
  })

  it('should work with props sync', () => {
    const propsConfig = ref<Partial<TestConfig> | null>({ title: 'From Props' })
    const emit = vi.fn()
    const { localConfig, updateLocalConfig, syncWithProps } = useChartConfigWithProps(
      defaultConfig,
      propsConfig,
      emit
    )

    expect(localConfig.title).toBe('From Props')

    updateLocalConfig({ size: 25 })

    expect(localConfig.size).toBe(25)
    expect(emit).toHaveBeenCalledWith('configChange', { size: 25 })
  })

  it('should sync with props changes', async () => {
    const propsConfig = ref<Partial<TestConfig> | null>({ title: 'Initial' })
    const emit = vi.fn()
    const { localConfig } = useChartConfigWithProps(
      defaultConfig,
      propsConfig,
      emit
    )

    expect(localConfig.title).toBe('Initial')

    propsConfig.value = { title: 'Updated' }

    await nextTick()
    expect(localConfig.title).toBe('Updated')
  })
})
