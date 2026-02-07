<!--
  PPT 幻灯片预览组件
  提供完整的幻灯片预览、导航、缩放、全屏等功能
-->
<template>
  <div
    ref="containerRef"
    class="ppt-preview"
    :class="{
      'is-fullscreen': isFullscreen,
      'show-thumbnails': showThumbnails,
      'show-notes': showNotes
    }"
  >
    <!-- 顶部导航栏 -->
    <div class="preview-header">
      <div class="header-left">
        <h3 class="preview-title">
          <el-icon><Document /></el-icon>
          {{ title || 'PPT 预览' }}
        </h3>
      </div>
      <div class="header-right">
        <SlideNavigation
          :current-index="currentIndex"
          :total-slides="slides.length"
          :scale="scale"
          :min-scale="minScale"
          :max-scale="maxScale"
          :is-fullscreen="isFullscreen"
          :show-thumbnails="showThumbnails"
          :show-notes="showNotes"
          :autoplay="autoplay"
          :is-playing="isPlaying"
          @previous="previous"
          @next="next"
          @zoom-in="zoomIn"
          @zoom-out="zoomOut"
          @reset-zoom="resetZoom"
          @toggle-fullscreen="toggleFullscreen"
          @toggle-thumbnails="toggleThumbnails"
          @toggle-notes="toggleNotes"
          @export="handleExport"
          @toggle-play="togglePlay"
        />
      </div>
    </div>

    <!-- 主体区域 -->
    <div class="preview-body">
      <!-- 缩略图侧边栏 -->
      <transition name="slide-left">
        <div v-show="showThumbnails" class="thumbnail-sidebar">
          <div class="thumbnail-list">
            <SlideThumbnail
              v-for="(slide, index) in slides"
              :key="index"
              :slide="slide"
              :number="index + 1"
              :is-active="index === currentIndex"
              @click="goToSlide(index)"
            />
          </div>
        </div>
      </transition>

      <!-- 幻灯片展示区 -->
      <div class="slide-stage">
        <div
          class="slide-wrapper"
          :style="wrapperStyle"
        >
          <SlideContent
            v-if="currentSlide"
            :slide="currentSlide"
            :show-notes="showNotes"
            :slide-number="currentIndex + 1"
          />
          <div v-else class="slide-empty">
            <el-empty description="暂无幻灯片" />
          </div>
        </div>
      </div>
    </div>

    <!-- 底部快捷键提示 -->
    <div v-if="showKeyboardHints" class="keyboard-hints">
      <el-space :size="16">
        <span class="hint-item"><kbd>←</kbd> <kbd>→</kbd> 切换</span>
        <span class="hint-item"><kbd>+</kbd> <kbd>-</kbd> 缩放</span>
        <span class="hint-item"><kbd>F</kbd> 全屏</span>
        <span class="hint-item"><kbd>Esc</kbd> 退出</span>
      </el-space>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, readonly } from 'vue'
import { ElMessage } from 'element-plus'
import type { PPTSlide } from '@/types/lesson'
import { Document } from '@element-plus/icons-vue'
import SlideNavigation from './ppt/SlideNavigation.vue'
import SlideThumbnail from './ppt/SlideThumbnail.vue'
import SlideContent from './ppt/SlideContent.vue'

interface Props {
  /** 幻灯片数据 */
  slides: PPTSlide[]
  /** 标题 */
  title?: string
  /** 教案ID（用于导出等操作） */
  lessonId?: string
  /** 是否启用自动播放 */
  autoplay?: boolean
  /** 自动播放间隔（毫秒） */
  autoplayInterval?: number
  /** 是否显示键盘快捷键提示 */
  showKeyboardHints?: boolean
  /** 初始是否显示缩略图 */
  initialShowThumbnails?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  autoplay: false,
  autoplayInterval: 5000,
  showKeyboardHints: true,
  initialShowThumbnails: true
})

// 事件定义
const emit = defineEmits(['change', 'fullscreen-change', 'export'])

// DOM 引用
const containerRef = ref<HTMLElement>()

// 响应式状态
const currentIndex = ref(0)
const scale = ref(1)
const isFullscreen = ref(false)
const showThumbnails = ref(props.initialShowThumbnails)
const showNotes = ref(false)
const isPlaying = ref(false)

// 配置
const minScale = 0.5
const maxScale = 2
const scaleStep = 0.1

// 自动播放定时器
let autoplayTimer: ReturnType<typeof setInterval> | null = null

// 计算当前幻灯片
const currentSlide = computed(() => {
  if (!props.slides || props.slides.length === 0) return null
  return props.slides[currentIndex.value]
})

// 计算包装器样式
const wrapperStyle = computed(() => ({
  transform: `scale(${scale.value})`,
  transformOrigin: 'center center'
}))

// 上一页
const previous = () => {
  if (currentIndex.value > 0) {
    goToSlide(currentIndex.value - 1)
  }
}

// 下一页
const next = () => {
  if (currentIndex.value < props.slides.length - 1) {
    goToSlide(currentIndex.value + 1)
  }
}

// 跳转到指定页
const goToSlide = (index: number) => {
  if (index >= 0 && index < props.slides.length) {
    currentIndex.value = index
    emit('change', props.slides[index], index)
  }
}

// 放大
const zoomIn = () => {
  scale.value = Math.min(maxScale, scale.value + scaleStep)
}

// 缩小
const zoomOut = () => {
  scale.value = Math.max(minScale, scale.value - scaleStep)
}

// 重置缩放
const resetZoom = () => {
  scale.value = 1
}

// 切换全屏
const toggleFullscreen = async () => {
  if (!containerRef.value) return

  try {
    if (!isFullscreen.value) {
      await containerRef.value.requestFullscreen()
      isFullscreen.value = true
    } else {
      await document.exitFullscreen()
      isFullscreen.value = false
    }
    emit('fullscreen-change', isFullscreen.value)
  } catch (error) {
    console.error('全屏切换失败:', error)
    ElMessage.warning('全屏功能不可用')
  }
}

// 切换缩略图显示
const toggleThumbnails = () => {
  showThumbnails.value = !showThumbnails.value
}

// 切换备注显示
const toggleNotes = () => {
  showNotes.value = !showNotes.value
}

// 导出当前幻灯片
const handleExport = () => {
  if (currentSlide.value) {
    emit('export', currentSlide.value)
  }
}

// 切换自动播放
const togglePlay = () => {
  isPlaying.value = !isPlaying.value

  if (isPlaying.value) {
    startAutoplay()
  } else {
    stopAutoplay()
  }
}

// 开始自动播放
const startAutoplay = () => {
  stopAutoplay()
  autoplayTimer = setInterval(() => {
    if (currentIndex.value < props.slides.length - 1) {
      next()
    } else {
      // 播放到最后，停止播放
      stopAutoplay()
      isPlaying.value = false
    }
  }, props.autoplayInterval)
}

// 停止自动播放
const stopAutoplay = () => {
  if (autoplayTimer) {
    clearInterval(autoplayTimer)
    autoplayTimer = null
  }
}

// 键盘事件处理
const handleKeydown = (e: KeyboardEvent) => {
  // 如果正在输入框中，不处理快捷键
  const target = e.target as HTMLElement
  if (
    target.tagName === 'INPUT' ||
    target.tagName === 'TEXTAREA' ||
    target.isContentEditable
  ) {
    return
  }

  switch (e.key) {
    case 'ArrowLeft':
    case 'ArrowUp':
      e.preventDefault()
      previous()
      break
    case 'ArrowRight':
    case 'ArrowDown':
    case ' ':
      e.preventDefault()
      next()
      break
    case 'Home':
      e.preventDefault()
      goToSlide(0)
      break
    case 'End':
      e.preventDefault()
      goToSlide(props.slides.length - 1)
      break
    case '+':
    case '=':
      e.preventDefault()
      zoomIn()
      break
    case '-':
    case '_':
      e.preventDefault()
      zoomOut()
      break
    case '0':
      e.preventDefault()
      resetZoom()
      break
    case 'f':
    case 'F':
      e.preventDefault()
      toggleFullscreen()
      break
    case 't':
    case 'T':
      e.preventDefault()
      toggleThumbnails()
      break
    case 'n':
    case 'N':
      e.preventDefault()
      toggleNotes()
      break
    case 'Escape':
      if (isFullscreen.value) {
        e.preventDefault()
        toggleFullscreen()
      }
      break
  }
}

// 监听全屏变化事件
const handleFullscreenChange = () => {
  isFullscreen.value = !!document.fullscreenElement
  emit('fullscreen-change', isFullscreen.value)
}

// 生命周期
onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
  document.addEventListener('fullscreenchange', handleFullscreenChange)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
  stopAutoplay()
})

// 暴露方法给父组件
defineExpose({
  previous,
  next,
  goToSlide,
  zoomIn,
  zoomOut,
  resetZoom,
  toggleFullscreen,
  togglePlay,
  // 当前状态
  currentIndex: readonly(currentIndex),
  scale: readonly(scale),
  isFullscreen: readonly(isFullscreen),
  isPlaying: readonly(isPlaying)
})
</script>

<style scoped>
.ppt-preview {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  background: #f5f7fa;
  overflow: hidden;
}

.ppt-preview.is-fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
}

.preview-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.preview-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 缩略图侧边栏 */
.thumbnail-sidebar {
  width: 200px;
  background: #fff;
  border-right: 1px solid #e4e7ed;
  overflow-y: auto;
  flex-shrink: 0;
}

.thumbnail-list {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 幻灯片展示区 */
.slide-stage {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  overflow: hidden;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e7ed 100%);
}

.slide-wrapper {
  transition: transform 0.3s ease;
  max-width: 100%;
  max-height: 100%;
}

.slide-wrapper :deep(.slide-content) {
  width: 960px;
  height: 540px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  border-radius: 8px;
}

.slide-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 960px;
  height: 540px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
}

/* 键盘快捷键提示 */
.keyboard-hints {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.75);
  color: #fff;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 12px;
  pointer-events: none;
  z-index: 100;
}

.hint-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.hint-item kbd {
  background: rgba(255, 255, 255, 0.2);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: inherit;
  font-size: 11px;
}

/* 动画 */
.slide-left-enter-active,
.slide-left-leave-active {
  transition: all 0.3s ease;
}

.slide-left-enter-from,
.slide-left-leave-to {
  transform: translateX(-100%);
  opacity: 0;
}

/* 滚动条样式 */
.thumbnail-sidebar::-webkit-scrollbar {
  width: 6px;
}

.thumbnail-sidebar::-webkit-scrollbar-track {
  background: #f5f7fa;
}

.thumbnail-sidebar::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}

.thumbnail-sidebar::-webkit-scrollbar-thumb:hover {
  background: #c0c4cc;
}

/* 响应式 */
@media (max-width: 1024px) {
  .thumbnail-sidebar {
    width: 150px;
  }

  .slide-stage {
    padding: 20px;
  }

  .slide-wrapper :deep(.slide-content),
  .slide-empty {
    width: 720px;
    height: 405px;
  }
}

@media (max-width: 768px) {
  .preview-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }

  .thumbnail-sidebar {
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 10;
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
  }

  .slide-wrapper :deep(.slide-content),
  .slide-empty {
    width: 100%;
    height: auto;
    aspect-ratio: 16 / 9;
  }

  .keyboard-hints {
    display: none;
  }
}
</style>
