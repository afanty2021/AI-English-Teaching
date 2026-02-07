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
 * 语音识别配置接口
 */
export interface RecognitionConfig {
  language?: string          // 识别语言，默认 'zh-CN'
  continuous?: boolean       // 是否连续识别
  interimResults?: boolean   // 是否返回临时结果
  maxAlternatives?: number   // 最大候选结果数
  enableAutoPunctuation?: boolean  // 是否自动标点
  apiEndpoint?: string       // 云端 API 端点
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
 * Web Speech API 适配器
 * 使用浏览器内置的语音识别功能
 */
class WebSpeechRecognitionAdapter implements VoiceRecognitionBase {
  private recognition: any = null
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
        const SpeechRecognition = (window as any).SpeechRecognition ||
                                   (window as any).webkitSpeechRecognition

        if (!SpeechRecognition) {
          reject(new Error('Web Speech API 不可用'))
          return
        }

        this.recognition = new SpeechRecognition()

        // 配置识别参数
        this.recognition.lang = this.config.language || 'zh-CN'
        this.recognition.continuous = this.config.continuous || false
        this.recognition.interimResults = this.config.interimResults !== false
        this.recognition.maxAlternatives = this.config.maxAlternatives || 1

        // 设置事件监听器
        this.recognition.onresult = (event: any) => {
          const lastResult = event.results[event.results.length - 1]
          const transcript = lastResult[0].transcript
          const confidence = lastResult[0].confidence
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

        this.recognition.onerror = (event: any) => {
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
      const originalOnEnd = this.recognition.onend

      this.recognition.onend = () => {
        this.isActive = false
        originalOnEnd?.()
        resolve()
      }

      this.recognition.stop()
    })
  }

  on(callbacks: RecognitionCallbacks): void {
    this.callbacks = { ...this.callbacks, ...callbacks }
  }

  destroy(): void {
    if (this.isActive && this.recognition) {
      this.recognition.stop()
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

  constructor(config: RecognitionConfig = {}) {
    this.config = {
      language: 'zh-CN',
      apiEndpoint: '/api/v1/stt/transcribe',
      ...config
    }

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
    // 生成缓存键
    const cacheKey = this.generateCacheKey(audioBlob)

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
   * 基于音频大小和类型生成简化的缓存键
   * 注意：为了提高缓存命中率，这里使用简化的键生成策略
   * 在实际应用中，可以考虑使用音频内容的哈希值作为键
   * @param audioBlob 音频数据
   * @returns 缓存键
   */
  private generateCacheKey(audioBlob: Blob): string {
    // 简化版缓存键：基于大小和类型
    // 注意：这只是一个简化实现，可能产生哈希冲突
    // 实际应用中建议使用音频内容的哈希值（如 SHA-256）
    return `stt_${audioBlob.size}_${audioBlob.type}`
  }

  on(callbacks: RecognitionCallbacks): void {
    this.callbacks = { ...this.callbacks, ...callbacks }
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
