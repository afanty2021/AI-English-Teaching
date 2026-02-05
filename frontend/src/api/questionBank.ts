/**
 * 题库 API 客户端
 * 处理题库的增删改查和题目管理操作
 */
import { get, post, put, del } from '@/utils/request'
import type {
  QuestionBank,
  CreateQuestionBankRequest,
  UpdateQuestionBankRequest,
  QuestionBanksListResponse,
  QuestionsListResponse,
} from '@/types/question'

/**
 * 题库 API
 */
export const questionBankApi = {
  /**
   * 创建题库
   * @param data 题库数据
   * @returns 创建的题库
   */
  create: (data: CreateQuestionBankRequest) =>
    post<QuestionBank>('/v1/question-banks/', data),

  /**
   * 获取题库详情
   * @param bankId 题库ID
   * @returns 题库详情
   */
  getDetail: (bankId: string) =>
    get<QuestionBank>(`/v1/question-banks/${bankId}`),

  /**
   * 更新题库
   * @param bankId 题库ID
   * @param data 更新数据
   * @returns 更新后的题库
   */
  update: (bankId: string, data: UpdateQuestionBankRequest) =>
    put<QuestionBank>(`/v1/question-banks/${bankId}`, data),

  /**
   * 删除题库
   * @param bankId 题库ID
   * @returns 删除结果
   */
  delete: (bankId: string) =>
    del<{ message: string }>(`/v1/question-banks/${bankId}`),

  /**
   * 获取题库列表
   * @param params 查询参数
   * @returns 题库列表
   */
  list: (params?: {
    practice_type?: string
    difficulty_level?: string
    is_public?: boolean
    skip?: number
    limit?: number
  }) =>
    get<QuestionBanksListResponse>('/v1/question-banks/', { params }),

  /**
   * 获取题库中的题目列表
   * @param bankId 题库ID
   * @param params 查询参数
   * @returns 题目列表
   */
  getQuestions: (
    bankId: string,
    params?: {
      skip?: number
      limit?: number
    }
  ) =>
    get<QuestionsListResponse>(`/v1/question-banks/${bankId}/questions`, { params }),

  /**
   * 添加题目到题库
   * @param bankId 题库ID
   * @param data 题目数据
   * @returns 添加结果
   */
  addQuestion: (bankId: string, data: { question_id: string; order_index?: number }) =>
    post<{ message: string }>(`/v1/question-banks/${bankId}/questions`, data),

  /**
   * 从题库移除题目
   * @param bankId 题库ID
   * @param questionId 题目ID
   * @returns 移除结果
   */
  removeQuestion: (bankId: string, questionId: string) =>
    del<{ message: string }>(`/v1/question-banks/${bankId}/questions/${questionId}`),
}

export default questionBankApi
