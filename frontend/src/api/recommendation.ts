/**
 * 推荐系统API客户端
 */
import { get, post, put } from '@/utils/request'
import type {
  DailyRecommendations,
  StudentProfile,
  RecommendationFilter,
  ContentCompletionRequest,
  FeedbackRequest,
  RecommendationHistory
} from '@/types/recommendation'

/**
 * 获取每日推荐
 */
export const getDailyRecommendations = async (
  filter?: RecommendationFilter
): Promise<{
  recommendations: DailyRecommendations
  studentProfile: StudentProfile
}> => {
  const params = new URLSearchParams()

  if (filter?.contentTypes?.length) {
    params.append('content_types', filter.contentTypes.join(','))
  }
  if (filter?.difficultyLevels?.length) {
    params.append('difficulty_levels', filter.difficultyLevels.join(','))
  }
  if (filter?.topics?.length) {
    params.append('topics', filter.topics.join(','))
  }
  if (filter?.examTypes?.length) {
    params.append('exam_types', filter.examTypes.join(','))
  }
  if (filter?.maxRecommendations) {
    params.append('max_recommendations', filter.maxRecommendations.toString())
  }

  const queryString = params.toString()
  const url = `/api/v1/contents/recommend${queryString ? '?' + queryString : ''}`

  return get(url)
}

/**
 * 标记内容完成
 */
export const markContentCompleted = async (
  contentId: string,
  contentType: string
): Promise<void> => {
  const data: ContentCompletionRequest = {
    content_id: contentId,
    content_type: contentType,
    completed_at: new Date().toISOString()
  }

  return post('/api/v1/contents/complete', data)
}

/**
 * 提交推荐反馈
 */
export const submitFeedback = async (
  contentId: string,
  satisfaction: number,
  reason?: string
): Promise<void> => {
  const data: FeedbackRequest = {
    content_id: contentId,
    satisfaction,
    reason,
    feedback_type: 'recommendation'
  }

  return post('/api/v1/contents/feedback', data)
}

/**
 * 获取推荐历史
 */
export const getRecommendationHistory = async (
  page = 1,
  limit = 20
): Promise<RecommendationHistory> => {
  return get('/api/v1/contents/recommend/history', {
    params: { page, limit }
  })
}

/**
 * 获取推荐统计
 */
export const getRecommendationStats = async () => {
  return get('/api/v1/contents/recommend/stats')
}

/**
 * 更新推荐偏好
 */
export const updateRecommendationPreferences = async (
  preferences: {
    preferredTopics?: string[]
    preferredContentTypes?: string[]
    difficultyPreference?: 'easier' | 'same' | 'harder'
    studyTimePreference?: number
  }
) => {
  return put('/api/v1/contents/recommend/preferences', preferences)
}

/**
 * 获取推荐内容详情
 */
export const getContentDetail = async (contentId: string) => {
  return get(`/api/v1/contents/${contentId}`)
}

/**
 * 搜索内容
 */
export const searchContents = async (
  query: string,
  filters?: {
    contentType?: string
    difficultyLevel?: string
    topic?: string
  }
) => {
  const params: any = { query }

  if (filters?.contentType) {
    params.content_type = filters.contentType
  }
  if (filters?.difficultyLevel) {
    params.difficulty_level = filters.difficultyLevel
  }
  if (filters?.topic) {
    params.topic = filters.topic
  }

  return get('/api/v1/contents/search', { params })
}

export const recommendationApi = {
  getDailyRecommendations,
  markContentCompleted,
  submitFeedback,
  getRecommendationHistory,
  getRecommendationStats,
  updateRecommendationPreferences,
  getContentDetail,
  searchContents
}

export default recommendationApi
