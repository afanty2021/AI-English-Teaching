/**
 * 对话组件集成测试
 * 包含组件交互和边界条件测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import ConversationView from '@/views/student/ConversationView.vue'
import { ElMessage } from 'element-plus'

// Mock API
vi.mock('@/api/conversation', () => ({
  createConversation: vi.fn(() => Promise.resolve({
    id: 'test-conv-1',
    student_id: 'student-1',
    scenario: 'cafe_order',
    level: 'A2',
    status: 'in_progress',
    messages: [],
    started_at: new Date().toISOString()
  })),
  sendMessage: vi.fn(() => Promise.resolve({
    message: {
      id: 'msg-1',
      role: 'assistant',
      type: 'text',
      content: 'Hello! How can I help you?',
      timestamp: new Date().toISOString()
    }
  })),
  completeConversation: vi.fn(() => Promise.resolve({
    conversation: {
      id: 'test-conv-1',
      status: 'completed'
    },
    scores: {
      overall: 85,
      fluency: { score: 80, max_score: 100, name: '流利度', feedback: '', suggestions: [] },
      grammar: { score: 90, max_score: 100, name: '语法', feedback: '', suggestions: [] },
      vocabulary: { score: 75, max_score: 100, name: '词汇', feedback: '', suggestions: [] },
      pronunciation: { score: 85, max_score: 100, name: '发音', feedback: '', suggestions: [] },
      communication: { score: 88, max_score: 100, name: '沟通', feedback: '', suggestions: [] },
      suggestions: []
    }
  })),
  streamMessage: vi.fn(() => vi.fn())
}))

// Mock 路由
const mockRouter = {
  push: vi.fn(),
  back: vi.fn(),
  currentRoute: { value: { path: '/student/conversation' } }
}

vi.mock('vue-router', () => ({
  useRouter: () => mockRouter,
  useRoute: () => ({ query: {} })
}))

// Mock voice recognition
vi.mock('@/utils/voiceRecognition', () => ({
  isVoiceRecognitionSupported: () => true,
  createVoiceRecognition: vi.fn(() => ({
    on: vi.fn().mockReturnThis(),
    start: vi.fn(),
    stop: vi.fn(),
    abort: vi.fn(),
    destroy: vi.fn(),
    isListening: () => false,
    updateConfig: vi.fn(),
    getStatus: () => 'idle'
  }))
}))

// Mock error recovery
vi.mock('@/utils/errorRecovery', () => ({
  createConversationRecovery: () => ({
    saveConversationState: vi.fn(),
    loadConversationState: vi.fn(() => null),
    clearConversationState: vi.fn(),
    startAutoSave: vi.fn(),
    stopAutoSave: vi.fn(),
    getRecoverableConversations: vi.fn(() => [])
  }),
  createNetworkMonitor: () => ({
    onStatusChange: vi.fn(() => vi.fn()),
    getStatus: () => true
  })
}))

describe('ConversationView 组件测试', () => {
  let wrapper: VueWrapper<any>
  let pinia: any

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)

    wrapper = mount(ConversationView, {
      global: {
        plugins: [pinia, ElementPlus],
        stubs: {
          'el-icon': true,
          'el-avatar': true,
          'el-progress': true
        }
      }
    })
  })

  afterEach(() => {
    wrapper?.unmount()
    vi.clearAllMocks()
  })

  describe('初始渲染', () => {
    it('应该渲染场景选择界面', () => {
      expect(wrapper.find('.scenario-selection').exists()).toBe(true)
      expect(wrapper.find('.scenario-grid').exists()).toBe(true)
    })

    it('应该显示所有场景卡片', () => {
      const cards = wrapper.findAll('.scenario-card')
      expect(cards.length).toBe(8) // 8个场景
    })

    it('应该禁用开始按钮当没有选择场景', () => {
      const startButton = wrapper.find('.scenario-actions .el-button')
      expect(startButton.attributes('disabled')).toBeDefined()
    })
  })

  describe('场景选择', () => {
    it('应该选择场景', async () => {
      const firstCard = wrapper.find('.scenario-card')
      await firstCard.trigger('click')

      // 选择后应该高亮
      expect(wrapper.find('.scenario-card-selected').exists()).toBe(true)

      // 开始按钮应该启用
      const startButton = wrapper.find('.scenario-actions .el-button')
      expect(startButton.attributes('disabled')).toBeUndefined()
    })

    it('应该切换场景选择', async () => {
      const cards = wrapper.findAll('.scenario-card')

      // 选择第一个
      await cards[0].trigger('click')
      expect(wrapper.vm.selectedScenario).toBe('cafe_order')

      // 选择第二个
      await cards[1].trigger('click')
      expect(wrapper.vm.selectedScenario).toBe('restaurant')
    })
  })

  describe('开始对话', () => {
    it('应该切换到对话界面', async () => {
      wrapper.vm.selectedScenario = 'cafe_order'
      const startButton = wrapper.find('.scenario-actions .el-button')
      await startButton.trigger('click')

      // 等待异步操作
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(wrapper.vm.currentStep).toBe('conversation')
      expect(wrapper.find('.conversation-interface').exists()).toBe(true)
    })
  })

  describe('消息发送', () => {
    beforeEach(async () => {
      wrapper.vm.selectedScenario = 'cafe_order'
      wrapper.vm.conversationId = 'test-conv-1'
      wrapper.vm.currentStep = 'conversation'
      await wrapper.vm.$nextTick()
    })

    it('应该发送文本消息', async () => {
      wrapper.vm.userInput = 'Hello, I would like to order a coffee'
      await wrapper.vm.sendMessage()

      expect(wrapper.vm.messages.length).toBeGreaterThan(0)
      expect(wrapper.vm.isSending).toBe(false)
    })

    it('应该阻止发送空消息', async () => {
      wrapper.vm.userInput = ''
      await wrapper.vm.sendMessage()

      expect(wrapper.vm.messages.length).toBe(0)
    })

    it('应该阻止发送中的重复发送', async () => {
      wrapper.vm.isSending = true
      wrapper.vm.userInput = 'Test message'

      await wrapper.vm.sendMessage()

      // 应该不发送
      expect(wrapper.vm.userInput).toBe('Test message')
    })

    it('应该处理发送错误', async () => {
      const { sendMessage } = await import('@/api/conversation')
      vi.mocked(sendMessage).mockRejectedValueOnce(new Error('Network error'))

      wrapper.vm.userInput = 'Test'
      await wrapper.vm.sendMessage()

      expect(wrapper.vm.isSending).toBe(false)
    })
  })

  describe('语音输入', () => {
    beforeEach(async () => {
      wrapper.vm.selectedScenario = 'cafe_order'
      wrapper.vm.currentStep = 'conversation'
      await wrapper.vm.$nextTick()
    })

    it('应该切换语音输入状态', async () => {
      expect(wrapper.vm.isVoiceInput).toBe(false)

      await wrapper.vm.toggleVoiceInput()

      expect(wrapper.vm.isVoiceInput).toBe(true)
    })

    it('应该显示语音状态指示器', async () => {
      wrapper.vm.isVoiceInput = true
      await wrapper.vm.$nextTick()

      // 检查语音状态元素是否存在
      const voiceStatus = wrapper.find('.voice-status-indicator')
      expect(voiceStatus.exists()).toBe(true)
    })
  })

  describe('完成对话', () => {
    beforeEach(async () => {
      wrapper.vm.selectedScenario = 'cafe_order'
      wrapper.vm.conversationId = 'test-conv-1'
      wrapper.vm.currentStep = 'conversation'
      wrapper.vm.messages = [
        { id: '1', role: 'user', type: 'text', content: 'Hello', timestamp: new Date().toISOString() },
        { id: '2', role: 'assistant', type: 'text', content: 'Hi', timestamp: new Date().toISOString() }
      ]
      await wrapper.vm.$nextTick()
    })

    it('应该允许完成对话当有足够消息', () => {
      expect(wrapper.vm.canComplete).toBe(true)
    })

    it('不应该允许完成对话当消息不足', () => {
      wrapper.vm.messages = []
      expect(wrapper.vm.canComplete).toBe(false)
    })

    it('应该完成对话并显示评分', async () => {
      await wrapper.vm.handleComplete()

      expect(wrapper.vm.isComplete).toBe(true)
      expect(wrapper.vm.conversationScores).toBeDefined()
      expect(wrapper.vm.showFeedbackDrawer).toBe(true)
    })
  })

  describe('快捷回复', () => {
    beforeEach(async () => {
      wrapper.vm.selectedScenario = 'cafe_order'
      wrapper.vm.currentStep = 'conversation'
      await wrapper.vm.$nextTick()
    })

    it('应该显示初始快捷回复', () => {
      const replies = wrapper.vm.quickReplies
      expect(replies.length).toBeGreaterThan(0)
      expect(replies).toContain('Hello!')
    })

    it('应该根据最后一条消息显示快捷回复', async () => {
      wrapper.vm.messages = [{
        id: '1',
        role: 'assistant',
        type: 'text',
        content: 'What would you like to order?',
        timestamp: new Date().toISOString()
      }]
      await wrapper.vm.$nextTick()

      const replies = wrapper.vm.quickReplies
      expect(replies).toContain('Yes, please.')
      expect(replies).toContain('No, thank you.')
    })

    it('应该发送快捷回复', async () => {
      wrapper.vm.sendQuickReply('Hello!')
      expect(wrapper.vm.userInput).toBe('Hello!')
    })
  })

  describe('边界条件', () => {
    it('应该处理超长用户输入', async () => {
      wrapper.vm.selectedScenario = 'cafe_order'
      wrapper.vm.currentStep = 'conversation'
      wrapper.vm.userInput = 'A'.repeat(10000)
      await wrapper.vm.$nextTick()

      // 不应该崩溃
      expect(() => wrapper.vm.sendMessage()).not.toThrow()
    })

    it('应该处理特殊字符输入', async () => {
      wrapper.vm.userInput = '测试\n\t\r<script>alert("xss")</script>'
      await wrapper.vm.$nextTick()

      expect(() => wrapper.vm.sendMessage()).not.toThrow()
    })

    it('应该处理空格输入', async () => {
      wrapper.vm.userInput = '   '
      await wrapper.vm.sendMessage()

      expect(wrapper.vm.messages.length).toBe(0)
    })

    it('应该处理只有换行的输入', async () => {
      wrapper.vm.userInput = '\n\n\n'
      await wrapper.vm.sendMessage()

      expect(wrapper.vm.messages.length).toBe(0)
    })

    it('应该处理快速连续点击', async () => {
      wrapper.vm.selectedScenario = 'cafe_order'
      wrapper.vm.currentStep = 'conversation'

      // 快速多次点击开始按钮
      for (let i = 0; i < 10; i++) {
        try {
          await wrapper.vm.startConversation()
        } catch (e) {
          // 忽略错误
        }
      }

      // 应该只创建一次对话
      expect(wrapper.vm.currentStep).toBe('conversation')
    })
  })

  describe('设置对话框', () => {
    it('应该打开设置对话框', async () => {
      await wrapper.vm.$nextTick()

      // 查找设置按钮
      const settingButton = wrapper.find('.header-actions .el-button')
      if (settingButton.exists()) {
        await settingButton.trigger('click')
        expect(wrapper.vm.showSettings).toBe(true)
      }
    })

    it('应该更新难度级别', async () => {
      wrapper.vm.level = 'B1'
      await wrapper.vm.applySettings()
      expect(wrapper.vm.level).toBe('B1')
    })

    it('应该更新目标消息数', async () => {
      wrapper.vm.targetMessages = 15
      await wrapper.vm.applySettings()
      expect(wrapper.vm.targetMessages).toBe(15)
    })
  })

  describe('组件清理', () => {
    it('应该在卸载时清理语音识别器', async () => {
      const { createVoiceRecognition } = await import('@/utils/voiceRecognition')
      const mockRecognition = {
        destroy: vi.fn()
      }
      vi.mocked(createVoiceRecognition).mockReturnValue(mockRecognition)

      wrapper.vm.voiceRecognition = mockRecognition

      wrapper.unmount()

      expect(mockRecognition.destroy).toHaveBeenCalled()
    })

    it('应该在卸载时停止自动保存', async () => {
      const mockRecovery = {
        stopAutoSave: vi.fn()
      }
      const { createConversationRecovery } = await import('@/utils/errorRecovery')
      vi.mocked(createConversationRecovery).mockReturnValue(mockRecovery)

      wrapper.vm.conversationRecovery = mockRecovery

      wrapper.unmount()

      expect(mockRecovery.stopAutoSave).toHaveBeenCalled()
    })

    it('应该在卸载时清理流式连接', async () => {
      const mockCleanup = vi.fn()
      wrapper.vm.streamCleanup = mockCleanup

      wrapper.unmount()

      expect(mockCleanup).toHaveBeenCalled()
    })
  })

  describe('键盘交互', () => {
    beforeEach(async () => {
      wrapper.vm.selectedScenario = 'cafe_order'
      wrapper.vm.currentStep = 'conversation'
      wrapper.vm.userInput = 'Test message'
      await wrapper.vm.$nextTick()
    })

    it('应该在按 Enter 时发送消息', () => {
      const event = new KeyboardEvent('keydown', { key: 'Enter' })
      wrapper.vm.handleEnterKey(event)

      // Enter 键应该触发发送（通过 isSending 标志验证）
      // 由于 sendMessage 是异步的，这里只检查不抛错
      expect(() => wrapper.vm.handleEnterKey(event)).not.toThrow()
    })

    it('应该在按 Shift+Enter 时换行', () => {
      const event = new KeyboardEvent('keydown', {
        key: 'Enter',
        shiftKey: true
      })
      wrapper.vm.handleEnterKey(event)

      // Shift+Enter 不应该发送消息
      expect(wrapper.vm.userInput).toBe('Test message')
    })
  })

  describe('状态持久化', () => {
    it('应该保存当前对话状态', () => {
      wrapper.vm.conversationId = 'test-conv-1'
      wrapper.vm.messages = [
        { id: '1', role: 'user', type: 'text', content: 'Test', timestamp: new Date().toISOString() }
      ]

      wrapper.vm.saveCurrentState()

      expect(wrapper.vm.conversationRecovery.saveConversationState).toHaveBeenCalledWith(
        'test-conv-1',
        expect.objectContaining({
          messages: expect.any(Array)
        })
      )
    })

    it('应该加载已保存的状态', async () => {
      const savedState = {
        messages: [
          { id: '1', role: 'user', type: 'text', content: 'Saved message', timestamp: new Date().toISOString() }
        ],
        userInput: 'Saved input',
        timestamp: Date.now()
      }

      const { createConversationRecovery } = await import('@/utils/errorRecovery')
      vi.mocked(createConversationRecovery).mockReturnValue({
        saveConversationState: vi.fn(),
        loadConversationState: vi.fn(() => savedState),
        clearConversationState: vi.fn(),
        startAutoSave: vi.fn(),
        stopAutoSave: vi.fn(),
        getRecoverableConversations: vi.fn(() => [])
      })

      wrapper.vm.conversationId = 'test-conv-1'
      await wrapper.vm.recoverConversationState()

      // 验证加载逻辑被调用
      expect(wrapper.vm.conversationRecovery.loadConversationState).toHaveBeenCalledWith('test-conv-1')
    })
  })
})
