import { describe, it, expect, vi } from 'vitest'
import { ref } from 'vue'
import { useChartTools } from '@/composables/useChartTools'
import type { ECharts } from 'echarts'

// Mock ECharts instance
const createMockChart = () => ({
  dispatchAction: vi.fn(),
  dispose: vi.fn()
}) as any

describe('useChartTools', () => {
  let mockChart: ECharts | null
  let chartRef: () => ECharts | null

  beforeEach(() => {
    mockChart = createMockChart()
    chartRef = () => mockChart
  })

  it('should initialize with tools enabled', () => {
    const { canZoom, canPan, canReset } = useChartTools(chartRef)

    expect(canZoom.value).toBe(true)
    expect(canPan.value).toBe(true)
    expect(canReset.value).toBe(false)
  })

  it('should zoom in', () => {
    const { zoomIn } = useChartTools(chartRef)

    zoomIn()

    expect(mockChart?.dispatchAction).toHaveBeenCalledWith({
      type: 'dataZoom',
      batch: [{ start: 0, end: 50 }]
    })
  })

  it('should zoom out', () => {
    const { zoomOut } = useChartTools(chartRef)

    zoomOut()

    expect(mockChart?.dispatchAction).toHaveBeenCalledWith({
      type: 'dataZoom',
      batch: [{ start: 50, end: 100 }]
    })
  })

  it('should reset zoom', () => {
    const { resetZoom } = useChartTools(chartRef)

    resetZoom()

    expect(mockChart?.dispatchAction).toHaveBeenCalledWith({
      type: 'dataZoom',
      batch: [{ start: 0, end: 100 }]
    })
  })

  it('should enable zoom', () => {
    const { enableZoom } = useChartTools(chartRef)

    enableZoom()

    expect(mockChart?.dispatchAction).toHaveBeenCalledWith({
      type: 'takeGlobalCursor',
      key: 'dataZoomSelect',
      dataZoomSelectActive: true
    })
  })

  it('should disable zoom', () => {
    const { disableZoom } = useChartTools(chartRef)

    disableZoom()

    expect(mockChart?.dispatchAction).toHaveBeenCalledWith({
      type: 'takeGlobalCursor',
      key: 'dataZoomSelect',
      dataZoomSelectActive: false
    })
  })

  it('should enable pan', () => {
    const { enablePan } = useChartTools(chartRef)

    enablePan()

    expect(mockChart?.dispatchAction).toHaveBeenCalledWith({
      type: 'takeGlobalCursor',
      key: 'dataZoomSelect',
      dataZoomSelectActive: true
    })
  })

  it('should disable pan', () => {
    const { disablePan } = useChartTools(chartRef)

    disablePan()

    expect(mockChart?.dispatchAction).toHaveBeenCalledWith({
      type: 'takeGlobalCursor',
      key: 'dataZoomSelect',
      dataZoomSelectActive: false
    })
  })

  it('should update canReset when zoom is used', () => {
    const { zoomIn, canReset } = useChartTools(chartRef)

    expect(canReset.value).toBe(false)

    zoomIn()

    expect(canReset.value).toBe(true)
  })

  it('should not dispatch actions when chart is null', () => {
    mockChart = null
    const { zoomIn, zoomOut, resetZoom } = useChartTools(chartRef)

    expect(() => zoomIn()).not.toThrow()
    expect(() => zoomOut()).not.toThrow()
    expect(() => resetZoom()).not.toThrow()
  })

  it('should disable zoom and pan when disabled', () => {
    const { disableZoom, disablePan, canZoom, canPan } = useChartTools(chartRef)

    disableZoom()
    expect(canZoom.value).toBe(false)

    disablePan()
    expect(canPan.value).toBe(false)
  })
})
