<!--
  PPTPreview 组件使用示例

  基本用法：
  <PPTPreview :slides="slides" />

  完整配置：
  <PPTPreview
    :slides="slides"
    title="我的教案"
    :autoplay="true"
    :autoplay-interval="3000"
    @change="handleChange"
    @export="handleExport"
  />
-->
<template>
  <div class="ppt-preview-example">
    <el-card header="PPT 预览组件使用示例">
      <!-- 基础用法 -->
      <div class="example-section">
        <h4>1. 基础用法</h4>
        <el-button @click="showBasicPreview = true">打开基础预览</el-button>

        <el-dialog
          v-model="showBasicPreview"
          title="PPT 预览"
          width="90%"
          :close-on-click-modal="false"
        >
          <PPTPreview
            :slides="sampleSlides"
            @change="handleSlideChange"
          />
        </el-dialog>
      </div>

      <!-- 带自动播放 -->
      <div class="example-section">
        <h4>2. 自动播放模式</h4>
        <el-button @click="showAutoplayPreview = true">打开自动播放预览</el-button>

        <el-dialog
          v-model="showAutoplayPreview"
          title="PPT 自动播放预览"
          width="90%"
          :close-on-click-modal="false"
        >
          <PPTPreview
            :slides="sampleSlides"
            title="自动播放示例"
            :autoplay="true"
            :autoplay-interval="3000"
          />
        </el-dialog>
      </div>

      <!-- 带事件回调 -->
      <div class="example-section">
        <h4>3. 带事件回调</h4>
        <el-button @click="showCallbackPreview = true">打开带回调的预览</el-button>

        <el-dialog
          v-model="showCallbackPreview"
          title="PPT 预览（带回调）"
          width="90%"
          :close-on-click-modal="false"
        >
          <PPTPreview
            :slides="sampleSlides"
            title="事件回调示例"
            @change="handleSlideChange"
            @fullscreen-change="handleFullscreenChange"
            @export="handleExport"
          />
        </el-dialog>

        <el-alert
          v-if="lastEvent"
          :title="lastEvent"
          type="info"
          :closable="false"
          style="margin-top: 12px"
        />
      </div>

      <!-- 使用 ref 控制组件 -->
      <div class="example-section">
        <h4>4. 使用 ref 控制</h4>
        <el-space>
          <el-button @click="showControlPreview = true">打开预览</el-button>
          <el-button @click="controlNext">下一页</el-button>
          <el-button @click="controlPrevious">上一页</el-button>
          <el-button @click="controlFullscreen">全屏</el-button>
        </el-space>

        <el-dialog
          v-model="showControlPreview"
          title="PPT 预览（外部控制）"
          width="90%"
          :close-on-click-modal="false"
        >
          <PPTPreview
            ref="previewRef"
            :slides="sampleSlides"
            title="外部控制示例"
          />
        </el-dialog>
      </div>
    </el-card>

    <!-- 快捷键说明 -->
    <el-card header="快捷键说明" style="margin-top: 20px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="← / →">切换幻灯片</el-descriptions-item>
        <el-descriptions-item label="+ / -">放大 / 缩小</el-descriptions-item>
        <el-descriptions-item label="0">重置缩放</el-descriptions-item>
        <el-descriptions-item label="F">切换全屏</el-descriptions-item>
        <el-descriptions-item label="T">切换缩略图</el-descriptions-item>
        <el-descriptions-item label="N">切换备注</el-descriptions-item>
        <el-descriptions-item label="Home">第一页</el-descriptions-item>
        <el-descriptions-item label="End">最后一页</el-descriptions-item>
        <el-descriptions-item label="Esc">退出全屏</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { PPTSlide } from '@/types/lesson'
import PPTPreview from '@/components/PPTPreview.vue'

// 对话框显示状态
const showBasicPreview = ref(false)
const showAutoplayPreview = ref(false)
const showCallbackPreview = ref(false)
const showControlPreview = ref(false)

// 组件引用
const previewRef = ref<InstanceType<typeof PPTPreview>>()

// 最后的事件消息
const lastEvent = ref('')

// 示例幻灯片数据
const sampleSlides: PPTSlide[] = [
  {
    slide_number: 1,
    title: '课程介绍',
    content: [
      '本课程将帮助学生掌握英语基础语法',
      '通过互动练习提高口语表达能力',
      '培养英语思维习惯'
    ],
    notes: '这是开场白，需要热情洋溢地介绍课程内容',
    layout: 'default'
  },
  {
    slide_number: 2,
    title: '学习目标',
    content: [
      '掌握 100+ 个核心词汇',
      '理解 5 种基本时态',
      '能够进行简单对话'
    ],
    notes: '强调学习目标的重要性',
    layout: 'two-columns'
  },
  {
    slide_number: 3,
    title: '课程大纲',
    content: [
      '第一周：基础词汇与问候语',
      '第二周：一般现在时',
      '第三周：一般过去时',
      '第四周：一般将来时'
    ],
    notes: '详细说明每周的学习内容',
    layout: 'timeline'
  },
  {
    slide_number: 4,
    title: '教学方法',
    content: [
      '互动式教学',
      '情境模拟',
      '游戏化学习'
    ],
    notes: '介绍我们的特色教学方法',
    layout: 'image-text'
  },
  {
    slide_number: 5,
    title: '感谢聆听',
    content: [
      '如有疑问，欢迎随时提问',
      '祝学习愉快！'
    ],
    notes: '结束语',
    layout: 'title-center'
  }
]

// 事件处理
const handleSlideChange = (slide: PPTSlide, index: number) => {
  lastEvent.value = `切换到幻灯片 ${index + 1}: ${slide.title}`
}

const handleFullscreenChange = (isFullscreen: boolean) => {
  lastEvent.value = `全屏状态: ${isFullscreen ? '开启' : '关闭'}`
}

const handleExport = (slide: PPTSlide) => {
  lastEvent.value = `导出幻灯片: ${slide.title}`
  ElMessage.success('导出功能需要配合后端实现')
}

// 外部控制方法
const controlNext = () => {
  previewRef.value?.next()
}

const controlPrevious = () => {
  previewRef.value?.previous()
}

const controlFullscreen = () => {
  previewRef.value?.toggleFullscreen()
}
</script>

<style scoped>
.ppt-preview-example {
  padding: 20px;
}

.example-section {
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid #e4e7ed;
}

.example-section:last-child {
  border-bottom: none;
}

.example-section h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

:deep(.el-dialog__body) {
  height: 70vh;
  padding: 0;
}

:deep(.el-dialog__header) {
  padding: 16px 20px;
}
</style>
