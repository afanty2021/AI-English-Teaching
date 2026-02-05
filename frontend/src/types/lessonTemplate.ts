/**
 * 教案模板相关类型定义
 */

// ==================== 基础类型 ====================

/**
 * CEFR 语言级别
 */
export type CEFRLevel = 'A1' | 'A2' | 'B1' | 'B2' | 'C1' | 'C2'

/**
 * 模板分类
 */
export interface TemplateCategory {
  key: string
  label: string
  icon?: string
}

/**
 * 模板结构
 */
export interface TemplateStructure {
  sections: TemplateSection[]
  objectives?: string[]
  vocabulary?: {
    nouns: number
    verbs: number
    adjectives: number
  }
  grammar_points?: string[]
}

/**
 * 模板章节
 */
export interface TemplateSection {
  key: string
  label: string
  duration: number
  required: boolean
  content_template?: string
}

// ==================== 模板类型 ====================

/**
 * 教案模板
 */
export interface LessonTemplate {
  id: string
  name: string
  description: string
  category: TemplateCategory
  level: CEFRLevel
  duration: number
  structure: TemplateStructure
  thumbnail_url?: string
  is_public: boolean
  is_official: boolean
  usage_count: number
  rating: number
  created_by: string
  created_at: string
  updated_at: string
}

/**
 * 模板列表项（摘要视图）
 */
export interface TemplateListItem {
  id: string
  name: string
  description: string
  category_key: string
  category_label: string
  level: CEFRLevel
  duration: number
  thumbnail_url?: string
  is_public: boolean
  is_official: boolean
  usage_count: number
  rating: number
  created_at: string
}

// ==================== 请求类型 ====================

/**
 * 创建模板请求
 */
export interface CreateTemplateRequest {
  name: string
  description: string
  category_key: string
  level: CEFRLevel
  duration: number
  structure: TemplateStructure
  is_public: boolean
}

/**
 * 更新模板请求
 */
export interface UpdateTemplateRequest {
  name?: string
  description?: string
  category_key?: string
  level?: CEFRLevel
  duration?: number
  structure?: TemplateStructure
  is_public?: boolean
}

/**
 * 模板查询参数
 */
export interface TemplateQueryParams {
  page?: number
  page_size?: number
  category?: string
  level?: CEFRLevel
  search?: string
  is_public?: boolean
  is_official?: boolean
  sort_by?: 'created_at' | 'usage_count' | 'rating' | 'name'
  sort_order?: 'asc' | 'desc'
}

// ==================== 响应类型 ====================

/**
 * 模板列表响应
 */
export interface TemplateListResponse {
  items: TemplateListItem[]
  total: number
  page: number
  page_size: number
}

/**
 * 模板详情响应
 */
export interface TemplateDetailResponse {
  template: LessonTemplate
}

/**
 * 应用模板响应
 */
export interface ApplyTemplateResponse {
  lesson_plan_id: string
  lesson_plan: any
}
