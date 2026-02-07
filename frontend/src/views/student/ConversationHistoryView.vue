<template>
  <div class="conversation-history-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <el-page-header
        title="返回"
        @back="goBack"
      >
        <template #content>
          <span class="page-title">对话历史</span>
        </template>
      </el-page-header>
      <div class="header-actions">
        <el-input
          v-model="searchQuery"
          placeholder="搜索对话..."
          :prefix-icon="Search"
          clearable
          style="width: 250px"
        />
        <el-select
          v-model="filterScenario"
          placeholder="筛选场景"
          clearable
          style="width: 150px"
        >
          <el-option
            v-for="scenario in scenarios"
            :key="scenario.value"
            :label="scenario.label"
            :value="scenario.value"
          />
        </el-select>
      </div>
    </div>

    <!-- 对话列表 -->
    <div
      v-loading="isLoading"
      class="history-list"
    >
      <el-empty
        v-if="!isLoading && filteredConversations.length === 0"
        description="暂无对话历史"
      />

      <transition-group
        name="list"
        tag="div"
        class="conversation-grid"
      >
        <div
          v-for="conversation in filteredConversations"
          :key="conversation.id"
          :class="['conversation-card', { 'conversation-card-completed': conversation.status === 'completed' }]"
          @click="viewConversation(conversation.id)"
        >
          <div class="card-header">
            <div class="scenario-info">
              <el-icon
                :size="24"
                :color="getScenarioColor(conversation.scenario)"
              >
                <component :is="getScenarioIcon(conversation.scenario)" />
              </el-icon>
              <div>
                <h3>{{ getScenarioName(conversation.scenario) }}</h3>
                <span class="level-badge">{{ conversation.level }}</span>
              </div>
            </div>
            <el-tag
              :type="getStatusType(conversation.status)"
              size="small"
            >
              {{ getStatusText(conversation.status) }}
            </el-tag>
          </div>

          <div class="card-body">
            <div class="stats-row">
              <div class="stat-item">
                <el-icon><ChatDotRound /></el-icon>
                <span>{{ conversation.message_count }} 条消息</span>
              </div>
              <div
                v-if="conversation.duration"
                class="stat-item"
              >
                <el-icon><Clock /></el-icon>
                <span>{{ formatDuration(conversation.duration) }}</span>
              </div>
            </div>

            <div
              v-if="conversation.scores"
              class="score-preview"
            >
              <div class="score-circle">
                <el-progress
                  type="circle"
                  :percentage="conversation.scores.overall_score || 0"
                  :width="60"
                  :stroke-width="6"
                />
              </div>
              <span class="score-label">综合评分</span>
            </div>

            <div class="card-footer">
              <span class="date">{{ formatDate(conversation.started_at) }}</span>
              <el-button
                type="primary"
                link
              >
                查看详情
              </el-button>
            </div>
          </div>
        </div>
      </transition-group>
    </div>

    <!-- 对话详情抽屉 -->
    <el-drawer
      v-model="showDetailDrawer"
      title="对话详情"
      direction="rtl"
      size="600px"
    >
      <div
        v-if="selectedConversation"
        class="detail-content"
      >
        <!-- 对话信息 -->
        <div class="detail-header">
          <h3>{{ getScenarioName(selectedConversation.scenario) }}</h3>
          <div class="detail-meta">
            <el-tag size="small">
              {{ selectedConversation.level }}
            </el-tag>
            <el-tag
              :type="getStatusType(selectedConversation.status)"
              size="small"
            >
              {{ getStatusText(selectedConversation.status) }}
            </el-tag>
            <span>{{ formatDate(selectedConversation.started_at) }}</span>
          </div>
        </div>

        <!-- 评分信息 -->
        <div
          v-if="selectedConversation.scores"
          class="detail-scores"
        >
          <h4>综合评分</h4>
          <div class="overall-score">
            <el-progress
              type="circle"
              :percentage="selectedConversation.scores.overall_score || 0"
              :width="120"
            >
              <template #default="{ percentage }">
                <span class="score-text">{{ percentage }}</span>
              </template>
            </el-progress>
          </div>

          <div class="score-breakdown">
            <div class="score-item">
              <span>流利度</span>
              <el-progress
                :percentage="selectedConversation.scores.fluency_score || 0"
                :stroke-width="8"
                :show-text="false"
              />
            </div>
            <div class="score-item">
              <span>词汇量</span>
              <el-progress
                :percentage="selectedConversation.scores.vocabulary_score || 0"
                :stroke-width="8"
                :show-text="false"
              />
            </div>
            <div class="score-item">
              <span>语法</span>
              <el-progress
                :percentage="selectedConversation.scores.grammar_score || 0"
                :stroke-width="8"
                :show-text="false"
              />
            </div>
          </div>

          <div
            v-if="selectedConversation.scores.feedback"
            class="feedback-box"
          >
            <h5>评价</h5>
            <p>{{ selectedConversation.scores.feedback }}</p>
          </div>
        </div>

        <!-- 对话记录 -->
        <div class="detail-messages">
          <h4>对话记录</h4>
          <div class="messages-list">
            <div
              v-for="(message, index) in selectedConversation.messages"
              :key="index"
              :class="['message-item', `message-${message.role}`]"
            >
              <div class="message-header">
                <el-icon v-if="message.role === 'user'">
                  <User />
                </el-icon>
                <el-icon v-else>
                  <ChatDotRound />
                </el-icon>
                <span class="role-label">{{ message.role === 'user' ? '你' : 'AI' }}</span>
              </div>
              <div class="message-content">
                {{ message.content }}
              </div>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="detail-actions">
          <el-button
            type="primary"
            @click="practiceAgain"
          >
            <el-icon><Refresh /></el-icon>
            再次练习
          </el-button>
          <el-button
            :disabled="selectedConversation.status === 'completed'"
            @click="continueConversation"
          >
            <el-icon><VideoPlay /></el-icon>
            继续对话
          </el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Search,
  ChatDotRound,
  Clock,
  User,
  Refresh,
  VideoPlay,
  Coffee,
  Food,
  ShoppingBag,
  Location,
  Briefcase,
  Football,
  Picture
} from '@element-plus/icons-vue'
import { getStudentConversations, getConversation } from '@/api/conversation'
import type { Conversation, ConversationScenario } from '@/types/conversation'

const router = useRouter()

// 状态
const isLoading = ref(true)
const conversations = ref<Conversation[]>([])
const searchQuery = ref('')
const filterScenario = ref<ConversationScenario | ''>('')
const showDetailDrawer = ref(false)
const selectedConversation = ref<Conversation | null>(null)

// 场景配置
const scenarios = [
  { value: 'cafe_order' as ConversationScenario, label: '咖啡店点餐', icon: Coffee, color: '#8B4513' },
  { value: 'restaurant' as ConversationScenario, label: '餐厅用餐', icon: Food, color: '#E74C3C' },
  { value: 'shopping' as ConversationScenario, label: '购物', icon: ShoppingBag, color: '#3498DB' },
  { value: 'asking_direction' as ConversationScenario, label: '问路', icon: Location, color: '#27AE60' },
  { value: 'job_interview' as ConversationScenario, label: '求职面试', icon: Briefcase, color: '#2C3E50' },
  { value: 'talking_about_hobbies' as ConversationScenario, label: '谈论爱好', icon: Football, color: '#E67E22' },
  { value: 'describing_picture' as ConversationScenario, label: '描述图片', icon: Picture, color: '#9B59B6' },
  { value: 'free_talk' as ConversationScenario, label: '自由对话', icon: ChatDotRound, color: '#1ABC9C' }
]

// 过滤后的对话列表
const filteredConversations = computed(() => {
  let result = conversations.value

  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(c =>
      getScenarioName(c.scenario).toLowerCase().includes(query)
    )
  }

  // 场景过滤
  if (filterScenario.value) {
    result = result.filter(c => c.scenario === filterScenario.value)
  }

  // 按时间倒序
  return result.sort((a, b) =>
    new Date(b.started_at).getTime() - new Date(a.started_at).getTime()
  )
})

// 获取场景名称
const getScenarioName = (scenario: ConversationScenario): string => {
  const found = scenarios.find(s => s.value === scenario)
  return found?.label || scenario
}

// 获取场景图标
const getScenarioIcon = (scenario: ConversationScenario) => {
  const found = scenarios.find(s => s.value === scenario)
  return found?.icon || ChatDotRound
}

// 获取场景颜色
const getScenarioColor = (scenario: ConversationScenario): string => {
  const found = scenarios.find(s => s.value === scenario)
  return found?.color || '#409EFF'
}

// 获取状态类型
const getStatusType = (status: string) => {
  const types: Record<string, any> = {
    'in_progress': 'primary',
    'completed': 'success',
    'abandoned': 'info'
  }
  return types[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string): string => {
  const texts: Record<string, string> = {
    'in_progress': '进行中',
    'completed': '已完成',
    'abandoned': '已放弃'
  }
  return texts[status] || status
}

// 格式化日期
const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  // 小于 1 天
  if (diff < 24 * 60 * 60 * 1000) {
    const hours = Math.floor(diff / (60 * 60 * 1000))
    if (hours < 1) {
      const minutes = Math.floor(diff / (60 * 1000))
      return minutes < 1 ? '刚刚' : `${minutes} 分钟前`
    }
    return `${hours} 小时前`
  }

  // 小于 7 天
  if (diff < 7 * 24 * 60 * 60 * 1000) {
    const days = Math.floor(diff / (24 * 60 * 60 * 1000))
    return `${days} 天前`
  }

  // 格式化为具体日期
  return date.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 格式化时长
const formatDuration = (seconds: number): string => {
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return minutes > 0 ? `${minutes} 分 ${secs} 秒` : `${secs} 秒`
}

// 加载对话列表
const loadConversations = async () => {
  isLoading.value = true
  try {
    const result = await getStudentConversations()
    conversations.value = result.conversations || []
  } catch (error) {
    console.error('Failed to load conversations:', error)
  } finally {
    isLoading.value = false
  }
}

// 查看对话详情
const viewConversation = async (conversationId: string) => {
  try {
    const conversation = await getConversation(conversationId)
    selectedConversation.value = conversation
    showDetailDrawer.value = true
  } catch (error) {
    console.error('Failed to load conversation:', error)
  }
}

// 再次练习
const practiceAgain = () => {
  showDetailDrawer.value = false
  if (selectedConversation.value) {
    router.push({
      path: '/student/conversation',
      query: { scenario: selectedConversation.value.scenario }
    })
  }
}

// 继续对话
const continueConversation = () => {
  showDetailDrawer.value = false
  if (selectedConversation.value) {
    router.push({
      path: '/student/conversation',
      query: { conversationId: selectedConversation.value.id }
    })
  }
}

// 返回
const goBack = () => {
  router.back()
}

// 组件挂载
onMounted(() => {
  loadConversations()
})
</script>

<style scoped>
.conversation-history-view {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
}

.history-list {
  min-height: 400px;
}

.conversation-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.conversation-card {
  background: var(--el-fill-color-blank);
  border: 1px solid var(--el-border-color);
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s;
}

.conversation-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.conversation-card-completed {
  border-left: 4px solid var(--el-color-success);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.scenario-info {
  display: flex;
  gap: 12px;
}

.scenario-info h3 {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
}

.level-badge {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  background: var(--el-fill-color-light);
  padding: 2px 8px;
  border-radius: 4px;
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stats-row {
  display: flex;
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.score-preview {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
}

.score-label {
  font-size: 14px;
  font-weight: 500;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.date {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

/* 详情抽屉 */
.detail-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 20px;
}

.detail-header h3 {
  margin: 0 0 8px 0;
  font-size: 20px;
}

.detail-meta {
  display: flex;
  gap: 8px;
  align-items: center;
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.detail-scores {
  padding: 20px;
  background: var(--el-fill-color-light);
  border-radius: 12px;
}

.detail-scores h4 {
  margin: 0 0 16px 0;
}

.overall-score {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.score-text {
  font-size: 28px;
  font-weight: bold;
}

.score-breakdown {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.score-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.score-item span {
  min-width: 60px;
  font-size: 14px;
}

.feedback-box {
  padding: 12px;
  background: var(--el-fill-color-blank);
  border-radius: 8px;
}

.feedback-box h5 {
  margin: 0 0 8px 0;
  font-size: 14px;
}

.feedback-box p {
  margin: 0;
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.detail-messages h4 {
  margin: 0 0 16px 0;
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.message-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  border-radius: 8px;
}

.message-user {
  align-items: flex-end;
  background: var(--el-color-primary-light-9);
}

.message-assistant {
  align-items: flex-start;
  background: var(--el-fill-color-light);
}

.message-header {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.message-content {
  font-size: 14px;
  line-height: 1.6;
}

.detail-actions {
  display: flex;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.detail-actions .el-button {
  flex: 1;
}

/* 列表动画 */
.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}

.list-enter-from {
  opacity: 0;
  transform: translateY(30px);
}

.list-leave-to {
  opacity: 0;
  transform: scale(0.9);
}

@media (max-width: 768px) {
  .conversation-grid {
    grid-template-columns: 1fr;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .header-actions {
    width: 100%;
    flex-direction: column;
  }

  .header-actions .el-input,
  .header-actions .el-select {
    width: 100% !important;
  }
}
</style>
