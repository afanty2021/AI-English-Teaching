<template>
  <el-drawer
    v-model="visible"
    :title="drawerTitle"
    direction="rtl"
    size="400px"
    :before-close="handleClose"
  >
    <!-- 抽屉内容 -->
    <div class="feedback-drawer-content">
      <!-- 整体评分卡片 -->
      <div v-if="scores" class="overall-score-card">
        <div class="score-circle-wrapper">
          <el-progress
            type="circle"
            :percentage="overallPercentage"
            :color="getScoreColor(overallPercentage)"
            :width="120"
          >
            <template #default="{ percentage }">
              <span class="score-percentage">{{ percentage }}</span>
            </template>
          </el-progress>
        </div>
        <div class="score-info">
          <h3>总体评分</h3>
          <p class="score-description">{{ scoreDescription }}</p>
        </div>
      </div>

      <!-- 分项评分 -->
      <div v-if="scores" class="detailed-scores">
        <h4>分项评分</h4>
        <div class="score-list">
          <div
            v-for="dimension in scoreDimensions"
            :key="dimension.name"
            class="score-dimension"
          >
            <div class="dimension-header">
              <span class="dimension-name">{{ dimension.name }}</span>
              <el-icon :class="getDimensionIconClass(dimension.score, dimension.max_score)">
                <component :is="getDimensionIcon(dimension.name)" />
              </el-icon>
            </div>
            <el-progress
              :percentage="getDimensionPercentage(dimension.score, dimension.max_score)"
              :color="getScoreColor(getDimensionPercentage(dimension.score, dimension.max_score))"
              :stroke-width="8"
              :show-text="true"
            >
              <template #default="{ percentage }">
                <span class="progress-text">{{ dimension.score }}/{{ dimension.max_score }}</span>
              </template>
            </el-progress>
            <div v-if="dimension.feedback" class="dimension-feedback">
              {{ dimension.feedback }}
            </div>
            <div v-if="dimension.suggestions && dimension.suggestions.length > 0" class="dimension-suggestions">
              <div
                v-for="(suggestion, index) in dimension.suggestions"
                :key="index"
                class="suggestion-item"
              >
                <el-icon><Check /></el-icon>
                <span>{{ suggestion }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 改进建议 -->
      <div v-if="scores && scores.suggestions && scores.suggestions.length > 0" class="suggestions-section">
        <h4>改进建议</h4>
        <div class="suggestions-list">
          <div
            v-for="(suggestion, index) in scores.suggestions"
            :key="index"
            class="main-suggestion-item"
          >
            <el-icon class="suggestion-icon"><Star /></el-icon>
            <span>{{ suggestion }}</span>
          </div>
        </div>
      </div>

      <!-- 关键词学习 -->
      <div v-if="keyWords.length > 0" class="key-words-section">
        <h4>关键词</h4>
        <div class="key-words-list">
          <el-tag
            v-for="(word, index) in keyWords"
            :key="index"
            class="key-word-tag"
            :type="getWordTagType(word.score)"
          >
            {{ word.word }}
            <span class="word-score">{{ word.score }}</span>
          </el-tag>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="drawer-actions">
        <el-button type="primary" @click="handleContinue">
          继续练习
          <el-icon class="el-icon--right"><Right /></el-icon>
        </el-button>
        <el-button @click="handleViewReport">
          查看详细报告
        </el-button>
      </div>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  Check,
  Star,
  Right,
  Clock,
  ChatDotRound,
  Microphone,
  Document,
  TrendCharts
} from '@element-plus/icons-vue'
import type { ConversationScores } from '@/types/conversation'

interface Props {
  visible: boolean
  scores?: ConversationScores
  keyWords?: Array<{ word: string; score: number; phonetic?: string }>
  isComplete?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  keyWords: () => [],
  isComplete: false
})

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'continue': []
  'view-report': []
}>()

// 抽屉标题
const drawerTitle = computed(() => {
  return props.isComplete ? '对话完成' : '实时反馈'
})

// 整体评分百分比
const overallPercentage = computed(() => {
  if (!props.scores) return 0
  return props.scores.overall
})

// 评分描述
const scoreDescription = computed(() => {
  const percentage = overallPercentage.value
  if (percentage >= 90) return '优秀！继续保持！'
  if (percentage >= 75) return '很好！再接再厉！'
  if (percentage >= 60) return '及格，还有提升空间'
  return '需要更多练习哦'
})

// 分项评分维度
const scoreDimensions = computed(() => {
  if (!props.scores) return []
  return [
    props.scores.fluency,
    props.scores.grammar,
    props.scores.vocabulary,
    props.scores.pronunciation,
    props.scores.communication
  ]
})

// 获取评分颜色
const getScoreColor = (percentage: number) => {
  if (percentage >= 90) return '#67C23A'
  if (percentage >= 75) return '#409EFF'
  if (percentage >= 60) return '#E6A23C'
  return '#F56C6C'
}

// 获取维度百分比
const getDimensionPercentage = (score: number, maxScore: number) => {
  return Math.round((score / maxScore) * 100)
}

// 获取维度图标
const getDimensionIcon = (name: string) => {
  const icons: Record<string, any> = {
    '流利度': Clock,
    '语法': Document,
    '词汇': TrendCharts,
    '发音': Microphone,
    '沟通能力': ChatDotRound
  }
  return icons[name] || Document
}

// 获取维度图标样式类
const getDimensionIconClass = (score: number, maxScore: number) => {
  const percentage = getDimensionPercentage(score, maxScore)
  if (percentage >= 80) return 'icon-excellent'
  if (percentage >= 60) return 'icon-good'
  if (percentage >= 40) return 'icon-fair'
  return 'icon-poor'
}

// 获取词汇标签类型
const getWordTagType = (score: number) => {
  if (score >= 90) return 'success'
  if (score >= 70) return 'primary'
  if (score >= 60) return 'warning'
  return 'info'
}

// 关闭抽屉
const handleClose = () => {
  emit('update:visible', false)
}

// 继续练习
const handleContinue = () => {
  emit('continue')
  handleClose()
}

// 查看报告
const handleViewReport = () => {
  emit('view-report')
  handleClose()
}
</script>

<style scoped>
.feedback-drawer-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 20px;
  height: 100%;
}

.overall-score-card {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
}

.score-circle-wrapper {
  flex-shrink: 0;
}

.score-percentage {
  font-size: 24px;
  font-weight: bold;
}

.score-info h3 {
  margin: 0 0 8px 0;
  font-size: 20px;
}

.score-description {
  margin: 0;
  opacity: 0.9;
  font-size: 14px;
}

.detailed-scores h4,
.suggestions-section h4,
.key-words-section h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.score-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.score-dimension {
  padding: 16px;
  background: var(--el-fill-color-blank);
  border-radius: 8px;
}

.dimension-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.dimension-name {
  font-weight: 500;
  font-size: 14px;
}

.dimension-feedback {
  margin-top: 8px;
  font-size: 13px;
  color: var(--el-text-color-regular);
}

.dimension-suggestions {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 8px;
}

.suggestion-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--el-color-success);
}

.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.main-suggestion-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
  font-size: 14px;
}

.suggestion-icon {
  color: var(--el-color-warning);
  margin-top: 2px;
  flex-shrink: 0;
}

.key-words-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.key-word-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.word-score {
  margin-left: 4px;
  font-size: 12px;
  opacity: 0.7;
}

.drawer-actions {
  margin-top: auto;
  display: flex;
  gap: 12px;
}

.drawer-actions .el-button {
  flex: 1;
}
</style>
