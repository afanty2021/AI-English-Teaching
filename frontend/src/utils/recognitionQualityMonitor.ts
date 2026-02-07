/**
 * 识别准确率监控工具类
 * 用于追踪语音识别的准确率、置信度、延迟和错误率
 */

/**
 * 质量指标接口
 */
export interface QualityMetrics {
  accuracy: number           // 准确率 (0-1)
  confidence: number         // 平均置信度
  latency: number            // 平均延迟 (ms)
  errorRate: number         // 错误率 (0-1)
  sampleCount: number       // 样本数量
}

/**
 * 识别结果接口
 */
export interface RecognitionResult {
  confidence?: number
  latency?: number
}

/**
 * 识别准确率监控器
 *
 * 用于追踪和计算语音识别的各项质量指标：
 * - 准确率：基于 Levenshtein 距离计算
 * - 置信度：识别结果的平均置信度
 * - 延迟：识别的平均响应时间
 * - 错误率：识别失败的比例
 */
export class RecognitionQualityMonitor {
  private metrics: QualityMetrics = {
    accuracy: 0,
    confidence: 0,
    latency: 0,
    errorRate: 0,
    sampleCount: 0
  }

  /**
   * 记录识别结果
   * @param result 识别结果，包含置信度和延迟
   */
  recordResult(result: RecognitionResult): void {
    const count = this.metrics.sampleCount

    if (result.confidence !== undefined) {
      this.metrics.confidence = this.updateAverage(
        this.metrics.confidence,
        result.confidence,
        count
      )
    }

    if (result.latency !== undefined) {
      this.metrics.latency = this.updateAverage(
        this.metrics.latency,
        result.latency,
        count
      )
    }

    this.metrics.sampleCount++
  }

  /**
   * 记录识别错误
   */
  recordError(): void {
    const count = this.metrics.sampleCount
    this.metrics.errorRate = this.updateAverage(
      this.metrics.errorRate,
      1,  // 错误记为 1
      count
    )
    this.metrics.sampleCount++
  }

  /**
   * 记录准确率
   * 通过比较用户修正的文本和原始识别结果来计算准确率
   * @param userCorrection 用户修正后的文本
   * @param originalTranscript 原始识别结果
   */
  recordAccuracy(userCorrection: string, originalTranscript: string): void {
    const distance = this.calculateLevenshteinDistance(userCorrection, originalTranscript)
    const maxLen = Math.max(userCorrection.length, originalTranscript.length)
    const accuracy = maxLen > 0 ? 1 - (distance / maxLen) : 0

    const count = this.metrics.sampleCount
    this.metrics.accuracy = this.updateAverage(
      this.metrics.accuracy,
      accuracy,
      count
    )
  }

  /**
   * 更新平均值
   * 使用递增平均算法，避免存储所有历史数据
   * @param currentAvg 当前平均值
   * @param newValue 新值
   * @param count 当前样本数
   * @returns 更新后的平均值
   */
  private updateAverage(currentAvg: number, newValue: number, count: number): number {
    if (count === 0) return newValue
    return ((currentAvg * count) + newValue) / (count + 1)
  }

  /**
   * 计算 Levenshtein 距离
   * Levenshtein 距离是衡量两个字符串相似度的标准算法
   * 表示将一个字符串转换为另一个字符串所需的最少编辑操作数
   *
   * 编辑操作包括：
   * - 插入一个字符
   * - 删除一个字符
   * - 替换一个字符
   *
   * @param str1 第一个字符串
   * @param str2 第二个字符串
   * @returns Levenshtein 距离
   */
  private calculateLevenshteinDistance(str1: string, str2: string): number {
    const len1 = str1.length
    const len2 = str2.length

    // 创建动态规划矩阵
    // matrix[i][j] 表示 str1[0..i-1] 和 str2[0..j-1] 的编辑距离
    const matrix: number[][] = []

    // 初始化第一行和第一列
    // 第一行：将空字符串转换为 str2[0..j-1] 需要插入 j 个字符
    // 第一列：将 str1[0..i-1] 转换为空字符串需要删除 i 个字符
    for (let i = 0; i <= len1; i++) {
      matrix[i] = [i]
    }
    for (let j = 0; j <= len2; j++) {
      const row = matrix[0]
      if (row) row[j] = j
    }

    // 填充矩阵
    for (let i = 1; i <= len1; i++) {
      for (let j = 1; j <= len2; j++) {
        // 如果当前字符相同，编辑成本为 0，否则为 1
        const cost = str1[i - 1] === str2[j - 1] ? 0 : 1

        const prevRow = matrix[i - 1]
        const currentRow = matrix[i]

        // 确保所有行都存在
        if (!prevRow || !currentRow) continue

        // 选择三种操作中成本最小的：
        // 1. 从上方单元格+1（删除操作）
        // 2. 从左方单元格+1（插入操作）
        // 3. 从对角线单元格+cost（替换操作，相同字符则 cost=0）
        const deleteCost = prevRow[j] ?? 0
        const insertCost = currentRow[j - 1] ?? 0
        const replaceCost = prevRow[j - 1] ?? 0

        currentRow[j] = Math.min(
          deleteCost + 1,        // 删除
          insertCost + 1,        // 插入
          replaceCost + cost     // 替换或匹配
        )
      }
    }

    // 返回最终结果：右下角的单元格值即为编辑距离
    const finalRow = matrix[len1]
    return finalRow?.[len2] ?? 0
  }

  /**
   * 获取当前质量指标
   * @returns 质量指标的副本
   */
  getMetrics(): QualityMetrics {
    return { ...this.metrics }
  }

  /**
   * 重置所有指标
   */
  reset(): void {
    this.metrics = {
      accuracy: 0,
      confidence: 0,
      latency: 0,
      errorRate: 0,
      sampleCount: 0
    }
  }

  /**
   * 获取格式化的质量报告
   * @returns 格式化的质量报告字符串
   */
  getFormattedReport(): string {
    const m = this.metrics
    if (m.sampleCount === 0) {
      return '暂无数据'
    }

    return `
识别质量报告
============
样本数量: ${m.sampleCount}
准确率: ${((m.accuracy ?? 0) * 100).toFixed(2)}%
平均置信度: ${((m.confidence ?? 0) * 100).toFixed(2)}%
平均延迟: ${(m.latency ?? 0).toFixed(2)}ms
错误率: ${((m.errorRate ?? 0) * 100).toFixed(2)}%
    `.trim()
  }
}

/**
 * 创建识别质量监控器实例
 * @returns RecognitionQualityMonitor 实例
 */
export function createRecognitionQualityMonitor(): RecognitionQualityMonitor {
  return new RecognitionQualityMonitor()
}

/**
 * 默认导出
 */
export default RecognitionQualityMonitor
