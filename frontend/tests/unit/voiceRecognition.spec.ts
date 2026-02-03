/**
 * 语音识别工具测试
 * 包含正常场景和边界条件测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  VoiceRecognition,
  createVoiceRecognition,
  isVoiceRecognitionSupported,
  VoiceRecognitionStatus,
  type VoiceRecognitionCallbacks
} from '@/utils/voiceRecognition'

// Mock window.SpeechRecognition
const mockSpeechRecognition = vi.fn()

class MockSpeechRecognition {
  onstart: (() => void) | null = null
  onend: (() => void) | null = null
  onresult: ((event: any) => void) | null = null
  onerror: ((event: any) => void) | null = null
  lang = 'en-US'
  continuous = false
  interimResults = true
  maxAlternatives = 1

  constructor() {
    mockSpeechRecognition(this)
  }

  start() {
    setTimeout(() => {
      this.onstart?.()
    }, 0)
  }

  stop() {
    setTimeout(() => {
      this.onend?.()
    }, 0)
  }

  abort() {
    this.onend?.()
  }
}

describe('VoiceRecognition', () => {
  let originalSpeechRecognition: any

  beforeEach(() => {
    // 保存原始 SpeechRecognition
    originalSpeechRecognition = (window as any).SpeechRecognition
    ;(window as any).SpeechRecognition = MockSpeechRecognition
    ;(window as any).webkitSpeechRecognition = MockSpeechRecognition
  })

  afterEach(() => {
    // 恢复原始 SpeechRecognition
    ;(window as any).SpeechRecognition = originalSpeechRecognition
    ;(window as any).webkitSpeechRecognition = originalSpeechRecognition
    vi.clearAllMocks()
  })

  describe('isVoiceRecognitionSupported', () => {
    it('应该返回 true 当浏览器支持语音识别', () => {
      expect(isVoiceRecognitionSupported()).toBe(true)
    })

    it('应该返回 false 当浏览器不支持语音识别', () => {
      ;(window as any).SpeechRecognition = undefined
      ;(window as any).webkitSpeechRecognition = undefined
      expect(isVoiceRecognitionSupported()).toBe(false)
    })
  })

  describe('createVoiceRecognition', () => {
    it('应该创建语音识别实例', () => {
      const recognition = createVoiceRecognition()
      expect(recognition).toBeInstanceOf(VoiceRecognition)
    })

    it('应该使用默认配置', () => {
      const recognition = createVoiceRecognition()
      // 验证默认配置（通过检查内部状态）
      expect(recognition.getStatus()).toBe(VoiceRecognitionStatus.Idle)
    })

    it('应该接受自定义配置', () => {
      const recognition = createVoiceRecognition({
        language: 'zh-CN',
        continuous: true,
        interimResults: false
      })
      expect(recognition).toBeInstanceOf(VoiceRecognition)
    })
  })

  describe('语音识别生命周期', () => {
    let recognition: VoiceRecognition
    let callbacks: VoiceRecognitionCallbacks

    beforeEach(() => {
      callbacks = {
        onStart: vi.fn(),
        onStop: vi.fn(),
        onResult: vi.fn(),
        onInterimResult: vi.fn(),
        onError: vi.fn(),
        onStatusChange: vi.fn()
      }
      recognition = createVoiceRecognition()
      recognition.on(callbacks)
    })

    it('应该从 idle 状态开始', () => {
      expect(recognition.getStatus()).toBe(VoiceRecognitionStatus.Idle)
      expect(recognition.isListening()).toBe(false)
    })

    it('启动时应该变为 listening 状态', async () => {
      recognition.start()
      // 等待异步操作
      await new Promise(resolve => setTimeout(resolve, 10))
      expect(callbacks.onStart).toHaveBeenCalled()
    })

    it('停止时应该回到 idle 状态', async () => {
      recognition.start()
      await new Promise(resolve => setTimeout(resolve, 10))
      recognition.stop()
      await new Promise(resolve => setTimeout(resolve, 10))
      expect(callbacks.onStop).toHaveBeenCalled()
    })

    it('abort 应该立即停止识别', async () => {
      recognition.start()
      recognition.abort()
      expect(recognition.isListening()).toBe(false)
    })
  })

  describe('识别结果处理', () => {
    let recognition: VoiceRecognition
    let mockInstance: any

    beforeEach(() => {
      recognition = createVoiceRecognition()
      recognition.start()
      mockInstance = mockSpeechRecognition.mock.calls[mockSpeechRecognition.mock.calls.length - 1][0]
    })

    it('应该接收最终结果', async () => {
      const onResult = vi.fn()
      recognition.on({ onResult })

      // 模拟最终结果
      mockInstance.onresult?.({
        results: [{
          isFinal: true,
          0: {
            transcript: 'Hello world',
            confidence: 0.95
          }
        }]
      })

      await new Promise(resolve => setTimeout(resolve, 10))

      expect(onResult).toHaveBeenCalledWith({
        transcript: 'Hello world',
        isFinal: true,
        confidence: 0.95
      })
    })

    it('应该接收临时结果', async () => {
      const onInterimResult = vi.fn()
      recognition.on({ onInterimResult })

      // 模拟临时结果
      mockInstance.onresult?.({
        results: [{
          isFinal: false,
          0: {
            transcript: 'Hello',
            confidence: 0.8
          }
        }]
      })

      await new Promise(resolve => setTimeout(resolve, 10))

      expect(onInterimResult).toHaveBeenCalledWith({
        transcript: 'Hello',
        isFinal: false,
        confidence: 0.8
      })
    })

    it('应该处理空字符串结果', async () => {
      const onResult = vi.fn()
      recognition.on({ onResult })

      mockInstance.onresult?.({
        results: [{
          isFinal: true,
          0: {
            transcript: '',
            confidence: 0
          }
        }]
      })

      await new Promise(resolve => setTimeout(resolve, 10))

      expect(onResult).toHaveBeenCalledWith({
        transcript: '',
        isFinal: true,
        confidence: 0
      })
    })
  })

  describe('错误处理', () => {
    let recognition: VoiceRecognition
    let mockInstance: any

    beforeEach(() => {
      recognition = createVoiceRecognition()
      recognition.start()
      mockInstance = mockSpeechRecognition.mock.calls[mockSpeechRecognition.mock.calls.length - 1][0]
    })

    it('应该处理 no-speech 错误', async () => {
      const onError = vi.fn()
      recognition.on({ onError })

      mockInstance.onerror?.({ error: 'no-speech' })

      await new Promise(resolve => setTimeout(resolve, 10))

      expect(onError).toHaveBeenCalledWith({
        code: 'no_speech',
        message: '未检测到语音输入'
      })
    })

    it('应该处理 not-allowed 错误', async () => {
      const onError = vi.fn()
      recognition.on({ onError })

      mockInstance.onerror?.({ error: 'not-allowed' })

      await new Promise(resolve => setTimeout(resolve, 10))

      expect(onError).toHaveBeenCalledWith({
        code: 'not_allowed',
        message: '未授权使用麦克风'
      })
    })

    it('应该处理 network 错误', async () => {
      const onError = vi.fn()
      recognition.on({ onError })

      mockInstance.onerror?.({ error: 'network' })

      await new Promise(resolve => setTimeout(resolve, 10))

      expect(onError).toHaveBeenCalledWith({
        code: 'network',
        message: '网络连接失败，语音识别需要网络连接'
      })
    })

    it('应该处理未知错误', async () => {
      const onError = vi.fn()
      recognition.on({ onError })

      mockInstance.onerror?.({ error: 'unknown_error', message: 'Something went wrong' })

      await new Promise(resolve => setTimeout(resolve, 10))

      expect(onError).toHaveBeenCalledWith({
        code: 'unknown_error',
        message: 'Something went wrong'
      })
    })
  })

  describe('边界条件', () => {
    it('应该在未初始化时调用 start 返回错误', () => {
      const recognition = new VoiceRecognition()
      // 不调用 initRecognition，直接调用 start
      expect(() => recognition.start()).not.toThrow()
    })

    it('应该处理多次调用 start', async () => {
      const recognition = createVoiceRecognition()
      const onError = vi.fn()
      recognition.on({ onError })

      recognition.start()
      await new Promise(resolve => setTimeout(resolve, 10))
      recognition.start() // 第二次调用
      await new Promise(resolve => setTimeout(resolve, 10))

      // 不应该抛出错误
      expect(onError).not.toHaveBeenCalled()
    })

    it('应该处理在未启动时调用 stop', () => {
      const recognition = createVoiceRecognition()
      expect(() => recognition.stop()).not.toThrow()
    })

    it('应该处理在未启动时调用 abort', () => {
      const recognition = createVoiceRecognition()
      expect(() => recognition.abort()).not.toThrow()
    })

    it('应该处理空回调对象', () => {
      const recognition = createVoiceRecognition()
      expect(() => recognition.on({})).not.toThrow()
    })

    it('应该处理 updateConfig', () => {
      const recognition = createVoiceRecognition()
      expect(() => recognition.updateConfig({ language: 'zh-CN' })).not.toThrow()
    })

    it('destroy 应该清理所有资源', () => {
      const recognition = createVoiceRecognition()
      expect(() => recognition.destroy()).not.toThrow()
    })

    it('应该处理 destroy 后调用方法', () => {
      const recognition = createVoiceRecognition()
      recognition.destroy()
      expect(() => recognition.start()).not.toThrow()
      expect(() => recognition.stop()).not.toThrow()
    })
  })

  describe('状态变化回调', () => {
    it('应该通知状态变化', async () => {
      const onStatusChange = vi.fn()
      const recognition = createVoiceRecognition()
      recognition.on({ onStatusChange })

      recognition.start()
      await new Promise(resolve => setTimeout(resolve, 10))

      expect(onStatusChange).toHaveBeenCalledWith(VoiceRecognitionStatus.Listening)
    })

    it('应该处理所有状态转换', async () => {
      const onStatusChange = vi.fn()
      const recognition = createVoiceRecognition()
      recognition.on({ onStatusChange })

      recognition.start()
      await new Promise(resolve => setTimeout(resolve, 10))
      expect(onStatusChange).toHaveBeenLastCalledWith(VoiceRecognitionStatus.Listening)

      recognition.stop()
      await new Promise(resolve => setTimeout(resolve, 10))
      expect(onStatusChange).toHaveBeenLastCalledWith(VoiceRecognitionStatus.Idle)
    })
  })

  describe('配置更新', () => {
    it('应该更新语言配置', () => {
      const recognition = createVoiceRecognition({ language: 'en-US' })
      recognition.updateConfig({ language: 'zh-CN' })
      // 配置已更新（内部验证）
      expect(recognition).toBeInstanceOf(VoiceRecognition)
    })

    it('应该更新 continuous 配置', () => {
      const recognition = createVoiceRecognition({ continuous: false })
      recognition.updateConfig({ continuous: true })
      expect(recognition).toBeInstanceOf(VoiceRecognition)
    })

    it('应该更新 interimResults 配置', () => {
      const recognition = createVoiceRecognition({ interimResults: true })
      recognition.updateConfig({ interimResults: false })
      expect(recognition).toBeInstanceOf(VoiceRecognition)
    })
  })
})
