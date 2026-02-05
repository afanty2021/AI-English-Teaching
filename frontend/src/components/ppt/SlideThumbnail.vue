<!--
  PPT 幻灯片缩略图组件
  用于显示幻灯片的缩略图预览，支持点击切换
-->
<template>
  <div
    class="slide-thumbnail"
    :class="{ active: isActive, disabled: disabled }"
    @click="handleClick"
  >
    <!-- 缩略图内容 -->
    <div class="thumbnail-content">
      <!-- 幻灯片编号 -->
      <span class="slide-number">{{ number }}</span>

      <!-- 幻灯片标题 -->
      <div class="slide-title" :title="slide.title">
        {{ slide.title || `幻灯片 ${number}` }}
      </div>

      <!-- 幻灯片预览内容 -->
      <div class="slide-preview">
        <template v-if="slide.content && slide.content.length > 0">
          <p v-for="(line, index) in previewLines" :key="index" class="preview-line">
            {{ line }}
          </p>
        </template>
        <p v-else class="preview-empty">无内容</p>
      </div>
    </div>

    <!-- 活动状态指示器 -->
    <div v-if="isActive" class="active-indicator">
      <el-icon><Check /></el-icon>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PPTSlide } from '@/types/lesson'

interface Props {
  /** 幻灯片数据 */
  slide: PPTSlide
  /** 幻灯片编号 */
  number: number
  /** 是否为当前活动的幻灯片 */
  isActive?: boolean
  /** 是否禁用点击 */
  disabled?: boolean
}

interface Emits {
  /** 点击事件 */
  click: []
}

const props = withDefaults(defineProps<Props>(), {
  isActive: false,
  disabled: false
})

const emit = defineEmits<Emits>()

// 预览行数限制
const PREVIEW_LINES = 3

// 计算预览内容（只显示前几行）
const previewLines = computed(() => {
  if (!props.slide.content || props.slide.content.length === 0) {
    return []
  }
  return props.slide.content.slice(0, PREVIEW_LINES)
})

// 处理点击事件
const handleClick = () => {
  if (!props.disabled) {
    emit('click')
  }
}
</script>

<script lang="ts">
import { Check } from '@element-plus/icons-vue'
</script>

<style scoped>
.slide-thumbnail {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  background: #fff;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  overflow: hidden;
}

.slide-thumbnail:hover:not(.disabled) {
  border-color: #409eff;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.2);
  transform: translateY(-2px);
}

.slide-thumbnail.active {
  border-color: #409eff;
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.3);
}

.slide-thumbnail.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.thumbnail-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.slide-number {
  position: absolute;
  top: 8px;
  left: 8px;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.slide-title {
  padding-left: 40px;
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.slide-preview {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow: hidden;
  margin-top: 8px;
}

.preview-line {
  font-size: 11px;
  color: #606266;
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.preview-empty {
  font-size: 12px;
  color: #909399;
  font-style: italic;
}

.active-indicator {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: #409eff;
  color: #fff;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
