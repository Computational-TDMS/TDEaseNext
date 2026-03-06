import { ref, type Ref } from 'vue'
import * as echarts from 'echarts'

export interface ExportOptions {
  format?: 'png' | 'jpeg' | 'svg'
  pixelRatio?: number
  backgroundColor?: string
}

export interface UseChartExportReturn {
  isExporting: Ref<boolean>
  exportChart: (chart: echarts.ECharts, filename: string, options?: ExportOptions) => Promise<void>
  exportDataURL: (chart: echarts.ECharts, options?: ExportOptions) => Promise<string>
}

export function useChartExport(): UseChartExportReturn {
  const isExporting = ref(false)

  const exportDataURL = async (
    chart: echarts.ECharts,
    options: ExportOptions = {}
  ): Promise<string> => {
    const {
      format = 'png',
      pixelRatio = window.devicePixelRatio || 1,
      backgroundColor = '#fff'
    } = options

    if (!chart) {
      throw new Error('[useChartExport] Chart instance is required')
    }

    try {
      const url = chart.getDataURL({
        type: format,
        pixelRatio,
        backgroundColor
      })

      return url
    } catch (error) {
      console.error('[useChartExport] Error exporting chart to data URL:', error)
      throw error
    }
  }

  const exportChart = async (
    chart: echarts.ECharts,
    filename: string,
    options: ExportOptions = {}
  ): Promise<void> => {
    if (isExporting.value) {
      console.warn('[useChartExport] Export already in progress')
      return
    }

    isExporting.value = true

    try {
      const { format = 'png' } = options
      const dataURL = await exportDataURL(chart, options)

      // Create a temporary link element to trigger download
      const link = document.createElement('a')
      link.href = dataURL
      link.download = `${filename}.${format}`
      link.style.display = 'none'

      document.body.appendChild(link)
      link.click()

      // Cleanup
      setTimeout(() => {
        document.body.removeChild(link)
      }, 100)

      console.log(`[useChartExport] Chart exported as ${filename}.${format}`)
    } catch (error) {
      console.error('[useChartExport] Error exporting chart:', error)
      throw error
    } finally {
      isExporting.value = false
    }
  }

  return {
    isExporting,
    exportChart,
    exportDataURL
  }
}
