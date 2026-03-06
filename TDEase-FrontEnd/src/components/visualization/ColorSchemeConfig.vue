<template>
  <div class="color-scheme-config">
    <el-form label-position="top" size="small">
      <!-- Predefined Schemes -->
      <el-form-item label="Color Scheme">
        <el-radio-group v-model="localSchemeId" @change="handleSchemeChange">
          <el-radio-button v-for="scheme in schemes" :key="scheme.id" :value="scheme.id">
            <span class="scheme-label">{{ scheme.name }}</span>
            <span class="scheme-type">{{ scheme.type }}</span>
          </el-radio-button>
        </el-radio-group>
      </el-form-item>

      <!-- Color Preview -->
      <el-form-item label="Preview">
        <div class="color-preview">
          <div
            v-for="(color, idx) in currentSchemeColors"
            :key="idx"
            class="color-block"
            :style="{ backgroundColor: color }"
            :title="color"
          />
        </div>
      </el-form-item>

      <!-- Custom Colors (when 'custom' is selected) -->
      <template v-if="localSchemeId === 'custom'">
        <el-divider content-position="left">Custom Colors</el-divider>
        
        <el-form-item label="Custom Color Palette">
          <div class="custom-colors">
            <el-color-picker
              v-for="(_, idx) in localCustomColors"
              :key="idx"
              v-model="localCustomColors[idx]"
              show-alpha
              @change="handleCustomChange"
            />
            <el-button size="small" :icon="Plus" circle @click="addCustomColor" />
            <el-button 
              v-if="localCustomColors.length > 2" 
              size="small" 
              :icon="Minus" 
              circle 
              @click="removeCustomColor" 
            />
          </div>
        </el-form-item>
      </template>

      <!-- Color Scheme Info -->
      <el-form-item v-if="selectedScheme">
        <div class="scheme-info">
          <el-tag :type="schemeTypeTag" size="small">{{ selectedScheme.type }}</el-tag>
          <span class="scheme-desc">{{ selectedScheme.description }}</span>
        </div>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Plus, Minus } from '@element-plus/icons-vue'
import type { ColorSchemeId, ColorScheme } from '@/types/visualization'
import { COLOR_SCHEMES } from '@/types/visualization'

interface Props {
  modelValue?: ColorSchemeId | string
  customColors?: string[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [schemeId: ColorSchemeId]
  'update:customColors': [colors: string[]]
  change: [scheme: ColorScheme | { id: ColorSchemeId; colors: string[] }]
}>()

const schemes = COLOR_SCHEMES

const localSchemeId = ref<ColorSchemeId>('viridis')
const localCustomColors = ref<string[]>(['#000000', '#ffffff', '#ff0000'])

// Initialize from props
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    localSchemeId.value = newVal as ColorSchemeId
  }
}, { immediate: true })

watch(() => props.customColors, (newVal) => {
  if (newVal && newVal.length > 0) {
    localCustomColors.value = [...newVal]
  }
}, { immediate: true })

// Computed
const selectedScheme = computed(() => schemes.find(s => s.id === localSchemeId.value))

const currentSchemeColors = computed(() => {
  if (localSchemeId.value === 'custom') {
    return localCustomColors.value
  }
  return selectedScheme.value?.colors || schemes[0].colors
})

const schemeTypeTag = computed(() => {
  const type = selectedScheme.value?.type
  if (type === 'sequential') return 'success'
  if (type === 'diverging') return 'warning'
  return 'info'
})

// Methods
function handleSchemeChange() {
  emit('update:modelValue', localSchemeId.value)
  emit('change', {
    id: localSchemeId.value,
    colors: currentSchemeColors.value,
  })
}

function handleCustomChange() {
  emit('update:customColors', [...localCustomColors.value])
  emit('change', {
    id: 'custom' as ColorSchemeId,
    colors: localCustomColors.value,
  })
}

function addCustomColor() {
  if (localCustomColors.value.length < 10) {
    const lastColor = localCustomColors.value[localCustomColors.value.length - 1]
    localCustomColors.value.push(lastColor || '#000000')
    handleCustomChange()
  }
}

function removeCustomColor() {
  if (localCustomColors.value.length > 2) {
    localCustomColors.value.pop()
    handleCustomChange()
  }
}
</script>

<style scoped>
.color-scheme-config {
  padding: 12px;
}

.color-scheme-config :deep(.el-form-item) {
  margin-bottom: 16px;
}

.color-scheme-config :deep(.el-form-item__label) {
  font-size: 12px;
  color: #606266;
}

.color-scheme-config :deep(.el-radio-group) {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.color-scheme-config :deep(.el-radio-button) {
  margin: 0;
}

.scheme-label {
  font-size: 12px;
}

.scheme-type {
  font-size: 10px;
  opacity: 0.7;
  margin-left: 4px;
}

.color-preview {
  display: flex;
  height: 24px;
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid #dcdfe6;
}

.color-block {
  flex: 1;
  min-width: 20px;
  cursor: pointer;
  transition: transform 0.1s;
}

.color-block:hover {
  transform: scaleY(1.2);
}

.custom-colors {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.scheme-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #909399;
}

.scheme-desc {
  color: #606266;
}
</style>
