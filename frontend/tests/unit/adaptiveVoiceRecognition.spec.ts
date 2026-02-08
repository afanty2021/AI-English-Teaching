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
import { BrowserCompatibility } from '../../src/utils/browserCompatibility'

// Mock AudioContext
const MockAudioContext = class {
  createAnalyser() {
    return {
      fftSize: 512,
      disconnect: vi.fn(),
      connect: vi.fn()
    }
  }
  createDynamicsCompressor() {
    return {
      threshold: { setValueAtTime: vi.fn() },
      knee: { setValueAtTime: vi.fn() },
      ratio: { setValueAtTime: vi.fn() },
      attack: { setValueAtTime: vi.fn() },
      release: { setValueAtTime: vi.fn() },
      connect: vi.fn(),
      disconnect: vi.fn()
    }
  }
  createGain() {
    return { connect: vi.fn(), disconnect: vi.fn(), gainValue: 1 }
  }
  close() {}
}

// Mock fetch
const mockFetch = vi.fn()

// Mock SpeechRecognition
const createMockSpeechRecognition = () => {
  return function() {
    this.start = vi.fn()
    this.stop = vi.fn()
    this.abort = vi.fn()
    this.onstart = null
    this.onend = null
    this.onresult = null
    this.onerror = null
    this.lang = 'zh-CN'
    this.continuous = false
    this.interimResults = true
    this.maxAlternatives = 1
  }
}

describe('WebSpeechEngine', () => {
  let engine: WebSpeechEngine
  let mockSpeechRecognition: any

  beforeEach(() => {
    // 设置全局 AudioContext mock
    Object.defineProperty(globalThis, 'AudioContext', {
      value: MockAudioContext,
      writable: true
    })
    Object.defineProperty(globalThis, 'webkitAudioContext', {
      value: MockAudioContext,
      writable: true
    })
    vi.stubGlobal('performance', { now: vi.fn().mockReturnValue(0) })

    // Mock SpeechRecognition
    mockSpeechRecognition = createMockSpeechRecognition()
    vi.stubGlobal('SpeechRecognition', mockSpeechRecognition)
    vi.stubGlobal('webkitSpeechRecognition', mockSpeechRecognition)

    // Mock BrowserCompatibility.detect
    vi.spyOn(BrowserCompatibility, 'detect').mockReturnValue({
      engine: 'chrome' as const,
      version: '120.0.0.0',
      webSpeechSupported: true,
      webAudioSupported: true,
      wasmSupported: false,
      isSecureContext: true,
      userAgent: 'Mozilla/5.0 Chrome/120.0.0.0'
    })

    engine = new WebSpeechEngine()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('isSupported', () => {
    it('应该支持Web Speech API', () => {
      expect(engine.isSupported()).toBe(true)
    })
  })

  describe('initialize', () => {
    it('应该在初始化时创建SpeechRecognition', async () => {
      await expect(engine.initialize()).resolves.toBeUndefined()
    })
  })
})

describe('CloudSTTEngine', () => {
  let engine: CloudSTTEngine

  beforeEach(() => {
    Object.defineProperty(globalThis, 'AudioContext', {
      value: MockAudioContext,
      writable: true
    })
    vi.stubGlobal('fetch', mockFetch)
    vi.stubGlobal('performance', { now: vi.fn().mockReturnValue(0) })
    engine = new CloudSTTEngine('/api/test')
  })

  afterEach(() => {
    vi.restoreAllMocks()
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
  })
})

describe('OfflineEngine', () => {
  let engine: OfflineEngine

  beforeEach(() => {
    Object.defineProperty(globalThis, 'WebAssembly', {
      value: { instantiate: vi.fn().mockResolvedValue({}) },
      writable: true
    })
    Object.defineProperty(globalThis, 'isSecureContext', { value: true, writable: true })
    vi.stubGlobal('performance', { now: vi.fn().mockReturnValue(0) })
    engine = new OfflineEngine()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('isSupported', () => {
    it('应该在支持WASM时返回true', () => {
      expect(engine.isSupported()).toBe(true)
    })
  })

  describe('initialize', () => {
    it('应该在支持时初始化成功', async () => {
      await expect(engine.initialize()).resolves.toBeUndefined()
    })
  })

  describe('transcribe', () => {
    it('应该返回模拟结果', async () => {
      await engine.initialize()
      const result = await engine.transcribe(new Float32Array([0.1, 0.2, 0.3]))

      expect(result).toBe('这是离线引擎的模拟识别结果')
    })
  })
})

describe('NetworkQualityTester', () => {
  let tester: NetworkQualityTester

  beforeEach(() => {
    Object.defineProperty(globalThis, 'AudioContext', {
      value: MockAudioContext,
      writable: true
    })
    vi.stubGlobal('fetch', mockFetch)
    vi.stubGlobal('performance', { now: vi.fn().mockReturnValue(0) })
    tester = new NetworkQualityTester()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('testNetworkQuality', () => {
    it('应该测试网络质量', async () => {
      mockFetch.mockResolvedValue({
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
      // Mock性能计时器返回一个固定值，使测试可预测
      let callCount = 0
      const fixedTime = 100
      vi.stubGlobal('performance', {
        now: vi.fn().mockImplementation(() => {
          callCount++
          return callCount <= 2 ? fixedTime : fixedTime + 10
        })
      })

      mockFetch.mockRejectedValue(new Error('Network error'))

      const result = await tester.testNetworkQuality()

      // 网络错误时应返回默认值
      expect(result.bandwidth).toBe(0)
      // 检查 latency 为 0 或 NaN（取决于实现）
      expect(result.latency === 0 || Number.isNaN(result.latency)).toBe(true)
    })
  })
})

// 便利函数测试
describe('便利函数', () => {
  it('应该提供便利的创建函数', () => {
    // 直接测试静态方法是否存在
    expect(typeof AdaptiveVoiceRecognition.create).toBe('function')
  })
})
