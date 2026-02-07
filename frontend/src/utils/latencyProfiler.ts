/**
 * 延迟分析器 - 用于分解语音识别延迟的工具
 *
 * 将语音识别的完整流程分解为多个阶段，帮助定位性能瓶颈：
 * - recording: 录音阶段（用户开始说话到录音结束）
 * - uploading: 上传阶段（音频数据上传到服务器）
 * - processing: 处理阶段（服务器处理音频）
 * - downloading: 下载阶段（接收识别结果）
 *
 * 使用示例：
 * ```typescript
 * const profiler = createLatencyProfiler()
 * profiler.start('recognition')
 * // ... 录音完成
 * profiler.end('recording')
 * profiler.start('uploading')
 * // ... 上传完成
 * profiler.end('uploading')
 * profiler.start('processing')
 * // ... 处理完成
 * profiler.end('processing')
 * profiler.start('downloading')
 * // ... 下载完成
 * profiler.end('downloading')
 *
 * const profile = profiler.getProfile()
 * console.log('总延迟:', profile.total)
 * console.log('录音延迟:', profile.recording)
 * ```
 */

/**
 * 延迟配置文件
 */
export interface LatencyProfile {
  /** 总延迟（完整识别流程的时间） */
  total: number
  /** 录音延迟（用户录音阶段） */
  recording: number
  /** 上传延迟（音频上传到服务器） */
  uploading: number
  /** 处理延迟（服务器音频处理） */
  processing: number
  /** 下载延迟（接收识别结果） */
  downloading: number
}

/**
 * 延迟阶段类型
 */
export type LatencyPhase = 'recording' | 'uploading' | 'processing' | 'downloading'

/**
 * 里程碑记录
 */
interface Milestone {
  /** 开始时间戳 */
  start: number
  /** 结束时间戳 */
  end?: number
}

/**
 * 延迟分析器类
 */
export class LatencyProfiler {
  /** 里程碑记录表 */
  private milestones = new Map<string, Milestone>()

  /** 开始记录某个操作的时间点
   * @param operation 操作名称（如 'recording', 'uploading' 等）
   */
  start(operation: LatencyPhase): void {
    const key = `${operation}_start`
    this.milestones.set(key, {
      start: performance.now()
    })
  }

  /** 结束记录某个操作
   * @param operation 操作名称
   * @returns 持续时间（毫秒）
   */
  end(operation: LatencyPhase): number {
    const startKey = `${operation}_start`
    const endKey = `${operation}_end`

    const milestone = this.milestones.get(startKey)
    if (!milestone) {
      console.warn(`[LatencyProfiler] No start time found for operation: ${operation}`)
      return 0
    }

    const endTime = performance.now()
    const duration = endTime - milestone.start

    // 更新里程碑记录
    this.milestones.set(endKey, {
      start: milestone.start,
      end: endTime
    })

    return duration
  }

  /** 获取某个操作的延迟时间
   * @param operation 操作名称
   * @returns 延迟时间（毫秒），如果未记录则返回 0
   */
  getLatency(operation: LatencyPhase): number {
    const startKey = `${operation}_start`
    const endKey = `${operation}_end`

    const startMilestone = this.milestones.get(startKey)
    const endMilestone = this.milestones.get(endKey)

    if (endMilestone?.end && startMilestone) {
      return endMilestone.end - startMilestone.start
    }

    return 0
  }

  /** 获取完整的延迟配置文件
   * @returns 延迟配置文件对象
   */
  getProfile(): LatencyProfile {
    return {
      total: this.getLatency('recording') +
             this.getLatency('uploading') +
             this.getLatency('processing') +
             this.getLatency('downloading'),
      recording: this.getLatency('recording'),
      uploading: this.getLatency('uploading'),
      processing: this.getLatency('processing'),
      downloading: this.getLatency('downloading')
    }
  }

  /** 检查某个操作是否已完成
   * @param operation 操作名称
   * @returns 是否已完成
   */
  isCompleted(operation: LatencyPhase): boolean {
    const endKey = `${operation}_end`
    return this.milestones.has(endKey)
  }

  /** 检查某个操作是否正在进行中
   * @param operation 操作名称
   * @returns 是否正在进行
   */
  isInProgress(operation: LatencyPhase): boolean {
    const startKey = `${operation}_start`
    const endKey = `${operation}_end`
    return this.milestones.has(startKey) && !this.milestones.has(endKey)
  }

  /** 获取当前正在进行的操作
   * @returns 当前操作名称，如果没有则返回 null
   */
  getCurrentOperation(): LatencyPhase | null {
    const operations: LatencyPhase[] = ['recording', 'uploading', 'processing', 'downloading']
    for (const op of operations) {
      if (this.isInProgress(op)) {
        return op
      }
    }
    return null
  }

  /** 清空所有记录 */
  clear(): void {
    this.milestones.clear()
  }

  /** 重置分析器（清空所有记录） */
  reset(): void {
    this.clear()
  }

  /** 获取记录的统计信息
   * @returns 统计信息
   */
  getStats(): {
    totalMilestones: number
    completedOperations: number
    inProgressOperations: number
  } {
    let completed = 0
    let inProgress = 0

    const operations: LatencyPhase[] = ['recording', 'uploading', 'processing', 'downloading']
    for (const op of operations) {
      if (this.isCompleted(op)) completed++
      else if (this.isInProgress(op)) inProgress++
    }

    return {
      totalMilestones: this.milestones.size,
      completedOperations: completed,
      inProgressOperations: inProgress
    }
  }

  /** 导出为 JSON 格式
   * @returns JSON 字符串
   */
  toJSON(): string {
    return JSON.stringify({
      profile: this.getProfile(),
      stats: this.getStats(),
      milestones: Array.from(this.milestones.entries()).map(([key, value]) => ({
        key,
        start: value.start,
        end: value.end
      }))
    })
  }
}

/**
 * 创建延迟分析器实例
 * @returns 延迟分析器实例
 */
export function createLatencyProfiler(): LatencyProfiler {
  return new LatencyProfiler()
}

/**
 * 默认导出
 */
export default LatencyProfiler
