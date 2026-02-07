/**
 * 音频缓冲器单元测试
 * 验证缓冲策略和音频合并逻辑
 */

import { describe, it, expect } from 'vitest'
import { AudioBuffer, createAudioBuffer, AudioBufferConfig } from '@/utils/audioBuffer'

/**
 * 创建模拟音频 Blob
 * @param durationMs 音频时长（毫秒）
 * @returns 模拟的音频 Blob
 */
function createMockAudioBlob(durationMs: number): Blob {
  // 假设 16kHz, 16bit, 单声道
  const sampleRate = 16000
  const bitDepth = 16
  const channels = 1

  // 计算字节数
  const bytesPerSecond = (sampleRate * bitDepth * channels) / 8
  const bytes = (durationMs / 1000) * bytesPerSecond

  // 创建模拟数据
  const arrayBuffer = new ArrayBuffer(Math.ceil(bytes))
  const dataView = new Uint8Array(arrayBuffer)

  return new Blob([dataView], { type: 'audio/webm' })
}

describe('AudioBuffer', () => {
  describe('基础功能', () => {
    it('应该创建音频缓冲器实例', () => {
      const buffer = new AudioBuffer()
      expect(buffer).toBeInstanceOf(AudioBuffer)
      expect(buffer.isEmpty()).toBe(true)
    })

    it('应该使用便利函数创建缓冲器', () => {
      const buffer = createAudioBuffer()
      expect(buffer).toBeInstanceOf(AudioBuffer)
    })

    it('应该接受自定义配置', () => {
      const config: AudioBufferConfig = {
        bufferSize: 3000,
        bufferThreshold: 1500,
        minAudioLength: 600
      }
      const buffer = new AudioBuffer(config)
      expect(buffer).toBeInstanceOf(AudioBuffer)
    })
  })

  describe('音频添加与缓冲', () => {
    it('应该缓冲短音频片段', () => {
      const buffer = new AudioBuffer({
        bufferThreshold: 1000,
        minAudioLength: 500
      })

      // 添加300ms音频（小于minAudioLength）
      const shortAudio = createMockAudioBlob(300)
      const result = buffer.add(shortAudio)

      // 应该被缓冲
      expect(result).toBe(true)
      expect(buffer.getChunkCount()).toBe(1)
      expect(buffer.getTotalDuration()).toBe(300)
    })

    it('应该在达到阈值时停止缓冲', () => {
      const buffer = new AudioBuffer({
        bufferSize: 2000,
        bufferThreshold: 1000,
        minAudioLength: 500
      })

      // 添加多个短音频片段
      buffer.add(createMockAudioBlob(300))
      buffer.add(createMockAudioBlob(400))
      buffer.add(createMockAudioBlob(400))

      // 总时长1100ms，超过阈值1000ms
      // 最后一次add应该返回false
      expect(buffer.getTotalDuration()).toBeGreaterThanOrEqual(1000)
      expect(buffer.isReady()).toBe(true)
    })

    it('应该正确估算音频时长', () => {
      const buffer = new AudioBuffer()

      // 添加500ms音频
      buffer.add(createMockAudioBlob(500))

      // 时长应该是500ms（允许小误差）
      expect(buffer.getTotalDuration()).toBeCloseTo(500, 0)
    })

    it('应该拒绝超过最大缓冲区的音频', () => {
      const buffer = new AudioBuffer({
        bufferSize: 1000,  // 最大1秒
        bufferThreshold: 500,
        minAudioLength: 200
      })

      // 添加接近最大值的音频
      buffer.add(createMockAudioBlob(900))
      expect(buffer.getChunkCount()).toBe(1)

      // 尝试添加更多，应该被拒绝
      const result = buffer.add(createMockAudioBlob(200))
      expect(result).toBe(false)
    })
  })

  describe('状态查询', () => {
    it('应该返回正确的缓冲区状态', () => {
      const buffer = new AudioBuffer({
        bufferThreshold: 1000
      })

      buffer.add(createMockAudioBlob(500))

      const state = buffer.getState()
      expect(state.chunkCount).toBe(1)
      expect(state.totalDuration).toBe(500)
      expect(state.isThresholdReached).toBe(false)
      expect(state.totalSize).toBeGreaterThan(0)
    })

    it('应该检测阈值是否已达到', () => {
      const buffer = new AudioBuffer({
        bufferThreshold: 1000
      })

      expect(buffer.isReady()).toBe(false)

      buffer.add(createMockAudioBlob(1000))
      expect(buffer.isReady()).toBe(true)
    })

    it('应该检测缓冲区是否为空', () => {
      const buffer = new AudioBuffer()

      expect(buffer.isEmpty()).toBe(true)

      buffer.add(createMockAudioBlob(100))
      expect(buffer.isEmpty()).toBe(false)
    })
  })

  describe('清空与刷新', () => {
    it('应该正确清空缓冲区', () => {
      const buffer = new AudioBuffer()

      buffer.add(createMockAudioBlob(500))
      buffer.add(createMockAudioBlob(300))

      expect(buffer.isEmpty()).toBe(false)

      buffer.clear()

      expect(buffer.isEmpty()).toBe(true)
      expect(buffer.getChunkCount()).toBe(0)
      expect(buffer.getTotalDuration()).toBe(0)
    })

    it('应该刷新并返回合并的音频', () => {
      const buffer = new AudioBuffer()

      buffer.add(createMockAudioBlob(300))
      buffer.add(createMockAudioBlob(400))
      buffer.add(createMockAudioBlob(300))

      const mergedBlob = buffer.flush()

      expect(mergedBlob).toBeInstanceOf(Blob)
      expect(mergedBlob?.type).toBe('audio/webm')
      expect(buffer.isEmpty()).toBe(true)
    })

    it('空缓冲区刷新应该返回null', () => {
      const buffer = new AudioBuffer()

      const mergedBlob = buffer.flush()
      expect(mergedBlob).toBeNull()
    })
  })

  describe('实际使用场景', () => {
    it('应该模拟 MediaRecorder 音频缓冲流程', () => {
      const buffer = new AudioBuffer({
        bufferSize: 2000,
        bufferThreshold: 1000,
        minAudioLength: 500
      })

      // 模拟 MediaRecorder 产生的音频块
      const chunks = [250, 300, 350, 400, 500]  // 毫秒
      let shouldBuffer = true

      for (const duration of chunks) {
        const chunk = createMockAudioBlob(duration)
        shouldBuffer = buffer.add(chunk)

        if (!shouldBuffer) {
          break
        }
      }

      // 应该在总时长超过1000ms时停止缓冲
      expect(shouldBuffer).toBe(false)
      expect(buffer.getTotalDuration()).toBeGreaterThanOrEqual(1000)

      // 刷新获取合并音频
      const merged = buffer.flush()
      expect(merged).toBeInstanceOf(Blob)
    })

    it('应该处理边界情况：正好达到阈值', () => {
      const buffer = new AudioBuffer({
        bufferSize: 2000,
        bufferThreshold: 1000,
        minAudioLength: 500
      })

      // 添加正好1000ms的音频
      buffer.add(createMockAudioBlob(500))
      buffer.add(createMockAudioBlob(500))

      expect(buffer.isReady()).toBe(true)
      expect(buffer.getTotalDuration()).toBe(1000)
    })

    it('应该处理边界情况：单个长音频', () => {
      const buffer = new AudioBuffer({
        bufferSize: 2000,
        bufferThreshold: 1000,
        minAudioLength: 500
      })

      // 添加单个1500ms音频
      const result = buffer.add(createMockAudioBlob(1500))

      // 单个长音频超过minAudioLength且超过threshold
      // 应该被添加到缓冲区，但返回false表示已达到阈值
      expect(result).toBe(false)  // 修正：超过阈值应该返回false
      expect(buffer.getTotalDuration()).toBe(1500)
      expect(buffer.isReady()).toBe(true)  // 应该标记为ready
    })
  })

  describe('性能与边界', () => {
    it('应该处理大量小块音频', () => {
      const buffer = new AudioBuffer({
        bufferSize: 5000,
        bufferThreshold: 2000,
        minAudioLength: 100
      })

      // 添加100个50ms的音频块
      for (let i = 0; i < 100; i++) {
        buffer.add(createMockAudioBlob(50))
      }

      expect(buffer.getChunkCount()).toBeLessThanOrEqual(100)
      expect(buffer.getTotalDuration()).toBeGreaterThan(0)
    })

    it('应该正确计算总大小', () => {
      const buffer = new AudioBuffer()

      const chunk1 = createMockAudioBlob(500)
      const chunk2 = createMockAudioBlob(300)

      const expectedSize = chunk1.size + chunk2.size

      buffer.add(chunk1)
      buffer.add(chunk2)

      expect(buffer.getTotalSize()).toBe(expectedSize)
    })

    it('应该处理零大小音频', () => {
      const buffer = new AudioBuffer()

      const emptyBlob = new Blob([], { type: 'audio/webm' })
      const result = buffer.add(emptyBlob)

      // 零大小音频应该被缓冲但不增加时长
      expect(result).toBe(true)
      expect(buffer.getTotalDuration()).toBe(0)
    })
  })
})
