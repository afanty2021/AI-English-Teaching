/**
 * 通知设置 API 客户端
 *
 * 提供通知偏好设置的 API 调用方法。
 */
import request from '@/utils/request'

// 邮件通知频率类型
export type EmailFrequency = 'immediate' | 'hourly' | 'daily' | 'weekly' | 'never'

// 通知偏好设置接口
export interface NotificationPreference {
  id: string
  user_id: string
  enable_share_notifications: boolean
  enable_comment_notifications: boolean
  enable_system_notifications: boolean
  notify_via_websocket: boolean
  notify_via_email: boolean
  email_frequency: EmailFrequency
  quiet_hours_start: string | null
  quiet_hours_end: string | null
  created_at: string
  updated_at: string
}

// 更新通知偏好设置请求
export interface UpdateNotificationPreferenceRequest {
  enable_share_notifications?: boolean
  enable_comment_notifications?: boolean
  enable_system_notifications?: boolean
  notify_via_websocket?: boolean
  notify_via_email?: boolean
  email_frequency?: EmailFrequency
  quiet_hours_start?: string | null
  quiet_hours_end?: string | null
}

// 静默时段检查响应
export interface QuietHoursStatusResponse {
  in_quiet_hours: boolean
  quiet_hours_configured: boolean
  quiet_hours_start: string | null
  quiet_hours_end: string | null
}

/**
 * 获取当前用户的通知偏好设置
 */
export function getNotificationPreference() {
  return request<NotificationPreference>({
    url: '/api/v1/notifications/preferences',
    method: 'get'
  })
}

/**
 * 更新当前用户的通知偏好设置
 */
export function updateNotificationPreference(data: UpdateNotificationPreferenceRequest) {
  return request<NotificationPreference>({
    url: '/api/v1/notifications/preferences',
    method: 'put',
    data
  })
}

/**
 * 重置当前用户的通知偏好设置为默认值
 */
export function resetNotificationPreference() {
  return request<NotificationPreference>({
    url: '/api/v1/notifications/preferences/reset',
    method: 'post'
  })
}

/**
 * 检查当前用户是否处于静默时段
 */
export function checkQuietHoursStatus() {
  return request<QuietHoursStatusResponse>({
    url: '/api/v1/notifications/preferences/check-quiet-hours',
    method: 'get'
  })
}
