/**
 * 音频增强工具类
 * 支持语音活动检测(VAD)、噪音抑制、音量检测、音频预处理等功能
 */

// 导入音频预处理器相关类型和类
import {
  AudioPreprocessor,
  createAudioPreprocessor,
  PreprocessorPresets,
  type AudioPreprocessorConfig
} from './audioPreprocessor'

export interface VoiceActivityResult {
  hasVoice: boolean
  confidence: number
  volume: number
}

export interface NoiseReductionConfig {
  threshold: number
  knee: number
  ratio: number
  attack: number
  release: number
}

export interface AudioEnhancementOptions {
  enableVAD: boolean
  enableNoiseReduction: boolean
  enableVolumeDetection: boolean
  vadThreshold?: number
  noiseReductionConfig?: NoiseReductionConfig
}

/**
 * 语音活动检测器
 *
 * 优化说明：
 * - 使用平滑检测队列减少误判
 * - 检测间隔 30ms，队列大小 2，总延迟约 60ms
 * - 支持多数表决逻辑，只要有 1 个样本为正就判定为有语音
 * - 正确处理资源清理
 */
export class VoiceActivityDetector {
  private analyser: AnalyserNode
  private audioContext: AudioContext
  private dataArray: Uint8Array<ArrayBuffer>
  private bufferLength: number
  private cleanup: (() => void) | null = null

  // VAD 优化配置
  private readonly DETECTION_QUEUE_SIZE = 2  // 检测队列大小
  private readonly CHECK_INTERVAL = 30       // 检测间隔 30ms

  constructor(audioContext?: AudioContext) {
    this.audioContext = audioContext || new AudioContext()
    this.analyser = this.audioContext.createAnalyser()
    this.bufferLength = this.analyser.frequencyBinCount
    this.dataArray = new Uint8Array(this.bufferLength) as Uint8Array<ArrayBuffer>

    // 配置分析器参数
    this.analyser.fftSize = 512
    this.analyser.smoothingTimeConstant = 0.8
  }

  /**
   * 检测语音活动（优化版：使用平滑检测队列）
   * @param stream 音频流
   * @param threshold VAD阈值 (0-1)
   * @returns 语音活动检测结果
   */
  detectVoiceActivity(stream: MediaStream, threshold: number = 0.3): Promise<VoiceActivityResult> {
    return new Promise((resolve) => {
      const source = this.audioContext.createMediaStreamSource(stream)
      source.connect(this.analyser)

      const results: boolean[] = []
      const confidenceResults: number[] = []
      const volumeResults: number[] = []
      let samples = 0

      const intervalId = setInterval(() => {
        this.analyser.getByteFrequencyData(this.dataArray)
        const result = this.analyzeWithSmoothing(this.dataArray, threshold)
        results.push(result.hasVoice)
        confidenceResults.push(result.confidence)
        volumeResults.push(result.volume)
        samples++

        if (samples >= this.DETECTION_QUEUE_SIZE) {
          clearInterval(intervalId)

          // 多数表决：只要有 1 个样本为正就判定为有语音
          const hasVoice = results.some(r => r)

          resolve({
            hasVoice,
            confidence: result.confidence,
            volume: result.volume
          })
        }
      }, this.CHECK_INTERVAL)

      // 设置清理函数
      this.cleanup = () => {
        clearInterval(intervalId)
        try {
          source.disconnect()
        } catch (e) {
          // 忽略断开连接错误
        }
      }
    })
  }

  /**
   * 使用平滑算法分析语音活动
   * @param dataArray 频域数据
   * @param threshold VAD阈值
   * @returns 语音活动分析结果
   */
  private analyzeWithSmoothing(dataArray: Uint8Array<ArrayBuffer>, threshold: number): VoiceActivityResult {
    const average = dataArray.reduce((sum, v) => sum + v, 0) / dataArray.length
    const lowFreq = this.getLowFrequencyEnergyFromData(dataArray)
    const highFreq = this.getHighFrequencyEnergyFromData(dataArray)

    // 使用现有的判断条件
    const hasVoice = average > (threshold * 255) && lowFreq > highFreq * 0.3

    const normalizedVolume = average / 255
    const confidence = Math.min(normalizedVolume / threshold, 1.0)

    return { hasVoice, confidence, volume: normalizedVolume }
  }

  /**
   * 获取低频能量 (语音主要在低频) - 从指定数据计算
   */
  private getLowFrequencyEnergyFromData(dataArray: Uint8Array<ArrayBuffer>): number {
    const lowFreqCount = Math.floor(dataArray.length * 0.3) // 30%低频
    let energy = 0
    for (let i = 0; i < lowFreqCount; i++) {
      energy += (dataArray[i] || 0) * (dataArray[i] || 0)
    }
    return energy / lowFreqCount
  }

  /**
   * 获取高频能量 (噪音主要在高頻) - 从指定数据计算
   */
  private getHighFrequencyEnergyFromData(dataArray: Uint8Array<ArrayBuffer>): number {
    const highFreqStart = Math.floor(dataArray.length * 0.7) // 70%高频
    let energy = 0
    let count = 0
    for (let i = highFreqStart; i < dataArray.length; i++) {
      energy += (dataArray[i] || 0) * (dataArray[i] || 0)
      count++
    }
    return energy / count
  }

  /**
   * 实时监听语音活动
   * @param stream 音频流
   * @param callback 回调函数
   * @param interval 检测间隔(ms)
   */
  monitorVoiceActivity(
    stream: MediaStream,
    callback: (result: VoiceActivityResult) => void,
    interval: number = 100
  ): () => void {
    const source = this.audioContext.createMediaStreamSource(stream)
    source.connect(this.analyser)

    const intervalId = setInterval(() => {
      this.detectVoiceActivity(stream).then(callback)
    }, interval)

    // 返回停止监听的函数
    return () => {
      clearInterval(intervalId)
      try {
        source.disconnect()
      } catch (e) {
        // 忽略断开连接错误
      }
    }
  }

  /**
   * 销毁检测器
   */
  destroy(): void {
    // 执行清理函数
    this.cleanup?.()
    this.cleanup = null

    // 关闭音频上下文
    try {
      this.analyser.disconnect()
      if (this.audioContext && this.audioContext.state !== 'closed') {
        this.audioContext.close()
      }
    } catch (e) {
      // 忽略关闭错误
    }
  }
}

/**
 * 噪音抑制处理器
 */
export class NoiseSuppressor {
  private audioContext: AudioContext
  private compressor: DynamicsCompressorNode
  private filter: BiquadFilterNode

  constructor(audioContext?: AudioContext) {
    this.audioContext = audioContext || new AudioContext()

    // 创建动态压缩器
    this.compressor = this.audioContext.createDynamicsCompressor()
    this.compressor.threshold.setValueAtTime(-50, this.audioContext.currentTime)
    this.compressor.knee.setValueAtTime(40, this.audioContext.currentTime)
    this.compressor.ratio.setValueAtTime(12, this.audioContext.currentTime)
    this.compressor.attack.setValueAtTime(0.003, this.audioContext.currentTime)
    this.compressor.release.setValueAtTime(0.25, this.audioContext.currentTime)

    // 创建高通滤波器，去除低频噪音
    this.filter = this.audioContext.createBiquadFilter()
    this.filter.type = 'highpass'
    this.filter.frequency.setValueAtTime(80, this.audioContext.currentTime) // 去除80Hz以下噪音
    this.filter.Q.setValueAtTime(1, this.audioContext.currentTime)
  }

  /**
   * 应用噪音抑制
   * @param stream 输入音频流
   * @param config 配置参数
   * @returns 处理后的音频流
   */
  suppress(stream: MediaStream, config?: NoiseReductionConfig): MediaStream {
    // 创建音频源
    const source = this.audioContext.createMediaStreamSource(stream)

    // 如果提供了自定义配置，更新压缩器参数
    if (config) {
      this.updateConfig(config)
    }

    // 连接处理节点
    source.connect(this.filter)
    this.filter.connect(this.compressor)

    // 返回处理后的音频流
    const destination = this.audioContext.createMediaStreamDestination()
    this.compressor.connect(destination)

    return destination.stream
  }

  /**
   * 更新配置参数
   */
  private updateConfig(config: NoiseReductionConfig): void {
    this.compressor.threshold.setValueAtTime(config.threshold, this.audioContext.currentTime)
    this.compressor.knee.setValueAtTime(config.knee, this.audioContext.currentTime)
    this.compressor.ratio.setValueAtTime(config.ratio, this.audioContext.currentTime)
    this.compressor.attack.setValueAtTime(config.attack, this.audioContext.currentTime)
    this.compressor.release.setValueAtTime(config.release, this.audioContext.currentTime)
  }

  /**
   * 创建增强音频处理器
   * @param stream 输入音频流
   * @param callback 回调函数
   * @returns 处理器对象
   */
  static createProcessor(
    stream: MediaStream,
    callback: (buffer: Float32Array) => void
  ): ScriptProcessorNode {
    const audioContext = new AudioContext()
    const source = audioContext.createMediaStreamSource(stream)
    const processor = audioContext.createScriptProcessor(4096, 1, 1)

    processor.onaudioprocess = (event) => {
      const inputBuffer = event.inputBuffer.getChannelData(0)
      callback(new Float32Array(inputBuffer))
    }

    source.connect(processor)
    processor.connect(audioContext.destination)

    return processor
  }

  /**
   * 销毁处理器
   */
  destroy(): void {
    try {
      this.compressor.disconnect()
      this.filter.disconnect()
      this.audioContext.close()
    } catch (e) {
      // 忽略关闭错误
    }
  }
}

/**
 * 音量检测器
 */
export class VolumeDetector {
  private analyser: AnalyserNode
  private audioContext: AudioContext
  private dataArray: Uint8Array

  constructor(audioContext?: AudioContext) {
    this.audioContext = audioContext || new AudioContext()
    this.analyser = this.audioContext.createAnalyser()
    this.dataArray = new Uint8Array(this.analyser.frequencyBinCount)

    this.analyser.fftSize = 256
    this.analyser.smoothingTimeConstant = 0.8
  }

  /**
   * 获取当前音量
   * @param stream 音频流
   * @returns 音量值 (0-1)
   */
  getVolume(stream: MediaStream): number {
    const source = this.audioContext.createMediaStreamSource(stream)
    source.connect(this.analyser)

    this.analyser.getByteFrequencyData(this.dataArray as Uint8Array<ArrayBuffer>)

    const average = this.dataArray.reduce((sum, value) => sum + value, 0) / this.dataArray.length
    return average / 255
  }

  /**
   * 实时监听音量变化
   * @param stream 音频流
   * @param callback 回调函数
   * @param interval 检测间隔(ms)
   */
  monitorVolume(
    stream: MediaStream,
    callback: (volume: number) => void,
    interval: number = 50
  ): () => void {
    const source = this.audioContext.createMediaStreamSource(stream)
    source.connect(this.analyser)

    const intervalId = setInterval(() => {
      const volume = this.getVolume(stream)
      callback(volume)
    }, interval)

    return () => {
      clearInterval(intervalId)
      try {
        source.disconnect()
      } catch (e) {
        // 忽略断开连接错误
      }
    }
  }

  /**
   * 销毁检测器
   */
  destroy(): void {
    try {
      this.analyser.disconnect()
      this.audioContext.close()
    } catch (e) {
      // 忽略关闭错误
    }
  }
}

/**
 * 音频增强配置接口（扩展版）
 */
export interface AudioEnhancementOptionsExtended {
  /** 是否启用语音活动检测 */
  enableVAD?: boolean
  /** 是否启用噪音抑制 */
  enableNoiseReduction?: boolean
  /** 是否启用音量检测 */
  enableVolumeDetection?: boolean
  /** VAD阈值 */
  vadThreshold?: number
  /** 噪音抑制配置 */
  noiseReductionConfig?: NoiseReductionConfig
  /** 是否启用音频预处理 */
  enablePreprocessing?: boolean
  /** 音频预处理配置 */
  preprocessorConfig?: Partial<AudioPreprocessorConfig>
}

/**
 * 音频增强主类
 */
export class AudioEnhancer {
  private voiceDetector: VoiceActivityDetector
  private noiseSuppressor: NoiseSuppressor
  private volumeDetector: VolumeDetector
  private preprocessor: AudioPreprocessor | null = null
  private options: AudioEnhancementOptionsExtended

  constructor(options: AudioEnhancementOptionsExtended = {}) {
    // Merge provided options with defaults
    const defaults: AudioEnhancementOptionsExtended = {
      enableVAD: true,
      enableNoiseReduction: true,
      enableVolumeDetection: true,
      enablePreprocessing: true,
      vadThreshold: 0.3,
      noiseReductionConfig: {
        threshold: -50,
        knee: 40,
        ratio: 12,
        attack: 0.003,
        release: 0.25
      },
      preprocessorConfig: {}
    }
    this.options = { ...defaults, ...options }

    this.voiceDetector = new VoiceActivityDetector()
    this.noiseSuppressor = new NoiseSuppressor()
    this.volumeDetector = new VolumeDetector()

    // 初始化预处理器
    if (this.options.enablePreprocessing) {
      this.preprocessor = createAudioPreprocessor(this.options.preprocessorConfig)
    }
  }

  /**
   * 增强音频流
   * @param stream 输入音频流
   * @returns 增强后的音频流
   */
  async enhance(stream: MediaStream): Promise<MediaStream> {
    let enhancedStream = stream

    // 1. 应用音频预处理（如果启用）
    if (this.options.enablePreprocessing && this.preprocessor) {
      const preprocessResult = await this.preprocessor.process(stream)
      if (preprocessResult.success) {
        enhancedStream = preprocessResult.stream
      } else {
        console.warn('音频预处理失败，使用原始流:', preprocessResult.error)
      }
    }

    // 2. 应用噪音抑制
    if (this.options.enableNoiseReduction) {
      enhancedStream = this.noiseSuppressor.suppress(enhancedStream, this.options.noiseReductionConfig)
    }

    return enhancedStream
  }

  /**
   * 检测语音活动
   * @param stream 音频流
   * @returns 语音活动检测结果
   */
  async detectVoiceActivity(stream: MediaStream): Promise<VoiceActivityResult> {
    if (!this.options.enableVAD) {
      throw new Error('VAD功能已禁用')
    }

    return this.voiceDetector.detectVoiceActivity(stream, this.options.vadThreshold)
  }

  /**
   * 实时监听语音活动
   * @param stream 音频流
   * @param callback 回调函数
   * @returns 停止监听函数
   */
  monitorVoiceActivity(
    stream: MediaStream,
    callback: (result: VoiceActivityResult) => void
  ): () => void {
    if (!this.options.enableVAD) {
      throw new Error('VAD功能已禁用')
    }

    return this.voiceDetector.monitorVoiceActivity(stream, callback)
  }

  /**
   * 获取音量
   * @param stream 音频流
   * @returns 音量值
   */
  getVolume(stream: MediaStream): number {
    if (!this.options.enableVolumeDetection) {
      throw new Error('音量检测功能已禁用')
    }

    return this.volumeDetector.getVolume(stream)
  }

  /**
   * 实时监听音量
   * @param stream 音频流
   * @param callback 回调函数
   * @returns 停止监听函数
   */
  monitorVolume(
    stream: MediaStream,
    callback: (volume: number) => void
  ): () => void {
    if (!this.options.enableVolumeDetection) {
      throw new Error('音量检测功能已禁用')
    }

    return this.volumeDetector.monitorVolume(stream, callback)
  }

  /**
   * 更新配置
   * @param newOptions 新配置
   */
  updateOptions(newOptions: Partial<AudioEnhancementOptionsExtended>): void {
    this.options = { ...this.options, ...newOptions }
  }

  /**
   * 获取当前配置
   */
  getOptions(): AudioEnhancementOptionsExtended {
    return { ...this.options }
  }

  /**
   * 销毁增强器
   */
  destroy(): void {
    this.voiceDetector.destroy()
    this.noiseSuppressor.destroy()
    this.volumeDetector.destroy()

    // 清理预处理器
    if (this.preprocessor) {
      this.preprocessor.destroy()
      this.preprocessor = null
    }
  }

  /**
   * 获取预处理器实例
   */
  getPreprocessor(): AudioPreprocessor | null {
    return this.preprocessor
  }

  /**
   * 更新预处理配置
   */
  updatePreprocessorConfig(config: Partial<AudioPreprocessorConfig>): void {
    if (this.preprocessor) {
      this.preprocessor.updateConfig(config)
    } else {
      console.warn('预处理器未初始化')
    }
  }
}

/**
 * 便利函数
 */
export const audioEnhancer = {
  create: (options?: AudioEnhancementOptionsExtended) =>
    new AudioEnhancer(options ?? {
      enableVAD: true,
      enableNoiseReduction: true,
      enableVolumeDetection: true,
      enablePreprocessing: true
    }),
  VoiceActivityDetector,
  NoiseSuppressor,
  VolumeDetector,
  AudioPreprocessor,
  createAudioPreprocessor,
  PreprocessorPresets
}

export default AudioEnhancer