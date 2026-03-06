<template>
  <div class="node-body" :class="[`layout-${layout}`, `gap-${gap}`]">
    <slot />
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  layout?: 'flex' | 'grid' | 'row' | 'column'
  gap?: 'none' | 'small' | 'medium' | 'large'
  align?: 'start' | 'center' | 'end' | 'stretch'
  justify?: 'start' | 'center' | 'end' | 'between' | 'around'
}>(), {
  layout: 'flex',
  gap: 'medium',
  align: 'stretch',
  justify: 'start'
})
</script>

<style scoped>
.node-body {
  display: flex;
  padding: 12px;
  flex: 1 0 auto;
}

.layout-flex,
.layout-row {
  flex-direction: row;
  align-items: v-bind(align);
  justify-content: v-bind(justify);
}

.layout-column {
  flex-direction: column;
  align-items: v-bind(align);
}

.layout-grid {
  display: grid;
  gap: v-bind(gap);
  align-items: v-bind(align);
}

.gap-none {
  gap: 0;
}

.gap-small {
  gap: 6px;
}

.gap-medium {
  gap: 12px;
}

.gap-large {
  gap: 20px;
}
</style>