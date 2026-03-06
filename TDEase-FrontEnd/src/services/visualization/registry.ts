/**
 * Visualization component registration system
 *
 * Design: extensible registry for visualization types
 * so that new visualizations can be registered without changing core editor code.
 */

import { defineAsyncComponent, type Component } from 'vue'

export type VisualizationType = 
  | 'featuremap'   // Scatter plot for feature maps (RT vs Mass)
  | 'scatter'      // Generic scatter plot with color/size mapping
  | 'heatmap'      // Heatmap for matrix data
  | 'volcano'      // Volcano plot for differential expression
  | 'spectrum'     // Mass spectrum visualization
  | 'table'        // Data table with AG-Grid
  | 'html'         // HTML fragment viewer

export interface VisualizationRegistration {
  type: VisualizationType
  label: string
  description?: string
  component: Component
  icon?: string
  category?: 'plot' | 'table' | 'scientific'
  defaultConfig?: Record<string, unknown>
  /** Optional: validator for node visualizationConfig */
  validateConfig?: (config: Record<string, unknown>) => boolean
}

const registry = new Map<VisualizationType, VisualizationRegistration>()

// Lazy-loaded components for better performance
const FeatureMapViewer = defineAsyncComponent(() => 
  import('@/components/visualization/FeatureMapViewer.vue')
)
const ScatterPlotViewer = defineAsyncComponent(() => 
  import('@/components/visualization/ScatterPlotViewer.vue')
)
const HeatmapViewer = defineAsyncComponent(() => 
  import('@/components/visualization/HeatmapViewer.vue')
)
const VolcanoPlotViewer = defineAsyncComponent(() => 
  import('@/components/visualization/VolcanoPlotViewer.vue')
)
const SpectrumViewer = defineAsyncComponent(() => 
  import('@/components/visualization/SpectrumViewer.vue')
)
const TableViewer = defineAsyncComponent(() => 
  import('@/components/visualization/TableViewer.vue')
)
const HtmlViewer = defineAsyncComponent(() =>
  import('@/components/visualization/HtmlViewer.vue')
)

// Register all built-in visualizations
const builtInVisualizations: VisualizationRegistration[] = [
  {
    type: 'featuremap',
    label: 'Feature Map',
    description: '2D scatter plot for RT vs Mass visualization with intensity coloring',
    component: FeatureMapViewer,
    icon: 'Coordinate',
    category: 'scientific',
    defaultConfig: { topN: 10000 },
  },
  {
    type: 'scatter',
    label: 'Scatter Plot',
    description: 'Generic scatter plot with X, Y, Z axis mapping and color/size encoding',
    component: ScatterPlotViewer,
    icon: 'ScatterChart',
    category: 'plot',
    defaultConfig: {
      axisMapping: { x: '', y: '', z: '', color: '', size: '' },
      colorScheme: 'viridis',
      showLegend: true,
      symbolSize: 8,
      symbolType: 'circle',
    },
  },
  {
    type: 'heatmap',
    label: 'Heatmap',
    description: 'Matrix heatmap visualization for expression patterns',
    component: HeatmapViewer,
    icon: 'HeatMap',
    category: 'plot',
    defaultConfig: {
      rowColumn: 'row',
      columnColumn: 'column',
      valueColumn: 'value',
      colorScheme: 'viridis',
      showRowLabels: true,
      showColumnLabels: true,
      clusteringEnabled: false,
      missingValueColor: '#d3d3d3',
    },
  },
  {
    type: 'volcano',
    label: 'Volcano Plot',
    description: 'Volcano plot for differential expression analysis',
    component: VolcanoPlotViewer,
    icon: 'TrendCharts',
    category: 'scientific',
    defaultConfig: {
      foldChangeColumn: '',
      pValueColumn: '',
      nameColumn: '',
      foldChangeThreshold: 1,
      pValueThreshold: 0.05,
      upregulatedColor: '#e74c3c',
      downregulatedColor: '#3498db',
      neutralColor: '#95a5a6',
    },
  },
  {
    type: 'spectrum',
    label: 'Mass Spectrum',
    description: 'Mass spectrometry spectrum visualization with peak detection',
    component: SpectrumViewer,
    icon: 'Histogram',
    category: 'scientific',
    defaultConfig: {
      mzColumn: '',
      intensityColumn: '',
      normalizeIntensity: true,
      showPeaks: true,
      peakThreshold: 0,
      overlayMode: 'none',
      comparisonSpectra: [],
    },
  },
  {
    type: 'table',
    label: 'Data Table',
    description: 'Interactive data table with AG-Grid',
    component: TableViewer,
    icon: 'Table',
    category: 'table',
    defaultConfig: {
      visibleColumns: [],
      columnOrder: [],
      sortBy: undefined,
      pageSize: 50,
      enableSelection: true,
      enableExport: true,
    },
  },
  {
    type: 'html',
    label: 'HTML Viewer',
    description: 'Isolated HTML fragment viewer for selected rows',
    component: HtmlViewer,
    icon: 'Document',
    category: 'scientific',
    defaultConfig: {
      htmlFileId: '',
      sourceNodeId: '',
      enableFullscreen: true,
      enableExport: true,
      sandboxEnabled: true,
    },
  },
]

// Register all built-in visualizations
builtInVisualizations.forEach(reg => {
  registry.set(reg.type, reg)
})

export function registerVisualization(reg: VisualizationRegistration): void {
  if (registry.has(reg.type)) {
    console.warn(`[VisualizationRegistry] Overriding existing visualization: ${reg.type}`)
  }
  registry.set(reg.type, reg)
}

export function getVisualization(type: VisualizationType): VisualizationRegistration | undefined {
  return registry.get(type)
}

export function listVisualizations(): VisualizationRegistration[] {
  return Array.from(registry.values())
}

export function listVisualizationsByCategory(category: VisualizationRegistration['category']): VisualizationRegistration[] {
  return Array.from(registry.values()).filter(reg => reg.category === category)
}

export function hasVisualization(type: VisualizationType): boolean {
  return registry.has(type)
}

export function unregisterVisualization(type: VisualizationType): boolean {
  return registry.delete(type)
}

/**
 * Get default configuration for a visualization type
 */
export function getDefaultConfig(type: VisualizationType): Record<string, unknown> | undefined {
  return registry.get(type)?.defaultConfig
}

/**
 * Validate configuration for a visualization type
 */
export function validateConfig(type: VisualizationType, config: Record<string, unknown>): { valid: boolean; errors: string[] } {
  const registration = registry.get(type)
  
  if (!registration) {
    return { valid: false, errors: [`Unknown visualization type: ${type}`] }
  }
  
  if (registration.validateConfig) {
    const isValid = registration.validateConfig(config)
    return { 
      valid: isValid, 
      errors: isValid ? [] : ['Configuration validation failed'] 
    }
  }
  
  return { valid: true, errors: [] }
}

/**
 * Get visualization component by type
 */
export function getVisualizationComponent(type: VisualizationType): Component | undefined {
  return registry.get(type)?.component
}

/**
 * Get all visualization types
 */
export function getVisualizationTypes(): VisualizationType[] {
  return Array.from(registry.keys())
}
