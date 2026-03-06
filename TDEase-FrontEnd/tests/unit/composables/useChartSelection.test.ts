import { describe, it, expect } from 'vitest'
import { useChartSelection } from '@/composables/useChartSelection'

describe('useChartSelection', () => {
  it('should initialize with empty selection', () => {
    const { selectedItems, selectedCount, hasSelection } = useChartSelection<number>()

    expect(selectedItems.value.size).toBe(0)
    expect(selectedCount.value).toBe(0)
    expect(hasSelection.value).toBe(false)
  })

  it('should add single item to selection', () => {
    const { addSelection, selectedItems, selectedCount } = useChartSelection<number>()

    addSelection(1)

    expect(selectedItems.value.has(1)).toBe(true)
    expect(selectedCount.value).toBe(1)
  })

  it('should add multiple items to selection', () => {
    const { addSelection, selectedItems, selectedCount } = useChartSelection<number>()

    addSelection([1, 2, 3])

    expect(selectedItems.value.size).toBe(3)
    expect(selectedCount.value).toBe(3)
  })

  it('should remove single item from selection', () => {
    const { addSelection, removeSelection, selectedItems, selectedCount } = useChartSelection<number>()

    addSelection([1, 2, 3])
    removeSelection(2)

    expect(selectedItems.value.has(2)).toBe(false)
    expect(selectedCount.value).toBe(2)
  })

  it('should remove multiple items from selection', () => {
    const { addSelection, removeSelection, selectedItems, selectedCount } = useChartSelection<number>()

    addSelection([1, 2, 3, 4, 5])
    removeSelection([2, 4])

    expect(selectedItems.value.size).toBe(3)
    expect(selectedCount.value).toBe(3)
  })

  it('should toggle item selection', () => {
    const { toggleSelection, selectedItems, selectedCount } = useChartSelection<number>()

    toggleSelection(1)
    expect(selectedItems.value.has(1)).toBe(true)
    expect(selectedCount.value).toBe(1)

    toggleSelection(1)
    expect(selectedItems.value.has(1)).toBe(false)
    expect(selectedCount.value).toBe(0)
  })

  it('should clear all selections', () => {
    const { addSelection, clearSelection, selectedItems, selectedCount } = useChartSelection<number>()

    addSelection([1, 2, 3, 4, 5])
    clearSelection()

    expect(selectedItems.value.size).toBe(0)
    expect(selectedCount.value).toBe(0)
  })

  it('should set selection to specific items', () => {
    const { setSelection, selectedItems, selectedCount } = useChartSelection<number>()

    setSelection([1, 2, 3])

    expect(selectedItems.value.size).toBe(3)
    expect(selectedCount.value).toBe(3)

    setSelection([4, 5])

    expect(selectedItems.value.size).toBe(2)
    expect(selectedItems.value.has(4)).toBe(true)
    expect(selectedItems.value.has(5)).toBe(true)
  })

  it('should check if item is selected', () => {
    const { addSelection, isItemSelected } = useChartSelection<number>()

    addSelection([1, 2, 3])

    expect(isItemSelected(1)).toBe(true)
    expect(isItemSelected(2)).toBe(true)
    expect(isItemSelected(4)).toBe(false)
  })

  it('should get selected items as array', () => {
    const { addSelection, getSelectedItems } = useChartSelection<number>()

    addSelection([3, 1, 2])

    const items = getSelectedItems()
    expect(items).toHaveLength(3)
    expect(items).toContain(1)
    expect(items).toContain(2)
    expect(items).toContain(3)
  })

  it('should respect max selections limit', () => {
    const { addSelection, selectedCount } = useChartSelection<number>({ maxSelections: 3 })

    addSelection([1, 2, 3, 4, 5])

    expect(selectedCount.value).toBe(3)
  })

  it('should call selection change callbacks', () => {
    const callback = vi.fn()
    const { addSelection, onSelectionChange } = useChartSelection<number>()

    onSelectionChange(callback)

    addSelection(1)
    expect(callback).toHaveBeenCalledWith([1])

    addSelection([2, 3])
    expect(callback).toHaveBeenCalledWith([1, 2, 3])
  })
})
