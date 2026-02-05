/**
 * 性能监控工具类
 * 追踪语音识别准确率、延迟、缓存等功能
 */

export interface RecognitionMetrics {
  accuracy: number
  latency: number
  confidence: number
  timestamp: number
}

export interface PerformanceStats {
  totalRecognitions: number
  successfulRecognitions: number
  failedRecognitions: number
  successRate: number
  averageLatency: number
  averageAccuracy: number
  averageConfidence: number
}

export interface LatencyBreakdown {
  audioCapture: number
  processing: number
  recognition: number
  postProcessing: number
  total: number
}

/**
 * 识别准确率追踪器
 */
export class AccuracyTracker {
  private metrics: RecognitionMetrics[] = []
  private maxMetricsCount = 1000 // 限制保存数量，避免内存泄漏

  /**
   * 记录识别结果
   * @param actual 实际文本
   * @param recognized 识别文本
   * @param confidence 置信度
   * @param latency 延迟时间
   */
  recordRecognition(
    actual: string,
    recognized: string,
    confidence: number,
    latency: number
  ): void {
    const accuracy = this.calculateAccuracy(actual, recognized)

    const metric: RecognitionMetrics = {
      accuracy,
      latency,
      confidence,
      timestamp: Date.now()
    }

    this.metrics.push(metric)

    // 限制保存数量
    if (this.metrics.length > this.maxMetricsCount) {
      this.metrics.shift()
    }
  }

  /**
   * 计算文本准确率
   * @param actual 实际文本
   * @param recognized 识别文本
   * @returns 准确率 (0-1)
   */
  private calculateAccuracy(actual: string, recognized: string): number {
    // 简单的准确率计算：匹配字符数 / 总字符数
    const actualWords = actual.toLowerCase().trim().split(/\s+/)
    const recognizedWords = recognized.toLowerCase().trim().split(/\s+/)

    let matches = 0
    const maxLength = Math.max(actualWords.length, recognizedWords.length)

    for (let i = 0; i < maxLength; i++) {
      if (actualWords[i] === recognizedWords[i]) {
        matches++
      }
    }

    return maxLength > 0 ? matches / maxLength : 0
  }

  /**
   * 获取平均准确率
   * @param count 最近N次记录
   * @returns 平均准确率
   */
  getAverageAccuracy(count: number = 10): number {
    if (this.metrics.length === 0) return 0

    const recentMetrics = this.metrics.slice(-count)
    const sum = recentMetrics.reduce((acc, metric) => acc + metric.accuracy, 0)
    return sum / recentMetrics.length
  }

  /**
   * 获取平均置信度
   * @param count 最近N次记录
   * @returns 平均置信度
   */
  getAverageConfidence(count: number = 10): number {
    if (this.metrics.length === 0) return 0

    const recentMetrics = this.metrics.slice(-count)
    const sum = recentMetrics.reduce((acc, metric) => acc + metric.confidence, 0)
    return sum / recentMetrics.length
  }

  /**
   * 获取详细统计
   * @returns 性能统计信息
   */
  getStatistics(count: number = 10): PerformanceStats {
    if (this.metrics.length === 0) {
      return {
        totalRecognitions: 0,
        successfulRecognitions: 0,
        failedRecognitions: 0,
        successRate: 0,
        averageLatency: 0,
        averageAccuracy: 0,
        averageConfidence: 0
      }
    }

    const recentMetrics = this.metrics.slice(-count)

    const total = recentMetrics.length
    const successful = recentMetrics.filter(m => m.accuracy > 0.7).length
    const failed = total - successful

    const avgLatency = recentMetrics.reduce((acc, m) => acc + m.latency, 0) / total
    const avgAccuracy = recentMetrics.reduce((acc, m) => acc + m.accuracy, 0) / total
    const avgConfidence = recentMetrics.reduce((acc, m) => acc + m.confidence, 0) / total

    return {
      totalRecognitions: total,
      successfulRecognitions: successful,
      failedRecognitions: failed,
      successRate: successful / total,
      averageLatency: avgLatency,
      averageAccuracy: avgAccuracy,
      averageConfidence: avgConfidence
    }
  }

  /**
   * 重置统计数据
   */
  reset(): void {
    this.metrics = []
  }
}

/**
 * 延迟监控器
 */
export class LatencyMonitor {
  private timingPoints: Map<string, number> = new Map()
  private breakdowns: LatencyBreakdown[] = []

  /**
   * 记录时间点
   * @param pointName 时间点名称
   */
  startTiming(pointName: string): void {
    this.timingPoints.set(pointName, performance.now())
  }

  /**
   * 结束时间点记录
   * @param pointName 时间点名称
   * @returns 持续时间(ms)
   */
  endTiming(pointName: string): number {
    const startTime = this.timingPoints.get(pointName)
    if (!startTime) {
      console.warn(`未找到时间点: ${pointName}`)
      return 0
    }

    const duration = performance.now() - startTime
    this.timingPoints.delete(pointName)
    return duration
  }

  /**
   * 记录完整延迟分解
   * @param breakdown 延迟分解数据
   */
  recordBreakdown(breakdown: LatencyBreakdown): void {
    this.breakdowns.push(breakdown)

    // 限制保存数量
    if (this.breakdowns.length > 100) {
      this.breakdowns.shift()
    }
  }

  /**
   * 获取平均延迟
   * @returns 平均延迟分解
   */
  getAverageBreakdown(): LatencyBreakdown | null {
    if (this.breakdowns.length === 0) return null

    const sum = this.breakdowns.reduce(
      (acc, breakdown) => ({
        audioCapture: acc.audioCapture + breakdown.audioCapture,
        processing: acc.processing + breakdown.processing,
        recognition: acc.recognition + breakdown.recognition,
        postProcessing: acc.postProcessing + breakdown.postProcessing,
        total: acc.total + breakdown.total
      }),
      { audioCapture: 0, processing: 0, recognition: 0, postProcessing: 0, total: 0 }
    )

    const count = this.breakdowns.length
    return {
      audioCapture: sum.audioCapture / count,
      processing: sum.processing / count,
      recognition: sum.recognition / count,
      postProcessing: sum.postProcessing / count,
      total: sum.total / count
    }
  }

  /**
   * 获取最慢的环节
   * @returns 最慢环节名称
   */
  getSlowestPhase(): string | null {
    const avg = this.getAverageBreakdown()
    if (!avg) return null

    const phases = [
      { name: '音频捕获', value: avg.audioCapture },
      { name: '音频处理', value: avg.processing },
      { name: '语音识别', value: avg.recognition },
      { name: '结果后处理', value: avg.postProcessing }
    ]

    phases.sort((a, b) => b.value - a.value)
    return phases[0].name
  }

  /**
   * 重置统计数据
   */
  reset(): void {
    this.timingPoints.clear()
    this.breakdowns = []
  }
}

/**
 * LRU缓存实现
 */
export class LRUCache<K, V> {
  private cache: Map<K, { value: V; timestamp: number }>
  private maxSize: number

  constructor(maxSize: number = 1000) {
    this.cache = new Map()
    this.maxSize = maxSize
  }

  /**
   * 获取缓存值
   * @param key 键
   * @returns 值或undefined
   */
  get(key: K): V | undefined {
    const item = this.cache.get(key)
    if (!item) return undefined

    // 更新访问时间
    this.cache.delete(key)
    this.cache.set(key, { value: item.value, timestamp: Date.now() })
    return item.value
  }

  /**
   * 设置缓存值
   * @param key 键
   * @param value 值
   */
  set(key: K, value: V): void {
    // 如果已存在，更新值
    if (this.cache.has(key)) {
      this.cache.delete(key)
    }

    this.cache.set(key, { value, timestamp: Date.now() })

    // 如果超过最大大小，删除最旧的项
    if (this.cache.size > this.maxSize) {
      const firstKey = this.cache.keys().next().value
      this.cache.delete(firstKey)
    }
  }

  /**
   * 检查是否包含键
   * @param key 键
   * @returns 是否包含
   */
  has(key: K): boolean {
    return this.cache.has(key)
  }

  /**
   * 删除缓存项
   * @param key 键
   * @returns 是否删除成功
   */
  delete(key: K): boolean {
    return this.cache.delete(key)
  }

  /**
   * 清空缓存
   */
  clear(): void {
    this.cache.clear()
  }

  /**
   * 获取缓存大小
   */
  get size(): number {
    return this.cache.size
  }

  /**
   * 获取所有键
   */
  keys(): K[] {
    return Array.from(this.cache.keys())
  }
}

/**
 * 音频哈希生成器
 */
export class AudioHasher {
  /**
   * 生成音频数据哈希
   * @param audioData 音频数据
   * @returns 哈希字符串
   */
  static generateHash(audioData: Float32Array): string {
    // 简单的哈希算法：将音频数据转换为字符串并生成哈希
    const sampleRate = 16000 // 假设采样率16kHz
    const duration = audioData.length / sampleRate

    // 计算关键特征
    let sum = 0
    let sumSquares = 0
    let zeroCrossings = 0

    for (let i = 0; i < audioData.length; i++) {
      const sample = audioData[i]
      sum += sample
      sumSquares += sample * sample

      // 计算过零率
      if (i > 0 && (audioData[i - 1] >= 0) !== (sample >= 0)) {
        zeroCrossings++
      }
    }

    const mean = sum / audioData.length
    const variance = sumSquares / audioData.length - mean * mean
    const rms = Math.sqrt(variance)
    const avgZeroCrossingRate = zeroCrossings / audioData.length

    // 生成特征向量
    const features = [
      Math.round(duration * 100) / 100,
      Math.round(mean * 10000) / 10000,
      Math.round(rms * 10000) / 10000,
      Math.round(avgZeroCrossingRate * 10000) / 10000
    ]

    // 简单的哈希生成
    return features.join('-')
  }

  /**
   * 生成音频文件哈希
   * @param audioBlob 音频文件
   * @returns 哈希字符串
   */
  static async generateHashFromBlob(audioBlob: Blob): Promise<string> {
    const arrayBuffer = await audioBlob.arrayBuffer()
    const uint8Array = new Uint8Array(arrayBuffer)

    // 简化版本：使用文件大小和部分内容生成哈希
    const hashArray = new Array(16)
    for (let i = 0; i < 16; i++) {
      const index = Math.floor((i * uint8Array.length) / 16)
      hashArray[i] = uint8Array[index] || 0
    }

    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
  }
}

/**
 * 结果缓存管理器
 */
export class ResultCache {
  private cache: LRUCache<string, any>

  constructor(maxSize: number = 1000) {
    this.cache = new LRUCache(maxSize)
  }

  /**
   * 获取缓存结果
   * @param audioHash 音频哈希
   * @returns 缓存结果或undefined
   */
  get(audioHash: string): any {
    return this.cache.get(audioHash)
  }

  /**
   * 设置缓存结果
   * @param audioHash 音频哈希
   * @param result 识别结果
   */
  set(audioHash: string, result: any): void {
    this.cache.set(audioHash, result)
  }

  /**
   * 检查是否有缓存
   * @param audioHash 音频哈希
   * @returns 是否有缓存
   */
  has(audioHash: string): boolean {
    return this.cache.has(audioHash)
  }

  /**
   * 删除缓存
   * @param audioHash 音频哈希
   * @returns 是否删除成功
   */
  delete(audioHash: string): boolean {
    return this.cache.delete(audioHash)
  }

  /**
   * 清空缓存
   */
  clear(): void {
    this.cache.clear()
  }

  /**
   * 获取缓存统计
   * @returns 缓存统计信息
   */
  getStats(): { size: number; maxSize: number } {
    return {
      size: this.cache.size,
      maxSize: 1000
    }
  }
}

/**
 * 性能监控主类
 */
export class PerformanceMonitor {
  private accuracyTracker: AccuracyTracker
  private latencyMonitor: LatencyMonitor
  private resultCache: ResultCache

  constructor() {
    this.accuracyTracker = new AccuracyTracker()
    this.latencyMonitor = new LatencyMonitor()
    this.resultCache = new ResultCache(1000)
  }

  /**
   * 记录识别结果
   * @param actual 实际文本
   * @param recognized 识别文本
   * @param confidence 置信度
   * @param latency 延迟
   */
  recordRecognition(
    actual: string,
    recognized: string,
    confidence: number,
    latency: number
  ): void {
    this.accuracyTracker.recordRecognition(actual, recognized, confidence, latency)
  }

  /**
   * 记录延迟分解
   * @param breakdown 延迟分解
   */
  recordLatencyBreakdown(breakdown: LatencyBreakdown): void {
    this.latencyMonitor.recordBreakdown(breakdown)
  }

  /**
   * 开始计时
   * @param pointName 时间点名称
   */
  startTiming(pointName: string): void {
    this.latencyMonitor.startTiming(pointName)
  }

  /**
   * 结束计时
   * @param pointName 时间点名称
   * @returns 持续时间
   */
  endTiming(pointName: string): number {
    return this.latencyMonitor.endTiming(pointName)
  }

  /**
   * 检查缓存
   * @param audioHash 音频哈希
   * @returns 缓存结果
   */
  checkCache(audioHash: string): any {
    return this.resultCache.get(audioHash)
  }

  /**
   * 设置缓存
   * @param audioHash 音频哈希
   * @param result 识别结果
   */
  setCache(audioHash: string, result: any): void {
    this.resultCache.set(audioHash, result)
  }

  /**
   * 获取准确率统计
   * @param count 最近N次
   * @returns 准确率统计
   */
  getAccuracyStats(count: number = 10): PerformanceStats {
    return this.accuracyTracker.getStatistics(count)
  }

  /**
   * 获取延迟统计
   * @returns 延迟统计
   */
  getLatencyStats(): LatencyBreakdown | null {
    return this.latencyMonitor.getAverageBreakdown()
  }

  /**
   * 获取最慢环节
   * @returns 最慢环节
   */
  getSlowestPhase(): string | null {
    return this.latencyMonitor.getSlowestPhase()
  }

  /**
   * 获取缓存统计
   * @returns 缓存统计
   */
  getCacheStats(): { size: number; maxSize: number } {
    return this.resultCache.getStats()
  }

  /**
   * 获取完整性能报告
   * @returns 性能报告
   */
  getPerformanceReport(): {
    accuracy: PerformanceStats
    latency: LatencyBreakdown | null
    cache: { size: number; maxSize: number }
    slowestPhase: string | null
  } {
    return {
      accuracy: this.accuracyTracker.getStatistics(10),
      latency: this.latencyMonitor.getAverageBreakdown(),
      cache: this.resultCache.getStats(),
      slowestPhase: this.latencyMonitor.getSlowestPhase()
    }
  }

  /**
   * 重置所有统计数据
   */
  reset(): void {
    this.accuracyTracker.reset()
    this.latencyMonitor.reset()
    this.resultCache.clear()
  }
}

/**
 * 便利函数
 */
export const performanceMonitor = {
  create: () => new PerformanceMonitor(),
  AccuracyTracker,
  LatencyMonitor,
  ResultCache,
  AudioHasher,
  LRUCache
}

export default PerformanceMonitor