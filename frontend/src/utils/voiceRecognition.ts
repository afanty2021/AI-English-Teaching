/**
 * 语音识别工具模块
 * 支持 Web Speech API 和后端 STT 服务
 */

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
  private recognition: any = null
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
    // 检查浏览器支持
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition

    if (!SpeechRecognition) {
      this.setStatus(VoiceRecognitionStatus.Error)
      this.triggerError({
        code: 'not_supported',
        message: '您的浏览器不支持语音识别功能，请使用 Chrome 或 Edge 浏览器'
      })
      return
    }

    try {
      this.recognition = new SpeechRecognition()
      this.setupRecognition()
    } catch (error) {
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
    const recognition = this.recognition

    recognition.lang = this.config.language || 'en-US'
    recognition.continuous = this.config.continuous || false
    recognition.interimResults = this.config.interimResults || true
    recognition.maxAlternatives = this.config.maxAlternatives || 1

    // 开始识别
    recognition.onstart = () => {
      this.setStatus(VoiceRecognitionStatus.Listening)
      this.callbacks.onStart?.()
    }

    // 识别结束
    recognition.onend = () => {
      if (this.status === VoiceRecognitionStatus.Listening) {
        // 如果状态还是 listening，说明是正常结束
        this.setStatus(VoiceRecognitionStatus.Idle)
        this.callbacks.onStop?.()
      }
    }

    // 获取结果
    recognition.onresult = (event: any) => {
      const last = event.results.length - 1
      const result = event.results[last]

      const recognitionResult: VoiceRecognitionResult = {
        transcript: result[0].transcript,
        isFinal: result.isFinal,
        confidence: result[0].confidence
      }

      if (result.isFinal) {
        this.callbacks.onResult?.(recognitionResult)
      } else {
        this.callbacks.onInterimResult?.(recognitionResult)
      }
    }

    // 错误处理
    recognition.onerror = (event: any) => {
      this.handleRecognitionError(event)
    }
  }

  /**
   * 处理识别错误
   */
  private handleRecognitionError(event: any) {
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
    if (!this.recognition) {
      this.triggerError({
        code: 'not_initialized',
        message: '语音识别未初始化'
      })
      return
    }

    try {
      this.setStatus(VoiceRecognitionStatus.Initializing)
      this.recognition.start()
    } catch (error) {
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
 * 检查浏览器是否支持语音识别
 */
export function isVoiceRecognitionSupported(): boolean {
  return !!(
    (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  )
}
