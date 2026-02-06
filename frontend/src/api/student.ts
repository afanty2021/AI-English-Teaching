/**
 * 学生管理API客户端
 * 提供教师端学生管理和诊断相关的接口
 */

import { get, post } from '@/utils/request'

// 学生档案
export interface StudentProfile {
  id: string
  user_id: string
  username: string
  email: string
  target_exam?: string
  target_score?: number
  study_goal?: string
  current_cefr_level?: string
  grade?: string
  created_at: string
}

// 知识图谱数据
export interface KnowledgeGraph {
  student_id: string
  nodes: Array<{
    id: string
    type: string
    label: string
    value?: number
    level?: string
    readiness?: boolean
    reason?: string
  }>
  edges: Array<{
    source: string
    target: string
    type: string
  }>
  abilities: Record<string, number>
  cefr_level?: string
  exam_coverage: {
    total_practices: number
    topics_covered: number
    recent_activity: number
  }
  ai_analysis: {
    weak_points?: Array<{
      topic: string
      ability: string
      current_level: number
      reason: string
      priority: string
    }>
    strong_points?: Array<{
      topic: string
      ability: string
      current_level: number
      reason: string
    }>
    recommendations?: Array<{
      priority: string
      suggestion: string
      ability: string
    }>
    [key: string]: any
  }
  last_ai_analysis_at?: string
  version: number
  created_at: string
  updated_at: string
}

// 学生进度
export interface StudentProgress {
  student_id: string
  target_exam?: string
  target_score?: number
  current_cefr_level?: string
  conversation_count: number
  practice_count: number
  average_score: number
}

// 诊断请求参数
export interface DiagnoseRequest {
  practice_data?: Array<{
    content_id: string
    topic: string
    difficulty: string
    score: number
    correct_rate: number
    time_spent: number
  }>
}

// 诊断响应
export interface DiagnoseResponse {
  message: string
  student_id: string
  status: string
  cefr_level?: string
  abilities?: Record<string, number>
}

/**
 * 学生管理API
 */
export default {
  /**
   * 获取学生列表（教师端）
   */
  getStudents(params?: {
    skip?: number
    limit?: number
    classId?: string
  }) {
    const query = new URLSearchParams()
    if (params?.skip !== undefined) query.append('skip', String(params.skip))
    if (params?.limit !== undefined) query.append('limit', String(params.limit))
    if (params?.classId) query.append('class_id', params.classId)

    const queryString = query.toString()
    return get<StudentProfile[]>(`/api/v1/students${queryString ? `?${queryString}` : ''}`)
  },

  /**
   * 获取学生详情
   */
  getStudent(studentId: string) {
    return get<StudentProfile>(`/api/v1/students/${studentId}`)
  },

  /**
   * 获取学生知识图谱
   */
  getKnowledgeGraph(studentId: string) {
    return get<KnowledgeGraph>(`/api/v1/students/${studentId}/knowledge-graph`)
  },

  /**
   * 触发学生初始诊断
   */
  diagnoseStudent(studentId: string, data?: DiagnoseRequest) {
    return post<DiagnoseResponse>(`/api/v1/students/${studentId}/diagnose`, data || {})
  },

  /**
   * 获取学生学习进度
   */
  getStudentProgress(studentId: string) {
    return get<StudentProgress>(`/api/v1/students/${studentId}/progress`)
  }
}
