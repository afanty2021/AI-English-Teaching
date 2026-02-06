/**
 * 学习报告增强功能类型定义
 *
 * 包含图表数据、异步任务状态等增强功能的TypeScript类型
 */

/**
 * 学习趋势图表数据类型
 */
export interface LearningTrendData {
  period: {
    start: string
    end: string
  }
  metrics: {
    practices: Array<{
      date: string
      count: number
    }>
    correctRate: Array<{
      date: string
      rate: number
    }>
    duration: Array<{
      date: string
      minutes: number
    }>
  }
}

/**
 * 学习趋势查询参数
 */
export interface LearningTrendQuery {
  period?: '7d' | '30d' | '90d' | 'custom'
  startDate?: string
  endDate?: string
  metrics?: ('practices' | 'correctRate' | 'duration')[]
}

/**
 * 能力雷达图数据类型
 */
export interface AbilityRadarData {
  abilities: Array<{
    name: string
    value: number
    confidence: number
    history?: number[]
    relatedTopics: string[]
    recommendedContent?: ContentRecommendation[]
  }>
  classAverage?: Record<string, number>
  strongestPoint: {
    name: string
    value: number
  }
  weakestPoint: {
    name: string
    value: number
  }
}

/**
 * 内容推荐
 */
export interface ContentRecommendation {
  contentId: string
  title: string
  difficulty: string
  type: string
}

/**
 * 能力雷达图查询参数
 */
export interface AbilityRadarQuery {
  compareWith?: 'none' | 'class_avg' | 'history'
  historyDate?: string
}

/**
 * 知识点数据类型
 */
export interface KnowledgePoint {
  topic: string
  ability: string
  difficulty: string
  masteryRate: number
  practiceCount: number
  trend: 'up' | 'down' | 'stable'
}

/**
 * 知识点热力图数据
 */
export interface KnowledgeHeatmapData {
  topics: Array<{
    id: string
    name: string
    abilities: Array<{
      name: string
      difficulty: string
      masteryRate: number
      practiceCount: number
      trend: 'up' | 'down' | 'stable'
    }>
  }>
}

/**
 * 知识点热力图查询参数
 */
export interface KnowledgeHeatmapQuery {
  filterByAbility?: string
  filterByTopic?: string
  filterByDifficulty?: string
}

/**
 * 异步任务状态枚举
 */
export type AsyncTaskStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'

/**
 * 异步任务类型枚举
 */
export type AsyncTaskType = 'report_export' | 'batch_export'

/**
 * 异步任务基本信息
 */
export interface AsyncTaskInfo {
  id: string
  taskType: AsyncTaskType
  status: AsyncTaskStatus
  progress: number
  message?: string
  createdAt: string
  updatedAt?: string
  completedAt?: string
  resultUrl?: string
  errorMessage?: string
}

/**
 * 异步导出请求参数
 */
export interface AsyncExportRequest {
  reportId?: string
  studentIds?: string[]
  exportFormat: 'pdf' | 'image'
  reportType: 'full' | 'summary' | 'comparison'
  includeCharts?: boolean
  asyncMode?: boolean
}

/**
 * 异步导出响应
 */
export interface AsyncExportResponse {
  taskId: string
  status: AsyncTaskStatus
  message: string
  estimatedTime?: number // 预计完成时间（秒）
}

/**
 * 批量导出请求参数
 */
export interface BatchExportRequest {
  studentIds: string[]
  classId?: string
  exportFormat: 'pdf' | 'image'
  reportType: 'full' | 'summary'
}

/**
 * 批量导出响应
 */
export interface BatchExportResponse {
  taskId: string
  totalCount: number
  status: AsyncTaskStatus
  message: string
}

/**
 * 导出进度信息（前端展示用）
 */
export interface ExportProgressInfo {
  taskId: string
  status: AsyncTaskStatus
  progress: number
  percentage: number
  message: string
  canCancel: boolean
  canRetry: boolean
  resultUrl?: string
  errorMessage?: string
  startTime: string
  estimatedRemainingTime?: number
}

/**
 * 图表通用配置
 */
export interface ChartConfig {
  theme?: 'light' | 'dark'
  animation?: boolean
  lazyUpdate?: boolean
  width?: string | number
  height?: string | number
}

/**
 * 时间范围选择选项
 */
export interface TimeRangeOption {
  value: '7d' | '30d' | '90d' | 'custom'
  label: string
  days: number
}

/**
 * 报告详情增强响应（整合所有图表数据）
 */
export interface ReportDetailEnhanced {
  // 基础报告信息
  id: string
  studentId: string
  reportType: string
  periodStart: string
  periodEnd: string
  createdAt: string

  // 原有报告数据
  statistics?: ReportStatistics
  abilityAnalysis?: AbilityAnalysis
  weakPoints?: WeakPoints
  recommendations?: Recommendations
  aiInsights?: any

  // 新增图表数据
  learningTrend?: LearningTrendData
  abilityRadar?: AbilityRadarData
  knowledgeHeatmap?: KnowledgeHeatmapData
}

/**
 * API响应包装（复用现有模式）
 */
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

/**
 * 分页响应
 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  limit: number
  offset: number
  hasMore: boolean
}
