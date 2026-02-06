/**
 * 教案分享 API 客户端
 *
 * 提供教案分享相关的API调用方法。
 */
import request from '@/utils/request'

export interface SharePermission {
  value: 'view' | 'edit' | 'copy'
  label: string
}

export interface ShareStatus {
  value: 'pending' | 'accepted' | 'rejected' | 'expired'
  label: string
}

// 分享权限枚举
export const SHARE_PERMISSIONS: SharePermission[] = [
  { value: 'view', label: '仅查看' },
  { value: 'edit', label: '可编辑' },
  { value: 'copy', label: '可复制' }
]

// 分享状态枚举
export const SHARE_STATUSES: ShareStatus[] = [
  { value: 'pending', label: '待接受' },
  { value: 'accepted', label: '已接受' },
  { value: 'rejected', label: '已拒绝' },
  { value: 'expired', label: '已过期' }
]

export interface UserSummary {
  id: string
  username: string
  full_name: string | null
  email: string
}

export interface LessonPlanSummary {
  id: string
  title: string
  topic: string
  level: string
  duration: number
  status: string
  created_at: string
  updated_at: string
}

export interface LessonPlanShare {
  id: string
  lesson_plan: LessonPlanSummary
  shared_by: UserSummary
  shared_to: UserSummary
  permission: string
  status: string
  message: string | null
  expires_at: string | null
  created_at: string
}

export interface CreateShareRequest {
  shared_to: string
  permission: string
  message?: string
  expires_days?: number
}

export interface ShareListResponse {
  shares: LessonPlanShare[]
  total: number
  page: number
  page_size: number
}

export interface DuplicateLessonPlanRequest {
  new_title?: string
  include_shares?: boolean
}

export interface DuplicateLessonPlanResponse {
  lesson_plan: LessonPlanSummary
  message: string
}

export interface CreateFromTemplateRequest {
  title: string
  topic: string
  level: string
  duration?: number
  target_exam?: string
  additional_requirements?: string
}

export interface LessonPlanTemplateSummary {
  id: string
  name: string
  description: string | null
  level: string
  target_exam: string | null
  is_system: boolean
  usage_count: number
  created_at: string
}

export interface TemplateListResponse {
  templates: LessonPlanTemplateSummary[]
  total: number
  page: number
  page_size: number
}

/**
 * 分享教案给其他教师
 */
export function shareLessonPlan(lessonPlanId: string, data: CreateShareRequest) {
  return request<LessonPlanShare>({
    url: `/api/v1/lesson-plans/${lessonPlanId}/share`,
    method: 'post',
    data
  })
}

/**
 * 获取分享给我的教案列表
 */
export function getSharedWithMe(params?: {
  status?: string
  page?: number
  page_size?: number
}) {
  return request<ShareListResponse>({
    url: '/api/v1/lesson-plans/shared',
    method: 'get',
    params
  })
}

/**
 * 获取我分享的教案列表
 */
export function getSharedByMe(params?: {
  status?: string
  page?: number
  page_size?: number
}) {
  return request<ShareListResponse>({
    url: '/api/v1/lesson-plans/shared-by-me',
    method: 'get',
    params
  })
}

/**
 * 接受分享
 */
export function acceptShare(shareId: string) {
  return request<LessonPlanShare>({
    url: `/api/v1/lesson-plans/shared/${shareId}/accept`,
    method: 'put'
  })
}

/**
 * 拒绝分享
 */
export function rejectShare(shareId: string) {
  return request<LessonPlanShare>({
    url: `/api/v1/lesson-plans/shared/${shareId}/reject`,
    method: 'put'
  })
}

/**
 * 取消分享
 */
export function cancelShare(shareId: string) {
  return request({
    url: `/api/v1/lesson-plans/shared/${shareId}`,
    method: 'delete'
  })
}

/**
 * 复制教案
 */
export function duplicateLessonPlan(lessonPlanId: string, data?: DuplicateLessonPlanRequest) {
  return request<DuplicateLessonPlanResponse>({
    url: `/api/v1/lesson-plans/${lessonPlanId}/duplicate`,
    method: 'post',
    data
  })
}

/**
 * 获取教案模板列表
 */
export function getLessonPlanTemplates(params?: {
  level?: string
  target_exam?: string
  is_system?: boolean
  page?: number
  page_size?: number
}) {
  return request<TemplateListResponse>({
    url: '/api/v1/lesson-plans/templates',
    method: 'get',
    params
  })
}

/**
 * 从模板创建教案
 */
export function createFromTemplate(templateId: string, data: CreateFromTemplateRequest) {
  return request<{
    lesson_plan: LessonPlanSummary
  }>({
    url: `/api/v1/lesson-plans/from-template/${templateId}`,
    method: 'post',
    data
  })
}
