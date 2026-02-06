<template>
  <div class="notification-settings">
    <h2>通知设置</h2>

    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <span>通知偏好设置</span>
          <el-button type="primary" link @click="resetToDefault">
            重置为默认
          </el-button>
        </div>
      </template>

      <div v-loading="isLoading">
        <!-- 通知类型开关 -->
        <div class="section">
          <h3>通知类型</h3>
          <el-form label-position="top">
            <el-form-item label="分享通知">
              <el-switch
                v-model="preferences.enable_share_notifications"
                active-text="启用"
                inactive-text="关闭"
                @change="savePreferences"
              />
              <div class="description">当其他教师分享教案给您时接收通知</div>
            </el-form-item>

            <el-form-item label="评论通知">
              <el-switch
                v-model="preferences.enable_comment_notifications"
                active-text="启用"
                inactive-text="关闭"
                @change="savePreferences"
              />
              <div class="description">当您的内容收到评论时接收通知</div>
            </el-form-item>

            <el-form-item label="系统通知">
              <el-switch
                v-model="preferences.enable_system_notifications"
                active-text="启用"
                inactive-text="关闭"
                @change="savePreferences"
              />
              <div class="description">接收系统公告和重要提醒</div>
            </el-form-item>
          </el-form>
        </div>

        <el-divider />

        <!-- 通知方式 -->
        <div class="section">
          <h3>通知方式</h3>
          <el-form label-position="top">
            <el-form-item label="实时通知 (WebSocket)">
              <el-switch
                v-model="preferences.notify_via_websocket"
                active-text="启用"
                inactive-text="关闭"
                :disabled="!preferences.enable_share_notifications && !preferences.enable_comment_notifications && !preferences.enable_system_notifications"
                @change="savePreferences"
              />
              <div class="description">通过 WebSocket 实时推送通知（无需刷新页面）</div>
            </el-form-item>

            <el-form-item label="邮件通知">
              <el-switch
                v-model="preferences.notify_via_email"
                active-text="启用"
                inactive-text="关闭"
                @change="savePreferences"
              />
              <div class="description">通过邮件接收通知摘要</div>
            </el-form-item>

            <el-form-item
              v-if="preferences.notify_via_email"
              label="邮件发送频率"
            >
              <el-select
                v-model="preferences.email_frequency"
                style="width: 200px"
                @change="savePreferences"
              >
                <el-option label="立即发送" value="immediate" />
                <el-option label="每小时汇总" value="hourly" />
                <el-option label="每天汇总" value="daily" />
                <el-option label="每周汇总" value="weekly" />
                <el-option label="从不发送" value="never" />
              </el-select>
            </el-form-item>
          </el-form>
        </div>

        <el-divider />

        <!-- 静默时段 -->
        <div class="section">
          <h3>静默时段</h3>
          <p class="section-description">
            在静默时段内，您将不会收到任何通知（除非有紧急通知）。
          </p>
          <el-form label-position="top">
            <el-form-item label="启用静默时段">
              <el-switch
                v-model="quietHoursEnabled"
                active-text="启用"
                inactive-text="关闭"
                @change="toggleQuietHours"
              />
            </el-form-item>

            <template v-if="quietHoursEnabled">
              <el-form-item label="静默时间范围">
                <el-time-picker
                  v-model="quietHoursStart"
                  placeholder="开始时间"
                  format="HH:mm"
                  value-format="HH:mm"
                  style="margin-right: 16px; width: 140px"
                  @change="saveQuietHours"
                />
                <span style="margin: 0 8px">至</span>
                <el-time-picker
                  v-model="quietHoursEnd"
                  placeholder="结束时间"
                  format="HH:mm"
                  value-format="HH:mm"
                  style="width: 140px"
                  @change="saveQuietHours"
                />
              </el-form-item>
            </template>
          </el-form>

          <!-- 当前状态 -->
          <div class="quiet-hours-status">
            <el-tag
              :type="isInQuietHours ? 'warning' : 'success'"
              size="small"
            >
              {{ isInQuietHours ? '当前处于静默时段' : '当前可接收通知' }}
            </el-tag>
          </div>
        </div>

        <el-divider />

        <!-- 最后更新 -->
        <div class="last-updated">
          最后更新: {{ formatTime(preferences.updated_at) }}
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { NotificationPreference, EmailFrequency } from '@/api/notification'
import {
  getNotificationPreference,
  updateNotificationPreference,
  resetNotificationPreference,
  checkQuietHoursStatus
} from '@/api/notification'

const isLoading = ref(false)
const isInQuietHours = ref(false)

// 通知偏好设置
const preferences = ref<NotificationPreference>({
  id: '',
  user_id: '',
  enable_share_notifications: true,
  enable_comment_notifications: true,
  enable_system_notifications: true,
  notify_via_websocket: true,
  notify_via_email: false,
  email_frequency: 'immediate',
  quiet_hours_start: null,
  quiet_hours_end: null,
  created_at: '',
  updated_at: ''
})

// 静默时段开关
const quietHoursEnabled = computed(() => {
  return !!preferences.value.quiet_hours_start && !!preferences.value.quiet_hours_end
})

// 静默时段时间（用于时间选择器）
const quietHoursStart = computed({
  get: () => preferences.value.quiet_hours_start,
  set: (val: string | null) => {
    preferences.value.quiet_hours_start = val
  }
})

const quietHoursEnd = computed({
  get: () => preferences.value.quiet_hours_end,
  set: (val: string | null) => {
    preferences.value.quiet_hours_end = val
  }
})

// 加载设置
const loadPreferences = async () => {
  isLoading.value = true
  try {
    const response = await getNotificationPreference()
    preferences.value = response

    // 检查静默时段状态
    await checkQuietHours()
  } catch (error: any) {
    console.error('加载通知设置失败:', error)
    ElMessage.error(error.response?.data?.detail || '加载通知设置失败')
  } finally {
    isLoading.value = false
  }
}

// 检查静默时段状态
const checkQuietHours = async () => {
  try {
    const response = await checkQuietHoursStatus()
    isInQuietHours.value = response.in_quiet_hours
  } catch (error) {
    console.error('检查静默时段状态失败:', error)
  }
}

// 保存设置
const savePreferences = async () => {
  try {
    await updateNotificationPreference({
      enable_share_notifications: preferences.value.enable_share_notifications,
      enable_comment_notifications: preferences.value.enable_comment_notifications,
      enable_system_notifications: preferences.value.enable_system_notifications,
      notify_via_websocket: preferences.value.notify_via_websocket,
      notify_via_email: preferences.value.notify_via_email,
      email_frequency: preferences.value.email_frequency as EmailFrequency
    })
    ElMessage.success('设置已保存')
    await checkQuietHours()
  } catch (error: any) {
    console.error('保存通知设置失败:', error)
    ElMessage.error(error.response?.data?.detail || '保存通知设置失败')
    // 重新加载以恢复原始值
    await loadPreferences()
  }
}

// 切换静默时段
const toggleQuietHours = async () => {
  if (quietHoursEnabled.value) {
    // 启用静默时段，如果没有设置时间，设置默认值
    if (!preferences.value.quiet_hours_start) {
      preferences.value.quiet_hours_start = '22:00'
    }
    if (!preferences.value.quiet_hours_end) {
      preferences.value.quiet_hours_end = '08:00'
    }
  } else {
    // 禁用静默时段
    preferences.value.quiet_hours_start = null
    preferences.value.quiet_hours_end = null
  }
  await saveQuietHours()
}

// 保存静默时段
const saveQuietHours = async () => {
  try {
    await updateNotificationPreference({
      quiet_hours_start: preferences.value.quiet_hours_start,
      quiet_hours_end: preferences.value.quiet_hours_end
    })
    ElMessage.success('静默时段设置已保存')
    await checkQuietHours()
  } catch (error: any) {
    console.error('保存静默时段失败:', error)
    ElMessage.error(error.response?.data?.detail || '保存静默时段失败')
    await loadPreferences()
  }
}

// 重置为默认设置
const resetToDefault = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要将通知设置重置为默认值吗？',
      '确认重置',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    isLoading.value = true
    const response = await resetNotificationPreference()
    preferences.value = response
    ElMessage.success('已重置为默认设置')
    await checkQuietHours()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('重置通知设置失败:', error)
      ElMessage.error(error.response?.data?.detail || '重置通知设置失败')
    }
  } finally {
    isLoading.value = false
  }
}

// 格式化时间
const formatTime = (timeString: string | null) => {
  if (!timeString) return '-'
  const date = new Date(timeString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  loadPreferences()
})
</script>

<style scoped>
.notification-settings {
  padding: 24px;
  max-width: 800px;
  margin: 0 auto;
}

h2 {
  margin-bottom: 24px;
  color: #303133;
}

h3 {
  margin-bottom: 16px;
  color: #606266;
  font-size: 16px;
  font-weight: 600;
}

.settings-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section {
  margin-bottom: 16px;
}

.section-description {
  color: #909399;
  font-size: 14px;
  margin-bottom: 16px;
}

.description {
  color: #909399;
  font-size: 12px;
  margin-top: 4px;
}

.quiet-hours-status {
  margin-top: 16px;
}

.last-updated {
  color: #909399;
  font-size: 12px;
  text-align: right;
}
</style>
