<!--
  导出进度对话框组件
  显示导出任务进度、状态和操作按钮
-->
<template>
  <el-dialog
    :model-value="visible"
    title="导出进度"
    width="500px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="status !== 'processing'"
    @close="handleClose"
  >
    <!-- 进度显示 -->
    <div class="progress-content">
      <!-- 连接状态 -->
      <div
        v-if="wsState !== 'connected' && status === 'processing'"
        class="connection-status"
      >
        <el-icon class="is-loading">
          <Loading />
        </el-icon>
        <span>正在连接服务器...</span>
      </div>

      <!-- 连接重试提示 -->
      <div
        v-if="reconnecting"
        class="connection-status"
      >
        <el-icon class="is-loading">
          <Loading />
        </el-icon>
        <span>连接中断，正在重新连接... ({{ reconnectAttempts }}/5)</span>
      </div>

      <!-- 教案标题 -->
      <div class="lesson-title">
        <el-icon><Document /></el-icon>
        <span>{{ lessonTitle }}</span>
      </div>

      <!-- 当前阶段 -->
      <div class="current-stage">
        <el-tag :type="getStageType(currentStage)">
          {{ getStageLabel(currentStage) }}
        </el-tag>
        <span class="stage-message">{{ stageMessage || getProgressStageText(progress) }}</span>
      </div>

      <!-- 进度条 -->
      <div class="progress-bar-wrapper">
        <el-progress
          :percentage="progress"
          :status="getProgressStatus()"
          :stroke-width="12"
          :indeterminate="progress === 0 && status === 'processing'"
        >
          <template #default="{ percentage }">
            <span class="progress-text">{{ percentage }}%</span>
          </template>
        </el-progress>
      </div>

      <!-- 状态信息 -->
      <div class="status-info">
        <div class="info-item">
          <span class="label">格式：</span>
          <el-tag
            size="small"
            type="info"
          >
            {{ getFormatLabel(format) }}
          </el-tag>
        </div>
        <div class="info-item">
          <span class="label">状态：</span>
          <el-tag
            :type="getStatusTagType(status)"
            size="small"
          >
            {{ getStatusLabel(status) }}
          </el-tag>
        </div>
        <div
          v-if="estimatedTime > 0 && status === 'processing'"
          class="info-item"
        >
          <span class="label">预计剩余：</span>
          <span class="time-value">{{ formatTime(estimatedTime) }}</span>
        </div>
      </div>

      <!-- 错误信息 -->
      <el-alert
        v-if="status === 'failed' && errorMessage"
        type="error"
        :title="errorMessage"
        :closable="false"
        show-icon
        class="error-alert"
      />

      <!-- 成功信息 -->
      <el-alert
        v-if="status === 'completed'"
        type="success"
        title="导出完成！"
        :closable="false"
        show-icon
        class="success-alert"
      >
        <template #default>
          <p>文件已准备就绪，您可以点击下方按钮下载。</p>
        </template>
      </el-alert>
    </div>

    <!-- 操作按钮 -->
    <template #footer>
      <div class="dialog-footer">
        <el-button
          v-if="status === 'processing'"
          type="danger"
          :icon="CloseBold"
          @click="handleCancel"
        >
          取消导出
        </el-button>

        <el-button
          v-if="status === 'failed'"
          type="primary"
          :icon="RefreshRight"
          @click="handleRetry"
        >
          重试
        </el-button>

        <el-button
          v-if="status === 'completed'"
          type="primary"
          :icon="Download"
          @click="handleDownload"
        >
          下载文件
        </el-button>

        <el-button
          v-if="status === 'completed'"
          @click="handleClose"
        >
          关闭
        </el-button>

        <el-button
          v-if="status === 'failed'"
          @click="handleClose"
        >
          关闭
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, onBeforeUnmount } from 'vue'
import {
  Loading,
  Download,
  CloseBold,
  RefreshRight,
  Document
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  connectExportWebSocket,
  WebSocketState
} from '@/utils/exportWebSocket'
import ExportWebSocket from '@/utils/exportWebSocket'
import type { ExportFormat } from '@/types/lessonExport'
import type { ExportProgressEvent } from '@/types/lessonExport'

// 浏览器全局变量类型声明

/**
 * 进度阶段映射
 * 根据进度百分比返回对应的阶段文本
 */
const PROGRESS_STAGES: Record<number, string> = {
  5: '正在加载数据...',
  20: '正在渲染内容...',
  50: '正在生成文档...',
  80: '正在保存文件...',
  90: '即将完成...',
  100: '导出完成！'
}

interface Props {
  visible: boolean
  taskId: string
  lessonTitle: string
  format: ExportFormat
  initialProgress?: number
  initialStatus?: 'pending' | 'processing' | 'completed' | 'failed'
  initialErrorMessage?: string
}

interface Emits {
  'update:visible': [value: boolean]
  complete: [downloadUrl: string]
  error: [errorMessage: string]
  cancel: []
  retry: []
  download: []
}

const props = withDefaults(defineProps<Props>(), {
  initialProgress: 0,
  initialStatus: 'processing',
  initialErrorMessage: ''
})

const emit = defineEmits<Emits>()

// 状态
const progress = ref(props.initialProgress)
const status = ref<'pending' | 'processing' | 'completed' | 'failed'>(
  props.initialStatus
)
const errorMessage = ref(props.initialErrorMessage)
const currentStage = ref<string>('')
const stageMessage = ref<string>('')
const wsState = ref<WebSocketState>(WebSocketState.DISCONNECTED)
const estimatedTime = ref(0) // 预计剩余时间（秒）
const reconnecting = ref(false) // 是否正在重连
const reconnectAttempts = ref(0) // 重连次数
const downloadUrl = ref('') // 下载链接

// WebSocket 连接
let ws: ExportWebSocket | null = null
let estimatedTimeTimer: ReturnType<typeof setInterval> | null = null

// 对话框可见性
watch(
  () => props.visible,
  (newVal) => {
    if (newVal && props.taskId) {
      initWebSocket()
    } else if (!newVal) {
      cleanup()
    }
  },
  { immediate: true }
)

// 更新外部可见性
watch([status, progress], () => {
  if (status.value === 'completed' || status.value === 'failed') {
    emit('update:visible', true)
  }
})

/**
 * 初始化 WebSocket 连接
 */
function initWebSocket(): void {
  // 清理旧连接
  cleanup()

  // 重置状态
  progress.value = props.initialProgress
  status.value = props.initialStatus
  errorMessage.value = props.initialErrorMessage
  currentStage.value = ''
  stageMessage.value = ''

  // 如果任务已完成或失败，不需要连接 WebSocket
  if (
    props.initialStatus === 'completed' ||
    props.initialStatus === 'failed'
  ) {
    return
  }

  // 连接 WebSocket
  connectExportWebSocket(props.taskId, {
    onProgress: handleProgress,
    onComplete: handleComplete,
    onError: handleError,
    onStateChange: handleStateChange
  })
    .then((connection) => {
      ws = connection
    })
    .catch((error) => {
      console.error('WebSocket 连接失败:', error)
      ElMessage.error('连接服务器失败，将使用轮询方式获取进度')
      // 可以在这里启动轮询降级方案
    })
}

/**
 * 处理进度更新
 * 同时处理进度和阶段更新（WebSocket 的 stage 事件也通过此回调传递）
 */
function handleProgress(event: ExportProgressEvent): void {
  // 处理进度百分比
  if (event.data.progress !== undefined) {
    const oldProgress = progress.value
    progress.value = event.data.progress

    // 更新预计剩余时间（简单估算）
    if (event.data.progress > 0 && event.data.progress < 100) {
      updateEstimatedTime(oldProgress, event.data.progress)
    }
  }

  // 处理阶段信息（WebSocket 的 stage 类型事件）
  if (event.data.stage) {
    currentStage.value = event.data.stage
  }
  if (event.data.message) {
    stageMessage.value = event.data.message
  }
  if (event.data.stage_progress !== undefined) {
    progress.value = event.data.stage_progress
  }
}

/**
 * 处理完成事件
 */
function handleComplete(event: ExportProgressEvent): void {
  status.value = 'completed'
  progress.value = 100
  estimatedTime.value = 0
  if (event.data.message) {
    stageMessage.value = event.data.message
  }
  if (event.data.download_url) {
    downloadUrl.value = event.data.download_url
    emit('complete', event.data.download_url)
  }
  ElMessage.success('导出完成！')
}

/**
 * 处理错误事件
 */
function handleError(event: ExportProgressEvent): void {
  status.value = 'failed'
  estimatedTime.value = 0
  if (event.data.error) {
    errorMessage.value = event.data.error
    emit('error', event.data.error)
  }
  ElMessage.error('导出失败')
}

/**
 * 处理状态变化
 */
function handleStateChange(state: WebSocketState): void {
  wsState.value = state

  // 处理重连状态
  if (state === WebSocketState.CONNECTING && ws?.isConnected() === false) {
    reconnecting.value = true
    reconnectAttempts.value++
  } else if (state === WebSocketState.CONNECTED) {
    reconnecting.value = false
    reconnectAttempts.value = 0
  }
}

/**
 * 更新预计剩余时间
 */
function updateEstimatedTime(oldProgress: number, newProgress: number): void {
  // 清除旧定时器
  if (estimatedTimeTimer) {
    clearInterval(estimatedTimeTimer)
    estimatedTimeTimer = null
  }

  // 计算剩余时间（简单线性估算）
  const progressDiff = newProgress - oldProgress
  if (progressDiff > 0) {
    // 假设每秒更新一次，计算剩余时间
    const remainingProgress = 100 - newProgress
    const estimatedSeconds = (remainingProgress / progressDiff)

    // 更新显示
    estimatedTime.value = Math.max(1, Math.round(estimatedSeconds))

    // 启动倒计时定时器
    estimatedTimeTimer = setInterval(() => {
      if (estimatedTime.value > 0) {
        estimatedTime.value--
      } else {
        if (estimatedTimeTimer) {
          clearInterval(estimatedTimeTimer)
          estimatedTimeTimer = null
        }
      }
    }, 1000)
  }
}

/**
 * 获取进度阶段文本
 */
function getProgressStageText(progress: number): string {
  // 找到最接近的阶段
  const stages = Object.keys(PROGRESS_STAGES).map(Number).sort((a, b) => a - b)

  for (const stage of stages) {
    if (progress <= stage) {
      return PROGRESS_STAGES[stage] || '处理中...'
    }
  }

  return PROGRESS_STAGES[100] || '处理中...'
}

/**
 * 格式化时间显示
 */
function formatTime(seconds: number): string {
  if (seconds < 60) {
    return `${seconds}秒`
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60)
    return `${minutes}分钟`
  } else {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return `${hours}小时${minutes}分钟`
  }
}

/**
 * 获取进度状态
 */
function getProgressStatus():
  | 'success'
  | 'exception'
  | 'warning'
  | undefined {
  if (status.value === 'completed') {
    return 'success'
  }
  if (status.value === 'failed') {
    return 'exception'
  }
  return undefined
}

/**
 * 获取格式标签
 */
function getFormatLabel(format: ExportFormat): string {
  const labels: Record<ExportFormat, string> = {
    word: 'Word 文档',
    pdf: 'PDF 文档',
    pptx: 'PPT 演示',
    markdown: 'Markdown'
  }
  return labels[format] || format
}

/**
 * 获取状态标签
 */
function getStatusLabel(s: 'pending' | 'processing' | 'completed' | 'failed'): string {
  const labels: Record<string, string> = {
    pending: '等待中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return labels[s] || s
}

/**
 * 获取状态标签类型
 */
function getStatusTagType(
  s: 'pending' | 'processing' | 'completed' | 'failed'
): 'info' | 'warning' | 'success' | 'danger' {
  const types: Record<string, 'info' | 'warning' | 'success' | 'danger'> = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return types[s] || 'info'
}

/**
 * 获取阶段标签
 */
function getStageLabel(stage: string): string {
  const labels: Record<string, string> = {
    preparing: '准备中',
    rendering: '渲染中',
    generating: '生成中',
    uploading: '上传中',
    finalizing: '完成中'
  }
  return labels[stage] || stage
}

/**
 * 获取阶段类型
 */
function getStageType(stage: string): 'info' | 'warning' | 'success' {
  const types: Record<string, 'info' | 'warning' | 'success'> = {
    preparing: 'info',
    rendering: 'warning',
    generating: 'warning',
    uploading: 'warning',
    finalizing: 'success'
  }
  return types[stage] || 'info'
}

/**
 * 取消导出
 */
async function handleCancel(): Promise<void> {
  try {
    await ElMessageBox.confirm('确定要取消导出吗？', '确认', {
      type: 'warning'
    })
    emit('cancel')
    handleClose()
  } catch {
    // 用户取消
  }
}

/**
 * 重试
 */
function handleRetry(): void {
  emit('retry')
  handleClose()
}

/**
 * 下载文件
 */
function handleDownload(): void {
  emit('download')
}

/**
 * 关闭对话框
 */
function handleClose(): void {
  emit('update:visible', false)
}

/**
 * 清理资源
 */
function cleanup(): void {
  if (ws) {
    ws.close()
    ws = null
  }

  if (estimatedTimeTimer) {
    clearInterval(estimatedTimeTimer)
    estimatedTimeTimer = null
  }

  // 重置状态
  reconnecting.value = false
  reconnectAttempts.value = 0
  estimatedTime.value = 0
}

// 组件卸载时清理
onBeforeUnmount(() => {
  cleanup()
})

// 暴露方法供父组件调用
defineExpose({
  updateProgress: (value: number) => {
    progress.value = value
  },
  updateStatus: (
    s: 'pending' | 'processing' | 'completed' | 'failed',
    msg?: string
  ) => {
    status.value = s
    if (msg) {
      errorMessage.value = msg
    }
  }
})
</script>

<style scoped>
.progress-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 8px 0;
}

/* 连接状态 */
.connection-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

/* 教案标题 */
.lesson-title {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: var(--el-fill-color-blank);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
  font-size: 15px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

/* 当前阶段 */
.current-stage {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--el-fill-color-blank);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
}

.stage-message {
  flex: 1;
  font-size: 14px;
  color: var(--el-text-color-regular);
}

/* 进度条 */
.progress-bar-wrapper {
  padding: 0 8px;
}

.progress-text {
  font-size: 14px;
  font-weight: 600;
}

/* 状态信息 */
.status-info {
  display: flex;
  gap: 24px;
  padding: 12px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
  flex-wrap: wrap;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.info-item .label {
  font-weight: 500;
  color: var(--el-text-color-secondary);
}

.time-value {
  font-weight: 600;
  color: var(--el-color-primary);
}

/* 错误提示 */
.error-alert {
  margin: 0;
}

/* 成功提示 */
.success-alert {
  margin: 0;
}

.success-alert p {
  margin: 8px 0 0 0;
  font-size: 13px;
  color: var(--el-text-color-regular);
}

/* 对话框底部 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@media (max-width: 768px) {
  .status-info {
    flex-direction: column;
    gap: 12px;
  }

  .dialog-footer {
    flex-direction: column;
  }

  .dialog-footer .el-button {
    width: 100%;
  }
}
</style>
