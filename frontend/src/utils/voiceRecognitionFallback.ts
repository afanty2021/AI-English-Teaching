/**
 * 语音识别降级策略模块
 * 为不同浏览器提供最优的语音识别方案
 */

import { BrowserCompatibility, BrowserInfo } from './browserCompatibility'
import { AudioBuffer } from './audioBuffer'
import { RecognitionLRUCache } from './recognitionCache'

/**
 * 识别策略枚举
 */
export enum RecognitionStrategy {
  WebSpeechAPI = 'web_speech_api',        // Chrome/Edge 最佳
  CloudSTT = 'cloud_stt',                  // 后端 Whisper
  Hybrid = 'hybrid',                      // 前端+后端混合
  Disabled = 'disabled'                   // 完全不支持
}

/**
 * Web Speech API 接口定义
 * 定义浏览器原生语音识别 API 的类型
 */
export interface SpeechRecognition extends EventTarget {
  /**
   * 设置或返回语音识别的语言
   */
  lang: string

  /**
   * 设置或返回是否连续识别
   */
  continuous: boolean

  /**
   * 设置或返回是否返回临时结果
   */
  interimResults: boolean

  /**
   * 设置或返回最大候选结果数
   */
  maxAlternatives: number

  /**
   * 开始语音识别
   */
  start(): void

  /**
   * 停止语音识别
   */
  stop(): void

  /**
   * 取消语音识别
   */
  abort(): void

  /**
   * 识别结果事件
   */
  onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => unknown) | null

  /**
   * 识别错误事件
   */
  onerror: ((this: SpeechRecognition, ev: SpeechRecognitionErrorEvent) => unknown) | null

  /**
   * 识别开始事件
   */
  onstart: ((this: SpeechRecognition, ev: Event) => unknown) | null

  /**
   * 识别结束事件
   */
  onend: ((this: SpeechRecognition, ev: Event) => unknown) | null

  /**
   * 音频开始事件
   */
  onaudiostart: ((this: SpeechRecognition, ev: Event) => unknown) | null

  /**
   * 音频结束事件
   */
  onaudioend: ((this: SpeechRecognition, ev: Event) => unknown) | null

  /**
   * 语音开始事件
   */
  onspeechstart: ((this: SpeechRecognition, ev: Event) => unknown) | null

  /**
   * 语音结束事件
   */
  onspeechend: ((this: SpeechRecognition, ev: Event) => unknown) | null
}

/**
 * 语音识别事件接口
 */
export interface SpeechRecognitionEvent extends Event {
  /**
   * 识别结果列表
   */
  readonly results: SpeechRecognitionResultList

  /**
   * 识别结果索引
   */
  readonly resultIndex: number

  /**
   * 识别会话历史
   */
  readonly interpretation: unknown
}

/**
 * 语音识别结果列表接口
 */
export interface SpeechRecognitionResultList {
  /**
   * 结果列表长度
   */
  readonly length: number

  /**
   * 获取指定索引的结果
   */
  item(index: number): SpeechRecognitionResult

  [index: number]: SpeechRecognitionResult
}

/**
 * 单个语音识别结果接口
 */
export interface SpeechRecognitionResult {
  /**
   * 是否为最终结果
   */
  readonly isFinal: boolean

  /**
   * 识别候选项列表长度
   */
  readonly length: number

  /**
   * 获取指定索引的候选项
   */
  item(index: number): SpeechRecognitionAlternative

  [index: number]: SpeechRecognitionAlternative
}

/**
 * 识别候选项接口
 */
export interface SpeechRecognitionAlternative {
  /**
   * 识别文本
   */
  readonly transcript: string

  /**
   * 置信度 (0-1)
   */
  readonly confidence: number
}

/**
 * 语音识别错误事件接口
 */
export interface SpeechRecognitionErrorEvent extends Event {
  /**
   * 错误类型
   */
  readonly error: 'no-speech' | 'audio-capture' | 'not-allowed' | 'network' | 'aborted' | 'language-not-supported' | 'service-not-allowed'

  /**
   * 错误消息
   */
  readonly message: string
}

/**
 * SpeechRecognition 构造函数接口
 */
export interface SpeechRecognitionConstructor {
  new (): SpeechRecognition
  prototype: SpeechRecognition
}

/**
 * 重试策略接口
 */
export interface RetryStrategy {
  maxRetries: number
  retryDelay: number
  backoffMultiplier: number
  retryableErrors: Set<string>
}

/**
 * 用户反馈接口
 */
export interface RecognitionFeedback {
  transcript: string
  userCorrection?: string
  wasHelpful: boolean
  timestamp?: number
}

/**
 * 识别准确度跟踪
 */
export interface RecognitionAccuracy {
  totalRecognitions: number
  correctRecognitions: number
  userCorrections: number
  accuracyRate: number
}

/**
 * 语音识别配置接口
 */
export interface RecognitionConfig {
  language?: string          // 识别语言，默认 'zh-CN'
  continuous?: boolean       // 是否连续识别
  interimResults?: boolean   // 是否返回临时结果
  maxAlternatives?: number   // 最大候选结果数
  enableAutoPunctuation?: boolean  // 是否自动标点
  apiEndpoint?: string       // 云端 API 端点
  retryStrategy?: RetryStrategy  // 重试策略配置
}

/**
 * 语音识别结果接口
 */
export interface RecognitionResult {
  text: string               // 识别文本
  confidence: number         // 置信度 0-1
  isFinal: boolean           // 是否最终结果
  alternatives?: Array<{    // 候选结果
    text: string
    confidence: number
  }>
  strategy?: RecognitionStrategy  // 使用的策略
}

/**
 * 语音识别事件回调接口
 */
export interface RecognitionCallbacks {
  onResult?: (result: RecognitionResult) => void
  onInterimResult?: (result: RecognitionResult) => void
  onError?: (error: Error) => void
  onStart?: () => void
  onEnd?: () => void
}

/**
 * 语音识别基础接口
 */
export interface VoiceRecognitionBase {
  start(): Promise<void>
  stop(): Promise<void>
  isSupported(): boolean
  getStrategy(): RecognitionStrategy
  on(callbacks: RecognitionCallbacks): void
  destroy(): void
}

/**
 * 浏览器兼容性降级策略接口
 */
export interface VoiceRecognitionFallback {
  canUseWebSpeechAPI(): boolean
  canUseCloudSTT(): boolean
  canUseHybrid(): boolean
  getRecommendedStrategy(): RecognitionStrategy
  createRecognition(options: RecognitionConfig): VoiceRecognitionBase
  getBrowserInfo(): BrowserInfo
  getStrategyReason(): string
}

/**
 * 默认重试策略
 */
export const DEFAULT_RETRY_STRATEGY: RetryStrategy = {
  maxRetries: 3,
  retryDelay: 1000,
  backoffMultiplier: 2,
  retryableErrors: new Set(['no-speech', 'network', 'aborted'])
}

/**
 * 识别准确度跟踪器
 */
export class RecognitionAccuracyTracker {
  private accuracy: RecognitionAccuracy = {
    totalRecognitions: 0,
    correctRecognitions: 0,
    userCorrections: 0,
    accuracyRate: 1.0
  }
  private feedbackHistory: RecognitionFeedback[] = []
  private readonly MAX_FEEDBACK_HISTORY = 100

  /**
   * 记录识别结果
   */
  recordRecognition(): void {
    this.accuracy.totalRecognitions++
  }

  /**
   * 记录正确的识别
   */
  recordCorrect(): void {
    this.accuracy.correctRecognitions++
    this.updateAccuracyRate()
  }

  /**
   * 记录用户修正
   */
  recordCorrection(): void {
    this.accuracy.userCorrections++
    this.updateAccuracyRate()
  }

  /**
   * 添加用户反馈
   */
  addFeedback(feedback: RecognitionFeedback): void {
    const feedbackWithTimestamp: RecognitionFeedback = {
      ...feedback,
      timestamp: Date.now()
    }
    this.feedbackHistory.push(feedbackWithTimestamp)

    // 限制历史记录大小
    if (this.feedbackHistory.length > this.MAX_FEEDBACK_HISTORY) {
      this.feedbackHistory.shift()
    }

    // 更新准确度
    if (feedback.wasHelpful) {
      this.recordCorrect()
    } else if (feedback.userCorrection) {
      this.recordCorrection()
    }
  }

  /**
   * 获取最近的反馈
   */
  getRecentFeedback(count: number = 10): RecognitionFeedback[] {
    return this.feedbackHistory.slice(-count)
  }

  /**
   * 更新准确率
   */
  private updateAccuracyRate(): void {
    const total = this.accuracy.totalRecognitions
    if (total === 0) {
      this.accuracy.accuracyRate = 1.0
    } else {
      this.accuracy.accuracyRate = this.accuracy.correctRecognitions / total
    }
  }

  /**
   * 获取当前准确度
   */
  getAccuracy(): RecognitionAccuracy {
    return { ...this.accuracy }
  }

  /**
   * 重置统计
   */
  reset(): void {
    this.accuracy = {
      totalRecognitions: 0,
      correctRecognitions: 0,
      userCorrections: 0,
      accuracyRate: 1.0
    }
    this.feedbackHistory = []
  }
}

/**
 * Web Speech API 适配器
 * 使用浏览器内置的语音识别功能
 */
class WebSpeechRecognitionAdapter implements VoiceRecognitionBase {
  private recognition: SpeechRecognition | null = null
  private isActive = false
  private config: RecognitionConfig
  private callbacks: RecognitionCallbacks = {}
  private strategy = RecognitionStrategy.WebSpeechAPI

  constructor(config: RecognitionConfig = {}) {
    this.config = {
      language: 'zh-CN',
      continuous: false,
      interimResults: true,
      maxAlternatives: 1,
      enableAutoPunctuation: true,
      ...config
    }
  }

  isSupported(): boolean {
    const browser = BrowserCompatibility.detect()
    return browser.webSpeechSupported &&
           (browser.engine === 'chrome' || browser.engine === 'edge')
  }

  /**
   * 获取浏览器的 SpeechRecognition 构造函数
   * 使用类型守卫确保类型安全
   */
  private getSpeechRecognitionClass(): SpeechRecognitionConstructor | null {
    const windowWithSpeech = window as unknown as {
      SpeechRecognition?: SpeechRecognitionConstructor
      webkitSpeechRecognition?: SpeechRecognitionConstructor
    }

    return windowWithSpeech.SpeechRecognition ||
           windowWithSpeech.webkitSpeechRecognition ||
           null
  }

  getStrategy(): RecognitionStrategy {
    return this.strategy
  }

  async start(): Promise<void> {
    if (!this.isSupported()) {
      throw new Error('当前浏览器不支持 Web Speech API')
    }

    if (this.isActive) {
      return
    }

    return new Promise((resolve, reject) => {
      try {
        // 类型守卫：检测浏览器是否支持 SpeechRecognition
        const SpeechRecognitionClass = this.getSpeechRecognitionClass()

        if (!SpeechRecognitionClass) {
          reject(new Error('Web Speech API 不可用'))
          return
        }

        this.recognition = new SpeechRecognitionClass()

        // 配置识别参数
        this.recognition.lang = this.config.language || 'zh-CN'
        this.recognition.continuous = this.config.continuous || false
        this.recognition.interimResults = this.config.interimResults !== false
        this.recognition.maxAlternatives = this.config.maxAlternatives || 1

        // 设置事件监听器
        this.recognition.onresult = (event: SpeechRecognitionEvent) => {
          const resultLength = event.results.length
          if (resultLength === 0) {
            return
          }

          // 使用 item() 方法安全地获取结果
          const lastResult = event.results.item(resultLength - 1)
          if (!lastResult || lastResult.length === 0) {
            return
          }

          // 使用 item() 方法安全地获取候选项
          const alternative = lastResult.item(0)
          if (!alternative) {
            return
          }

          const transcript = alternative.transcript
          const confidence = alternative.confidence
          const isFinal = lastResult.isFinal

          const result: RecognitionResult = {
            text: transcript,
            confidence: confidence || 0.8,
            isFinal,
            strategy: this.strategy
          }

          if (isFinal) {
            this.callbacks.onResult?.(result)
          } else {
            this.callbacks.onInterimResult?.(result)
          }
        }

        this.recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
          const error = new Error(`Web Speech API 错误: ${event.error}`)
          this.callbacks.onError?.(error)
          reject(error)
        }

        this.recognition.onstart = () => {
          this.isActive = true
          this.callbacks.onStart?.()
          resolve()
        }

        this.recognition.onend = () => {
          this.isActive = false
          this.callbacks.onEnd?.()
        }

        this.recognition.start()
      } catch (error) {
        reject(error)
      }
    })
  }

  async stop(): Promise<void> {
    if (!this.isActive || !this.recognition) {
      return
    }

    return new Promise((resolve) => {
      const recognition = this.recognition!
      const originalOnEnd = recognition.onend

      recognition.onend = (event: Event) => {
        this.isActive = false
        if (originalOnEnd) {
          originalOnEnd.call(recognition, event)
        }
        resolve()
      }

      // 类型断言：原生 stop() 方法不需要参数
      ;(recognition as unknown as { stop: () => void }).stop()
    })
  }

  on(callbacks: RecognitionCallbacks): void {
    this.callbacks = { ...this.callbacks, ...callbacks }
  }

  destroy(): void {
    if (this.isActive && this.recognition) {
      // 类型断言：原生 stop() 方法不需要参数
      ;(this.recognition as unknown as { stop: () => void }).stop()
    }
    this.recognition = null
    this.isActive = false
    this.callbacks = {}
  }
}

/**
 * 云端 STT 适配器
 * 使用后端 Whisper API 进行语音识别
 * 集成音频缓冲器以解决音频碎片化问题
 * 集成 LRU 缓存以避免重复识别
 */
class CloudSTTAdapter implements VoiceRecognitionBase {
  private config: RecognitionConfig
  private callbacks: RecognitionCallbacks = {}
  private strategy = RecognitionStrategy.CloudSTT
  private mediaRecorder: MediaRecorder | null = null
  private isActive = false
  private audioBuffer: AudioBuffer  // 音频缓冲器
  private cache: RecognitionLRUCache  // LRU 缓存
  private retryStrategy: RetryStrategy  // 重试策略
  private accuracyTracker: RecognitionAccuracyTracker  // 准确度跟踪器
  private readonly MAX_DELAY = 30000  // 30秒最大重试延迟

  constructor(config: RecognitionConfig = {}) {
    this.config = {
      language: 'zh-CN',
      apiEndpoint: '/api/v1/stt/transcribe',
      ...config
    }

    // 初始化重试策略
    this.retryStrategy = this.config.retryStrategy ?? DEFAULT_RETRY_STRATEGY

    // 初始化准确度跟踪器
    this.accuracyTracker = new RecognitionAccuracyTracker()

    // 初始化音频缓冲器
    this.audioBuffer = new AudioBuffer({
      bufferSize: 2000,      // 最大缓冲2秒
      bufferThreshold: 1000, // 1秒后触发识别
      minAudioLength: 500,   // 最小音频长度500ms
      sampleRate: 16000,     // 16kHz采样率
      bitDepth: 16,          // 16bit
      channels: 1            // 单声道
    })

    // 初始化 LRU 缓存
    this.cache = new RecognitionLRUCache({
      maxSize: 100,    // 最多缓存100个识别结果
      ttl: 300000      // 5分钟过期
    })
  }

  isSupported(): boolean {
    // 云端 API 总是可用（假设后端已部署）
    return true
  }

  getStrategy(): RecognitionStrategy {
    return this.strategy
  }

  async start(): Promise<void> {
    if (this.isActive) {
      return
    }

    return new Promise((resolve, reject) => {
      navigator.mediaDevices.getUserMedia({ audio: true })
        .then((stream) => {
          this.mediaRecorder = new MediaRecorder(stream)
          this.audioBuffer.clear()  // 清空缓冲器

          this.mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
              // 先尝试缓冲
              const shouldContinue = this.audioBuffer.add(event.data)

              if (!shouldContinue) {
                // 缓冲器拒绝，说明音频已足够
                // 触发识别
                const bufferedAudio = this.audioBuffer.flush()
                if (bufferedAudio) {
                  void this.transcribeAudio(bufferedAudio)
                }
              }
            }
          }

          this.mediaRecorder.onstop = async () => {
            // 停止时，处理剩余的缓冲音频
            const remainingAudio = this.audioBuffer.flush()
            if (remainingAudio) {
              await this.transcribeAudio(remainingAudio)
            }
          }

          this.mediaRecorder.onstart = () => {
            this.isActive = true
            this.callbacks.onStart?.()
            resolve()
          }

          this.mediaRecorder.start()
        })
        .catch((error) => {
          this.callbacks.onError?.(error)
          reject(error)
        })
    })
  }

  async stop(): Promise<void> {
    if (!this.isActive || !this.mediaRecorder) {
      return
    }

    return new Promise((resolve) => {
      if (this.mediaRecorder?.state === 'recording') {
        this.mediaRecorder.stop()
      }

      // 等待转录完成
      setTimeout(() => {
        this.isActive = false
        this.callbacks.onEnd?.()
        resolve()
      }, 100)
    })
  }

  private async transcribeAudio(audioBlob: Blob): Promise<void> {
    // 生成缓存键（使用 SHA-256 哈希确保唯一性）
    const cacheKey = await this.generateCacheKey(audioBlob)

    // 检查缓存
    const cached = this.cache.get(cacheKey)
    if (cached) {
      // 缓存命中，直接返回缓存结果
      this.callbacks.onResult?.({
        text: cached.transcript,
        confidence: cached.confidence,
        isFinal: true,
        strategy: this.strategy
      })
      return
    }

    // 缓存未命中，执行识别
    try {
      const formData = new FormData()
      formData.append('audio', audioBlob, 'speech.webm')
      formData.append('language', this.config.language === 'zh-CN' ? 'zh' : 'en')
      formData.append('model', 'whisper-1')

      const response = await fetch(this.config.apiEndpoint!, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: formData
      })

      if (!response.ok) {
        throw new Error(`云端 STT 请求失败: ${response.statusText}`)
      }

      const result = await response.json()

      const recognitionResult: RecognitionResult = {
        text: result.text || '',
        confidence: 0.85, // Whisper 通常有较高的准确率
        isFinal: true,
        strategy: this.strategy
      }

      // 存入缓存
      this.cache.set(cacheKey, {
        transcript: result.text || '',
        confidence: 0.85,
        timestamp: Date.now()
      })

      this.callbacks.onResult?.(recognitionResult)
    } catch (error) {
      const errorObj = error instanceof Error ? error : new Error(String(error))
      this.callbacks.onError?.(errorObj)
    }
  }

  /**
   * 生成音频 Blob 的缓存键
   * 使用 Web Crypto API 的 SHA-256 哈希确保缓存键的唯一性
   * 这避免了基于大小的简单键可能产生的碰撞问题
   * @param audioBlob 音频数据
   * @returns Promise<string> 缓存键（前缀 + SHA-256 哈希的十六进制表示）
   */
  private async generateCacheKey(audioBlob: Blob): Promise<string> {
    try {
      // 将 Blob 转换为 ArrayBuffer
      const arrayBuffer = await audioBlob.arrayBuffer()

      // 使用 Web Crypto API 计算 SHA-256 哈希
      const hashBuffer = await crypto.subtle.digest('SHA-256', arrayBuffer)

      // 将 ArrayBuffer 转换为十六进制字符串
      const hashArray = Array.from(new Uint8Array(hashBuffer))
      const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('')

      // 返回带前缀的缓存键
      return `stt_${hashHex}`
    } catch (error) {
      // 如果哈希计算失败，降级到基于大小的简单键
      // 这种情况下仍然能工作，但可能产生碰撞
      console.warn('Failed to generate SHA-256 hash, falling back to size-based key:', error)
      return `stt_fallback_${audioBlob.size}_${audioBlob.type}`
    }
  }

  on(callbacks: RecognitionCallbacks): void {
    this.callbacks = { ...this.callbacks, ...callbacks }
  }

  /**
   * 带重试的启动方法
   * 在遇到可重试错误时自动重试，使用指数退避策略
   * @param timeoutMs 总超时时间，默认60000ms（60秒）
   */
  async startWithRetry(timeoutMs: number = 60000): Promise<void> {
    const startTime = Date.now()
    let lastError: Error | null = null

    for (let attempt = 0; attempt <= this.retryStrategy.maxRetries; attempt++) {
      // 检查超时
      if (Date.now() - startTime > timeoutMs) {
        throw new Error(`Retry timeout exceeded after ${timeoutMs}ms`)
      }

      try {
        await this.start()
        // 启动成功，记录识别
        this.accuracyTracker.recordRecognition()
        return
      } catch (error) {
        lastError = error as Error

        // 检查是否可重试
        if (!this.isRetryableError(lastError)) {
          // 不可重试的错误，直接抛出
          throw lastError
        }

        // 如果还有重试机会，等待后重试
        if (attempt < this.retryStrategy.maxRetries) {
          const delay = this.calculateRetryDelay(attempt)
          await this.sleep(delay)
        }
      }
    }

    // 所有重试都失败，抛出最后一个错误
    throw lastError
  }

  /**
   * 检查错误是否可重试
   */
  private isRetryableError(error: Error): boolean {
    const message = error.message.toLowerCase()

    for (const retryableError of this.retryStrategy.retryableErrors) {
      if (message.includes(retryableError.toLowerCase())) {
        return true
      }
    }

    return false
  }

  /**
   * 计算重试延迟（指数退避）
   * 延迟会被限制在 MAX_DELAY (30000ms) 以内
   */
  private calculateRetryDelay(attempt: number): number {
    const delay = this.retryStrategy.retryDelay *
                  Math.pow(this.retryStrategy.backoffMultiplier, attempt)
    return Math.min(delay, this.MAX_DELAY)
  }

  /**
   * 异步等待函数
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  /**
   * 提交用户反馈
   */
  submitFeedback(feedback: RecognitionFeedback): void {
    this.accuracyTracker.addFeedback(feedback)
  }

  /**
   * 获取识别准确度统计
   */
  getAccuracy(): RecognitionAccuracy {
    return this.accuracyTracker.getAccuracy()
  }

  /**
   * 获取最近的反馈记录
   */
  getRecentFeedback(count?: number): RecognitionFeedback[] {
    return this.accuracyTracker.getRecentFeedback(count)
  }

  /**
   * 更新识别准确度（当用户手动更正识别结果时调用）
   */
  updateAccuracy(transcript: string, userCorrection: string): void {
    this.submitFeedback({
      transcript,
      userCorrection,
      wasHelpful: false
    })
  }

  destroy(): void {
    if (this.isActive && this.mediaRecorder) {
      this.mediaRecorder.stop()
    }
    this.mediaRecorder = null
    this.audioBuffer.clear()  // 清空缓冲器
    this.cache.clear()        // 清空缓存
    this.isActive = false
    this.callbacks = {}
    this.accuracyTracker.reset()  // 重置准确度跟踪
  }
}

/**
 * 语音识别降级策略实现类
 */
export class VoiceRecognitionFallback implements VoiceRecognitionFallback {
  private browserInfo: BrowserInfo
  private hasApiKey: boolean

  constructor() {
    this.browserInfo = BrowserCompatibility.detect()
    // 检查是否配置了 API key（用于云端 STT）
    this.hasApiKey = !!import.meta.env.VITE_OPENAI_API_KEY ||
                    !!localStorage.getItem('openai_api_key')
  }

  /**
   * 检查是否可以使用 Web Speech API
   */
  canUseWebSpeechAPI(): boolean {
    return this.browserInfo.webSpeechSupported &&
           (this.browserInfo.engine === 'chrome' ||
            this.browserInfo.engine === 'edge')
  }

  /**
   * 检查是否可以使用云端 STT
   */
  canUseCloudSTT(): boolean {
    return this.hasApiKey || this.hasNetworkAccess()
  }

  /**
   * 检查是否可以使用混合模式
   */
  canUseHybrid(): boolean {
    return this.canUseWebSpeechAPI() && this.canUseCloudSTT()
  }

  /**
   * 获取推荐的识别策略
   */
  getRecommendedStrategy(): RecognitionStrategy {
    // 1. 优先使用浏览器内置 API（最快、无成本）
    if (this.canUseWebSpeechAPI()) {
      return RecognitionStrategy.WebSpeechAPI
    }

    // 2. 降级到云端 STT
    if (this.canUseCloudSTT()) {
      return RecognitionStrategy.CloudSTT
    }

    // 3. 完全不支持，显示提示
    return RecognitionStrategy.Disabled
  }

  /**
   * 创建语音识别实例
   */
  createRecognition(options: RecognitionConfig = {}): VoiceRecognitionBase {
    const strategy = this.getRecommendedStrategy()

    switch (strategy) {
      case RecognitionStrategy.WebSpeechAPI:
        return new WebSpeechRecognitionAdapter(options)

      case RecognitionStrategy.CloudSTT:
        return new CloudSTTAdapter(options)

      case RecognitionStrategy.Disabled:
        throw new Error(
          '当前浏览器不支持语音识别，请使用 Chrome 或 Edge 浏览器。' +
          '或者检查网络连接以使用云端识别服务。'
        )

      default:
        throw new Error(`未知的识别策略: ${strategy}`)
    }
  }

  /**
   * 获取浏览器信息
   */
  getBrowserInfo(): BrowserInfo {
    return this.browserInfo
  }

  /**
   * 获取策略选择原因
   */
  getStrategyReason(): string {
    const strategy = this.getRecommendedStrategy()

    switch (strategy) {
      case RecognitionStrategy.WebSpeechAPI:
        return `使用浏览器内置语音识别（${this.browserInfo.engine} ${this.browserInfo.version}），无需网络连接，响应速度最快。`

      case RecognitionStrategy.CloudSTT:
        return `当前浏览器（${this.browserInfo.engine}）不支持 Web Speech API，已降级到云端语音识别服务。需要稳定的网络连接。`

      case RecognitionStrategy.Disabled:
        return `当前浏览器不支持语音识别，且无法连接到云端服务。建议使用 Chrome 或 Edge 浏览器。`

      default:
        return '未知策略'
    }
  }

  /**
   * 检查是否有网络访问
   */
  private hasNetworkAccess(): boolean {
    // 简化检查：假设如果有网络环境就可以使用云端服务
    // 实际实现可能需要 ping 测试
    return typeof navigator.onLine === 'boolean' ? navigator.onLine : true
  }
}

/**
 * 便利函数：创建降级策略实例
 */
export function createVoiceRecognitionFallback(): VoiceRecognitionFallback {
  return new VoiceRecognitionFallback()
}

/**
 * 便利函数：获取推荐的识别策略
 */
export function getRecommendedRecognitionStrategy(): RecognitionStrategy {
  const fallback = createVoiceRecognitionFallback()
  return fallback.getRecommendedStrategy()
}

/**
 * 便利函数：创建语音识别实例
 */
export function createVoiceRecognition(
  options?: RecognitionConfig
): VoiceRecognitionBase {
  const fallback = createVoiceRecognitionFallback()
  return fallback.createRecognition(options)
}

/**
 * 便利函数：检查是否支持语音识别
 */
export function isVoiceRecognitionSupported(): boolean {
  const strategy = getRecommendedRecognitionStrategy()
  return strategy !== RecognitionStrategy.Disabled
}

/**
 * 便利函数：获取策略说明
 */
export function getStrategyDescription(): string {
  const fallback = createVoiceRecognitionFallback()
  return fallback.getStrategyReason()
}

// 默认导出
export default VoiceRecognitionFallback
