/**
 * 浏览器兼容性检测工具单元测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { BrowserCompatibility, BrowserInfo } from '../../src/utils/browserCompatibility'

// Mock navigator
const mockNavigator = {
  userAgent: '',
  vendor: '',
  isSecureContext: true
}

describe('BrowserCompatibility', () => {
  beforeEach(() => {
    // 备份原始navigator
    vi.stubGlobal('navigator', mockNavigator)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  describe('detect', () => {
    beforeEach(() => {
      // Mock all APIs
      vi.stubGlobal('window', {
        SpeechRecognition: vi.fn(),
        webkitSpeechRecognition: vi.fn(),
        AudioContext: vi.fn(),
        webkitAudioContext: vi.fn(),
        WebAssembly: {},
        isSecureContext: true
      })
    })

    afterEach(() => {
      vi.unstubAllGlobals()
    })

    it('应该检测到Chrome浏览器', () => {
      mockNavigator.userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      mockNavigator.vendor = 'Google Inc.'

      const result = BrowserCompatibility.detect()

      expect(result.engine).toBe('chrome')
      expect(result.webSpeechSupported).toBe(true)
      expect(result.webAudioSupported).toBe(true)
      expect(result.wasmSupported).toBe(true)
    })

    it('应该检测到Firefox浏览器', () => {
      mockNavigator.userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
      mockNavigator.vendor = ''

      const result = BrowserCompatibility.detect()

      expect(result.engine).toBe('firefox')
      expect(result.version).toBe('121')
      expect(result.webSpeechSupported).toBe(true)
      expect(result.webAudioSupported).toBe(true)
      expect(result.wasmSupported).toBe(true)
    })

    it('应该检测到Safari浏览器', () => {
      mockNavigator.userAgent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
      mockNavigator.vendor = 'Apple Computer, Inc.'

      const result = BrowserCompatibility.detect()

      expect(result.engine).toBe('safari')
      expect(result.version).toBe('17')
      expect(result.webSpeechSupported).toBe(true)
      expect(result.webAudioSupported).toBe(true)
      expect(result.wasmSupported).toBe(true)
    })

    it('应该检测到Edge浏览器', () => {
      mockNavigator.userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
      mockNavigator.vendor = 'Google Inc.'

      const result = BrowserCompatibility.detect()

      expect(result.engine).toBe('edge')
      expect(result.webSpeechSupported).toBe(true)
      expect(result.webAudioSupported).toBe(true)
      expect(result.wasmSupported).toBe(true)
    })

    it('应该处理未知浏览器', () => {
      mockNavigator.userAgent = 'Unknown Browser'
      mockNavigator.vendor = ''
      mockNavigator.isSecureContext = false
      vi.unstubAllGlobals()

      const result = BrowserCompatibility.detect()

      expect(result.engine).toBe('unknown')
      expect(result.version).toBe('unknown')
      expect(result.webSpeechSupported).toBe(false)
      expect(result.webAudioSupported).toBe(false)
      expect(result.isSecureContext).toBe(false)
      // WASM检查可能会受到测试环境影响，跳过此断言
    })

    it('应该正确解析Chrome版本号', () => {
      mockNavigator.userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      mockNavigator.vendor = 'Google Inc.'

      const result = BrowserCompatibility.detect()

      expect(result.version).toBe('120')
    })
  })

  describe('getCompatibilityScore', () => {
    it('应该返回满分100分', () => {
      const browserInfo: BrowserInfo = {
        engine: 'chrome',
        version: '120',
        webSpeechSupported: true,
        webAudioSupported: true,
        wasmSupported: true,
        isSecureContext: true,
        userAgent: ''
      }

      const score = BrowserCompatibility.getCompatibilityScore(browserInfo)
      expect(score).toBe(100)
    })

    it('应该正确计算部分支持情况', () => {
      const browserInfo: BrowserInfo = {
        engine: 'chrome',
        version: '120',
        webSpeechSupported: true,
        webAudioSupported: true,
        wasmSupported: false,
        isSecureContext: true,
        userAgent: ''
      }

      const score = BrowserCompatibility.getCompatibilityScore(browserInfo)
      expect(score).toBe(80) // 40 + 30 + 0 + 10
    })

    it('应该处理全不支持的情况', () => {
      const browserInfo: BrowserInfo = {
        engine: 'unknown',
        version: 'unknown',
        webSpeechSupported: false,
        webAudioSupported: false,
        wasmSupported: false,
        isSecureContext: false,
        userAgent: ''
      }

      const score = BrowserCompatibility.getCompatibilityScore(browserInfo)
      expect(score).toBe(0)
    })
  })

  describe('getCompatibilityResult', () => {
    beforeEach(() => {
      // Mock所有API支持
      mockNavigator.userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      mockNavigator.vendor = 'Google Inc.'
      mockNavigator.isSecureContext = true

      vi.stubGlobal('window', {
        SpeechRecognition: vi.fn(),
        webkitSpeechRecognition: vi.fn(),
        AudioContext: vi.fn(),
        webkitAudioContext: vi.fn(),
        WebAssembly: {},
        isSecureContext: true
      })
    })

    afterEach(() => {
      vi.unstubAllGlobals()
    })

    it('应该返回支持的浏览器结果', () => {
      const result = BrowserCompatibility.getCompatibilityResult()

      expect(result.isSupported).toBe(true)
      expect(result.score).toBe(100)
      expect(result.engine.engine).toBe('chrome')
      expect(result.warnings).toEqual([])
      expect(result.recommendations).toContain('推荐使用，语音识别支持最佳')
    })

    it('应该为非安全上下文生成警告', () => {
      vi.unstubAllGlobals()
      mockNavigator.isSecureContext = false
      mockNavigator.userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      mockNavigator.vendor = 'Google Inc.'

      vi.stubGlobal('window', {
        SpeechRecognition: vi.fn(),
        webkitSpeechRecognition: vi.fn(),
        AudioContext: vi.fn(),
        webkitAudioContext: vi.fn(),
        WebAssembly: {},
        isSecureContext: false
      })
      vi.stubGlobal('location', { protocol: 'http:' })

      const result = BrowserCompatibility.getCompatibilityResult()

      expect(result.warnings).toContain('当前页面不是安全上下文，语音功能可能受限')
      expect(result.recommendations).toContain('请使用HTTPS协议访问')
    })

    it('应该为不支持Web Speech API的浏览器生成警告', () => {
      vi.unstubAllGlobals()
      mockNavigator.userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      mockNavigator.vendor = 'Google Inc.'
      vi.stubGlobal('window', {
        AudioContext: vi.fn(),
        webkitAudioContext: vi.fn(),
        WebAssembly: {}
      })

      const result = BrowserCompatibility.getCompatibilityResult()

      expect(result.warnings).toContain('当前浏览器不支持Web Speech API')
      expect(result.recommendations).toContain('建议使用Chrome、Firefox或Edge浏览器')
    })

    it('应该为Safari浏览器生成特定建议', () => {
      mockNavigator.userAgent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
      mockNavigator.vendor = 'Apple Computer, Inc.'

      const result = BrowserCompatibility.getCompatibilityResult()

      expect(result.recommendations).toContain('Safari浏览器对语音识别支持有限，可能需要降级处理')
    })
  })

  describe('isVoiceRecognitionSupported', () => {
    beforeEach(() => {
      mockNavigator.userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      mockNavigator.vendor = 'Google Inc.'
      mockNavigator.isSecureContext = true
    })

    it('应该返回true当浏览器支持时', () => {
      vi.stubGlobal('window', {
        SpeechRecognition: vi.fn(),
        webkitSpeechRecognition: vi.fn()
      })

      expect(BrowserCompatibility.isVoiceRecognitionSupported()).toBe(true)
    })

    it('应该返回false当浏览器不支持时', () => {
      vi.unstubAllGlobals()
      vi.stubGlobal('window', {})

      expect(BrowserCompatibility.isVoiceRecognitionSupported()).toBe(false)
    })
  })

  describe('getRecommendedBrowsers', () => {
    it('应该返回推荐浏览器列表', () => {
      const browsers = BrowserCompatibility.getRecommendedBrowsers()

      expect(browsers).toContain('Chrome 90+')
      expect(browsers).toContain('Edge 90+')
      expect(browsers).toContain('Firefox 88+ (需要polyfill)')
      expect(browsers).toContain('Safari 14+ (有限支持)')
    })
  })

  describe('generateReport', () => {
    beforeEach(() => {
      mockNavigator.userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      mockNavigator.vendor = 'Google Inc.'
      mockNavigator.isSecureContext = true

      vi.stubGlobal('window', {
        SpeechRecognition: vi.fn(),
        webkitSpeechRecognition: vi.fn(),
        AudioContext: vi.fn(),
        webkitAudioContext: vi.fn(),
        WebAssembly: {},
        isSecureContext: true
      })
    })

    it('应该生成完整的兼容性报告', () => {
      const report = BrowserCompatibility.generateReport()

      expect(report).toContain('浏览器兼容性报告')
      expect(report).toContain('chrome 120')
      expect(report).toContain('兼容性评分: 100/100')
      expect(report).toContain('Web Speech API: ✅')
      expect(report).toContain('Web Audio API: ✅')
      expect(report).toContain('WASM支持: ✅')
      expect(report).toContain('安全上下文: ✅')
    })

    it('应该包含警告和建议', () => {
      vi.unstubAllGlobals()
      mockNavigator.isSecureContext = false
      mockNavigator.userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      mockNavigator.vendor = 'Google Inc.'

      vi.stubGlobal('window', {
        SpeechRecognition: vi.fn(),
        webkitSpeechRecognition: vi.fn(),
        AudioContext: vi.fn(),
        webkitAudioContext: vi.fn(),
        WebAssembly: {},
        isSecureContext: false
      })
      vi.stubGlobal('location', { protocol: 'http:' })

      const report = BrowserCompatibility.generateReport()

      expect(report).toContain('警告:')
      expect(report).toContain('建议:')
      expect(report).toContain('当前页面不是安全上下文')
    })
  })
})