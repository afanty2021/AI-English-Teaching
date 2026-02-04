/**
 * 对话服务 API 客户端
 */
import { request } from '@/utils/request'
import type {
  Conversation,
  ConversationMessage,
  ConversationScenario,
  CreateConversationRequest,
  SendMessageRequest,
  ConversationScores
} from '@/types/conversation'

const BASE_URL = '/api/v1/conversations'

/**
 * 创建新的对话会话
 */
export async function createConversation(data: CreateConversationRequest): Promise<Conversation> {
  return request({
    url: BASE_URL,
    method: 'POST',
    data
  })
}

/**
 * 获取对话详情
 */
export async function getConversation(conversationId: string): Promise<Conversation> {
  return request({
    url: `${BASE_URL}/${conversationId}`,
    method: 'GET'
  })
}

/**
 * 发送消息
 */
export async function sendMessage(
  conversationId: string,
  data: SendMessageRequest
): Promise<{ conversation: Conversation; message: ConversationMessage }> {
  return request({
    url: `${BASE_URL}/${conversationId}/message`,
    method: 'POST',
    data
  })
}

/**
 * 完成对话并获取评分
 */
export async function completeConversation(
  conversationId: string
): Promise<{ conversation: Conversation; scores: ConversationScores }> {
  return request({
    url: `${BASE_URL}/${conversationId}/complete`,
    method: 'POST'
  })
}

/**
 * 获取可用的对话场景列表
 */
export async function getScenarios(): Promise<{ scenarios: ConversationScenario[] }> {
  return request({
    url: `${BASE_URL}/scenarios/available`,
    method: 'GET'
  })
}

/**
 * 获取学生的对话列表
 */
export async function getStudentConversations(): Promise<{ conversations: Conversation[] }> {
  return request({
    url: BASE_URL,
    method: 'GET'
  })
}

/**
 * 流式发送消息（SSE）
 *
 * @param conversationId 对话ID
 * @param content 用户消息内容
 * @param callbacks 回调函数集合
 * @returns 清理函数，调用可关闭连接
 */
export function streamMessage(
  conversationId: string,
  content: string,
  callbacks: {
    onToken?: (token: string, index: number) => void
    onComplete?: (fullMessage: string, tokenCount: number) => void
    onError?: (error: Error) => void
    onStart?: () => void
    onEnd?: () => void
  }
): () => void {
  const { onToken, onComplete, onError, onStart, onEnd } = callbacks

  // 构建 SSE URL
  const url = `${BASE_URL}/${conversationId}/message/stream?message=${encodeURIComponent(content)}`

  // 创建 EventSource
  const eventSource = new EventSource(url)

  // 连接打开
  eventSource.onopen = () => {
    onStart?.()
  }

  // 接收消息
  eventSource.onmessage = (event) => {
    const data = event.data

    // 检查结束标记
    if (data === '[DONE]') {
      eventSource.close()
      onEnd?.()
      return
    }

    try {
      const parsed = JSON.parse(data)

      switch (parsed.type) {
        case 'token':
          // 单个 token
          onToken?.(parsed.content, parsed.index)
          break

        case 'complete':
          // 完整消息
          eventSource.close()
          onComplete?.(parsed.full_message, parsed.total_tokens)
          onEnd?.()
          break

        case 'error':
          // 错误
          eventSource.close()
          onError?.(new Error(parsed.error || 'Unknown error'))
          onEnd?.()
          break
      }
    } catch (e) {
      // JSON 解析失败，可能是其他格式的数据
      console.error('Failed to parse SSE data:', e)
    }
  }

  // 错误处理
  eventSource.onerror = (_error: Event) => {
    eventSource.close()
    onError?.(new Error('Stream connection error'))
    onEnd?.()
  }

  // 返回清理函数
  return () => {
    eventSource.close()
  }
}
