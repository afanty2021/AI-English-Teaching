/**
 * LRU 缓存模块
 * 用于缓存语音识别结果，避免重复识别相同或相似的音频
 */

/**
 * 缓存条目接口
 */
export interface RecognitionCacheEntry {
  /** 识别的文本结果 */
  transcript: string
  /** 置信度 (0-1) */
  confidence: number
  /** 时间戳 */
  timestamp: number
  /** 访问次数 */
  accessCount: number
}

/**
 * 缓存统计信息
 */
export interface CacheStats {
  /** 当前缓存大小 */
  size: number
  /** 最大缓存大小 */
  maxSize: number
  /** 缓存利用率 (0-1) */
  utilization: number
  /** 缓存命中次数 */
  hits: number
  /** 缓存未命中次数 */
  misses: number
  /** 命中率 (0-1) */
  hitRate: number
}

/**
 * LRU 缓存配置接口
 */
export interface LRUCacheConfig {
  /** 最大缓存条目数 */
  maxSize?: number
  /** 缓存条目有效期（毫秒） */
  ttl?: number
}

/**
 * LRU (Least Recently Used) 缓存实现
 * 用于存储语音识别结果，自动淘汰最久未使用的条目
 */
export class RecognitionLRUCache {
  private cache = new Map<string, RecognitionCacheEntry>()
  private readonly maxSize: number
  private readonly ttl: number
  private hits = 0
  private misses = 0

  constructor(config: LRUCacheConfig = {}) {
    this.maxSize = config.maxSize ?? 100
    this.ttl = config.ttl ?? 300000 // 默认5分钟
  }

  /**
   * 设置缓存条目
   * @param key 缓存键
   * @param value 缓存值（不包含 accessCount）
   */
  set(key: string, value: Omit<RecognitionCacheEntry, 'accessCount'>): void {
    // 如果键已存在，更新值并重置访问计数
    if (this.cache.has(key)) {
      this.cache.set(key, {
        ...value,
        accessCount: 0
      })
      return
    }

    // 检查容量限制
    if (this.cache.size >= this.maxSize) {
      this.evictLRU()
    }

    // 添加新条目
    this.cache.set(key, {
      ...value,
      accessCount: 0
    })
  }

  /**
   * 获取缓存条目
   * @param key 缓存键
   * @returns 缓存条目或 undefined（如果不存在或已过期）
   */
  get(key: string): RecognitionCacheEntry | undefined {
    const entry = this.cache.get(key)

    // 条目不存在
    if (!entry) {
      this.misses++
      return undefined
    }

    // 检查是否过期
    const now = Date.now()
    if (now - entry.timestamp > this.ttl) {
      this.cache.delete(key)
      this.misses++
      return undefined
    }

    // 更新访问信息
    entry.accessCount++
    entry.timestamp = now
    this.hits++

    return entry
  }

  /**
   * 检查缓存键是否存在（不考虑过期）
   * @param key 缓存键
   * @returns 是否存在
   */
  has(key: string): boolean {
    return this.cache.has(key)
  }

  /**
   * 删除指定缓存条目
   * @param key 缓存键
   * @returns 是否删除成功
   */
  delete(key: string): boolean {
    return this.cache.delete(key)
  }

  /**
   * 淘汰最久未访问的条目
   */
  private evictLRU(): void {
    let oldestKey: string | null = null
    let oldestTime = Date.now()

    // 找到最久未访问的条目
    for (const [key, entry] of this.cache.entries()) {
      if (entry.timestamp < oldestTime) {
        oldestTime = entry.timestamp
        oldestKey = key
      }
    }

    // 如果找到最旧的条目，删除它
    if (oldestKey) {
      this.cache.delete(oldestKey)
      return
    }

    // 如果所有条目的时间戳都相同，删除第一个条目
    const firstKey = this.cache.keys().next().value
    if (firstKey) {
      this.cache.delete(firstKey)
    }
  }

  /**
   * 清空所有缓存
   */
  clear(): void {
    this.cache.clear()
    this.hits = 0
    this.misses = 0
  }

  /**
   * 获取当前缓存大小
   */
  get size(): number {
    return this.cache.size
  }

  /**
   * 获取缓存统计信息
   */
  getStats(): CacheStats {
    const total = this.hits + this.misses
    return {
      size: this.size,
      maxSize: this.maxSize,
      utilization: this.size / this.maxSize,
      hits: this.hits,
      misses: this.misses,
      hitRate: total > 0 ? this.hits / total : 0
    }
  }

  /**
   * 清理过期的缓存条目
   * @returns 清理的条目数
   */
  cleanExpired(): number {
    const now = Date.now()
    let cleaned = 0

    for (const [key, entry] of this.cache.entries()) {
      if (now - entry.timestamp > this.ttl) {
        this.cache.delete(key)
        cleaned++
      }
    }

    return cleaned
  }

  /**
   * 获取所有缓存键
   */
  keys(): string[] {
    return Array.from(this.cache.keys())
  }

  /**
   * 获取所有缓存值
   */
  values(): RecognitionCacheEntry[] {
    return Array.from(this.cache.values())
  }

  /**
   * 重置统计计数器
   */
  resetStats(): void {
    this.hits = 0
    this.misses = 0
  }
}

/**
 * 创建 LRU 缓存实例的便利函数
 * @param config 缓存配置
 * @returns RecognitionLRUCache 实例
 */
export function createRecognitionCache(config?: LRUCacheConfig): RecognitionLRUCache {
  return new RecognitionLRUCache(config)
}

// 默认导出
export default RecognitionLRUCache
