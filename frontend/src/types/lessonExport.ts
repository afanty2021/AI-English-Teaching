/**
 * 教案导出相关类型定义
 */

// ==================== 基础类型 ====================

/**
 * 导出格式
 */
export type ExportFormat = 'word' | 'pdf' | 'pptx' | 'markdown'

/**
 * 导出内容章节
 */
export type ExportSection =
  | 'overview'
  | 'objectives'
  | 'vocabulary'
  | 'grammar'
  | 'structure'
  | 'materials'
  | 'exercises'

/**
 * 导出语言
 */
export type ExportLanguage = 'zh' | 'en' | 'bilingual'

/**
 * 导出选项
 */
export interface ExportOptions {
  /** 导出格式 */
  format: ExportFormat
  /** 要导出的章节 */
  sections: ExportSection[]
  /** 样式模板ID（可选） */
  template_id?: string
  /** 是否包含教师备注 */
  include_teacher_notes: boolean
  /** 是否包含练习答案 */
  include_answers: boolean
  /** 导出语言 */
  language: ExportLanguage
  /** 是否包含页码 */
  include_page_numbers: boolean
  /** 是否包含目录 */
  include_toc: boolean
}

/**
 * 导出任务状态
 */
export type ExportTaskStatus = 'pending' | 'processing' | 'completed' | 'failed'

/**
 * 导出任务
 */
export interface ExportTask {
  id: string
  lesson_id: string
  lesson_title: string
  format: ExportFormat
  options: ExportOptions
  status: ExportTaskStatus
  progress: number
  error_message?: string
  download_url?: string
  created_at: string
  completed_at?: string
}

/**
 * 导出模板
 */
export interface ExportTemplate {
  id: string
  name: string
  description: string
  preview_url: string
  format: ExportFormat
  is_default: boolean
}

// ==================== 请求类型 ====================

/**
 * 创建导出任务请求
 */
export interface CreateExportTaskRequest {
  lesson_id: string
  format: ExportFormat
  options?: Partial<ExportOptions>
}

/**
 * 批量导出请求
 */
export interface BatchExportRequest {
  lesson_ids: string[]
  format: ExportFormat
  options?: Partial<ExportOptions>
}

// ==================== 响应类型 ====================

/**
 * 导出任务响应
 */
export interface ExportTaskResponse {
  task: ExportTask
}

/**
 * 导出任务列表响应
 */
export interface ExportTaskListResponse {
  tasks: ExportTask[]
  total: number
}

/**
 * 导出模板列表响应
 */
export interface ExportTemplateListResponse {
  templates: ExportTemplate[]
}

/**
 * 导出进度事件
 */
export interface ExportProgressEvent {
  type: 'progress' | 'stage' | 'completed' | 'failed'
  task_id: string
  data: {
    progress?: number
    stage?: string
    stage_progress?: number
    message?: string
    download_url?: string
    error?: string
  }
}
