/**
 * 语音识别测试共享Mock配置
 * 提供统一的Web Speech API和浏览器API Mock
 */

import { BrowserCompatibility } from '../../src/utils/browserCompatibility'

/**
 * 创建Mock SpeechRecognition构造函数
 */
export function createMockSpeechRecognition(): any {
  return function() {
    this.start = vi.fn()
    this.stop = vi.fn()
    this.abort = vi.fn()
    this.onstart = null
    this.onend = null
    this.onresult = null
    this.onerror = null
    this.onaudiostart = null
    this.onaudioend = null
    this.onspeechstart = null
    this.onspeechend = null
    this.lang = 'zh-CN'
    this.continuous = false
    this.interimResults = true
    this.maxAlternatives = 1
  }
}

/**
 * 创建Mock AudioContext
 */
export function createMockAudioContext() {
  return class MockAudioContext {
    constructor() {}
    createAnalyser() {
      return {
        fftSize: 512,
        frequencyBinCount: 256,
        getByteFrequencyData: vi.fn(),
        disconnect: vi.fn(),
        connect: vi.fn()
      }
    }
    createGain() {
      return {
        connect: vi.fn(),
        disconnect: vi.fn(),
        gainValue: 1,
        gain: { setValueAtTime: vi.fn() }
      }
    }
    createMediaStreamSource() {
      return {
        connect: vi.fn(),
        disconnect: vi.fn()
      }
    }
    createDynamicsCompressor() {
      return {
        threshold: { setValueAtTime: vi.fn() },
        knee: { setValueAtTime: vi.fn() },
        ratio: { setValueAtTime: vi.fn() },
        attack: { setValueAtTime: vi.fn() },
        release: { setValueAtTime: vi.fn() },
        connect: vi.fn(),
        disconnect: vi.fn()
      }
    }
    close() {}
    resume() {}
    suspend() {}
    get currentTime(): number { return 0 }
  }
}

/**
 * Mock navigator对象
 */
export function createMockNavigator(userAgent: string = 'Mozilla/5.0 Chrome/120.0.0.0') {
  return {
    userAgent,
    vendor: 'Google Inc',
    language: 'zh-CN',
    languages: ['zh-CN', 'zh', 'en-US', 'en'],
    onLine: true,
    mediaDevices: {
      getUserMedia: vi.fn().mockResolvedValue(new MediaStream())
    },
    serviceWorker: {
      register: vi.fn().mockResolvedValue({})
    }
  }
}

/**
 * Mock window对象（完整）
 */
export function createMockWindow(mockSpeechRecognition: any) {
  return {
    SpeechRecognition: mockSpeechRecognition,
    webkitSpeechRecognition: mockSpeechRecognition,
    AudioContext: createMockAudioContext(),
    webkitAudioContext: createMockAudioContext(),
    navigator: createMockNavigator(),
    location: {
      href: 'http://localhost:3000',
      protocol: 'http:',
      host: 'localhost:3000'
    },
    performance: {
      now: vi.fn().mockReturnValue(0)
    },
    fetch: vi.fn().mockResolvedValue({
      ok: true,
      blob: async () => new Blob(['test']),
      json: async () => ({ text: 'test' })
    }),
    WebAssembly: {
      instantiate: vi.fn().mockResolvedValue({})
    },
    isSecureContext: true,
    sessionStorage: {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn()
    },
    localStorage: {
      getItem: vi.fn().mockReturnValue(null),
      setItem: vi.fn(),
      removeItem: vi.fn()
    }
  }
}

/**
 * 全局Mock设置器 - 用于vitest.setup.ts
 */
export function setupGlobalMocks() {
  const mockSpeechRecognition = createMockSpeechRecognition()
  const mockWindow = createMockWindow(mockSpeechRecognition)

  // 设置全局mock
  vi.stubGlobal('window', mockWindow)
  vi.stubGlobal('AudioContext', mockWindow.AudioContext)
  vi.stubGlobal('navigator', mockWindow.navigator)
  vi.stubGlobal('performance', mockWindow.performance)
  vi.stubGlobal('fetch', mockWindow.fetch)
  vi.stubGlobal('WebAssembly', mockWindow.WebAssembly)
}

/**
 * 清理全局Mock
 */
export function cleanupGlobalMocks() {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
}

/**
 * 用于WebSpeechEngine测试的专用Mock
 * WebSpeechEngine.isSupported() 需要:
 * - BrowserCompatibility.detect() 返回 engine: 'chrome' 或 'edge'
 * - webSpeechSupported: true
 */
import { BrowserCompatibility } from '../../src/utils/browserCompatibility'

// 创建mock AudioContext实例供测试使用
let mockAudioContextInstance: any = null

export function setupWebSpeechMocks() {
  const mockSpeechRecognition = createMockSpeechRecognition()
  const MockAudioContext = createMockAudioContext()
  mockAudioContextInstance = new MockAudioContext()

  // 使用Object.defineProperty来正确设置全局AudioContext
  Object.defineProperty(globalThis, 'AudioContext', {
    value: MockAudioContext,
    writable: true,
    configurable: true
  })

  Object.defineProperty(globalThis, 'webkitAudioContext', {
    value: MockAudioContext,
    writable: true,
    configurable: true
  })

  vi.stubGlobal('window', {
    SpeechRecognition: mockSpeechRecognition,
    webkitSpeechRecognition: mockSpeechRecognition,
    AudioContext: MockAudioContext,
    webkitAudioContext: MockAudioContext,
    navigator: {
      userAgent: 'Mozilla/5.0 Chrome/120.0.0.0',
      vendor: 'Google Inc',
      language: 'zh-CN',
      languages: ['zh-CN', 'zh', 'en-US', 'en'],
      onLine: true
    },
    location: {
      href: 'http://localhost:3000',
      protocol: 'http:'
    }
  })

  // Mock BrowserCompatibility.detect() 直接返回所需值
  vi.spyOn(BrowserCompatibility, 'detect').mockReturnValue({
    engine: 'chrome' as const,
    version: '120.0.0.0',
    webSpeechSupported: true,
    webAudioSupported: true,
    wasmSupported: false,
    isSecureContext: true,
    userAgent: 'Mozilla/5.0 Chrome/120.0.0.0'
  })
}

/**
 * 获取mock的AudioContext实例
 */
export function getMockAudioContext() {
  if (!mockAudioContextInstance) {
    const MockAudioContext = createMockAudioContext()
    mockAudioContextInstance = new MockAudioContext()
  }
  return mockAudioContextInstance
}

/**
 * 用于CloudSTTEngine测试的专用Mock
 */
export function setupCloudSTTMocks(mockFetchResult?: any) {
  vi.stubGlobal('AudioContext', createMockAudioContext())
  vi.stubGlobal('performance', {
    now: vi.fn().mockReturnValue(0)
  })
  vi.stubGlobal('fetch', mockFetchResult || vi.fn().mockResolvedValue({
    ok: true,
    blob: async () => new Blob(['test']),
    json: async () => ({ text: 'test transcription' })
  }))
}

/**
 * 用于OfflineEngine测试的专用Mock
 */
export function setupOfflineMocks() {
  vi.stubGlobal('window', {
    WebAssembly: {
      instantiate: vi.fn().mockResolvedValue({})
    },
    isSecureContext: true,
    navigator: {
      userAgent: 'Mozilla/5.0 Chrome/120.0.0.0'
    }
  })
}
