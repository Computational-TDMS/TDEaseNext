import { ref, computed, type ComputedRef } from 'vue'
import type { ECharts } from 'echarts'

export interface ChartToolState {
  canZoom: boolean
  canPan: boolean
  canReset: boolean
  zoomLevel: number
}

export interface UseChartToolsReturn {
  canZoom: ComputedRef<boolean>
  canPan: ComputedRef<boolean>
  canReset: ComputedRef<boolean>
  zoomIn: () => void
  zoomOut: () => void
  resetZoom: () => void
  enableZoom: () => void
  disableZoom: () => void
  enablePan: () => void
  disablePan: () => void
}

export function useChartTools(
  chart: () => ECharts | null
): UseChartToolsReturn {
  const isZoomEnabled = ref(true)
  const isPanEnabled = ref(true)
  const hasZoomed = ref(false)

  const canZoom = computed(() => isZoomEnabled.value && chart() !== null)
  const canPan = computed(() => isPanEnabled.value && chart() !== null)
  const canReset = computed(() => hasZoomed.value && chart() !== null)

  const zoomIn = () => {
    const currentChart = chart()
    if (!currentChart || !isZoomEnabled.value) return

    try {
      currentChart.dispatchAction({
        type: 'dataZoom',
        batch: [
          { start: 0, end: 50 }
        ]
      })
      hasZoomed.value = true
    } catch (error) {
      console.error('[useChartTools] Error zooming in:', error)
    }
  }

  const zoomOut = () => {
    const currentChart = chart()
    if (!currentChart || !isZoomEnabled.value) return

    try {
      currentChart.dispatchAction({
        type: 'dataZoom',
        batch: [
          { start: 50, end: 100 }
        ]
      })
      hasZoomed.value = true
    } catch (error) {
      console.error('[useChartTools] Error zooming out:', error)
    }
  }

  const resetZoom = () => {
    const currentChart = chart()
    if (!currentChart) return

    try {
      currentChart.dispatchAction({
        type: 'dataZoom',
        batch: [
          { start: 0, end: 100 }
        ]
      })
      hasZoomed.value = false
    } catch (error) {
      console.error('[useChartTools] Error resetting zoom:', error)
    }
  }

  const enableZoom = () => {
    isZoomEnabled.value = true
    const currentChart = chart()
    if (currentChart) {
      currentChart.dispatchAction({
        type: 'takeGlobalCursor',
        key: 'dataZoomSelect',
        dataZoomSelectActive: true
      })
    }
  }

  const disableZoom = () => {
    isZoomEnabled.value = false
    const currentChart = chart()
    if (currentChart) {
      currentChart.dispatchAction({
        type: 'takeGlobalCursor',
        key: 'dataZoomSelect',
        dataZoomSelectActive: false
      })
    }
  }

  const enablePan = () => {
    isPanEnabled.value = true
    const currentChart = chart()
    if (currentChart) {
      currentChart.dispatchAction({
        type: 'takeGlobalCursor',
        key: 'dataZoomSelect',
        dataZoomSelectActive: true
      })
    }
  }

  const disablePan = () => {
    isPanEnabled.value = false
    const currentChart = chart()
    if (currentChart) {
      currentChart.dispatchAction({
        type: 'takeGlobalCursor',
        key: 'dataZoomSelect',
        dataZoomSelectActive: false
      })
    }
  }

  return {
    canZoom,
    canPan,
    canReset,
    zoomIn,
    zoomOut,
    resetZoom,
    enableZoom,
    disableZoom,
    enablePan,
    disablePan
  }
}
