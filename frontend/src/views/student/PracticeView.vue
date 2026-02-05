<template>
  <div class="practice-view">
    <!-- 顶部进度栏 -->
    <el-affix :offset="0">
      <el-card class="progress-bar">
        <div class="progress-content">
          <div class="progress-info">
            <span class="current-index">第 {{ currentQuestionIndex + 1 }} / {{ totalQuestions }} 题</span>
            <span class="correct-rate">
              正确率：{{ ((correctCount / answeredCount) * 100 || 0).toFixed(1) }}%
              ({{ correctCount }}/{{ answeredCount }})
            </span>
          </div>
          <el-progress
            :percentage="progressPercentage"
            :stroke-width="20"
            :show-text="false"
          />
          <div class="action-buttons">
            <el-button @click="handlePause" :icon="VideoPause" circle />
            <el-button @click="showQuitDialog = true" :icon="Close" circle type="danger" />
          </div>
        </div>
      </el-card>
    </el-affix>

    <!-- 题目内容 -->
    <div v-loading="loading" class="question-area">
      <el-empty v-if="!currentQuestion && !loading" description="没有更多题目" />

      <QuestionRenderer
        v-else-if="currentQuestion"
        :key="currentQuestion.id"
        :question="currentQuestion"
        v-model="currentAnswer"
        :show-result="showResult"
        :submitted="isQuestionAnswered"
        @submit="handleSubmit"
      />
    </div>

    <!-- 底部导航栏 -->
    <el-affix position="bottom" :offset="20">
      <el-card class="navigation-bar">
        <div class="nav-buttons">
          <el-button
            :disabled="currentQuestionIndex === 0"
            @click="handlePrevious"
          >
            <el-icon><ArrowLeft /></el-icon> 上一题
          </el-button>

          <el-button
            v-if="canShowNext"
            type="primary"
            @click="handleNext"
          >
            下一题 <el-icon><ArrowRight /></el-icon>
          </el-button>
          <el-button
            v-else-if="allAnswered"
            type="success"
            @click="handleComplete"
          >
            完成练习 <el-icon><Check /></el-icon>
          </el-button>
          <el-button v-else disabled>
            请先答题
          </el-button>
        </div>
      </el-card>
    </el-affix>

    <!-- 暂停对话框 -->
    <el-dialog
      v-model="showPauseDialog"
      title="练习暂停"
      width="400px"
    >
      <p>练习已暂停，您可以稍后继续。</p>
      <template #footer>
        <el-button type="primary" @click="handleResume">继续练习</el-button>
        <el-button @click="$router.back()">返回列表</el-button>
      </template>
    </el-dialog>

    <!-- 退出确认对话框 -->
    <el-dialog
      v-model="showQuitDialog"
      title="退出练习"
      width="400px"
    >
      <p>确定要退出练习吗？进度将自动保存。</p>
      <template #footer>
        <el-button type="danger" @click="handleQuit">确定退出</el-button>
        <el-button @click="showQuitDialog = false">继续练习</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  VideoPause,
  Close,
  ArrowLeft,
  ArrowRight,
  Check
} from '@element-plus/icons-vue'
import QuestionRenderer from '@/components/question/QuestionRenderer.vue'
import { practiceSessionApi } from '@/api/practiceSession'
import type { Question, SubmitAnswerResponse } from '@/types/question'

const router = useRouter()
const route = useRoute()

const sessionId = route.params.sessionId as string

const loading = ref(false)
const currentQuestion = ref<Question | null>(null)
const currentQuestionIndex = ref(0)
const totalQuestions = ref(0)
const correctCount = ref(0)
const answeredCount = ref(0)
const showResult = ref(false)
const currentAnswer = ref<any>(null)

const showPauseDialog = ref(false)
const showQuitDialog = ref(false)

// 进度百分比
const progressPercentage = computed(() => {
  return ((currentQuestionIndex.value + 1) / totalQuestions.value) * 100
})

// 当前题是否已答
const isQuestionAnswered = computed(() => {
  return currentAnswer.value !== null && currentAnswer.value !== undefined
})

// 是否可以显示下一题按钮
const canShowNext = computed(() => {
  return currentQuestionIndex.value < totalQuestions.value - 1
})

// 是否全部答完
const allAnswered = computed(() => {
  return answeredCount.value >= totalQuestions.value
})

// 加载当前题目
const loadCurrentQuestion = async () => {
  loading.value = true
  try {
    const response = await practiceSessionApi.getCurrentQuestion(sessionId)
    currentQuestion.value = response.question
    currentQuestionIndex.value = response.question_index
    totalQuestions.value = response.total
    currentAnswer.value = response.previous_answer ?? null
    showResult.value = response.is_answered

    // 更新统计（简化处理，实际应从会话详情获取）
    if (response.is_answered) {
      answeredCount.value = Math.max(answeredCount.value, response.question_index + 1)
    }
  } catch (error) {
    ElMessage.error('加载题目失败')
  } finally {
    loading.value = false
  }
}

// 提交答案
const handleSubmit = async (answer: any) => {
  try {
    const response = await practiceSessionApi.submitAnswer(sessionId, { answer }) as SubmitAnswerResponse

    showResult.value = true
    if (response.is_completed) {
      ElMessage.success('练习完成！')
      await router.push({
        name: 'practice-result',
        params: { sessionId }
      })
      return
    }

    // 更新统计
    if (response.is_correct) {
      correctCount.value = response.correct_count
    }
    answeredCount.value = response.question_count
  } catch (error) {
    ElMessage.error('提交答案失败')
  }
}

// 上一题
const handlePrevious = async () => {
  try {
    const response = await practiceSessionApi.navigate(sessionId, { direction: 'previous' })
    currentQuestion.value = response.question
    currentQuestionIndex.value = response.question_index
    currentAnswer.value = response.previous_answer ?? null
    showResult.value = response.is_answered
  } catch (error) {
    ElMessage.error('切换题目失败')
  }
}

// 下一题
const handleNext = async () => {
  try {
    const response = await practiceSessionApi.navigate(sessionId, { direction: 'next' })
    currentQuestion.value = response.question
    currentQuestionIndex.value = response.question_index
    currentAnswer.value = response.previous_answer ?? null
    showResult.value = response.is_answered
  } catch (error) {
    ElMessage.error('切换题目失败')
  }
}

// 暂停
const handlePause = async () => {
  try {
    await practiceSessionApi.pause(sessionId)
    showPauseDialog.value = true
  } catch (error) {
    ElMessage.error('暂停失败')
  }
}

// 继续
const handleResume = async () => {
  try {
    const response = await practiceSessionApi.resume(sessionId)
    currentQuestion.value = response.question
    currentQuestionIndex.value = response.question_index
    currentAnswer.value = response.previous_answer ?? null
    showResult.value = response.is_answered
    showPauseDialog.value = false
    ElMessage.success('继续练习')
  } catch (error) {
    ElMessage.error('继续失败')
  }
}

// 完成
const handleComplete = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要完成练习吗？完成后将生成练习报告。',
      '确认完成',
      { type: 'warning' }
    )

    loading.value = true
    await practiceSessionApi.complete(sessionId)
    ElMessage.success('练习完成！')

    await router.push({
      name: 'practice-result',
      params: { sessionId }
    })
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('完成练习失败')
    }
  } finally {
    loading.value = false
  }
}

// 退出
const handleQuit = async () => {
  try {
    await practiceSessionApi.pause(sessionId)
    showQuitDialog.value = false
    await router.push({ name: 'practice-list' })
  } catch (error) {
    ElMessage.error('退出失败')
  }
}

// 防止页面刷新丢失数据
const handleBeforeUnload = (e: BeforeUnloadEvent) => {
  e.preventDefault()
  e.returnValue = ''
}

onMounted(() => {
  loadCurrentQuestion()
  window.addEventListener('beforeunload', handleBeforeUnload)
})

onUnmounted(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
})
</script>

<style scoped>
.practice-view {
  min-height: 100vh;
  padding-bottom: 100px;
}

.progress-bar {
  border-radius: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.progress-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.progress-info {
  flex: 1;
  display: flex;
  gap: 20px;
  font-size: 14px;
}

.correct-rate {
  color: #67c23a;
  font-weight: 600;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.question-area {
  max-width: 900px;
  margin: 20px auto;
  min-height: 400px;
}

.navigation-bar {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.nav-buttons {
  display: flex;
  justify-content: center;
  gap: 16px;
}

.nav-buttons .el-button {
  min-width: 120px;
}
</style>
