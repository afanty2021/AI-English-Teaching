<template>
  <div
    class="confidence-indicator"
    :class="confidenceClass"
  >
    <div class="confidence-bar">
      <div
        class="confidence-fill"
        :style="{ width: `${confidence * 100}%` }"
      ></div>
    </div>
    <span class="confidence-text">{{ confidenceText }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

/**
 * 语音识别置信度显示组件
 * 用于实时显示语音识别的置信度水平
 */
interface Props {
  /** 置信度值 (0-1之间) */
  confidence: number
}

const props = defineProps<Props>()

/**
 * 根据置信度值计算对应的CSS类名
 * @returns 'high' | 'medium' | 'low'
 */
const confidenceClass = computed(() => {
  if (props.confidence >= 0.8) return 'high'
  if (props.confidence >= 0.5) return 'medium'
  return 'low'
})

/**
 * 根据置信度值获取对应的文本描述
 * @returns 中文置信度描述
 */
const confidenceText = computed(() => {
  if (props.confidence >= 0.8) return '高置信度'
  if (props.confidence >= 0.5) return '中置信度'
  return '低置信度'
})
</script>

<style scoped>
.confidence-indicator {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.confidence-bar {
  width: 80px;
  height: 6px;
  background: var(--el-border-color);
  border-radius: 3px;
  overflow: hidden;
}

.confidence-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.high .confidence-fill {
  background: var(--el-color-success);
}

.medium .confidence-fill {
  background: var(--el-color-warning);
}

.low .confidence-fill {
  background: var(--el-color-danger);
}

.confidence-text {
  min-width: 60px;
}
</style>
