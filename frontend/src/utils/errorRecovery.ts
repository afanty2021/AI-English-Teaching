/**
 * 错误恢复工具模块
 * 提供自动重试、状态恢复等功能
 */

/**
 * 重试配置
 */
export interface RetryConfig {
  maxAttempts?: number
  initialDelay?: number
  maxDelay?: number
  backoffMultiplier?: number
  retryableErrors?: Array<string | RegExp>
}

/**
 * 重试结果
 */
export interface RetryResult<T> {
  success: boolean
  data?: T
  error?: Error
  attempts: number
}

/**
 * 默认重试配置
 */
const DEFAULT_RETRY_CONFIG: Required<RetryConfig> = {
  maxAttempts: 3,
  initialDelay: 1000,
  maxDelay: 10000,
  backoffMultiplier: 2,
  retryableErrors: [
    'network',
    'timeout',
    'ECONNREFUSED',
    'ETIMEDOUT',
    /5\d\d/ // 5xx 服务器错误
  ]
}

/**
 * 检查错误是否可重试
 */
function isRetryableError(
  error: Error,
  retryableErrors: Array<string | RegExp>
): boolean {
  const message = error.message.toLowerCase()

  return retryableErrors.some(pattern => {
    if (pattern instanceof RegExp) {
      return pattern.test(error.message)
    }
    return message.includes(pattern.toLowerCase())
  })
}

/**
 * 计算重试延迟（指数退避）
 */
function calculateRetryDelay(
  attempt: number,
  initialDelay: number,
  maxDelay: number,
  backoffMultiplier: number
): number {
  const delay = initialDelay * Math.pow(backoffMultiplier, attempt)
  return Math.min(delay, maxDelay)
}

/**
 * 带重试的异步函数执行
 */
export async function retryAsync<T>(
  fn: () => Promise<T>,
  config: RetryConfig = {}
): Promise<RetryResult<T>> {
  const finalConfig = { ...DEFAULT_RETRY_CONFIG, ...config }
  let lastError: Error | undefined

  for (let attempt = 0; attempt < finalConfig.maxAttempts; attempt++) {
    try {
      const data = await fn()
      return {
        success: true,
        data,
        attempts: attempt + 1
      }
    } catch (error) {
      lastError = error as Error

      // 检查是否可重试
      if (!isRetryableError(lastError, finalConfig.retryableErrors)) {
        return {
          success: false,
          error: lastError,
          attempts: attempt + 1
        }
      }

      // 如果不是最后一次尝试，等待后重试
      if (attempt < finalConfig.maxAttempts - 1) {
        const delay = calculateRetryDelay(
          attempt,
          finalConfig.initialDelay,
          finalConfig.maxDelay,
          finalConfig.backoffMultiplier
        )
        await new Promise(resolve => setTimeout(resolve, delay))
      }
    }
  }

  return {
    success: false,
    error: lastError,
    attempts: finalConfig.maxAttempts
  }
}

/**
 * 对话状态恢复器
 */
export class ConversationRecovery {
  private storageKey = 'conversation_recovery'
  private saveInterval: number | null = null
  private readonly SAVE_INTERVAL_MS = 5000 // 5秒自动保存

  /**
   * 保存对话状态
   */
  saveConversationState(conversationId: string, state: {
    messages: any[]
    userInput: string
    timestamp: number
  }): void {
    try {
      const data = this.loadRecoveryData()
      data[conversationId] = {
        ...state,
        savedAt: Date.now()
      }
      localStorage.setItem(this.storageKey, JSON.stringify(data))
    } catch (error) {
      console.error('Failed to save conversation state:', error)
    }
  }

  /**
   * 加载对话状态
   */
  loadConversationState(conversationId: string): any | null {
    try {
      const data = this.loadRecoveryData()
      const state = data[conversationId]

      // 检查状态是否过期（30分钟）
      if (state && Date.now() - state.savedAt < 30 * 60 * 1000) {
        return state
      }

      // 删除过期状态
      if (state) {
        delete data[conversationId]
        this.saveRecoveryData(data)
      }

      return null
    } catch (error) {
      console.error('Failed to load conversation state:', error)
      return null
    }
  }

  /**
   * 清除对话状态
   */
  clearConversationState(conversationId: string): void {
    try {
      const data = this.loadRecoveryData()
      delete data[conversationId]
      this.saveRecoveryData(data)
    } catch (error) {
      console.error('Failed to clear conversation state:', error)
    }
  }

  /**
   * 获取所有可恢复的对话
   */
  getRecoverableConversations(): Array<{
    conversationId: string
    timestamp: number
    messageCount: number
  }> {
    try {
      const data = this.loadRecoveryData()
      const now = Date.now()

      return Object.entries(data)
        .filter(([_, state]: any[]) => now - state.savedAt < 30 * 60 * 1000)
        .map(([conversationId, state]: any[]) => ({
          conversationId,
          timestamp: state.timestamp,
          messageCount: state.messages?.length || 0
        }))
    } catch (error) {
      console.error('Failed to get recoverable conversations:', error)
      return []
    }
  }

  /**
   * 启动自动保存
   */
  startAutoSave(conversationId: string, getState: () => any): void {
    this.stopAutoSave()

    this.saveInterval = window.setInterval(() => {
      this.saveConversationState(conversationId, getState())
    }, this.SAVE_INTERVAL_MS)
  }

  /**
   * 停止自动保存
   */
  stopAutoSave(): void {
    if (this.saveInterval) {
      clearInterval(this.saveInterval)
      this.saveInterval = null
    }
  }

  /**
   * 加载恢复数据
   */
  private loadRecoveryData(): Record<string, any> {
    try {
      const data = localStorage.getItem(this.storageKey)
      return data ? JSON.parse(data) : {}
    } catch {
      return {}
    }
  }

  /**
   * 保存恢复数据
   */
  private saveRecoveryData(data: Record<string, any>): void {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(data))
    } catch (error) {
      console.error('Failed to save recovery data:', error)
    }
  }
}

/**
 * 创建对话恢复器实例
 */
export function createConversationRecovery(): ConversationRecovery {
  return new ConversationRecovery()
}

/**
 * 网络状态监听器
 */
export class NetworkMonitor {
  private isOnline = navigator.onLine
  private listeners: Array<(online: boolean) => void> = []

  constructor() {
    if (typeof window !== 'undefined') {
      window.addEventListener('online', () => this.handleStatusChange(true))
      window.addEventListener('offline', () => this.handleStatusChange(false))
    }
  }

  /**
   * 处理网络状态变化
   */
  private handleStatusChange(online: boolean): void {
    this.isOnline = online
    this.listeners.forEach(listener => {
      try {
        listener(online)
      } catch (error) {
        // 隔离监听器错误，不影响其他监听器
        console.error('Error in network status listener:', error)
      }
    })
  }

  /**
   * 监听网络状态
   */
  onStatusChange(callback: (online: boolean) => void): () => void {
    this.listeners.push(callback)

    // 返回取消监听函数
    return () => {
      const index = this.listeners.indexOf(callback)
      if (index !== -1) {
        this.listeners.splice(index, 1)
      }
    }
  }

  /**
   * 获取当前网络状态
   */
  getStatus(): boolean {
    return this.isOnline
  }
}

/**
 * 创建网络状态监听器
 */
export function createNetworkMonitor(): NetworkMonitor {
  return new NetworkMonitor()
}
