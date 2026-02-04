<template>
  <div class="conversation-view">
    <!-- 场景选择界面 -->
    <div v-if="currentStep === 'scenario'" class="scenario-selection">
      <el-page-header @back="goBack" title="返回">
        <template #content>
          <span class="page-title">选择对话场景</span>
        </template>
      </el-page-header>

      <div class="scenario-grid">
        <div
          v-for="scenario in scenarios"
          :key="scenario.value"
          :class="[
            'scenario-card',
            { 'scenario-card-selected': selectedScenario === scenario.value },
          ]"
          @click="selectScenario(scenario.value)"
        >
          <el-icon :size="48" :color="getScenarioColor(scenario.value)">
            <component :is="scenario.icon" />
          </el-icon>
          <h3>{{ scenario.label }}</h3>
          <p>{{ scenario.description }}</p>
          <div class="scenario-level">
            <el-tag size="small" type="info">{{ scenario.level }}</el-tag>
          </div>
        </div>
      </div>

      <div class="scenario-actions">
        <el-button
          type="primary"
          size="large"
          :disabled="!selectedScenario"
          @click="startConversation"
        >
          开始对话
          <el-icon class="el-icon--right"><Right /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 对话界面 -->
    <div
      v-else-if="currentStep === 'conversation'"
      class="conversation-interface"
    >
      <!-- 顶部栏 -->
      <div class="conversation-header">
        <el-button link @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <div class="header-info">
          <h2>{{ getScenarioName(selectedScenario) }}</h2>
          <el-tag size="small">{{ level || "A2" }}</el-tag>
        </div>
        <div class="header-actions">
          <el-button circle :icon="Setting" @click="showSettings = true" />
        </div>
      </div>

      <!-- 状态指示器 -->
      <div class="status-bar">
        <ConversationStatusComponent
          :status="conversationStatus"
          :message-count="messages.length"
          :target-messages="targetMessages"
        />
      </div>

      <!-- 消息列表 -->
      <div ref="messagesContainer" class="messages-container">
        <ConversationMessageComponent
          v-for="message in messages"
          :key="message.id"
          :message="message"
          :show-header="true"
          :is-highlighted="highlightedMessageId === message.id"
          :is-streaming="streamingMessage?.id === message.id"
        />

        <!-- AI 思考中占位符 -->
        <div v-if="isAIThinking" class="thinking-indicator">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>AI 正在思考...</span>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-area">
        <!-- 快捷回复 -->
        <div v-if="quickReplies.length > 0" class="quick-replies">
          <el-button
            v-for="(reply, index) in quickReplies"
            :key="index"
            size="small"
            @click="sendQuickReply(reply)"
          >
            {{ reply }}
          </el-button>
        </div>

        <!-- 输入框 -->
        <div class="input-box">
          <el-button
            :type="isVoiceInput ? 'primary' : 'default'"
            circle
            :icon="Microphone"
            :class="{ 'voice-active': isVoiceInput }"
            @click="toggleVoiceInput"
          />
          <div class="input-wrapper">
            <el-input
              ref="messageInput"
              v-model="userInput"
              type="textarea"
              :rows="2"
              :placeholder="inputPlaceholder"
              :disabled="isSending || isVoiceInput"
              @keydown.enter.prevent="handleEnterKey"
            />
            <!-- 语音识别状态指示器 -->
            <transition name="fade">
              <div v-if="isVoiceInput" class="voice-status-indicator">
                <div class="voice-wave">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <span class="voice-text">{{
                  interimTranscript || "正在听..."
                }}</span>
              </div>
            </transition>
          </div>
          <el-button
            type="primary"
            circle
            :icon="isSending ? Loading : Promotion"
            :loading="isSending"
            :disabled="!userInput.trim() || isVoiceInput"
            @click="sendMessage"
          />
        </div>

        <!-- 完成对话按钮 -->
        <div v-if="canComplete" class="complete-action">
          <el-button type="success" @click="handleComplete">
            <el-icon><CircleCheck /></el-icon>
            完成对话并查看评分
          </el-button>
        </div>
      </div>
    </div>

    <!-- 反馈抽屉 -->
    <ConversationFeedbackDrawer
      v-model:visible="showFeedbackDrawer"
      :scores="conversationScores"
      :key-words="keyWords"
      :is-complete="isComplete"
      @continue="handleContinue"
      @view-report="handleViewReport"
    />

    <!-- 设置对话框 -->
    <el-dialog v-model="showSettings" title="对话设置" width="500px">
      <el-form label-width="100px">
        <el-form-item label="难度级别">
          <el-select v-model="level" placeholder="选择难度">
            <el-option label="A1 - 入门" value="A1" />
            <el-option label="A2 - 初级" value="A2" />
            <el-option label="B1 - 中级" value="B1" />
            <el-option label="B2 - 中高级" value="B2" />
            <el-option label="C1 - 高级" value="C1" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标消息数">
          <el-input-number v-model="targetMessages" :min="5" :max="20" />
        </el-form-item>
        <el-form-item label="自动发音">
          <el-switch v-model="autoPronunciation" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSettings = false">取消</el-button>
        <el-button type="primary" @click="applySettings">应用设置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import {
  Right,
  ArrowLeft,
  Setting,
  Microphone,
  Promotion,
  CircleCheck,
  Loading,
  Coffee,
  Food,
  ShoppingBag,
  Location,
  Briefcase,
  Football,
  Picture,
  ChatDotRound
} from '@element-plus/icons-vue'
import ConversationMessageComponent from '@/components/ConversationMessage.vue'
import ConversationStatusComponent from '@/components/ConversationStatus.vue'
import ConversationFeedbackDrawer from '@/components/ConversationFeedbackDrawer.vue'
import {
  createConversation,
  sendMessage as sendApiMessage,
  completeConversation,
  streamMessage
} from '@/api/conversation'
import type {
  ConversationScenario,
  ConversationMessage,
  ConversationScores
} from '@/types/conversation'
import {
  MessageRole,
  MessageType
} from '@/types/conversation'
import {
  createVoiceRecognition,
  isVoiceRecognitionSupported,
  type VoiceRecognition,
  VoiceRecognitionStatus
} from '@/utils/voiceRecognition'
import {
  retryAsync,
  createConversationRecovery,
  createNetworkMonitor
} from '@/utils/errorRecovery'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()

// 步骤状态
const currentStep = ref<'scenario' | 'conversation' | 'result'>('scenario')

// 对话场景选项
const scenarios = [
  {
    value: 'cafe_order' as ConversationScenario,
    label: '咖啡店点餐',
    description: '学习如何在咖啡店点餐和询问推荐',
    icon: Coffee,
    level: 'A1-A2',
    color: '#8B4513'
  },
  {
    value: 'restaurant' as ConversationScenario,
    label: '餐厅用餐',
    description: '练习餐厅预订、点餐和结账对话',
    icon: Food,
    level: 'A2-B1',
    color: '#E74C3C'
  },
  {
    value: 'shopping' as ConversationScenario,
    label: '购物',
    description: '学习购物时的询问、比价和支付',
    icon: ShoppingBag,
    level: 'A2-B1',
    color: '#3498DB'
  },
  {
    value: 'asking_direction' as ConversationScenario,
    label: '问路',
    description: '练习询问和指示方向的表达',
    icon: Location,
    level: 'A1-A2',
    color: '#27AE60'
  },
  {
    value: 'job_interview' as ConversationScenario,
    label: '求职面试',
    description: '模拟面试场景，提升职场英语',
    icon: Briefcase,
    level: 'B1-C1',
    color: '#2C3E50'
  },
  {
    value: 'talking_about_hobbies' as ConversationScenario,
    label: '谈论爱好',
    description: '讨论兴趣爱好和休闲活动',
    icon: Football,
    level: 'A2-B1',
    color: '#E67E22'
  },
  {
    value: 'describing_picture' as ConversationScenario,
    label: '描述图片',
    description: '练习描述和讨论图片内容',
    icon: Picture,
    level: 'B1-B2',
    color: '#9B59B6'
  },
  {
    value: 'free_talk' as ConversationScenario,
    label: '自由对话',
    description: '自由话题，AI 陪你聊任何感兴趣的话题',
    icon: ChatDotRound,
    level: 'A2-C1',
    color: '#1ABC9C'
  }
]

// 对话状态
const selectedScenario = ref<ConversationScenario | null>(null)
const level = ref('A2')
const targetMessages = ref(10)
const autoPronunciation = ref(true)

const conversationId = ref<string>('')
const conversationStatus = ref<'in_progress' | 'completed' | 'abandoned' | 'connecting' | 'thinking' | 'listening'>('connecting')
const messages = ref<ConversationMessage[]>([])
const isAIThinking = ref(false)
const isSending = ref(false)
const isVoiceInput = ref(false)
const userInput = ref('')

// 流式响应
const streamingMessage = ref<ConversationMessage | null>(null)
const streamCleanup = ref<(() => void) | null>(null)

// 语音识别
const voiceRecognition = ref<VoiceRecognition | null>(null)
const voiceRecognitionStatus = ref<VoiceRecognitionStatus>(VoiceRecognitionStatus.Idle)
const interimTranscript = ref('')

// 错误恢复
const conversationRecovery = createConversationRecovery()
const networkMonitor = createNetworkMonitor()
const hasRecoverableState = ref(false)
const isRetrying = ref(false)

// 反馈相关
const showFeedbackDrawer = ref(false)
const conversationScores = ref<ConversationScores | undefined>()
const keyWords = ref<Array<{ word: string; score: number; phonetic?: string }>>([])
const isComplete = ref(false)

// UI 状态
const highlightedMessageId = ref<string>('')
const showSettings = ref(false)
const messagesContainer = ref<HTMLElement>()
const messageInput = ref()

// 快捷回复
const quickReplies = computed(() => {
  if (messages.value.length === 0) {
    return ['Hello!', 'Hi, how are you?', 'Excuse me...']
  }
  const lastMessage = messages.value[messages.value.length - 1]
  if (lastMessage && lastMessage.role === 'assistant') {
    return [
      'Yes, please.',
      'No, thank you.',
      'Could you repeat that?',
      "I don't understand."
    ]
  }
  return []
})

// 输入提示
const inputPlaceholder = computed(() => {
  if (isVoiceInput.value) {
    return '正在录音中...点击麦克风图标停止'
  }
  if (isSending.value) {
    return '发送中...'
  }
  return '输入你的回复... (按 Enter 发送)'
})

// 是否可以完成对话
const canComplete = computed(() => {
  return messages.value.length >= 6 && conversationStatus.value !== 'thinking'
})

// 获取场景名称
const getScenarioName = (scenario: ConversationScenario | null) => {
  if (!scenario) return ''
  const found = scenarios.find(s => s.value === scenario)
  return found?.label || ''
}

// 获取场景颜色
const getScenarioColor = (scenario: ConversationScenario) => {
  const found = scenarios.find(s => s.value === scenario)
  return found?.color || '#409EFF'
}

// 选择场景
const selectScenario = (scenario: ConversationScenario) => {
  selectedScenario.value = scenario
}

// 开始对话
const startConversation = async () => {
  if (!selectedScenario.value) return

  try {
    currentStep.value = 'conversation'
    conversationStatus.value = 'connecting'

    const conversation = await createConversation({
      scenario: selectedScenario.value,
      level: level.value
    })

    conversationId.value = conversation.id
    conversationStatus.value = 'in_progress'

    // 添加欢迎消息
    if (conversation.messages.length > 0) {
      messages.value = conversation.messages
      await scrollToBottom()
    }

    // 启动自动保存
    conversationRecovery.startAutoSave(conversationId.value, () => ({
      messages: messages.value,
      userInput: userInput.value,
      timestamp: Date.now()
    }))

    // 检查是否有可恢复的状态
    recoverConversationState()
  } catch (error) {
    console.error('Failed to create conversation:', error)
    ElMessage.error('创建对话失败，请重试')
    currentStep.value = 'scenario'
  }
}

// 发送消息
const sendMessage = async () => {
  const content = userInput.value.trim()
  if (!content || !conversationId.value || isSending.value) return

  try {
    isSending.value = true

    // 添加用户消息
    const userMessage: ConversationMessage = {
      id: `msg-${Date.now()}`,
      role: MessageRole.USER,
      type: MessageType.TEXT,
      content,
      timestamp: new Date().toISOString()
    }
    messages.value.push(userMessage)
    userInput.value = ''

    await scrollToBottom()

    // 设置 AI 思考状态
    isAIThinking.value = true
    conversationStatus.value = 'thinking'

    // 创建流式消息占位符
    const aiMessageId = `msg-${Date.now() + 1}`
    streamingMessage.value = {
      id: aiMessageId,
      role: MessageRole.ASSISTANT,
      type: MessageType.TEXT,
      content: '',
      timestamp: new Date().toISOString()
    }
    messages.value.push(streamingMessage.value)

    await scrollToBottom()

    // 使用流式响应
    streamCleanup.value = streamMessage(conversationId.value, content, {
      onStart: () => {
        console.log('Stream started')
      },
      onToken: (token: string) => {
        if (streamingMessage.value) {
          streamingMessage.value.content += token
          // 自动滚动到底部
          scrollToBottom()
        }
      },
      onComplete: (fullMessage: string) => {
        if (streamingMessage.value) {
          streamingMessage.value.content = fullMessage
        }
        isAIThinking.value = false
        conversationStatus.value = 'in_progress'
        streamingMessage.value = null

        // 高亮最新消息
        highlightedMessageId.value = aiMessageId
        setTimeout(() => {
          highlightedMessageId.value = ''
        }, 2000)
      },
      onError: (error: Error) => {
        console.error('Stream error:', error)
        // 移除流式消息占位符
        if (streamingMessage.value) {
          const index = messages.value.findIndex(m => m.id === aiMessageId)
          if (index !== -1) {
            messages.value.splice(index, 1)
          }
        }
        isAIThinking.value = false
        conversationStatus.value = 'in_progress'
        streamingMessage.value = null

        // 尝试重试
        handleSendError(error, content)
        ElMessage.error('消息发送失败，请重试')
      },
      onEnd: () => {
        streamCleanup.value = null
      }
    })
  } catch (error) {
    console.error('Failed to send message:', error)
    isAIThinking.value = false
    conversationStatus.value = 'in_progress'
    streamingMessage.value = null
  } finally {
    isSending.value = false
  }
}

// 发送快捷回复
const sendQuickReply = (reply: string) => {
  userInput.value = reply
  sendMessage()
}

// 处理发送错误
const handleSendError = (error: Error, originalContent: string) => {
  // 检查是否可重试
  const isRetryable = error.message.includes('network') ||
                      error.message.includes('timeout') ||
                      error.message.includes('5')

  if (isRetryable && !isRetrying.value) {
    ElMessageBox.confirm(
      '消息发送失败，是否重试？',
      '网络错误',
      {
        confirmButtonText: '重试',
        cancelButtonText: '取消',
        type: 'warning'
      }
    ).then(() => {
      isRetrying.value = true
      userInput.value = originalContent
      sendMessage().finally(() => {
        isRetrying.value = false
      })
    }).catch(() => {
      // 用户取消重试
      ElMessage.info('已取消发送')
    })
  } else {
    ElMessage.error(`消息发送失败: ${error.message}`)
  }
}

// 保存当前对话状态
const saveCurrentState = () => {
  if (conversationId.value) {
    conversationRecovery.saveConversationState(conversationId.value, {
      messages: messages.value,
      userInput: userInput.value,
      timestamp: Date.now()
    })
  }
}

// 恢复对话状态
const recoverConversationState = () => {
  if (conversationId.value) {
    const state = conversationRecovery.loadConversationState(conversationId.value)
    if (state && state.messages.length > 0) {
      ElMessageBox.confirm(
        '检测到未完成的对话，是否恢复？',
        '恢复对话',
        {
          confirmButtonText: '恢复',
          cancelButtonText: '开始新对话',
          type: 'info'
        }
      ).then(() => {
        messages.value = state.messages
        userInput.value = state.userInput || ''
        hasRecoverableState.value = false
        scrollToBottom()
      }).catch(() => {
        // 清除保存的状态
        conversationRecovery.clearConversationState(conversationId.value)
      })
    }
  }
}

// 处理 Enter 键
const handleEnterKey = (event: KeyboardEvent) => {
  if (event.shiftKey) {
    // Shift + Enter 换行
    return
  }
  // Enter 发送
  sendMessage()
}

// 切换语音输入
const toggleVoiceInput = () => {
  if (!isVoiceRecognitionSupported()) {
    ElMessage.warning('您的浏览器不支持语音识别功能，请使用 Chrome 或 Edge 浏览器')
    return
  }

  isVoiceInput.value = !isVoiceInput.value
  if (isVoiceInput.value) {
    startVoiceRecognition()
  } else {
    stopVoiceRecognition()
  }
}

// 开始语音识别
const startVoiceRecognition = () => {
  if (!voiceRecognition.value) {
    voiceRecognition.value = createVoiceRecognition({
      language: 'en-US',
      continuous: false,
      interimResults: true
    })

    // 注册回调
    voiceRecognition.value.on({
      onStart: () => {
        conversationStatus.value = 'listening'
        interimTranscript.value = ''
      },
      onStop: () => {
        conversationStatus.value = 'in_progress'
        if (userInput.value.trim()) {
          // 自动发送
          sendMessage()
        }
      },
      onResult: (result) => {
        userInput.value = result.transcript
        interimTranscript.value = ''
        // 自动停止并发送
        stopVoiceRecognition()
      },
      onInterimResult: (result) => {
        interimTranscript.value = result.transcript
        userInput.value = result.transcript
      },
      onError: (error) => {
        console.error('Voice recognition error:', error)
        ElMessage.error(error.message)
        isVoiceInput.value = false
        conversationStatus.value = 'in_progress'
      },
      onStatusChange: (status) => {
        voiceRecognitionStatus.value = status
      }
    })
  }

  voiceRecognition.value.start()
}

// 停止语音识别
const stopVoiceRecognition = () => {
  if (voiceRecognition.value?.isListening()) {
    voiceRecognition.value.stop()
  }
  isVoiceInput.value = false
  interimTranscript.value = ''
}

// 滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 完成对话
const handleComplete = async () => {
  if (!conversationId.value) return

  try {
    conversationStatus.value = 'thinking'
    isSending.value = true

    const result = await completeConversation(conversationId.value)

    conversationScores.value = result.scores
    isComplete.value = true

    // 提取关键词（从评分中获取）
    if (result.scores?.vocabulary.feedback) {
      // TODO: 从反馈中提取关键词
      keyWords.value = [
        { word: 'excellent', score: 95, phonetic: '/ˈeksələnt/' },
        { word: 'pronunciation', score: 88, phonetic: '/prəˌnʌnsiˈeɪʃn/' },
        { word: 'vocabulary', score: 92, phonetic: '/vəˈkæbjələri/' }
      ]
    }

    showFeedbackDrawer.value = true
  } catch (error) {
    console.error('Failed to complete conversation:', error)
  } finally {
    isSending.value = false
  }
}

// 继续练习
const handleContinue = () => {
  // 重置状态
  currentStep.value = 'scenario'
  selectedScenario.value = null
  conversationId.value = ''
  messages.value = []
  conversationScores.value = undefined
  keyWords.value = []
  isComplete.value = false
}

// 查看详细报告
const handleViewReport = () => {
  showFeedbackDrawer.value = false
  // TODO: 跳转到详细报告页面
  router.push('/student/progress')
}

// 应用设置
const applySettings = () => {
  showSettings.value = false
  // 如果正在对话中，更新设置
  if (conversationId.value) {
    // TODO: 调用 API 更新对话设置
  }
}

// 返回
const goBack = () => {
  if (currentStep.value === 'conversation') {
    // 确认是否放弃当前对话
    // TODO: 显示确认对话框
  }
  router.back()
}

// 组件挂载
onMounted(() => {
  // 检查浏览器是否支持语音识别
  if (!isVoiceRecognitionSupported()) {
    console.warn('Voice recognition is not supported in this browser')
  }

  // 监听网络状态变化
  networkMonitor.onStatusChange((online) => {
    if (online) {
      ElMessage.success('网络已连接')
      // 网络恢复后可以尝试重试失败的请求
    } else {
      ElMessage.warning('网络连接已断开')
    }
  })
})

// 组件卸载
onUnmounted(() => {
  // 清理语音识别器
  if (voiceRecognition.value) {
    voiceRecognition.value.destroy()
    voiceRecognition.value = null
  }
  // 清理流式连接
  if (streamCleanup.value) {
    streamCleanup.value()
    streamCleanup.value = null
  }
  // 停止自动保存
  conversationRecovery.stopAutoSave();
})
</script>

<style scoped>
.conversation-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color-page);
}

/* 场景选择界面 */
.scenario-selection {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
}

.scenario-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
  margin-top: 24px;
}

.scenario-card {
  padding: 24px;
  background: var(--el-fill-color-blank);
  border: 2px solid var(--el-border-color);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.scenario-card:hover {
  border-color: var(--el-color-primary);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
  transform: translateY(-2px);
}

.scenario-card-selected {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}

.scenario-card h3 {
  margin: 16px 0 8px;
  font-size: 18px;
  font-weight: 600;
}

.scenario-card p {
  margin: 0;
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.scenario-level {
  margin-top: 12px;
}

.scenario-actions {
  margin-top: 32px;
  text-align: center;
}

/* 对话界面 */
.conversation-interface {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.conversation-header {
  display: flex;
  align-items: center;
  padding: 16px 24px;
  background: var(--el-fill-color-blank);
  border-bottom: 1px solid var(--el-border-color);
  gap: 16px;
}

.header-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-info h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.status-bar {
  padding: 12px 24px;
  background: var(--el-fill-color-blank);
  border-bottom: 1px solid var(--el-border-color);
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.thinking-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
  color: var(--el-text-color-secondary);
  align-self: flex-start;
}

.input-area {
  background: var(--el-fill-color-blank);
  border-top: 1px solid var(--el-border-color);
  padding: 16px 24px;
}

.quick-replies {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.input-box {
  display: flex;
  align-items: flex-end;
  gap: 12px;
}

.input-box .el-input {
  flex: 1;
}

.input-box .el-textarea :deep(textarea) {
  resize: none;
}

.input-wrapper {
  flex: 1;
  position: relative;
}

.voice-active {
  animation: voice-pulse 1.5s ease-in-out infinite;
}

@keyframes voice-pulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(64, 158, 255, 0.4);
  }
  50% {
    box-shadow: 0 0 0 10px rgba(64, 158, 255, 0);
  }
}

.voice-status-indicator {
  position: absolute;
  bottom: 8px;
  left: 12px;
  right: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--el-color-primary-light-9);
  border-radius: 6px;
  pointer-events: none;
}

.voice-wave {
  display: flex;
  align-items: center;
  gap: 3px;
}

.voice-wave span {
  display: block;
  width: 3px;
  height: 12px;
  background: var(--el-color-primary);
  border-radius: 2px;
  animation: wave 1s ease-in-out infinite;
}

.voice-wave span:nth-child(2) {
  animation-delay: 0.1s;
}

.voice-wave span:nth-child(3) {
  animation-delay: 0.2s;
}

@keyframes wave {
  0%,
  100% {
    height: 12px;
  }
  50% {
    height: 20px;
  }
}

.voice-text {
  font-size: 13px;
  color: var(--el-color-primary);
  font-weight: 500;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 打字机光标效果 */
.typing-cursor {
  display: inline-block;
  width: 2px;
  height: 1em;
  background: var(--el-color-primary);
  margin-left: 2px;
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0;
  }
}

/* 流式消息淡入效果 */
.streaming-message {
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.complete-action {
  margin-top: 12px;
  text-align: center;
}

@media (max-width: 768px) {
  .scenario-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 12px;
  }

  .scenario-card {
    padding: 16px;
  }

  .messages-container {
    padding: 16px;
  }

  .input-area {
    padding: 12px 16px;
  }
}
</style>
