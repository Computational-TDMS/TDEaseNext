import { ref, computed } from 'vue'

export interface HistoryState {
  nodes: any[]
  connections: any[]
  timestamp: number
}

export function useHistoryManager() {
  const history = ref<HistoryState[]>([])
  const currentIndex = ref(-1)
  const maxHistorySize = 50

  // 计算是否可以撤销/重做
  const canUndo = computed(() => currentIndex.value > 0)
  const canRedo = computed(() => currentIndex.value < history.value.length - 1)

  // 添加新状态到历史记录
  const pushState = (state: Omit<HistoryState, 'timestamp'>) => {
    const newState: HistoryState = {
      ...state,
      timestamp: Date.now()
    }

    // 如果当前不在历史记录的末尾，删除后面的所有记录
    if (currentIndex.value < history.value.length - 1) {
      history.value = history.value.slice(0, currentIndex.value + 1)
    }

    // 添加新状态
    history.value.push(newState)

    // 限制历史记录大小
    if (history.value.length > maxHistorySize) {
      history.value.shift()
    } else {
      currentIndex.value++
    }
  }

  // 获取当前状态
  const getCurrentState = (): HistoryState | null => {
    if (currentIndex.value >= 0 && currentIndex.value < history.value.length) {
      return history.value[currentIndex.value]
    }
    return null
  }

  // 撤销操作
  const undo = (): HistoryState | null => {
    if (canUndo.value) {
      currentIndex.value--
      return getCurrentState()
    }
    return null
  }

  // 重做操作
  const redo = (): HistoryState | null => {
    if (canRedo.value) {
      currentIndex.value++
      return getCurrentState()
    }
    return null
  }

  // 获取撤销操作的描述
  const getUndoDescription = (): string => {
    if (canUndo.value && currentIndex.value > 0) {
      const currentState = history.value[currentIndex.value]
      const previousState = history.value[currentIndex.value - 1]

      // 简单的状态变化检测
      if (currentState.nodes.length > previousState.nodes.length) {
        return '添加节点'
      } else if (currentState.nodes.length < previousState.nodes.length) {
        return '删除节点'
      } else if (currentState.connections.length !== previousState.connections.length) {
        return '修改连接'
      } else {
        return '修改节点属性'
      }
    }
    return '撤销'
  }

  // 获取重做操作的描述
  const getRedoDescription = (): string => {
    if (canRedo.value && currentIndex.value < history.value.length - 1) {
      const currentState = history.value[currentIndex.value]
      const nextState = history.value[currentIndex.value + 1]

      // 简单的状态变化检测
      if (nextState.nodes.length > currentState.nodes.length) {
        return '添加节点'
      } else if (nextState.nodes.length < currentState.nodes.length) {
        return '删除节点'
      } else if (nextState.connections.length !== currentState.connections.length) {
        return '修改连接'
      } else {
        return '修改节点属性'
      }
    }
    return '重做'
  }

  // 清空历史记录
  const clearHistory = () => {
    history.value = []
    currentIndex.value = -1
  }

  // 初始化历史记录（用于加载工作流时）
  const initializeHistory = (state: Omit<HistoryState, 'timestamp'>) => {
    clearHistory()
    pushState(state)
  }

  return {
    history: computed(() => history.value),
    currentIndex: computed(() => currentIndex.value),
    canUndo,
    canRedo,
    pushState,
    getCurrentState,
    undo,
    redo,
    getUndoDescription,
    getRedoDescription,
    clearHistory,
    initializeHistory
  }
}