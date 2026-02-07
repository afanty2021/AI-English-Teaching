/**
 * 音频预处理工具类
 *
 * 提供音频预处理功能：
 * - 高通滤波：去除低频噪音（如风声、背景嗡嗡声）
 * - 噪音门：静音低音量部分
 * - 归一化：调整音频到目标音量（暂时禁用，需要更复杂实现）
 *
 * 注意：由于 Web Audio API 的限制，某些功能需要简化实现
 */

/**
 * 音频预处理配置接口
 */
export interface AudioPreprocessorConfig {
  /** 是否启用高通滤波 */
  enableHighPassFilter: boolean
  /** 高通滤波截止频率 (Hz) - 默认 80Hz 去除低频噪音 */
  highPassCutoff: number
  /** 是否启用归一化（暂时禁用，需要更复杂实现） */
  enableNormalization: boolean
  /** 是否启用噪音门 */
  enableNoiseGate: boolean
  /** 噪音门阈值 (0-1) - 低于此阈值的音频将被静音 */
  noiseGateThreshold: number
  /** 目标音量等级 (0-1) - 用于归一化 */
  targetLevel: number
}

/**
 * 预处理结果接口
 */
export interface PreprocessResult {
  /** 处理后的音频流 */
  stream: MediaStream
  /** 使用的配置 */
  config: AudioPreprocessorConfig
  /** 处理是否成功 */
  success: boolean
  /** 错误信息（如果处理失败） */
  error?: string
}

/**
 * 音频预处理器类
 */
export class AudioPreprocessor {
  private audioContext: AudioContext | null = null
  private config: AudioPreprocessorConfig
  private activeNodes: AudioNode[] = []

  constructor(config: AudioPreprocessorConfig) {
    this.config = config
  }

  /**
   * 处理音频流
   * @param stream 输入音频流
   * @param audioContext 可选的 AudioContext 实例
   * @returns 处理后的音频流
   */
  async process(stream: MediaStream, audioContext?: AudioContext): Promise<PreprocessResult> {
    try {
      // 创建或使用提供的 AudioContext
      this.audioContext = audioContext || new AudioContext()

      // 确保 AudioContext 处于运行状态
      if (this.audioContext.state === 'suspended') {
        await this.audioContext.resume()
      }

      // 创建音频源
      const source = this.audioContext.createMediaStreamSource(stream)
      this.activeNodes.push(source)

      // 创建目标节点
      const destination = this.audioContext.createMediaStreamDestination()

      // 构建处理链
      let currentNode: AudioNode = source

      // 1. 高通滤波
      if (this.config.enableHighPassFilter) {
        const highPass = this.audioContext.createBiquadFilter()
        highPass.type = 'highpass'
        highPass.frequency.value = this.config.highPassCutoff
        highPass.Q.value = 1

        currentNode.connect(highPass)
        currentNode = highPass
        this.activeNodes.push(highPass)
      }

      // 2. 噪音门
      if (this.config.enableNoiseGate) {
        const noiseGate = this.createNoiseGate()
        currentNode.connect(noiseGate)
        currentNode = noiseGate
        this.activeNodes.push(noiseGate)
      }

      // 3. 归一化（暂时禁用，需要更复杂实现）
      // Web Audio API 没有内置的归一化节点
      // 需要使用 ScriptProcessor 或 AudioWorklet 实现
      // 这里预留接口，但暂时不实现
      if (this.config.enableNormalization) {
        // TODO: 实现归一化功能
        // 可能的实现方式：
        // 1. 使用 ScriptProcessorNode 分析音频数据
        // 2. 计算峰值或 RMS 值
        // 3. 应用增益调整
        console.warn('归一化功能暂时禁用，需要更复杂的实现')
      }

      // 连接到目标
      currentNode.connect(destination)
      this.activeNodes.push(destination)

      return {
        stream: destination.stream,
        config: { ...this.config },
        success: true
      }
    } catch (error) {
      return {
        stream,
        config: { ...this.config },
        success: false,
        error: error instanceof Error ? error.message : String(error)
      }
    }
  }

  /**
   * 创建噪音门
   * 使用 DynamicsCompressorNode 作为噪音门
   *
   * 原理：
   * - threshold：低于此阈值的信号被压缩
   * - ratio：高比率实现门效果
   * - attack：快速响应
   * - release：释放时间
   */
  private createNoiseGate(): DynamicsCompressorNode {
    if (!this.audioContext) {
      throw new Error('AudioContext 未初始化')
    }

    const dynamics = this.audioContext.createDynamicsCompressor()

    // 阈值：将分贝值转换为线性值
    dynamics.threshold.value = this.config.noiseGateThreshold * -100

    // 膝点：0 使压缩器作为硬门
    dynamics.knee.value = 0

    // 比率：高比率实现门效果
    dynamics.ratio.value = 20

    // 启动时间：快速响应
    dynamics.attack.value = 0.001

    // 释放时间：快速释放
    dynamics.release.value = 0.1

    return dynamics
  }

  /**
   * 更新配置
   */
  updateConfig(config: Partial<AudioPreprocessorConfig>): void {
    this.config = { ...this.config, ...config }
  }

  /**
   * 获取当前配置
   */
  getConfig(): AudioPreprocessorConfig {
    return { ...this.config }
  }

  /**
   * 销毁预处理器
   * 断开所有音频节点的连接并清理资源
   */
  destroy(): void {
    // 断开所有活动节点的连接
    for (const node of this.activeNodes) {
      try {
        node.disconnect()
      } catch (e) {
        // 忽略断开连接错误
        console.debug('节点断开连接时出错:', e)
      }
    }

    this.activeNodes = []

    // 关闭 AudioContext
    if (this.audioContext && this.audioContext.state !== 'closed') {
      try {
        this.audioContext.close()
      } catch (e) {
        // 忽略关闭错误
        console.debug('关闭 AudioContext 时出错:', e)
      }
    }

    this.audioContext = null
  }

  /**
   * 获取处理器状态
   */
  getStatus(): {
    isActive: boolean
    nodeCount: number
    config: AudioPreprocessorConfig
  } {
    return {
      isActive: this.audioContext !== null && this.audioContext.state === 'running',
      nodeCount: this.activeNodes.length,
      config: { ...this.config }
    }
  }
}

/**
 * 创建音频预处理器实例的便利函数
 * @param config 可选的配置参数
 * @returns 音频预处理器实例
 */
export function createAudioPreprocessor(
  config: Partial<AudioPreprocessorConfig> = {}
): AudioPreprocessor {
  const defaultConfig: AudioPreprocessorConfig = {
    enableHighPassFilter: true,
    highPassCutoff: 80, // 80Hz - 去除低频噪音
    enableNormalization: false, // 暂时禁用（需要更复杂实现）
    enableNoiseGate: true,
    noiseGateThreshold: 0.02, // 0.02 约等于 -50dB
    targetLevel: 0.8 // 目标音量 80%
  }

  return new AudioPreprocessor({ ...defaultConfig, ...config })
}

/**
 * 预设配置
 */
export const PreprocessorPresets = {
  /**
   * 激进降噪预设
   * 适用于嘈杂环境
   */
  aggressive: {
    enableHighPassFilter: true,
    highPassCutoff: 100, // 更高的截止频率
    enableNormalization: false,
    enableNoiseGate: true,
    noiseGateThreshold: 0.05, // 更高的阈值
    targetLevel: 0.8
  } as AudioPreprocessorConfig,

  /**
   * 轻柔处理预设
   * 适用于相对安静的环境
   */
  gentle: {
    enableHighPassFilter: true,
    highPassCutoff: 60, // 较低的截止频率
    enableNormalization: false,
    enableNoiseGate: true,
    noiseGateThreshold: 0.01, // 较低的阈值
    targetLevel: 0.8
  } as AudioPreprocessorConfig,

  /**
   * 仅高通滤波预设
   * 只去除低频噪音，不应用噪音门
   */
  highPassOnly: {
    enableHighPassFilter: true,
    highPassCutoff: 80,
    enableNormalization: false,
    enableNoiseGate: false,
    noiseGateThreshold: 0.02,
    targetLevel: 0.8
  } as AudioPreprocessorConfig,

  /**
   * 无处理预设
   * 直接传递原始音频流
   */
  bypass: {
    enableHighPassFilter: false,
    highPassCutoff: 80,
    enableNormalization: false,
    enableNoiseGate: false,
    noiseGateThreshold: 0.02,
    targetLevel: 0.8
  } as AudioPreprocessorConfig
}

export default AudioPreprocessor
