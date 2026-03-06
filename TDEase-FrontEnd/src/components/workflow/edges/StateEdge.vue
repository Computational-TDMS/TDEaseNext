<template>
  <svg class="state-edge-svg" style="overflow: visible">
    <g class="state-edge-group">
      <!-- Main edge line -->
      <path
        :d="path"
        fill="none"
        stroke="#f59f00"
        stroke-width="2"
        stroke-dasharray="5,5"
        class="state-edge-path"
      />

      <!-- Animated flow indicator for active state propagation -->
      <circle
        v-if="isActive"
        r="4"
        fill="#f59f00"
        class="state-edge-flow"
      >
        <animateMotion
          :dur="animationDuration + 's'"
          repeatCount="indefinite"
          :path="path"
        />
      </circle>

      <!-- Edge label -->
      <text
        v-if="showLabel"
        :x="labelPosition.x"
        :y="labelPosition.y"
        class="state-edge-label"
        text-anchor="middle"
        font-size="10"
        fill="#f59f00"
      >
        {{ label }}
      </text>
    </g>
  </svg>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { getBezierPath, getStraightPath, type EdgeProps } from '@vue-flow/core'

interface StateEdgeProps extends Omit<EdgeProps, 'data'> {
  data: {
    semanticType?: string
    active?: boolean
  }
}

const props = withDefaults(defineProps<StateEdgeProps>(), {
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

// Check if edge is actively propagating state
const isActive = computed(() => props.data?.active ?? false)

// Calculate actual path length using euclidean distance as approximation
// For bezier curves, actual length is typically 1.2-1.5x the straight-line distance
const pathLength = computed(() => {
  const dx = props.targetX - props.sourceX
  const dy = props.targetY - props.sourceY
  const straightDistance = Math.hypot(dx, dy)
  // Approximate bezier path length as 1.3x straight distance (typical for bezier curves)
  return straightDistance * 1.3
})

// Animation duration based on actual path length (in pixels)
// Scale: 1-3 seconds for paths 0-600px long
const animationDuration = computed(() => {
  const length = pathLength.value
  // Scale duration: 1s for 0px, 3s for 600px+
  return Math.max(1, Math.min(3, length / 200))
})

// Show label for semantic type
const showLabel = computed(() => {
  return props.data?.semanticType && props.data.semanticType.startsWith('state/')
})

const label = computed(() => {
  const semanticType = props.data?.semanticType || ''
  if (semanticType === 'state/selection_ids') return 'Selection'
  if (semanticType === 'state/range') return 'Range'
  if (semanticType === 'state/viewport') return 'Viewport'
  if (semanticType === 'state/annotation') return 'Annotation'
  if (semanticType === 'state/sequence') return 'Sequence'
  return 'State'
})

// Use labelX and labelY from path utility (center of path), fallback to midpoint
const labelPosition = computed(() => {
  if (typeof labelX.value === 'number' && typeof labelY.value === 'number') {
    return { x: labelX.value, y: labelY.value - 10 }
  }
  // Fallback to midpoint if labelX/labelY not available
  return {
    x: (props.sourceX + props.targetX) / 2,
    y: (props.sourceY + props.targetY) / 2 - 10
  }
})
</script>

<style scoped>
.state-edge-svg {
  overflow: visible;
}

.state-edge-group {
  pointer-events: stroke;
  cursor: pointer;
}

.state-edge-path {
  transition: stroke-width 0.2s ease;
  shape-rendering: geometricPrecision;
}

.state-edge-path:hover {
  stroke-width: 3;
}

.state-edge-flow {
  filter: drop-shadow(0 0 2px rgba(245, 159, 0, 0.6));
}

.state-edge-label {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-weight: 500;
  pointer-events: none;
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8);
}
</style>
