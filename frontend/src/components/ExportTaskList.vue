<!--
  导出任务列表组件
  显示导出任务的状态和进度
-->
<template>
  <div class="export-task-list">
    <!-- 任务列表 -->
    <div v-if="tasks.length > 0" class="tasks-container">
      <div
        v-for="task in tasks"
        :key="task.id"
        class="task-item"
        :class="`status-${task.status}`"
      >
        <!-- 任务信息 -->
        <div class="task-info">
          <div class="task-header">
            <h4 class="task-title">{{ task.lesson_title }}</h4>
            <el-tag :type="getStatusType(task.status)" size="small">
              {{ getStatusText(task.status) }}
            </el-tag>
          </div>

          <div class="task-meta">
            <span class="format-badge">
              {{ getFormatLabel(task.format) }}
            </span>
            <span class="task-time">{{ formatTime(task.created_at) }}</span>
          </div>

          <!-- 错误信息 -->
          <div v-if="task.status === 'failed' && task.error_message" class="task-error">
            <el-icon><Warning /></el-icon>
            <span>{{ task.error_message }}</span>
          </div>
        </div>

        <!-- 进度条 -->
        <div v-if="task.status === 'processing'" class="task-progress">
          <el-progress
            :percentage="task.progress"
            :indeterminate="task.progress === 0"
            :stroke-width="6"
          />
        </div>

        <!-- 操作按钮 -->
        <div class="task-actions">
          <!-- 下载按钮（已完成） -->
          <el-button
            v-if="task.status === 'completed'"
            type="primary"
            size="small"
            :icon="Download"
            @click="handleDownload(task)"
          >
            下载
          </el-button>

          <!-- 取消按钮（处理中） -->
          <el-button
            v-if="task.status === 'processing'"
            size="small"
            :icon="Close"
            @click="handleCancel(task)"
          >
            取消
          </el-button>

          <!-- 重试按钮（失败） -->
          <el-button
            v-if="task.status === 'failed'"
            type="warning"
            size="small"
            :icon="RefreshRight"
            @click="handleRetry(task)"
          >
            重试
          </el-button>

          <!-- 删除按钮 -->
          <el-button
            size="small"
            :icon="Delete"
            @click="handleDelete(task)"
          >
            删除
          </el-button>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <el-empty
      v-else
      description="暂无导出任务"
      :image-size="100"
    >
      <p style="color: var(--el-text-color-secondary); font-size: 13px;">
        选择教案并配置导出选项后，点击"开始导出"创建任务
      </p>
    </el-empty>
  </div>
</template>

<script setup lang="ts">
import { Download, Close, Delete, RefreshRight, Warning } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import type { ExportTask } from '@/types/lessonExport'

interface Props {
  tasks: ExportTask[]
}

interface Emits {
  download: [task: ExportTask]
  cancel: [task: ExportTask]
  retry: [task: ExportTask]
  delete: [task: ExportTask]
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 获取状态对应的标签类型
const getStatusType = (status: string) => {
  const types: Record<string, any> = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    pending: '等待中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return texts[status] || status
}

// 获取格式标签
const getFormatLabel = (format: string) => {
  const labels: Record<string, string> = {
    word: 'Word',
    pdf: 'PDF',
    pptx: 'PPT',
    markdown: 'Markdown'
  }
  return labels[format] || format
}

// 格式化时间
const formatTime = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  // 小于1分钟
  if (diff < 60000) {
    return '刚刚'
  }

  // 小于1小时
  if (diff < 3600000) {
    const minutes = Math.floor(diff / 60000)
    return `${minutes} 分钟前`
  }

  // 小于1天
  if (diff < 86400000) {
    const hours = Math.floor(diff / 3600000)
    return `${hours} 小时前`
  }

  // 大于1天
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 处理下载
const handleDownload = (task: ExportTask) => {
  emit('download', task)
}

// 处理取消
const handleCancel = async (task: ExportTask) => {
  try {
    await ElMessageBox.confirm('确定要取消此导出任务吗？', '确认', {
      type: 'warning'
    })
    emit('cancel', task)
  } catch {
    // 用户取消
  }
}

// 处理重试
const handleRetry = (task: ExportTask) => {
  emit('retry', task)
}

// 处理删除
const handleDelete = async (task: ExportTask) => {
  try {
    await ElMessageBox.confirm('确定要删除此任务记录吗？', '确认', {
      type: 'warning'
    })
    emit('delete', task)
  } catch {
    // 用户取消
  }
}
</script>

<style scoped>
.export-task-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tasks-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-item {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background: var(--el-fill-color-blank);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  transition: all 0.3s ease;
}

.task-item:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.task-item.status-completed {
  border-left: 3px solid var(--el-color-success);
}

.task-item.status-failed {
  border-left: 3px solid var(--el-color-danger);
}

.task-item.status-processing {
  border-left: 3px solid var(--el-color-warning);
}

/* 任务信息 */
.task-info {
  flex: 1;
}

.task-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.task-title {
  flex: 1;
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.task-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.format-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  background: var(--el-fill-color-light);
  border-radius: 4px;
  font-weight: 500;
}

.task-error {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  margin-top: 8px;
  background: var(--el-color-danger-light-9);
  border-radius: 6px;
  color: var(--el-color-danger);
  font-size: 13px;
}

/* 进度条 */
.task-progress {
  padding: 0 4px;
}

/* 操作按钮 */
.task-actions {
  display: flex;
  gap: 8px;
  padding-top: 4px;
  border-top: 1px solid var(--el-border-color-lighter);
}

/* 响应式 */
@media (max-width: 768px) {
  .task-actions {
    flex-wrap: wrap;
  }

  .task-actions .el-button {
    flex: 1;
    min-width: 0;
  }
}
</style>
