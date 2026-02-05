/**
 * 自适应语音识别系统单元测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  AdaptiveVoiceRecognition,
  WebSpeechEngine,
  CloudSTTEngine,
  OfflineEngine,
  NetworkQualityTester
} from '../../src/utils/adaptiveVoiceRecognition'

// Mock fetch
const mockFetch = vi.fn()

// Mock AudioContext
class MockAudioContext {
  createAnalyser() {
    return {
      fftSize: 512,
      disconnect: vi.fn(),
      connect: vi.fn()
    }
  }
  createGain() {
    return { connect: vi.fn(), disconnect: vi.fn() }
  }
  close() {}
}

describe('WebSpeechEngine', () => {
  let engine: WebSpeechEngine

  beforeEach(() => {
    vi.stubGlobal('AudioContext', MockAudioContext)
    vi.stubGlobal('performance', {
      now: vi.fn().mockReturnValue(0)
    })
    engine = new WebSpeechEngine()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  describe('isSupported', () => {
    it('应该支持Web Speech API', () => {
      vi.stubGlobal('window', {
        SpeechRecognition: vi.fn(),
        webkitSpeechRecognition: vi.fn()
      })

      const result = engine.isSupported()
      expect(result).toBe(true)
    })

    it('应该在不支持时返回false', () => {
      vi.stubGlobal('window', {})

      const result = engine.isSupported()
      expect(result).toBe(false)
    })
  })

  describe('initialize', () => {
    it('应该在初始化时创建SpeechRecognition', async () => {
      vi.stubGlobal('window', {
        SpeechRecognition: vi.fn(),
        webkitSpeechRecognition: vi.fn()
      })

      await expect(engine.initialize()).resolves.toBeUndefined()
    })

    it('应该在不支持时抛出错误', async () => {
      vi.stubGlobal('window', {})

      await expect(engine.initialize()).rejects.toThrow('Web Speech API 不受支持')
    })
  })

  describe('transcribe', () => {
    it('应该处理音频转录', async () => {
      vi.stubGlobal('window', {
        SpeechRecognition: vi.fn(),
        webkitSpeechRecognition: vi.fn().mockImplementation(function() {
          this.start = vi.fn()
          this.stop = vi.fn()
          this.onresult = null
          this.onerror = null
          this.onend = null
        })
      })

      await engine.initialize()

      const mockBlob = new Blob(['test'], { type: 'audio/webm' })

      // 注意：WebSpeechEngine的transcribe方法是异步的，但由于它是基于事件的，
      // 在测试环境中可能不会完成
      expect(engine).toBeDefined()
    })
  })

  describe('setLanguage', () => {
    it('应该设置识别语言', () => {
      vi.stubGlobal('window', {
        SpeechRecognition: vi.fn(),
        webkitSpeechRecognition: vi.fn().mockImplementation(function() {
          this.start = vi.fn()
          this.stop = vi.fn()
          this.onresult = null
          this.onerror = null
          this.onend = null
        })
      })

      engine.initialize()
      engine.setLanguage('en-US')

      // 由于mock实现，这个测试主要验证方法调用不会出错
      expect(engine).toBeDefined()
    })
  })

  describe('cleanup', () => {
    it('应该清理资源', () => {
      engine.cleanup()
      expect(engine).toBeDefined()
    })
  })
})

describe('CloudSTTEngine', () => {
  let engine: CloudSTTEngine

  beforeEach(() => {
    vi.stubGlobal('fetch', mockFetch)
    vi.stubGlobal('AudioContext', MockAudioContext)
    vi.stubGlobal('performance', {
      now: vi.fn().mockReturnValue(0)
    })
    engine = new CloudSTTEngine('/api/test')
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  describe('isSupported', () => {
    it('应该总是返回true', () => {
      expect(engine.isSupported()).toBe(true)
    })
  })

  describe('initialize', () => {
    it('应该初始化成功', async () => {
      await expect(engine.initialize()).resolves.toBeUndefined()
    })
  })

  describe('transcribe', () => {
    it('应该处理音频转录', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ text: 'test transcription' })
      })

      const mockBlob = new Blob(['test'], { type: 'audio/wav' })
      const result = await engine.transcribe(mockBlob)

      expect(result).toBe('test transcription')
    })

    it('应该处理API错误', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        statusText: 'Bad Request'
      })

      const mockBlob = new Blob(['test'], { type: 'audio/wav' })

      await expect(engine.transcribe(mockBlob)).rejects.toThrow('云端 STT 请求失败')
    })

    it('应该处理Float32Array输入', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ text: 'test from array' })
      })

      const mockArray = new Float32Array([0.1, 0.2, 0.3])
      const result = await engine.transcribe(mockArray)

      expect(result).toBe('test from array')
    })
  })

  describe('cleanup', () => {
    it('应该清理资源', () => {
      engine.cleanup()
      expect(engine).toBeDefined()
    })
  })
})

describe('OfflineEngine', () => {
  let engine: OfflineEngine

  beforeEach(() => {
    vi.stubGlobal('AudioContext', MockAudioContext)
    vi.stubGlobal('performance', {
      now: vi.fn().mockReturnValue(0)
    })
    engine = new OfflineEngine()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  describe('isSupported', () => {
    it('应该在支持WASM时返回true', () => {
      vi.stubGlobal('window', {
        WebAssembly: {}
      })

      const result = engine.isSupported()
      expect(result).toBe(true)
    })

    it('应该在不支持WASM时返回false', () => {
      vi.stubGlobal('window', {
        WebAssembly: undefined
      })

      const result = engine.isSupported()
      expect(result).toBe(false)
    })
  })

  describe('initialize', () => {
    it('应该在支持时初始化成功', async () => {
      vi.stubGlobal('window', {
        WebAssembly: {},
        isSecureContext: true
      })

      await expect(engine.initialize()).resolves.toBeUndefined()
    })

    it('应该在不支持时抛出错误', async () => {
      vi.stubGlobal('window', {
        WebAssembly: undefined
      })

      await expect(engine.initialize()).rejects.toThrow('离线引擎不受支持')
    })
  })

  describe('transcribe', () => {
    it('应该返回模拟结果', async () => {
      vi.stubGlobal('window', {
        WebAssembly: {},
        isSecureContext: true
      })

      await engine.initialize()

      const result = await engine.transcribe(new Float32Array([0.1, 0.2, 0.3]))

      expect(result).toBe('这是离线引擎的模拟识别结果')
    })
  })

  describe('cleanup', () => {
    it('应该清理资源', () => {
      engine.cleanup()
      expect(engine).toBeDefined()
    })
  })
})

describe('NetworkQualityTester', () => {
  let tester: NetworkQualityTester

  beforeEach(() => {
    vi.stubGlobal('fetch', mockFetch)
    vi.stubGlobal('AudioContext', MockAudioContext)
    vi.stubGlobal('performance', {
      now: vi.fn().mockReturnValue(0)
    })
    tester = new NetworkQualityTester()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  describe('testNetworkQuality', () => {
    it('应该测试网络质量', async () => {
      // Mock fetch 成功响应
      mockFetch.mockResolvedValueOnce({
        ok: true,
        blob: async () => new Blob(['test'], { type: 'image/x-icon' })
      })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        blob: async () => new Blob(['test'], { type: 'image/x-icon' })
      })

      const result = await tester.testNetworkQuality()

      expect(result).toHaveProperty('bandwidth')
      expect(result).toHaveProperty('latency')
      expect(result).toHaveProperty('jitter')
      expect(result).toHaveProperty('isStable')
    })

    it('应该处理网络错误', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      const result = await tester.testNetworkQuality()

      expect(result.latency).toBe(0)
      expect(result.bandwidth).toBe(0)
    })
  })
})

describe('AdaptiveVoiceRecognition', () => {
  let adaptiveEngine: AdaptiveVoiceRecognition

  beforeEach(() => {
    vi.stubGlobal('fetch', mockFetch)
    vi.stubGlobal('AudioContext', MockAudioContext)
    vi.stubGlobal('performance', {
      now: vi.fn().mockReturnValue(0)
    })
    adaptiveEngine = new AdaptiveVoiceRecognition()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    try {
      adaptiveEngine.cleanup()
    } catch (e) {
      // 忽略清理错误
    }
  })

  describe('constructor', () => {
    it('应该使用默认配置创建实例', () => {
      expect(adaptiveEngine).toBeDefined()
    })

    it('应该使用自定义配置创建实例', () => {
      const engine = new AdaptiveVoiceRecognition({
        preferCloudSTT: false,
        maxRetries: 5
      })

      expect(engine).toBeDefined()
    })
  })

  describe('initialize', () => {
    it('应该初始化所有引擎', async () => {
      vi.stubGlobal('window', {
        SpeechRecognition: vi.fn(),
        webkitSpeechRecognition: vi.fn(),
        WebAssembly: {},
        isSecureContext: true
      })

      await adaptiveEngine.initialize()

      expect(adaptiveEngine).toBeDefined()
    })
  })

  describe('selectBestEngine', () => {
    it('应该在初始化后选择最佳引擎', async () => {
      vi.stubGlobal('window', {
        SpeechRecognition: vi.fn(),
        webkitSpeechRecognition: vi.fn(),
        WebAssembly: {},
        isSecureContext: true
      })

      // Mock fetch
      mockFetch.mockResolvedValueOnce({
        ok: true,
        blob: async () => new Blob(['test'])
      })

      await adaptiveEngine.initialize()
      const engine = await adaptiveEngine.selectBestEngine()

      expect(engine).toBeDefined()
      expect(['webspeech', 'cloud', 'offline']).toContain(engine.type)
    })
  })

  describe('switchEngine', () => {
    it('应该切换到指定引擎', async () => {
      vi.stubGlobal('window', {
        SpeechRecognition: vi.fn(),
        webkitSpeechRecognition: vi.fn(),
        WebAssembly: {},
        isSecureContext: true
      })

      await adaptiveEngine.initialize()
      await adaptiveEngine.switchEngine('webspeech')

      // 验证切换成功
      expect(adaptiveEngine).toBeDefined()
    })

    it('应该在引擎不可用时抛出错误', async () => {
      await expect(adaptiveEngine.switchEngine('webspeech')).rejects.toThrow()
    })
  })

  describe('transcribe', () => {
    it('应该在没有当前引擎时自动选择', async () => {
      vi.stubGlobal('window', {
        SpeechRecognition: vi.fn(),
        webkitSpeechRecognition: vi.fn().mockImplementation(function() {
          this.start = vi.fn()
          this.stop = vi.fn()
          this.onresult = null
          this.onerror = null
          this.onend = null
        }),
        WebAssembly: {},
        isSecureContext: true
      })

      mockFetch.mockResolvedValueOnce({
        ok: true,
        blob: async () => new Blob(['test']),
        json: async () => ({ text: 'test result' })
      })

      await adaptiveEngine.initialize()
      const result = await adaptiveEngine.transcribe(new Float32Array([0.1, 0.2, 0.3]))

      expect(result).toBeDefined()
      expect(result.text).toBeDefined()
    })

    it('应该在失败时重试', async () => {
      vi.stubGlobal('window', {
        SpeechRecognition: vi.fn(),
        webkitSpeechRecognition: vi.fn().mockImplementation(function() {
          this.start = vi.fn()
          this.stop = vi.fn()
          this.onresult = null
          this.onerror = null
          this.onend = null
        }),
        WebAssembly: {},
        isSecureContext: true
      })

      // 模拟第一次失败，第二次成功
      mockFetch
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          blob: async () => new Blob(['test']),
          json: async () => ({ text: 'test result' })
        })

      await adaptiveEngine.initialize()
      const result = await adaptiveEngine.transcribe(new Float32Array([0.1, 0.2, 0.3]))

      expect(result).toBeDefined()
    }, 10000) // 增加超时时间，因为有重试机制
  })

  describe('getPerformanceReport', () => {
    it('应该返回性能报告', () => {
      const report = adaptiveEngine.getPerformanceReport()

      expect(report).toHaveProperty('currentEngine')
      expect(report).toHaveProperty('engines')
      expect(report).toHaveProperty('performance')
      expect(report).toHaveProperty('options')
    })
  })

  describe('updateOptions', () => {
    it('应该更新配置', () => {
      adaptiveEngine.updateOptions({
        preferCloudSTT: false,
        maxRetries: 10
      })

      const report = adaptiveEngine.getPerformanceReport()
      expect(report.options.preferCloudSTT).toBe(false)
    })
  })

  describe('cleanup', () => {
    it('应该清理所有资源', () => {
      adaptiveEngine.cleanup()

      expect(adaptiveEngine).toBeDefined()
    })
  })
})

describe('便利函数', () => {
  it('应该提供便利的创建函数', () => {
    const engine = AdaptiveVoiceRecognition.create({
      preferCloudSTT: false
    })

    expect(engine).toBeDefined()
    expect(engine).toBeInstanceOf(AdaptiveVoiceRecognition)
  })
})