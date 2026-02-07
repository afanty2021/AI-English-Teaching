<template>
  <div class="notification-bell">
    <el-badge
      :value="notificationCount"
      :hidden="notificationCount === 0"
      type="danger"
    >
      <el-button
        :icon="Bell"
        circle
        @click="showNotifications = true"
      />
    </el-badge>

    <!-- 通知抽屉 -->
    <el-drawer
      v-model="showNotifications"
      title="分享通知"
      direction="rtl"
      size="400px"
    >
      <div v-loading="isLoading">
        <el-empty
          v-if="!isLoading && notifications.length === 0"
          description="暂无通知"
        />

        <div
          v-else
          class="notifications-list"
        >
          <div
            v-for="notification in notifications"
            :key="notification.id"
            class="notification-item"
          >
            <div class="notification-header">
              <el-icon class="notification-icon">
                <Share />
              </el-icon>
              <div class="notification-title">
                {{ notification.title }}
              </div>
              <div class="notification-time">
                {{ formatTime(notification.created_at) }}
              </div>
            </div>

            <div class="notification-content">
              {{ notification.content }}
            </div>

            <div class="notification-actions">
              <el-button
                type="primary"
                size="small"
                @click="viewLesson(notification.lesson_plan_id)"
              >
                查看
              </el-button>
              <el-button
                size="small"
                @click="acceptShare(notification.id)"
              >
                接受
              </el-button>
              <el-button
                size="small"
                @click="dismissNotification(notification.id)"
              >
                忽略
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Bell, Share } from '@element-plus/icons-vue'
import { getPendingNotifications } from '@/api/user'
import { acceptShare as apiAcceptShare } from '@/api/lessonShare'

const router = useRouter()

const showNotifications = ref(false)
const isLoading = ref(false)
const notifications = ref<any[]>([])
const notificationCount = ref(0)

let pollingTimer: ReturnType<typeof setInterval> | null = null

// 加载通知
const loadNotifications = async () => {
  try {
    const response = await getPendingNotifications()
    notifications.value = response.notifications
    notificationCount.value = response.count
  } catch (error) {
    console.error('加载通知失败:', error)
  }
}

// 开始轮询
const startPolling = () => {
  // 立即加载一次
  loadNotifications()
  // 每30秒轮询一次
  pollingTimer = setInterval(loadNotifications, 30000)
}

// 停止轮询
const stopPolling = () => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
}

// 查看教案
const viewLesson = (lessonPlanId: string) => {
  showNotifications.value = false
  router.push({ name: 'lessons', query: { id: lessonPlanId } })
}

// 接受分享
const acceptShare = async (shareId: string) => {
  try {
    await apiAcceptShare(shareId)
    ElMessage.success('已接受分享')
    await loadNotifications()
  } catch (error: any) {
    console.error('接受分享失败:', error)
    ElMessage.error(error.response?.data?.detail || '接受分享失败')
  }
}

// 忽略通知
const dismissNotification = (id: string) => {
  notifications.value = notifications.value.filter(n => n.id !== id)
  notificationCount.value = notifications.value.length
}

// 格式化时间
const formatTime = (dateString: string | null) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return `${Math.floor(diff / 86400000)}天前`
}

onMounted(() => {
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})

// 暴露刷新方法供外部调用
defineExpose({
  refresh: loadNotifications
})
</script>

<style scoped>
.notification-bell {
  display: inline-block;
}

.notifications-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.notification-item {
  padding: 16px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
  transition: all 0.3s;
}

.notification-item:hover {
  background: var(--el-fill-color);
}

.notification-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.notification-icon {
  color: #409eff;
  font-size: 18px;
}

.notification-title {
  flex: 1;
  font-weight: 600;
  color: #303133;
}

.notification-time {
  font-size: 12px;
  color: #909399;
}

.notification-content {
  margin-bottom: 12px;
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
}

.notification-actions {
  display: flex;
  gap: 8px;
}
</style>
