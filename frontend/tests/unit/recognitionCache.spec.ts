/**
 * LRU 缓存单元测试
 * 验证缓存策略、淘汰机制和统计功能
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import {
  RecognitionLRUCache,
  createRecognitionCache,
  LRUCacheConfig,
  RecognitionCacheEntry,
  CacheStats
} from '@/utils/recognitionCache'

describe('RecognitionLRUCache', () => {
  let cache: RecognitionLRUCache

  beforeEach(() => {
    // 每个测试前创建新缓存实例
    cache = new RecognitionLRUCache()
    // 使用 fake timers 进行时间相关测试
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('基础功能', () => {
    it('应该创建缓存实例', () => {
      expect(cache).toBeInstanceOf(RecognitionLRUCache)
      expect(cache.size).toBe(0)
    })

    it('应该使用便利函数创建缓存', () => {
      const cache2 = createRecognitionCache()
      expect(cache2).toBeInstanceOf(RecognitionLRUCache)
    })

    it('应该接受自定义配置', () => {
      const config: LRUCacheConfig = {
        maxSize: 50,
        ttl: 60000
      }
      const customCache = new RecognitionLRUCache(config)
      expect(customCache).toBeInstanceOf(RecognitionLRUCache)
    })

    it('应该使用默认配置', () => {
      const defaultCache = new RecognitionLRUCache()
      const stats = defaultCache.getStats()
      expect(stats.maxSize).toBe(100)
      expect(defaultCache['ttl']).toBe(300000)
    })
  })

  describe('缓存设置与获取', () => {
    it('应该设置和获取缓存条目', () => {
      const entry: Omit<RecognitionCacheEntry, 'accessCount'> = {
        transcript: 'Hello world',
        confidence: 0.95,
        timestamp: Date.now()
      }

      cache.set('key1', entry)
      const retrieved = cache.get('key1')

      expect(retrieved).toBeDefined()
      expect(retrieved?.transcript).toBe('Hello world')
      expect(retrieved?.confidence).toBe(0.95)
      expect(retrieved?.accessCount).toBe(1)
    })

    it('应该增加访问计数', () => {
      const entry: Omit<RecognitionCacheEntry, 'accessCount'> = {
        transcript: 'Test',
        confidence: 0.8,
        timestamp: Date.now()
      }

      cache.set('key1', entry)
      cache.get('key1')
      cache.get('key1')
      cache.get('key1')

      const retrieved = cache.get('key1')
      expect(retrieved?.accessCount).toBe(4)
    })

    it('应该在获取时更新时间戳', () => {
      const entry: Omit<RecognitionCacheEntry, 'accessCount'> = {
        transcript: 'Test',
        confidence: 0.8,
        timestamp: Date.now()
      }

      cache.set('key1', entry)
      const firstGet = cache.get('key1')
      const firstTimestamp = firstGet?.timestamp ?? 0

      // 等待一小段时间（使用 fake timers）
      vi.advanceTimersByTime(100)

      const secondGet = cache.get('key1')
      const secondTimestamp = secondGet?.timestamp ?? 0

      // 时间戳应该增加
      expect(secondTimestamp).toBeGreaterThan(firstTimestamp)
    })

    it('应该返回 undefined 对于不存在的键', () => {
      const result = cache.get('nonexistent')
      expect(result).toBeUndefined()
    })

    it('应该正确更新已存在的键', () => {
      cache.set('key1', {
        transcript: 'Original',
        confidence: 0.5,
        timestamp: Date.now()
      })

      cache.set('key1', {
        transcript: 'Updated',
        confidence: 0.9,
        timestamp: Date.now()
      })

      const result = cache.get('key1')
      expect(result?.transcript).toBe('Updated')
      expect(result?.confidence).toBe(0.9)
      expect(result?.accessCount).toBe(1) // 重置为0后+1
    })
  })

  describe('LRU 淘汰机制', () => {
    it('应该在达到最大容量时淘汰最久未访问的条目', () => {
      const smallCache = new RecognitionLRUCache({ maxSize: 3 })

      // 添加3个条目
      smallCache.set('key1', { transcript: 'A', confidence: 0.8, timestamp: Date.now() })
      smallCache.set('key2', { transcript: 'B', confidence: 0.8, timestamp: Date.now() })
      smallCache.set('key3', { transcript: 'C', confidence: 0.8, timestamp: Date.now() })

      expect(smallCache.size).toBe(3)

      // 访问 key2 和 key3，使 key1 成为最久未访问
      vi.advanceTimersByTime(100)
      smallCache.get('key2')
      vi.advanceTimersByTime(100)
      smallCache.get('key3')

      // 添加第4个条目，应该淘汰 key1
      smallCache.set('key4', { transcript: 'D', confidence: 0.8, timestamp: Date.now() })

      expect(smallCache.size).toBe(3)
      expect(smallCache.has('key1')).toBe(false)
      expect(smallCache.has('key2')).toBe(true)
      expect(smallCache.has('key3')).toBe(true)
      expect(smallCache.has('key4')).toBe(true)
    })

    it('应该在更新已存在键时不触发淘汰', () => {
      const smallCache = new RecognitionLRUCache({ maxSize: 2 })

      smallCache.set('key1', { transcript: 'A', confidence: 0.8, timestamp: Date.now() })
      smallCache.set('key2', { transcript: 'B', confidence: 0.8, timestamp: Date.now() })

      // 更新 key1，不应该触发淘汰
      smallCache.set('key1', { transcript: 'AUpdated', confidence: 0.9, timestamp: Date.now() })

      expect(smallCache.size).toBe(2)
      expect(smallCache.has('key1')).toBe(true)
      expect(smallCache.has('key2')).toBe(true)
    })
  })

  describe('TTL 过期机制', () => {
    it('应该返回 undefined 对于过期的条目', () => {
      const shortTTLCache = new RecognitionLRUCache({ ttl: 100 })

      shortTTLCache.set('key1', {
        transcript: 'Will expire',
        confidence: 0.8,
        timestamp: Date.now()
      })

      // 等待超过 TTL
      vi.advanceTimersByTime(150)

      const result = shortTTLCache.get('key1')
      expect(result).toBeUndefined()
    })

    it('应该在获取时删除过期条目', () => {
      const shortTTLCache = new RecognitionLRUCache({ ttl: 100 })

      shortTTLCache.set('key1', {
        transcript: 'Expire me',
        confidence: 0.8,
        timestamp: Date.now()
      })

      expect(shortTTLCache.size).toBe(1)

      vi.advanceTimersByTime(150)

      shortTTLCache.get('key1')

      expect(shortTTLCache.size).toBe(0)
    })

    it('应该正确清理过期条目', () => {
      const shortTTLCache = new RecognitionLRUCache({ ttl: 100 })

      shortTTLCache.set('key1', {
        transcript: 'A',
        confidence: 0.8,
        timestamp: Date.now() - 200
      })
      shortTTLCache.set('key2', {
        transcript: 'B',
        confidence: 0.8,
        timestamp: Date.now()
      })

      const cleaned = shortTTLCache.cleanExpired()

      expect(cleaned).toBe(1)
      expect(shortTTLCache.size).toBe(1)
      expect(shortTTLCache.has('key1')).toBe(false)
      expect(shortTTLCache.has('key2')).toBe(true)
    })
  })

  describe('统计功能', () => {
    it('应该正确跟踪命中和未命中', () => {
      cache.set('key1', {
        transcript: 'Hit me',
        confidence: 0.8,
        timestamp: Date.now()
      })

      cache.get('key1') // 命中
      cache.get('key1') // 命中
      cache.get('nonexistent') // 未命中

      const stats = cache.getStats()

      expect(stats.hits).toBe(2)
      expect(stats.misses).toBe(1)
      expect(stats.hitRate).toBeCloseTo(2 / 3, 2)
    })

    it('应该返回正确的统计信息', () => {
      const smallCache = new RecognitionLRUCache({ maxSize: 10 })

      for (let i = 0; i < 5; i++) {
        smallCache.set(`key${i}`, {
          transcript: `Value${i}`,
          confidence: 0.8,
          timestamp: Date.now()
        })
      }

      smallCache.get('key1')
      smallCache.get('key2')
      smallCache.get('nonexistent')

      const stats: CacheStats = smallCache.getStats()

      expect(stats.size).toBe(5)
      expect(stats.maxSize).toBe(10)
      expect(stats.utilization).toBe(0.5)
      expect(stats.hits).toBe(2)
      expect(stats.misses).toBe(1)
      expect(stats.hitRate).toBeCloseTo(2 / 3, 2)
    })

    it('应该正确处理空缓存的统计', () => {
      const stats = cache.getStats()

      expect(stats.size).toBe(0)
      expect(stats.hits).toBe(0)
      expect(stats.misses).toBe(0)
      expect(stats.hitRate).toBe(0)
    })

    it('应该重置统计计数器', () => {
      cache.set('key1', {
        transcript: 'Test',
        confidence: 0.8,
        timestamp: Date.now()
      })

      cache.get('key1')
      cache.get('nonexistent')

      cache.resetStats()

      const stats = cache.getStats()
      expect(stats.hits).toBe(0)
      expect(stats.misses).toBe(0)
      expect(stats.hitRate).toBe(0)
      expect(stats.size).toBe(1) // 缓存条目不受影响
    })
  })

  describe('缓存操作', () => {
    it('应该检查键是否存在', () => {
      expect(cache.has('key1')).toBe(false)

      cache.set('key1', {
        transcript: 'Exists',
        confidence: 0.8,
        timestamp: Date.now()
      })

      expect(cache.has('key1')).toBe(true)
    })

    it('应该删除指定条目', () => {
      cache.set('key1', {
        transcript: 'Delete me',
        confidence: 0.8,
        timestamp: Date.now()
      })

      expect(cache.has('key1')).toBe(true)

      const deleted = cache.delete('key1')

      expect(deleted).toBe(true)
      expect(cache.has('key1')).toBe(false)
    })

    it('删除不存在的键应该返回 false', () => {
      const deleted = cache.delete('nonexistent')
      expect(deleted).toBe(false)
    })

    it('应该清空所有缓存', () => {
      cache.set('key1', {
        transcript: 'A',
        confidence: 0.8,
        timestamp: Date.now()
      })
      cache.set('key2', {
        transcript: 'B',
        confidence: 0.8,
        timestamp: Date.now()
      })

      expect(cache.size).toBe(2)

      cache.clear()

      expect(cache.size).toBe(0)
      expect(cache.has('key1')).toBe(false)
      expect(cache.has('key2')).toBe(false)
    })

    it('clear() 应该重置统计计数器', () => {
      cache.set('key1', {
        transcript: 'Test',
        confidence: 0.8,
        timestamp: Date.now()
      })

      cache.get('key1')

      cache.clear()

      const stats = cache.getStats()
      expect(stats.hits).toBe(0)
      expect(stats.misses).toBe(0)
    })

    it('应该获取所有键', () => {
      cache.set('key1', {
        transcript: 'A',
        confidence: 0.8,
        timestamp: Date.now()
      })
      cache.set('key2', {
        transcript: 'B',
        confidence: 0.8,
        timestamp: Date.now()
      })

      const keys = cache.keys()
      expect(keys).toContain('key1')
      expect(keys).toContain('key2')
      expect(keys.length).toBe(2)
    })

    it('应该获取所有值', () => {
      cache.set('key1', {
        transcript: 'A',
        confidence: 0.8,
        timestamp: Date.now()
      })
      cache.set('key2', {
        transcript: 'B',
        confidence: 0.9,
        timestamp: Date.now()
      })

      const values = cache.values()
      expect(values.length).toBe(2)

      const transcripts = values.map(v => v.transcript)
      expect(transcripts).toContain('A')
      expect(transcripts).toContain('B')
    })
  })

  describe('实际使用场景', () => {
    it('应该模拟语音识别缓存的使用流程', () => {
      const recognitionCache = new RecognitionLRUCache({
        maxSize: 50,
        ttl: 300000 // 5分钟
      })

      // 模拟第一次识别结果
      const audioFingerprint1 = 'audio_12345'
      recognitionCache.set(audioFingerprint1, {
        transcript: '你好世界',
        confidence: 0.92,
        timestamp: Date.now()
      })

      // 尝试识别相同音频，应该从缓存获取
      const cached = recognitionCache.get(audioFingerprint1)
      expect(cached?.transcript).toBe('你好世界')
      expect(cached?.confidence).toBe(0.92)

      // 验证缓存命中
      const stats = recognitionCache.getStats()
      expect(stats.hits).toBe(1)
      expect(stats.misses).toBe(0)
    })

    it('应该在高频访问下保持性能', () => {
      const largeCache = new RecognitionLRUCache({ maxSize: 1000 })

      // 添加大量条目
      for (let i = 0; i < 1000; i++) {
        largeCache.set(`key${i}`, {
          transcript: `Text${i}`,
          confidence: Math.random(),
          timestamp: Date.now()
        })
      }

      expect(largeCache.size).toBe(1000)

      // 添加更多条目，触发淘汰
      largeCache.set('key1000', {
        transcript: 'Latest',
        confidence: 0.9,
        timestamp: Date.now()
      })

      // 第1001个条目会触发淘汰，但缓存大小仍然是1000
      expect(largeCache.size).toBe(1000) // 保持最大容量
    })

    it('应该处理并发访问场景', () => {
      const testCache = new RecognitionLRUCache({ maxSize: 10 })

      // 先添加9个条目，留下一个位置
      for (let i = 0; i < 9; i++) {
        testCache.set(`cold${i}`, {
          transcript: `Cold${i}`,
          confidence: 0.5,
          timestamp: Date.now()
        })
        vi.advanceTimersByTime(10)
      }

      // 添加 hot 键
      testCache.set('hot', {
        transcript: 'Frequently accessed',
        confidence: 0.9,
        timestamp: Date.now()
      })
      vi.advanceTimersByTime(10)

      // hot 键被多次访问，更新其时间戳
      for (let i = 0; i < 10; i++) {
        testCache.get('hot')
        vi.advanceTimersByTime(10)
      }

      // 添加第11个条目，触发淘汰
      // 最久未访问的 cold0 应该被淘汰（因为 hot 最近被访问过）
      testCache.set('cold9', {
        transcript: 'Cold9',
        confidence: 0.5,
        timestamp: Date.now()
      })

      // 验证结果
      expect(testCache.has('hot')).toBe(true)
      expect(testCache.has('cold0')).toBe(false) // cold0 被淘汰
      expect(testCache.size).toBe(10)
    })
  })

  describe('边界情况', () => {
    it('应该处理空字符串键', () => {
      cache.set('', {
        transcript: 'Empty key',
        confidence: 0.8,
        timestamp: Date.now()
      })

      expect(cache.has('')).toBe(true)
      expect(cache.get('')?.transcript).toBe('Empty key')
    })

    it('应该处理特殊字符键', () => {
      const specialKey = 'key/with\\special:chars?and#symbols'
      cache.set(specialKey, {
        transcript: 'Special',
        confidence: 0.8,
        timestamp: Date.now()
      })

      expect(cache.get(specialKey)?.transcript).toBe('Special')
    })

    it('应该处理零置信度', () => {
      cache.set('key1', {
        transcript: 'Low confidence',
        confidence: 0,
        timestamp: Date.now()
      })

      expect(cache.get('key1')?.confidence).toBe(0)
    })

    it('应该处理空文本', () => {
      cache.set('key1', {
        transcript: '',
        confidence: 0.5,
        timestamp: Date.now()
      })

      expect(cache.get('key1')?.transcript).toBe('')
    })

    it('应该处理最大容量为1的情况', () => {
      const tinyCache = new RecognitionLRUCache({ maxSize: 1 })

      tinyCache.set('key1', {
        transcript: 'A',
        confidence: 0.8,
        timestamp: Date.now()
      })

      expect(tinyCache.size).toBe(1)

      // 添加第二个键，会触发淘汰
      tinyCache.set('key2', {
        transcript: 'B',
        confidence: 0.8,
        timestamp: Date.now()
      })

      // 第一个键应该被淘汰
      expect(tinyCache.size).toBe(1)
      expect(tinyCache.has('key1')).toBe(false)
      expect(tinyCache.has('key2')).toBe(true)
    })

    it('应该处理零 TTL', () => {
      const zeroTTLCache = new RecognitionLRUCache({ ttl: 0 })

      // 手动设置一个过去的时间戳
      zeroTTLCache.set('key1', {
        transcript: 'Immediately expired',
        confidence: 0.8,
        timestamp: Date.now() - 100  // 100ms 前
      })

      // 应该立即过期
      const result = zeroTTLCache.get('key1')
      expect(result).toBeUndefined()
    })
  })
})
