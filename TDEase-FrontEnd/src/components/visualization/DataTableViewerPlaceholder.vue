<template>
  <div class="data-table-viewer-placeholder">
    <div class="placeholder-content">
      <span class="placeholder-icon">📊</span>
      <p class="placeholder-title">数据表格查看器 (AG-Grid)</p>
      <p class="placeholder-desc">此处为占位组件，后续将接入 AG-Grid 或等效表格组件用于展示 TSV/CSV 等表格数据。</p>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 8.4 Data table viewer architecture placeholder
 * Future: integrate AG-Grid or similar for tabular data display.
 */
</script>

<style scoped>
.data-table-viewer-placeholder {
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  border: 1px dashed #dcdfe6;
  border-radius: 8px;
  padding: 24px;
}

.placeholder-content {
  text-align: center;
  color: #606266;
}

.placeholder-icon {
  font-size: 32px;
  display: block;
  margin-bottom: 8px;
}

.placeholder-title {
  font-weight: 600;
  font-size: 14px;
  margin: 0 0 4px 0;
  color: #303133;
}

.placeholder-desc {
  font-size: 12px;
  margin: 0;
  max-width: 280px;
  line-height: 1.5;
}
</style>
