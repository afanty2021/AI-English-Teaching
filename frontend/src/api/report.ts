/**
 * 学习报告 API
 */
import request from '@/utils/request'

export interface GenerateReportRequest {
  report_type?: 'weekly' | 'monthly' | 'custom'
  period_start?: string  // ISO 8601 格式
  period_end?: string    // ISO 8601 格式
}

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

export interface AbilityAnalysis {
  current_abilities: Record<string, any>
  ability_radar: Array<{
    name: string
    value: number
    confidence: number
  }>
  strongest_area?: {
    name: string
    level: number
  }
  weakest_area?: {
    name: string
    level: number
  }
  last_updated?: string
}

export interface WeakPoints {
  total_unmastered: number
  knowledge_points: Record<string, number>
  knowledge_point_counts: Record<string, number>
  by_topic: Record<string, number>
  by_difficulty: Record<string, number>
  top_weak_points: Array<{
    point: string
    count: number
  }>
}

export interface Recommendation {
  category: string
  priority: 'high' | 'medium' | 'low'
  title: string
  description: string
}

export interface Recommendations {
  recommendations: Recommendation[]
  priority_count: {
    high: number
    medium: number
    low: number
  }
  total_count: number
}

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

export interface ReportListResponse {
  total: number
  limit: number
  offset: number
  reports: Array<{
    id: string
    report_type: string
    period_start: string
    period_end: string
    status: string
    title?: string
    created_at: string
  }>
}

const reportApi = {
  /**
   * 生成学习报告
   */
  async generateReport(data: GenerateReportRequest): Promise<LearningReport> {
    return request({
      url: '/v1/reports/generate',
      method: 'post',
      data
    })
  },

  /**
   * 获取我的报告列表
   */
  async getMyReports(params?: {
    report_type?: string
    limit?: number
    offset?: number
  }): Promise<ReportListResponse> {
    return request({
      url: '/v1/reports/me',
      method: 'get',
      params
    })
  },

  /**
   * 获取报告详情
   */
  async getReportDetail(reportId: string): Promise<LearningReport> {
    return request({
      url: `/v1/reports/${reportId}`,
      method: 'get'
    })
  },

  /**
   * 导出报告
   */
  async exportReport(reportId: string, format: 'pdf' | 'image' = 'pdf'): Promise<Blob> {
    const response = await request({
      url: `/v1/reports/${reportId}/export`,
      method: 'post',
      params: { format_type: format },
      responseType: 'blob'
    })
    return response
  },

  /**
   * 删除报告
   */
  async deleteReport(reportId: string): Promise<void> {
    return request({
      url: `/v1/reports/${reportId}`,
      method: 'delete'
    })
  }
}

export default reportApi
