import { ref, computed, onMounted, onUnmounted } from 'vue'

export interface CanvasTransform {
  scale: number
  translateX: number
  translateY: number
}

export function useCanvasControls() {
  // 画布变换状态
  const transform = ref<CanvasTransform>({
    scale: 1,
    translateX: 0,
    translateY: 0
  })

  // 画布尺寸
  const canvasSize = ref({ width: 0, height: 0 })

  // 鼠标拖拽状态
  const isDragging = ref(false)
  const dragStart = ref({ x: 0, y: 0 })
  const lastTransform = ref<CanvasTransform>({ scale: 1, translateX: 0, translateY: 0 })

  // 计算画布的实际尺寸
  const scaledCanvasSize = computed(() => ({
    width: canvasSize.value.width * transform.value.scale,
    height: canvasSize.value.height * transform.value.scale
  }))

  // 计算变换的 CSS 值
  const transformStyle = computed(() => {
    return `translate(${transform.value.translateX}px, ${transform.value.translateY}px) scale(${transform.value.scale})`
  })

  // 缩放函数
  const zoom = (delta: number, center?: { x: number, y: number }) => {
    const newScale = Math.max(0.1, Math.min(5, transform.value.scale + delta))

    if (center) {
      // 以鼠标位置为中心进行缩放
      const scaleChange = newScale - transform.value.scale
      transform.value.translateX -= center.x * scaleChange
      transform.value.translateY -= center.y * scaleChange
    }

    transform.value.scale = newScale
  }

  // 放大
  const zoomIn = (center?: { x: number, y: number }) => {
    zoom(0.1, center)
  }

  // 缩小
  const zoomOut = (center?: { x: number, y: number }) => {
    zoom(-0.1, center)
  }

  // 重置缩放
  const resetZoom = () => {
    transform.value = { scale: 1, translateX: 0, translateY: 0 }
  }

  // 适应画布
  const fitToScreen = (contentBounds?: { width: number, height: number }) => {
    if (contentBounds && canvasSize.value.width > 0 && canvasSize.value.height > 0) {
      const scaleX = (canvasSize.value.width - 100) / contentBounds.width
      const scaleY = (canvasSize.value.height - 100) / contentBounds.height
      const newScale = Math.min(scaleX, scaleY, 1)

      transform.value.scale = Math.max(0.1, newScale)
      transform.value.translateX = 50
      transform.value.translateY = 50
    } else {
      resetZoom()
    }
  }

  // 开始拖拽
  const startDrag = (event: MouseEvent) => {
    isDragging.value = true
    dragStart.value = { x: event.clientX, y: event.clientY }
    lastTransform.value = { ...transform.value }
  }

  // 拖拽中
  const drag = (event: MouseEvent) => {
    if (!isDragging.value) return

    const deltaX = event.clientX - dragStart.value.x
    const deltaY = event.clientY - dragStart.value.y

    transform.value.translateX = lastTransform.value.translateX + deltaX
    transform.value.translateY = lastTransform.value.translateY + deltaY
  }

  // 结束拖拽
  const endDrag = () => {
    isDragging.value = false
  }

  // 获取鼠标在画布中的位置
  const getMousePosition = (event: MouseEvent): { x: number, y: number } => {
    const rect = (event.currentTarget as HTMLElement).getBoundingClientRect()
    const x = (event.clientX - rect.left - transform.value.translateX) / transform.value.scale
    const y = (event.clientY - rect.top - transform.value.translateY) / transform.value.scale
    return { x, y }
  }

  // 设置画布尺寸
  const setCanvasSize = (width: number, height: number) => {
    canvasSize.value = { width, height }
  }

  // 鼠标滚轮缩放
  const handleWheel = (event: WheelEvent) => {
    event.preventDefault()
    const rect = (event.currentTarget as HTMLElement).getBoundingClientRect()
    const center = {
      x: event.clientX - rect.left,
      y: event.clientY - rect.top
    }

    const delta = event.deltaY > 0 ? -0.1 : 0.1
    zoom(delta, center)
  }

  // 初始化事件监听
  const initCanvasControls = (canvasElement: HTMLElement) => {
    // 滚轮缩放
    canvasElement.addEventListener('wheel', handleWheel, { passive: false })

    // 设置画布尺寸
    const updateSize = () => {
      const rect = canvasElement.getBoundingClientRect()
      setCanvasSize(rect.width, rect.height)
    }

    updateSize()
    window.addEventListener('resize', updateSize)

    // 清理函数
    return () => {
      canvasElement.removeEventListener('wheel', handleWheel)
      window.removeEventListener('resize', updateSize)
    }
  }

  // 全局拖拽事件处理
  const handleMouseMove = (event: MouseEvent) => {
    drag(event)
  }

  const handleMouseUp = () => {
    endDrag()
  }

  onMounted(() => {
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
  })

  onUnmounted(() => {
    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', handleMouseUp)
  })

  return {
    // 状态
    transform,
    canvasSize,
    isDragging,
    scaledCanvasSize,
    transformStyle,

    // 缩放控制
    zoom,
    zoomIn,
    zoomOut,
    resetZoom,
    fitToScreen,

    // 拖拽控制
    startDrag,
    drag,
    endDrag,

    // 工具函数
    getMousePosition,
    setCanvasSize,
    initCanvasControls,
    handleWheel
  }
}
