/**
 * 语音识别降级策略单元测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  VoiceRecognitionFallback,
  RecognitionStrategy,
  RecognitionConfig,
  RecognitionResult,
  createVoiceRecognitionFallback,
  getRecommendedRecognitionStrategy,
  createVoiceRecognition,
  isVoiceRecognitionSupported,
  getStrategyDescription
} from '../../src/utils/voiceRecognitionFallback'
import { BrowserCompatibility, BrowserInfo } from '../../src/utils/browserCompatibility'

// Mock navigator
const mockNavigator = {
  userAgent: '',
  vendor: '',
  isSecureContext: true,
  onLine: true
}

// Mock SpeechRecognition
class MockSpeechRecognition {
  lang = 'zh-CN'
  continuous = false
  interimResults = true
  maxAlternatives = 1

  onresult: any = null
  onerror: any = null
  onstart: any = null
  onend: any = null

  start() {
    // 异步触发 onstart
    setTimeout(() => {
      this.onstart?.()
    }, 0)
  }

  stop() {
    // 异步触发 onend
    setTimeout(() => {
      this.onend?.()
    }, 0)
  }
}

// Mock MediaRecorder
class MockMediaRecorder {
  state: 'idle' | 'recording' | 'paused' = 'idle'
  ondataavailable: any = null
  onstop: any = null
  onstart: any = null

  constructor(_stream: MediaStream) {
    setTimeout(() => {
      this.state = 'recording'
      this.onstart?.()
    }, 0)
  }

  start() {
    this.state = 'recording'
  }

  stop() {
    this.state = 'idle'
    setTimeout(() => {
      this.onstop?.()
    }, 0)
  }
}

// Mock getUserMedia
const mockGetUserMedia = vi.fn().mockResolvedValue({
  getTracks: () => []
})

describe('VoiceRecognitionFallback', () => {
  let fallback: VoiceRecognitionFallback

  beforeEach(() => {
    vi.stubGlobal('navigator', mockNavigator)
    // 不在 beforeEach 中设置 import.meta.env，让每个测试用例自己设置
    fallback = new VoiceRecognitionFallback()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  describe('canUseWebSpeechAPI', () => {
    it('应该在 Chrome 浏览器支持 Web Speech API 时返回 true', () => {
      mockNavigator.userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      mockNavigator.vendor = 'Google Inc.'

      vi.stubGlobal('window', {
        SpeechRecognition: MockSpeechRecognition,
        webkitSpeechRecognition: MockSpeechRecognition
      })

      fallback = new VoiceRecognitionFallback()
      expect(fallback.canUseWebSpeechAPI()).toBe(true)
    })

    it('应该在 Edge 浏览器支持 Web Speech API 时返回 true', () => {
      mockNavigator.userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
      mockNavigator.vendor = 'Google Inc.'

      vi.stubGlobal('window', {
        SpeechRecognition: MockSpeechRecognition,
        webkitSpeechRecognition: MockSpeechRecognition
      })

      fallback = new VoiceRecognitionFallback()
      expect(fallback.canUseWebSpeechAPI()).toBe(true)
    })

    it('应该在 Safari 浏览器返回 false（优先使用云端 STT）', () => {
      mockNavigator.userAgent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
      mockNavigator.vendor = 'Apple Computer, Inc.'

      vi.stubGlobal('window', {
        SpeechRecognition: MockSpeechRecognition,
        webkitSpeechRecognition: MockSpeechRecognition
      })

      fallback = new VoiceRecognitionFallback()
      expect(fallback.canUseWebSpeechAPI()).toBe(false)
    })

    it('应该在浏览器不支持 Web Speech API 时返回 false', () => {
      mockNavigator.userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      mockNavigator.vendor = 'Google Inc.'

      vi.stubGlobal('window', {})

      fallback = new VoiceRecognitionFallback()
      expect(fallback.canUseWebSpeechAPI()).toBe(false)
    })
  })

  describe('canUseCloudSTT', () => {
    it('应该在有 API key 时返回 true', () => {
      vi.stubGlobal('import.meta', {
        env: { VITE_OPENAI_API_KEY: 'test-key' }
      })

      fallback = new VoiceRecognitionFallback()
      expect(fallback.canUseCloudSTT()).toBe(true)
    })

    it('应该在有网络连接时返回 true', () => {
      mockNavigator.onLine = true
      vi.stubGlobal('import.meta', { env: {} })

      fallback = new VoiceRecognitionFallback()
      expect(fallback.canUseCloudSTT()).toBe(true)
    })

    it('应该在没有网络且没有 API key 时返回 false', () => {
      mockNavigator.onLine = false
      vi.stubGlobal('import.meta', { env: {} })
      vi.stubGlobal('navigator', { onLine: false })

      fallback = new VoiceRecognitionFallback()
      expect(fallback.canUseCloudSTT()).toBe(false)
    })
  })

  describe('canUseHybrid', () => {
    it('应该在同时支持 Web Speech API 和 Cloud STT 时返回 true', () => {
      // 先设置环境变量
      vi.stubGlobal('import.meta', {
        env: { VITE_OPENAI_API_KEY: 'test-key' }
      })

      mockNavigator.userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      mockNavigator.vendor = 'Google Inc.'
      mockNavigator.onLine = true

      vi.stubGlobal('window', {
        SpeechRecognition: MockSpeechRecognition,
        webkitSpeechRecognition: MockSpeechRecognition
      })

      vi.stubGlobal('navigator', {
        ...mockNavigator,
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        vendor: 'Google Inc.',
        isSecureContext: true,
        onLine: true
      })

      // 创建新实例以使用更新后的环境
      fallback = new VoiceRecognitionFallback()
      expect(fallback.canUseHybrid()).toBe(true)
    })
  })

  describe('getRecommendedStrategy', () => {
    it('应该为 Chrome 推荐使用 Web Speech API', () => {
      mockNavigator.userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      mockNavigator.vendor = 'Google Inc.'

      vi.stubGlobal('window', {
        SpeechRecognition: MockSpeechRecognition,
        webkitSpeechRecognition: MockSpeechRecognition
      })

      fallback = new VoiceRecognitionFallback()
      expect(fallback.getRecommendedStrategy()).toBe(RecognitionStrategy.WebSpeechAPI)
    })

    it('应该为 Edge 推荐使用 Web Speech API', () => {
      mockNavigator.userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
      mockNavigator.vendor = 'Google Inc.'

      vi.stubGlobal('window', {
        SpeechRecognition: MockSpeechRecognition,
        webkitSpeechRecognition: MockSpeechRecognition
      })

      fallback = new VoiceRecognitionFallback()
      expect(fallback.getRecommendedStrategy()).toBe(RecognitionStrategy.WebSpeechAPI)
    })

    it('应该为 Safari 推荐使用 Cloud STT（当有网络时）', () => {
      mockNavigator.userAgent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
      mockNavigator.vendor = 'Apple Computer, Inc.'
      mockNavigator.onLine = true

      vi.stubGlobal('window', {
        SpeechRecognition: MockSpeechRecognition,
        webkitSpeechRecognition: MockSpeechRecognition
      })
      vi.stubGlobal('navigator', {
        ...mockNavigator,
        userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        vendor: 'Apple Computer, Inc.',
        isSecureContext: true,
        onLine: true
      })

      fallback = new VoiceRecognitionFallback()
      expect(fallback.getRecommendedStrategy()).toBe(RecognitionStrategy.CloudSTT)
    })

    it('应该为不支持的浏览器返回 Disabled', () => {
      mockNavigator.userAgent = 'Unknown Browser'
      mockNavigator.vendor = ''
      mockNavigator.onLine = false

      vi.stubGlobal('window', {})
      vi.stubGlobal('navigator', {
        userAgent: 'Unknown Browser',
        vendor: '',
        isSecureContext: false,
        onLine: false
      })

      fallback = new VoiceRecognitionFallback()
      expect(fallback.getRecommendedStrategy()).toBe(RecognitionStrategy.Disabled)
    })
  })

  describe('createRecognition', () => {
    it('应该为 Chrome 创建 Web Speech API 适配器', () => {
      mockNavigator.userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      mockNavigator.vendor = 'Google Inc.'

      vi.stubGlobal('window', {
        SpeechRecognition: MockSpeechRecognition,
        webkitSpeechRecognition: MockSpeechRecognition
      })

      fallback = new VoiceRecognitionFallback()
      const recognition = fallback.createRecognition({ language: 'zh-CN' })

      expect(recognition.getStrategy()).toBe(RecognitionStrategy.WebSpeechAPI)
      expect(recognition.isSupported()).toBe(true)
    })

    it('应该为 Safari 创建 Cloud STT 适配器（当有网络时）', () => {
      mockNavigator.userAgent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
      mockNavigator.vendor = 'Apple Computer, Inc.'
      mockNavigator.onLine = true

      vi.stubGlobal('window', {
        SpeechRecognition: MockSpeechRecognition,
        webkitSpeechRecognition: MockSpeechRecognition
      })
      vi.stubGlobal('MediaRecorder', MockMediaRecorder)
      vi.stubGlobal('navigator', {
        ...mockNavigator,
        userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        vendor: 'Apple Computer, Inc.',
        isSecureContext: true,
        onLine: true,
        mediaDevices: { getUserMedia: mockGetUserMedia }
      })

      fallback = new VoiceRecognitionFallback()
      const recognition = fallback.createRecognition({ language: 'zh-CN' })

      expect(recognition.getStrategy()).toBe(RecognitionStrategy.CloudSTT)
      expect(recognition.isSupported()).toBe(true)
    })

    it('应该在不支持的浏览器抛出错误', () => {
      mockNavigator.userAgent = 'Unknown Browser'
      mockNavigator.vendor = ''
      mockNavigator.onLine = false

      vi.stubGlobal('window', {})
      vi.stubGlobal('navigator', {
        userAgent: 'Unknown Browser',
        vendor: '',
        isSecureContext: false,
        onLine: false
      })

      fallback = new VoiceRecognitionFallback()

      expect(() => fallback.createRecognition()).toThrow()
    })
  })

  describe('getBrowserInfo', () => {
    it('应该返回浏览器信息', () => {
      const browserInfo = fallback.getBrowserInfo()

      expect(browserInfo).toHaveProperty('engine')
      expect(browserInfo).toHaveProperty('version')
      expect(browserInfo).toHaveProperty('webSpeechSupported')
      expect(browserInfo).toHaveProperty('webAudioSupported')
    })
  })

  describe('getStrategyReason', () => {
    it('应该为 Chrome 返回正确的策略原因', () => {
      mockNavigator.userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      mockNavigator.vendor = 'Google Inc.'

      vi.stubGlobal('window', {
        SpeechRecognition: MockSpeechRecognition,
        webkitSpeechRecognition: MockSpeechRecognition
      })

      fallback = new VoiceRecognitionFallback()
      const reason = fallback.getStrategyReason()

      expect(reason).toContain('浏览器内置语音识别')
      expect(reason).toContain('chrome')
    })

    it('应该为 Safari 返回正确的策略原因（当有网络时）', () => {
      mockNavigator.userAgent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
      mockNavigator.vendor = 'Apple Computer, Inc.'
      mockNavigator.onLine = true

      vi.stubGlobal('window', {
        SpeechRecognition: MockSpeechRecognition,
        webkitSpeechRecognition: MockSpeechRecognition
      })
      vi.stubGlobal('navigator', {
        ...mockNavigator,
        userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        vendor: 'Apple Computer, Inc.',
        isSecureContext: true,
        onLine: true
      })

      fallback = new VoiceRecognitionFallback()
      const reason = fallback.getStrategyReason()

      expect(reason).toContain('云端语音识别')
      expect(reason).toContain('safari')
    })

    it('应该为不支持的浏览器返回错误说明', () => {
      mockNavigator.userAgent = 'Unknown Browser'
      mockNavigator.vendor = ''
      mockNavigator.onLine = false

      vi.stubGlobal('window', {})
      vi.stubGlobal('navigator', {
        userAgent: 'Unknown Browser',
        vendor: '',
        isSecureContext: false,
        onLine: false
      })

      fallback = new VoiceRecognitionFallback()
      const reason = fallback.getStrategyReason()

      expect(reason).toContain('不支持语音识别')
    })
  })
})

describe('WebSpeechRecognitionAdapter', () => {
  let recognition: any

  beforeEach(() => {
    vi.stubGlobal('navigator', mockNavigator)
    vi.stubGlobal('window', {
      SpeechRecognition: MockSpeechRecognition,
      webkitSpeechRecognition: MockSpeechRecognition
    })
    mockNavigator.userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    mockNavigator.vendor = 'Google Inc.'
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    recognition?.destroy()
  })

  describe('start', () => {
    it('应该启动语音识别', async () => {
      const fallback = new VoiceRecognitionFallback()
      recognition = fallback.createRecognition({ language: 'zh-CN' })

      await expect(recognition.start()).resolves.toBeUndefined()
    })

    it('应该触发 onStart 回调', async () => {
      const fallback = new VoiceRecognitionFallback()
      recognition = fallback.createRecognition({ language: 'zh-CN' })

      const onStart = vi.fn()
      recognition.on({ onStart })

      await recognition.start()

      expect(onStart).toHaveBeenCalled()
    })
  })

  describe('stop', () => {
    it('应该停止语音识别', async () => {
      const fallback = new VoiceRecognitionFallback()
      recognition = fallback.createRecognition({ language: 'zh-CN' })

      await recognition.start()
      await expect(recognition.stop()).resolves.toBeUndefined()
    })
  })

  describe('on', () => {
    it('应该注册回调函数', async () => {
      const fallback = new VoiceRecognitionFallback()
      recognition = fallback.createRecognition({ language: 'zh-CN' })

      const callbacks = {
        onResult: vi.fn(),
        onError: vi.fn(),
        onStart: vi.fn(),
        onEnd: vi.fn()
      }

      recognition.on(callbacks)

      await recognition.start()

      expect(callbacks.onStart).toHaveBeenCalled()
    })
  })

  describe('destroy', () => {
    it('应该清理资源', async () => {
      const fallback = new VoiceRecognitionFallback()
      recognition = fallback.createRecognition({ language: 'zh-CN' })

      await recognition.start()
      recognition.destroy()

      expect(recognition.isSupported()).toBe(true)
    })
  })
})

describe('CloudSTTAdapter', () => {
  let recognition: any

  beforeEach(() => {
    mockNavigator.userAgent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
    mockNavigator.vendor = 'Apple Computer, Inc.'
    mockNavigator.onLine = true

    vi.stubGlobal('navigator', {
      ...mockNavigator,
      mediaDevices: { getUserMedia: mockGetUserMedia }
    })
    vi.stubGlobal('window', {})
    vi.stubGlobal('MediaRecorder', MockMediaRecorder)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    recognition?.destroy()
  })

  describe('start', () => {
    it('应该启动语音识别', async () => {
      const fallback = new VoiceRecognitionFallback()
      recognition = fallback.createRecognition({ language: 'zh-CN' })

      await expect(recognition.start()).resolves.toBeUndefined()
    })
  })

  describe('isSupported', () => {
    it('应该总是返回 true', () => {
      const fallback = new VoiceRecognitionFallback()
      recognition = fallback.createRecognition({ language: 'zh-CN' })

      expect(recognition.isSupported()).toBe(true)
    })
  })
})

describe('便利函数', () => {
  beforeEach(() => {
    vi.stubGlobal('navigator', mockNavigator)
    vi.stubGlobal('window', {
      SpeechRecognition: MockSpeechRecognition,
      webkitSpeechRecognition: MockSpeechRecognition
    })
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  describe('createVoiceRecognitionFallback', () => {
    it('应该创建降级策略实例', () => {
      const fallback = createVoiceRecognitionFallback()

      expect(fallback).toBeInstanceOf(VoiceRecognitionFallback)
      expect(fallback.canUseWebSpeechAPI()).toBeDefined()
      expect(fallback.getRecommendedStrategy()).toBeDefined()
    })
  })

  describe('getRecommendedRecognitionStrategy', () => {
    it('应该返回推荐的策略', () => {
      mockNavigator.userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      mockNavigator.vendor = 'Google Inc.'

      const strategy = getRecommendedRecognitionStrategy()

      expect(strategy).toBe(RecognitionStrategy.WebSpeechAPI)
    })
  })

  describe('createVoiceRecognition', () => {
    it('应该创建语音识别实例', () => {
      mockNavigator.userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      mockNavigator.vendor = 'Google Inc.'

      const recognition = createVoiceRecognition({ language: 'zh-CN' })

      expect(recognition).toBeDefined()
      expect(recognition.getStrategy()).toBe(RecognitionStrategy.WebSpeechAPI)
    })

    it('应该使用默认配置', () => {
      mockNavigator.userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      mockNavigator.vendor = 'Google Inc.'

      const recognition = createVoiceRecognition()

      expect(recognition).toBeDefined()
    })
  })

  describe('isVoiceRecognitionSupported', () => {
    it('应该在支持时返回 true', () => {
      mockNavigator.userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      mockNavigator.vendor = 'Google Inc.'

      expect(isVoiceRecognitionSupported()).toBe(true)
    })

    it('应该在不支持时返回 false', () => {
      vi.unstubAllGlobals()
      mockNavigator.userAgent = 'Unknown Browser'
      mockNavigator.vendor = ''
      mockNavigator.onLine = false

      vi.stubGlobal('navigator', {
        userAgent: 'Unknown Browser',
        vendor: '',
        isSecureContext: false,
        onLine: false
      })
      vi.stubGlobal('window', {})

      expect(isVoiceRecognitionSupported()).toBe(false)
    })
  })

  describe('getStrategyDescription', () => {
    it('应该返回策略描述', () => {
      const description = getStrategyDescription()

      expect(typeof description).toBe('string')
      expect(description.length).toBeGreaterThan(0)
    })

    it('应该为 Chrome 返回内置 API 描述', () => {
      mockNavigator.userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      mockNavigator.vendor = 'Google Inc.'

      const description = getStrategyDescription()

      expect(description).toContain('浏览器内置语音识别')
    })
  })
})

describe('RecognitionStrategy 枚举', () => {
  it('应该定义所有策略类型', () => {
    expect(RecognitionStrategy.WebSpeechAPI).toBe('web_speech_api')
    expect(RecognitionStrategy.CloudSTT).toBe('cloud_stt')
    expect(RecognitionStrategy.Hybrid).toBe('hybrid')
    expect(RecognitionStrategy.Disabled).toBe('disabled')
  })
})
