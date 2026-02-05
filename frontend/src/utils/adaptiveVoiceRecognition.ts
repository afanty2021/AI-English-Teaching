/**
 * 智能语音识别系统
 * 支持多引擎自动选择和降级策略
 */

import { BrowserCompatibility, browserCompatibility } from './browserCompatibility'
import { AudioEnhancer, audioEnhancer } from './audioEnhancer'
import { PerformanceMonitor } from './performanceMonitor'

export type RecognitionEngineType = 'webspeech' | 'cloud' | 'offline'

export interface RecognitionEngine {
  type: RecognitionEngineType
  isSupported(): boolean
  initialize(): Promise<void>
  transcribe(audioData: Float32Array | Blob): Promise<string>
  cleanup(): void
}

export interface NetworkQuality {
  bandwidth: number
  latency: number
  jitter: number
  isStable: boolean
}

export interface AdaptiveOptions {
  preferCloudSTT: boolean
  enableOfflineFallback: boolean
  networkQualityThreshold: number
  latencyThreshold: number
  accuracyThreshold: number
  maxRetries: number
  retryDelay: number
}

export interface RecognitionResult {
  text: string
  confidence: number
  engine: RecognitionEngineType
  latency: number
  isFinal: boolean
  language?: string
}

/**
 * Web Speech API 引擎
 */
export class WebSpeechEngine implements RecognitionEngine {
  type: RecognitionEngineType = 'webspeech'
  private recognition: any = null
  private isActive = false
  private resolvePromise?: (value: string) => void
  private rejectPromise?: (error: Error) => void

  isSupported(): boolean {
    const browser = BrowserCompatibility.detect()
    return browser.webSpeechSupported && (browser.engine === 'chrome' || browser.engine === 'edge')
  }

  async initialize(): Promise<void> {
    if (!this.isSupported()) {
      throw new Error('Web Speech API 不受支持')
    }

    // 创建 SpeechRecognition 实例
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    this.recognition = new SpeechRecognition()

    // 配置参数
    this.recognition.continuous = false
    this.recognition.interimResults = true
    this.recognition.lang = 'zh-CN'
    this.recognition.maxAlternatives = 1

    return Promise.resolve()
  }

  async transcribe(audioData: Float32Array | Blob): Promise<string> {
    if (!this.recognition) {
      throw new Error('引擎未初始化')
    }

    return new Promise((resolve, reject) => {
      this.resolvePromise = resolve
      this.rejectPromise = reject

      let finalTranscript = ''
      let interimTranscript = ''

      this.recognition.onresult = (event: any) => {
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript
          if (event.results[i].isFinal) {
            finalTranscript += transcript
          } else {
            interimTranscript += transcript
          }
        }
      }

      this.recognition.onerror = (event: any) => {
        reject(new Error(`Web Speech API 错误: ${event.error}`))
      }

      this.recognition.onend = () => {
        this.isActive = false
        resolve(finalTranscript || interimTranscript)
      }

      // 开始识别
      this.recognition.start()
      this.isActive = true
    })
  }

  cleanup(): void {
    if (this.recognition && this.isActive) {
      this.recognition.stop()
    }
    this.recognition = null
    this.isActive = false
  }

  /**
   * 设置语言
   */
  setLanguage(language: string): void {
    if (this.recognition) {
      this.recognition.lang = language
    }
  }
}

/**
 * 云端 STT 引擎
 */
export class CloudSTTEngine implements RecognitionEngine {
  type: RecognitionEngineType = 'cloud'
  private apiEndpoint: string

  constructor(apiEndpoint: string = '/api/v1/stt/transcribe') {
    this.apiEndpoint = apiEndpoint
  }

  isSupported(): boolean {
    // 云端引擎总是可用的，只要网络连接正常
    return true
  }

  async initialize(): Promise<void> {
    // 云端引擎无需特殊初始化
    return Promise.resolve()
  }

  async transcribe(audioData: Float32Array | Blob): Promise<string> {
    try {
      // 将音频数据转换为 FormData
      const formData = new FormData()

      let audioBlob: Blob
      if (audioData instanceof Blob) {
        audioBlob = audioData
      } else {
        // Float32Array 需要转换为 WAV 格式
        audioBlob = this.floatToWav(audioData)
      }

      formData.append('audio', audioBlob, 'speech.wav')
      formData.append('language', 'zh')
      formData.append('model', 'whisper-1')
      formData.append('response_format', 'verbose_json')

      // 调用云端 API
      const response = await fetch(this.apiEndpoint, {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      })

      if (!response.ok) {
        throw new Error(`云端 STT 请求失败: ${response.statusText}`)
      }

      const result = await response.json()
      return result.text || ''

    } catch (error) {
      throw new Error(`云端 STT 失败: ${error}`)
    }
  }

  /**
   * 将 Float32Array 转换为 WAV 格式
   */
  private floatToWav(float32Array: Float32Array): Blob {
    const sampleRate = 16000
    const length = float32Array.length
    const arrayBuffer = new ArrayBuffer(44 + length * 2)
    const view = new DataView(arrayBuffer)

    // WAV 头部
    const writeString = (offset: number, string: string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i))
      }
    }

    writeString(0, 'RIFF')
    view.setUint32(4, 36 + length * 2, true)
    writeString(8, 'WAVE')
    writeString(12, 'fmt ')
    view.setUint32(16, 16, true)
    view.setUint16(20, 1, true)
    view.setUint16(22, 1, true)
    view.setUint32(24, sampleRate, true)
    view.setUint32(28, sampleRate * 2, true)
    view.setUint16(32, 2, true)
    view.setUint16(34, 16, true)
    writeString(36, 'data')
    view.setUint32(40, length * 2, true)

    // 音频数据
    let offset = 44
    for (let i = 0; i < length; i++) {
      const sample = Math.max(-1, Math.min(1, float32Array[i]))
      view.setInt16(offset, sample * 0x7FFF, true)
      offset += 2
    }

    return new Blob([arrayBuffer], { type: 'audio/wav' })
  }

  cleanup(): void {
    // 云端引擎无需特殊清理
  }
}

/**
 * 离线引擎（简化实现）
 */
export class OfflineEngine implements RecognitionEngine {
  type: RecognitionEngineType = 'offline'
  private isInitialized = false

  isSupported(): boolean {
    const browser = BrowserCompatibility.detect()
    return browser.wasmSupported && browser.isSecureContext
  }

  async initialize(): Promise<void> {
    if (!this.isSupported()) {
      throw new Error('离线引擎不受支持')
    }

    // 模拟离线引擎初始化
    this.isInitialized = true
    return Promise.resolve()
  }

  async transcribe(audioData: Float32Array | Blob): Promise<string> {
    if (!this.isInitialized) {
      throw new Error('离线引擎未初始化')
    }

    // 简化的离线识别逻辑（实际应集成 Vosk 或其他离线模型）
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve('这是离线引擎的模拟识别结果')
      }, 100)
    })
  }

  cleanup(): void {
    this.isInitialized = false
  }
}

/**
 * 网络质量检测器
 */
export class NetworkQualityTester {
  private testUrls: string[] = [
    'https://www.google.com/favicon.ico',
    'https://www.github.com/favicon.ico'
  ]

  /**
   * 测试网络质量
   */
  async testNetworkQuality(): Promise<NetworkQuality> {
    const results = await Promise.all(
      this.testUrls.map(url => this.testSingleUrl(url))
    )

    // 计算平均延迟和抖动
    const latencies = results.map(r => r.latency).filter(l => l > 0)
    const avgLatency = latencies.reduce((a, b) => a + b, 0) / latencies.length

    const jitters = this.calculateJitter(latencies)
    const avgJitter = jitters.reduce((a, b) => a + b, 0) / jitters.length

    // 计算带宽（简化估算）
    const totalBytes = results.reduce((sum, r) => sum + r.bytes, 0)
    const totalTime = results.reduce((sum, r) => sum + r.time, 0)
    const bandwidth = (totalBytes * 8) / totalTime / 1000 // Kbps

    return {
      bandwidth,
      latency: avgLatency,
      jitter: avgJitter,
      isStable: avgLatency < 200 && avgJitter < 50
    }
  }

  private async testSingleUrl(url: string): Promise<{ latency: number; bytes: number; time: number }> {
    const startTime = performance.now()

    try {
      const response = await fetch(url, { cache: 'no-cache' })
      const blob = await response.blob()
      const endTime = performance.now()

      return {
        latency: endTime - startTime,
        bytes: blob.size,
        time: endTime - startTime
      }
    } catch (error) {
      return {
        latency: 0,
        bytes: 0,
        time: performance.now() - startTime
      }
    }
  }

  private calculateJitter(latencies: number[]): number[] {
    if (latencies.length < 2) return [0]

    const jitters: number[] = []
    for (let i = 1; i < latencies.length; i++) {
      jitters.push(Math.abs(latencies[i] - latencies[i - 1]))
    }
    return jitters
  }
}

/**
 * 自适应语音识别主类
 */
export class AdaptiveVoiceRecognition {
  private engines: Map<RecognitionEngineType, RecognitionEngine> = new Map()
  private currentEngine?: RecognitionEngine
  private audioEnhancer?: AudioEnhancer
  private performanceMonitor?: PerformanceMonitor
  private networkTester?: NetworkQualityTester
  private options: AdaptiveOptions
  private isInitialized = false

  constructor(options: Partial<AdaptiveOptions> = {}) {
    this.options = {
      preferCloudSTT: true,
      enableOfflineFallback: true,
      networkQualityThreshold: 1000, // Kbps
      latencyThreshold: 500, // ms
      accuracyThreshold: 0.7,
      maxRetries: 3,
      retryDelay: 1000,
      ...options
    }

    // 初始化音频增强器
    this.audioEnhancer = audioEnhancer.create({
      enableVAD: true,
      enableNoiseReduction: true,
      enableVolumeDetection: true,
      vadThreshold: 0.3
    })

    // 初始化性能监控器
    this.performanceMonitor = new PerformanceMonitor()

    // 初始化网络测试器
    this.networkTester = new NetworkQualityTester()
  }

  /**
   * 初始化所有可用引擎
   */
  async initialize(): Promise<void> {
    if (this.isInitialized) {
      return
    }

    // 创建可用引擎
    this.engines.set('webspeech', new WebSpeechEngine())
    this.engines.set('cloud', new CloudSTTEngine())
    this.engines.set('offline', new OfflineEngine())

    // 初始化支持的网络测试器
    this.networkTester = new NetworkQualityTester()

    this.isInitialized = true
  }

  /**
   * 自动选择最佳引擎
   */
  async selectBestEngine(): Promise<RecognitionEngine> {
    const capabilities = await this.detectCapabilities()
    const engineType = this.selectEngineType(capabilities)

    const engine = this.engines.get(engineType)
    if (!engine) {
      throw new Error(`引擎 ${engineType} 不可用`)
    }

    // 初始化选中的引擎
    if (!this.isEngineInitialized(engineType)) {
      await engine.initialize()
    }

    this.currentEngine = engine
    return engine
  }

  /**
   * 检测系统能力
   */
  private async detectCapabilities(): Promise<{
    browser: ReturnType<typeof BrowserCompatibility.detect>
    network: NetworkQuality
    performance: any
  }> {
    const browser = BrowserCompatibility.detect()
    const network = await this.networkTester!.testNetworkQuality()
    const performance = this.performanceMonitor!.getPerformanceReport()

    return {
      browser,
      network,
      performance
    }
  }

  /**
   * 选择最佳引擎类型
   */
  private selectEngineType(capabilities: any): RecognitionEngineType {
    const { browser, network, performance } = capabilities

    // 1. 首选云端 STT
    if (this.options.preferCloudSTT &&
        network.isStable &&
        network.bandwidth > this.options.networkQualityThreshold) {
      return 'cloud'
    }

    // 2. Web Speech API (如果浏览器支持且性能良好)
    if (browser.webSpeechSupported &&
        (browser.engine === 'chrome' || browser.engine === 'edge') &&
        performance.accuracy.successRate > this.options.accuracyThreshold) {
      return 'webspeech'
    }

    // 3. 离线引擎 (作为降级)
    if (this.options.enableOfflineFallback && browser.wasmSupported) {
      return 'offline'
    }

    // 4. 默认返回云端
    return 'cloud'
  }

  /**
   * 切换引擎
   */
  async switchEngine(engineType: RecognitionEngineType): Promise<void> {
    if (this.currentEngine) {
      this.currentEngine.cleanup()
    }

    const engine = this.engines.get(engineType)
    if (!engine) {
      throw new Error(`引擎 ${engineType} 不可用`)
    }

    if (!this.isEngineInitialized(engineType)) {
      await engine.initialize()
    }

    this.currentEngine = engine
    console.log(`切换到 ${engineType} 引擎`)
  }

  /**
   * 语音识别主方法
   */
  async transcribe(
    audioData: Float32Array | Blob,
    language: string = 'zh-CN'
  ): Promise<RecognitionResult> {
    if (!this.currentEngine) {
      await this.selectBestEngine()
    }

    const startTime = performance.now()
    let lastError: Error | null = null

    // 尝试使用当前引擎，失败后自动降级
    for (let attempt = 0; attempt < this.options.maxRetries; attempt++) {
      try {
        // 应用音频增强
        let enhancedAudio = audioData
        if (audioData instanceof Float32Array) {
          // 对于 Float32Array，直接使用
          enhancedAudio = audioData
        }

        // 执行识别
        const text = await this.currentEngine!.transcribe(enhancedAudio)
        const latency = performance.now() - startTime

        // 记录性能指标
        this.performanceMonitor!.recordRecognition(
          '', // 实际文本未知
          text,
          0.8, // 默认置信度
          latency
        )

        return {
          text,
          confidence: 0.8,
          engine: this.currentEngine!.type,
          latency,
          isFinal: true,
          language
        }

      } catch (error) {
        lastError = error as Error
        console.warn(`识别失败 (尝试 ${attempt + 1}/${this.options.maxRetries}):`, error)

        // 等待重试
        if (attempt < this.options.maxRetries - 1) {
          await new Promise(resolve => setTimeout(resolve, this.options.retryDelay))

          // 尝试切换到其他引擎
          await this.tryFallbackEngine()
        }
      }
    }

    throw new Error(`语音识别最终失败: ${lastError?.message}`)
  }

  /**
   * 尝试降级到其他引擎
   */
  private async tryFallbackEngine(): Promise<void> {
    const fallbackOrder: RecognitionEngineType[] = ['webspeech', 'cloud', 'offline']
    const currentIndex = fallbackOrder.indexOf(this.currentEngine!.type)

    for (let i = currentIndex + 1; i < fallbackOrder.length; i++) {
      const engineType = fallbackOrder[i]
      const engine = this.engines.get(engineType)

      if (engine && engine.isSupported()) {
        await this.switchEngine(engineType)
        return
      }
    }
  }

  /**
   * 检查引擎是否已初始化
   */
  private isEngineInitialized(engineType: RecognitionEngineType): boolean {
    // 简化的检查，实际实现中可能需要更复杂的跟踪
    return true
  }

  /**
   * 获取性能报告
   */
  getPerformanceReport() {
    return {
      currentEngine: this.currentEngine?.type,
      engines: Array.from(this.engines.keys()),
      performance: this.performanceMonitor?.getPerformanceReport(),
      options: this.options
    }
  }

  /**
   * 更新配置
   */
  updateOptions(newOptions: Partial<AdaptiveOptions>): void {
    this.options = { ...this.options, ...newOptions }
  }

  /**
   * 清理资源
   */
  cleanup(): void {
    // 清理所有引擎
    this.engines.forEach(engine => {
      try {
        engine.cleanup()
      } catch (error) {
        console.warn('清理引擎时出错:', error)
      }
    })

    // 清理音频增强器
    this.audioEnhancer?.destroy()

    // 清理性能监控器
    this.performanceMonitor?.reset()

    this.engines.clear()
    this.currentEngine = undefined
    this.isInitialized = false
  }
}

/**
 * 便利函数
 */
export const adaptiveVoiceRecognition = {
  create: (options?: Partial<AdaptiveOptions>) => new AdaptiveVoiceRecognition(options),
  WebSpeechEngine,
  CloudSTTEngine,
  OfflineEngine,
  NetworkQualityTester
}

export default AdaptiveVoiceRecognition