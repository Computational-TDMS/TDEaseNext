import { ref, type Ref, onUnmounted } from 'vue'

export interface UseFullscreenReturn {
  isFullscreen: Ref<boolean>
  toggleFullscreen: (element?: HTMLElement) => void
  enterFullscreen: (element?: HTMLElement) => void
  exitFullscreen: () => void
  isSupported: Ref<boolean>
}

export function useFullscreen(): UseFullscreenReturn {
  const isFullscreen = ref(false)

  const isSupported = ref(typeof document !== 'undefined' && !!(
    document.fullscreenEnabled ||
    (document as any).webkitFullscreenEnabled ||
    (document as any).mozFullScreenEnabled ||
    (document as any).msFullscreenEnabled
  ))

  const getFullscreenElement = (): Element | null => {
    return document.fullscreenElement ||
      (document as any).webkitFullscreenElement ||
      (document as any).mozFullScreenElement ||
      (document as any).msFullscreenElement ||
      null
  }

  const enterFullscreen = (element?: HTMLElement) => {
    const targetElement = element || document.documentElement

    if (!isSupported.value) {
      console.warn('[useFullscreen] Fullscreen API not supported')
      return
    }

    try {
      if (targetElement.requestFullscreen) {
        targetElement.requestFullscreen()
      } else if ((targetElement as any).webkitRequestFullscreen) {
        (targetElement as any).webkitRequestFullscreen()
      } else if ((targetElement as any).mozRequestFullScreen) {
        (targetElement as any).mozRequestFullScreen()
      } else if ((targetElement as any).msRequestFullscreen) {
        (targetElement as any).msRequestFullscreen()
      }
    } catch (error) {
      console.error('[useFullscreen] Error entering fullscreen:', error)
    }
  }

  const exitFullscreen = () => {
    if (!isSupported.value) {
      console.warn('[useFullscreen] Fullscreen API not supported')
      return
    }

    try {
      if (document.exitFullscreen) {
        document.exitFullscreen()
      } else if ((document as any).webkitExitFullscreen) {
        (document as any).webkitExitFullscreen()
      } else if ((document as any).mozCancelFullScreen) {
        (document as any).mozCancelFullScreen()
      } else if ((document as any).msExitFullscreen) {
        (document as any).msExitFullscreen()
      }
    } catch (error) {
      console.error('[useFullscreen] Error exiting fullscreen:', error)
    }
  }

  const toggleFullscreen = (element?: HTMLElement) => {
    if (isFullscreen.value) {
      exitFullscreen()
    } else {
      enterFullscreen(element)
    }
  }

  const handleFullscreenChange = () => {
    isFullscreen.value = getFullscreenElement() !== null
  }

  // Listen for fullscreen changes
  document.addEventListener('fullscreenchange', handleFullscreenChange)
  document.addEventListener('webkitfullscreenchange', handleFullscreenChange)
  document.addEventListener('mozfullscreenchange', handleFullscreenChange)
  document.addEventListener('MSFullscreenChange', handleFullscreenChange)

  onUnmounted(() => {
    document.removeEventListener('fullscreenchange', handleFullscreenChange)
    document.removeEventListener('webkitfullscreenchange', handleFullscreenChange)
    document.removeEventListener('mozfullscreenchange', handleFullscreenChange)
    document.removeEventListener('MSFullscreenChange', handleFullscreenChange)
  })

  return {
    isFullscreen,
    toggleFullscreen,
    enterFullscreen,
    exitFullscreen,
    isSupported
  }
}
