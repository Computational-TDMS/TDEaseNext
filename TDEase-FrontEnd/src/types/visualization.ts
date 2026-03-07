/**
 * Visualization type definitions for interactive nodes
 * Enhanced version with heatmap, volcano plot, and advanced configurations
 */

/**
 * Supported visualization types
 */
export type VisualizationType =
  | 'featuremap'   // Scatter plot for feature maps (RT vs Mass)
  | 'scatter'      // Generic scatter plot
  | 'heatmap'      // Heatmap for matrix data
  | 'volcano'      // Volcano plot for differential expression
  | 'spectrum'     // Mass spectrum visualization
  | 'table'        // Data table with AG-Grid
  | 'topmsv_ms2'   // TopMSV-style PrSM MS2 peak viewer
  | 'topmsv_sequence' // TopMSV-style sequence/modification viewer

/**
 * Column definition for tabular data
 */
export interface ColumnDef {
  id: string
  name: string
  type: 'text' | 'string' | 'number' | 'boolean' | 'date'
  visible: boolean
  sortable?: boolean
  filterable?: boolean
  detectedType?: 'continuous' | 'categorical'
}

/**
 * Table data structure
 */
export interface TableData {
  columns: ColumnDef[]
  rows: Record<string, unknown>[]
  totalRows: number
  sourceFile: string
}

/**
 * Brush region for feature map selection
 */
export interface BrushRegion {
  xMin?: number
  xMax?: number
  yMin?: number
  yMax?: number
}

/**
 * Selection mode types
 */
export type SelectionMode = 'box' | 'lasso' | 'brush' | 'point'

/**
 * Selection event output
 */
export interface SelectionEvent {
  type: SelectionMode
  indices: number[]
  coordinates?: { x: number; y: number }[]
  brushRegion?: BrushRegion
  timestamp: number
}

/**
 * Filter definition
 */
export interface FilterDef {
  columnId: string
  operator: 'eq' | 'ne' | 'gt' | 'lt' | 'gte' | 'lte' | 'contains'
  value: unknown
}

/**
 * Selection state for a node
 */
export interface SelectionState {
  selectedIndices: Set<number>
  filterCriteria: FilterDef[]
  brushRegion: BrushRegion | null
}

/**
 * Data source type
 */
export type DataSourceType = 'file' | 'state' | 'none'

/**
 * Data source resolution result
 */
export interface DataSource {
  type: DataSourceType
  executionId?: string
  sourceNodeId?: string
  sourcePortId?: string
}

/**
 * Loading state for a node
 */
export interface LoadingState {
  status: 'idle' | 'loading' | 'success' | 'error' | 'pending'
  error?: string
  message?: string
  timestamp?: number
}

/**
 * Axis mapping configuration
 */
export interface AxisMapping {
  x?: string      // Column ID for X axis
  y?: string      // Column ID for Y axis
  z?: string      // Column ID for Z axis (3D or bubble size)
  color?: string  // Column ID for color mapping
  size?: string   // Column ID for size mapping
}

/**
 * Volcano plot specific configuration
 */
export interface VolcanoConfig {
  foldChangeColumn: string      // Log2 fold change column
  pValueColumn: string          // P-value column
  nameColumn?: string           // Gene/protein name column
  foldChangeThreshold: number   // Default: 1 or 2
  pValueThreshold: number       // Default: 0.05
  upregulatedColor: string      // Color for up-regulated points
  downregulatedColor: string    // Color for down-regulated points
  neutralColor: string          // Color for non-significant points
}

/**
 * Feature map specific configuration
 *
 * 每个 feature 使用 start/end time + mass + intensity 绘制一条横向 trace。
 */
export interface FeatureMapConfig {
  axisMapping: {
    startTime: string
    endTime: string
    mass: string
    intensity?: string
  }
  colorScheme: ColorSchemeId
  opacity: number
  /**
   * 最大渲染的 feature 条数，超过后按行号等间距采样。
   */
  maxTraces: number
}

/**
 * Heatmap specific configuration
 */
export interface HeatmapConfig {
  rowColumn: string          // Column for row labels
  columnColumn?: string      // Column for column labels (if matrix data)
  valueColumn: string        // Column for cell values
  colorScheme: ColorSchemeId // Color scheme for intensity
  showRowLabels: boolean
  showColumnLabels: boolean
  clusteringEnabled: boolean
  missingValueColor: string  // Color for null/NaN cells
}

/**
 * Scatter plot specific configuration
 */
export interface ScatterConfig {
  axisMapping: AxisMapping
  colorScheme: ColorSchemeId
  showLegend: boolean
  symbolSize: number | 'auto'
  symbolType: 'circle' | 'square' | 'triangle' | 'diamond'
}

/**
 * Spectrum specific configuration
 */
export interface SpectrumConfig {
  mzColumn: string
  intensityColumn: string
  normalizeIntensity: boolean
  showPeaks: boolean
  peakThreshold: number      // Minimum intensity to show peak
  overlayMode: 'none' | 'overlay' | 'comparison'
  comparisonSpectra?: string[] // Node IDs of spectra to compare
}

/**
 * Annotation data returned by Compute Proxy or other services
 */
export interface AnnotationData {
  annotations: Array<{
    mz: number
    type: string
    error: number
    matchedMz?: number
  }>
}

/**
 * Table viewer specific configuration
 */
export interface TableViewerConfig {
  visibleColumns: string[]
  columnOrder: string[]
  sortBy?: { column: string; direction: 'asc' | 'desc' }
  pageSize: number
  enableSelection: boolean
  enableExport: boolean
}

/**
 * Color scheme identifiers
 */
export type ColorSchemeId = 
  | 'viridis'
  | 'plasma'
  | 'inferno'
  | 'magma'
  | 'cividis'
  | 'cool'
  | 'warm'
  | 'rainbow'
  | 'spectral'
  | 'blues'
  | 'reds'
  | 'greens'
  | 'custom'

/**
 * Color scheme definition
 */
export interface ColorScheme {
  id: ColorSchemeId
  name: string
  type: 'sequential' | 'diverging' | 'categorical'
  colors: string[]
  description?: string
}

/**
 * Predefined color schemes
 */
export const COLOR_SCHEMES: ColorScheme[] = [
  { id: 'viridis', name: 'Viridis', type: 'sequential', colors: ['#440154', '#3b528b', '#21918c', '#5ec962', '#fde725'] },
  { id: 'plasma', name: 'Plasma', type: 'sequential', colors: ['#0d0887', '#6a00a8', '#b12a90', '#e16462', '#fca636'] },
  { id: 'inferno', name: 'Inferno', type: 'sequential', colors: ['#000004', '#420a68', '#932667', '#dd513a', '#fca50a'] },
  { id: 'magma', name: 'Magma', type: 'sequential', colors: ['#000004', '#3b0f70', '#8c2981', '#de4968', '#fec287'] },
  { id: 'cividis', name: 'Cividis', type: 'sequential', colors: ['#00204d', '#414287', '#7c7b78', '#beae6e', '#ffe945'] },
  { id: 'cool', name: 'Cool', type: 'diverging', colors: ['#6e40aa', '#6054c8', '#4c6edb', '#368ce1', '#23abd8', '#1ac7c2', '#1ddfa3', '#30ef82', '#52f667', '#7fff56'] },
  { id: 'warm', name: 'Warm', type: 'diverging', colors: ['#6e40aa', '#963db3', '#bf3caf', '#e4419d', '#fe4b83', '#ff5e63', '#ff7847', '#fb9633', '#e2b72f', '#c6d63c'] },
  { id: 'rainbow', name: 'Rainbow', type: 'categorical', colors: ['#9e0142', '#d53e4f', '#f46d43', '#fdae61', '#fee08b', '#e6f598', '#abdda4', '#66c2a5', '#3288bd', '#5e4fa2'] },
  { id: 'spectral', name: 'Spectral', type: 'diverging', colors: ['#9e0142', '#d53e4f', '#f46d43', '#fdae61', '#fee08b', '#e6f598', '#abdda4', '#66c2a5', '#3288bd', '#5e4fa2'] },
  { id: 'blues', name: 'Blues', type: 'sequential', colors: ['#f7fbff', '#deebf7', '#c6dbef', '#9ecae1', '#6baed6', '#4292c6', '#2171b5', '#08519c', '#08306b'] },
  { id: 'reds', name: 'Reds', type: 'sequential', colors: ['#fff5f0', '#fee0d2', '#fcbba1', '#fc9272', '#fb6a4a', '#ef3b2c', '#cb181d', '#a50f15', '#67000d'] },
  { id: 'greens', name: 'Greens', type: 'sequential', colors: ['#f7fcf5', '#e5f5e0', '#c7e9c0', '#a1d99b', '#74c476', '#41ab5d', '#238b45', '#006d2c', '#00441b'] },
]

/**
 * Export format options
 */
export type ExportFormat = 'png' | 'svg' | 'pdf' | 'csv' | 'json'

/**
 * Export configuration
 */
export interface ExportConfig {
  format: ExportFormat
  includeMetadata: boolean
  title?: string
  width?: number
  height?: number
  quality?: number  // For PNG (0-1)
}

/**
 * Visualization config for a node
 */
export interface VisualizationConfig {
  type: VisualizationType
  config?:
    | ScatterConfig
    | HeatmapConfig
    | VolcanoConfig
    | SpectrumConfig
    | FeatureMapConfig
    | TableViewerConfig
    | Record<string, unknown>
}

/**
 * Node data in visualization store
 */
export interface NodeDataEntry {
  data: TableData | null
  loadingState: LoadingState
}

/**
 * Node selection in visualization store
 */
export interface NodeSelectionEntry {
  selection: SelectionState | null
  timestamp?: number
}

/**
 * Data sampling configuration for large datasets
 */
export interface SamplingConfig {
  enabled: boolean
  method: 'random' | 'stratified' | 'nth' | 'density'
  sampleSize: number
  threshold: number  // Number of points above which to sample
}

/**
 * Performance monitoring state
 */
export interface PerformanceState {
  dataSize: number
  renderedPoints: number
  samplingApplied: boolean
  memoryUsage?: number
  renderTime?: number
}

/**
 * Volcano point data
 */
export interface VolcanoPoint {
  name: string
  log2FoldChange: number
  negLog10PValue: number
  index: number
  isSignificant: boolean
  regulation: 'up' | 'down' | 'neutral'
}

/**
 * Heatmap cell data
 */
export interface HeatmapCell {
  row: string
  column: string
  value: number | null
  rowIndex: number
  columnIndex: number
}
