/**
 * 导出模板管理 API 客户端
 * 用于管理教案导出模板（创建、编辑、删除、预览、设置默认模板）
 */
import request from '@/utils/request'

const BASE_URL = '/api/v1/export-templates'

/**
 * 模板格式
 */
export type TemplateFormat = 'word' | 'pdf' | 'pptx'

/**
 * 模板类型
 */
export type TemplateType = 'system' | 'custom'

/**
 * 模板变量定义
 */
export interface TemplateVariable {
  /** 变量名 */
  name: string
  /** 变量描述 */
  description: string
  /** 默认值 */
  default_value?: string
  /** 是否必需 */
  required: boolean
}

/**
 * 导出模板
 */
export interface ExportTemplate {
  id: string
  name: string
  description: string
  format: TemplateFormat
  type: TemplateType
  /** 模板文件URL */
  file_url: string
  /** 模板变量定义 */
  variables: TemplateVariable[]
  /** 使用次数 */
  usage_count: number
  /** 是否为默认模板 */
  is_default: boolean
  /** 创建者ID */
  creator_id?: string
  created_at: string
  updated_at: string
}

/**
 * 创建模板请求
 */
export interface CreateTemplateRequest {
  name: string
  description?: string
  format: TemplateFormat
  variables: TemplateVariable[]
  /** 模板文件（FormData） */
  file: File
}

/**
 * 更新模板请求
 */
export interface UpdateTemplateRequest {
  name?: string
  description?: string
  variables?: TemplateVariable[]
  file?: File
}

/**
 * 模板列表查询参数
 */
export interface TemplateListParams {
  format?: TemplateFormat
  type?: TemplateType
  search?: string
  skip?: number
  limit?: number
}

/**
 * 模板列表响应
 */
export interface TemplateListResponse {
  templates: ExportTemplate[]
  total: number
}

/**
 * 模板详情响应
 */
export interface TemplateDetailResponse {
  template: ExportTemplate
}

/**
 * 模板预览响应
 */
export interface TemplatePreviewResponse {
  preview_url: string
  expires_at: string
}

/**
 * 获取模板列表
 */
export async function getTemplates(params?: TemplateListParams): Promise<TemplateListResponse> {
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
  const formData = new FormData()
  formData.append('name', data.name)
  formData.append('format', data.format)
  formData.append('variables', JSON.stringify(data.variables))
  if (data.description) {
    formData.append('description', data.description)
  }
  formData.append('file', data.file)

  return request({
    url: BASE_URL,
    method: 'POST',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 更新模板
 */
export async function updateTemplate(
  templateId: string,
  data: UpdateTemplateRequest
): Promise<TemplateDetailResponse> {
  const formData = new FormData()
  if (data.name !== undefined) {
    formData.append('name', data.name)
  }
  if (data.description !== undefined) {
    formData.append('description', data.description)
  }
  if (data.variables !== undefined) {
    formData.append('variables', JSON.stringify(data.variables))
  }
  if (data.file) {
    formData.append('file', data.file)
  }

  return request({
    url: `${BASE_URL}/${templateId}`,
    method: 'PUT',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
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
 * 设置默认模板
 */
export async function setDefaultTemplate(templateId: string): Promise<void> {
  return request({
    url: `${BASE_URL}/${templateId}/set-default`,
    method: 'POST'
  })
}

/**
 * 预览模板
 */
export async function previewTemplate(templateId: string): Promise<TemplatePreviewResponse> {
  return request({
    url: `${BASE_URL}/${templateId}/preview`,
    method: 'POST'
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
