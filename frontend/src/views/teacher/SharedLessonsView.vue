<template>
  <div class="shared-lessons-page">
    <el-container>
      <el-header>
        <div class="header-content">
          <h1>分享的教案</h1>
          <div class="header-actions">
            <ShareNotificationBell />
            <div class="header-tabs">
              <el-radio-group
                v-model="activeTab"
                @change="handleTabChange"
              >
                <el-radio-button value="received">
                  分享给我的
                </el-radio-button>
                <el-radio-button value="given">
                  我分享的
                </el-radio-button>
              </el-radio-group>
            </div>
          </div>
        </div>
      </el-header>

      <el-main>
        <!-- 统计卡片 -->
        <div class="statistics-bar">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">
                {{ statistics.pending_count }}
              </div>
              <div class="stat-label">
                待接受
              </div>
            </div>
          </el-card>
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">
                {{ statistics.total_shared_by_me }}
              </div>
              <div class="stat-label">
                我分享的
              </div>
            </div>
          </el-card>
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">
                {{ statistics.accepted_count }}
              </div>
              <div class="stat-label">
                已接受
              </div>
            </div>
          </el-card>
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">
                {{ statistics.acceptance_rate }}%
              </div>
              <div class="stat-label">
                接受率
              </div>
            </div>
          </el-card>
        </div>

        <!-- 筛选栏 -->
        <div class="filter-bar">
          <el-select
            v-model="filterStatus"
            placeholder="状态筛选"
            clearable
            style="width: 120px"
            @change="loadShares"
          >
            <el-option
              v-for="status in SHARE_STATUSES"
              :key="status.value"
              :label="status.label"
              :value="status.value"
            />
          </el-select>
        </div>

        <!-- 分享列表 -->
        <el-card v-loading="isLoading">
          <el-empty
            v-if="!isLoading && shares.length === 0"
            description="暂无分享记录"
          >
            <el-button
              type="primary"
              @click="goToLessons"
            >
              浏览教案库
            </el-button>
          </el-empty>

          <div
            v-else
            class="shares-list"
          >
            <div
              v-for="share in shares"
              :key="share.id"
              class="share-card"
            >
              <!-- 分享信息 -->
              <div class="share-header">
                <div class="share-info">
                  <div class="share-title">
                    {{ share.lesson_plan.title }}
                  </div>
                  <div class="share-meta">
                    <el-tag
                      size="small"
                      :type="getLevelType(share.lesson_plan.level)"
                    >
                      {{ share.lesson_plan.level }}
                    </el-tag>
                    <el-tag
                      size="small"
                      :type="getPermissionType(share.permission)"
                    >
                      {{ getPermissionLabel(share.permission) }}
                    </el-tag>
                    <span class="share-date">{{ formatDate(share.created_at) }}</span>
                  </div>
                </div>

                <!-- 分享给我的：操作按钮 -->
                <template v-if="activeTab === 'received'">
                  <el-button
                    v-if="share.status === 'pending'"
                    type="primary"
                    size="small"
                    :loading="accepting === share.id"
                    @click="handleAccept(share)"
                  >
                    接受
                  </el-button>
                  <el-button
                    v-if="share.status === 'pending'"
                    size="small"
                    :loading="rejecting === share.id"
                    @click="handleReject(share)"
                  >
                    拒绝
                  </el-button>
                  <el-button
                    v-if="share.status === 'accepted'"
                    type="primary"
                    size="small"
                    @click="viewLesson(share.lesson_plan.id)"
                  >
                    查看
                  </el-button>
                </template>

                <!-- 我分享的：取消按钮 -->
                <template v-else>
                  <el-dropdown @command="(cmd: string) => handleAction(cmd, share)">
                    <el-button size="small">
                      操作 <el-icon class="el-icon--right">
                        <ArrowDown />
                      </el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item
                          command="view"
                          :icon="View"
                        >
                          查看
                        </el-dropdown-item>
                        <el-dropdown-item
                          v-if="share.status === 'pending'"
                          command="cancel"
                          :icon="Close"
                        >
                          取消分享
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </template>
              </div>

              <!-- 分享状态和详情 -->
              <div class="share-body">
                <div class="share-status">
                  <el-tag :type="getStatusType(share.status)">
                    {{ getStatusLabel(share.status) }}
                  </el-tag>
                  <span
                    v-if="share.expires_at"
                    class="expires-info"
                  >
                    {{ getExpiresText(share.expires_at) }}
                  </span>
                </div>

                <div class="share-people">
                  <div class="person-info">
                    <span class="label">{{ activeTab === 'received' ? '分享者' : '接收者' }}:</span>
                    <span class="name">
                      {{ activeTab === 'received' ? share.shared_by.full_name || share.shared_by.username : share.shared_to.full_name || share.shared_to.username }}
                    </span>
                  </div>
                </div>

                <div
                  v-if="share.message"
                  class="share-message"
                >
                  <el-icon><ChatLineSquare /></el-icon>
                  <span>{{ share.message }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 分页 -->
          <div
            v-if="total > 0"
            class="pagination-wrapper"
          >
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :total="total"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="loadShares"
              @current-change="loadShares"
            />
          </div>
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowDown,
  View,
  Close,
  ChatLineSquare
} from '@element-plus/icons-vue'
import {
  getSharedWithMe,
  getSharedByMe,
  acceptShare,
  rejectShare,
  cancelShare
} from '@/api/lessonShare'
import { getLessonPlan } from '@/api/lesson'
import { getShareStatistics } from '@/api/user'
import { SHARE_STATUSES } from '@/api/lessonShare'
import type { LessonPlanShare } from '@/api/lessonShare'
import ShareNotificationBell from '@/components/ShareNotificationBell.vue'

const router = useRouter()

// 状态
const activeTab = ref<'received' | 'given'>('received')
const isLoading = ref(false)
const shares = ref<LessonPlanShare[]>([])
const filterStatus = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 操作状态
const accepting = ref<string | null>(null)
const rejecting = ref<string | null>(null)

// 统计数据
const statistics = ref({
  pending_count: 0,
  total_shared_by_me: 0,
  total_shared_to_me: 0,
  accepted_count: 0,
  rejected_count: 0,
  acceptance_rate: 0
})

// 加载分享列表
const loadShares = async () => {
  isLoading.value = true
  try {
    const apiFunc = activeTab.value === 'received' ? getSharedWithMe : getSharedByMe
    const response = await apiFunc({
      status: filterStatus.value || undefined,
      page: currentPage.value,
      page_size: pageSize.value
    })

    shares.value = response.shares
    total.value = response.total
  } catch (error) {
    console.error('加载分享列表失败:', error)
    ElMessage.error('加载分享列表失败')
  } finally {
    isLoading.value = false
  }
}

// 切换标签
const handleTabChange = () => {
  currentPage.value = 1
  filterStatus.value = ''
  loadShares()
}

// 接受分享
const handleAccept = async (share: LessonPlanShare) => {
  try {
    accepting.value = share.id
    await acceptShare(share.id)
    ElMessage.success('已接受分享')
    await loadShares()
    await loadStatistics()
  } catch (error: any) {
    console.error('接受分享失败:', error)
    ElMessage.error(error.response?.data?.detail || '接受分享失败')
  } finally {
    accepting.value = null
  }
}

// 拒绝分享
const handleReject = async (share: LessonPlanShare) => {
  try {
    rejecting.value = share.id
    await rejectShare(share.id)
    ElMessage.success('已拒绝分享')
    await loadShares()
    await loadStatistics()
  } catch (error: any) {
    console.error('拒绝分享失败:', error)
    ElMessage.error(error.response?.data?.detail || '拒绝分享失败')
  } finally {
    rejecting.value = null
  }
}

// 取消分享
const handleAction = async (command: string, share: LessonPlanShare) => {
  if (command === 'view') {
    await viewLesson(share.lesson_plan.id)
  } else if (command === 'cancel') {
    try {
      await ElMessageBox.confirm('确认取消此分享吗？', '取消分享')
      await cancelShare(share.id)
      ElMessage.success('已取消分享')
      await loadShares()
    } catch (error) {
      if (error !== 'cancel') {
        console.error('取消分享失败:', error)
        ElMessage.error('取消分享失败')
      }
    }
  }
}

// 查看教案
const viewLesson = async (lessonPlanId: string) => {
  try {
    await getLessonPlan(lessonPlanId)
    // TODO: 打开教案详情对话框
    router.push({ name: 'lessons', query: { id: lessonPlanId } })
  } catch (error) {
    console.error('加载教案详情失败:', error)
    ElMessage.error('加载教案详情失败')
  }
}

// 跳转到教案列表
const goToLessons = () => {
  router.push({ name: 'lessons' })
}

// 辅助函数
const getLevelType = (level: string) => {
  const typeMap: Record<string, string> = {
    A1: '',
    A2: 'success',
    B1: 'warning',
    B2: 'danger',
    C1: 'info',
    C2: 'primary'
  }
  return typeMap[level] || ''
}

const getPermissionType = (permission: string) => {
  const typeMap: Record<string, string> = {
    view: 'info',
    edit: 'warning',
    copy: 'success'
  }
  return typeMap[permission] || ''
}

const getPermissionLabel = (permission: string) => {
  const labelMap: Record<string, string> = {
    view: '仅查看',
    edit: '可编辑',
    copy: '可复制'
  }
  return labelMap[permission] || permission
}

const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    pending: 'warning',
    accepted: 'success',
    rejected: 'info',
    expired: 'info'
  }
  return typeMap[status] || ''
}

const getStatusLabel = (status: string) => {
  const statusItem = SHARE_STATUSES.find(s => s.value === status)
  return statusItem?.label || status
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return `${Math.floor(diff / 86400000)}天前`
}

const getExpiresText = (expiresAt: string) => {
  const expires = new Date(expiresAt)
  const now = new Date()
  const diff = expires.getTime() - now.getTime()

  if (diff < 0) return '已过期'
  if (diff < 86400000) return `剩余 ${Math.floor(diff / 3600000)} 小时`
  return `剩余 ${Math.floor(diff / 86400000)} 天`
}

// 初始化
onMounted(() => {
  loadShares()
  loadStatistics()
})

// 加载统计数据
const loadStatistics = async () => {
  try {
    const stats = await getShareStatistics()
    statistics.value = stats
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

// SHARE_STATUSES is automatically exposed to template in Vue 3 <script setup>
</script>

<style scoped>
.shared-lessons-page {
  height: 100%;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
}

.header-content h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-tabs {
  display: flex;
  gap: 16px;
}

.filter-bar {
  margin-bottom: 16px;
}

.statistics-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.stat-card {
  flex: 1;
  padding: 16px;
}

.stat-card :deep(.el-card__body) {
  padding: 0;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #409eff;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.shares-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.share-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.3s;
}

.share-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.share-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.share-info {
  flex: 1;
}

.share-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.share-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #909399;
}

.share-date {
  color: #909399;
}

.share-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.share-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.expires-info {
  font-size: 12px;
  color: #909399;
}

.share-people {
  font-size: 13px;
  color: #606266;
}

.person-info {
  display: flex;
  gap: 4px;
}

.person-info .label {
  color: #909399;
}

.person-info .name {
  font-weight: 500;
  color: #303133;
}

.share-message {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 13px;
  color: #606266;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>
