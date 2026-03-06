import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useChartExport } from '@/composables/useChartExport'
import type { ECharts } from 'echarts'

// Mock ECharts instance
const createMockChart = () => ({
  getDataURL: vi.fn(() => 'data:image/png;base64,mockdata'),
  dispose: vi.fn()
}) as any

describe('useChartExport', () => {
  let mockChart: ECharts
  let createElementSpy: ReturnType<typeof vi.spyOn>
  let appendChildSpy: ReturnType<typeof vi.spyOn>
  let removeChildSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    mockChart = createMockChart()

    // Mock document methods
    createElementSpy = vi.spyOn(document, 'createElement')
    appendChildSpy = vi.spyOn(document.body, 'appendChild')
    removeChildSpy = vi.spyOn(document.body, 'removeChild')
  })

  afterEach(() => {
    createElementSpy.mockRestore()
    appendChildSpy.mockRestore()
    removeChildSpy.mockRestore()
  })

  it('should initialize with not exporting', () => {
    const { isExporting } = useChartExport()

    expect(isExporting.value).toBe(false)
  })

  it('should export chart as data URL', async () => {
    const { exportDataURL } = useChartExport()

    const dataURL = await exportDataURL(mockChart, { format: 'png' })

    expect(dataURL).toBe('data:image/png;base64,mockdata')
    expect(mockChart.getDataURL).toHaveBeenCalledWith({
      type: 'png',
      pixelRatio: expect.any(Number),
      backgroundColor: '#fff',
      quality: 1
    })
  })

  it('should export chart and trigger download', async () => {
    const { exportChart, isExporting } = useChartExport()

    // Create a mock link element
    const mockLink = {
      href: '',
      download: '',
      style: { display: '' },
      click: vi.fn()
    }

    createElementSpy.mockReturnValue(mockLink as any)
    appendChildSpy.mockImplementation(() => mockLink as any)
    removeChildSpy.mockImplementation(() => mockLink as any)

    await exportChart(mockChart, 'test-chart')

    expect(isExporting.value).toBe(false)
    expect(mockChart.getDataURL).toHaveBeenCalled()
    expect(mockLink.download).toBe('test-chart.png')
    expect(mockLink.click).toHaveBeenCalled()
  })

  it('should export chart as JPEG', async () => {
    const { exportDataURL } = useChartExport()

    const dataURL = await exportDataURL(mockChart, { format: 'jpeg' })

    expect(dataURL).toBe('data:image/png;base64,mockdata')
    expect(mockChart.getDataURL).toHaveBeenCalledWith(
      expect.objectContaining({ type: 'jpeg' })
    )
  })

  it('should export chart as SVG', async () => {
    const { exportDataURL } = useChartExport()

    await exportDataURL(mockChart, { format: 'svg' })

    expect(mockChart.getDataURL).toHaveBeenCalledWith(
      expect.objectContaining({ type: 'svg' })
    )
  })

  it('should use custom options', async () => {
    const { exportDataURL } = useChartExport()

    await exportDataURL(mockChart, {
      format: 'png',
      quality: 0.8,
      pixelRatio: 2,
      backgroundColor: '#000'
    })

    expect(mockChart.getDataURL).toHaveBeenCalledWith({
      type: 'png',
      quality: 0.8,
      pixelRatio: 2,
      backgroundColor: '#000'
    })
  })

  it('should throw error when chart is null', async () => {
    const { exportDataURL } = useChartExport()

    await expect(exportDataURL(null as any)).rejects.toThrow()
  })

  it('should handle export errors', async () => {
    mockChart.getDataURL.mockImplementation(() => {
      throw new Error('Export failed')
    })

    const { exportDataURL } = useChartExport()

    await expect(exportDataURL(mockChart)).rejects.toThrow('Export failed')
  })
})
