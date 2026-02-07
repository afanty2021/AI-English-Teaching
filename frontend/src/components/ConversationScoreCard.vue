<!--
  对话评分卡片组件
  用于展示AI对话的评分结果，包括总分、分项评分、反馈和建议
-->
<template>
  <el-card
    class="score-card"
    shadow="hover"
  >
    <template #header>
      <div class="card-header">
        <el-icon><TrendCharts /></el-icon>
        <span>对话评分</span>
      </div>
    </template>

    <el-empty
      v-if="!scores"
      description="暂无评分数据"
      class="empty-state"
    />

    <div
      v-else
      class="score-content"
    >
      <!-- 总分展示 -->
      <div class="overall-score">
        <div
          class="score-circle"
          :class="getScoreClass(scores.overall_score || scores.overall || 0)"
        >
          <span class="score-value">{{ scores.overall_score || scores.overall || 0 }}</span>
          <span class="score-label">总分</span>
        </div>
        <div class="score-labels">
          <el-tag
            :type="getScoreType(scores.overall_score || scores.overall || 0)"
            size="large"
          >
            {{ getScoreLabel(scores.overall_score || scores.overall || 0) }}
          </el-tag>
        </div>
      </div>

      <!-- 分项评分 -->
      <el-divider />

      <div class="dimension-scores">
        <div class="score-item">
          <div class="score-header">
            <span>流利度</span>
            <span class="score-number">{{ scores.fluency_score || 0 }}</span>
          </div>
          <el-progress
            :percentage="scores.fluency_score || 0"
            :color="getProgressColor(scores.fluency_score || 0)"
            :show-text="false"
          />
        </div>

        <div class="score-item">
          <div class="score-header">
            <span>词汇</span>
            <span class="score-number">{{ scores.vocabulary_score || 0 }}</span>
          </div>
          <el-progress
            :percentage="scores.vocabulary_score || 0"
            :color="getProgressColor(scores.vocabulary_score || 0)"
            :show-text="false"
          />
        </div>

        <div class="score-item">
          <div class="score-header">
            <span>语法</span>
            <span class="score-number">{{ scores.grammar_score || 0 }}</span>
          </div>
          <el-progress
            :percentage="scores.grammar_score || 0"
            :color="getProgressColor(scores.grammar_score || 0)"
            :show-text="false"
          />
        </div>
      </div>

      <!-- 反馈 -->
      <el-divider />

      <div
        v-if="scores.feedback"
        class="feedback-section"
      >
        <h4>AI 反馈</h4>
        <p class="feedback-text">
          {{ scores.feedback }}
        </p>
      </div>

      <!-- 建议 -->
      <div
        v-if="scores.suggestions?.length"
        class="suggestions-section"
      >
        <h4>改进建议</h4>
        <ul class="suggestions-list">
          <li
            v-for="(suggestion, index) in scores.suggestions"
            :key="index"
            class="suggestion-item"
          >
            <el-icon><Right /></el-icon>
            <span>{{ suggestion }}</span>
          </li>
        </ul>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { TrendCharts, Right } from '@element-plus/icons-vue'
import type { ConversationScores } from '@/types/conversation'

interface Props {
  scores: ConversationScores | null
}

const props = defineProps<Props>()

function getScoreClass(score: number): string {
  if (score >= 90) return 'excellent'
  if (score >= 75) return 'good'
  if (score >= 60) return 'satisfactory'
  return 'needs-improvement'
}

function getScoreType(score: number): 'success' | 'warning' | 'danger' | 'info' {
  if (score >= 90) return 'success'
  if (score >= 75) return 'success'
  if (score >= 60) return 'warning'
  return 'danger'
}

function getScoreLabel(score: number): string {
  if (score >= 90) return '优秀'
  if (score >= 75) return '良好'
  if (score >= 60) return '满意'
  return '需改进'
}

function getProgressColor(score: number): string {
  if (score >= 90) return '#67C23A'
  if (score >= 75) return '#409EFF'
  if (score >= 60) return '#E6A23C'
  return '#F56C6C'
}
</script>

<style scoped>
.score-card {
  margin-top: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
}

.overall-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
}

.score-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 4px solid;
  margin-bottom: 16px;
}

.score-circle.excellent {
  border-color: #67C23A;
  background: linear-gradient(135deg, #f0fff4 0%, #dcfce7 100%);
}

.score-circle.good {
  border-color: #409EFF;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
}

.score-circle.satisfactory {
  border-color: #E6A23C;
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
}

.score-circle.needs-improvement {
  border-color: #F56C6C;
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
}

.score-value {
  font-size: 36px;
  font-weight: 700;
  line-height: 1;
}

.score-label {
  font-size: 14px;
  color: #606266;
  margin-top: 4px;
}

.dimension-scores {
  padding: 0 20px;
}

.score-item {
  margin-bottom: 20px;
}

.score-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.score-number {
  font-weight: 600;
  font-size: 16px;
}

.feedback-section,
.suggestions-section {
  padding: 0 20px 20px;
}

.feedback-section h4,
.suggestions-section h4 {
  margin: 0 0 12px;
  font-size: 16px;
  font-weight: 600;
}

.feedback-text {
  margin: 0;
  line-height: 1.6;
  color: #606266;
}

.suggestions-list {
  margin: 0;
  padding-left: 0;
  list-style: none;
}

.suggestion-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 0;
  line-height: 1.6;
}

.suggestion-item .el-icon {
  margin-top: 2px;
  color: #409EFF;
  flex-shrink: 0;
}
</style>
