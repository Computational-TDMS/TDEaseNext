import { ref, computed, onMounted, onUnmounted } from 'vue'

export type NodeTheme = 'light' | 'dark' | 'glass'
export type NodeStatus = 'idle' | 'running' | 'success' | 'error'

export interface NodeThemeConfig {
  mode: NodeTheme
  primaryColor: string
  backgroundColor: string
  borderColor: string
  textColor: string
  headerBackground: string
  headerTextColor: string
  shadow: string
  backdropBlur?: number
}

const themePresets: Record<NodeTheme, NodeThemeConfig> = {
  light: {
    mode: 'light',
    primaryColor: '#409eff',
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderColor: '#409eff',
    textColor: '#303133',
    headerBackground: '#409eff',
    headerTextColor: '#ffffff',
    shadow: '0 4px 12px rgba(0, 0, 0, 0.12)'
  },
  dark: {
    mode: 'dark',
    primaryColor: '#409eff',
    backgroundColor: 'rgba(48, 54, 61, 0.95)',
    borderColor: '#409eff',
    textColor: '#e5eaf3',
    headerBackground: '#1f1f1f',
    headerTextColor: '#ffffff',
    shadow: '0 4px 16px rgba(0, 0, 0, 0.4)'
  },
  glass: {
    mode: 'glass',
    primaryColor: '#409eff',
    backgroundColor: 'rgba(255, 255, 255, 0.7)',
    borderColor: '#409eff',
    textColor: '#303133',
    headerBackground: 'rgba(64, 158, 255, 0.9)',
    headerTextColor: '#ffffff',
    shadow: '0 8px 32px rgba(0, 0, 0, 0.15)',
    backdropBlur: 8
  }
}

export function useNodeThemes(initialTheme: NodeTheme = 'glass') {
  const currentTheme = ref<NodeTheme>(initialTheme)

  const config = computed(() => themePresets[currentTheme.value])

  const setTheme = (theme: NodeTheme) => {
    currentTheme.value = theme
  }

  const getStatusColor = (status: NodeStatus): string => {
    const statusColors: Record<NodeStatus, string> = {
      idle: '#909399',
      running: '#409eff',
      success: '#67c23a',
      error: '#f56c6c'
    }
    return statusColors[status]
  }

  const getPortColor = (type: string): string => {
    const colorMap: Record<string, string> = {
      data: '#67c23a',
      file: '#409eff',
      string: '#e6a23c',
      number: '#f56c6c',
      boolean: '#909399',
      select: '#3742fa',
      multiselect: '#e6a23c'
    }
    return colorMap[type] || '#606266'
  }

  return {
    currentTheme,
    config,
    setTheme,
    getStatusColor,
    getPortColor,
    themePresets
  }
}

export function useSystemTheme() {
  const isDarkMode = ref(false)

  const updateTheme = () => {
    isDarkMode.value = window.matchMedia('(prefers-color-scheme: dark)').matches
  }

  onMounted(() => {
    updateTheme()
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    mediaQuery.addEventListener('change', updateTheme)
  })

  onUnmounted(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    mediaQuery.removeEventListener('change', updateTheme)
  })

  const theme = computed(() => (isDarkMode.value ? 'dark' : 'light'))

  return {
    isDarkMode,
    theme
  }
}

export function useGlassmorphism(enabled = true) {
  const blurAmount = ref(enabled ? 8 : 0)
  const opacity = ref(enabled ? 0.7 : 1)

  const setEnabled = (value: boolean) => {
    blurAmount.value = value ? 8 : 0
    opacity.value = value ? 0.7 : 1
  }

  const glassStyle = computed(() => ({
    backdropFilter: `blur(${blurAmount.value}px)`,
    WebkitBackdropFilter: `blur(${blurAmount.value}px)`,
    backgroundColor: `rgba(255, 255, 255, ${opacity.value})`
  }))

  return {
    blurAmount,
    opacity,
    setEnabled,
    glassStyle
  }
}
