<template>
  <div class="speaking-page">
    <el-container>
      <el-header>
        <div class="header-content">
          <h1>口语练习</h1>
          <el-menu
            :default-active="activeMenu"
            mode="horizontal"
            :ellipsis="false"
            router
          >
            <el-menu-item index="/student">
              仪表板
            </el-menu-item>
            <el-menu-item index="/student/learning">
              学习内容
            </el-menu-item>
            <el-menu-item index="/student/speaking">
              口语练习
            </el-menu-item>
            <el-menu-item index="/student/progress">
              学习进度
            </el-menu-item>
            <el-menu-item
              index="/"
              @click="handleLogout"
            >
              退出
            </el-menu-item>
          </el-menu>
        </div>
      </el-header>

      <el-main>
        <el-card>
          <template #header>
            <h3>选择对话场景</h3>
          </template>

          <el-row :gutter="20">
            <el-col
              v-for="scenario in scenarios"
              :key="scenario.value"
              :span="8"
            >
              <el-card
                class="scenario-card"
                :class="{ selected: selectedScenario === scenario.value }"
                @click="selectedScenario = scenario.value"
              >
                <div class="scenario-icon">
                  💬
                </div>
                <h4>{{ scenario.label }}</h4>
                <p>{{ scenario.description }}</p>
                <el-tag
                  :type="selectedScenario === scenario.value ? 'success' : 'info'"
                  size="small"
                >
                  {{ scenario.level }}
                </el-tag>
              </el-card>
            </el-col>
          </el-row>

          <div class="action-bar mt-3">
            <el-button
              type="primary"
              size="large"
              :disabled="!selectedScenario"
              @click="startConversation"
            >
              开始对话
            </el-button>
          </div>
        </el-card>

        <!-- 对话历史 -->
        <el-card class="mt-2">
          <template #header>
            <div class="card-header">
              <h3>对话历史</h3>
              <el-button
                type="primary"
                link
                @click="loadConversations"
              >
                刷新
              </el-button>
            </div>
          </template>

          <el-empty
            v-if="conversationHistory.length === 0"
            description="暂无对话记录"
          />

          <el-timeline v-else>
            <el-timeline-item
              v-for="conv in conversationHistory"
              :key="conv.id"
              :timestamp="conv.date"
              placement="top"
            >
              <el-card>
                <div class="history-item">
                  <div class="history-header">
                    <h4>{{ conv.scenario }}</h4>
                    <el-tag size="small">
                      {{ conv.duration }}
                    </el-tag>
                  </div>
                  <p>{{ conv.messages }} 条对话消息</p>
                </div>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-main>
    </el-container>

    <!-- 对话弹窗 - 增强版 -->
    <el-dialog
      v-model="dialogVisible"
      width="800px"
      :close-on-click-modal="false"
      class="conversation-dialog"
    >
      <template #header>
        <div class="dialog-header">
          <div class="header-left">
            <h3>{{ currentScenario?.label }}</h3>
            <el-tag
              :type="statusType"
              size="small"
            >
              {{ statusText }}
            </el-tag>
          </div>
          <div class="header-right">
            <el-button
              link
              @click="handleComplete"
            >
              结束练习
            </el-button>
          </div>
        </div>
      </template>

      <!-- 对话状态指示器 -->
      <div
        v-if="status === 'active'"
        class="conversation-status"
      >
        <div class="scenario-info">
          <el-tag type="primary">
            {{ currentScenario?.label }}
          </el-tag>
          <el-tag type="info">
            Level {{ currentScenario?.level }}
          </el-tag>
        </div>

        <div class="progress-indicator">
          <span>第 {{ currentRound }} 轮</span>
          <el-progress
            :percentage="roundProgress"
            :stroke-width="6"
            :show-text="false"
          />
          <span>目标: 5-8 轮</span>
        </div>

        <div class="timer">
          <el-icon><Timer /></el-icon>
          <span>{{ formatTime(elapsedTime) }}</span>
        </div>
      </div>

      <!-- 消息区域 -->
      <div class="conversation-box">
        <div
          ref="messagesRef"
          class="messages"
        >
          <div
            v-for="(msg, index) in messages"
            :key="index"
            :class="['message', msg.role === 'user' ? 'user' : 'assistant']"
          >
            <!-- 用户消息 -->
            <template v-if="msg.role === 'user'">
              <div class="message user-message">
                <div class="avatar">
                  👤
                </div>
                <div class="content">
                  <p>{{ msg.content }}</p>
                  <span class="time">{{ formatTimestamp(msg.timestamp) }}</span>
                </div>
              </div>
            </template>

            <!-- AI 消息带评分 -->
            <template v-else>
              <div class="message assistant-message">
                <div class="content">
                  <p>{{ msg.content }}</p>

                  <!-- 评分胶囊 -->
                  <div
                    v-if="msg.scores"
                    class="score-pills"
                  >
                    <el-tag
                      :type="getScoreType(msg.scores?.fluency)"
                      size="small"
                      class="score-tag"
                    >
                      流利度 {{ formatScore(msg.scores?.fluency) }}
                    </el-tag>
                    <el-tag
                      :type="getScoreType(msg.scores?.vocabulary)"
                      size="small"
                      class="score-tag"
                    >
                      词汇 {{ formatScore(msg.scores?.vocabulary) }}
                    </el-tag>
                    <el-tag
                      :type="getScoreType(msg.scores?.grammar)"
                      size="small"
                      class="score-tag"
                    >
                      语法 {{ formatScore(msg.scores?.grammar) }}
                    </el-tag>
                    <el-button
                      link
                      type="primary"
                      size="small"
                      class="feedback-btn"
                      @click="showFeedback(msg)"
                    >
                      查看反馈
                    </el-button>
                  </div>

                  <span class="time">{{ formatTimestamp(msg.timestamp) }}</span>
                </div>
                <div class="avatar">
                  🤖
                </div>
              </div>
            </template>

            <el-icon
              v-if="loading"
              class="is-loading"
            >
              <Loading />
            </el-icon>
          </div>
        </div>

        <!-- 学习建议横幅 -->
        <div
          v-if="latestRecommendation && status === 'active'"
          class="learning-banner"
        >
          <el-alert
            type="info"
            :closable="false"
            show-icon
          >
            <template #default>
              <span class="tip-icon">💡</span>
              <span>{{ latestRecommendation.tip }}</span>
            </template>
          </el-alert>
        </div>

        <!-- 输入区域 -->
        <div class="input-area">
          <el-input
            v-model="inputMessage"
            type="textarea"
            :rows="2"
            placeholder="输入你的回复..."
            :disabled="status !== 'active'"
            @keydown.enter.exact="handleSend"
          />

          <div class="input-actions">
            <el-button
              circle
              :icon="Microphone"
              :disabled="status !== 'active'"
            />
            <el-button
              type="primary"
              :loading="sending"
              :disabled="!inputMessage.trim() || status !== 'active'"
              @click="handleSend"
            >
              发送
            </el-button>
          </div>
        </div>
      </div>

      <!-- 完成后的总结界面 -->
      <div
        v-if="status === 'completed'"
        class="completion-summary"
      >
        <el-result
          icon="success"
          title="练习完成！"
          :sub-title="`共进行 ${totalRounds} 轮对话，用时 ${formatDuration(elapsedTime)}`"
        >
          <template #extra>
            <!-- 快速统计 -->
            <div class="quick-stats">
              <el-statistic
                title="流利度"
                :value="finalScores.fluency"
                suffix="/100"
                :precision="1"
              />
              <el-statistic
                title="词汇量"
                :value="finalScores.vocabulary"
                suffix="/100"
                :precision="1"
              />
              <el-statistic
                title="语法"
                :value="finalScores.grammar"
                suffix="/100"
                :precision="1"
              />
              <el-statistic
                title="综合"
                :value="finalScores.overall"
                suffix="/100"
                :precision="1"
              />
            </div>

            <el-button
              type="primary"
              @click="viewFullFeedback"
            >
              查看详细反馈
            </el-button>
            <el-button @click="startNew">
              开始新练习
            </el-button>
          </template>
        </el-result>
      </div>
    </el-dialog>

    <!-- AI 反馈抽屉 -->
    <el-drawer
      v-model="feedbackVisible"
      title="AI 学习反馈"
      direction="btt"
      size="45%"
      class="feedback-drawer"
    >
      <div
        v-if="currentFeedback"
        class="feedback-content"
      >
        <!-- 整体评分概览 -->
        <div class="score-overview">
          <h4>评分概览</h4>
          <el-row
            :gutter="16"
            class="mt-2"
          >
            <el-col
              v-for="item in scoreOverview"
              :key="item.label"
              :span="6"
            >
              <div class="score-card">
                <el-progress
                  type="dashboard"
                  :percentage="item.score"
                  :color="getProgressColor(item.score)"
                  :width="80"
                />
                <p>{{ item.label }}</p>
                <span class="score-value">{{ item.score }}</span>
              </div>
            </el-col>
          </el-row>
        </div>

        <el-divider />

        <!-- 详细反馈 -->
        <!-- 优势 -->
        <div
          v-if="currentFeedback.strengths?.length"
          class="feedback-section"
        >
          <h4>
            <el-icon class="success-icon">
              <Check />
            </el-icon> 做得好的地方
          </h4>
          <ul>
            <li
              v-for="item in currentFeedback.strengths"
              :key="item"
            >
              {{ item }}
            </li>
          </ul>
        </div>

        <!-- 改进建议 -->
        <div
          v-if="currentFeedback.improvements?.length"
          class="feedback-section"
        >
          <h4>
            <el-icon class="warning-icon">
              <TrendCharts />
            </el-icon> 需要改进
          </h4>
          <ul>
            <li
              v-for="item in currentFeedback.improvements"
              :key="item"
            >
              {{ item }}
            </li>
          </ul>
        </div>

        <!-- 语法注释 -->
        <div
          v-if="currentFeedback.grammar_notes"
          class="feedback-section"
        >
          <h4>
            <el-icon class="info-icon">
              <Document />
            </el-icon> 语法要点
          </h4>
          <p>{{ currentFeedback.grammar_notes }}</p>
        </div>

        <!-- 学习建议 -->
        <div
          v-if="currentFeedback.recommendations?.length"
          class="feedback-section recommendations"
        >
          <h4>
            <el-icon class="star-icon">
              <Star />
            </el-icon> 学习建议
          </h4>
          <div class="recommendation-tags">
            <el-tag
              v-for="item in currentFeedback.recommendations"
              :key="item"
              type="warning"
              class="recommendation-tag"
              effect="plain"
            >
              {{ item }}
            </el-tag>
          </div>
        </div>

        <!-- 综合 AI 评语 -->
        <div
          v-if="currentFeedback.feedback"
          class="feedback-section"
        >
          <h4><el-icon><ChatDotSquare /></el-icon> AI 评语</h4>
          <p class="ai-feedback">
            {{ currentFeedback.feedback }}
          </p>
        </div>
      </div>

      <el-empty
        v-else
        description="暂无反馈数据"
      />
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Loading,
  Timer,
  Check,
  TrendCharts,
  Document,
  Star,
  ChatDotSquare,
  Microphone
} from '@element-plus/icons-vue'
// useAuthStore imported but not currently used - reserved for future auth features
// import { useAuthStore } from '@/stores/auth'

// 类型定义
interface MessageScore {
  fluency?: number
  vocabulary?: number
  grammar?: number
  overall?: number
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date | string
  scores?: MessageScore
  feedback?: string
}

interface ConversationFeedback {
  fluency_score: number
  vocabulary_score: number
  grammar_score: number
  overall_score: number
  feedback: string
  strengths: string[]
  improvements: string[]
  grammar_notes?: string
  vocabulary_notes?: string
  recommendations: string[]
}

interface LearningRecommendation {
  tip: string
  type: 'grammar' | 'vocabulary' | 'pronunciation' | 'fluency' | string
}

const route = useRoute()
const router = useRouter()

// 基础状态
const activeMenu = computed(() => route.path)
const selectedScenario = ref('')
const dialogVisible = ref(false)
const loading = ref(false)
const sending = ref(false)
const inputMessage = ref('')
const messagesRef = ref<HTMLElement>()

// 对话状态
const status = ref<'idle' | 'active' | 'paused' | 'completed'>('idle')
const currentRound = ref(0)
const elapsedTime = ref(0)
const timerInterval = ref<number | null>(null)

// 对话历史记录类型
interface ConversationHistoryItem {
  id: string
  scenario: string
  date: string
  duration: string
  messages: number
}

// 消息数据
const messages = ref<Message[]>([])
const conversationHistory = ref<ConversationHistoryItem[]>([])

// 评分和反馈
const currentFeedback = ref<ConversationFeedback | null>(null)
const feedbackVisible = ref(false)
const finalScores = ref<MessageScore>({})

const latestRecommendation = ref<LearningRecommendation | null>(null)

// 计算属性
const currentScenario = computed(() =>
  scenarios.find(s => s.value === selectedScenario.value)
)

const roundProgress = computed(() => {
  const target = 8
  return Math.min((currentRound.value / target) * 100, 100)
})

const scoreOverview = computed(() => {
  if (!currentFeedback.value) return []
  const f = currentFeedback.value
  return [
    { label: '流利度', score: f.fluency_score || 0 },
    { label: '词汇', score: f.vocabulary_score || 0 },
    { label: '语法', score: f.grammar_score || 0 },
    { label: '综合', score: f.overall_score || 0 }
  ]
})

const totalRounds = computed(() => messages.value.filter(m => m.role === 'user').length)

// 状态文本和类型
const statusText = computed(() => {
  switch (status.value) {
    case 'active': return '进行中'
    case 'paused': return '已暂停'
    case 'completed': return '已完成'
    default: return '未开始'
  }
})

const statusType = computed(() => {
  switch (status.value) {
    case 'active': return 'primary'
    case 'completed': return 'success'
    default: return 'info'
  }
})

// 场景配置
const scenarios = [
  {
    value: 'daily_greeting',
    label: '日常问候',
    description: '练习日常问候和闲聊',
    level: 'A1-A2'
  },
  {
    value: 'shopping',
    label: '购物场景',
    description: '在商店购物的对话练习',
    level: 'A2-B1'
  },
  {
    value: 'restaurant',
    label: '餐厅点餐',
    description: '在餐厅点餐和交流',
    level: 'A2-B1'
  },
  {
    value: 'directions',
    label: '问路指路',
    description: '询问和指示方向的对话',
    level: 'B1-B2'
  },
  {
    value: 'job_interview',
    label: '求职面试',
    description: '模拟求职面试场景',
    level: 'B2-C1'
  },
  {
    value: 'business_meeting',
    label: '商务会议',
    description: '商务会议讨论场景',
    level: 'C1-C2'
  }
]

// 方法
function getScoreType(score?: number): 'success' | 'warning' | 'info' | 'danger' {
  if (!score) return 'info'
  if (score >= 80) return 'success'
  if (score >= 60) return 'warning'
  return 'danger'
}

function formatScore(score?: number): string {
  return score ? score.toFixed(0) : '-'
}

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function formatTimestamp(timestamp: string | Date): string {
  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp
  return formatTime(Math.floor(date.getTime() / 1000))
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  if (mins > 0) {
    return `${mins} 分 ${secs} 秒`
  }
  return `${secs} 秒`
}

function getProgressColor(score: number): string {
  if (score >= 80) return '#67c23a'
  if (score >= 60) return '#e6a23c'
  return '#f56c6c'
}

function startTimer() {
  stopTimer()
  timerInterval.value = window.setInterval(() => {
    elapsedTime.value++
  }, 1000)
}

function stopTimer() {
  if (timerInterval.value) {
    clearInterval(timerInterval.value)
    timerInterval.value = null
  }
}

async function startConversation() {
  dialogVisible.value = true
  status.value = 'active'
  messages.value = []
  currentRound.value = 0
  elapsedTime.value = 0
  currentFeedback.value = null
  latestRecommendation.value = null
  startTimer()

  // 添加 AI 开场白
  const greeting = getScenarioGreeting(selectedScenario.value)
  messages.value.push({
    role: 'assistant',
    content: greeting,
    timestamp: new Date()
  })

  nextTick(() => {
    scrollToBottom()
  })
}

function getScenarioGreeting(scenario: string): string {
  const greetings: Record<string, string> = {
    daily_greeting: 'Hello! How are you today? Did you sleep well last night?',
    shopping: 'Welcome to our store! How can I help you today?',
    restaurant: 'Good evening! Do you have a reservation? How many people?',
    directions: 'Excuse me, could you help me? I\'m looking for the train station.',
    job_interview: 'Thank you for coming in today. Tell me about yourself.',
    business_meeting: 'Let\'s get started. Shall we begin with the agenda review?'
  }
  return greetings[scenario] || 'Hello! How can I help you today?'
}

async function handleSend() {
  if (!inputMessage.value.trim() || status.value !== 'active') return

  const userMsg = inputMessage.value
  inputMessage.value = ''

  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: userMsg,
    timestamp: new Date()
  })

  await nextTick()
  scrollToBottom()

  sending.value = true

  try {
    // 调用后端 API（如果可用）或使用模拟响应
    const response = await sendMessageToBackend(userMsg)

    messages.value.push({
      role: 'assistant',
      content: response.message,
      timestamp: new Date(),
      scores: response.scores
    })

    currentRound.value++

    // 更新学习建议
    if (response.recommendation) {
      latestRecommendation.value = response.recommendation
    }
  } catch (error) {
    ElMessage.error('发送失败，请重试')
  } finally {
    sending.value = false
    await nextTick()
    scrollToBottom()
  }
}

async function sendMessageToBackend(message: string) {
  // TODO: 集成真实 API
  // 目前使用模拟数据
  await new Promise(resolve => setTimeout(resolve, 1500))

  return {
    message: getMockResponse(message),
    scores: {
      fluency: 65 + Math.floor(Math.random() * 25),
      vocabulary: 70 + Math.floor(Math.random() * 20),
      grammar: 60 + Math.floor(Math.random() * 30),
      overall: 65 + Math.floor(Math.random() * 25)
    },
    recommendation: {
      tip: '尝试使用更丰富的词汇来表达',
      type: 'vocabulary'
    }
  }
}

function getMockResponse(userMessage: string): string {
  const responses = [
    'That\'s interesting! Tell me more.',
    'I understand. Go on.',
    'Could you explain that in more detail?',
    'Your vocabulary is improving! Keep practicing.',
    'Good sentence structure! Try to use more complex grammar.'
  ]

  const lowerMsg = userMessage.toLowerCase()
  if (lowerMsg.includes('thank') || lowerMsg.includes('thanks')) {
    return 'You\'re welcome! Is there anything else I can help you with?'
  } else if (lowerMsg.includes('goodbye') || lowerMsg.includes('bye')) {
    return 'Goodbye! It was nice talking to you. Have a great day!'
  }

  return responses[Math.floor(Math.random() * responses.length)] || 'Could you please say that again?'
}

function scrollToBottom() {
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

function showFeedback(message: Message) {
  if (message.scores) {
    currentFeedback.value = {
      fluency_score: message.scores.fluency || 0,
      vocabulary_score: message.scores.vocabulary || 0,
      grammar_score: message.scores.grammar || 0,
      overall_score: message.scores.overall || 0,
      feedback: message.feedback || 'Good effort!',
      strengths: ['语法结构正确', '发音清晰'],
      improvements: ['可以增加词汇多样性', '注意时态一致性'],
      grammar_notes: '注意过去时和现在时的使用',
      vocabulary_notes: '尝试使用更高级的词汇',
      recommendations: ['每天学习5个新单词', '练习过去时态']
    }
    feedbackVisible.value = true
  }
}

function viewFullFeedback() {
  feedbackVisible.value = true
}

async function handleComplete() {
  try {
    await ElMessageBox.confirm(
      `确定要结束对话吗？目前已完成 ${totalRounds.value} 轮对话。`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '继续练习',
        type: 'warning'
      }
    )

    // 生成最终评分
    finalScores.value = {
      fluency: 70,
      vocabulary: 72,
      grammar: 68,
      overall: 70
    }

    currentFeedback.value = {
      fluency_score: 70,
      vocabulary_score: 72,
      grammar_score: 68,
      overall_score: 70,
      feedback: '整体表现不错！继续努力！',
      strengths: ['对话流畅', '语法基本正确', '词汇运用恰当'],
      improvements: ['可以增加复杂句型', '注意细节表达'],
      grammar_notes: '建议复习时态和语序',
      vocabulary_notes: '多积累高级词汇',
      recommendations: ['练习长难句', '背诵常用短语']
    }

    status.value = 'completed'
    stopTimer()

    // 保存到历史
    const scenarioLabel = currentScenario.value?.label || '未知场景'
    conversationHistory.value.unshift({
      id: Date.now().toString(),
      scenario: scenarioLabel,
      date: new Date().toLocaleString('zh-CN'),
      duration: formatDuration(elapsedTime.value),
      messages: totalRounds.value
    })

  } catch {
    // 用户取消
  }
}

function startNew() {
  status.value = 'idle'
  messages.value = []
  currentRound.value = 0
  elapsedTime.value = 0
  currentFeedback.value = null
  finalScores.value = {}
  latestRecommendation.value = null
  selectedScenario.value = ''
}

async function loadConversations() {
  // TODO: 从后端 API 加载
  conversationHistory.value = [
    {
      id: '1',
      scenario: '日常问候',
      date: '2026-02-01 14:30',
      duration: '5 分',
      messages: 8
    }
  ]
}

function handleLogout() {
  router.push('/login')
}

// 组件挂载时加载历史
loadConversations()
</script>

<style scoped>
.speaking-page {
  min-height: 100vh;
  background: #f5f7fa;
}

.el-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0 20px;
}

.header-content {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-content h1 {
  margin: 0;
  font-size: 24px;
  color: white;
}

.el-main {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
}

.scenario-card {
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 20px;
  text-align: center;
}

.scenario-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.scenario-card.selected {
  border: 2px solid #667eea;
  background: #f0f4ff;
}

.scenario-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.scenario-card h4 {
  margin: 0 0 8px;
  color: #333;
}

.scenario-card p {
  color: #666;
  font-size: 14px;
  margin: 8px 0;
}

.action-bar {
  text-align: center;
}

/* 对话对话框样式 */
.conversation-dialog .el-dialog__body {
  padding: 0;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h3 {
  margin: 0;
  font-size: 18px;
}

/* 状态指示器 */
.conversation-status {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background: #f8f9fa;
  border-bottom: 1px solid #eee;
}

.scenario-info {
  display: flex;
  gap: 8px;
}

.progress-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.progress-indicator span {
  font-size: 12px;
  color: #666;
}

.timer {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #666;
  font-variant-numeric: tabular-nums;
}

/* 对话区域 */
.conversation-box {
  display: flex;
  flex-direction: column;
  height: 500px;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #f5f7fa;
}

.message {
  margin-bottom: 16px;
  display: flex;
  gap: 8px;
}

.user-message {
  justify-content: flex-end;
}

.assistant-message {
  justify-content: flex-start;
}

.message .avatar {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e0e7ff;
  border-radius: 50%;
  font-size: 16px;
  flex-shrink: 0;
}

.message .content {
  max-width: 70%;
}

.message .content p {
  margin: 0 0 4px;
  word-wrap: break-word;
}

.message .content .time {
  font-size: 11px;
  color: #999;
}

.user-message .message .content {
  background: #667eea;
  color: white;
  padding: 10px 14px;
  border-radius: 12px;
  border-bottom-right-radius: 4px;
}

.assistant-message .message .content {
  background: white;
  color: #333;
  padding: 10px 14px;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
  border-bottom-left-radius: 4px;
}

/* 评分胶囊 */
.score-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.score-tag {
  font-size: 11px;
}

.feedback-btn {
  font-size: 11px;
}

/* 学习建议横幅 */
.learning-banner {
  padding: 0 16px 12px 16px;
}

.learning-banner .tip-icon {
  font-size: 16px;
  margin-right: 8px;
}

/* 输入区域 */
.input-area {
  border-top: 1px solid #eee;
  padding: 16px;
  background: white;
}

.input-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

/* 完成总结 */
.completion-summary {
  padding: 32px 16px;
}

.quick-stats {
  display: flex;
  justify-content: space-around;
  margin: 24px 0;
}

/* 反馈抽屉 */
.feedback-content {
  padding: 20px;
}

.score-overview h4 {
  margin: 0 0 16px;
}

.score-card {
  text-align: center;
}

.score-card p {
  margin: 8px 0 4px;
  font-size: 12px;
  color: #666;
}

.score-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.feedback-section {
  margin: 20px 0;
}

.feedback-section h4 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 12px;
}

.feedback-section ul {
  margin: 0;
  padding-left: 20px;
}

.feedback-section li {
  margin: 4px 0;
  color: #666;
}

.feedback-section p {
  color: #666;
  line-height: 1.6;
}

.ai-feedback {
  background: #f8f9fa;
  padding: 12px;
  border-radius: 6px;
  color: #666;
}

.recommendation-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.recommendation-tag {
  margin: 0;
}

.history-item {
  padding: 8px 0;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.history-header h4 {
  margin: 0;
  color: #333;
}

.history-item p {
  margin: 4px 0 0;
  color: #666;
  font-size: 14px;
}

.mt-2 {
  margin-top: 20px;
}

.is-loading {
  display: block;
  text-align: center;
  color: #999;
  margin: 12px 0;
}

/* 图标颜色 */
.success-icon { color: #67c23a; }
.warning-icon { color: #e6a23c; }
.info-icon { color: #409eff; }
.star-icon { color: #ff9800; }
</style>
