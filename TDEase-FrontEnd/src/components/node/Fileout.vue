<template>
  <li class="io-item" :class="{ 'has-files': row.expected && row.expected.length > 0 }">
  <div class="io-content">
      <span class="io-name" :title="`${row.port.name || row.port.id} (${row.port.type || 'file'})`">
        {{ row.port.name || row.port.id }}
        <em v-if="row.port.required && (!row.expected || row.expected.length === 0)" style="color:#e6a23c; margin-left:6px; font-style: normal;">缺少输入文件</em>
      </span>
      
      <!-- 文件列表，每个文件都有独立的 Handle -->
      <div v-if="row.expected && row.expected.length" class="file-list">
        <div 
          v-for="(f, idx) in row.expected" 
          :key="`${row.port.id}-${idx}-${f}`" 
          class="file-pill"
          :style="{ position: 'relative' }"
        >
          <span class="file-name">{{ f }}</span>
          <!-- 文件级别的 Handle -->
          <Handle 
            type="source" 
            :position="Position.Right" 
            :id="`output-${row.port.id}__${idx}`"
            :class="['file-handle', portKindClass]"
            :style="{ 
              position: 'absolute',
              right: '-6px',
              top: '50%',
              transform: 'translateY(-50%)'
            }"
          />
        </div>
      </div>
    </div>
    
    <Handle 
      v-if="!(row.expected && row.expected.length)"
      type="source" 
      :position="Position.Right" 
      :id="`output-${row.port.id}`"
      :class="['port-handle', portKindClass]"
      :style="{ position: 'absolute', right: '-6px', top: '50%', transform: 'translateY(-50%)' }"
    />
  </li>
</template>

<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'
import { computed } from 'vue'
import type { PortRow } from './PortList.vue'

const props = defineProps<{ 
  row: PortRow
  nodeId: string 
}>()

const portKindClass = computed(() => {
  const kind = props.row.port?.portKind || 'data'
  return `port-kind-${kind}`
})
</script>

<style scoped>
.io-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 4px 0;
  position: relative;
  min-height: 28px;
}

.io-item.has-files {
  min-height: auto;
  padding-bottom: 8px;
}

.port-handle { z-index: 10; }

.io-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.io-name {
  font-size: 12px;
  color: #303133;
  background: #f5f7fa;
  padding: 4px 8px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
}

.file-pill {
  font-size: 11px;
  color: #606266;
  background: #fff;
  padding: 4px 20px 4px 8px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  position: relative;
  display: flex;
  align-items: center;
  min-height: 24px;
  transition: all 0.2s ease;
}

.file-pill:hover {
  background: #f5f7fa;
  border-color: #409eff;
}

.file-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-handle {
  z-index: 10;
}

.port-kind-state-in {
  background: #fff6e6 !important;
  border: 2px solid #f59f00 !important;
  border-radius: 3px !important;
}

.port-kind-state-out {
  background: #f59f00 !important;
  border: 2px solid #f59f00 !important;
  border-radius: 3px !important;
}
</style>
