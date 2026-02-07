<!--
  PPT 幻灯片导航控制组件
  提供幻灯片切换、缩放、全屏等功能
-->
<template>
  <div class="slide-navigation">
    <!-- 导航按钮组 -->
    <div class="navigation-group">
      <el-button-group>
        <el-tooltip content="上一页 (←)" placement="top">
          <el-button
            :disabled="currentIndex === 0"
            @click="handlePrevious"
          >
            <el-icon><ArrowLeft /></el-icon>
          </el-button>
        </el-tooltip>

        <el-tooltip content="下一页 (→)" placement="top">
          <el-button
            :disabled="currentIndex === totalSlides - 1"
            @click="handleNext"
          >
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </el-tooltip>
      </el-button-group>

      <!-- 页码显示 -->
      <div class="page-indicator">
        <span class="current">{{ currentIndex + 1 }}</span>
        <span class="separator">/</span>
        <span class="total">{{ totalSlides }}</span>
      </div>
    </div>

    <!-- 缩放控制组 -->
    <div class="zoom-group">
      <el-button-group>
        <el-tooltip content="缩小 (-)" placement="top">
          <el-button
            :disabled="scale <= minScale"
            @click="handleZoomOut"
          >
            <el-icon><ZoomOut /></el-icon>
          </el-button>
        </el-tooltip>

        <el-button disabled class="scale-display">
          {{ Math.round(scale * 100) }}%
        </el-button>

        <el-tooltip content="放大 (+)" placement="top">
          <el-button
            :disabled="scale >= maxScale"
            @click="handleZoomIn"
          >
            <el-icon><ZoomIn /></el-icon>
          </el-button>
        </el-tooltip>

        <el-tooltip content="重置 (R)" placement="top">
          <el-button @click="handleResetZoom">
            <el-icon><RefreshRight /></el-icon>
          </el-button>
        </el-tooltip>
      </el-button-group>
    </div>

    <!-- 功能按钮组 -->
    <div class="action-group">
      <el-button-group>
        <el-tooltip :content="isFullscreen ? '退出全屏 (Esc)' : '全屏 (F)'" placement="top">
          <el-button @click="handleToggleFullscreen">
            <el-icon>
              <component :is="isFullscreen ? 'FullScreen' : 'FullScreen'" />
            </el-icon>
          </el-button>
        </el-tooltip>

        <el-tooltip :content="showThumbnails ? '隐藏缩略图' : '显示缩略图'" placement="top">
          <el-button @click="handleToggleThumbnails">
            <el-icon><Grid /></el-icon>
          </el-button>
        </el-tooltip>

        <el-tooltip :content="showNotes ? '隐藏备注' : '显示备注'" placement="top">
          <el-button @click="handleToggleNotes">
            <el-icon><Document /></el-icon>
          </el-button>
        </el-tooltip>

        <el-tooltip content="导出当前页" placement="top">
          <el-button @click="handleExport">
            <el-icon><Download /></el-icon>
          </el-button>
        </el-tooltip>

        <el-tooltip v-if="autoplay" :content="isPlaying ? '暂停' : '播放'" placement="top">
          <el-button @click="handleTogglePlay">
            <el-icon>
              <component :is="isPlaying ? 'VideoPause' : 'VideoPlay'" />
            </el-icon>
          </el-button>
        </el-tooltip>
      </el-button-group>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  ArrowLeft,
  ArrowRight,
  ZoomIn,
  ZoomOut,
  RefreshRight,
  Grid,
  Document,
  Download
} from '@element-plus/icons-vue'

interface Props {
  /** 当前幻灯片索引 */
  currentIndex: number
  /** 幻灯片总数 */
  totalSlides: number
  /** 当前缩放比例 */
  scale: number
  /** 最小缩放比例 */
  minScale?: number
  /** 最大缩放比例 */
  maxScale?: number
  /** 是否全屏 */
  isFullscreen: boolean
  /** 是否显示缩略图 */
  showThumbnails: boolean
  /** 是否显示备注 */
  showNotes: boolean
  /** 是否启用自动播放 */
  autoplay?: boolean
  /** 是否正在播放 */
  isPlaying?: boolean
}

interface Emits {
  /** 上一页 */
  previous: []
  /** 下一页 */
  next: []
  /** 跳转到指定页 */
  goto: [index: number]
  /** 放大 */
  zoomIn: []
  /** 缩小 */
  zoomOut: []
  /** 重置缩放 */
  resetZoom: []
  /** 设置缩放 */
  setScale: [scale: number]
  /** 切换全屏 */
  toggleFullscreen: []
  /** 切换缩略图显示 */
  toggleThumbnails: []
  /** 切换备注显示 */
  toggleNotes: []
  /** 导出当前页 */
  export: []
  /** 切换播放状态 */
  togglePlay: []
}

const props = withDefaults(defineProps<Props>(), {
  minScale: 0.5,
  maxScale: 2,
  autoplay: false,
  isPlaying: false
})

const emit = defineEmits<Emits>()

// 处理上一页
const handlePrevious = () => {
  emit('previous')
}

// 处理下一页
const handleNext = () => {
  emit('next')
}

// 处理放大
const handleZoomIn = () => {
  emit('zoomIn')
}

// 处理缩小
const handleZoomOut = () => {
  emit('zoomOut')
}

// 处理重置缩放
const handleResetZoom = () => {
  emit('resetZoom')
}

// 处理切换全屏
const handleToggleFullscreen = () => {
  emit('toggleFullscreen')
}

// 处理切换缩略图
const handleToggleThumbnails = () => {
  emit('toggleThumbnails')
}

// 处理切换备注
const handleToggleNotes = () => {
  emit('toggleNotes')
}

// 处理导出
const handleExport = () => {
  emit('export')
}

// 处理切换播放
const handleTogglePlay = () => {
  emit('togglePlay')
}
</script>

<style scoped>
.slide-navigation {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
  flex-wrap: wrap;
}

.navigation-group,
.zoom-group,
.action-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 0 12px;
  font-size: 14px;
  font-weight: 500;
  color: #606266;
}

.page-indicator .current {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.page-indicator .separator {
  color: #909399;
}

.page-indicator .total {
  color: #909399;
}

.scale-display {
  min-width: 60px !important;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .slide-navigation {
    flex-direction: column;
    align-items: stretch;
  }

  .navigation-group,
  .zoom-group,
  .action-group {
    justify-content: center;
  }
}
</style>
