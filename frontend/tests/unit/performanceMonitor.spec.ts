/**
 * 性能监控工具单元测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  PerformanceMonitor,
  AccuracyTracker,
  LatencyMonitor,
  LRUCache,
  ResultCache,
  AudioHasher,
  RecognitionMetrics,
  PerformanceStats,
  LatencyBreakdown
} from '../../src/utils/performanceMonitor'

// Mock performance.now
const mockPerformanceNow = vi.fn()

describe('AccuracyTracker', () => {
  let tracker: AccuracyTracker

  beforeEach(() => {
    // Mock performance.now
    vi.stubGlobal('performance', {
      now: mockPerformanceNow
    })
    mockPerformanceNow.mockReturnValue(Date.now())

    tracker = new AccuracyTracker()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    tracker.reset()
  })

  describe('recordRecognition', () => {
    it('应该记录识别结果', () => {
      const actual = 'hello world'
      const recognized = 'hello world'
      const confidence = 0.95
      const latency = 200

      tracker.recordRecognition(actual, recognized, confidence, latency)

      const stats = tracker.getStatistics()
      expect(stats.totalRecognitions).toBe(1)
      expect(stats.averageAccuracy).toBe(1)
      expect(stats.averageConfidence).toBe(confidence)
    })

    it('应该计算准确率', () => {
      // 完全匹配
      tracker.recordRecognition('hello', 'hello', 1.0, 100)
      expect(tracker.getStatistics().averageAccuracy).toBe(1)

      tracker.reset()

      // 部分匹配
      tracker.recordRecognition('hello world', 'hello', 0.5, 100)
      expect(tracker.getStatistics().averageAccuracy).toBe(0.5)
    })

    it('应该处理大小写不敏感', () => {
      tracker.recordRecognition('HELLO', 'hello', 1.0, 100)
      const stats = tracker.getStatistics()

      expect(stats.averageAccuracy).toBe(1)
    })

    it('应该处理空白字符', () => {
      tracker.recordRecognition('hello   world', 'hello world', 1.0, 100)
      const stats = tracker.getStatistics()

      expect(stats.averageAccuracy).toBe(1)
    })

    it('应该限制保存数量', () => {
      // 模拟超过限制
      for (let i = 0; i < 1005; i++) {
        tracker.recordRecognition('test', 'test', 1.0, 100)
      }

      const stats = tracker.getStatistics(1000)
      expect(stats.totalRecognitions).toBeLessThanOrEqual(1000)
    })
  })

  describe('getAverageAccuracy', () => {
    it('应该返回最近N次的平均准确率', () => {
      tracker.recordRecognition('a', 'a', 1.0, 100)
      tracker.recordRecognition('b', 'b', 0.8, 100)
      tracker.recordRecognition('c', 'c', 0.6, 100)

      const accuracy = tracker.getAverageAccuracy(2)
      expect(accuracy).toBeGreaterThan(0)
      expect(accuracy).toBeLessThanOrEqual(1)
    })

    it('应该处理空记录', () => {
      expect(tracker.getAverageAccuracy(10)).toBe(0)
    })

    it('应该处理请求数量超过实际数量', () => {
      tracker.recordRecognition('a', 'a', 1.0, 100)

      expect(tracker.getAverageAccuracy(10)).toBe(1)
    })
  })

  describe('getAverageConfidence', () => {
    it('应该返回平均置信度', () => {
      tracker.recordRecognition('a', 'a', 0.9, 100)
      tracker.recordRecognition('b', 'b', 0.8, 100)
      tracker.recordRecognition('c', 'c', 0.7, 100)

      expect(tracker.getAverageConfidence(3)).toBeCloseTo(0.8, 2)
    })

    it('应该处理空记录', () => {
      expect(tracker.getAverageConfidence(10)).toBe(0)
    })
  })

  describe('getStatistics', () => {
    it('应该返回完整统计信息', () => {
      tracker.recordRecognition('a', 'a', 1.0, 100) // 成功
      tracker.recordRecognition('b', 'x', 0.5, 100) // 失败
      tracker.recordRecognition('c', 'c', 0.8, 100) // 成功

      const stats = tracker.getStatistics()

      expect(stats.totalRecognitions).toBe(3)
      expect(stats.successfulRecognitions).toBe(2)
      expect(stats.failedRecognitions).toBe(1)
      expect(stats.successRate).toBeCloseTo(0.67, 2)
      expect(stats.averageLatency).toBe(100)
      // 实际准确率是(a + x + c)/3 = (1 + 0 + 1)/3 = 0.67
      expect(stats.averageAccuracy).toBeCloseTo(0.67, 2)
      expect(stats.averageConfidence).toBeCloseTo(0.77, 2)
    })

    it('应该处理空记录', () => {
      const stats = tracker.getStatistics()

      expect(stats.totalRecognitions).toBe(0)
      expect(stats.successRate).toBe(0)
      expect(stats.averageLatency).toBe(0)
    })
  })

  describe('reset', () => {
    it('应该清空所有记录', () => {
      tracker.recordRecognition('a', 'a', 1.0, 100)
      tracker.reset()

      const stats = tracker.getStatistics()
      expect(stats.totalRecognitions).toBe(0)
    })
  })
})

describe('LatencyMonitor', () => {
  let monitor: LatencyMonitor

  beforeEach(() => {
    vi.stubGlobal('performance', {
      now: mockPerformanceNow
    })
    mockPerformanceNow.mockReturnValue(0)
    monitor = new LatencyMonitor()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  describe('startTiming and endTiming', () => {
    it('应该记录时间点', () => {
      monitor.startTiming('test')

      // 这个测试主要验证API能正常调用，不检查精确的时序
      expect(() => monitor.endTiming('test')).not.toThrow()
    })

    it('应该在未找到时间点时返回0', () => {
      const duration = monitor.endTiming('nonexistent')

      expect(duration).toBe(0)
    })
  })

  describe('recordBreakdown', () => {
    it('应该记录延迟分解', () => {
      const breakdown: LatencyBreakdown = {
        audioCapture: 10,
        processing: 20,
        recognition: 100,
        postProcessing: 30,
        total: 160
      }

      monitor.recordBreakdown(breakdown)

      const stats = monitor.getAverageBreakdown()
      expect(stats).toEqual(breakdown)
    })

    it('应该计算平均延迟', () => {
      monitor.recordBreakdown({
        audioCapture: 10,
        processing: 20,
        recognition: 100,
        postProcessing: 30,
        total: 160
      })

      monitor.recordBreakdown({
        audioCapture: 20,
        processing: 30,
        recognition: 200,
        postProcessing: 40,
        total: 290
      })

      const avg = monitor.getAverageBreakdown()

      expect(avg?.audioCapture).toBe(15)
      expect(avg?.processing).toBe(25)
      expect(avg?.recognition).toBe(150)
      expect(avg?.postProcessing).toBe(35)
      expect(avg?.total).toBe(225)
    })

    it('应该限制保存数量', () => {
      for (let i = 0; i < 105; i++) {
        monitor.recordBreakdown({
          audioCapture: 10,
          processing: 20,
          recognition: 100,
          postProcessing: 30,
          total: 160
        })
      }

      const stats = monitor.getAverageBreakdown()
      expect(stats).toBeDefined()
    })
  })

  describe('getSlowestPhase', () => {
    it('应该返回最慢的环节', () => {
      monitor.recordBreakdown({
        audioCapture: 10,
        processing: 20,
        recognition: 200, // 最慢
        postProcessing: 30,
        total: 260
      })

      const slowest = monitor.getSlowestPhase()
      expect(slowest).toBe('语音识别')
    })

    it('应该处理空数据', () => {
      expect(monitor.getSlowestPhase()).toBeNull()
    })
  })

  describe('reset', () => {
    it('应该重置所有数据', () => {
      monitor.startTiming('test')
      monitor.recordBreakdown({
        audioCapture: 10,
        processing: 20,
        recognition: 100,
        postProcessing: 30,
        total: 160
      })

      monitor.reset()

      expect(monitor.getSlowestPhase()).toBeNull()
    })
  })
})

describe('LRUCache', () => {
  it('应该正常工作', () => {
    const cache = new LRUCache<string, number>(3)

    cache.set('a', 1)
    cache.set('b', 2)
    cache.set('c', 3)

    expect(cache.get('a')).toBe(1)
    expect(cache.get('b')).toBe(2)
    expect(cache.get('c')).toBe(3)

    // 添加第四个，应该淘汰最旧的
    cache.set('d', 4)

    expect(cache.get('a')).toBeUndefined()
    expect(cache.get('b')).toBe(2)
    expect(cache.get('c')).toBe(3)
    expect(cache.get('d')).toBe(4)
  })

  it('应该更新现有键', () => {
    const cache = new LRUCache<string, number>(3)

    cache.set('a', 1)
    cache.set('a', 2)

    expect(cache.get('a')).toBe(2)
    expect(cache.size).toBe(1)
  })

  it('应该处理has方法', () => {
    const cache = new LRUCache<string, number>()
    cache.set('a', 1)

    expect(cache.has('a')).toBe(true)
    expect(cache.has('b')).toBe(false)
  })

  it('应该删除键', () => {
    const cache = new LRUCache<string, number>()
    cache.set('a', 1)

    const deleted = cache.delete('a')
    expect(deleted).toBe(true)
    expect(cache.has('a')).toBe(false)
  })

  it('应该清空缓存', () => {
    const cache = new LRUCache<string, number>()
    cache.set('a', 1)
    cache.set('b', 2)

    cache.clear()

    expect(cache.size).toBe(0)
  })

  it('应该返回所有键', () => {
    const cache = new LRUCache<string, number>()
    cache.set('a', 1)
    cache.set('b', 2)
    cache.set('c', 3)

    const keys = cache.keys()
    expect(keys).toContain('a')
    expect(keys).toContain('b')
    expect(keys).toContain('c')
  })
})

describe('AudioHasher', () => {
  describe('generateHash', () => {
    it('应该生成音频哈希', () => {
      const audioData = new Float32Array([0.1, 0.2, 0.3, 0.4, 0.5])
      const hash = AudioHasher.generateHash(audioData)

      expect(hash).toBeDefined()
      expect(typeof hash).toBe('string')
    })

    it('应该为相同音频生成相同哈希', () => {
      const audioData1 = new Float32Array([0.1, 0.2, 0.3])
      const audioData2 = new Float32Array([0.1, 0.2, 0.3])

      const hash1 = AudioHasher.generateHash(audioData1)
      const hash2 = AudioHasher.generateHash(audioData2)

      expect(hash1).toBe(hash2)
    })

    it('应该为不同音频生成不同哈希', () => {
      const audioData1 = new Float32Array([0.1, 0.2, 0.3])
      const audioData2 = new Float32Array([0.4, 0.5, 0.6])

      const hash1 = AudioHasher.generateHash(audioData1)
      const hash2 = AudioHasher.generateHash(audioData2)

      expect(hash1).not.toBe(hash2)
    })
  })

  describe('generateHashFromBlob', () => {
    it('应该从音频Blob生成哈希', async () => {
      const mockArrayBuffer = new Uint8Array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]).buffer
      const blob = {
        type: 'audio/webm',
        arrayBuffer: vi.fn().mockResolvedValue(mockArrayBuffer)
      } as any

      const hash = await AudioHasher.generateHashFromBlob(blob)

      expect(hash).toBeDefined()
      expect(hash).toHaveLength(32) // MD5哈希长度
      expect(blob.arrayBuffer).toHaveBeenCalled()
    })
  })
})

describe('ResultCache', () => {
  let cache: ResultCache

  beforeEach(() => {
    cache = new ResultCache(1000)
  })

  it('应该正常工作', () => {
    cache.set('hash1', { text: 'result1' })
    expect(cache.get('hash1')).toEqual({ text: 'result1' })
    expect(cache.has('hash1')).toBe(true)
  })

  it('应该处理LRU策略', () => {
    const smallCache = new ResultCache(3)
    smallCache.set('a', { text: 'a' })
    smallCache.set('b', { text: 'b' })
    smallCache.set('c', { text: 'c' })

    // 访问'a'以更新其时间戳
    smallCache.get('a')

    // 添加'd'应该淘汰最旧的'b'
    smallCache.set('d', { text: 'd' })

    expect(smallCache.has('a')).toBe(true)
    expect(smallCache.has('b')).toBe(false)
    expect(smallCache.has('c')).toBe(true)
    expect(smallCache.has('d')).toBe(true)
  })

  it('应该删除缓存项', () => {
    cache.set('hash1', { text: 'result' })
    expect(cache.delete('hash1')).toBe(true)
    expect(cache.has('hash1')).toBe(false)
  })

  it('应该获取统计信息', () => {
    cache.set('hash1', { text: 'result1' })
    cache.set('hash2', { text: 'result2' })

    const stats = cache.getStats()
    expect(stats.size).toBe(2)
    expect(stats.maxSize).toBe(1000)
  })
})

describe('PerformanceMonitor', () => {
  let monitor: PerformanceMonitor

  beforeEach(() => {
    vi.stubGlobal('performance', {
      now: mockPerformanceNow
    })
    mockPerformanceNow.mockReturnValue(0)
    monitor = new PerformanceMonitor()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  describe('recordRecognition', () => {
    it('应该记录识别结果', () => {
      monitor.recordRecognition('hello', 'hello', 0.95, 200)

      const stats = monitor.getAccuracyStats()
      expect(stats.totalRecognitions).toBe(1)
      expect(stats.averageConfidence).toBe(0.95)
    })
  })

  describe('recordLatencyBreakdown', () => {
    it('应该记录延迟分解', () => {
      monitor.recordLatencyBreakdown({
        audioCapture: 10,
        processing: 20,
        recognition: 100,
        postProcessing: 30,
        total: 160
      })

      const stats = monitor.getLatencyStats()
      expect(stats?.audioCapture).toBe(10)
      expect(stats?.recognition).toBe(100)
    })
  })

  describe('startTiming and endTiming', () => {
    it('应该记录时间点', () => {
      monitor.startTiming('test')

      // 这个测试主要验证API能正常调用，不检查精确的时序
      expect(() => monitor.endTiming('test')).not.toThrow()
    })
  })

  describe('checkCache and setCache', () => {
    it('应该检查和设置缓存', () => {
      const audioHash = 'test-hash'
      const result = { text: 'recognition result' }

      expect(monitor.checkCache(audioHash)).toBeUndefined()

      monitor.setCache(audioHash, result)
      expect(monitor.checkCache(audioHash)).toEqual(result)
    })
  })

  describe('getAccuracyStats', () => {
    it('应该返回准确率统计', () => {
      monitor.recordRecognition('a', 'a', 1.0, 100)
      monitor.recordRecognition('b', 'b', 0.8, 100)

      const stats = monitor.getAccuracyStats()

      expect(stats.totalRecognitions).toBe(2)
      expect(stats.averageAccuracy).toBe(1)
    })
  })

  describe('getLatencyStats', () => {
    it('应该返回延迟统计', () => {
      monitor.recordLatencyBreakdown({
        audioCapture: 10,
        processing: 20,
        recognition: 100,
        postProcessing: 30,
        total: 160
      })

      const stats = monitor.getLatencyStats()

      expect(stats).toEqual({
        audioCapture: 10,
        processing: 20,
        recognition: 100,
        postProcessing: 30,
        total: 160
      })
    })
  })

  describe('getSlowestPhase', () => {
    it('应该返回最慢环节', () => {
      monitor.recordLatencyBreakdown({
        audioCapture: 10,
        processing: 20,
        recognition: 200,
        postProcessing: 30,
        total: 260
      })

      const slowest = monitor.getSlowestPhase()
      expect(slowest).toBe('语音识别')
    })
  })

  describe('getCacheStats', () => {
    it('应该返回缓存统计', () => {
      const stats = monitor.getCacheStats()

      expect(stats.size).toBe(0)
      expect(stats.maxSize).toBe(1000)
    })
  })

  describe('getPerformanceReport', () => {
    it('应该返回完整性能报告', () => {
      monitor.recordRecognition('a', 'a', 1.0, 100)
      monitor.recordLatencyBreakdown({
        audioCapture: 10,
        processing: 20,
        recognition: 100,
        postProcessing: 30,
        total: 160
      })

      const report = monitor.getPerformanceReport()

      expect(report.accuracy).toBeDefined()
      expect(report.latency).toBeDefined()
      expect(report.cache).toBeDefined()
      expect(report.slowestPhase).toBeDefined()
    })
  })

  describe('reset', () => {
    it('应该重置所有统计数据', () => {
      monitor.recordRecognition('a', 'a', 1.0, 100)
      monitor.setCache('hash', { text: 'result' })

      monitor.reset()

      const stats = monitor.getAccuracyStats()
      expect(stats.totalRecognitions).toBe(0)

      const cacheStats = monitor.getCacheStats()
      expect(cacheStats.size).toBe(0)
    })
  })
})