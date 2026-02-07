/**
 * 导出任务 WebSocket 连接工具
 * 用于监听导出任务的实时进度更新
 */
import { ElNotification } from 'element-plus'
import type { ExportProgressEvent } from '@/types/lessonExport'

// 浏览器全局变量类型声明
declare const window: Window
declare const setInterval: (handler: TimerHandler, timeout?: number) => number
declare const clearInterval: (id: number) => void
declare const setTimeout: (handler: TimerHandler, timeout?: number) => number
declare const clearTimeout: (id: number) => void

/**
 * WebSocket 连接状态
 */
export enum WebSocketState {
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  ERROR = 'error'
}

/**
 * 导出 WebSocket 连接类
 */
class ExportWebSocket {
  private ws: WebSocket | null = null
  private taskId: string = ''
  private url: string = ''
  private reconnectAttempts: number = 0
  private maxReconnectAttempts: number = 5
  private reconnectDelay: number = 2000
  private reconnectTimer: number | null = null
  private heartbeatTimer: number | null = null
  private heartbeatInterval: number = 30000

  // 回调函数
  private onProgressCallback: ((event: ExportProgressEvent) => void) | null = null
  private onCompleteCallback: ((event: ExportProgressEvent) => void) | null = null
  private onErrorCallback: ((event: ExportProgressEvent) => void) | null = null
  private onStateChangeCallback: ((state: WebSocketState) => void) | null = null

  /**
   * 连接 WebSocket
   */
  connect(taskId: string, url?: string): Promise<void> {
    return new Promise((resolve, reject) => {
      this.taskId = taskId

      // 构建 WebSocket URL
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsHost = url || window.location.host
      this.url = `${wsProtocol}//${wsHost}/api/v1/ws/export/${taskId}`

      try {
        this.ws = new WebSocket(this.url)
        this.notifyStateChange(WebSocketState.CONNECTING)

        this.ws.onopen = () => {
          console.log('[ExportWebSocket] 已连接:', this.url)
          this.reconnectAttempts = 0
          this.startHeartbeat()
          this.notifyStateChange(WebSocketState.CONNECTED)
          resolve()
        }

        this.ws.onmessage = (event) => {
          this.handleMessage(event.data)
        }

        this.ws.onerror = (error) => {
          console.error('[ExportWebSocket] 错误:', error)
          this.notifyStateChange(WebSocketState.ERROR)
          reject(error)
        }

        this.ws.onclose = (event) => {
          console.log('[ExportWebSocket] 已关闭:', event.code, event.reason)
          this.stopHeartbeat()

          // 如果非正常关闭且未达到最大重连次数，尝试重连
          if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect()
          } else {
            this.notifyStateChange(WebSocketState.DISCONNECTED)
          }
        }
      } catch (error) {
        console.error('[ExportWebSocket] 连接失败:', error)
        this.notifyStateChange(WebSocketState.ERROR)
        reject(error)
      }
    })
  }

  /**
   * 处理消息
   */
  private handleMessage(data: string): void {
    try {
      const event: ExportProgressEvent = JSON.parse(data)

      // 验证事件类型
      if (event.task_id !== this.taskId) {
        console.warn('[ExportWebSocket] 忽略不相关任务:', event.task_id)
        return
      }

      switch (event.type) {
        case 'progress':
          if (this.onProgressCallback) {
            this.onProgressCallback(event)
          }
          break

        case 'stage':
          if (this.onProgressCallback) {
            this.onProgressCallback(event)
          }
          break

        case 'completed':
          if (this.onCompleteCallback) {
            this.onCompleteCallback(event)
          }
          // 完成后关闭连接
          this.close()
          break

        case 'failed':
          if (this.onErrorCallback) {
            this.onErrorCallback(event)
          }
          // 失败后关闭连接
          this.close()
          break

        default:
          console.warn('[ExportWebSocket] 未知事件类型:', event.type)
      }
    } catch (error) {
      console.error('[ExportWebSocket] 消息解析失败:', error)
    }
  }

  /**
   * 安排重连
   */
  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      return
    }

    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)

    console.log(
      `[ExportWebSocket] 将在 ${delay}ms 后尝试第 ${this.reconnectAttempts} 次重连`
    )

    // 显示重连通知
    ElNotification({
      title: '连接中断',
      message: `正在尝试重连... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`,
      type: 'warning',
      duration: 3000
    })

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null
      this.connect(this.taskId).catch((error) => {
        console.error('[ExportWebSocket] 重连失败:', error)
      })
    }, delay)
  }

  /**
   * 开始心跳
   */
  private startHeartbeat(): void {
    this.stopHeartbeat()

    this.heartbeatTimer = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, this.heartbeatInterval)
  }

  /**
   * 停止心跳
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  /**
   * 通知状态变化
   */
  private notifyStateChange(state: WebSocketState): void {
    if (this.onStateChangeCallback) {
      this.onStateChangeCallback(state)
    }
  }

  /**
   * 监听进度更新
   */
  onProgress(callback: (event: ExportProgressEvent) => void): void {
    this.onProgressCallback = callback
  }

  /**
   * 监听完成事件
   */
  onComplete(callback: (event: ExportProgressEvent) => void): void {
    this.onCompleteCallback = callback
  }

  /**
   * 监听错误事件
   */
  onError(callback: (event: ExportProgressEvent) => void): void {
    this.onErrorCallback = callback
  }

  /**
   * 监听状态变化
   */
  onStateChange(callback: (state: WebSocketState) => void): void {
    this.onStateChangeCallback = callback
  }

  /**
   * 关闭连接
   */
  close(): void {
    // 清理重连定时器
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    // 停止心跳
    this.stopHeartbeat()

    // 关闭 WebSocket
    if (this.ws) {
      this.ws.close(1000, '客户端主动关闭')
      this.ws = null
    }

    this.notifyStateChange(WebSocketState.DISCONNECTED)
  }

  /**
   * 获取连接状态
   */
  getState(): WebSocketState {
    if (!this.ws) {
      return WebSocketState.DISCONNECTED
    }

    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return WebSocketState.CONNECTING
      case WebSocket.OPEN:
        return WebSocketState.CONNECTED
      case WebSocket.CLOSING:
      case WebSocket.CLOSED:
        return WebSocketState.DISCONNECTED
      default:
        return WebSocketState.ERROR
    }
  }

  /**
   * 是否已连接
   */
  isConnected(): boolean {
    return this.getState() === WebSocketState.CONNECTED
  }
}

/**
 * 创建导出 WebSocket 连接
 */
export function createExportWebSocket(taskId: string, url?: string): ExportWebSocket {
  const ws = new ExportWebSocket()
  ws.connect(taskId, url).catch((error) => {
    console.error('[ExportWebSocket] 初始化连接失败:', error)
  })
  return ws
}

/**
 * 连接导出 WebSocket（便捷方法）
 */
export async function connectExportWebSocket(
  taskId: string,
  callbacks: {
    onProgress?: (event: ExportProgressEvent) => void
    onComplete?: (event: ExportProgressEvent) => void
    onError?: (event: ExportProgressEvent) => void
    onStateChange?: (state: WebSocketState) => void
  },
  url?: string
): Promise<ExportWebSocket> {
  const ws = new ExportWebSocket()

  if (callbacks.onProgress) {
    ws.onProgress(callbacks.onProgress)
  }

  if (callbacks.onComplete) {
    ws.onComplete(callbacks.onComplete)
  }

  if (callbacks.onError) {
    ws.onError(callbacks.onError)
  }

  if (callbacks.onStateChange) {
    ws.onStateChange(callbacks.onStateChange)
  }

  await ws.connect(taskId, url)
  return ws
}

export default ExportWebSocket
