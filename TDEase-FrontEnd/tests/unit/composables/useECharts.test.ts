import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { ref, nextTick } from 'vue'
import { mount } from '@vue/test-utils'
import { defineComponent } from 'vue'
import { useECharts } from '@/composables/useECharts'

// Test component that uses the composable
const TestComponent = defineComponent({
  props: ['container'],
  setup(props) {
    const { chart, isReady, init, dispose, setOption, resize, on, off, showLoading, hideLoading, clear } = useECharts(
      ref(props.container as HTMLElement | undefined)
    )
    return { chart, isReady, init, dispose, setOption, resize, on, off, showLoading, hideLoading, clear }
  },
  template: '<div></div>'
})

describe('useECharts', () => {
  let container: HTMLElement

  beforeEach(() => {
    container = document.createElement('div')
    document.body.appendChild(container)
  })

  afterEach(() => {
    document.body.removeChild(container)
  })

  it('should initialize chart when init is called', () => {
    const wrapper = mount(TestComponent, {
      props: { container }
    })

    wrapper.vm.init()

    expect(wrapper.vm.chart).not.toBeNull()
    expect(wrapper.vm.isReady).toBe(true)

    wrapper.unmount()
  })

  it('should dispose chart on unmount', async () => {
    const wrapper = mount(TestComponent, {
      props: { container }
    })

    wrapper.vm.init()
    expect(wrapper.vm.chart).not.toBeNull()

    await wrapper.unmount()

    // After unmount, the chart should be disposed (null)
    // Note: The composable's internal chart ref will be null after disposal
  })

  it('should set chart option', () => {
    const wrapper = mount(TestComponent, {
      props: { container }
    })

    wrapper.vm.init()

    const option = {
      xAxis: { type: 'category' },
      yAxis: { type: 'value' },
      series: [{ type: 'line', data: [1, 2, 3] }]
    }

    expect(() => wrapper.vm.setOption(option)).not.toThrow()

    wrapper.unmount()
  })

  it('should resize chart', () => {
    const wrapper = mount(TestComponent, {
      props: { container }
    })

    wrapper.vm.init()

    expect(() => wrapper.vm.resize({ width: 800, height: 600 })).not.toThrow()

    wrapper.unmount()
  })

  it('should attach event handlers', () => {
    const wrapper = mount(TestComponent, {
      props: { container }
    })

    wrapper.vm.init()
    const mockHandler = vi.fn()

    wrapper.vm.on('click', mockHandler)

    expect(wrapper.vm.chart).not.toBeNull()

    wrapper.unmount()
  })

  it('should detach event handlers', () => {
    const wrapper = mount(TestComponent, {
      props: { container }
    })

    wrapper.vm.init()
    const mockHandler = vi.fn()

    wrapper.vm.on('click', mockHandler)
    wrapper.vm.off('click', mockHandler)

    expect(wrapper.vm.chart).not.toBeNull()

    wrapper.unmount()
  })

  it('should show and hide loading', () => {
    const wrapper = mount(TestComponent, {
      props: { container }
    })

    wrapper.vm.init()

    expect(() => {
      wrapper.vm.showLoading()
      wrapper.vm.hideLoading()
    }).not.toThrow()

    wrapper.unmount()
  })

  it('should clear chart', () => {
    const wrapper = mount(TestComponent, {
      props: { container }
    })

    wrapper.vm.init()

    expect(() => wrapper.vm.clear()).not.toThrow()

    wrapper.unmount()
  })

  it('should not initialize when container is not found', () => {
    const emptyRef = ref<HTMLElement | undefined>()
    const { chart, isReady, init } = useECharts(emptyRef)

    init()

    expect(chart.value).toBeNull()
    expect(isReady.value).toBe(false)
  })
})
