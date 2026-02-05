<template>
  <div class="practice-result">
    <el-page-header @back="$router.back()">
      <template #content>
        <h2>练习结果</h2>
      </template>
    </el-page-header>

    <div v-loading="loading" class="result-content">
      <el-empty v-if="!result && !loading" description="暂无结果" />

      <div v-else class="result-detail">
        <!-- 总体统计卡片 -->
        <el-row :gutter="16" class="stats-cards">
          <el-col :xs="12" :sm="6">
            <el-card class="stat-card">
              <div class="stat-icon" style="background: #e1f3ff;">
                <el-icon :size="32" color="#409eff"><Document /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ result?.total_questions }}</div>
                <div class="stat-label">总题数</div>
              </div>
            </el-card>
          </el-col>
          <el-col :xs="12" :sm="6">
            <el-card class="stat-card">
              <div class="stat-icon" style="background: #f0f9ff;">
                <el-icon :size="32" color="#67c23a"><Select /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ result?.correct_count }}</div>
                <div class="stat-label">答对</div>
              </div>
            </el-card>
          </el-col>
          <el-col :xs="12" :sm="6">
            <el-card class="stat-card">
              <div class="stat-icon" style="background: #fef0f0;">
                <el-icon :size="32" color="#f56c6c"><Close /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ result?.total_questions - result?.correct_count }}</div>
                <div class="stat-label">答错</div>
              </div>
            </el-card>
          </el-col>
          <el-col :xs="12" :sm="6">
            <el-card class="stat-card">
              <div class="stat-icon" style="background: #f4f4f5;">
                <el-icon :size="32" color="#909399"><TrendCharts /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ (result?.correct_rate * 100).toFixed(1) }}%</div>
                <div class="stat-label">正确率</div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 详细统计 -->
        <el-card class="detail-stats">
          <template #header>
            <h3>详细统计</h3>
          </template>

          <el-tabs>
            <!-- 按题型统计 -->
            <el-tab-pane label="按题型">
              <div v-if="getTypeStats().length" class="stats-list">
                <div v-for="item in getTypeStats()" :key="item.type" class="stats-item">
                  <div class="stats-label">{{ getTypeLabel(item.type) }}</div>
                  <div class="stats-bar">
                    <div
                      class="stats-bar-fill"
                      :style="{ width: `${(item.correct / item.total) * 100}%` }"
                    />
                  </div>
                  <div class="stats-value">{{ item.correct }}/{{ item.total }}</div>
                </div>
              </div>
              <el-empty v-else description="暂无数据" />
            </el-tab-pane>

            <!-- 按难度统计 -->
            <el-tab-pane label="按难度">
              <div v-if="getDifficultyStats().length" class="stats-list">
                <div v-for="item in getDifficultyStats()" :key="item.level" class="stats-item">
                  <div class="stats-label">{{ item.level }}</div>
                  <div class="stats-bar">
                    <div
                      class="stats-bar-fill"
                      :style="{ width: `${(item.correct / item.total) * 100}%` }"
                    />
                  </div>
                  <div class="stats-value">{{ item.correct }}/{{ item.total }}</div>
                </div>
              </div>
              <el-empty v-else description="暂无数据" />
            </el-tab-pane>

            <!-- 按主题统计 -->
            <el-tab-pane label="按主题">
              <div v-if="getTopicStats().length" class="stats-list">
                <div v-for="item in getTopicStats()" :key="item.topic" class="stats-item">
                  <div class="stats-label">{{ item.topic }}</div>
                  <div class="stats-bar">
                    <div
                      class="stats-bar-fill"
                      :style="{ width: `${(item.correct / item.total) * 100}%` }"
                    />
                  </div>
                  <div class="stats-value">{{ item.correct }}/{{ item.total }}</div>
                </div>
              </div>
              <el-empty v-else description="暂无数据" />
            </el-tab-pane>
          </el-tabs>
        </el-card>

        <!-- 错题列表 -->
        <el-card v-if="result?.wrong_questions?.length" class="wrong-questions">
          <template #header>
            <div class="card-header">
              <h3>错题回顾</h3>
              <span class="wrong-count">共 {{ result.wrong_questions.length }} 题</span>
            </div>
          </template>

          <div class="wrong-list">
            <div v-for="(wrong, index) in result.wrong_questions" :key="wrong.question_id" class="wrong-item">
              <div class="wrong-header">
                <span class="wrong-index">第 {{ index + 1 }} 题</span>
                <el-tag size="small">{{ getQuestionTypeLabel(wrong.question_type) }}</el-tag>
              </div>
              <div class="wrong-content">{{ wrong.content_text }}</div>
              <div class="wrong-answers">
                <div class="answer-item">
                  <span class="answer-label">您的答案：</span>
                  <span class="answer-value wrong">{{ formatAnswer(wrong.user_answer) }}</span>
                </div>
                <div class="answer-item">
                  <span class="answer-label">正确答案：</span>
                  <span class="answer-value correct">{{ formatAnswer(wrong.correct_answer) }}</span>
                </div>
              </div>
              <div v-if="wrong.explanation" class="wrong-explanation">
                <strong>解析：</strong>{{ wrong.explanation }}
              </div>
              <div v-if="wrong.knowledge_points?.length" class="knowledge-points">
                <el-tag
                  v-for="point in wrong.knowledge_points"
                  :key="point"
                  size="small"
                  type="warning"
                >
                  {{ point }}
                </el-tag>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 操作按钮 -->
        <div class="action-buttons">
          <el-button size="large" @click="$router.back()">
            <el-icon><Back /></el-icon> 返回
          </el-button>
          <el-button type="primary" size="large" @click="$router.push({ name: 'practice-list' })">
            <el-icon><Document /></el-icon> 继续练习
          </el-button>
          <el-button
            v-if="result?.wrong_questions?.length"
            type="warning"
            size="large"
            @click="handlePracticeWrong"
          >
            <el-icon><Refresh /></el-icon> 练习错题
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Document,
  Select,
  Close,
  TrendCharts,
  Back,
  Refresh
} from '@element-plus/icons-vue'
import { practiceSessionApi } from '@/api/practiceSession'
import type { CompleteSessionResponse, WrongQuestion } from '@/types/question'

const router = useRouter()
const route = useRoute()

const sessionId = route.params.sessionId as string

const loading = ref(false)
const result = ref<CompleteSessionResponse | null>(null)

// 获取题型统计
const getTypeStats = () => {
  if (!result.value?.statistics?.by_type) return []
  return Object.entries(result.value.statistics.by_type).map(([type, data]: [string, any]) => ({
    type,
    total: data.total,
    correct: data.correct
  }))
}

// 获取难度统计
const getDifficultyStats = () => {
  if (!result.value?.statistics?.by_difficulty) return []
  return Object.entries(result.value.statistics.by_difficulty).map(([level, data]: [string, any]) => ({
    level,
    total: data.total,
    correct: data.correct
  }))
}

// 获取主题统计
const getTopicStats = () => {
  if (!result.value?.statistics?.by_topic) return []
  return Object.entries(result.value.statistics.by_topic).map(([topic, data]: [string, any]) => ({
    topic,
    total: data.total,
    correct: data.correct
  }))
}

// 获取题型标签
const getQuestionTypeLabel = (type: string) => {
  const labelMap: Record<string, string> = {
    choice: '选择题',
    fill_blank: '填空题',
    reading: '阅读理解',
    writing: '写作题',
    speaking: '口语题',
    listening: '听力题',
    translation: '翻译题'
  }
  return labelMap[type] || type
}

// 获取类型标签
const getTypeLabel = (type: string) => {
  const labelMap: Record<string, string> = {
    choice: '选择题',
    fill_blank: '填空题',
    reading: '阅读理解',
    writing: '写作',
    speaking: '口语',
    listening: '听力'
  }
  return labelMap[type] || type
}

// 格式化答案
const formatAnswer = (answer: any) => {
  if (typeof answer === 'object') {
    return answer.key || answer.content || JSON.stringify(answer)
  }
  return String(answer)
}

// 练习错题（占位功能）
const handlePracticeWrong = () => {
  ElMessage.info('错题练习功能即将推出')
}

// 加载结果
const loadResult = async () => {
  loading.value = true
  try {
    result.value = await practiceSessionApi.getResult(sessionId)
  } catch (error) {
    ElMessage.error('加载练习结果失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadResult()
})
</script>

<style scoped>
.practice-result {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.result-detail {
  margin-top: 20px;
}

.stats-cards {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.detail-stats {
  margin-bottom: 20px;
}

.detail-stats h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.stats-list {
  padding: 16px 0;
}

.stats-item {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.stats-label {
  width: 100px;
  font-size: 14px;
}

.stats-bar {
  flex: 1;
  height: 8px;
  background: #e4e7ed;
  border-radius: 4px;
  overflow: hidden;
}

.stats-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #409eff, #67c23a);
  transition: width 0.5s;
}

.stats-value {
  width: 80px;
  text-align: right;
  font-size: 14px;
  font-weight: 600;
}

.wrong-questions {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.wrong-count {
  font-size: 14px;
  color: #f56c6c;
}

.wrong-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.wrong-item {
  padding: 16px;
  background: #fef0f0;
  border-radius: 8px;
}

.wrong-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.wrong-index {
  font-weight: 600;
  color: #f56c6c;
}

.wrong-content {
  margin-bottom: 12px;
  font-size: 15px;
  line-height: 1.6;
}

.wrong-answers {
  display: flex;
  gap: 24px;
  margin-bottom: 12px;
}

.answer-item {
  display: flex;
  gap: 8px;
  font-size: 14px;
}

.answer-label {
  color: #909399;
}

.answer-value {
  font-weight: 600;
}

.answer-value.wrong {
  color: #f56c6c;
}

.answer-value.correct {
  color: #67c23a;
}

.wrong-explanation {
  margin-bottom: 12px;
  padding: 12px;
  background: #fff;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.6;
}

.knowledge-points {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding: 20px 0;
}

.action-buttons .el-button {
  min-width: 140px;
}
</style>
