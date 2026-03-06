<template>
  <div
    class="node-container"
    :class="{
      'is-selected': selected,
      'is-dragging': dragging,
      'is-hovered': isHovered
    }"
    :style="containerStyle"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
  >
    <slot />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

const props = withDefaults(defineProps<{
  selected?: boolean
  dragging?: boolean
  color?: string
  width?: number | string
  minHeight?: number | string
}>(), {
  selected: false,
  dragging: false,
  width: 240,
  minHeight: 80
})

const emit = defineEmits<{
  (e: 'hover', value: boolean): void
}>()

const isHovered = ref(false)

const containerStyle = computed(() => ({
  width: typeof props.width === 'number' ? `${props.width}px` : props.width,
  minHeight: typeof props.minHeight === 'number' ? `${props.minHeight}px` : props.minHeight,
  borderColor: props.color || '#409eff'
}))

const handleMouseEnter = () => {
  isHovered.value = true
  emit('hover', true)
}

const handleMouseLeave = () => {
  isHovered.value = false
  emit('hover', false)
}
</script>

<style scoped>
.node-container {
  position: relative;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 2px solid v-bind('props.color || "#409eff"');
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  overflow: hidden;
  transition: all 0.2s ease-in-out;
  display: flex;
  flex-direction: column;
}

.node-container:hover {
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.18);
  transform: translateY(-1px);
}

.node-container.is-selected {
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.4), 0 6px 20px rgba(0, 0, 0, 0.18);
}

.node-container.is-dragging {
  opacity: 0.9;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
}

.node-container.is-hovered:not(.is-selected) {
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.25), 0 6px 16px rgba(0, 0, 0, 0.15);
}

/* Vue Flow 节点样式覆盖 */
:global(.vue-flow__node) {
  border: none !important;
  background: transparent !important;
  padding: 0 !important;
}

:global(.vue-flow__node.selected) {
  box-shadow: none !important;
}
</style>