/**
 * 教案模板 API 客户端
 */
import request from '@/utils/request'
import type {
  LessonTemplate,
  TemplateListItem,
  CreateTemplateRequest,
  UpdateTemplateRequest,
  TemplateQueryParams,
  TemplateListResponse,
  TemplateDetailResponse,
  ApplyTemplateResponse
} from '@/types/lessonTemplate'

const BASE_URL = '/api/v1/lesson-templates'

/**
 * 获取模板列表
 */
export async function getTemplates(params?: TemplateQueryParams): Promise<TemplateListResponse> {
  return request({
    url: BASE_URL,
    method: 'GET',
    params
  })
}

/**
 * 获取模板详情
 */
export async function getTemplate(templateId: string): Promise<TemplateDetailResponse> {
  return request({
    url: `${BASE_URL}/${templateId}`,
    method: 'GET'
  })
}

/**
 * 创建模板
 */
export async function createTemplate(data: CreateTemplateRequest): Promise<TemplateDetailResponse> {
  return request({
    url: BASE_URL,
    method: 'POST',
    data
  })
}

/**
 * 更新模板
 */
export async function updateTemplate(
  templateId: string,
  data: UpdateTemplateRequest
): Promise<TemplateDetailResponse> {
  return request({
    url: `${BASE_URL}/${templateId}`,
    method: 'PUT',
    data
  })
}

/**
 * 删除模板
 */
export async function deleteTemplate(templateId: string): Promise<void> {
  return request({
    url: `${BASE_URL}/${templateId}`,
    method: 'DELETE'
  })
}

/**
 * 复制模板
 */
export async function duplicateTemplate(templateId: string): Promise<TemplateDetailResponse> {
  return request({
    url: `${BASE_URL}/${templateId}/duplicate`,
    method: 'POST'
  })
}

/**
 * 应用模板（基于模板生成教案）
 */
export async function applyTemplate(
  templateId: string,
  lessonData?: {
    title?: string
    topic?: string
    additional_requirements?: string
  }
): Promise<ApplyTemplateResponse> {
  return request({
    url: `${BASE_URL}/${templateId}/apply`,
    method: 'POST',
    data: lessonData
  })
}

/**
 * 收藏/取消收藏模板
 */
export async function toggleFavoriteTemplate(templateId: string): Promise<{ favorited: boolean }> {
  return request({
    url: `${BASE_URL}/${templateId}/favorite`,
    method: 'POST'
  })
}

/**
 * 评价模板
 */
export async function rateTemplate(templateId: string, rating: number): Promise<{ average_rating: number }> {
  return request({
    url: `${BASE_URL}/${templateId}/rate`,
    method: 'POST',
    data: { rating }
  })
}

/**
 * 获取官方模板分类
 */
export async function getTemplateCategories(): Promise<Array<{ key: string; label: string; icon?: string }>> {
  return request({
    url: `${BASE_URL}/categories`,
    method: 'GET'
  })
}

// 导出类型别名，方便组件使用
export type { LessonTemplate, TemplateListItem, TemplateQueryParams } from '@/types/lessonTemplate'
