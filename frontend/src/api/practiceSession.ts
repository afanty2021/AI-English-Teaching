/**
 * 练习会话 API 客户端
 * 处理练习会话的创建、答题、导航、完成等操作
 */
import { get, post } from '@/utils/request'
import type {
  PracticeSession,
  StartPracticeSessionRequest,
  CurrentQuestionResponse,
  SubmitAnswerRequest,
  SubmitAnswerResponse,
  NavigateRequest,
  CompleteSessionResponse,
  PracticeSessionsListResponse,
} from '@/types/question'

/**
 * 练习会话 API
 */
export const practiceSessionApi = {
  /**
   * 开始练习会话
   * @param data 会话数据
   * @returns 创建的会话
   */
  start: (data: StartPracticeSessionRequest) =>
    post<PracticeSession>('/v1/practice-sessions/', data),

  /**
   * 获取会话详情
   * @param sessionId 会话ID
   * @returns 会话详情
   */
  getDetail: (sessionId: string) =>
    get<PracticeSession>(`/v1/practice-sessions/${sessionId}`),

  /**
   * 获取当前题目
   * @param sessionId 会话ID
   * @returns 当前题目信息
   */
  getCurrentQuestion: (sessionId: string) =>
    get<CurrentQuestionResponse>(`/v1/practice-sessions/${sessionId}/current`),

  /**
   * 提交答案
   * @param sessionId 会话ID
   * @param data 答案数据
   * @returns 答题结果
   */
  submitAnswer: (sessionId: string, data: SubmitAnswerRequest) =>
    post<SubmitAnswerResponse>(`/v1/practice-sessions/${sessionId}/submit`, data),

  /**
   * 导航题目（上一题/下一题）
   * @param sessionId 会话ID
   * @param data 导航方向
   * @returns 新的当前题目
   */
  navigate: (sessionId: string, data: NavigateRequest) =>
    post<CurrentQuestionResponse>(`/v1/practice-sessions/${sessionId}/navigate`, data),

  /**
   * 暂停会话
   * @param sessionId 会话ID
   * @returns 暂停结果
   */
  pause: (sessionId: string) =>
    post<{ message: string }>(`/v1/practice-sessions/${sessionId}/pause`, {}),

  /**
   * 继续会话
   * @param sessionId 会话ID
   * @returns 当前题目
   */
  resume: (sessionId: string) =>
    post<CurrentQuestionResponse>(`/v1/practice-sessions/${sessionId}/resume`, {}),

  /**
   * 完成会话
   * @param sessionId 会话ID
   * @returns 练习结果
   */
  complete: (sessionId: string) =>
    post<CompleteSessionResponse>(`/v1/practice-sessions/${sessionId}/complete`, {}),

  /**
   * 获取会话列表
   * @param params 查询参数
   * @returns 会话列表
   */
  list: (params?: {
    status_filter?: string
    skip?: number
    limit?: number
  }) =>
    get<PracticeSessionsListResponse>('/v1/practice-sessions/', { params }),

  /**
   * 获取练习结果详情
   * @param sessionId 会话ID
   * @returns 练习结果
   */
  getResult: (sessionId: string) =>
    get<CompleteSessionResponse>(`/v1/practice-sessions/${sessionId}/result`),
}

export default practiceSessionApi
