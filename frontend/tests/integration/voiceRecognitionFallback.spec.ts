/**
 * Voice Recognition Fallback Integration Tests
 *
 * 集成测试：验证语音识别在不同浏览器环境下的降级处理策略
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import { ElMessage } from 'element-plus'

// Mock dependencies
vi.mock('@/utils/voiceRecognition', () => ({
  createVoiceRecognition: vi.fn(() => ({
    on: vi.fn(),
    start: vi.fn(),
    stop: vi.fn(),
    isListening: vi.fn(() => false),
    destroy: vi.fn()
  })),
  isVoiceRecognitionSupported: vi.fn(() => true),
  VoiceRecognitionStatus: {
    Idle: 'idle',
    Starting: 'starting',
    Listening: 'listening',
    Stopping: 'stopping',
    Error: 'error'
  }
}))

import ConversationView from '@/views/student/ConversationView.vue'
import VoiceRecognitionUnsupported from '@/components/VoiceRecognitionUnsupported.vue'
import { BrowserCompatibility } from '@/utils/browserCompatibility'

// Stubs for child components
const stubs = {
  // Element Plus components
  'el-page-header': true,
  'el-page-header': true,
  'el-icon': true,
  'el-button': {
    template: '<button class="el-button" @click="$emit(\'click\')"><slot /></button>'
  },
  'el-input': true,
  'el-textarea': true,
  'el-switch': true,
  'el-select': true,
  'el-option': true,
  'el-input-number': true,
  'el-form': true,
  'el-form-item': true,
  'el-dialog': true,
  'el-tag': true,
  'el-divider': true,
  'el-result': true,
  'el-message-box': true,
  // Custom components
  ConversationMessageComponent: true,
  ConversationStatusComponent: true,
  ConversationFeedbackDrawer: {
    template: '<div class="feedback-drawer"><slot name="extra" /></div>',
    props: ['visible', 'scores', 'keyWords', 'isComplete']
  },
  ConversationScoreCard: true
  // Note: VoiceRecognitionUnsupported is NOT stubbed to access its methods
}

describe('Voice Recognition Fallback - Integration', () => {
  let wrapper: VueWrapper<any>
  let router: any
  let pinia: any

  beforeEach(async () => {
    // Pinia setup
    pinia = createPinia()
    setActivePinia(pinia)

    // Router setup
    router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/', component: { template: '<div>Home</div>' } },
        { path: '/student/conversation', component: ConversationView }
      ]
    })

    await router.push('/student/conversation')
    await router.isReady()

    wrapper = mount(ConversationView, {
      global: {
        plugins: [pinia, router],
        stubs,
        mocks: {
          $router: router
        }
      }
    })
  })

  afterEach(() => {
    wrapper?.unmount()
    vi.clearAllMocks()
  })

  describe('Firefox Browser Scenario', () => {
    it('should show unsupported dialog for Firefox without Web Speech API', async () => {
      // Mock browser detection to return Firefox without Web Speech support
      vi.spyOn(BrowserCompatibility, 'detect').mockReturnValue({
        engine: 'firefox',
        version: '120.0',
        webSpeechSupported: false,
        webAudioSupported: true,
        wasmSupported: true,
        isSecureContext: true,
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0'
      })

      // Navigate to conversation step
      wrapper.vm.currentStep = 'conversation'
      wrapper.vm.selectedScenario = 'free_talk'
      await wrapper.vm.$nextTick()

      // Simulate voice input toggle
      await wrapper.vm.toggleVoiceInput()
      await wrapper.vm.$nextTick()

      // Verify unsupported dialog ref is set and dialog is shown
      expect(wrapper.vm.unsupportedDialogRef).toBeTruthy()
      const unsupportedDialog = wrapper.findComponent(VoiceRecognitionUnsupported)
      expect(unsupportedDialog.exists()).toBe(true)
      expect(unsupportedDialog.vm.visible).toBe(true)
    })
  })

  describe('Safari Browser Scenario', () => {
    it('should show warning message for Safari with partial support', async () => {
      // Mock ElMessage.warning
      const warningSpy = vi.spyOn(ElMessage, 'warning')

      // Mock browser detection to return Safari with partial Web Speech support
      vi.spyOn(BrowserCompatibility, 'detect').mockReturnValue({
        engine: 'safari',
        version: '17.0',
        webSpeechSupported: true, // Safari has partial support
        webAudioSupported: true,
        wasmSupported: true,
        isSecureContext: true,
        userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
      })

      wrapper.vm.currentStep = 'conversation'
      wrapper.vm.selectedScenario = 'free_talk'
      await wrapper.vm.$nextTick()

      // Toggle voice input
      await wrapper.vm.toggleVoiceInput()
      await wrapper.vm.$nextTick()

      // Verify warning is shown but dialog is not
      expect(warningSpy).toHaveBeenCalledWith(
        expect.stringContaining('Safari 浏览器的语音识别功能可能不稳定')
      )

      const unsupportedDialog = wrapper.findComponent(VoiceRecognitionUnsupported)
      expect(unsupportedDialog.vm.visible).toBe(false)

      warningSpy.mockRestore()
    })
  })

  describe('Chrome Browser Scenario', () => {
    it('should allow voice input for Chrome with full support', async () => {
      // Mock browser detection to return Chrome with full support
      vi.spyOn(BrowserCompatibility, 'detect').mockReturnValue({
        engine: 'chrome',
        version: '120.0',
        webSpeechSupported: true,
        webAudioSupported: true,
        wasmSupported: true,
        isSecureContext: true,
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      })

      wrapper.vm.currentStep = 'conversation'
      wrapper.vm.selectedScenario = 'free_talk'
      await wrapper.vm.$nextTick()

      // Toggle voice input
      await wrapper.vm.toggleVoiceInput()
      await wrapper.vm.$nextTick()

      // Verify voice input is enabled
      expect(wrapper.vm.isVoiceInput).toBe(true)

      const unsupportedDialog = wrapper.findComponent(VoiceRecognitionUnsupported)
      expect(unsupportedDialog.vm.visible).toBe(false)
    })
  })

  describe('Dialog Interaction Flow', () => {
    it('should complete full user flow when browser is unsupported', async () => {
      vi.spyOn(BrowserCompatibility, 'detect').mockReturnValue({
        engine: 'firefox',
        version: '120.0',
        webSpeechSupported: false,
        webAudioSupported: true,
        wasmSupported: true,
        isSecureContext: true,
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0'
      })

      wrapper.vm.currentStep = 'conversation'
      wrapper.vm.selectedScenario = 'free_talk'
      await wrapper.vm.$nextTick()

      // Step 1: User clicks voice button
      await wrapper.vm.toggleVoiceInput()
      await wrapper.vm.$nextTick()

      const unsupportedDialog = wrapper.findComponent(VoiceRecognitionUnsupported)
      expect(unsupportedDialog.vm.visible).toBe(true)

      // Step 2: User confirms to continue with text input
      await unsupportedDialog.vm.handleConfirm()
      await wrapper.vm.$nextTick()

      // Step 3: Dialog should be hidden after calling handleConfirm directly
      expect(unsupportedDialog.vm.visible).toBe(false)

      // Step 4: Voice input should remain disabled
      expect(wrapper.vm.isVoiceInput).toBe(false)
    })
  })

  describe('Multiple Browser Checks', () => {
    it('should handle consecutive browser checks correctly', async () => {
      // First check: Firefox (unsupported)
      vi.spyOn(BrowserCompatibility, 'detect').mockReturnValueOnce({
        engine: 'firefox',
        version: '120.0',
        webSpeechSupported: false,
        webAudioSupported: true,
        wasmSupported: true,
        isSecureContext: true,
        userAgent: 'Mozilla/5.0 Firefox/120.0'
      })

      wrapper.vm.currentStep = 'conversation'
      wrapper.vm.selectedScenario = 'free_talk'
      await wrapper.vm.$nextTick()

      await wrapper.vm.toggleVoiceInput()
      await wrapper.vm.$nextTick()

      let unsupportedDialog = wrapper.findComponent(VoiceRecognitionUnsupported)
      expect(unsupportedDialog.vm.visible).toBe(true)

      // Close dialog using handleConfirm
      await unsupportedDialog.vm.handleConfirm()
      await wrapper.vm.$nextTick()

      // Second check: Chrome (supported)
      vi.spyOn(BrowserCompatibility, 'detect').mockReturnValueOnce({
        engine: 'chrome',
        version: '120.0',
        webSpeechSupported: true,
        webAudioSupported: true,
        wasmSupported: true,
        isSecureContext: true,
        userAgent: 'Mozilla/5.0 Chrome/120.0'
      })

      await wrapper.vm.toggleVoiceInput()
      await wrapper.vm.$nextTick()

      unsupportedDialog = wrapper.findComponent(VoiceRecognitionUnsupported)
      expect(unsupportedDialog.vm.visible).toBe(false)
      expect(wrapper.vm.isVoiceInput).toBe(true)
    })
  })

  describe('Non-Secure Context Scenario', () => {
    it('should handle non-secure context appropriately', async () => {
      vi.spyOn(BrowserCompatibility, 'detect').mockReturnValue({
        engine: 'chrome',
        version: '120.0',
        webSpeechSupported: false, // Not supported in non-secure context
        webAudioSupported: true,
        wasmSupported: true,
        isSecureContext: false, // HTTP context
        userAgent: 'Mozilla/5.0 Chrome/120.0'
      })

      wrapper.vm.currentStep = 'conversation'
      wrapper.vm.selectedScenario = 'free_talk'
      await wrapper.vm.$nextTick()

      await wrapper.vm.toggleVoiceInput()
      await wrapper.vm.$nextTick()

      // Should show unsupported dialog
      const unsupportedDialog = wrapper.findComponent(VoiceRecognitionUnsupported)
      expect(unsupportedDialog.vm.visible).toBe(true)
    })
  })
})
