/**
 * 语音合成工具模块
 * 使用 Web Speech API 实现 TTS (Text-to-Speech)
 */

/**
 * TTS 事件类型
 */
export enum TTSEvent {
  Start = 'start',
  End = 'end',
  Pause = 'pause',
  Resume = 'resume',
  Error = 'error',
  Boundary = 'boundary'
}

/**
 * TTS 状态
 */
export enum TTSStatus {
  Idle = 'idle',
  Initializing = 'initializing',
  Speaking = 'speaking',
  Paused = 'paused',
  Error = 'error'
}

/**
 * TTS 结果
 */
export interface TTSResult {
  success: boolean
  duration?: number
  error?: string
}

/**
 * TTS 配置
 */
export interface TTSConfig {
  language?: string
  rate?: number          // 0.1 - 10
  pitch?: number         // 0 - 2
  volume?: number        // 0 - 1
  voice?: SpeechSynthesisVoice | null
}

/**
 * TTS 回调
 */
export interface TTSCallbacks {
  onStart?: () => void
  onEnd?: () => void
  onPause?: () => void
  onResume?: () => void
  onError?: (error: Error) => void
  onBoundary?: (event: SpeechSynthesisEvent) => void
  onStatusChange?: (status: TTSStatus) => void
}

/**
 * 语音合成器类
 */
export class TextToSpeech {
  private synthesis: SpeechSynthesis | null = null
  private utterance: SpeechSynthesisUtterance | null = null
  private status: TTSStatus = TTSStatus.Idle
  private callbacks: TTSCallbacks = {}
  private config: TTSConfig = {}

  constructor(config: TTSConfig = {}) {
    this.config = {
      language: 'en-US',
      rate: 1.0,
      pitch: 1.0,
      volume: 1.0,
      voice: null,
      ...config
    }

    this.initSynthesis()
  }

  /**
   * 初始化语音合成
   */
  private initSynthesis() {
    if (!('speechSynthesis' in window)) {
      this.setStatus(TTSStatus.Error)
      this.triggerError(new Error('您的浏览器不支持语音合成功能'))
      return
    }

    try {
      this.synthesis = window.speechSynthesis
    } catch (error) {
      this.setStatus(TTSStatus.Error)
      this.triggerError(new Error('语音合成初始化失败'))
    }
  }

  /**
   * 配置语音合成utterance
   */
  private setupUtterance(text: string): SpeechSynthesisUtterance {
    const utterance = new SpeechSynthesisUtterance(text)

    utterance.lang = this.config.language || 'en-US'
    utterance.rate = this.config.rate || 1.0
    utterance.pitch = this.config.pitch || 1.0
    utterance.volume = this.config.volume || 1.0

    if (this.config.voice) {
      utterance.voice = this.config.voice
    }

    // 事件处理
    utterance.onstart = () => {
      this.setStatus(TTSStatus.Speaking)
      this.callbacks.onStart?.()
    }

    utterance.onend = () => {
      this.setStatus(TTSStatus.Idle)
      this.utterance = null
      this.callbacks.onEnd?.()
    }

    utterance.onerror = (event: SpeechSynthesisErrorEvent) => {
      this.setStatus(TTSStatus.Error)
      this.utterance = null
      this.triggerError(new Error(event.error || '语音合成发生错误'))
    }

    utterance.onpause = () => {
      this.setStatus(TTSStatus.Paused)
      this.callbacks.onPause?.()
    }

    utterance.onresume = () => {
      this.setStatus(TTSStatus.Speaking)
      this.callbacks.onResume?.()
    }

    utterance.onboundary = (event: SpeechSynthesisEvent) => {
      this.callbacks.onBoundary?.(event)
    }

    return utterance
  }

  /**
   * 触发错误回调
   */
  private triggerError(error: Error) {
    this.callbacks.onError?.(error)
  }

  /**
   * 设置状态
   */
  private setStatus(status: TTSStatus) {
    this.status = status
    this.callbacks.onStatusChange?.(status)
  }

  /**
   * 注册回调
   */
  public on(callbacks: TTSCallbacks): TextToSpeech {
    this.callbacks = { ...this.callbacks, ...callbacks }
    return this
  }

  /**
   * 开始语音合成
   */
  public speak(text: string): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.synthesis) {
        reject(new Error('语音合成未初始化'))
        return
      }

      // 取消当前播放
      if (this.utterance) {
        this.stop()
      }

      this.utterance = this.setupUtterance(text)

      // 添加一次性回调
      this.utterance.onend = (_event: any) => {
        resolve()
      }

      this.utterance.onerror = (event: any) => {
        reject(new Error(event.error || '语音合成失败'))
      }

      try {
        this.synthesis.speak(this.utterance)
      } catch (error) {
        this.setStatus(TTSStatus.Error)
        reject(error)
      }
    })
  }

  /**
   * 停止语音合成
   */
  public stop(): void {
    if (!this.synthesis) return

    this.synthesis.cancel()
    this.utterance = null
    this.setStatus(TTSStatus.Idle)
  }

  /**
   * 暂停语音合成
   */
  public pause(): void {
    if (!this.synthesis || this.status !== TTSStatus.Speaking) return

    this.synthesis.pause()
    // 手动设置状态，因为浏览器的onpause事件可能不会立即触发
    this.setStatus(TTSStatus.Paused)
  }

  /**
   * 恢复语音合成
   */
  public resume(): void {
    if (!this.synthesis || this.status !== TTSStatus.Paused) return

    this.synthesis.resume()
    // 手动设置状态，因为浏览器的onresume事件可能不会立即触发
    this.setStatus(TTSStatus.Speaking)
  }

  /**
   * 设置语速
   */
  public setRate(rate: number): void {
    this.config.rate = Math.max(0.1, Math.min(10, rate))
  }

  /**
   * 设置音调
   */
  public setPitch(pitch: number): void {
    this.config.pitch = Math.max(0, Math.min(2, pitch))
  }

  /**
   * 设置音量
   */
  public setVolume(volume: number): void {
    this.config.volume = Math.max(0, Math.min(1, volume))
  }

  /**
   * 设置语言
   */
  public setLanguage(language: string): void {
    this.config.language = language
  }

  /**
   * 设置语音
   */
  public setVoice(voice: SpeechSynthesisVoice | null): void {
    this.config.voice = voice
  }

  /**
   * 获取当前状态
   */
  public getStatus(): TTSStatus {
    return this.status
  }

  /**
   * 是否正在播放
   */
  public isSpeaking(): boolean {
    return this.status === TTSStatus.Speaking
  }

  /**
   * 是否已暂停
   */
  public isPaused(): boolean {
    return this.status === TTSStatus.Paused
  }

  /**
   * 获取可用语音列表
   */
  public getVoices(): SpeechSynthesisVoice[] {
    if (!this.synthesis) return []

    return this.synthesis.getVoices()
  }

  /**
   * 获取指定语言的语音
   */
  public getVoicesForLanguage(language: string): SpeechSynthesisVoice[] {
    return this.getVoices().filter(voice =>
      voice.lang.startsWith(language)
    )
  }

  /**
   * 销毁合成器
   */
  public destroy(): void {
    this.stop()
    this.synthesis = null
    this.callbacks = {}
  }
}

/**
 * 创建语音合成器实例
 */
export function createTextToSpeech(config?: TTSConfig): TextToSpeech {
  return new TextToSpeech(config)
}

/**
 * 检查浏览器是否支持语音合成
 */
export function isTextToSpeechSupported(): boolean {
  return 'speechSynthesis' in window
}

/**
 * 获取最佳英语语音
 */
export function getBestEnglishVoice(): SpeechSynthesisVoice | null {
  if (!isTextToSpeechSupported()) return null

  const tts = createTextToSpeech()
  const voices = tts.getVoicesForLanguage('en')

  // 优先选择Google英语语音
  const googleVoice = voices.find(v => v.name.includes('Google') && v.lang.includes('en'))
  if (googleVoice) return googleVoice

  // 其次选择Microsoft英语语音
  const microsoftVoice = voices.find(v => v.name.includes('Microsoft') && v.lang.includes('en'))
  if (microsoftVoice) return microsoftVoice

  // 最后返回第一个英语语音
  return voices[0] || null
}
