import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import VoiceRecognitionUnsupported from '@/components/VoiceRecognitionUnsupported.vue'

// Mock window.open
const mockOpen = vi.fn()
Object.defineProperty(window, 'open', {
  value: mockOpen,
  writable: true
})

describe('VoiceRecognitionUnsupported', () => {
  let wrapper: VueWrapper<any>

  beforeEach(() => {
    mockOpen.mockClear()
    wrapper = mount(VoiceRecognitionUnsupported, {
      global: {
        stubs: {
          'el-dialog': {
            template: '<div class="el-dialog"><slot v-if="modelValue" /></div>',
            props: ['modelValue']
          },
          'el-result': {
            template: '<div class="el-result"><slot /></div>'
          },
          'el-icon': {
            template: '<div class="el-icon"><slot /></div>'
          },
          'el-button': {
            template: '<button class="el-button" @click="$emit(\'click\')"><slot /></button>'
          },
          'el-divider': {
            template: '<div class="el-divider"><slot /></div>'
          }
        }
      }
    })
  })

  afterEach(() => {
    wrapper?.unmount()
  })

  describe('Component Rendering', () => {
    it('should render dialog component', () => {
      const dialog = wrapper.find('.el-dialog')
      expect(dialog.exists()).toBe(true)
    })

    it('should not be visible by default', () => {
      expect(wrapper.vm.visible).toBe(false)
    })

    it('should expose show method', () => {
      expect(wrapper.vm.show).toBeInstanceOf(Function)
    })
  })

  describe('Show/Hide Behavior', () => {
    it('should show dialog when show(true) is called', async () => {
      wrapper.vm.show(true)
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.visible).toBe(true)
    })

    it('should hide dialog when show(false) is called', async () => {
      wrapper.vm.show(true)
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.visible).toBe(true)

      wrapper.vm.show(false)
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.visible).toBe(false)
    })
  })

  describe('Browser Link Actions', () => {
    it('should open Chrome download link when chrome is called', async () => {
      wrapper.vm.show(true)
      await wrapper.vm.$nextTick()

      wrapper.vm.openBrowserLink('chrome')

      expect(mockOpen).toHaveBeenCalledWith(
        'https://www.google.com/chrome/',
        '_blank'
      )
    })

    it('should open Edge download link when edge is called', async () => {
      wrapper.vm.show(true)
      await wrapper.vm.$nextTick()

      wrapper.vm.openBrowserLink('edge')

      expect(mockOpen).toHaveBeenCalledWith(
        'https://www.microsoft.com/edge',
        '_blank'
      )
    })
  })

  describe('Confirm Action', () => {
    it('should emit confirm event when handleConfirm is called', async () => {
      wrapper.vm.handleConfirm()
      await wrapper.vm.$nextTick()

      expect(wrapper.emitted('confirm')).toBeTruthy()
      expect(wrapper.emitted('confirm')).toHaveLength(1)
    })

    it('should hide dialog after handleConfirm is called', async () => {
      wrapper.vm.show(true)
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.visible).toBe(true)

      wrapper.vm.handleConfirm()
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.visible).toBe(false)
    })
  })

  describe('Alternative Actions Content', () => {
    it('should display alternative actions section', async () => {
      wrapper.vm.show(true)
      await wrapper.vm.$nextTick()
      const alternativeActions = wrapper.find('.alternative-actions')
      expect(alternativeActions.exists()).toBe(true)
    })

    it('should mention text input as alternative', async () => {
      wrapper.vm.show(true)
      await wrapper.vm.$nextTick()
      const html = wrapper.html()
      expect(html).toContain('文本输入')
    })

    it('should mention quick replies as alternative', async () => {
      wrapper.vm.show(true)
      await wrapper.vm.$nextTick()
      const html = wrapper.html()
      expect(html).toContain('快捷回复')
    })
  })

  describe('Dialog Content', () => {
    it('should display warning about unsupported browser', async () => {
      wrapper.vm.show(true)
      await wrapper.vm.$nextTick()
      const html = wrapper.html()
      expect(html).toContain('当前浏览器不支持语音识别')
    })

    it('should display browser recommendations', async () => {
      wrapper.vm.show(true)
      await wrapper.vm.$nextTick()
      const html = wrapper.html()
      expect(html).toContain('推荐使用以下浏览器获得最佳体验')
    })

    it('should have browser recommendation items structure', async () => {
      wrapper.vm.show(true)
      await wrapper.vm.$nextTick()
      // Check that the result component exists
      const resultComponent = wrapper.find('.el-result')
      expect(resultComponent.exists()).toBe(true)
    })
  })

  describe('Edge Cases', () => {
    it('should handle multiple show/hide cycles', async () => {
      // First cycle
      wrapper.vm.show(true)
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.visible).toBe(true)

      wrapper.vm.show(false)
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.visible).toBe(false)

      // Second cycle
      wrapper.vm.show(true)
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.visible).toBe(true)

      wrapper.vm.show(false)
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.visible).toBe(false)
    })

    it('should handle confirm when dialog is not visible', async () => {
      expect(wrapper.vm.visible).toBe(false)

      wrapper.vm.handleConfirm()
      await wrapper.vm.$nextTick()

      expect(wrapper.emitted('confirm')).toBeTruthy()
      expect(wrapper.vm.visible).toBe(false)
    })
  })
})
