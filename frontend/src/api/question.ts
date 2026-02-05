/**
 * 题目 API 客户端
 * 处理题目的增删改查操作
 */
import { get, post, put, del } from '@/utils/request'
import type {
  Question,
  CreateQuestionRequest,
  UpdateQuestionRequest,
  QuestionsListResponse,
} from '@/types/question'

/**
 * 题目 API
 */
export const questionApi = {
  /**
   * 创建题目
   * @param data 题目数据
   * @returns 创建的题目
   */
  create: (data: CreateQuestionRequest) =>
    post<Question>('/v1/questions/', data),

  /**
   * 获取题目详情
   * @param questionId 题目ID
   * @returns 题目详情
   */
  getDetail: (questionId: string) =>
    get<Question>(`/v1/questions/${questionId}`),

  /**
   * 更新题目
   * @param questionId 题目ID
   * @param data 更新数据
   * @returns 更新后的题目
   */
  update: (questionId: string, data: UpdateQuestionRequest) =>
    put<Question>(`/v1/questions/${questionId}`, data),

  /**
   * 删除题目
   * @param questionId 题目ID
   * @returns 删除结果
   */
  delete: (questionId: string) =>
    del<{ message: string }>(`/v1/questions/${questionId}`),

  /**
   * 获取题目列表
   * @param params 查询参数
   * @returns 题目列表
   */
  list: (params?: {
    question_type?: string
    difficulty_level?: string
    topic?: string
    question_bank_id?: string
    is_active?: boolean
    skip?: number
    limit?: number
  }) =>
    get<QuestionsListResponse>('/v1/questions/', { params }),

  /**
   * 批量创建题目
   * @param data 批量数据
   * @returns 创建的题目列表
   */
  batchCreate: (data: {
    questions: CreateQuestionRequest[]
    question_bank_id?: string
  }) =>
    post<{
      total: number
      items: Question[]
      message: string
    }>('/v1/questions/batch', data),
}

export default questionApi
