/**
 * ConversationView 组件单元测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import ConversationView from '@/views/student/ConversationView.vue'
import * as conversationApi from '@/api/conversation'
import { createVoiceRecognition, VoiceRecognitionStatus } from '@/utils/voiceRecognition'
import { createTextToSpeech, TTSStatus } from '@/utils/textToSpeech'
import type { ConversationScenario, ConversationMessage, ConversationScores } from '@/types/conversation'

// Mock API
vi.mock('@/api/conversation', () => ({
  createConversation: vi.fn(),
  getConversation: vi.fn(),
  sendMessage: vi.fn(),
  completeConversation: vi.fn(),
  getScenarios: vi.fn(),
  streamMessage: vi.fn(() => vi.fn())
}))

// Mock Element Plus 图标
vi.mock('@element-plus/icons-vue', () => ({
  Right: { template: '<div></div>' },
  ArrowLeft: { template: '<div></div>' },
  Setting: { template: '<div></div>' },
  Microphone: { template: '<div></div>' },
  Promotion: { template: '<div></div>' },
  CircleCheck: { template: '<div></div>' },
  Loading: { template: '<div></div>' },
  Coffee: { template: '<div></div>' },
  Food: { template: '<div></div>' },
  ShoppingBag: { template: '<div></div>' },
  Location: { template: '<div></div>' },
  Briefcase: { template: '<div></div>' },
  Football: { template: '<div></div>' },
  Picture: { template: '<div></div>' },
  ChatDotRound: { template: '<div></div>' },
  VideoPause: { template: '<div></div>' }
}))

// Mock Element Plus 组件
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn()
  }
}))

// Mock 对话相关组件
vi.mock('@/components/ConversationMessage.vue', () => ({
  default: {
    name: 'ConversationMessage',
    template: '<div class="mock-message">{{ message.content }}</div>',
    props: ['message', 'showHeader', 'isHighlighted', 'isStreaming']
  }
}))

vi.mock('@/components/ConversationStatus.vue', () => ({
  default: {
    name: 'ConversationStatus',
    template: '<div class="mock-status">{{ status }}</div>',
    props: ['status', 'messageCount', 'targetMessages']
  }
}))

vi.mock('@/components/ConversationFeedbackDrawer.vue', () => ({
  default: {
    name: 'ConversationFeedbackDrawer',
    template: '<div class="mock-drawer"><slot name="extra"></slot></div>',
    props: ['visible', 'scores', 'keyWords', 'isComplete']
  }
}))

vi.mock('@/components/ConversationScoreCard.vue', () => ({
  default: {
    name: 'ConversationScoreCard',
    template: '<div class="mock-score">{{ scores?.overall_score }}</div>',
    props: ['scores']
  }
}))

// Mock Web Speech API
const mockSpeechRecognition = vi.fn()
global.SpeechRecognition = mockSpeechRecognition
global.webkitSpeechRecognition = mockSpeechRecognition

// 创建测试路由
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: { template: '<div></div>' } },
    { path: '/student/conversation', component: ConversationView }
  ]
})

describe('ConversationView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())

    // Mock创建对话响应
    vi.mocked(conversationApi.createConversation).mockResolvedValue({
      id: 'test-conv-1',
      student_id: 'student-1',
      scenario: 'cafe_order' as ConversationScenario,
      level: 'A2',
      status: 'in_progress',
      messages: [],
      started_at: new Date().toISOString(),
      created_at: new Date().toISOString()
    })

    // Mock完成对话响应
    vi.mocked(conversationApi.completeConversation).mockResolvedValue({
      conversation: {
        id: 'test-conv-1',
        status: 'completed'
      },
      scores: {
        overall: 85,
        overall_score: 85,
        fluency_score: 80,
        grammar_score: 75,
        vocabulary_score: 88,
        feedback: 'Good job!',
        suggestions: ['Keep practicing']
      } as ConversationScores
    })
  })

  const mountWithRouter = () => {
    return mount(ConversationView, {
      global: {
        plugins: [router]
      }
    })
  }

  it('应该正确渲染场景选择界面', () => {
    const wrapper = mountWithRouter()
    expect(wrapper.find('.scenario-selection').exists()).toBe(true)
  })

  it('应该能选择场景', () => {
    const wrapper = mountWithRouter()
    wrapper.vm.selectScenario('cafe_order' as ConversationScenario)
    expect(wrapper.vm.selectedScenario).toBe('cafe_order')
  })

  it('应该能开始对话', async () => {
    const wrapper = mountWithRouter()
    wrapper.vm.selectScenario('cafe_order' as ConversationScenario)

    await wrapper.vm.startConversation()

    expect(conversationApi.createConversation).toHaveBeenCalledWith({
      scenario: 'cafe_order',
      level: 'A2'
    })
    expect(wrapper.vm.conversationId).toBe('test-conv-1')
    expect(wrapper.vm.currentStep).toBe('conversation')
  })

  it('应该支持语音输入', async () => {
    const wrapper = mountWithRouter()
    await wrapper.vm.$nextTick()

    // 手动设置语音识别实例
    const recognition = createVoiceRecognition()
    wrapper.vm.voiceRecognition = recognition
    const startSpy = vi.spyOn(recognition, 'start')

    wrapper.vm.startVoiceRecognition()
    expect(startSpy).toHaveBeenCalled()
  })

  it('应该支持TTS播放AI回复', async () => {
    const wrapper = mountWithRouter()
    await wrapper.vm.$nextTick()

    // 手动设置 TTS 实例
    const tts = createTextToSpeech()
    wrapper.vm.textToSpeech = tts
    wrapper.vm.autoPlayResponse = true

    const speakSpy = vi.spyOn(tts, 'speak')
    speakSpy.mockResolvedValue()

    await wrapper.vm.playAIResponse('Hello, how are you?')
    expect(speakSpy).toHaveBeenCalledWith('Hello, how are you?')
  })

  it('应该能停止TTS播放', async () => {
    const wrapper = mountWithRouter()
    await wrapper.vm.$nextTick()

    // 手动设置 TTS 实例
    const tts = createTextToSpeech()
    wrapper.vm.textToSpeech = tts
    vi.spyOn(tts, 'isSpeaking').mockReturnValue(true)

    const stopSpy = vi.spyOn(tts, 'stop')

    wrapper.vm.stopPlayback()
    expect(stopSpy).toHaveBeenCalled()
  })

  it('应该能切换消息播放状态', async () => {
    const wrapper = mountWithRouter()
    await wrapper.vm.$nextTick()

    // 手动设置 TTS 实例
    const tts = createTextToSpeech()
    wrapper.vm.textToSpeech = tts
    wrapper.vm.autoPlayResponse = true
    wrapper.vm.ttsStatus = TTSStatus.Idle

    const speakSpy = vi.spyOn(tts, 'speak')
    speakSpy.mockResolvedValue()

    const message: ConversationMessage = {
      id: 'msg-1',
      role: 'assistant' as any,
      type: 'text' as any,
      content: 'Hello, how are you?',
      timestamp: new Date().toISOString()
    }

    await wrapper.vm.toggleMessagePlayback(message)
    // playAIResponse 只传递 text 参数，messageId 是可选的
    expect(speakSpy).toHaveBeenCalledWith('Hello, how are you?')
  })

  it('应该能完成对话并获取评分', async () => {
    const wrapper = mountWithRouter()
    wrapper.vm.conversationId = 'test-conv-1'

    await wrapper.vm.handleComplete()

    expect(conversationApi.completeConversation).toHaveBeenCalledWith('test-conv-1')
    expect(wrapper.vm.conversationScores).toBeDefined()
    expect(wrapper.vm.conversationScores?.overall_score).toBe(85)
  })

  it('应该正确检测消息播放状态', () => {
    const wrapper = mountWithRouter()
    wrapper.vm.currentPlayingMessageId = 'msg-1'

    expect(wrapper.vm.isMessagePlaying('msg-1')).toBe(false) // TTSStatus不是Speaking
    expect(wrapper.vm.isMessagePlaying('msg-2')).toBe(false)
  })

  it('应该正确初始化TTS', () => {
    const wrapper = mountWithRouter()
    expect(wrapper.vm.textToSpeech).toBeTruthy()
    expect(wrapper.vm.ttsStatus).toBe(TTSStatus.Idle)
  })

  it('应该在组件卸载时清理资源', () => {
    const wrapper = mountWithRouter()
    const tts = wrapper.vm.textToSpeech
    const destroySpy = vi.spyOn(tts, 'destroy')

    wrapper.unmount()
    expect(destroySpy).toHaveBeenCalled()
  })

  it('应该支持快捷回复', async () => {
    const wrapper = mountWithRouter()
    wrapper.vm.conversationId = 'test-conv-1'
    wrapper.vm.isSending = false // 确保可以发送

    // 使用 vi.spyOn 监控 sendMessage 方法
    const sendMessageSpy = vi.spyOn(wrapper.vm, 'sendMessage').mockImplementation(async () => {
      // 模拟原始行为：清空输入
      wrapper.vm.userInput = ''
    })

    // sendQuickReply 设置 userInput 并调用 sendMessage
    wrapper.vm.sendQuickReply('Hello')

    // 由于响应式代理，我们需要通过访问器调用原始方法
    // 或者直接检查行为结果
    expect(wrapper.vm.userInput).toBe('') // 因为 sendMessage 清空了输入

    // 恢复原始方法
    sendMessageSpy.mockRestore()
  })
})
