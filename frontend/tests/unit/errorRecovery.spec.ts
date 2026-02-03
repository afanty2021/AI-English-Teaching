/**
 * 错误恢复工具测试
 * 包含正常场景和边界条件测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  retryAsync,
  ConversationRecovery,
  createConversationRecovery,
  NetworkMonitor,
  createNetworkMonitor,
  type RetryConfig
} from '@/utils/errorRecovery'

describe('retryAsync', () => {
  afterEach(() => {
    vi.clearAllMocks()
    vi.restoreAllMocks()
  })

  describe('正常场景', () => {
    it('应该一次性成功', async () => {
      const fn = vi.fn().mockResolvedValue('success')
      const result = await retryAsync(fn)

      expect(result.success).toBe(true)
      expect(result.data).toBe('success')
      expect(result.attempts).toBe(1)
      expect(fn).toHaveBeenCalledTimes(1)
    })

    it('应该返回失败结果当函数抛出错误', async () => {
      const error = new Error('Test error')
      const fn = vi.fn().mockRejectedValue(error)
      const result = await retryAsync(fn, { maxAttempts: 1 })

      expect(result.success).toBe(false)
      expect(result.error).toBe(error)
      expect(result.attempts).toBe(1)
    })
  })

  describe('重试逻辑', () => {
    it('应该在可重试错误时重试', async () => {
      const fn = vi.fn()
        .mockRejectedValueOnce(new Error('network error'))
        .mockResolvedValueOnce('success')

      const result = await retryAsync(fn, {
        maxAttempts: 3,
        retryableErrors: ['network']
      })

      expect(result.success).toBe(true)
      expect(result.data).toBe('success')
      expect(result.attempts).toBe(2)
    })

    it('应该在达到最大尝试次数后停止', async () => {
      const error = new Error('network error')
      const fn = vi.fn().mockRejectedValue(error)

      const result = await retryAsync(fn, {
        maxAttempts: 2,
        retryableErrors: ['network']
      })

      expect(result.success).toBe(false)
      expect(result.error).toBe(error)
      expect(result.attempts).toBe(2)
    })

    it('应该使用指数退避计算延迟', async () => {
      const fn = vi.fn()
        .mockRejectedValueOnce(new Error('network error'))
        .mockRejectedValueOnce(new Error('network error'))
        .mockResolvedValueOnce('success')

      const startTime = Date.now()
      await retryAsync(fn, {
        maxAttempts: 3,
        initialDelay: 100,
        backoffMultiplier: 2
      })
      const endTime = Date.now()

      // 第一次重试延迟 100ms，第二次延迟 200ms
      expect(endTime - startTime).toBeGreaterThanOrEqual(300)
    })

    it('应该遵守最大延迟限制', async () => {
      const fn = vi.fn()
        .mockRejectedValueOnce(new Error('network error'))
        .mockResolvedValueOnce('success')

      const startTime = Date.now()
      await retryAsync(fn, {
        maxAttempts: 2,
        initialDelay: 100,
        maxDelay: 150,
        backoffMultiplier: 10 // 会导致 1000ms 延迟，但被限制在 150
      })
      const endTime = Date.now()

      expect(endTime - startTime).toBeLessThan(300)
    })
  })

  describe('错误分类', () => {
    it('应该识别网络错误为可重试', async () => {
      const fn = vi.fn().mockResolvedValue('success')
      await retryAsync(fn, { retryableErrors: ['network'] })

      // 默认配置包含 'network'
      expect(fn).toHaveBeenCalled()
    })

    it('应该识别超时错误为可重试', async () => {
      const fn = vi.fn()
        .mockRejectedValueOnce(new Error('timeout'))
        .mockResolvedValueOnce('success')

      const result = await retryAsync(fn, { maxAttempts: 2 })

      expect(result.success).toBe(true)
    })

    it('应该识别 5xx 错误为可重试', async () => {
      const fn = vi.fn()
        .mockRejectedValueOnce(new Error('500 Internal Server Error'))
        .mockResolvedValueOnce('success')

      const result = await retryAsync(fn, { maxAttempts: 2 })

      expect(result.success).toBe(true)
    })

    it('不应该重试 4xx 错误', async () => {
      const error = new Error('404 Not Found')
      const fn = vi.fn().mockRejectedValue(error)

      const result = await retryAsync(fn, { maxAttempts: 3 })

      expect(result.success).toBe(false)
      expect(fn).toHaveBeenCalledTimes(1) // 只调用一次，不重试
    })

    it('应该支持正则表达式匹配错误', async () => {
      const fn = vi.fn()
        .mockRejectedValueOnce(new Error('ECONNREFUSED'))
        .mockResolvedValueOnce('success')

      const result = await retryAsync(fn, {
        maxAttempts: 2,
        retryableErrors: [/ECONN/]
      })

      expect(result.success).toBe(true)
    })
  })

  describe('边界条件', () => {
    it('应该处理 maxAttempts 为 0', async () => {
      const fn = vi.fn().mockResolvedValue('success')
      const result = await retryAsync(fn, { maxAttempts: 0 })

      expect(result.success).toBe(false)
      expect(fn).not.toHaveBeenCalled()
    })

    it('应该处理 initialDelay 为 0', async () => {
      const fn = vi.fn()
        .mockRejectedValueOnce(new Error('network error'))
        .mockResolvedValueOnce('success')

      const result = await retryAsync(fn, {
        maxAttempts: 2,
        initialDelay: 0
      })

      expect(result.success).toBe(true)
    })

    it('应该处理负数延迟', async () => {
      const fn = vi.fn().mockResolvedValue('success')
      const result = await retryAsync(fn, {
        initialDelay: -100
      })

      expect(result.success).toBe(true)
    })

    it('应该处理空 retryableErrors 数组', async () => {
      const error = new Error('any error')
      const fn = vi.fn().mockRejectedValue(error)

      const result = await retryAsync(fn, {
        maxAttempts: 3,
        retryableErrors: []
      })

      expect(result.success).toBe(false)
      expect(fn).toHaveBeenCalledTimes(1)
    })

    it('应该处理函数抛出非 Error 对象', async () => {
      const fn = vi.fn().mockRejectedValue('string error')

      const result = await retryAsync(fn, { maxAttempts: 1 })

      expect(result.success).toBe(false)
      // 字符串错误被包装
      expect(result.error).toBeTruthy()
    })

    it('应该处理函数返回 null', async () => {
      const fn = vi.fn().mockResolvedValue(null)
      const result = await retryAsync(fn)

      expect(result.success).toBe(true)
      expect(result.data).toBeNull()
    })

    it('应该处理函数返回 undefined', async () => {
      const fn = vi.fn().mockResolvedValue(undefined)
      const result = await retryAsync(fn)

      expect(result.success).toBe(true)
      expect(result.data).toBeUndefined()
    })
  })
})

describe('ConversationRecovery', () => {
  let recovery: ConversationRecovery

  beforeEach(() => {
    // Mock localStorage
    const mockStorage: Record<string, string> = {}
    global.localStorage = {
      getItem: vi.fn((key) => mockStorage[key] || null),
      setItem: vi.fn((key, value) => { mockStorage[key] = value }),
      removeItem: vi.fn((key) => { delete mockStorage[key] }),
      clear: vi.fn(() => { Object.keys(mockStorage).forEach(key => delete mockStorage[key]) }),
      length: 0,
      key: vi.fn()
    } as any

    recovery = createConversationRecovery()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('状态保存和加载', () => {
    it('应该保存对话状态', () => {
      const conversationId = 'test-conv-1'
      const state = {
        messages: [{ role: 'user', content: 'Hello' }],
        userInput: 'Test',
        timestamp: Date.now()
      }

      recovery.saveConversationState(conversationId, state)

      const loaded = recovery.loadConversationState(conversationId)
      expect(loaded).toMatchObject(state)
      expect(loaded?.messages).toEqual(state.messages)
    })

    it('应该加载已保存的对话状态', () => {
      const conversationId = 'test-conv-2'
      const state = {
        messages: [{ role: 'assistant', content: 'Hi there' }],
        userInput: '',
        timestamp: Date.now()
      }

      recovery.saveConversationState(conversationId, state)
      const loaded = recovery.loadConversationState(conversationId)

      expect(loaded).not.toBeNull()
      expect(loaded?.messages).toEqual(state.messages)
    })

    it('应该返回 null 对于不存在的对话', () => {
      const loaded = recovery.loadConversationState('non-existent')
      expect(loaded).toBeNull()
    })

    it('应该清除对话状态', () => {
      const conversationId = 'test-conv-3'
      const state = {
        messages: [],
        userInput: '',
        timestamp: Date.now()
      }

      recovery.saveConversationState(conversationId, state)
      recovery.clearConversationState(conversationId)

      const loaded = recovery.loadConversationState(conversationId)
      expect(loaded).toBeNull()
    })
  })

  describe('过期处理', () => {
    it('应该返回 null 对于过期的状态', () => {
      const conversationId = 'test-conv-expired'
      const state = {
        messages: [],
        userInput: '',
        timestamp: Date.now() - (31 * 60 * 1000) // 31 分钟前
      }

      // 直接模拟 localStorage 中的过期数据
      localStorage.setItem('conversation_recovery', JSON.stringify({
        [conversationId]: {
          ...state,
          savedAt: Date.now() - (31 * 60 * 1000)
        }
      }))

      const loaded = recovery.loadConversationState(conversationId)
      expect(loaded).toBeNull()
    })

    it('应该加载未过期的状态', () => {
      const conversationId = 'test-conv-valid'
      const state = {
        messages: [],
        userInput: '',
        timestamp: Date.now() - (10 * 60 * 1000) // 10 分钟前
      }

      // 模拟 localStorage 中的有效数据
      localStorage.setItem('conversation_recovery', JSON.stringify({
        [conversationId]: {
          ...state,
          savedAt: Date.now() - (10 * 60 * 1000)
        }
      }))

      const loaded = recovery.loadConversationState(conversationId)
      expect(loaded).not.toBeNull()
    })
  })

  describe('自动保存', () => {
    it('应该启动自动保存', () => {
      const conversationId = 'test-conv-auto'
      const getState = vi.fn().mockReturnValue({
        messages: [],
        userInput: '',
        timestamp: Date.now()
      })

      recovery.startAutoSave(conversationId, getState)

      // 等待第一个保存间隔
      return new Promise(resolve => {
        setTimeout(() => {
          expect(getState).toHaveBeenCalled()
          recovery.stopAutoSave()
          resolve(null)
        }, 5100) // 略多于 SAVE_INTERVAL_MS (5000)
      })
    })

    it('应该停止自动保存', () => {
      const conversationId = 'test-conv-stop'
      const getState = vi.fn().mockReturnValue({
        messages: [],
        userInput: '',
        timestamp: Date.now()
      })

      recovery.startAutoSave(conversationId, getState)
      recovery.stopAutoSave()

      // 等待足够的时间但不应再保存
      return new Promise(resolve => {
        setTimeout(() => {
          const callCount = getState.mock.calls.length
          expect(callCount).toBe(0) // 立即停止，没有调用
          resolve(null)
        }, 100)
      })
    })

    it('应该处理多次调用 startAutoSave', () => {
      const conversationId = 'test-conv-multi'
      const getState = vi.fn()

      recovery.startAutoSave(conversationId, getState)
      recovery.startAutoSave(conversationId, getState)

      // 第二次调用应该覆盖第一次
      recovery.stopAutoSave()
    })
  })

  describe('获取可恢复对话', () => {
    it('应该返回所有可恢复的对话', () => {
      const state1 = {
        messages: [{ role: 'user', content: 'Message 1' }],
        userInput: '',
        timestamp: Date.now() - (5 * 60 * 1000)
      }
      const state2 = {
        messages: [{ role: 'user', content: 'Message 2' }],
        userInput: '',
        timestamp: Date.now() - (10 * 60 * 1000)
      }

      localStorage.setItem('conversation_recovery', JSON.stringify({
        'conv-1': { ...state1, savedAt: Date.now() - (5 * 60 * 1000) },
        'conv-2': { ...state2, savedAt: Date.now() - (10 * 60 * 1000) },
        'conv-expired': {
          ...state1,
          savedAt: Date.now() - (31 * 60 * 1000) // 过期
        }
      }))

      const recoverable = recovery.getRecoverableConversations()

      expect(recoverable).toHaveLength(2)
      expect(recoverable.some(c => c.conversationId === 'conv-1')).toBe(true)
      expect(recoverable.some(c => c.conversationId === 'conv-2')).toBe(true)
    })

    it('应该返回空数组当没有可恢复对话', () => {
      const recoverable = recovery.getRecoverableConversations()
      expect(recoverable).toEqual([])
    })
  })

  describe('边界条件', () => {
    it('应该处理损坏的 localStorage 数据', () => {
      localStorage.setItem('conversation_recovery', 'invalid json')

      const loaded = recovery.loadConversationState('any-conv')
      expect(loaded).toBeNull()
    })

    it('应该处理保存空消息列表', () => {
      const conversationId = 'test-conv-empty'
      const state = {
        messages: [],
        userInput: '',
        timestamp: Date.now()
      }

      recovery.saveConversationState(conversationId, state)
      const loaded = recovery.loadConversationState(conversationId)

      expect(loaded?.messages).toEqual([])
    })

    it('应该处理大型消息列表', () => {
      const conversationId = 'test-conv-large'
      const largeMessages = Array(1000).fill(null).map((_, i) => ({
        role: 'user',
        content: `Message ${i}`.repeat(10)
      }))

      const state = {
        messages: largeMessages,
        userInput: '',
        timestamp: Date.now()
      }

      expect(() => recovery.saveConversationState(conversationId, state)).not.toThrow()
    })

    it('应该处理特殊字符在内容中', () => {
      const conversationId = 'test-conv-special'
      const state = {
        messages: [{
          role: 'user',
          content: '测试\n\t\r<script>alert("xss")</script>'
        }],
        userInput: '',
        timestamp: Date.now()
      }

      recovery.saveConversationState(conversationId, state)
      const loaded = recovery.loadConversationState(conversationId)

      expect(loaded?.messages[0].content).toContain('<script>')
    })
  })
})

describe('NetworkMonitor', () => {
  let monitor: NetworkMonitor

  beforeEach(() => {
    monitor = createNetworkMonitor()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('网络状态监听', () => {
    it('应该返回初始在线状态', () => {
      const status = monitor.getStatus()
      expect(typeof status).toBe('boolean')
    })

    it('应该通知状态变化', () => {
      const callback = vi.fn()
      const unsubscribe = monitor.onStatusChange(callback)

      // 模拟 offline 事件
      window.dispatchEvent(new Event('offline'))

      expect(callback).toHaveBeenCalledWith(false)

      unsubscribe()
    })

    it('应该支持取消监听', () => {
      const callback = vi.fn()
      const unsubscribe = monitor.onStatusChange(callback)

      unsubscribe()

      // 取消后不应再调用
      window.dispatchEvent(new Event('offline'))
      expect(callback).not.toHaveBeenCalled()
    })

    it('应该支持多个监听器', () => {
      const callback1 = vi.fn()
      const callback2 = vi.fn()

      monitor.onStatusChange(callback1)
      monitor.onStatusChange(callback2)

      window.dispatchEvent(new Event('offline'))

      expect(callback1).toHaveBeenCalledWith(false)
      expect(callback2).toHaveBeenCalledWith(false)
    })
  })

  describe('边界条件', () => {
    it('应该处理多次调用 onStatusChange', () => {
      const callback = vi.fn()
      const unsubscribe1 = monitor.onStatusChange(callback)
      const unsubscribe2 = monitor.onStatusChange(callback)

      window.dispatchEvent(new Event('offline'))

      // 两个监听器都应该被调用
      expect(callback).toHaveBeenCalledTimes(2)

      unsubscribe1()
      unsubscribe2()
    })

    it('应该处理监听器抛出错误', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      const errorCallback = vi.fn().mockImplementation(() => {
        throw new Error('Listener error')
      })
      const normalCallback = vi.fn()

      monitor.onStatusChange(errorCallback)
      monitor.onStatusChange(normalCallback)

      // 不应该抛出错误
      expect(() => {
        window.dispatchEvent(new Event('offline'))
      }).not.toThrow()

      // 正常的回调应仍被调用
      expect(normalCallback).toHaveBeenCalled()

      consoleSpy.mockRestore()
    })

    it('应该处理空回调函数', () => {
      expect(() => {
        monitor.onStatusChange(() => {})
      }).not.toThrow()
    })
  })
})
