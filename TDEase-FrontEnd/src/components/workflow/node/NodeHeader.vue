<template>
  <div class="node-header" :style="{ backgroundColor: bgColor }">
    <div class="header-left">
      <div v-if="icon" class="header-icon">
        <el-icon :size="18">
          <component :is="icon" />
        </el-icon>
      </div>
      <div v-else class="header-icon fallback">
        {{ typeChar }}
      </div>
      <span class="header-title">{{ title }}</span>
    </div>
    <div class="header-right">
      <div v-if="status === 'running'" class="status-pulse"></div>
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

type NodeStatus = 'idle' | 'running' | 'success' | 'error'

const props = withDefaults(defineProps<{
  title: string
  color?: string
  icon?: object | string
  status?: NodeStatus
  type?: string
}>(), {
  title: 'Node',
  color: '#409eff',
  status: 'idle'
})

const bgColor = computed(() => props.color || '#409eff')

const typeChar = computed(() => {
  if (props.type) {
    return props.type.charAt(0).toUpperCase()
  }
  return props.title.charAt(0).toUpperCase()
})
</script>

<style scoped>
.node-header {
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  color: #fff;
  border-radius: 6px 6px 0 0;
  user-select: none;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.header-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.header-icon.fallback {
  width: 22px;
  height: 22px;
  background: rgba(255, 255, 255, 0.25);
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
}

.header-title {
  font-weight: 600;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-pulse {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 0 8px 2px rgba(255, 255, 255, 0.8);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
    box-shadow: 0 0 8px 2px rgba(255, 255, 255, 0.8);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.15);
    box-shadow: 0 0 12px 4px rgba(255, 255, 255, 0.5);
  }
}
</style>