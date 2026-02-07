/**
 * 音频缓冲器
 * 用于 CloudSTT 模式的音频数据缓冲策略
 * 解决音频碎片化问题，提高语音识别准确率
 */

/**
 * 音频块接口
 */
export interface AudioChunk {
  data: Blob          // 音频数据（Blob格式）
  timestamp: number   // 时间戳
  duration: number    // 估算时长（毫秒）
}

/**
 * 音频缓冲器配置
 */
export interface AudioBufferConfig {
  /** 缓冲区最大时长（毫秒），默认2000ms */
  bufferSize?: number
  /** 缓冲阈值（毫秒），默认1000ms */
  bufferThreshold?: number
  /** 最小音频长度（毫秒），默认500ms */
  minAudioLength?: number
  /** 采样率（Hz），默认16000 */
  sampleRate?: number
  /** 位深度，默认16bit */
  bitDepth?: number
  /** 单声道/立体声，默认单声道 */
  channels?: number
}

/**
 * 音频缓冲器状态
 */
export interface AudioBufferState {
  /** 缓冲区中的音频块数量 */
  chunkCount: number
  /** 缓冲区总大小（字节） */
  totalSize: number
  /** 缓冲区总时长（毫秒） */
  totalDuration: number
  /** 是否已达到阈值 */
  isThresholdReached: boolean
}

/**
 * 音频缓冲器类
 *
 * 主要功能：
 * 1. 缓冲短音频片段（<500ms）
 * 2. 累积音频直到达到阈值（1000ms）
 * 3. 合并所有缓冲的音频块为一个 Blob
 *
 * 使用场景：
 * - CloudSTT 模式（云端语音识别）
 * - 解决 MediaRecorder 产生的音频碎片化问题
 * - 提高语音识别准确率
 *
 * @example
 * const buffer = new AudioBuffer({
 *   bufferSize: 2000,
 *   bufferThreshold: 1000,
 *   minAudioLength: 500
 * })
 *
 * mediaRecorder.ondataavailable = (event) => {
 *   if (!buffer.add(event.data)) {
 *     // 音频已足够，可以发送识别
 *     const audioBlob = buffer.flush()
 *     transcribeAudio(audioBlob)
 *   }
 * }
 */
export class AudioBuffer {
  private buffer: AudioChunk[] = []
  private totalSize: number = 0
  private totalDuration: number = 0
  private config: Required<AudioBufferConfig>

  constructor(config: AudioBufferConfig = {}) {
    this.config = {
      bufferSize: 2000,
      bufferThreshold: 1000,
      minAudioLength: 500,
      sampleRate: 16000,
      bitDepth: 16,
      channels: 1,
      ...config
    }
  }

  /**
   * 添加音频块到缓冲区
   *
   * @param chunk - 音频数据 Blob
   * @returns 如果音频已被缓冲返回 true，如果音频已足够返回 false
   *
   * 逻辑：
   * 1. 如果音频太短（< minAudioLength），缓冲
   * 2. 如果累积音频未达阈值，缓冲
   * 3. 否则返回 false，表示音频已足够
   */
  add(chunk: Blob): boolean {
    // 估算音频时长
    const estimatedDuration = this.estimateDuration(chunk)

    // 检查是否超过最大缓冲区大小
    if (this.totalDuration + estimatedDuration > this.config.bufferSize) {
      // 缓冲区已满，拒绝添加
      return false
    }

    // 添加到缓冲区
    const audioChunk: AudioChunk = {
      data: chunk,
      timestamp: Date.now(),
      duration: estimatedDuration
    }

    this.buffer.push(audioChunk)
    this.totalSize += chunk.size
    this.totalDuration += estimatedDuration

    // 检查是否达到阈值
    if (this.totalDuration >= this.config.bufferThreshold) {
      // 达到阈值，应该发送识别
      return false
    }

    // 继续缓冲
    return true
  }

  /**
   * 清空缓冲区并返回合并后的音频 Blob
   *
   * @returns 合并后的音频 Blob，如果缓冲区为空返回 null
   */
  flush(): Blob | null {
    if (this.buffer.length === 0) {
      return null
    }

    // 合并所有 Blob
    const mergedBlob = new Blob(
      this.buffer.map(chunk => chunk.data),
      { type: 'audio/webm' }
    )

    // 清空缓冲区
    this.clear()

    return mergedBlob
  }

  /**
   * 清空缓冲区（不返回数据）
   */
  clear(): void {
    this.buffer = []
    this.totalSize = 0
    this.totalDuration = 0
  }

  /**
   * 获取缓冲区当前状态
   */
  getState(): AudioBufferState {
    return {
      chunkCount: this.buffer.length,
      totalSize: this.totalSize,
      totalDuration: this.totalDuration,
      isThresholdReached: this.totalDuration >= this.config.bufferThreshold
    }
  }

  /**
   * 估算音频时长（毫秒）
   *
   * 基于音频参数估算：
   * 时长 = (数据大小 / (采样率 * 位深度/8 * 声道数)) * 1000
   *
   * @param blob - 音频 Blob
   * @returns 估算的时长（毫秒）
   */
  private estimateDuration(blob: Blob): number {
    const bytesPerSecond = (this.config.sampleRate * this.config.bitDepth * this.config.channels) / 8
    const durationSeconds = blob.size / bytesPerSecond
    return durationSeconds * 1000 // 转换为毫秒
  }

  /**
   * 检查缓冲区是否为空
   */
  isEmpty(): boolean {
    return this.buffer.length === 0
  }

  /**
   * 检查缓冲区是否已达到阈值
   */
  isReady(): boolean {
    return this.totalDuration >= this.config.bufferThreshold
  }

  /**
   * 获取缓冲区中的音频块数量
   */
  getChunkCount(): number {
    return this.buffer.length
  }

  /**
   * 获取缓冲区总大小（字节）
   */
  getTotalSize(): number {
    return this.totalSize
  }

  /**
   * 获取缓冲区总时长（毫秒）
   */
  getTotalDuration(): number {
    return this.totalDuration
  }
}

/**
 * 便利函数：创建音频缓冲器
 */
export function createAudioBuffer(config?: AudioBufferConfig): AudioBuffer {
  return new AudioBuffer(config)
}

/**
 * 默认导出
 */
export default AudioBuffer
