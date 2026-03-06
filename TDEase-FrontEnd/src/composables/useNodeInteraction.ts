import { ref, type Ref } from 'vue'

export interface NodeInteractionState {
  isHovered: Ref<boolean>
  isSelected: Ref<boolean>
  isDragging: Ref<boolean>
}

export function useNodeInteraction(initialSelected = false, initialDragging = false) {
  const isHovered = ref(false)
  const isSelected = ref(initialSelected)
  const isDragging = ref(initialDragging)

  const setHovered = (value: boolean) => {
    isHovered.value = value
  }

  const setSelected = (value: boolean) => {
    isSelected.value = value
  }

  const setDragging = (value: boolean) => {
    isDragging.value = value
  }

  const toggleSelected = () => {
    isSelected.value = !isSelected.value
  }

  const reset = () => {
    isHovered.value = false
    isSelected.value = false
    isDragging.value = false
  }

  const interactionState: NodeInteractionState = {
    isHovered,
    isSelected,
    isDragging
  }

  return {
    isHovered,
    isSelected,
    isDragging,
    setHovered,
    setSelected,
    setDragging,
    toggleSelected,
    reset,
    interactionState
  }
}

export function useNodeSelection(_nodeId: Ref<string | undefined>) {
  const isSelected = ref(false)

  const setSelected = (value: boolean) => {
    isSelected.value = value
  }

  return {
    isSelected,
    setSelected
  }
}

export function useNodeDrag(_nodeId: Ref<string | undefined>) {
  const isDragging = ref(false)
  const dragStartPosition = ref({ x: 0, y: 0 })

  const startDrag = (event: MouseEvent) => {
    isDragging.value = true
    dragStartPosition.value = { x: event.clientX, y: event.clientY }
  }

  const endDrag = () => {
    isDragging.value = false
    dragStartPosition.value = { x: 0, y: 0 }
  }

  return {
    isDragging,
    dragStartPosition,
    startDrag,
    endDrag
  }
}
