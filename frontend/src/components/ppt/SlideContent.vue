<!--
  PPT 幻灯片内容渲染组件
  根据不同的布局类型渲染幻灯片内容
-->
<template>
  <div class="slide-content" :class="[`layout-${slide.layout || 'default'}`, { 'show-notes': showNotes }]">
    <!-- 幻灯片主体内容 -->
    <div class="slide-body">
      <!-- 标题 -->
      <h1 v-if="slide.title" class="slide-title">
        {{ slide.title }}
      </h1>

      <!-- 内容区域 - 根据布局类型渲染 -->
      <div class="slide-content-area" :class="`layout-${slide.layout || 'default'}`">
        <!-- 默认布局：垂直列表 -->
        <template v-if="!slide.layout || slide.layout === 'default'">
          <ul v-if="slide.content && slide.content.length > 0" class="content-list">
            <li v-for="(item, index) in slide.content" :key="index" class="content-item">
              {{ item }}
            </li>
          </ul>
          <div v-else class="content-empty">
            <el-empty description="暂无内容" :image-size="80" />
          </div>
        </template>

        <!-- 两栏布局 -->
        <template v-else-if="slide.layout === 'two-columns'">
          <div class="two-columns">
            <div class="column left">
              <h3>要点</h3>
              <ul class="content-list">
                <li v-for="(item, index) in leftColumn" :key="index" class="content-item">
                  {{ item }}
                </li>
              </ul>
            </div>
            <div class="column right">
              <h3>详解</h3>
              <ul class="content-list">
                <li v-for="(item, index) in rightColumn" :key="index" class="content-item">
                  {{ item }}
                </li>
              </ul>
            </div>
          </div>
        </template>

        <!-- 图文布局 -->
        <template v-else-if="slide.layout === 'image-text'">
          <div class="image-text">
            <div class="text-content">
              <ul v-if="slide.content && slide.content.length > 0" class="content-list">
                <li v-for="(item, index) in slide.content" :key="index" class="content-item">
                  {{ item }}
                </li>
              </ul>
            </div>
            <div class="image-placeholder">
              <el-icon><Picture /></el-icon>
              <p>图片区域</p>
            </div>
          </div>
        </template>

        <!-- 标题居中布局 -->
        <template v-else-if="slide.layout === 'title-center'">
          <div class="title-center">
            <p v-for="(item, index) in slide.content" :key="index" class="center-text">
              {{ item }}
            </p>
          </div>
        </template>

        <!-- 时间线布局 -->
        <template v-else-if="slide.layout === 'timeline'">
          <div class="timeline">
            <div
              v-for="(item, index) in slide.content"
              :key="index"
              class="timeline-item"
            >
              <div class="timeline-marker">{{ index + 1 }}</div>
              <div class="timeline-content">{{ item }}</div>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- 备注区域 -->
    <transition name="slide-down">
      <div v-if="showNotes && slide.notes" class="slide-notes">
        <div class="notes-header">
          <el-icon><Document /></el-icon>
          <span>演讲者备注</span>
        </div>
        <div class="notes-content">
          {{ slide.notes }}
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import type { PPTSlide } from '@/types/lesson'
import { Picture, Document } from '@element-plus/icons-vue'

interface Props {
  /** 幻灯片数据 */
  slide: PPTSlide
  /** 是否显示备注 */
  showNotes?: boolean
  /** 幻灯片编号 */
  slideNumber?: number
}

const props = withDefaults(defineProps<Props>(), {
  showNotes: false,
  slideNumber: 1
})

// 计算左栏内容（两栏布局）
const leftColumn = computed(() => {
  if (!props.slide.content || props.slide.content.length === 0) return []
  const mid = Math.ceil(props.slide.content.length / 2)
  return props.slide.content.slice(0, mid)
})

// 计算右栏内容（两栏布局）
const rightColumn = computed(() => {
  if (!props.slide.content || props.slide.content.length === 0) return []
  const mid = Math.ceil(props.slide.content.length / 2)
  return props.slide.content.slice(mid)
})
</script>

<style scoped>
.slide-content {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  padding: 40px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

/* 标题样式 */
.slide-title {
  font-size: 32px;
  font-weight: 700;
  margin: 0 0 30px 0;
  text-align: center;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
}

/* 内容区域 */
.slide-content-area {
  flex: 1;
  overflow-y: auto;
}

/* 默认布局 */
.layout-default .content-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.layout-default .content-item {
  font-size: 20px;
  line-height: 1.8;
  padding: 8px 0 8px 30px;
  position: relative;
}

.layout-default .content-item::before {
  content: '•';
  position: absolute;
  left: 0;
  font-size: 24px;
  color: rgba(255, 255, 255, 0.8);
}

.content-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

/* 两栏布局 */
.two-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
  height: 100%;
}

.two-columns .column {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 20px;
  backdrop-filter: blur(10px);
}

.two-columns h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
  border-bottom: 2px solid rgba(255, 255, 255, 0.3);
  padding-bottom: 8px;
}

/* 图文布局 */
.image-text {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
  height: 100%;
}

.image-placeholder {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  border: 2px dashed rgba(255, 255, 255, 0.3);
}

.image-placeholder .el-icon {
  font-size: 48px;
  opacity: 0.6;
}

/* 标题居中布局 */
.title-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
}

.title-center .center-text {
  font-size: 24px;
  line-height: 2;
  margin: 8px 0;
}

/* 时间线布局 */
.timeline {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.timeline-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.timeline-marker {
  width: 32px;
  height: 32px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  flex-shrink: 0;
}

.timeline-content {
  flex: 1;
  font-size: 18px;
  line-height: 1.6;
  padding-top: 4px;
}

/* 备注区域 */
.slide-notes {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(0, 0, 0, 0.85);
  color: #fff;
  padding: 16px 20px;
  border-top: 3px solid #409eff;
  max-height: 40%;
  overflow-y: auto;
}

.notes-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #409eff;
}

.notes-content {
  font-size: 14px;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.9);
}

/* 动画 */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from {
  transform: translateY(100%);
}

.slide-down-leave-to {
  transform: translateY(100%);
}

/* 滚动条样式 */
.slide-content-area::-webkit-scrollbar,
.slide-notes::-webkit-scrollbar {
  width: 6px;
}

.slide-content-area::-webkit-scrollbar-track,
.slide-notes::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

.slide-content-area::-webkit-scrollbar-thumb,
.slide-notes::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 3px;
}

.slide-content-area::-webkit-scrollbar-thumb:hover,
.slide-notes::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}
</style>
