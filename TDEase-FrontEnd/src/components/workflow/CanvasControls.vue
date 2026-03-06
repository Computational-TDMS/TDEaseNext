


<template>
  <div class="canvas-controls">
    <!-- 缩放控制 -->
    <div class="zoom-controls">
      <el-button
        circle
        size="small"
        :icon="ZoomOut"
        @click="handleZoomOut"
        :disabled="transform.scale <= 0.1"
        title="缩小 (Ctrl+-)"
      />
      <div class="zoom-level">
        {{ Math.round(transform.scale * 100) }}%
      </div>
      <el-button
        circle
        size="small"
        :icon="ZoomIn"
        @click="handleZoomIn"
        :disabled="transform.scale >= 5"
        title="放大 (Ctrl++)"
      />
      <el-button
        circle
        size="small"
        :icon="FullScreen"
        @click="handleFitToScreen"
        title="适应屏幕 (Ctrl+0)"
      />
    </div>

    <!-- 缩放滑块 -->
    <div class="zoom-slider">
      <el-slider
        v-model="zoomValue"
        :min="10"
        :max="500"
        :step="10"
        :show-tooltip="false"
        @change="handleZoomSlider"
      />
    </div>

    <!-- 视图控制 -->
    <div class="view-controls">
      <el-button
        circle
        size="small"
        :icon="RefreshLeft"
        @click="handleResetView"
        title="重置视图"
      />
      <el-button
        circle
        size="small"
        :icon="Pointer"
        @click="togglePanMode"
        :type="panMode ? 'primary' : 'default'"
        title="拖拽模式"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElButton, ElSlider } from 'element-plus'
import {
  ZoomIn,
  ZoomOut,
  FullScreen,
  RefreshLeft,
  Pointer
} from '@element-plus/icons-vue'

interface Props {
  transform: {
    scale: number
    translateX: number
    translateY: number
  }
}

const props = defineProps<Props>()

const emit = defineEmits<{
  zoomIn: []
  zoomOut: []
  zoom: [scale: number]
  resetZoom: []
  fitToScreen: []
  resetView: []
  togglePanMode: []
}>()

// 拖拽模式
const panMode = ref(false)

// 缩放值用于滑块
const zoomValue = computed({
  get: () => Math.round(props.transform.scale * 100),
  set: (value: number) => {
    emit('zoom', value / 100)
  }
})

// 缩放控制处理
const handleZoomIn = () => {
  emit('zoomIn')
}

const handleZoomOut = () => {
  emit('zoomOut')
}

const handleZoomSlider = (value: number | number[]) => {
  const v = Array.isArray(value) ? value[0] : value
  emit('zoom', v / 100)
}

const handleFitToScreen = () => {
  emit('fitToScreen')
}

const handleResetView = () => {
  emit('resetView')
}

const togglePanMode = () => {
  panMode.value = !panMode.value
  emit('togglePanMode')
}
</script>

<style scoped>
.canvas-controls {
  position: absolute;
  top: 16px;
  right: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  z-index: 100;
}

.zoom-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  background: white;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  padding: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.zoom-level {
  min-width: 50px;
  text-align: center;
  font-size: 12px;
  font-weight: 600;
  color: #606266;
}

.zoom-slider {
  background: white;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  padding: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  width: 120px;
}

.view-controls {
  display: flex;
  flex-direction: column;
  gap: 4px;
  background: white;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  padding: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
</style>
