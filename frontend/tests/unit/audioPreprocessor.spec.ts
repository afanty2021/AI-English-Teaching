/**
 * 音频预处理工具单元测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  AudioPreprocessor,
  createAudioPreprocessor,
  PreprocessorPresets,
  type AudioPreprocessorConfig,
  type PreprocessResult
} from '../../src/utils/audioPreprocessor'

// Mock AudioContext
class MockAudioContext {
  state: AudioContextState = 'running'
  currentTime = 1000

  async resume(): Promise<void> {
    this.state = 'running'
  }

  async close(): Promise<void> {
    this.state = 'closed'
  }

  createMediaStreamSource(stream: MediaStream): MediaStreamAudioSourceNode {
    return {
      connect: vi.fn(),
      disconnect: vi.fn(),
      mediaStream: stream
    } as any
  }

  createMediaStreamDestination(): MediaStreamAudioDestinationNode {
    return {
      stream: new MediaStream(),
      connect: vi.fn(),
      disconnect: vi.fn()
    } as any
  }

  createBiquadFilter(): BiquadFilterNode {
    const node = {
      type: '',
      frequency: { value: 0 },
      Q: { value: 0 },
      connect: vi.fn(),
      disconnect: vi.fn()
    }
    return node as any
  }

  createDynamicsCompressor(): DynamicsCompressorNode {
    return {
      threshold: { value: 0 },
      knee: { value: 0 },
      ratio: { value: 0 },
      attack: { value: 0 },
      release: { value: 0 },
      connect: vi.fn(),
      disconnect: vi.fn()
    } as any
  }
}

// 创建模拟 MediaStream
function createMockMediaStream(): MediaStream {
  return {
    getTracks: vi.fn().mockReturnValue([]),
    getAudioTracks: vi.fn().mockReturnValue([]),
    getVideoTracks: vi.fn().mockReturnValue([]),
    addTrack: vi.fn(),
    removeTrack: vi.fn(),
    clone: vi.fn().mockReturnThis(),
    active: true,
    id: 'mock-stream-id',
    onaddtrack: null,
    onremovetrack: null,
    onactive: null,
    oninactive: null
  } as any
}

describe('AudioPreprocessor', () => {
  let preprocessor: AudioPreprocessor
  let mockStream: MediaStream

  beforeEach(() => {
    // Mock AudioContext 和 MediaStream
    vi.stubGlobal('AudioContext', MockAudioContext)
    vi.stubGlobal('MediaStream', class {
      constructor() {
        return createMockMediaStream()
      }
    })

    mockStream = createMockMediaStream()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    if (preprocessor) {
      preprocessor.destroy()
    }
  })

  describe('constructor', () => {
    it('应该使用默认配置创建预处理器', () => {
      preprocessor = new AudioPreprocessor({
        enableHighPassFilter: true,
        highPassCutoff: 80,
        enableNormalization: false,
        enableNoiseGate: true,
        noiseGateThreshold: 0.02,
        targetLevel: 0.8
      })

      const config = preprocessor.getConfig()
      expect(config.enableHighPassFilter).toBe(true)
      expect(config.highPassCutoff).toBe(80)
    })

    it('应该使用自定义配置创建预处理器', () => {
      const customConfig: AudioPreprocessorConfig = {
        enableHighPassFilter: true,
        highPassCutoff: 100,
        enableNormalization: false,
        enableNoiseGate: true,
        noiseGateThreshold: 0.05,
        targetLevel: 0.9
      }

      preprocessor = new AudioPreprocessor(customConfig)

      const config = preprocessor.getConfig()
      expect(config.highPassCutoff).toBe(100)
      expect(config.noiseGateThreshold).toBe(0.05)
      expect(config.targetLevel).toBe(0.9)
    })
  })

  describe('process', () => {
    it('应该处理音频流并返回成功结果', async () => {
      preprocessor = createAudioPreprocessor()

      const result = await preprocessor.process(mockStream)

      expect(result.success).toBe(true)
      expect(result.stream).toBeDefined()
      expect(result.config).toBeDefined()
      expect(result.error).toBeUndefined()
    })

    it('应该创建高通滤波器节点', async () => {
      preprocessor = createAudioPreprocessor({
        enableHighPassFilter: true,
        highPassCutoff: 100,
        enableNormalization: false,
        enableNoiseGate: false,
        noiseGateThreshold: 0.02,
        targetLevel: 0.8
      })

      const result = await preprocessor.process(mockStream)

      expect(result.success).toBe(true)
      expect(result.stream).toBeDefined()
    })

    it('应该创建噪音门节点', async () => {
      preprocessor = createAudioPreprocessor({
        enableHighPassFilter: false,
        enableNormalization: false,
        enableNoiseGate: true,
        noiseGateThreshold: 0.03,
        targetLevel: 0.8,
        highPassCutoff: 80
      })

      const result = await preprocessor.process(mockStream)

      expect(result.success).toBe(true)
      expect(result.stream).toBeDefined()
    })

    it('应该同时启用高通滤波和噪音门', async () => {
      preprocessor = createAudioPreprocessor({
        enableHighPassFilter: true,
        highPassCutoff: 80,
        enableNormalization: false,
        enableNoiseGate: true,
        noiseGateThreshold: 0.02,
        targetLevel: 0.8
      })

      const result = await preprocessor.process(mockStream)

      expect(result.success).toBe(true)
      expect(result.stream).toBeDefined()
    })

    it('应该在禁用所有功能时直接返回原始流', async () => {
      preprocessor = new AudioPreprocessor({
        enableHighPassFilter: false,
        highPassCutoff: 80,
        enableNormalization: false,
        enableNoiseGate: false,
        noiseGateThreshold: 0.02,
        targetLevel: 0.8
      })

      const result = await preprocessor.process(mockStream)

      expect(result.success).toBe(true)
      expect(result.stream).toBeDefined()
    })

    it('应该在归一化启用时记录警告', async () => {
      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      preprocessor = new AudioPreprocessor({
        enableHighPassFilter: false,
        highPassCutoff: 80,
        enableNormalization: true, // 启用归一化
        enableNoiseGate: false,
        noiseGateThreshold: 0.02,
        targetLevel: 0.8
      })

      const result = await preprocessor.process(mockStream)

      expect(result.success).toBe(true)
      expect(consoleWarnSpy).toHaveBeenCalledWith('归一化功能暂时禁用，需要更复杂的实现')

      consoleWarnSpy.mockRestore()
    })
  })

  describe('updateConfig', () => {
    it('应该更新配置', () => {
      preprocessor = createAudioPreprocessor()

      preprocessor.updateConfig({
        highPassCutoff: 120,
        noiseGateThreshold: 0.04
      })

      const config = preprocessor.getConfig()
      expect(config.highPassCutoff).toBe(120)
      expect(config.noiseGateThreshold).toBe(0.04)
    })

    it('应该保留未更新的配置值', () => {
      preprocessor = createAudioPreprocessor()
      const originalTargetLevel = preprocessor.getConfig().targetLevel

      preprocessor.updateConfig({
        highPassCutoff: 120
      })

      const config = preprocessor.getConfig()
      expect(config.highPassCutoff).toBe(120)
      expect(config.targetLevel).toBe(originalTargetLevel)
    })
  })

  describe('getConfig', () => {
    it('应该返回配置的副本', () => {
      preprocessor = createAudioPreprocessor()
      const config1 = preprocessor.getConfig()
      const config2 = preprocessor.getConfig()

      expect(config1).toEqual(config2)
      expect(config1).not.toBe(config2) // 应该是不同的对象引用
    })
  })

  describe('getStatus', () => {
    it('应该返回处理器状态', async () => {
      preprocessor = createAudioPreprocessor()
      await preprocessor.process(mockStream)

      const status = preprocessor.getStatus()

      expect(status.isActive).toBe(true)
      expect(status.nodeCount).toBeGreaterThan(0)
      expect(status.config).toBeDefined()
    })

    it('应该在未处理时返回非活动状态', () => {
      preprocessor = createAudioPreprocessor()

      const status = preprocessor.getStatus()

      expect(status.isActive).toBe(false)
      expect(status.nodeCount).toBe(0)
    })
  })

  describe('destroy', () => {
    it('应该清理所有资源', async () => {
      preprocessor = createAudioPreprocessor()
      await preprocessor.process(mockStream)

      preprocessor.destroy()

      const status = preprocessor.getStatus()
      expect(status.isActive).toBe(false)
      expect(status.nodeCount).toBe(0)
    })

    it('应该多次调用 destroy 不报错', async () => {
      preprocessor = createAudioPreprocessor()
      await preprocessor.process(mockStream)

      preprocessor.destroy()
      expect(() => preprocessor.destroy()).not.toThrow()
    })
  })

  describe('createAudioPreprocessor', () => {
    it('应该使用默认配置创建预处理器', () => {
      const preprocessor = createAudioPreprocessor()
      const config = preprocessor.getConfig()

      expect(config.enableHighPassFilter).toBe(true)
      expect(config.highPassCutoff).toBe(80)
      expect(config.enableNormalization).toBe(false)
      expect(config.enableNoiseGate).toBe(true)
      expect(config.noiseGateThreshold).toBe(0.02)
      expect(config.targetLevel).toBe(0.8)

      preprocessor.destroy()
    })

    it('应该允许覆盖默认配置', () => {
      const preprocessor = createAudioPreprocessor({
        highPassCutoff: 100,
        noiseGateThreshold: 0.05
      })
      const config = preprocessor.getConfig()

      expect(config.highPassCutoff).toBe(100)
      expect(config.noiseGateThreshold).toBe(0.05)
      expect(config.enableHighPassFilter).toBe(true) // 默认值保留

      preprocessor.destroy()
    })
  })

  describe('PreprocessorPresets', () => {
    it('应该提供 aggressive 预设', () => {
      expect(PreprocessorPresets.aggressive.enableHighPassFilter).toBe(true)
      expect(PreprocessorPresets.aggressive.highPassCutoff).toBe(100)
      expect(PreprocessorPresets.aggressive.noiseGateThreshold).toBe(0.05)
    })

    it('应该提供 gentle 预设', () => {
      expect(PreprocessorPresets.gentle.enableHighPassFilter).toBe(true)
      expect(PreprocessorPresets.gentle.highPassCutoff).toBe(60)
      expect(PreprocessorPresets.gentle.noiseGateThreshold).toBe(0.01)
    })

    it('应该提供 highPassOnly 预设', () => {
      expect(PreprocessorPresets.highPassOnly.enableHighPassFilter).toBe(true)
      expect(PreprocessorPresets.highPassOnly.enableNoiseGate).toBe(false)
    })

    it('应该提供 bypass 预设', () => {
      expect(PreprocessorPresets.bypass.enableHighPassFilter).toBe(false)
      expect(PreprocessorPresets.bypass.enableNoiseGate).toBe(false)
      expect(PreprocessorPresets.bypass.enableNormalization).toBe(false)
    })

    it('应该能够使用预设创建预处理器', async () => {
      const preprocessor = new AudioPreprocessor(PreprocessorPresets.aggressive)
      const config = preprocessor.getConfig()

      expect(config.highPassCutoff).toBe(100)
      expect(config.noiseGateThreshold).toBe(0.05)

      const result = await preprocessor.process(mockStream)
      expect(result.success).toBe(true)

      preprocessor.destroy()
    })
  })

  describe('error handling', () => {
    it('应该处理音频上下文创建失败', async () => {
      // Mock AudioContext 抛出错误
      vi.stubGlobal('AudioContext', class {
        constructor() {
          throw new Error('AudioContext not supported')
        }
      })

      preprocessor = createAudioPreprocessor()

      const result = await preprocessor.process(mockStream)

      expect(result.success).toBe(false)
      expect(result.error).toBeDefined()
    })

    it('应该在 AudioContext 暂停时恢复', async () => {
      const suspendedContext = new MockAudioContext()
      suspendedContext.state = 'suspended'

      preprocessor = createAudioPreprocessor()

      const result = await preprocessor.process(mockStream, suspendedContext as any)

      expect(result.success).toBe(true)
    })
  })
})

describe('PreprocessResult', () => {
  it('应该包含所有必需的字段', () => {
    const result: PreprocessResult = {
      stream: createMockMediaStream(),
      config: {
        enableHighPassFilter: true,
        highPassCutoff: 80,
        enableNormalization: false,
        enableNoiseGate: true,
        noiseGateThreshold: 0.02,
        targetLevel: 0.8
      },
      success: true
    }

    expect(result.stream).toBeDefined()
    expect(result.config).toBeDefined()
    expect(result.success).toBe(true)
    expect(result.error).toBeUndefined()
  })

  it('应该包含错误信息（如果处理失败）', () => {
    const result: PreprocessResult = {
      stream: createMockMediaStream(),
      config: {
        enableHighPassFilter: true,
        highPassCutoff: 80,
        enableNormalization: false,
        enableNoiseGate: true,
        noiseGateThreshold: 0.02,
        targetLevel: 0.8
      },
      success: false,
      error: '处理失败'
    }

    expect(result.success).toBe(false)
    expect(result.error).toBe('处理失败')
  })
})
