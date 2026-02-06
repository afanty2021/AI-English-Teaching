<template>
  <div v-if="visible" class="export-progress">
    <div class="progress-card">
      <div class="card-header">
        <div class="header-title">
          <el-icon v-if="status === 'processing'" class="is-loading"><Loading /></el-icon>
          <el-icon v-else-if="status === 'completed'"><CircleCheck /></el-icon>
          <el-icon v-else-if="status === 'failed'"><CircleClose /></el-icon>
          <el-icon v-else><Clock /></el-icon>
          <span>{{ getStatusTitle() }}</span>
        </div>
        <el-button v-if="showClose" text circle size="small" @click="handleClose">
          <el-icon><Close /></el-icon>
        </el-button>
      </div>

      <div class="card-content">
        <!-- 进度条 -->
        <div class="progress-section" v-if="status === 'processing'">
          <el-progress
            :percentage="progress"
            :stroke-width="10"
            :status="getProgressStatus()"
          />
          <div class="progress-info">
            <span class="progress-percent">{{ progress }}%</span>
            <span class="progress-message">{{ message || '正在处理...' }}</span>
          </div>
        </div>

        <!-- 完成状态 -->
        <div class="completed-section" v-else-if="status === 'completed'">
          <div class="completed-icon">
            <el-icon :size="48" color="#67C23A"><CircleCheck /></el-icon>
          </div>
          <p class="completed-message">导出完成！</p>
          <el-button type="primary" @click="handleDownload">
            <el-icon><Download /></el-icon>
            下载文件
          </el-button>
        </div>

        <!-- 失败状态 -->
        <div class="failed-section" v-else-if="status === 'failed'">
          <div class="failed-icon">
            <el-icon :size="48" color="#F56C6C"><CircleClose /></el-icon>
          </div>
          <p class="failed-message">{{ errorMessage || '导出失败，请稍后重试' }}</p>
          <div class="failed-actions">
            <el-button @click="handleRetry" v-if="canRetry">
              <el-icon><Refresh /></el-icon>
              重新导出
            </el-button>
          </div>
        </div>

        <!-- 等待状态 -->
        <div class="pending-section" v-else>
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>{{ message || '正在等待处理...' }}</span>
        </div>

        <!-- 批量导出信息 -->
        <div v-if="isBatch && batchInfo" class="batch-info">
          <div class="batch-progress">
            <span>已完成: {{ batchInfo.completed }} / {{ batchInfo.total }}</span>
          </div>
          <div class="batch-details">
            <span v-if="batchInfo.failed > 0" class="batch-failed">
              失败: {{ batchInfo.failed }}
            </span>
            <span class="batch-remaining">
              预计剩余: {{ batchInfo.estimatedTime }}秒
            </span>
          </div>
        </div>
      </div>

      <!-- 底部操作 -->
      <div class="card-footer" v-if="showActions">
        <el-button
          v-if="canCancel && status === 'processing'"
          type="danger"
          size="small"
          @click="handleCancel"
        >
          <el-icon><Close /></el-icon>
          取消导出
        </el-button>
        <el-button
          v-if="showBackdrop"
          size="small"
          @click="handleBackground"
        >
          <el-icon><Bottom /></el-icon>
          后台运行
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  Loading,
  CircleCheck,
  CircleClose,
  Clock,
  Close,
  Download,
  Refresh,
  Bottom
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { ExportProgressInfo, AsyncTaskStatus } from '@/types/report'

// Props
interface Props {
  taskId: string
  showBackdrop?: boolean
  showClose?: boolean
  showActions?: boolean
  autoCloseDelay?: number
}

const props = withDefaults(defineProps<Props>(), {
  showBackdrop: true,
  showClose: false,
  showActions: true,
  autoCloseDelay: 3000
})

// Emits
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'cancel'): void
  (e: 'retry'): void
  (e: 'download', url: string): void
}>()

// 状态
const visible = ref(true)
const status = ref<AsyncTaskStatus>('pending')
const progress = ref(0)
const message = ref('')
const errorMessage = ref('')
const canCancel = ref(false)
const canRetry = ref(false)
const resultUrl = ref('')
const isBatch = ref(false)

// 批量信息
const batchInfo = ref<{
  total: number
  completed: number
  failed: number
  estimatedTime: number
} | null>(null)

// 轮询定时器
let pollTimer: ReturnType<typeof setInterval> | null = null
const POLL_INTERVAL = 2000 // 2秒轮询一次

// 获取状态标题
function getStatusTitle(): string {
  const titles: Record<AsyncTaskStatus, string> = {
    pending: '等待导出',
    processing: '正在导出',
    completed: '导出完成',
    failed: '导出失败',
    cancelled: '已取消'
  }
  return titles[status.value] || '未知状态'
}

// 获取进度条状态
function getProgressStatus(): 'success' | 'exception' | undefined {
  if (status.value === 'failed') return 'exception'
  if (status.value === 'completed') return 'success'
  return undefined
}

// 获取任务状态
async function fetchTaskStatus() {
  if (!props.taskId) return

  try {
    const response = await fetch(`/api/v1/tasks/${props.taskId}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    })

    if (!response.ok) {
      throw new Error('获取状态失败')
    }

    const result = await response.json()
    if (result.code === 0) {
      const data = result.data
      updateFromTaskData(data)
    }
  } catch (error) {
    console.error('获取任务状态失败:', error)
  }
}

// 更新任务数据
function updateFromTaskData(data: any) {
  status.value = data.status as AsyncTaskStatus
  progress.value = data.progress || 0
  message.value = data.message || ''
  errorMessage.value = data.error_message || ''
  resultUrl.value = data.result_url || ''

  // 检查是否可以取消或重试
  canCancel.value = status.value === 'processing'
  canRetry.value = status.value === 'failed'

  // 检查是否是批量导出
  if (data.task_type === 'batch_export' && data.result_details) {
    isBatch.value = true
    batchInfo.value = {
      total: data.result_details.total || 0,
      completed: data.result_details.completed || 0,
      failed: data.result_details.failed || 0,
      estimatedTime: data.result_details.estimatedTime || 0
    }
  } else {
    isBatch.value = false
    batchInfo.value = null
  }

  // 完成或失败时停止轮询
  if (status.value === 'completed' || status.value === 'failed') {
    stopPolling()

    // 自动关闭
    if (props.autoCloseDelay > 0 && status.value === 'completed') {
      setTimeout(() => {
        visible.value = false
        emit('close')
      }, props.autoCloseDelay)
    }
  }
}

// 开始轮询
function startPolling() {
  stopPolling()
  fetchTaskStatus() // 立即获取一次
  pollTimer = setInterval(fetchTaskStatus, POLL_INTERVAL)
}

// 停止轮询
function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

// 处理关闭
function handleClose() {
  visible.value = false
  stopPolling()
  emit('close')
}

// 处理取消
async function handleCancel() {
  try {
    const response = await fetch(`/api/v1/tasks/${props.taskId}/cancel`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    })

    const result = await response.json()
    if (result.code === 0) {
      ElMessage.success('已取消导出')
      status.value = 'cancelled'
      stopPolling()
    } else {
      throw new Error(result.message || '取消失败')
    }
  } catch (error) {
    console.error('取消导出失败:', error)
    ElMessage.error('取消失败，请稍后重试')
  }
  emit('cancel')
}

// 处理重试
function handleRetry() {
  emit('retry')
}

// 处理下载
function handleDownload() {
  if (resultUrl.value) {
    window.open(resultUrl.value, '_blank')
    emit('download', resultUrl.value)
  } else {
    ElMessage.warning('暂无可下载文件')
  }
}

// 处理后台运行
function handleBackground() {
  visible.value = false
  ElMessage.info('导出任务已在后台运行，可稍后在任务列表查看')
  emit('close')
}

// 初始化
onMounted(() => {
  if (status.value === 'pending' || status.value === 'processing') {
    startPolling()
  } else {
    // 如果已经有状态，直接获取一次
    fetchTaskStatus()
  }
})

// 清理
onUnmounted(() => {
  stopPolling()
})

// 暴露方法
defineExpose({
  updateStatus: updateFromTaskData,
  show: () => { visible.value = true },
  hide: () => { visible.value = false }
})
</script>

<style scoped lang="scss">
.export-progress {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 9999;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(100px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.progress-card {
  width: 320px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  overflow: hidden;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: #f5f7fa;
    border-bottom: 1px solid #ebeef5;

    .header-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 14px;
      font-weight: 500;
      color: #303133;
    }
  }

  .card-content {
    padding: 20px 16px;
  }

  .progress-section {
    .el-progress {
      margin-bottom: 12px;
    }

    .progress-info {
      display: flex;
      justify-content: space-between;
      font-size: 12px;
      color: #909399;

      .progress-percent {
        font-size: 20px;
        font-weight: bold;
        color: #409EFF;
      }
    }
  }

  .completed-section,
  .failed-section {
    text-align: center;

    .completed-icon,
    .failed-icon {
      margin-bottom: 12px;
    }

    .completed-message {
      font-size: 14px;
      color: #67C23A;
      margin-bottom: 16px;
    }

    .failed-message {
      font-size: 13px;
      color: #F56C6C;
      margin-bottom: 16px;
    }

    .failed-actions {
      display: flex;
      justify-content: center;
      gap: 12px;
    }
  }

  .pending-section {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    color: #909399;
    font-size: 13px;
  }

  .batch-info {
    margin-top: 16px;
    padding-top: 12px;
    border-top: 1px solid #ebeef5;
    font-size: 12px;

    .batch-progress {
      color: #606266;
      margin-bottom: 6px;
    }

    .batch-details {
      display: flex;
      justify-content: space-between;
      color: #909399;

      .batch-failed {
        color: #F56C6C;
      }
    }
  }

  .card-footer {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    padding: 12px 16px;
    background: #fafafa;
    border-top: 1px solid #ebeef5;
  }
}
</style>
