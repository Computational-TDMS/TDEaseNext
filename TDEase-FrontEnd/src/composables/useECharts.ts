import { computed, shallowRef, watch, onUnmounted, type Ref as VueRef, type ComputedRef } from 'vue'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'

export interface UseEChartsOptions {
  theme?: string | object
  option?: EChartsOption
  autoResize?: boolean
  resizeDelay?: number
}

export interface UseEChartsReturn {
  chart: VueRef<echarts.ECharts | null>
  chartContainer: VueRef<HTMLElement | null | undefined>
  isReady: ComputedRef<boolean>
  init: () => void
  dispose: () => void
  setOption: (option: EChartsOption, notMerge?: boolean) => void
  resize: () => void
  on: (event: string, handler: (...args: any[]) => void) => void
  off: (event: string, handler?: (...args: any[]) => void) => void
  showLoading: (opts?: any) => void
  hideLoading: () => void
  clear: () => void
}

export function useECharts(
  container: VueRef<HTMLElement | null | undefined>,
  options: UseEChartsOptions = {}
): UseEChartsReturn {
  const {
    theme = '',
    autoResize = true,
    resizeDelay = 100
  } = options

  const chart = shallowRef<echarts.ECharts | null>(null)
  const chartContainer = container

  let resizeObserver: ResizeObserver | null = null
  let resizeTimer: ReturnType<typeof setTimeout> | null = null
  let visibilityHandler: (() => void) | null = null
  let focusHandler: (() => void) | null = null

  const isReady = computed(() => chart.value !== null)

  const init = () => {
    if (!chartContainer.value) {
      console.warn('[useECharts] Container element not found')
      return
    }

    if (chart.value) {
      console.warn('[useECharts] Chart already initialized')
      return
    }

    try {
      chart.value = echarts.init(chartContainer.value, theme)
      console.log('[useECharts] Chart initialized successfully')
    } catch (error) {
      console.error('[useECharts] Failed to initialize chart:', error)
    }
  }

  const dispose = () => {
    if (resizeObserver) {
      resizeObserver.disconnect()
      resizeObserver = null
    }

    if (resizeTimer) {
      clearTimeout(resizeTimer)
      resizeTimer = null
    }

    if (chart.value) {
      try {
        chart.value.dispose()
        chart.value = null
        console.log('[useECharts] Chart disposed')
      } catch (error) {
        console.error('[useECharts] Error disposing chart:', error)
      }
    }
  }

  const setOption = (option: EChartsOption, notMerge = false) => {
    if (!chart.value) {
      console.warn('[useECharts] Cannot set option: chart not initialized')
      return
    }

    try {
      chart.value.setOption(option, notMerge)
    } catch (error) {
      console.error('[useECharts] Error setting option:', error)
    }
  }

  const resize = () => {
    if (!chart.value) {
      console.warn('[useECharts] Cannot resize: chart not initialized')
      return
    }

    try {
      chart.value.resize()
    } catch (error) {
      console.error('[useECharts] Error resizing chart:', error)
    }
  }

  const on = (event: string, handler: (...args: any[]) => void) => {
    if (!chart.value) {
      console.warn(`[useECharts] Cannot attach event '${event}': chart not initialized`)
      return
    }

    chart.value.on(event, handler)
  }

  const off = (event: string, handler?: (...args: any[]) => void) => {
    if (!chart.value) {
      console.warn(`[useECharts] Cannot detach event '${event}': chart not initialized`)
      return
    }

    if (handler) {
      chart.value.off(event, handler)
    } else {
      chart.value.off(event)
    }
  }

  const showLoading = (opts?: any) => {
    if (!chart.value) {
      console.warn('[useECharts] Cannot show loading: chart not initialized')
      return
    }

    chart.value.showLoading('default', opts)
  }

  const hideLoading = () => {
    if (!chart.value) {
      console.warn('[useECharts] Cannot hide loading: chart not initialized')
      return
    }

    chart.value.hideLoading()
  }

  const clear = () => {
    if (!chart.value) {
      console.warn('[useECharts] Cannot clear: chart not initialized')
      return
    }

    chart.value.clear()
  }

  const setupAutoResize = () => {
    if (!autoResize || !chartContainer.value) return

    resizeObserver = new ResizeObserver(() => {
      if (resizeTimer) {
        clearTimeout(resizeTimer)
      }

      resizeTimer = setTimeout(() => {
        resize()
      }, resizeDelay)
    })

    resizeObserver.observe(chartContainer.value)

    visibilityHandler = () => {
      if (document.visibilityState === 'visible') {
        requestAnimationFrame(() => resize())
      }
    }
    focusHandler = () => {
      requestAnimationFrame(() => resize())
    }
    document.addEventListener('visibilitychange', visibilityHandler)
    window.addEventListener('focus', focusHandler)
  }

  watch(
    () => chartContainer.value,
    (el) => {
      if (!el || chart.value) return
      init()
      setupAutoResize()
      requestAnimationFrame(() => resize())
    },
    { immediate: true, flush: 'post' }
  )

  onUnmounted(() => {
    if (visibilityHandler) {
      document.removeEventListener('visibilitychange', visibilityHandler)
      visibilityHandler = null
    }
    if (focusHandler) {
      window.removeEventListener('focus', focusHandler)
      focusHandler = null
    }
    dispose()
  })

  return {
    chart,
    chartContainer,
    isReady,
    init,
    dispose,
    setOption,
    resize,
    on,
    off,
    showLoading,
    hideLoading,
    clear
  }
}
