/**
 * 错题本 API 客户端
 * 处理错题的增删改查、复习等操作
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器：添加 token
api.interceptors.request.use(
  (config: any) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error: any) => {
    return Promise.reject(error)
  }
)

// 响应拦截器：处理错误
api.interceptors.response.use(
  (response: any) => response.data,
  (error: any) => {
    if (error.response?.status === 401) {
      // 清除 token，跳转登录
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

/**
 * 错题类型枚举
 */
export enum MistakeType {
  GRAMMAR = 'grammar',
  VOCABULARY = 'vocabulary',
  READING = 'reading',
  LISTENING = 'listening',
  WRITING = 'writing',
  SPEAKING = 'speaking',
  PRONUNCIATION = 'pronunciation',
  COMPREHENSION = 'comprehension'
}

/**
 * 错题状态枚举
 */
export enum MistakeStatus {
  PENDING = 'pending',
  REVIEWING = 'reviewing',
  MASTERED = 'mastered',
  IGNORED = 'ignored'
}

/**
 * 错题类型定义
 */
export interface Mistake {
  id: string
  student_id: string
  practice_id?: string
  content_id?: string
  question: string
  wrong_answer: string
  correct_answer: string
  mistake_type: MistakeType
  status: MistakeStatus
  explanation?: string
  knowledge_points: string[]
  difficulty_level?: string
  topic?: string
  mistake_count: number
  review_count: number
  last_reviewed_at?: string
  first_mistaken_at?: string
  last_mistaken_at?: string
  ai_suggestion?: string
  ai_analysis?: Record<string, unknown>
  extra_metadata?: Record<string, unknown>
  mastery_level: number
  needs_review: boolean
  is_mastered: boolean
  created_at: string
  updated_at: string
}

/**
 * 创建错题请求
 */
export interface CreateMistakeRequest {
  question: string
  wrong_answer: string
  correct_answer: string
  mistake_type: MistakeType
  practice_id?: string
  content_id?: string
  explanation?: string
  knowledge_points?: string[]
  difficulty_level?: string
  topic?: string
  extra_metadata?: Record<string, unknown>
}

/**
 * 错题列表响应
 */
export interface MistakeListResponse {
  total: number
  limit: number
  offset: number
  mistakes: Mistake[]
}

/**
 * 错题统计数据
 */
export interface MistakeStatistics {
  student_id: string
  total_mistakes: number
  by_status: Record<string, number>
  by_type: Record<string, number>
  by_topic: Record<string, number>
  mastery_rate: number
  need_review_count: number
  recent_mistakes_count: number
  frequent_mistakes_count: number
}

/**
 * 复习计划
 */
export interface ReviewPlan {
  student_id: string
  urgent: Array<{ id: string; question: string; type: string }>
  today: Array<{ id: string; question: string; type: string }>
  week: Array<{ id: string; question: string; type: string }>
  knowledge_points: Array<[string, number]>
  total_pending: number
}

/**
 * 重做请求
 */
export interface RetryMistakeRequest {
  user_answer: string
  is_correct: boolean
}

/**
 * 重做响应
 */
export interface RetryMistakeResponse {
  mistake_id: string
  mastered: boolean
  review_count: number
  mistake_count: number
  status: MistakeStatus
  message: string
}

/**
 * 错题本 API
 */
export const mistakeApi = {
  /**
   * 创建错题记录
   */
  async createMistake(data: CreateMistakeRequest): Promise<Mistake> {
    return api.post('/mistakes/', data)
  },

  /**
   * 从练习记录中收集错题
   */
  async collectFromPractice(practiceId: string): Promise<{
    practice_id: string
    collected_count: number
    mistakes: Array<{
      id: string
      question: string
      mistake_type: string
      status: string
    }>
    message: string
  }> {
    return api.post(`/mistakes/collect/${practiceId}`)
  },

  /**
   * 获取错题列表
   */
  async getMyMistakes(params?: {
    status?: MistakeStatus
    mistake_type?: MistakeType
    topic?: string
    knowledge_point?: string
    needs_ai_analysis?: boolean
    limit?: number
    offset?: number
  }): Promise<MistakeListResponse> {
    return api.get('/mistakes/me', { params })
  },

  /**
   * 获取错题详情
   */
  async getMistake(mistakeId: string): Promise<Mistake> {
    return api.get(`/mistakes/${mistakeId}`)
  },

  /**
   * 更新错题状态
   */
  async updateMistakeStatus(
    mistakeId: string,
    status: MistakeStatus
  ): Promise<{ id: string; status: string; message: string }> {
    return api.put(`/mistakes/${mistakeId}/status`, { status })
  },

  /**
   * 重做错题
   */
  async retryMistake(
    mistakeId: string,
    data: RetryMistakeRequest
  ): Promise<RetryMistakeResponse> {
    return api.post(`/mistakes/${mistakeId}/retry`, data)
  },

  /**
   * 删除错题
   */
  async deleteMistake(mistakeId: string): Promise<void> {
    return api.delete(`/mistakes/${mistakeId}`)
  },

  /**
   * 获取错题统计数据
   */
  async getStatistics(): Promise<MistakeStatistics> {
    return api.get('/mistakes/me/statistics')
  },

  /**
   * 获取复习计划
   */
  async getReviewPlan(limit = 20): Promise<ReviewPlan> {
    return api.get('/mistakes/me/review-plan', { params: { limit } })
  },

  /**
   * 对单个错题进行AI分析
   */
  async analyzeMistake(mistakeId: string): Promise<{
    mistake_id: string
    analysis: {
      mistake_category: string
      severity: string
      explanation: string
      correct_approach: string
      knowledge_points: string[]
      recommendations: Array<{
        priority: number
        category: string
        title: string
        description: string
        resources?: string[]
        practice_exercises?: string[]
        estimated_time?: string
      }>
      review_plan: {
        review_frequency: string
        next_review_days: number[]
        mastery_criteria: string
        review_method: string
      }
      encouragement: string
    }
    message: string
  }> {
    return api.post(`/mistakes/${mistakeId}/analyze`)
  },

  /**
   * 批量AI分析错题
   */
  async batchAnalyzeMistakes(limit = 10): Promise<{
    analyzed_count: number
    summary: string
    common_patterns: string[]
    overall_recommendations: string[]
    priority_topics: string[]
    remaining_count: number
    message: string
  }> {
    return api.post('/mistakes/batch-analyze', null, { params: { limit } })
  },

  /**
   * 导出错题本
   */
  async exportMistakes(params: {
    format_type: 'markdown' | 'pdf' | 'word'
    status_filter?: string
    type_filter?: string
    topic_filter?: string
    knowledge_point_filter?: string
  }): Promise<void> {
    // 构建查询参数
    const queryParams = new URLSearchParams()
    queryParams.append('format_type', params.format_type)
    if (params.status_filter) queryParams.append('status_filter', params.status_filter)
    if (params.type_filter) queryParams.append('type_filter', params.type_filter)
    if (params.topic_filter) queryParams.append('topic_filter', params.topic_filter)
    if (params.knowledge_point_filter) queryParams.append('knowledge_point_filter', params.knowledge_point_filter)

    // 创建请求
    const token = localStorage.getItem('access_token')
    const url = `/api/v1/mistakes/export?${queryParams.toString()}`

    // 发起请求并下载文件
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || '导出失败')
    }

    // 从响应头获取文件名
    const contentDisposition = response.headers.get('Content-Disposition')
    let filename = '错题本导出'
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename\*=UTF-8''(.+)/)
      if (filenameMatch && filenameMatch[1]) {
        filename = decodeURIComponent(filenameMatch[1])
      }
    }

    // 获取文件内容
    const blob = await response.blob()

    // 创建下载链接
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
  },

  /**
   * 导出单个错题
   */
  async exportSingleMistake(
    mistakeId: string,
    format_type: 'markdown' | 'pdf' | 'word'
  ): Promise<void> {
    // 构建查询参数
    const queryParams = new URLSearchParams()
    queryParams.append('format_type', format_type)

    // 创建请求
    const token = localStorage.getItem('access_token')
    const url = `/api/v1/mistakes/${mistakeId}/export?${queryParams.toString()}`

    // 发起请求并下载文件
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || '导出失败')
    }

    // 从响应头获取文件名
    const contentDisposition = response.headers.get('Content-Disposition')
    let filename = '错题导出'
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename\*=UTF-8''(.+)/)
      if (filenameMatch && filenameMatch[1]) {
        filename = decodeURIComponent(filenameMatch[1])
      }
    }

    // 获取文件内容
    const blob = await response.blob()

    // 创建下载链接
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
  }
}

export default mistakeApi
