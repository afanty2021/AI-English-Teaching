<template>
  <div :class="['conversation-status', statusClass]">
    <!-- 状态图标 -->
    <div class="status-icon-wrapper">
      <el-icon
        v-if="status === 'connecting'"
        class="is-loading"
      >
        <Loading />
      </el-icon>
      <component
        :is="statusIcon"
        v-else-if="statusIcon"
        class="status-icon"
      />
      <div
        v-else
        class="status-placeholder"
      ></div>
    </div>

    <!-- 状态文本 -->
    <div class="status-text">
      <span class="status-label">{{ statusText }}</span>
      <span
        v-if="showProgress"
        class="status-progress"
      >
        {{ messageCount }}/{{ targetMessages }}
      </span>
    </div>

    <!-- 进度条 -->
    <el-progress
      v-if="showProgress"
      :percentage="progressPercentage"
      :stroke-width="4"
      :show-text="false"
      :color="progressColor"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  Clock,
  SuccessFilled,
  WarningFilled,
  Loading,
  Microphone
} from '@element-plus/icons-vue'

interface Props {
  status: 'in_progress' | 'completed' | 'abandoned' | 'connecting' | 'thinking' | 'listening'
  messageCount?: number
  targetMessages?: number
}

const props = withDefaults(defineProps<Props>(), {
  messageCount: 0,
  targetMessages: 10
})

// 状态图标映射
const statusIcons = {
  connecting: Clock,
  thinking: Loading,
  listening: Microphone,
  in_progress: Clock,
  completed: SuccessFilled,
  abandoned: WarningFilled
}

// 状态文本映射
const statusTexts = {
  connecting: '连接中...',
  thinking: 'AI 思考中...',
  listening: '正在听...',
  in_progress: '进行中',
  completed: '已完成',
  abandoned: '已放弃'
}

// 状态样式类
const statusClass = computed(() => {
  return `status-${props.status}`
})

const statusIcon = computed(() => statusIcons[props.status])

const statusText = computed(() => statusTexts[props.status] || props.status)

// 是否显示进度
const showProgress = computed(() => {
  return props.status === 'in_progress' &&
         props.messageCount > 0 &&
         props.targetMessages > 0
})

// 进度百分比
const progressPercentage = computed(() => {
  if (!showProgress.value) return 0
  return Math.min((props.messageCount / props.targetMessages) * 100, 100)
})

// 进度条颜色
const progressColor = computed(() => {
  const percentage = progressPercentage.value
  if (percentage >= 100) return 'success'
  if (percentage >= 80) return 'primary'
  if (percentage >= 50) return 'warning'
  return 'exception'
})
</script>

<style scoped>
.conversation-status {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  border-radius: 8px;
  background: var(--el-fill-color-blank);
  transition: all 0.3s;
}

.status-connecting,
.status-thinking {
  border-left: 3px solid var(--el-color-warning);
}

.status-listening {
  border-left: 3px solid var(--el-color-primary);
}

.status-in_progress {
  border-left: 3px solid var(--el-color-info);
}

.status-completed {
  border-left: 3px solid var(--el-color-success);
}

.status-abandoned {
  border-left: 3px solid var(--el-color-danger);
}

.status-icon-wrapper {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-icon {
  font-size: 20px;
}

.status-connecting .status-icon {
  color: var(--el-color-warning);
  animation: pulse 1.5s ease-in-out infinite;
}

.status-thinking .status-icon {
  color: var(--el-color-info);
  animation: spin 1s linear infinite;
}

.status-listening .status-icon {
  color: var(--el-color-primary);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.status-placeholder {
  width: 16px;
  height: 16px;
}

.status-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.status-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.status-progress {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.el-progress {
  margin-top: 4px;
}
</style>
