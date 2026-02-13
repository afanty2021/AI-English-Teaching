/**
 * 语音识别工具模块
 * 支持 Web Speech API 和后端 STT 服务
 */

import { createLogger } from '../utils/logger'

const log = createLogger('VoiceRecognition')

/**
 * Web Speech API 类型定义
 */
// 扩展 Window 接口以支持 SpeechRecognition
interface Window {
  SpeechRecognition: new () => SpeechRecognitionInterface
  webkitSpeechRecognition: new () => SpeechRecognitionInterface
}

interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList
  resultIndex: number
}

interface SpeechRecognitionResultList {
  length: number
  item(index: number): SpeechRecognitionResult
  [index: number]: SpeechRecognitionResult
}

interface SpeechRecognitionResult {
  length: number
  isFinal: boolean
  item(index: number): SpeechRecognitionAlternative
  [index: number]: SpeechRecognitionAlternative
}

interface SpeechRecognitionAlternative {
  transcript: string
  confidence: number
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string
  message: string
}

interface SpeechRecognitionInterface extends EventTarget {
  lang: string
  continuous: boolean
  interimResults: boolean
  maxAlternatives: number
  onstart: ((this: SpeechRecognitionInterface, ev: Event) => void) | null
  onend: ((this: SpeechRecognitionInterface, ev: Event) => void) | null
  onresult: ((this: SpeechRecognitionInterface, ev: SpeechRecognitionEvent) => void) | null
  onerror: ((this: SpeechRecognitionInterface, ev: SpeechRecognitionErrorEvent) => void) | null
  start(): void
  stop(): void
  abort(): void
}

/**
 * 语音识别事件类型
 */
export enum VoiceRecognitionEvent {
  Start = 'start',
  Stop = 'stop',
  Result = 'result',
  InterimResult = 'interimResult',
  Error = 'error'
}

/**
 * 语音识别状态
 */
export enum VoiceRecognitionStatus {
  Idle = 'idle',
  Initializing = 'initializing',
  Listening = 'listening',
  Processing = 'processing',
  Error = 'error'
}

/**
 * 语音识别结果
 */
export interface VoiceRecognitionResult {
  transcript: string
  isFinal: boolean
  confidence: number
}

/**
 * 语音识别错误
 */
export interface VoiceRecognitionError {
  code: string
  message: string
}

/**
 * 语音识别配置
 */
export interface VoiceRecognitionConfig {
  language?: string
  continuous?: boolean
  interimResults?: boolean
  maxAlternatives?: number
}

/**
 * 语音识别回调
 */
export interface VoiceRecognitionCallbacks {
  onStart?: () => void
  onStop?: () => void
  onResult?: (result: VoiceRecognitionResult) => void
  onInterimResult?: (result: VoiceRecognitionResult) => void
  onError?: (error: VoiceRecognitionError) => void
  onStatusChange?: (status: VoiceRecognitionStatus) => void
}

/**
 * 语音识别器类
 */
export class VoiceRecognition {
  private recognition: SpeechRecognitionInterface | null = null
  private status: VoiceRecognitionStatus = VoiceRecognitionStatus.Idle
  private callbacks: VoiceRecognitionCallbacks = {}
  private config: VoiceRecognitionConfig = {}

  constructor(config: VoiceRecognitionConfig = {}) {
    this.config = {
      language: 'en-US',
      continuous: false,
      interimResults: true,
      maxAlternatives: 1,
      ...config
    }

    this.initRecognition()
  }

  /**
   * 初始化语音识别
   */
  private initRecognition() {
    log.info('🎙 [VoiceRecognition] initRecognition 开始初始化')

    // 检查浏览器支持
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    log.info('🎙 [VoiceRecognition] 浏览器语音识别API:', SpeechRecognition ? '已找到' : '未找到')

    if (!SpeechRecognition) {
      log.error('❌ [VoiceRecognition] 浏览器不支持语音识别')
      this.setStatus(VoiceRecognitionStatus.Error)
      this.triggerError({
        code: 'not_supported',
        message: '您的浏览器不支持语音识别功能，请使用 Chrome 或 Edge 浏览器'
      })
      return
    }

    try {
      log.info('🎙 [VoiceRecognition] 创建 SpeechRecognition 实例...')
      this.recognition = new SpeechRecognition()
      log.info('✅ [VoiceRecognition] SpeechRecognition 实例创建成功:', this.recognition)
      this.setupRecognition()
    } catch (error) {
      log.error('❌ [VoiceRecognition] 创建实例失败:', error)
      this.setStatus(VoiceRecognitionStatus.Error)
      this.triggerError({
        code: 'init_failed',
        message: '语音识别初始化失败'
      })
    }
  }

  /**
   * 配置语音识别事件
   */
  private setupRecognition() {
    log.info('⚙️ [VoiceRecognition] setupRecognition 开始配置')

    const recognition = this.recognition
    log.info('⚙️ [VoiceRecognition] 当前配置:', this.config)

    recognition.lang = this.config.language || 'en-US'
    recognition.continuous = this.config.continuous || false
    recognition.interimResults = this.config.interimResults || true
    recognition.maxAlternatives = this.config.maxAlternatives || 1

    log.info('⚙️ [VoiceRecognition] 语音识别配置完成:')
    log.info('  - lang:', recognition.lang)
    log.info('  - continuous:', recognition.continuous)
    log.info('  - interimResults:', recognition.interimResults)
    log.info('  - maxAlternatives:', recognition.maxAlternatives)

    // 开始识别
    recognition.onstart = () => {
      log.info('✅ [VoiceRecognition] Web Speech API onstart 事件触发')
      this.setStatus(VoiceRecognitionStatus.Listening)
      this.callbacks.onStart?.()
    }

    // 识别结束
    recognition.onend = () => {
      log.info('⏸ [VoiceRecognition] Web Speech API onend 事件触发, 当前状态:', this.status)

      // 如果 recognition 已被销毁，不尝试重启
      if (!this.recognition) {
        this.setStatus(VoiceRecognitionStatus.Idle)
        this.callbacks.onStop?.()
        return
      }

      if (this.status === VoiceRecognitionStatus.Listening) {
        if (this.config.continuous) {
          // 连续模式下自动重启识别
          log.info('⏸ [VoiceRecognition] 连续模式，自动重启识别')
          try {
            this.setStatus(VoiceRecognitionStatus.Initializing)
            this.recognition.start()
            // 成功启动后，onstart 会将状态设为 Listening
          } catch (error) {
            log.error('❌ [VoiceRecognition] 连续模式重启失败:', error)
            this.setStatus(VoiceRecognitionStatus.Error)
            this.triggerError({
              code: 'continuous_restart_failed',
              message: '连续识别模式重启失败'
            })
            this.callbacks.onStop?.()
          }
        } else {
          this.setStatus(VoiceRecognitionStatus.Idle)
          this.callbacks.onStop?.()
        }
      }
    }

    // 获取结果
    recognition.onresult = (event: SpeechRecognitionEvent) => {
      log.info('📝 [VoiceRecognition] Web Speech API onresult 事件触发')
      const last = event.results.length - 1
      const result = event.results[last]
      log.info('📝 [VoiceRecognition] 识别结果数量:', event.results.length)

      const recognitionResult: VoiceRecognitionResult = {
        transcript: result[0].transcript,
        isFinal: result.isFinal,
        confidence: result[0].confidence
      }

      log.info('📝 [VoiceRecognition] 识别结果:', recognitionResult)

      if (result.isFinal) {
        this.callbacks.onResult?.(recognitionResult)
      } else {
        this.callbacks.onInterimResult?.(recognitionResult)
      }
    }

    // 错误处理
    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      log.error('❌ [VoiceRecognition] Web Speech API onerror 事件触发:', event)
      this.handleRecognitionError(event)
    }

    log.info('⚙️ [VoiceRecognition] 事件监听器注册完成')
  }

  /**
   * 处理识别错误
   */
  private handleRecognitionError(event: SpeechRecognitionErrorEvent) {
    let error: VoiceRecognitionError

    switch (event.error) {
      case 'no-speech':
        error = {
          code: 'no_speech',
          message: '未检测到语音输入'
        }
        break
      case 'audio-capture':
        error = {
          code: 'audio_capture',
          message: '无法访问麦克风'
        }
        break
      case 'not-allowed':
        error = {
          code: 'not_allowed',
          message: '未授权使用麦克风'
        }
        break
      case 'network':
        error = {
          code: 'network',
          message: '网络连接失败，语音识别需要网络连接'
        }
        break
      case 'aborted':
        // 用户主动取消，不触发错误
        return
      default:
        error = {
          code: event.error || 'unknown',
          message: event.message || '语音识别发生未知错误'
        }
    }

    this.setStatus(VoiceRecognitionStatus.Error)
    this.triggerError(error)
  }

  /**
   * 触发错误回调
   */
  private triggerError(error: VoiceRecognitionError) {
    this.callbacks.onError?.(error)
  }

  /**
   * 设置状态
   */
  private setStatus(status: VoiceRecognitionStatus) {
    this.status = status
    this.callbacks.onStatusChange?.(status)
  }

  /**
   * 注册回调
   */
  public on(callbacks: VoiceRecognitionCallbacks) {
    this.callbacks = { ...this.callbacks, ...callbacks }
    return this
  }

  /**
   * 开始识别
   */
  public start() {
    log.info('🎙 [VoiceRecognition] start() 方法被调用')

    if (!this.recognition) {
      log.error('❌ [VoiceRecognition] recognition 实例不存在!')
      this.triggerError({
        code: 'not_initialized',
        message: '语音识别未初始化'
      })
      return
    }

    log.info('🎙 [VoiceRecognition] 当前状态:', this.status)
    log.info('🎙 [VoiceRecognition] recognition 对象:', this.recognition)

    try {
      log.info('🎙 [VoiceRecognition] 设置状态为 Initializing...')
      this.setStatus(VoiceRecognitionStatus.Initializing)
      log.info('🎙 [VoiceRecognition] 调用 recognition.start()...')
      this.recognition.start()
      log.info('✅ [VoiceRecognition] recognition.start() 调用成功')
    } catch (error) {
      log.error('❌ [VoiceRecognition] recognition.start() 抛出异常:', error)
      this.setStatus(VoiceRecognitionStatus.Error)
      this.triggerError({
        code: 'start_failed',
        message: '启动语音识别失败'
      })
    }
  }

  /**
   * 停止识别
   */
  public stop() {
    if (!this.recognition) return

    try {
      this.recognition.stop()
    } catch (error) {
      // 忽略停止时的错误
    }
  }

  /**
   * 取消识别
   */
  public abort() {
    if (!this.recognition) return

    try {
      this.recognition.abort()
    } catch (error) {
      // 忽略取消时的错误
    }
  }

  /**
   * 获取当前状态
   */
  public getStatus(): VoiceRecognitionStatus {
    return this.status
  }

  /**
   * 是否正在监听
   */
  public isListening(): boolean {
    return this.status === VoiceRecognitionStatus.Listening
  }

  /**
   * 更新配置
   */
  public updateConfig(config: Partial<VoiceRecognitionConfig>) {
    this.config = { ...this.config, ...config }

    if (this.recognition) {
      if (config.language) {
        this.recognition.lang = config.language
      }
      if (config.continuous !== undefined) {
        this.recognition.continuous = config.continuous
      }
      if (config.interimResults !== undefined) {
        this.recognition.interimResults = config.interimResults
      }
    }
  }

  /**
   * 销毁识别器
   */
  public destroy() {
    this.abort()
    this.recognition = null
    this.callbacks = {}
  }
}

/**
 * 创建语音识别器实例
 */
export function createVoiceRecognition(
  config?: VoiceRecognitionConfig
): VoiceRecognition {
  return new VoiceRecognition(config)
}

/**
 * Web Speech API 类型定义
 */
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList
  resultIndex: number
}

interface SpeechRecognitionResultList {
  length: number
  item(index: number): SpeechRecognitionResult
  [index: number]: SpeechRecognitionResult
}

interface SpeechRecognitionResult {
  length: number
  isFinal: boolean
  item(index: number): SpeechRecognitionAlternative
  [index: number]: SpeechRecognitionAlternative
}

interface SpeechRecognitionAlternative {
  transcript: string
  confidence: number
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string
  message: string
}

/**
 * 检查浏览器是否支持语音识别
 */
export function isVoiceRecognitionSupported(): boolean {
  return !!(
    window.SpeechRecognition || window.webkitSpeechRecognition
  )
}
