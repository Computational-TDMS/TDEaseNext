import { onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'

export interface KeyboardShortcut {
  key: string
  ctrlKey?: boolean
  altKey?: boolean
  shiftKey?: boolean
  description: string
  action: () => void | Promise<void>
}

export function useKeyboardShortcuts(shortcuts: KeyboardShortcut[]) {
  let isEnabled = true

  const handleKeyDown = async (event: KeyboardEvent) => {
    if (!isEnabled) return

    // 忽略在输入框中的按键
    const target = event.target as HTMLElement
    if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.contentEditable === 'true') {
      return
    }

    // 查找匹配的快捷键
    const matchedShortcut = shortcuts.find(shortcut => {
      const keyMatches = shortcut.key.toLowerCase() === event.key.toLowerCase()
      const ctrlMatches = !!shortcut.ctrlKey === event.ctrlKey
      const altMatches = !!shortcut.altKey === event.altKey
      const shiftMatches = !!shortcut.shiftKey === event.shiftKey

      return keyMatches && ctrlMatches && altMatches && shiftMatches
    })

    if (matchedShortcut) {
      event.preventDefault()
      try {
        await matchedShortcut.action()
      } catch (error) {
        console.error('Error executing keyboard shortcut:', error)
        ElMessage.error(`快捷键执行失败: ${matchedShortcut.description}`)
      }
    }
  }

  const enable = () => {
    isEnabled = true
  }

  const disable = () => {
    isEnabled = false
  }

  onMounted(() => {
    document.addEventListener('keydown', handleKeyDown)
  })

  onUnmounted(() => {
    document.removeEventListener('keydown', handleKeyDown)
  })

  return {
    enable,
    disable
  }
}