<template>
  <svg class="data-edge-svg" style="overflow: visible">
    <g class="data-edge-group">
      <!-- Main edge line -->
      <path
        :d="path"
        fill="none"
        stroke="#409eff"
        stroke-width="2"
        class="data-edge-path"
      />

      <!-- Edge label -->
      <text
        v-if="showLabel"
        :x="labelPosition.x"
        :y="labelPosition.y"
        class="data-edge-label"
        text-anchor="middle"
        font-size="10"
        fill="#409eff"
      >
        {{ label }}
      </text>
    </g>
  </svg>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { getBezierPath, getStraightPath, type EdgeProps } from '@vue-flow/core'

interface DataEdgeProps extends Omit<EdgeProps, 'data'> {
  data: {
    dataType?: string
  }
}

const props = withDefaults(defineProps<DataEdgeProps>(), {
  data: () => ({})
})

// Check if source and target are horizontally or vertically aligned (degenerate case)
const isDegenerate = computed(() => {
  const dx = Math.abs(props.targetX - props.sourceX)
  const dy = Math.abs(props.targetY - props.sourceY)
  // If aligned horizontally or vertically (within 1px tolerance)
  return dx < 1 || dy < 1
})

// Calculate path - use straight path for degenerate cases, bezier otherwise
const pathParams = computed(() => {
  if (isDegenerate.value) {
    return getStraightPath(props)
  }
  return getBezierPath(props)
})

// Extract path and label positions from path utility function (keep as computed for reactivity)
const path = computed(() => pathParams.value[0])
const labelX = computed(() => pathParams.value[1])
const labelY = computed(() => pathParams.value[2])

// Show label for data type
const showLabel = computed(() => {
  return !!props.data?.dataType
})

const label = computed(() => {
  const dataType = props.data?.dataType || ''
  if (dataType === 'file') return 'Data'
  if (dataType === 'table') return 'Table'
  if (dataType === 'feature') return 'Feature'
  if (dataType === 'prsm') return 'PrSM'
  if (dataType === 'spectrum') return 'Spectrum'
  if (dataType === 'html') return 'HTML'
  return dataType.charAt(0).toUpperCase() + dataType.slice(1)
})

// Use labelX and labelY from path utility (center of path), fallback to midpoint
const labelPosition = computed(() => {
  if (typeof labelX === 'number' && typeof labelY === 'number') {
    return { x: labelX, y: labelY - 10 }
  }
  // Fallback to midpoint if labelX/labelY not available
  return {
    x: (props.sourceX + props.targetX) / 2,
    y: (props.sourceY + props.targetY) / 2 - 10
  }
})
</script>

<style scoped>
.data-edge-svg {
  overflow: visible;
}

.data-edge-group {
  pointer-events: stroke;
  cursor: pointer;
}

.data-edge-path {
  transition: stroke-width 0.2s ease;
  shape-rendering: geometricPrecision;
}

.data-edge-path:hover {
  stroke-width: 3;
}

.data-edge-label {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-weight: 500;
  pointer-events: none;
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8);
}
</style>
