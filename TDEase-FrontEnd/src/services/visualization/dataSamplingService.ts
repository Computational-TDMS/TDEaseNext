/**
 * Data Sampling Service - Handles large dataset sampling and performance optimization
 * 
 * Provides utilities for:
 * - Random sampling
 * - Stratified sampling
 * - Nth-point sampling
 * - Density-based sampling
 * - Performance monitoring
 */

import type { SamplingConfig, PerformanceState } from '@/types/visualization'

export interface SamplingResult {
  data: any[]
  sampledSize: number
  originalSize: number
  samplingApplied: boolean
  method: SamplingConfig['method']
}

/**
 * Random sampling - randomly select n points from the dataset
 */
export function randomSampling(
  data: any[],
  sampleSize: number
): SamplingResult {
  const originalSize = data.length

  if (data.length <= sampleSize) {
    return {
      data,
      sampledSize: data.length,
      originalSize,
      samplingApplied: false,
      method: 'random',
    }
  }

  const shuffled = [...data]
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }

  return {
    data: shuffled.slice(0, sampleSize),
    sampledSize: sampleSize,
    originalSize,
    samplingApplied: true,
    method: 'random',
  }
}

/**
 * Nth-point sampling - select every nth point from the dataset
 * Preserves data distribution along the order
 */
export function nthSampling(
  data: any[],
  sampleSize: number
): SamplingResult {
  const originalSize = data.length

  if (data.length <= sampleSize) {
    return {
      data,
      sampledSize: data.length,
      originalSize,
      samplingApplied: false,
      method: 'nth',
    }
  }

  const step = Math.ceil(data.length / sampleSize)
  const sampled = data.filter((_, index) => index % step === 0).slice(0, sampleSize)

  return {
    data: sampled,
    sampledSize: sampled.length,
    originalSize,
    samplingApplied: sampled.length < originalSize,
    method: 'nth',
  }
}

/**
 * Stratified sampling - divide data into groups and sample from each
 * Maintains representation from each group
 */
export function stratifiedSampling(
  data: any[],
  sampleSize: number,
  groupBy: (item: any) => string | number
): SamplingResult {
  const originalSize = data.length

  if (data.length <= sampleSize) {
    return {
      data,
      sampledSize: data.length,
      originalSize,
      samplingApplied: false,
      method: 'stratified',
    }
  }

  // Group data
  const groups = new Map<string | number, any[]>()
  data.forEach(item => {
    const key = groupBy(item)
    if (!groups.has(key)) {
      groups.set(key, [])
    }
    groups.get(key)!.push(item)
  })

  // Calculate samples per group
  const groupCount = groups.size
  const samplesPerGroup = Math.floor(sampleSize / groupCount)
  const remainder = sampleSize % groupCount

  const sampled: any[] = []
  let groupIndex = 0

  groups.forEach((groupData) => {
    // Distribute remainder samples to first groups
    let groupSampleCount = samplesPerGroup
    if (groupIndex < remainder) {
      groupSampleCount++
    }

    if (groupData.length <= groupSampleCount) {
      sampled.push(...groupData)
    } else {
      // Random sample within group
      const shuffled = [...groupData]
      for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1))
        ;[shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
      }
      sampled.push(...shuffled.slice(0, groupSampleCount))
    }

    groupIndex++
  })

  return {
    data: sampled,
    sampledSize: sampled.length,
    originalSize,
    samplingApplied: sampled.length < originalSize,
    method: 'stratified',
  }
}

/**
 * Density-based sampling - sample more points from dense regions
 * Good for preserving local structure in scatter plots
 */
export function densitySampling(
  data: any[],
  sampleSize: number,
  getPosition: (item: any) => { x: number; y: number },
  gridSize: number = 50
): SamplingResult {
  const originalSize = data.length

  if (data.length <= sampleSize) {
    return {
      data,
      sampledSize: data.length,
      originalSize,
      samplingApplied: false,
      method: 'density',
    }
  }

  // Calculate bounds
  let minX = Infinity, maxX = -Infinity
  let minY = Infinity, maxY = -Infinity

  data.forEach(item => {
    const pos = getPosition(item)
    if (pos.x < minX) minX = pos.x
    if (pos.x > maxX) maxX = pos.x
    if (pos.y < minY) minY = pos.y
    if (pos.y > maxY) maxY = pos.y
  })

  // Create grid and count density
  const cellWidth = (maxX - minX) / gridSize
  const cellHeight = (maxY - minY) / gridSize

  const grid = new Map<string, number[]>()

  data.forEach((item, index) => {
    const pos = getPosition(item)
    const cellX = Math.min(Math.floor((pos.x - minX) / cellWidth), gridSize - 1)
    const cellY = Math.min(Math.floor((pos.y - minY) / cellHeight), gridSize - 1)
    const cellKey = `${cellX},${cellY}`

    if (!grid.has(cellKey)) {
      grid.set(cellKey, [])
    }
    grid.get(cellKey)!.push(index)
  })

  // Sample from each cell proportionally
  const sampledIndices: number[] = []
  const targetPerCell = sampleSize / grid.size

  grid.forEach(indices => {
    if (indices.length <= targetPerCell) {
      sampledIndices.push(...indices)
    } else {
      const shuffled = [...indices]
      for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1))
        ;[shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
      }
      sampledIndices.push(...shuffled.slice(0, Math.ceil(targetPerCell)))
    }
  })

  return {
    data: sampledIndices.map(i => data[i]),
    sampledSize: sampledIndices.length,
    originalSize,
    samplingApplied: sampledIndices.length < originalSize,
    method: 'density',
  }
}

/**
 * Apply sampling based on configuration
 */
export function applySampling(
  data: any[],
  config: SamplingConfig,
  getPosition?: (item: any) => { x: number; y: number },
  groupBy?: (item: any) => string | number
): SamplingResult {
  if (!config.enabled || data.length <= config.sampleSize) {
    return {
      data,
      sampledSize: data.length,
      originalSize: data.length,
      samplingApplied: false,
      method: config.method,
    }
  }

  switch (config.method) {
    case 'random':
      return randomSampling(data, config.sampleSize)

    case 'nth':
      return nthSampling(data, config.sampleSize)

    case 'stratified':
      if (groupBy) {
        return stratifiedSampling(data, config.sampleSize, groupBy)
      }
      return randomSampling(data, config.sampleSize)

    case 'density':
      if (getPosition) {
        return densitySampling(data, config.sampleSize, getPosition)
      }
      return randomSampling(data, config.sampleSize)

    default:
      return randomSampling(data, config.sampleSize)
  }
}

/**
 * Monitor performance and suggest sampling
 */
export function calculatePerformanceState(
  dataSize: number,
  renderedPoints: number,
  config?: SamplingConfig
): PerformanceState {
  const state: PerformanceState = {
    dataSize,
    renderedPoints,
    samplingApplied: renderedPoints < dataSize,
  }

  // Estimate memory usage (rough estimate)
  // Assuming average row is ~1KB
  state.memoryUsage = dataSize * 1024

  // Check if sampling is needed
  if (config) {
    state.samplingApplied = dataSize > config.threshold
  } else {
    state.samplingApplied = dataSize > 10000
  }

  return state
}

/**
 * Get recommended sampling configuration based on data size
 */
export function getRecommendedSamplingConfig(dataSize: number): SamplingConfig {
  const threshold = 10000

  if (dataSize <= threshold) {
    return {
      enabled: false,
      method: 'random',
      sampleSize: dataSize,
      threshold,
    }
  }

  // Use density sampling for scatter-like data
  // Use random for others
  return {
    enabled: true,
    method: 'density',
    sampleSize: Math.min(10000, dataSize),
    threshold,
  }
}

/**
 * Calculate optimal sample size based on viewport dimensions
 */
export function calculateOptimalSampleSize(
  viewportWidth: number,
  viewportHeight: number,
  pixelRatio: number = 2
): number {
  const pixels = viewportWidth * viewportHeight * pixelRatio
  // Assume each point takes about 4x4 pixels on average
  const maxPoints = Math.floor(pixels / 16)
  return Math.min(maxPoints, 10000)
}
