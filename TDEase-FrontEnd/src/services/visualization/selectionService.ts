/**
 * Selection Service - Handles box, lasso, and brush selection for visualization nodes
 * 
 * Provides utilities for:
 * - Box selection detection
 * - Lasso/polygon selection detection
 * - Brush region calculation
 * - Selection event output
 */

import type { SelectionMode, SelectionEvent, BrushRegion } from '@/types/visualization'

export interface Point {
  x: number
  y: number
}

export interface SelectionConfig {
  mode: SelectionMode
  brushRegion?: BrushRegion
  tolerance?: number  // For point proximity selection
}

/**
 * Box selection detector
 * Checks if points fall within a rectangular region
 */
export function detectBoxSelection(
  points: Point[],
  region: BrushRegion
): number[] {
  const selectedIndices: number[] = []

  points.forEach((point, index) => {
    const xMin = region.xMin ?? -Infinity
    const xMax = region.xMax ?? Infinity
    const yMin = region.yMin ?? -Infinity
    const yMax = region.yMax ?? Infinity

    if (point.x >= xMin && point.x <= xMax && point.y >= yMin && point.y <= yMax) {
      selectedIndices.push(index)
    }
  })

  return selectedIndices
}

/**
 * Lasso/polygon selection detector
 * Uses ray casting algorithm to determine if points are inside polygon
 */
export function detectLassoSelection(
  points: Point[],
  polygon: Point[]
): number[] {
  if (polygon.length < 3) return []

  const selectedIndices: number[] = []

  points.forEach((point, index) => {
    if (isPointInPolygon(point, polygon)) {
      selectedIndices.push(index)
    }
  })

  return selectedIndices
}

/**
 * Ray casting algorithm to check if point is inside polygon
 */
function isPointInPolygon(point: Point, polygon: Point[]): boolean {
  let inside = false

  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const xi = polygon[i].x
    const yi = polygon[i].y
    const xj = polygon[j].x
    const yj = polygon[j].y

    const intersect = ((yi > point.y) !== (yj > point.y)) &&
      (point.x < (xj - xi) * (point.y - yi) / (yj - yi) + xi)

    if (intersect) inside = !inside
  }

  return inside
}

/**
 * Point proximity selection
 * Selects points within a certain distance of the clicked/touched point
 */
export function detectProximitySelection(
  points: Point[],
  center: Point,
  tolerance: number = 10
): number[] {
  const selectedIndices: number[] = []
  const toleranceSquared = tolerance * tolerance

  points.forEach((point, index) => {
    const dx = point.x - center.x
    const dy = point.y - center.y
    const distanceSquared = dx * dx + dy * dy

    if (distanceSquared <= toleranceSquared) {
      selectedIndices.push(index)
    }
  })

  return selectedIndices
}

/**
 * Convert ECharts brush area to selection region
 */
export function convertBrushAreaToRegion(area: any): BrushRegion {
  const coordRange = area?.coordRange

  if (!coordRange || coordRange.length !== 2) {
    return {}
  }

  return {
    xMin: Math.min(coordRange[0][0], coordRange[1][0]),
    xMax: Math.max(coordRange[0][0], coordRange[1][0]),
    yMin: Math.min(coordRange[0][1], coordRange[1][1]),
    yMax: Math.max(coordRange[0][1], coordRange[1][1]),
  }
}

/**
 * Convert polygon coordinates to selection region (for lasso)
 */
export function convertPolygonToRegion(polygon: Point[]): BrushRegion {
  if (polygon.length === 0) return {}

  const xValues = polygon.map(p => p.x)
  const yValues = polygon.map(p => p.y)

  return {
    xMin: Math.min(...xValues),
    xMax: Math.max(...xValues),
    yMin: Math.min(...yValues),
    yMax: Math.max(...yValues),
  }
}

/**
 * Create selection event from selection data
 */
export function createSelectionEvent(
  mode: SelectionMode,
  indices: number[],
  coordinates?: Point[],
  brushRegion?: BrushRegion
): SelectionEvent {
  return {
    type: mode,
    indices,
    coordinates,
    brushRegion,
    timestamp: Date.now(),
  }
}

/**
 * Selection Service class for managing selection state
 */
export class SelectionService {
  private selectedIndices: Set<number> = new Set()
  private selectionMode: SelectionMode = 'box'

  constructor(mode: SelectionMode = 'box') {
    this.selectionMode = mode
  }

  setMode(mode: SelectionMode): void {
    this.selectionMode = mode
  }

  getMode(): SelectionMode {
    return this.selectionMode
  }

  getSelectedIndices(): number[] {
    return Array.from(this.selectedIndices)
  }

  getSelectedCount(): number {
    return this.selectedIndices.size
  }

  select(indices: number[], additive: boolean = false): void {
    if (!additive) {
      this.selectedIndices.clear()
    }
    indices.forEach(i => this.selectedIndices.add(i))
  }

  deselect(indices: number[]): void {
    indices.forEach(i => this.selectedIndices.delete(i))
  }

  toggle(indices: number[]): void {
    indices.forEach(i => {
      if (this.selectedIndices.has(i)) {
        this.selectedIndices.delete(i)
      } else {
        this.selectedIndices.add(i)
      }
    })
  }

  clear(): void {
    this.selectedIndices.clear()
  }

  selectAll(allIndices: number[]): void {
    this.selectedIndices = new Set(allIndices)
  }

  isSelected(index: number): boolean {
    return this.selectedIndices.has(index)
  }

  selectBox(points: Point[], region: BrushRegion): void {
    const indices = detectBoxSelection(points, region)
    this.select(indices)
  }

  selectLasso(points: Point[], polygon: Point[]): void {
    const indices = detectLassoSelection(points, polygon)
    this.select(indices)
  }

  selectProximity(points: Point[], center: Point, tolerance?: number): void {
    const indices = detectProximitySelection(points, center, tolerance)
    this.toggle(indices)
  }

  getEvent(brushRegion?: BrushRegion): SelectionEvent {
    return createSelectionEvent(
      this.selectionMode,
      this.getSelectedIndices(),
      undefined,
      brushRegion
    )
  }
}

/**
 * Create a new SelectionService instance
 */
export function createSelectionService(mode: SelectionMode = 'box'): SelectionService {
  return new SelectionService(mode)
}

/**
 * Convert data points to Point array for selection detection
 */
export function dataToPoints(
  data: { x: number; y: number }[]
): Point[] {
  return data.map(d => ({ x: d.x, y: d.y }))
}