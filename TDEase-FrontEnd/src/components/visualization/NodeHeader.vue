<template>
  <div class="node-header">
    <div class="node-title">
      <el-icon v-if="loading" class="is-loading"><Loading /></el-icon>
      <el-icon v-else-if="error"><Warning /></el-icon>
      <el-icon v-else-if="pendingExecution"><Clock /></el-icon>
      <el-icon v-else><View /></el-icon>
      <span>{{ label }}</span>
      <el-tag v-if="visualizationType" size="small" type="info" style="margin-left: 8px">
        {{ visualizationType }}
      </el-tag>
    </div>
    <div class="node-actions">
      <el-button
        size="small"
        :type="isEditMode ? 'success' : 'default'"
        :icon="Edit"
        @click="$emit('toggleEditMode')"
        circle
        title="Toggle Edit Mode"
      />
      <el-button
        v-if="error"
        size="small"
        type="primary"
        :icon="Refresh"
        @click="$emit('retry')"
        circle
      />
      <el-button
        size="small"
        type="info"
        :icon="FullScreen"
        @click="$emit('toggleFullscreen')"
        circle
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Loading, Warning, Clock, View, Edit, Refresh, FullScreen } from '@element-plus/icons-vue'

interface Props {
  label: string
  visualizationType?: string
  loading?: boolean
  error?: boolean
  pendingExecution?: boolean
  isEditMode?: boolean
}

defineProps<Props>()
defineEmits<{
  toggleEditMode: []
  retry: []
  toggleFullscreen: []
}>()
</script>

<script lang="ts">
export default {
  name: 'NodeHeader'
}
</script>

<style scoped>
.node-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 8px 8px 0 0;
}

.node-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 14px;
}

.node-title .el-icon {
  font-size: 18px;
}

.node-actions {
  display: flex;
  gap: 8px;
}

.node-actions .el-button {
  border: none;
}
</style>
