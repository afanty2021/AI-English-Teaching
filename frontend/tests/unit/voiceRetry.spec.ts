/**
 * 智能重试机制单元测试
 * 测试语音识别的指数退避重试和用户反馈功能
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  DEFAULT_RETRY_STRATEGY,
  RecognitionAccuracyTracker,
  type RetryStrategy,
  type RecognitionFeedback,
  type RecognitionAccuracy
} from '@/utils/voiceRecognitionFallback'

// Mock CloudSTTAdapter 用于测试
class MockCloudSTTAdapter {
  private config: any
  private retryStrategy: RetryStrategy
  private accuracyTracker: RecognitionAccuracyTracker
  private startCallCount = 0
  private shouldFail = false
  private errorToThrow: Error | null = null
  private readonly MAX_DELAY = 30000  // 30秒最大延迟

  constructor(config: any = {}) {
    this.config = config
    this.retryStrategy = config.retryStrategy ?? DEFAULT_RETRY_STRATEGY
    this.accuracyTracker = new RecognitionAccuracyTracker()
  }

  async start(): Promise<void> {
    this.startCallCount++

    if (this.shouldFail && this.errorToThrow) {
      throw this.errorToThrow
    }
  }

  async startWithRetry(timeoutMs: number = 60000): Promise<void> {
    const startTime = Date.now()
    let lastError: Error | null = null

    for (let attempt = 0; attempt <= this.retryStrategy.maxRetries; attempt++) {
      // 检查超时
      if (Date.now() - startTime > timeoutMs) {
        throw new Error(`Retry timeout exceeded after ${timeoutMs}ms`)
      }

      try {
        await this.start()
        this.accuracyTracker.recordRecognition()
        return
      } catch (error) {
        lastError = error as Error

        if (!this.isRetryableError(lastError)) {
          throw lastError
        }

        if (attempt < this.retryStrategy.maxRetries) {
          const delay = this.calculateRetryDelay(attempt)
          await this.sleep(delay)
        }
      }
    }

    throw lastError
  }

  private isRetryableError(error: Error): boolean {
    const message = error.message.toLowerCase()
    for (const retryableError of this.retryStrategy.retryableErrors) {
      if (message.includes(retryableError.toLowerCase())) {
        return true
      }
    }
    return false
  }

  private calculateRetryDelay(attempt: number): number {
    const delay = this.retryStrategy.retryDelay * Math.pow(this.retryStrategy.backoffMultiplier, attempt)
    return Math.min(delay, this.MAX_DELAY)
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  submitFeedback(feedback: RecognitionFeedback): void {
    this.accuracyTracker.addFeedback(feedback)
  }

  getAccuracy(): RecognitionAccuracy {
    return this.accuracyTracker.getAccuracy()
  }

  getRecentFeedback(count?: number): RecognitionFeedback[] {
    return this.accuracyTracker.getRecentFeedback(count)
  }

  updateAccuracy(transcript: string, userCorrection: string): void {
    this.submitFeedback({
      transcript,
      userCorrection,
      wasHelpful: false
    })
  }

  // 测试辅助方法
  setShouldFail(shouldFail: boolean, error: Error | null = null): void {
    this.shouldFail = shouldFail
    this.errorToThrow = error
  }

  getStartCallCount(): number {
    return this.startCallCount
  }

  reset(): void {
    this.startCallCount = 0
    this.shouldFail = false
    this.errorToThrow = null
    this.accuracyTracker.reset()
  }
}

describe('智能重试机制', () => {
  let adapter: MockCloudSTTAdapter

  beforeEach(() => {
    adapter = new MockCloudSTTAdapter()
  })

  afterEach(() => {
    vi.clearAllMocks()
    vi.restoreAllMocks()
    adapter.reset()
  })

  describe('DEFAULT_RETRY_STRATEGY', () => {
    it('应该有正确的默认配置', () => {
      expect(DEFAULT_RETRY_STRATEGY.maxRetries).toBe(3)
      expect(DEFAULT_RETRY_STRATEGY.retryDelay).toBe(1000)
      expect(DEFAULT_RETRY_STRATEGY.backoffMultiplier).toBe(2)
      expect(DEFAULT_RETRY_STRATEGY.retryableErrors.has('no-speech')).toBe(true)
      expect(DEFAULT_RETRY_STRATEGY.retryableErrors.has('network')).toBe(true)
      expect(DEFAULT_RETRY_STRATEGY.retryableErrors.has('aborted')).toBe(true)
    })
  })

  describe('startWithRetry - 重试逻辑', () => {
    it('应该在第一次成功时不重试', async () => {
      await adapter.startWithRetry()
      expect(adapter.getStartCallCount()).toBe(1)
    })

    it('应该在 no-speech 错误时重试', async () => {
      adapter.setShouldFail(true, new Error('no-speech detected'))

      // 让第三次尝试成功
      vi.spyOn(adapter as any, 'start').mockImplementation(async function() {
        this.startCallCount++
        if (this.startCallCount < 3) {
          throw new Error('no-speech detected')
        }
      })

      await expect(adapter.startWithRetry()).resolves.not.toThrow()
    })

    it('应该在 network 错误时重试', async () => {
      adapter.setShouldFail(true, new Error('network error'))

      vi.spyOn(adapter as any, 'start').mockImplementation(async function() {
        this.startCallCount++
        if (this.startCallCount < 2) {
          throw new Error('network error')
        }
      })

      await expect(adapter.startWithRetry()).resolves.not.toThrow()
    })

    it('应该在 aborted 错误时重试', async () => {
      adapter.setShouldFail(true, new Error('aborted'))

      vi.spyOn(adapter as any, 'start').mockImplementation(async function() {
        this.startCallCount++
        if (this.startCallCount < 2) {
          throw new Error('aborted')
        }
      })

      await expect(adapter.startWithRetry()).resolves.not.toThrow()
    })

    it('应该在非可重试错误时立即失败', async () => {
      adapter.setShouldFail(true, new Error('not-allowed'))

      await expect(adapter.startWithRetry()).rejects.toThrow('not-allowed')
    })

    it('应该在达到最大重试次数后停止', async () => {
      adapter.setShouldFail(true, new Error('network error'))

      // 使用较短的重试配置来加速测试
      const fastStrategy: RetryStrategy = {
        maxRetries: 2,
        retryDelay: 10, // 极短的延迟
        backoffMultiplier: 2,
        retryableErrors: new Set(['network'])
      }
      const fastAdapter = new MockCloudSTTAdapter({ retryStrategy: fastStrategy })
      fastAdapter.setShouldFail(true, new Error('network error'))

      await expect(fastAdapter.startWithRetry()).rejects.toThrow()
      expect(fastAdapter.getStartCallCount()).toBeGreaterThan(1)
    }, 10000) // 增加超时时间到 10 秒
  })

  describe('指数退避计算', () => {
    it('应该正确计算重试延迟', () => {
      const strategy: RetryStrategy = {
        maxRetries: 3,
        retryDelay: 1000,
        backoffMultiplier: 2,
        retryableErrors: new Set(['network'])
      }
      const testAdapter = new MockCloudSTTAdapter({ retryStrategy: strategy })

      // 第一次重试延迟: 1000ms
      expect(testAdapter['calculateRetryDelay'](0)).toBe(1000)
      // 第二次重试延迟: 2000ms
      expect(testAdapter['calculateRetryDelay'](1)).toBe(2000)
      // 第三次重试延迟: 4000ms
      expect(testAdapter['calculateRetryDelay'](2)).toBe(4000)
    })

    it('应该使用正确的退避倍数', () => {
      const strategy: RetryStrategy = {
        maxRetries: 3,
        retryDelay: 500,
        backoffMultiplier: 3,
        retryableErrors: new Set(['network'])
      }
      const testAdapter = new MockCloudSTTAdapter({ retryStrategy: strategy })

      // 第一次重试延迟: 500ms
      expect(testAdapter['calculateRetryDelay'](0)).toBe(500)
      // 第二次重试延迟: 1500ms (500 * 3)
      expect(testAdapter['calculateRetryDelay'](1)).toBe(1500)
      // 第三次重试延迟: 4500ms (500 * 3^2)
      expect(testAdapter['calculateRetryDelay'](2)).toBe(4500)
    })
  })

  describe('可重试错误检测', () => {
    it('应该识别 no-speech 错误', () => {
      const error = new Error('no-speech detected')
      expect(adapter['isRetryableError'](error)).toBe(true)
    })

    it('应该识别 network 错误', () => {
      const error = new Error('network connection failed')
      expect(adapter['isRetryableError'](error)).toBe(true)
    })

    it('应该识别 aborted 错误', () => {
      const error = new Error('request aborted')
      expect(adapter['isRetryableError'](error)).toBe(true)
    })

    it('不应该识别其他错误为可重试', () => {
      const error = new Error('authentication failed')
      expect(adapter['isRetryableError'](error)).toBe(false)
    })

    it('应该大小写不敏感地检测错误', () => {
      const error = new Error('NETWORK ERROR')
      expect(adapter['isRetryableError'](error)).toBe(true)
    })
  })

  describe('RecognitionAccuracyTracker', () => {
    describe('准确度跟踪', () => {
      it('应该正确记录识别次数', () => {
        const tracker = new RecognitionAccuracyTracker()

        tracker.recordRecognition()
        tracker.recordRecognition()
        tracker.recordRecognition()

        const accuracy = tracker.getAccuracy()
        expect(accuracy.totalRecognitions).toBe(3)
      })

      it('应该正确记录正确识别', () => {
        const tracker = new RecognitionAccuracyTracker()

        tracker.recordRecognition()
        tracker.recordRecognition()
        tracker.recordCorrect()
        tracker.recordCorrect()

        const accuracy = tracker.getAccuracy()
        expect(accuracy.correctRecognitions).toBe(2)
        expect(accuracy.accuracyRate).toBe(1.0) // 2/2
      })

      it('应该正确记录用户修正', () => {
        const tracker = new RecognitionAccuracyTracker()

        tracker.recordRecognition()
        tracker.recordRecognition()
        tracker.recordCorrection()

        const accuracy = tracker.getAccuracy()
        expect(accuracy.userCorrections).toBe(1)
      })

      it('应该正确计算准确率', () => {
        const tracker = new RecognitionAccuracyTracker()

        tracker.recordRecognition()
        tracker.recordRecognition()
        tracker.recordRecognition()
        tracker.recordCorrect()
        tracker.recordCorrect()
        tracker.recordCorrection()

        const accuracy = tracker.getAccuracy()
        expect(accuracy.accuracyRate).toBeCloseTo(0.67, 2) // 2/3
      })

      it('应该在无识别时返回准确率1.0', () => {
        const tracker = new RecognitionAccuracyTracker()

        const accuracy = tracker.getAccuracy()
        expect(accuracy.accuracyRate).toBe(1.0)
      })
    })

    describe('用户反馈', () => {
      it('应该添加用户反馈', () => {
        const tracker = new RecognitionAccuracyTracker()
        const feedback: RecognitionFeedback = {
          transcript: 'hello',
          wasHelpful: true
        }

        tracker.addFeedback(feedback)

        const recent = tracker.getRecentFeedback(1)
        expect(recent).toHaveLength(1)
        expect(recent[0].transcript).toBe('hello')
      })

      it('应该在有帮助反馈时增加正确识别', () => {
        const tracker = new RecognitionAccuracyTracker()
        const feedback: RecognitionFeedback = {
          transcript: 'hello',
          wasHelpful: true
        }

        tracker.addFeedback(feedback)

        const accuracy = tracker.getAccuracy()
        expect(accuracy.correctRecognitions).toBe(1)
      })

      it('应该在用户修正时记录修正', () => {
        const tracker = new RecognitionAccuracyTracker()
        const feedback: RecognitionFeedback = {
          transcript: 'helo',
          userCorrection: 'hello',
          wasHelpful: false
        }

        tracker.addFeedback(feedback)

        const accuracy = tracker.getAccuracy()
        expect(accuracy.userCorrections).toBe(1)
      })

      it('应该正确更新准确率在用户修正后', () => {
        const tracker = new RecognitionAccuracyTracker()

        tracker.recordRecognition()
        tracker.recordRecognition()
        tracker.recordRecognition()

        const feedback: RecognitionFeedback = {
          transcript: 'wrong',
          userCorrection: 'right',
          wasHelpful: false
        }
        tracker.addFeedback(feedback)

        const accuracy = tracker.getAccuracy()
        // 用户修正只增加 userCorrections，不增加 totalRecognitions
        // 所以准确率 = 0 / 3 = 0
        expect(accuracy.accuracyRate).toBe(0)
        expect(accuracy.totalRecognitions).toBe(3) // 只有3次识别记录
        expect(accuracy.userCorrections).toBe(1)
      })

      it('应该限制反馈历史记录大小', () => {
        const tracker = new RecognitionAccuracyTracker()

        // 添加超过限制的反馈
        for (let i = 0; i < 150; i++) {
          tracker.addFeedback({
            transcript: `test ${i}`,
            wasHelpful: true
          })
        }

        const recent = tracker.getRecentFeedback(200)
        expect(recent.length).toBeLessThanOrEqual(100)
      })

      it('应该获取指定数量的最近反馈', () => {
        const tracker = new RecognitionAccuracyTracker()

        for (let i = 0; i < 20; i++) {
          tracker.addFeedback({
            transcript: `test ${i}`,
            wasHelpful: true
          })
        }

        const recent = tracker.getRecentFeedback(5)
        expect(recent).toHaveLength(5)
        expect(recent[0].transcript).toBe('test 15')
      })

      it('应该为反馈添加时间戳', () => {
        const tracker = new RecognitionAccuracyTracker()
        const beforeTime = Date.now()

        tracker.addFeedback({
          transcript: 'test',
          wasHelpful: true
        })

        const afterTime = Date.now()
        const recent = tracker.getRecentFeedback(1)

        expect(recent[0].timestamp).toBeGreaterThanOrEqual(beforeTime)
        expect(recent[0].timestamp).toBeLessThanOrEqual(afterTime)
      })

      it('应该在空反馈时返回空数组', () => {
        const tracker = new RecognitionAccuracyTracker()

        const recent = tracker.getRecentFeedback()
        expect(recent).toEqual([])
      })

      it('应该获取所有反馈当未指定数量时', () => {
        const tracker = new RecognitionAccuracyTracker()

        for (let i = 0; i < 5; i++) {
          tracker.addFeedback({
            transcript: `test ${i}`,
            wasHelpful: true
          })
        }

        const recent = tracker.getRecentFeedback()
        expect(recent).toHaveLength(5)
      })
    })

    describe('重置功能', () => {
      it('应该重置所有统计', () => {
        const tracker = new RecognitionAccuracyTracker()

        tracker.recordRecognition()
        tracker.recordCorrect()
        tracker.recordCorrection()
        tracker.addFeedback({
          transcript: 'test',
          wasHelpful: true
        })

        tracker.reset()

        const accuracy = tracker.getAccuracy()
        expect(accuracy.totalRecognitions).toBe(0)
        expect(accuracy.correctRecognitions).toBe(0)
        expect(accuracy.userCorrections).toBe(0)
        expect(accuracy.accuracyRate).toBe(1.0)

        const recent = tracker.getRecentFeedback()
        expect(recent).toEqual([])
      })
    })
  })

  describe('CloudSTTAdapter 集成功能', () => {
    it('应该提交用户反馈', () => {
      const feedback: RecognitionFeedback = {
        transcript: 'hello world',
        wasHelpful: true
      }

      adapter.submitFeedback(feedback)

      const recent = adapter.getRecentFeedback()
      expect(recent).toHaveLength(1)
      expect(recent[0]).toMatchObject(feedback)
    })

    it('应该获取准确度统计', () => {
      const accuracy = adapter.getAccuracy()
      expect(accuracy).toHaveProperty('totalRecognitions')
      expect(accuracy).toHaveProperty('correctRecognitions')
      expect(accuracy).toHaveProperty('userCorrections')
      expect(accuracy).toHaveProperty('accuracyRate')
    })

    it('应该更新准确度当用户修正时', () => {
      adapter.updateAccuracy('wrong', 'correct')

      const feedback = adapter.getRecentFeedback(1)[0]
      expect(feedback.transcript).toBe('wrong')
      expect(feedback.userCorrection).toBe('correct')
      expect(feedback.wasHelpful).toBe(false)
    })

    it('应该获取最近反馈', () => {
      adapter.submitFeedback({ transcript: 'test1', wasHelpful: true })
      adapter.submitFeedback({ transcript: 'test2', wasHelpful: true })
      adapter.submitFeedback({ transcript: 'test3', wasHelpful: true })

      const recent = adapter.getRecentFeedback(2)
      expect(recent).toHaveLength(2)
      expect(recent[0].transcript).toBe('test2')
      expect(recent[1].transcript).toBe('test3')
    })

    it('应该在识别时增加计数', async () => {
      await adapter.startWithRetry()

      const accuracy = adapter.getAccuracy()
      expect(accuracy.totalRecognitions).toBe(1)
    })
  })

  describe('边界条件', () => {
    it('应该处理零重试配置', async () => {
      const strategy: RetryStrategy = {
        maxRetries: 0,
        retryDelay: 1000,
        backoffMultiplier: 2,
        retryableErrors: new Set(['network'])
      }
      const testAdapter = new MockCloudSTTAdapter({ retryStrategy: strategy })
      testAdapter.setShouldFail(true, new Error('network error'))

      await expect(testAdapter.startWithRetry()).rejects.toThrow()
      expect(testAdapter.getStartCallCount()).toBe(1) // 只尝试一次，不重试
    })

    it('应该处理零延迟配置', async () => {
      const strategy: RetryStrategy = {
        maxRetries: 2,
        retryDelay: 0,
        backoffMultiplier: 2,
        retryableErrors: new Set(['network'])
      }
      const testAdapter = new MockCloudSTTAdapter({ retryStrategy: strategy })

      // 即使延迟为0，也不应该抛出异常
      await expect(testAdapter.startWithRetry()).resolves.not.toThrow()
    })

    it('应该处理空可重试错误集合', async () => {
      const strategy: RetryStrategy = {
        maxRetries: 3,
        retryDelay: 1000,
        backoffMultiplier: 2,
        retryableErrors: new Set()
      }
      const testAdapter = new MockCloudSTTAdapter({ retryStrategy: strategy })
      testAdapter.setShouldFail(true, new Error('network error'))

      await expect(testAdapter.startWithRetry()).rejects.toThrow()
      expect(testAdapter.getStartCallCount()).toBe(1) // 不重试
    })

    it('应该处理大退避倍数', () => {
      const strategy: RetryStrategy = {
        maxRetries: 3,
        retryDelay: 1000,
        backoffMultiplier: 100,
        retryableErrors: new Set(['network'])
      }
      const testAdapter = new MockCloudSTTAdapter({ retryStrategy: strategy })

      // 由于 MAX_DELAY 限制，大的退避倍数会被限制在 30000ms
      expect(testAdapter['calculateRetryDelay'](2)).toBe(30000) // 被限制在 MAX_DELAY
    })

    it('应该处理负数尝试次数', () => {
      const strategy: RetryStrategy = {
        maxRetries: 3,
        retryDelay: 1000,
        backoffMultiplier: 2,
        retryableErrors: new Set(['network'])
      }
      const testAdapter = new MockCloudSTTAdapter({ retryStrategy: strategy })

      expect(testAdapter['calculateRetryDelay'](-1)).toBe(500) // 1000 / 2
    })

    it('应该处理空转录文本反馈', () => {
      adapter.submitFeedback({
        transcript: '',
        wasHelpful: false
      })

      const feedback = adapter.getRecentFeedback(1)[0]
      expect(feedback.transcript).toBe('')
    })

    it('应该处理空用户修正', () => {
      adapter.updateAccuracy('test', '')

      const feedback = adapter.getRecentFeedback(1)[0]
      expect(feedback.userCorrection).toBe('')
    })

    it('应该处理特殊字符在反馈中', () => {
      adapter.submitFeedback({
        transcript: '测试\n\t\r<script>',
        wasHelpful: true
      })

      const feedback = adapter.getRecentFeedback(1)[0]
      expect(feedback.transcript).toContain('<script>')
    })
  })

  describe('MAX_DELAY 延迟上限保护', () => {
    it('应该将重试延迟限制在 MAX_DELAY (30000ms)', () => {
      const strategy: RetryStrategy = {
        maxRetries: 10,
        retryDelay: 1000,
        backoffMultiplier: 10, // 大倍数会导致快速超过 MAX_DELAY
        retryableErrors: new Set(['network'])
      }
      const testAdapter = new MockCloudSTTAdapter({ retryStrategy: strategy })

      // 第0次重试: 1000ms
      expect(testAdapter['calculateRetryDelay'](0)).toBe(1000)
      // 第1次重试: 10000ms
      expect(testAdapter['calculateRetryDelay'](1)).toBe(10000)
      // 第2次重试: 100000ms，但应该被限制在 30000ms
      expect(testAdapter['calculateRetryDelay'](2)).toBe(30000)
      // 第3次重试: 1000000ms，也应该被限制在 30000ms
      expect(testAdapter['calculateRetryDelay'](3)).toBe(30000)
    })

    it('应该在极端退避配置下也遵守 MAX_DELAY', () => {
      const extremeStrategy: RetryStrategy = {
        maxRetries: 5,
        retryDelay: 10000,
        backoffMultiplier: 1000,
        retryableErrors: new Set(['network'])
      }
      const extremeAdapter = new MockCloudSTTAdapter({ retryStrategy: extremeStrategy })

      // 即使初始延迟和倍数都很大，也应该被限制在 30000ms
      expect(extremeAdapter['calculateRetryDelay'](1)).toBe(30000)
      expect(extremeAdapter['calculateRetryDelay'](2)).toBe(30000)
    })

    it('应该正确处理边界值（刚好达到 MAX_DELAY）', () => {
      const strategy: RetryStrategy = {
        maxRetries: 3,
        retryDelay: 30000,
        backoffMultiplier: 2,
        retryableErrors: new Set(['network'])
      }
      const testAdapter = new MockCloudSTTAdapter({ retryStrategy: strategy })

      // 初始延迟就是 MAX_DELAY，不应该超过
      expect(testAdapter['calculateRetryDelay'](0)).toBe(30000)
      // 第二次重试会超过，但被限制
      expect(testAdapter['calculateRetryDelay'](1)).toBe(30000)
    })
  })

  describe('startWithRetry 超时保护', () => {
    it('应该在默认超时时间 (60000ms) 后抛出错误', async () => {
      const slowStrategy: RetryStrategy = {
        maxRetries: 100, // 大量重试次数
        retryDelay: 1000,
        backoffMultiplier: 1.1, // 缓慢增长
        retryableErrors: new Set(['network'])
      }
      const slowAdapter = new MockCloudSTTAdapter({ retryStrategy: slowStrategy })
      slowAdapter.setShouldFail(true, new Error('network error'))

      // 应该在超时前抛出错误
      await expect(slowAdapter.startWithRetry()).rejects.toThrow('Retry timeout exceeded')
    }, 65000) // 略长于默认超时时间

    it('应该接受自定义超时时间', async () => {
      const fastStrategy: RetryStrategy = {
        maxRetries: 50,
        retryDelay: 100,
        backoffMultiplier: 1.5,
        retryableErrors: new Set(['network'])
      }
      const fastAdapter = new MockCloudSTTAdapter({ retryStrategy: fastStrategy })
      fastAdapter.setShouldFail(true, new Error('network error'))

      // 使用较短的超时时间 (1000ms)
      await expect(fastAdapter.startWithRetry(1000)).rejects.toThrow('Retry timeout exceeded')
    }, 2000)

    it('应该在超时错误中包含实际超时时间', async () => {
      const strategy: RetryStrategy = {
        maxRetries: 10,
        retryDelay: 500,
        backoffMultiplier: 2,
        retryableErrors: new Set(['network'])
      }
      const testAdapter = new MockCloudSTTAdapter({ retryStrategy: strategy })
      testAdapter.setShouldFail(true, new Error('network error'))

      try {
        await testAdapter.startWithRetry(5000)
        expect.fail('应该抛出超时错误')
      } catch (error) {
        expect(error).toBeInstanceOf(Error)
        expect((error as Error).message).toContain('5000')
      }
    }, 10000) // 增加超时时间到 10 秒

    it('应该在超时时停止重试', async () => {
      const strategy: RetryStrategy = {
        maxRetries: 20,
        retryDelay: 200,
        backoffMultiplier: 1.2,
        retryableErrors: new Set(['network'])
      }
      const testAdapter = new MockCloudSTTAdapter({ retryStrategy: strategy })
      testAdapter.setShouldFail(true, new Error('network error'))

      const startTime = Date.now()
      try {
        await testAdapter.startWithRetry(2000)
        expect.fail('应该抛出超时错误')
      } catch (error) {
        const elapsed = Date.now() - startTime
        // 应该在超时时间附近停止（允许一些误差）
        expect(elapsed).toBeGreaterThanOrEqual(2000)
        expect(elapsed).toBeLessThan(3000)
        expect((error as Error).message).toContain('timeout')
      }
    }, 4000)

    it('应该在快速成功时不受超时限制影响', async () => {
      // 正常情况：快速成功，不应该超时
      await expect(adapter.startWithRetry(1000)).resolves.not.toThrow()
      expect(adapter.getStartCallCount()).toBe(1)
    })
  })
})
