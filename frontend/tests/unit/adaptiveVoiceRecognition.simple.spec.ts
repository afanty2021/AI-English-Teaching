/**
 * 自适应语音识别系统简化单元测试
 */

import { describe, it, expect, vi } from 'vitest'
import { AdaptiveVoiceRecognition } from '../../src/utils/adaptiveVoiceRecognition'

describe('AdaptiveVoiceRecognition (简化测试)', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      blob: async () => new Blob(['test'])
    }))
    vi.stubGlobal('performance', {
      now: vi.fn().mockReturnValue(0)
    })
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  describe('constructor', () => {
    it('应该使用默认配置创建实例', () => {
      const engine = new AdaptiveVoiceRecognition()
      expect(engine).toBeDefined()
    })

    it('应该使用自定义配置创建实例', () => {
      const engine = new AdaptiveVoiceRecognition({
        preferCloudSTT: false,
        maxRetries: 5
      })
      expect(engine).toBeDefined()
    })
  })

  describe('getPerformanceReport', () => {
    it('应该返回性能报告', () => {
      const engine = new AdaptiveVoiceRecognition()
      const report = engine.getPerformanceReport()

      expect(report).toHaveProperty('currentEngine')
      expect(report).toHaveProperty('engines')
      expect(report).toHaveProperty('performance')
      expect(report).toHaveProperty('options')
      expect(Array.isArray(report.engines)).toBe(true)
    })
  })

  describe('updateOptions', () => {
    it('应该更新配置', () => {
      const engine = new AdaptiveVoiceRecognition()

      engine.updateOptions({
        preferCloudSTT: false,
        maxRetries: 10
      })

      const report = engine.getPerformanceReport()
      expect(report.options.preferCloudSTT).toBe(false)
    })
  })
})

describe('便利函数', () => {
  it('应该提供便利的创建函数', () => {
    const { adaptiveVoiceRecognition } = require('../../src/utils/adaptiveVoiceRecognition')

    expect(adaptiveVoiceRecognition.create).toBeDefined()
    expect(typeof adaptiveVoiceRecognition.create).toBe('function')
  })
})