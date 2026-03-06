import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useFullscreen } from '@/composables/useFullscreen'

describe('useFullscreen', () => {
  let originalDocument: Document
  let originalElementRequestFullscreen: any
  let originalDocumentExitFullscreen: any

  beforeEach(() => {
    // Store originals
    originalDocument = global.document
    originalElementRequestFullscreen = Element.prototype.requestFullscreen
    originalDocumentExitFullscreen = document.exitFullscreen

    // Mock document.fullscreenEnabled
    Object.defineProperty(document, 'fullscreenEnabled', {
      writable: true,
      value: true,
      configurable: true
    })

    // Mock document.fullscreenElement
    Object.defineProperty(document, 'fullscreenElement', {
      writable: true,
      value: null,
      configurable: true
    })

    // Create spy functions
    const mockRequestFullscreen = vi.fn()
    const mockExitFullscreen = vi.fn()

    // Mock element.requestFullscreen on the prototype
    Element.prototype.requestFullscreen = mockRequestFullscreen as any

    // Mock document.exitFullscreen
    Object.defineProperty(document, 'exitFullscreen', {
      value: mockExitFullscreen,
      writable: true,
      configurable: true
    })
  })

  afterEach(() => {
    // Restore originals
    Element.prototype.requestFullscreen = originalElementRequestFullscreen
    if (originalDocumentExitFullscreen) {
      Object.defineProperty(document, 'exitFullscreen', {
        value: originalDocumentExitFullscreen,
        writable: true,
        configurable: true
      })
    }
    global.document = originalDocument
  })

  it('should initialize with fullscreen false', () => {
    const { isFullscreen } = useFullscreen()

    expect(isFullscreen.value).toBe(false)
  })

  it('should check if fullscreen is supported', () => {
    const { isSupported } = useFullscreen()

    expect(isSupported.value).toBe(true)
  })

  it('should enter fullscreen', () => {
    const { enterFullscreen, isFullscreen } = useFullscreen()

    const element = document.createElement('div')

    enterFullscreen(element)

    // Verify the element's requestFullscreen was called
    expect(Element.prototype.requestFullscreen).toHaveBeenCalled()

    // Manually update fullscreen element for the test
    Object.defineProperty(document, 'fullscreenElement', {
      writable: true,
      value: element,
      configurable: true
    })

    // Trigger the fullscreenchange event
    const event = new Event('fullscreenchange')
    document.dispatchEvent(event)

    expect(isFullscreen.value).toBe(true)
  })

  it('should exit fullscreen', () => {
    const { exitFullscreen, isFullscreen } = useFullscreen()

    const element = document.documentElement
    Object.defineProperty(document, 'fullscreenElement', {
      writable: true,
      value: element,
      configurable: true
    })

    // Update isFullscreen to true by triggering event
    const enterEvent = new Event('fullscreenchange')
    document.dispatchEvent(enterEvent)
    expect(isFullscreen.value).toBe(true)

    exitFullscreen()

    // Verify document.exitFullscreen was called
    expect(document.exitFullscreen).toHaveBeenCalled()

    // Clear the fullscreen element to simulate exit
    Object.defineProperty(document, 'fullscreenElement', {
      writable: true,
      value: null,
      configurable: true
    })

    // Trigger the fullscreenchange event
    const event = new Event('fullscreenchange')
    document.dispatchEvent(event)

    expect(isFullscreen.value).toBe(false)
  })

  it('should toggle fullscreen', () => {
    const { toggleFullscreen, isFullscreen } = useFullscreen()

    const element = document.createElement('div')

    // Should enter fullscreen
    toggleFullscreen(element)

    // Verify requestFullscreen was called
    expect(Element.prototype.requestFullscreen).toHaveBeenCalled()

    // Manually update for test
    Object.defineProperty(document, 'fullscreenElement', {
      writable: true,
      value: element,
      configurable: true
    })
    const event1 = new Event('fullscreenchange')
    document.dispatchEvent(event1)

    expect(isFullscreen.value).toBe(true)

    // Should exit fullscreen
    toggleFullscreen()

    expect(document.exitFullscreen).toHaveBeenCalled()
  })

  it('should use document element when no element provided', () => {
    const { enterFullscreen } = useFullscreen()

    enterFullscreen()

    expect(Element.prototype.requestFullscreen).toHaveBeenCalled()
  })

  it('should handle errors gracefully when entering fullscreen', () => {
    Element.prototype.requestFullscreen = vi.fn(() => {
      throw new Error('Fullscreen denied')
    }) as any

    const { enterFullscreen } = useFullscreen()

    expect(() => enterFullscreen()).not.toThrow()
  })

  it('should handle errors gracefully when exiting fullscreen', () => {
    Object.defineProperty(document, 'exitFullscreen', {
      value: vi.fn(() => {
        throw new Error('Exit fullscreen failed')
      }),
      writable: true,
      configurable: true
    })

    const { exitFullscreen } = useFullscreen()

    expect(() => exitFullscreen()).not.toThrow()
  })
})
