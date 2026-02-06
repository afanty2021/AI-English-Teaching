/**
 * 用户 API 客户端
 *
 * 提供用户搜索、查询等API调用方法。
 */
import request from '@/utils/request'

export interface UserResponse {
  id: string
  username: string
  email: string
  full_name: string | null
  role: string
  is_active: boolean
  created_at: string | null
  updated_at: string | null
}

export interface UserListResponse {
  users: UserResponse[]
  total: number
  skip: number
  limit: number
}

export interface TeacherSummary {
  id: string
  username: string
  full_name: string | null
  email: string
}

export interface ShareStatistics {
  pending_count: number
  total_shared_by_me: number
  total_shared_to_me: number
  accepted_count: number
  rejected_count: number
  acceptance_rate: number
}

export interface ShareNotification {
  id: string
  type: string
  title: string
  content: string
  lesson_plan_id: string
  lesson_plan_title: string
  permission: string
  sharer: {
    id: string
    username: string
    full_name: string | null
  }
  created_at: string | null
  expires_at: string | null
}

export interface PendingNotificationsResponse {
  notifications: ShareNotification[]
  count: number
}

/**
 * 搜索用户
 */
export function searchUsers(params: {
  q: string
  role?: string
  skip?: number
  limit?: number
}) {
  return request<UserListResponse>({
    url: '/api/v1/users/search',
    method: 'get',
    params
  })
}

/**
 * 获取教师列表
 */
export function getTeachers(params?: {
  skip?: number
  limit?: number
}) {
  return request<UserListResponse>({
    url: '/api/v1/users/teachers',
    method: 'get',
    params
  })
}

/**
 * 获取分享统计
 */
export function getShareStatistics() {
  return request<ShareStatistics>({
    url: '/api/v1/lesson-plans/shared/statistics/overview',
    method: 'get'
  })
}

/**
 * 获取待处理通知
 */
export function getPendingNotifications() {
  return request<PendingNotificationsResponse>({
    url: '/api/v1/lesson-plans/notifications/pending',
    method: 'get'
  })
}
