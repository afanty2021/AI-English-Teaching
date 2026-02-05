/**
 * 教师端学习报告API客户端
 * 提供教师查看学生学习报告的相关接口
 */

import { get, post } from '@/utils/request'

// 学生报告概览接口
export interface StudentReportSummary {
  student_id: string
  student_number: string
  student_name: string
  email: string
  class_id: string
  class_name: string
  grade: string
  latest_report?: {
    report_id: string
    created_at: string
    report_type: string
  }
  has_reports: boolean
}

// 学习报告详情
export interface LearningReport {
  id: string
  student_id: string
  report_type: string
  period_start: string
  period_end: string
  status: string
  title?: string
  description?: string
  statistics?: ReportStatistics
  ability_analysis?: AbilityAnalysis
  weak_points?: WeakPoints
  recommendations?: Recommendations
  ai_insights?: any
  created_at: string
  updated_at: string
}

// 报告统计
export interface ReportStatistics {
  total_practices: number
  completed_practices: number
  completion_rate: number
  avg_correct_rate: number
  total_duration_minutes: number
  total_duration_hours: number
  total_mistakes: number
  mistake_by_type: Record<string, number>
  mistake_by_status: Record<string, number>
  period_days: number
}

// 能力分析
export interface AbilityAnalysis {
  current_abilities: Record<string, any>
  ability_radar: Array<{
    name: string
    value: number
    confidence: number
  }>
  strongest_area?: { name: string; level: number }
  weakest_area?: { name: string; level: number }
  last_updated?: string
}

// 薄弱点
export interface WeakPoints {
  total_unmastered: number
  knowledge_points: Record<string, number>
  knowledge_point_counts: Record<string, number>
  by_topic: Record<string, number>
  by_difficulty: Record<string, number>
  top_weak_points: Array<{ point: string; count: number }>
}

// 学习建议
export interface Recommendations {
  rule_based: Array<{
    category: string
    priority: 'high' | 'medium' | 'low'
    title: string
    description: string
  }>
  ai_generated?: Array<{
    category: string
    priority: 'high' | 'medium' | 'low'
    title: string
    description: string
    confidence: number
  }>
}

// 班级学习状况汇总
export interface ClassSummary {
  class_id: string
  class_name: string
  total_students: number
  active_students: number
  overall_stats: {
    avg_completion_rate: number
    avg_correct_rate: number
    total_study_hours: number
  }
  ability_distribution: {
    listening: number
    reading: number
    speaking: number
    writing: number
    grammar: number
    vocabulary: number
  }
  top_weak_points: Array<{
    knowledge_point: string
    affected_students: number
  }>
  period_start: string
  period_end: string
}

// API响应类型
export interface TeacherStudentReportsResponse {
  total: number
  limit: number
  offset: number
  students: StudentReportSummary[]
}

export interface StudentReportsResponse {
  total: number
  limit: number
  offset: number
  reports: Array<{
    id: string
    report_type: string
    period_start: string
    period_end: string
    status: string
    title: string
    created_at: string
  }>
}

export interface GenerateReportRequest {
  report_type: 'weekly' | 'monthly' | 'custom'
  period_start?: string
  period_end?: string
}

/**
 * 教师端学习报告API
 */
export default {
  /**
   * 获取教师班级学生列表
   */
  getStudents(params: {
    classId?: string
    page?: number
    limit?: number
  }) {
    const query = new URLSearchParams()
    if (params.classId) query.append('class_id', params.classId)
    if (params.page) query.append('offset', String((params.page - 1) * (params.limit || 20)))
    if (params.limit) query.append('limit', String(params.limit))

    return get<TeacherStudentReportsResponse>(`/reports/teacher/students?${query.toString()}`)
  },

  /**
   * 获取学生报告详情（教师视角）
   */
  getStudentReport(studentId: string, reportId: string) {
    return get<LearningReport>(`/reports/teacher/students/${studentId}/reports/${reportId}`)
  },

  /**
   * 获取学生所有报告（教师视角）
   */
  getStudentReports(studentId: string, params: {
    reportType?: string
    page?: number
    limit?: number
  }) {
    const query = new URLSearchParams()
    if (params.reportType) query.append('report_type', params.reportType)
    if (params.page) query.append('offset', String((params.page - 1) * (params.limit || 20)))
    if (params.limit) query.append('limit', String(params.limit))

    return get<StudentReportsResponse>(`/reports/teacher/students/${studentId}?${query.toString()}`)
  },

  /**
   * 获取班级学习状况汇总
   */
  getClassSummary(params: {
    classId: string
    periodStart?: string
    periodEnd?: string
  }) {
    const query = new URLSearchParams()
    query.append('class_id', params.classId)
    if (params.periodStart) query.append('period_start', params.periodStart)
    if (params.periodEnd) query.append('period_end', params.periodEnd)

    return get<ClassSummary>(`/reports/teacher/class-summary?${query.toString()}`)
  },

  /**
   * 生成学生报告（教师触发）
   */
  generateStudentReport(_studentId: string, data: GenerateReportRequest) {
    return post(`/reports/generate`, data)
  },

  /**
   * 导出学生报告
   */
  exportStudentReport(_studentId: string, reportId: string, format: 'pdf' | 'image' = 'pdf') {
    return post(`/reports/${reportId}/export?format_type=${format}`, {}, {
      responseType: 'blob'
    } as any)
  }
}
