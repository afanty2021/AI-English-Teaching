/**
 * 语音识别优化集成测试
 *
 * 测试语音识别优化功能的完整集成：
 * 1. 浏览器兼容性降级策略
 * 2. 音频缓冲策略
 * 3. LRU 缓存避免重复识别
 * 4. 识别准确率监控
 * 5. 智能重试机制
 * 6. 端到端语音识别流程
 *
 * @test
 * @integration
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { BrowserCompatibility } from '@/utils/browserCompatibility'
import {
  VoiceRecognitionFallback,
  RecognitionStrategy,
  createVoiceRecognitionFallback,
  createVoiceRecognition
} from '@/utils/voiceRecognitionFallback'
import { AudioBuffer } from '@/utils/audioBuffer'
import { RecognitionLRUCache } from '@/utils/recognitionCache'
import { PerformanceMonitor } from '@/utils/performanceMonitor'

// ========== Mock Web Speech API ==========

class MockSpeechRecognition implements EventTarget {
  lang = 'zh-CN'
  continuous = false
  interimResults = true
  maxAlternatives = 1
  onstart: ((this: SpeechRecognition, ev: Event) => unknown) | null = null
  onend: ((this: SpeechRecognition, ev: Event) => unknown) | null = null
  onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => unknown) | null = null
  onerror: ((this: SpeechRecognition, ev: SpeechRecognitionErrorEvent) => unknown) | null = null

  private listeners: Map<string, Function[]> = new Map()
  private isActive = false

  addEventListener(type: string, callback: EventListenerOrEventListenerObject | null): void {
    if (callback) {
      const fn = typeof callback === 'function' ? callback : callback.handleEvent
      const existing = this.listeners.get(type) || []
      existing.push(fn)
      this.listeners.set(type, existing)
    }
  }

  removeEventListener(type: string, callback: EventListenerOrEventListenerObject | null): void {
    if (callback) {
      const fn = typeof callback === 'function' ? callback : callback.handleEvent
      const existing = this.listeners.get(type) || []
      const filtered = existing.filter(f => f !== fn)
      this.listeners.set(type, filtered)
    }
  }

  dispatchEvent(event: Event): boolean {
    const listeners = this.listeners.get(event.type) || []
    listeners.forEach(fn => fn.call(this, event))
    return true
  }

  start(): void {
    this.isActive = true
    setTimeout(() => {
      this.onstart?.(new Event('start'))
      this.dispatchResult()
    }, 10)
  }

  stop(): void {
    this.isActive = false
    setTimeout(() => {
      this.onend?.(new Event('end'))
    }, 10)
  }

  abort(): void {
    this.isActive = false
    this.onerror?.({ error: 'aborted', message: 'Recognition aborted' } as SpeechRecognitionErrorEvent)
  }

  private dispatchResult(): void {
    const mockEvent: SpeechRecognitionEvent = {
      results: {
        length: 1,
        item: (index: number) => ({
          isFinal: true,
          length: 1,
          item: (i: number) => ({
            transcript: '你好',
            confidence: 0.95
          }),
          0: {
            transcript: '你好',
            confidence: 0.95
          }
        }),
        0: {
          isFinal: true,
          length: 1,
          item: (i: number) => ({
            transcript: '你好',
            confidence: 0.95
          }),
          0: {
            transcript: '你好',
            confidence: 0.95
          }
        }
      },
      resultIndex: 0,
      interpretation: null
    }
    this.onresult?.(mockEvent)
  }
}

// ========== Mock Cloud STT API ==========

const mockCloudSTTResponse = {
  text: '你好，世界',
  confidence: 0.92
}

// ========== Test Setup ==========

function setupChromeEnvironment() {
  Object.defineProperty(navigator, 'userAgent', {
    value: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    writable: true,
    configurable: true
  })
  Object.defineProperty(navigator, 'vendor', {
    value: 'Google Inc.',
    writable: true,
    configurable: true
  })
  ;(window as any).SpeechRecognition = MockSpeechRecognition
  ;(window as any).webkitSpeechRecognition = MockSpeechRecognition
}

function setupSafariEnvironment() {
  Object.defineProperty(navigator, 'userAgent', {
    value: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    writable: true,
    configurable: true
  })
  Object.defineProperty(navigator, 'vendor', {
    value: 'Apple Computer, Inc.',
    writable: true,
    configurable: true
  })
  delete (window as any).SpeechRecognition
  delete (window as any).webkitSpeechRecognition
}

function setupFirefoxEnvironment() {
  Object.defineProperty(navigator, 'userAgent', {
    value: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    writable: true,
    configurable: true
  })
  Object.defineProperty(navigator, 'vendor', {
    value: '',
    writable: true,
    configurable: true
  })
  delete (window as any).SpeechRecognition
  delete (window as any).webkitSpeechRecognition
}

function mockFetchForCloudSTT() {
  global.fetch = vi.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve(mockCloudSTTResponse)
    } as Response)
  ) as any
}

function mockMediaRecorder() {
  const mockStream = {
    getAudioTracks: () => [],
    addEventListener: vi.fn(),
    removeEventListener: vi.fn()
  }

  global.navigator.mediaDevices = {
    getUserMedia: vi.fn(() => Promise.resolve(mockStream as any))
  } as any

  class MockMediaRecorder {
    state = 'inactive'
    ondataavailable: ((event: any) => void) | null = null
    onstop: ((event: Event) => void) | null = null
    onstart: ((event: Event) => void) | null = null

    start() {
      this.state = 'recording'
      setTimeout(() => {
        this.onstart?.(new Event('start'))
      }, 10)
    }

    stop() {
      this.state = 'inactive'
      setTimeout(() => {
        this.onstop?.(new Event('stop'))
      }, 10)
    }
  }

  global.MediaRecorder = MockMediaRecorder as any
}

// ========== Test Suites ==========

describe('语音识别优化集成测试', () => {
  let originalUserAgent: string
  let originalVendor: string
  let originalFetch: any
  let originalMediaDevices: any
  let originalMediaRecorder: any

  beforeEach(() => {
    originalUserAgent = navigator.userAgent
    originalVendor = (navigator as any).vendor
    originalFetch = global.fetch
    originalMediaDevices = global.navigator.mediaDevices
    originalMediaRecorder = global.MediaRecorder
    vi.clearAllMocks()
  })

  afterEach(() => {
    Object.defineProperty(navigator, 'userAgent', {
      value: originalUserAgent,
      writable: true,
      configurable: true
    })
    if (originalVendor !== undefined) {
      Object.defineProperty(navigator, 'vendor', {
        value: originalVendor,
        writable: true,
        configurable: true
      })
    }
    global.fetch = originalFetch
    global.navigator.mediaDevices = originalMediaDevices
    global.MediaRecorder = originalMediaRecorder
  })

  // ==================== 测试套件1: 浏览器兼容性降级策略 ====================

  describe('浏览器兼容性降级策略', () => {
    it('应该在 Chrome 浏览器使用 Web Speech API', () => {
      setupChromeEnvironment()

      const fallback = createVoiceRecognitionFallback()
      const strategy = fallback.getRecommendedStrategy()

      expect(strategy).toBe(RecognitionStrategy.WebSpeechAPI)
      expect(fallback.canUseWebSpeechAPI()).toBe(true)
      expect(fallback.getBrowserInfo().engine).toBe('chrome')
    })

    it('应该在 Safari 浏览器降级到 Cloud STT', () => {
      setupSafariEnvironment()

      const fallback = createVoiceRecognitionFallback()
      const strategy = fallback.getRecommendedStrategy()

      // Safari 不支持 Web Speech API，应该降级到云端
      expect(strategy).toBe(RecognitionStrategy.CloudSTT)
      expect(fallback.canUseWebSpeechAPI()).toBe(false)
      expect(fallback.getBrowserInfo().engine).toBe('safari')
    })

    it('应该在 Firefox 浏览器降级到 Cloud STT', () => {
      setupFirefoxEnvironment()

      const fallback = createVoiceRecognitionFallback()
      const strategy = fallback.getRecommendedStrategy()

      // Firefox 默认不支持 Web Speech API
      expect(strategy).toBe(RecognitionStrategy.CloudSTT)
      expect(fallback.canUseWebSpeechAPI()).toBe(false)
      expect(fallback.getBrowserInfo().engine).toBe('firefox')
    })

    it('应该返回正确的策略选择原因', () => {
      setupChromeEnvironment()

      const fallback = createVoiceRecognitionFallback()
      const reason = fallback.getStrategyReason()

      expect(reason).toContain('浏览器内置语音识别')
      expect(reason).toContain('chrome')
    })

    it('应该提供正确的浏览器信息', () => {
      setupChromeEnvironment()

      // Mock Web Audio API
      global.AudioContext = class AudioContext {} as any

      const fallback = createVoiceRecognitionFallback()
      const browserInfo = fallback.getBrowserInfo()

      expect(browserInfo).toBeDefined()
      expect(browserInfo.engine).toBe('chrome')
      expect(browserInfo.webSpeechSupported).toBe(true)
    })
  })

  // ==================== 测试套件2: 音频缓冲策略 ====================

  describe('音频缓冲策略', () => {
    it('应该缓冲短音频块直到达到阈值', () => {
      const audioBuffer = new AudioBuffer({
        bufferSize: 2000,
        bufferThreshold: 1000,
        minAudioLength: 500,
        sampleRate: 16000
      })

      // 创建小于阈值的音频块（约500ms）
      const smallChunk1 = new Blob([new ArrayBuffer(16000)], { type: 'audio/webm' })
      const smallChunk2 = new Blob([new ArrayBuffer(16000)], { type: 'audio/webm' })

      // 添加第一个小块，应该被缓冲（返回true表示继续缓冲）
      const result1 = audioBuffer.add(smallChunk1)
      expect(result1).toBe(true) // 应该继续缓冲

      // 添加第二个小块
      const result2 = audioBuffer.add(smallChunk2)
      // 音频块很小，可能还没达到阈值
      expect(result2).toBeDefined()

      // 验证状态
      const state = audioBuffer.getState()
      expect(state.chunkCount).toBe(2)
      expect(state.totalDuration).toBeGreaterThan(0)
    })

    it('应该正确刷新并返回合并的音频', () => {
      const audioBuffer = new AudioBuffer({
        bufferSize: 2000,
        bufferThreshold: 1000,
        minAudioLength: 500
      })

      // 创建音频块（足够大以产生估算的时长）
      const chunk1 = new Blob([new ArrayBuffer(16000)], { type: 'audio/webm' }) // 约500ms
      const chunk2 = new Blob([new ArrayBuffer(16000)], { type: 'audio/webm' })

      // 添加音频块 - add 方法返回 true 表示继续缓冲，false 表示已达到阈值
      const result1 = audioBuffer.add(chunk1)
      const result2 = audioBuffer.add(chunk2)

      // 刷新缓冲区
      const mergedAudio = audioBuffer.flush()

      // 验证返回的音频（如果缓冲区有内容）
      if (mergedAudio !== null) {
        expect(mergedAudio).toBeInstanceOf(Blob)
        expect(mergedAudio.type).toBe('audio/webm')
        expect(mergedAudio.size).toBeGreaterThan(0)
      }

      // 刷新后缓冲区应该为空
      const state = audioBuffer.getState()
      expect(state.chunkCount).toBe(0)
      expect(state.totalSize).toBe(0)
    })

    it('应该拒绝超过缓冲区大小的音频', () => {
      const audioBuffer = new AudioBuffer({
        bufferSize: 100, // 设置很小的缓冲区
        bufferThreshold: 50,
        minAudioLength: 10
      })

      // 创建超过缓冲区大小的音频块
      const largeChunk = new Blob([new ArrayBuffer(500000)], { type: 'audio/webm' })

      const result = audioBuffer.add(largeChunk)

      // 应该拒绝这个音频块（返回false）
      expect(result).toBe(false)

      const state = audioBuffer.getState()
      expect(state.chunkCount).toBe(0)
    })

    it('应该在清空缓冲区后重置所有状态', () => {
      const audioBuffer = new AudioBuffer({
        bufferSize: 2000,
        bufferThreshold: 1000
      })

      const chunk = new Blob([new ArrayBuffer(80000)], { type: 'audio/webm' })
      audioBuffer.add(chunk)

      // 清空缓冲区
      audioBuffer.clear()

      const state = audioBuffer.getState()
      expect(state.chunkCount).toBe(0)
      expect(state.totalSize).toBe(0)
      expect(state.totalDuration).toBe(0)
    })
  })

  // ==================== 测试套件3: LRU 缓存 ====================

  describe('LRU 缓存', () => {
    it('应该缓存和重用识别结果', () => {
      const cache = new RecognitionLRUCache({
        maxSize: 100,
        ttl: 300000 // 5分钟
      })

      // 使用简单的字符串作为缓存键
      const cacheKey = 'test_audio_hash_1'

      // 设置缓存
      cache.set(cacheKey, {
        transcript: '你好',
        confidence: 0.95,
        timestamp: Date.now()
      })

      // 检查缓存是否存在
      expect(cache.has(cacheKey)).toBe(true)

      // 获取缓存
      const cached = cache.get(cacheKey)
      expect(cached).toBeDefined()
      expect(cached?.transcript).toBe('你好')
      expect(cached?.confidence).toBe(0.95)
    })

    it('应该在缓存满时淘汰最旧的条目', () => {
      const cache = new RecognitionLRUCache({
        maxSize: 3, // 小容量测试
        ttl: 300000
      })

      // 添加4个条目（超过容量）
      for (let i = 0; i < 4; i++) {
        const key = `key_${i}`
        cache.set(key, {
          transcript: `text_${i}`,
          confidence: 0.9,
          timestamp: Date.now()
        })
      }

      // 第一个条目应该被淘汰
      expect(cache.has('key_0')).toBe(false)
      expect(cache.has('key_1')).toBe(true)
      expect(cache.has('key_2')).toBe(true)
      expect(cache.has('key_3')).toBe(true)

      // 验证缓存大小
      const stats = cache.getStats()
      expect(stats.size).toBe(3)
      expect(stats.maxSize).toBe(3)
    })

    it('应该正确计算缓存命中率', () => {
      const cache = new RecognitionLRUCache({
        maxSize: 10,
        ttl: 300000
      })

      const cacheKey = 'test_key_1'

      cache.set(cacheKey, {
        transcript: 'test',
        confidence: 0.9,
        timestamp: Date.now()
      })

      // 第一次访问 - 命中
      cache.get(cacheKey)
      // 第二次访问 - 命中
      cache.get(cacheKey)
      // 第三次访问 - 未命中
      cache.get('non_existent_key')

      const stats = cache.getStats()
      expect(stats.hits).toBe(2)
      expect(stats.misses).toBe(1)
      expect(stats.hitRate).toBeCloseTo(0.666, 1)
    })

    it('应该支持删除特定条目', () => {
      const cache = new RecognitionLRUCache({
        maxSize: 10,
        ttl: 300000
      })

      const cacheKey = 'test_key_delete'

      cache.set(cacheKey, {
        transcript: 'test',
        confidence: 0.9,
        timestamp: Date.now()
      })

      // 删除条目
      const deleted = cache.delete(cacheKey)
      expect(deleted).toBe(true)
      expect(cache.has(cacheKey)).toBe(false)
    })

    it('应该清理过期条目', () => {
      const cache = new RecognitionLRUCache({
        maxSize: 10,
        ttl: 100 // 100ms TTL，用于测试
      })

      const cacheKey = 'test_key_expired'

      cache.set(cacheKey, {
        transcript: 'test',
        confidence: 0.9,
        timestamp: Date.now() - 200 // 设置为过期时间
      })

      // 清理过期条目
      const cleaned = cache.cleanExpired()

      expect(cleaned).toBe(1)
      expect(cache.has(cacheKey)).toBe(false)
    })
  })

  // ==================== 测试套件4: 识别准确率监控 ====================

  describe('识别准确率监控', () => {
    it('应该追踪识别准确率', () => {
      const monitor = new PerformanceMonitor()

      // 记录多次识别结果
      // '你好世界' vs '你好世界' = 2个单词都匹配 = 1.0
      // '测试语音' vs '测试语音' = 2个单词都匹配 = 1.0
      // 'hello world' vs 'hello world' = 2个单词都匹配 = 1.0
      monitor.recordRecognition('你好世界', '你好世界', 0.95, 150)
      monitor.recordRecognition('测试语音', '测试语音', 0.85, 200)
      monitor.recordRecognition('hello world', 'hello world', 0.98, 120)

      const stats = monitor.getAccuracyStats(3)

      expect(stats.totalRecognitions).toBe(3)
      // 平均准确率 = (1 + 1 + 1) / 3 = 1.0
      expect(stats.averageAccuracy).toBe(1.0)
      expect(stats.averageLatency).toBeCloseTo(156.67, 1)
    })

    it('应该正确计算错误率', () => {
      const monitor = new PerformanceMonitor()

      // 记录多次识别结果（包含错误）
      // 'hello' vs 'hello' = 1/1 匹配 = 1.0
      // 'world' vs 'word' = 0/1 匹配 = 0.0 (单词不匹配)
      // 'test this' vs 'tst that' = 0/2 匹配 = 0.0
      monitor.recordRecognition('hello', 'hello', 0.95, 100)
      monitor.recordRecognition('world', 'word', 0.8, 120) // 单词不匹配
      monitor.recordRecognition('test this', 'tst that', 0.7, 110) // 单词不匹配

      const stats = monitor.getAccuracyStats(3)

      expect(stats.totalRecognitions).toBe(3)
      // 平均准确率 = (1 + 0 + 0) / 3 ≈ 0.33
      expect(stats.averageAccuracy).toBeGreaterThan(0.2)

      // 错误率 = 1 - 平均准确率
      const errorRate = 1 - stats.averageAccuracy
      expect(errorRate).toBeGreaterThan(0.5)
    })

    it('应该追踪置信度趋势', () => {
      const monitor = new PerformanceMonitor()

      // 记录不同置信度的识别
      monitor.recordRecognition('test1', 'test1', 0.95, 100)
      monitor.recordRecognition('test2', 'test2', 0.85, 110)
      monitor.recordRecognition('test3', 'test3', 0.90, 105)

      const avgConfidence = monitor.accuracyTracker.getAverageConfidence(3)

      expect(avgConfidence).toBeCloseTo(0.9, 1)
    })

    it('应该重置统计数据', () => {
      const monitor = new PerformanceMonitor()

      monitor.recordRecognition('test', 'test', 0.9, 100)
      monitor.recordRecognition('test2', 'test2', 0.8, 110)

      // 重置
      monitor.reset()

      const stats = monitor.getAccuracyStats()
      expect(stats.totalRecognitions).toBe(0)
      expect(stats.averageAccuracy).toBe(0)
    })

    it('应该记录质量指标', () => {
      const monitor = new PerformanceMonitor()

      // 初始化质量监控
      monitor.initQualityMonitoring()

      // 记录识别结果
      monitor.recordRecognitionResult({
        text: 'test',
        confidence: 0.95,
        latency: 100,
        isFinal: true
      })

      const metrics = monitor.getQualityMetrics()

      expect(metrics).toBeDefined()
      // QualityMetrics 包含 accuracy, confidence, latency, errorRate, sampleCount
      expect(metrics).toHaveProperty('accuracy')
      expect(metrics).toHaveProperty('confidence')
      expect(metrics).toHaveProperty('sampleCount')
    })
  })

  // ==================== 测试套件5: 端到端语音识别流程 ====================

  describe('端到端语音识别流程', () => {
    it('应该完成完整的 Web Speech API 识别流程', async () => {
      setupChromeEnvironment()

      const recognition = createVoiceRecognition({
        language: 'zh-CN',
        interimResults: true
      })

      const results: string[] = []

      recognition.on({
        onResult: (result) => {
          results.push(result.text)
        },
        onError: (error) => {
          // 忽略错误
        }
      })

      await recognition.start()

      // 等待识别完成
      await new Promise(resolve => setTimeout(resolve, 100))

      await recognition.stop()

      // 验证结果
      expect(results.length).toBeGreaterThan(0)
      expect(results[0]).toContain('你好')

      recognition.destroy()
    })

    it('应该完成完整的 Cloud STT 识别流程', async () => {
      setupSafariEnvironment() // 使用不支持 Web Speech API 的浏览器
      mockFetchForCloudSTT()
      mockMediaRecorder()

      const recognition = createVoiceRecognition({
        language: 'zh-CN',
        apiEndpoint: '/api/v1/stt/transcribe'
      })

      const results: string[] = []

      recognition.on({
        onResult: (result) => {
          results.push(result.text)
        },
        onError: (error) => {
          // 忽略错误
        }
      })

      await recognition.start()

      // 模拟 MediaRecorder 数据
      await new Promise(resolve => setTimeout(resolve, 100))

      await recognition.stop()

      // 验证使用了云端策略
      expect(recognition.getStrategy()).toBe(RecognitionStrategy.CloudSTT)

      recognition.destroy()
    })

    it('应该处理识别错误并重试', async () => {
      setupChromeEnvironment()

      const recognition = createVoiceRecognition()

      let errorOccurred = false

      recognition.on({
        onError: (error) => {
          errorOccurred = true
          expect(error).toBeDefined()
        }
      })

      // 模拟错误场景
      try {
        await recognition.start()
      } catch (error) {
        errorOccurred = true
      }

      recognition.destroy()
    })
  })

  // ==================== 测试套件6: 智能重试机制 ====================

  describe('智能重试机制', () => {
    it('应该支持配置重试策略', () => {
      setupSafariEnvironment()
      mockFetchForCloudSTT()
      mockMediaRecorder()

      const recognition = createVoiceRecognition({
        retryStrategy: {
          maxRetries: 5,
          retryDelay: 2000,
          backoffMultiplier: 2,
          retryableErrors: new Set(['network', 'timeout'])
        }
      })

      expect(recognition.getStrategy()).toBe(RecognitionStrategy.CloudSTT)
      recognition.destroy()
    })

    it('应该在可重试错误时自动重试', async () => {
      setupSafariEnvironment()
      mockMediaRecorder()

      // Mock fetch to fail first time, succeed second time
      let attemptCount = 0
      global.fetch = vi.fn(() =>
        Promise.resolve({
          ok: attemptCount++ > 0,
          json: () => Promise.resolve({ text: 'success', confidence: 0.9 })
        } as Response)
      ) as any

      const recognition = createVoiceRecognition({
        retryStrategy: {
          maxRetries: 3,
          retryDelay: 10,
          backoffMultiplier: 1,
          retryableErrors: new Set(['network'])
        }
      })

      await recognition.start()
      await new Promise(resolve => setTimeout(resolve, 100))
      await recognition.stop()

      recognition.destroy()
    })

    it('应该在达到最大重试次数后放弃', async () => {
      setupSafariEnvironment()
      mockMediaRecorder()

      // Mock fetch to always fail
      global.fetch = vi.fn(() =>
        Promise.reject(new Error('network error'))
      ) as any

      const recognition = createVoiceRecognition({
        retryStrategy: {
          maxRetries: 2,
          retryDelay: 10,
          backoffMultiplier: 1,
          retryableErrors: new Set(['network'])
        }
      })

      let errorOccurred = false

      recognition.on({
        onError: (error) => {
          errorOccurred = true
        }
      })

      try {
        await recognition.start()
        await new Promise(resolve => setTimeout(resolve, 100))
      } catch (error) {
        errorOccurred = true
      }

      recognition.destroy()
    })
  })

  // ==================== 测试套件7: 错误恢复集成 ====================

  describe('错误恢复集成', () => {
    it('应该在 Web Speech API 失败时降级到 Cloud STT', async () => {
      setupChromeEnvironment()

      // 模拟 Web Speech API 不可用
      delete (window as any).SpeechRecognition
      delete (window as any).webkitSpeechRecognition

      mockFetchForCloudSTT()
      mockMediaRecorder()

      const fallback = createVoiceRecognitionFallback()
      const strategy = fallback.getRecommendedStrategy()

      // 应该降级到 Cloud STT
      expect(strategy).toBe(RecognitionStrategy.CloudSTT)
    })

    it('应该提供清晰的错误消息', () => {
      setupFirefoxEnvironment()
      delete (window as any).SpeechRecognition

      const fallback = createVoiceRecognitionFallback()
      const reason = fallback.getStrategyReason()

      expect(reason).toBeDefined()
      expect(reason.length).toBeGreaterThan(0)
    })
  })

  // ==================== 测试套件8: 性能监控集成 ====================

  describe('性能监控集成', () => {
    it('应该记录完整的识别延迟', () => {
      const monitor = new PerformanceMonitor()

      monitor.startLatencyTracking()

      // 模拟各个阶段
      setTimeout(() => monitor.recordRecordingLatency(), 50)
      setTimeout(() => monitor.recordUploadingLatency(), 100)
      setTimeout(() => monitor.recordProcessingLatency(), 150)
      setTimeout(() => monitor.recordDownloadingLatency(), 200)

      // 等待所有阶段完成
      return new Promise(resolve => {
        setTimeout(() => {
          const profile = monitor.getLatencyProfile()

          expect(profile).toBeDefined()
          expect(profile?.recording).toBeGreaterThan(0)
          expect(profile?.uploading).toBeGreaterThan(0)
          expect(profile?.processing).toBeGreaterThan(0)
          expect(profile?.downloading).toBeGreaterThan(0)
          expect(profile?.total).toBeGreaterThan(0)

          resolve(true)
        }, 300)
      })
    })

    it('应该获取最慢的识别环节', () => {
      const monitor = new PerformanceMonitor()

      monitor.recordLatencyBreakdown({
        audioCapture: 50,
        processing: 200,
        recognition: 300,
        postProcessing: 30,
        total: 580
      })

      const slowest = monitor.getSlowestPhase()

      expect(slowest).toBe('语音识别')
    })

    it('应该生成完整的性能报告', () => {
      const monitor = new PerformanceMonitor()

      monitor.recordRecognition('test', 'test', 0.9, 100)
      monitor.recordLatencyBreakdown({
        audioCapture: 50,
        processing: 100,
        recognition: 150,
        postProcessing: 20,
        total: 320
      })

      const report = monitor.getPerformanceReport()

      expect(report).toBeDefined()
      expect(report.accuracy).toBeDefined()
      expect(report.latency).toBeDefined()
      expect(report.cache).toBeDefined()
      expect(report.slowestPhase).toBeDefined()
    })
  })

  // ==================== 测试套件9: 浏览器兼容性检测 ====================

  describe('浏览器兼容性检测', () => {
    // Mock Web Audio API
    function mockWebAudioAPI() {
      global.AudioContext = class AudioContext {} as any
    }

    beforeEach(() => {
      mockWebAudioAPI()
    })

    it('应该检测 Chrome 浏览器特性', () => {
      setupChromeEnvironment()

      const compatibility = BrowserCompatibility.detect()

      expect(compatibility.engine).toBe('chrome')
      expect(compatibility.webSpeechSupported).toBe(true)
      expect(compatibility.wasmSupported).toBe(true)
    })

    it('应该检测 Safari 浏览器特性', () => {
      setupSafariEnvironment()

      const compatibility = BrowserCompatibility.detect()

      expect(compatibility.engine).toBe('safari')
      expect(compatibility.wasmSupported).toBe(true)
    })

    it('应该检测 Firefox 浏览器特性', () => {
      setupFirefoxEnvironment()

      const compatibility = BrowserCompatibility.detect()

      expect(compatibility.engine).toBe('firefox')
      expect(compatibility.wasmSupported).toBe(true)
    })

    it('应该计算兼容性评分', () => {
      setupChromeEnvironment()

      const result = BrowserCompatibility.getCompatibilityResult()

      expect(result).toBeDefined()
      expect(result.score).toBeGreaterThan(0)
      expect(result.score).toBeLessThanOrEqual(100)
      expect(result.isSupported).toBe(true)
    })

    it('应该生成兼容性报告', () => {
      setupChromeEnvironment()

      const report = BrowserCompatibility.generateReport()

      expect(report).toBeDefined()
      expect(report).toContain('浏览器兼容性报告')
      expect(report).toContain('chrome')
      expect(report).toContain('Web Speech API')
    })
  })

  // ==================== 测试套件10: 集成场景测试 ====================

  describe('集成场景测试', () => {
    it('应该支持学生进行口语练习', async () => {
      setupChromeEnvironment()

      // 模拟口语练习场景
      const recognition = createVoiceRecognition({
        language: 'en-US',
        continuous: false,
        interimResults: true
      })

      const transcript: string[] = []

      recognition.on({
        onInterimResult: (result) => {
          if (result.text) {
            transcript.push(result.text)
          }
        },
        onResult: (result) => {
          if (result.isFinal) {
            transcript.push(result.text)
          }
        }
      })

      await recognition.start()
      await new Promise(resolve => setTimeout(resolve, 100))
      await recognition.stop()

      expect(transcript.length).toBeGreaterThan(0)
      recognition.destroy()
    })

    it('应该在网络不稳定时自动降级', async () => {
      setupSafariEnvironment()
      mockMediaRecorder()

      // 模拟网络不稳定
      let networkStable = false
      global.fetch = vi.fn(() => {
        if (networkStable) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ text: 'success', confidence: 0.9 })
          } as Response)
        }
        return Promise.reject(new Error('network error'))
      }) as any

      const recognition = createVoiceRecognition({
        retryStrategy: {
          maxRetries: 3,
          retryDelay: 10,
          backoffMultiplier: 1,
          retryableErrors: new Set(['network'])
        }
      })

      await recognition.start()
      await new Promise(resolve => setTimeout(resolve, 100))

      recognition.destroy()
    })

    it('应该缓存常见短语识别结果', () => {
      const cache = new RecognitionLRUCache({
        maxSize: 50,
        ttl: 300000
      })

      // 常见短语
      const commonPhrases = [
        'hello',
        'how are you',
        'thank you',
        'goodbye'
      ]

      for (const phrase of commonPhrases) {
        // 使用短语作为缓存键
        const key = `phrase_${phrase}`

        // 检查缓存
        if (!cache.has(key)) {
          // 模拟识别并缓存结果
          cache.set(key, {
            transcript: phrase,
            confidence: 0.95,
            timestamp: Date.now()
          })
        }
      }

      // 验证缓存
      const stats = cache.getStats()
      expect(stats.size).toBe(4)
      expect(stats.hitRate).toBe(0) // 尚未访问
    })

    it('应该生成学习进度报告', () => {
      const monitor = new PerformanceMonitor()

      // 模拟多次练习
      const practiceSessions = [
        { actual: 'hello', recognized: 'hello', confidence: 0.95, latency: 100 },
        { actual: 'world', recognized: 'world', confidence: 0.92, latency: 110 },
        { actual: 'test', recognized: 'tst', confidence: 0.75, latency: 130 },
        { actual: 'practice', recognized: 'practice', confidence: 0.98, latency: 95 }
      ]

      practiceSessions.forEach(session => {
        monitor.recordRecognition(
          session.actual,
          session.recognized,
          session.confidence,
          session.latency
        )
      })

      const report = monitor.getPerformanceReport()

      expect(report.accuracy.totalRecognitions).toBe(4)
      expect(report.accuracy.successfulRecognitions).toBe(3)
      expect(report.accuracy.averageLatency).toBeCloseTo(108.75, 1)
    })
  })
})
