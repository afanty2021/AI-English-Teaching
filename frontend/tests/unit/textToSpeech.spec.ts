/**
 * 语音合成(TTS)工具类测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { TextToSpeech, TTSEvent, TTSStatus, createTextToSpeech, isTextToSpeechSupported } from '@/utils/textToSpeech'

describe('TextToSpeech', () => {
  let tts: TextToSpeech

  beforeEach(() => {
    // Mock SpeechSynthesisUtterance
    global.SpeechSynthesisUtterance = class {
      text = ''
      lang = ''
      rate = 1
      pitch = 1
      volume = 1
      voice: SpeechSynthesisVoice | null = null
      onstart: (() => void) | null = null
      onend: (() => void) | null = null
      onerror: ((e: any) => void) | null = null
      onpause: (() => void) | null = null
      onresume: (() => void) | null = null
      onmark: (() => void) | null = null
      onboundary: (() => void) | null = null
    } as any

    // Mock SpeechSynthesis
    global.speechSynthesis = {
      speak: vi.fn(),
      cancel: vi.fn(),
      pause: vi.fn(),
      resume: vi.fn(),
      getVoices: vi.fn(() => []),
      speaking: false,
      pending: false,
      paused: false
    } as any

    tts = new TextToSpeech()
  })

  afterEach(() => {
    tts.destroy()
  })

  it('应该正确初始化语音合成', () => {
    expect(tts.getStatus()).toBe(TTSStatus.Idle)
  })

  it('应该在浏览器不支持时返回错误状态', () => {
    // @ts-expect-error - 测试不支持的情况
    delete global.speechSynthesis

    const tts2 = new TextToSpeech()
    expect(tts2.getStatus()).toBe(TTSStatus.Error)
  })

  it('应该正确开始语音合成', async () => {
    let spoken = false
    const mockSpeak = global.speechSynthesis.speak as any

    mockSpeak.mockImplementation((utterance: any) => {
      utterance.onstart?.()
      setTimeout(() => utterance.onend?.(), 10)
    })

    await new Promise<void>(resolve => {
      tts.on({
        onStart: () => {
          expect(tts.getStatus()).toBe(TTSStatus.Speaking)
        },
        onEnd: () => {
          expect(tts.getStatus()).toBe(TTSStatus.Idle)
          spoken = true
          resolve()
        }
      })
      tts.speak('Hello world')
    })

    expect(spoken).toBe(true)
  })

  it('应该正确停止语音合成', () => {
    tts.speak('Hello world')
    tts.stop()

    expect(global.speechSynthesis.cancel).toHaveBeenCalled()
  })

  it('应该支持暂停和恢复', () => {
    const mockPause = global.speechSynthesis.pause as any
    const mockResume = global.speechSynthesis.resume as any

    // 模拟speak触发onstart
    const mockSpeak = global.speechSynthesis.speak as any
    mockSpeak.mockImplementation((utterance: any) => {
      utterance.onstart?.()
    })

    // 不等待speak完成，只测试状态变化
    tts.speak('Hello world').catch(() => {})
    tts.pause()
    expect(tts.getStatus()).toBe(TTSStatus.Paused)
    expect(mockPause).toHaveBeenCalled()

    tts.resume()
    expect(tts.getStatus()).toBe(TTSStatus.Speaking)
    expect(mockResume).toHaveBeenCalled()
  })

  it('应该正确设置语音参数', () => {
    tts.setRate(1.5)
    tts.setPitch(1.2)
    tts.setVolume(0.8)
    tts.setLanguage('en-US')

    tts.speak('Test')

    const utterance = (global.speechSynthesis.speak as any).mock.calls[0][0]
    expect(utterance.rate).toBe(1.5)
    expect(utterance.pitch).toBe(1.2)
    expect(utterance.volume).toBe(0.8)
    expect(utterance.lang).toBe('en-US')
  })

  it('应该限制参数范围', () => {
    tts.setRate(15) // 超出范围
    expect(tts['config'].rate).toBe(10) // 应该被限制在10

    tts.setPitch(3) // 超出范围
    expect(tts['config'].pitch).toBe(2) // 应该被限制在2

    tts.setVolume(1.5) // 超出范围
    expect(tts['config'].volume).toBe(1) // 应该被限制在1

    tts.setVolume(-0.5) // 超出范围
    expect(tts['config'].volume).toBe(0) // 应该被限制在0
  })

  it('应该正确获取可用语音列表', () => {
    const mockVoices: SpeechSynthesisVoice[] = [
      { name: 'Google US English', lang: 'en-US', localService: true, default: true },
      { name: 'Microsoft David', lang: 'en-US', localService: true, default: false }
    ] as any[]

    global.speechSynthesis.getVoices = vi.fn(() => mockVoices)

    const voices = tts.getVoices()
    expect(voices).toHaveLength(2)
    expect(voices[0].name).toBe('Google US English')
  })

  it('应该按语言筛选语音', () => {
    const mockVoices: SpeechSynthesisVoice[] = [
      { name: 'Google US English', lang: 'en-US', localService: true, default: true },
      { name: 'Google 中文', lang: 'zh-CN', localService: true, default: false },
      { name: 'Microsoft David', lang: 'en-GB', localService: true, default: false }
    ] as any[]

    global.speechSynthesis.getVoices = vi.fn(() => mockVoices)

    const enVoices = tts.getVoicesForLanguage('en')
    expect(enVoices).toHaveLength(2) // en-US 和 en-GB

    const zhVoices = tts.getVoicesForLanguage('zh')
    expect(zhVoices).toHaveLength(1) // 只有 zh-CN
  })

  it('应该正确检查状态', () => {
    expect(tts.isSpeaking()).toBe(false)
    expect(tts.isPaused()).toBe(false)

    const mockSpeak = global.speechSynthesis.speak as any
    mockSpeak.mockImplementation((utterance: any) => {
      utterance.onstart?.()
    })

    tts.speak('Test').catch(() => {})
    expect(tts.isSpeaking()).toBe(true)

    tts.pause()
    expect(tts.isPaused()).toBe(true)
  })

  it('应该在未初始化时拒绝speak', async () => {
    const tts2 = new TextToSpeech()
    // @ts-expect-error - 模拟未初始化状态
    tts2.synthesis = null

    await expect(tts2.speak('test')).rejects.toThrow('语音合成未初始化')
  })

  it('应该正确触发错误回调', async () => {
    let errorTriggered = false
    const mockSpeak = global.speechSynthesis.speak as any

    mockSpeak.mockImplementation((utterance: any) => {
      utterance.onerror?.({ error: 'canceled' })
    })

    await new Promise<void>(resolve => {
      tts.on({
        onError: (error: Error) => {
          expect(error.message).toBeTruthy()
          errorTriggered = true
          resolve()
        }
      })
      tts.speak('Test').catch(() => {})
    })

    expect(errorTriggered).toBe(true)
  })

  it('应该正确处理边界事件', () => {
    let boundaryTriggered = false
    const mockSpeak = global.speechSynthesis.speak as any

    mockSpeak.mockImplementation((utterance: any) => {
      utterance.onboundary?.({ name: 'sentence', charLength: 5, charIndex: 0 } as any)
    })

    tts.on({
      onBoundary: (event: SpeechSynthesisEvent) => {
        expect(event.name).toBe('sentence')
        boundaryTriggered = true
      }
    })

    tts.speak('Test')
    expect(boundaryTriggered).toBe(true)
  })

  it('应该支持链式回调注册', () => {
    const callback = vi.fn()

    const result = tts.on({ onStart: callback })
    expect(result).toBe(tts) // 返回this以支持链式调用
  })

  it('应该支持配置语音', () => {
    const mockVoice: SpeechSynthesisVoice = {
      name: 'Custom Voice',
      lang: 'en-US',
      localService: true,
      default: false
    } as any

    tts.setVoice(mockVoice)
    tts.speak('Test')

    const utterance = (global.speechSynthesis.speak as any).mock.calls[0][0]
    expect(utterance.voice).toBe(mockVoice)
  })

  it('销毁时应该清理资源', () => {
    const mockCancel = global.speechSynthesis.cancel as any

    tts.speak('Test')
    tts.destroy()

    expect(mockCancel).toHaveBeenCalled()
    expect(tts.getStatus()).toBe(TTSStatus.Idle)
  })
})

/**
 * 辅助函数测试
 */
describe('textToSpeech 辅助函数', () => {
  beforeEach(() => {
    global.speechSynthesis = {
      speak: vi.fn(),
      cancel: vi.fn(),
      pause: vi.fn(),
      resume: vi.fn(),
      getVoices: vi.fn(() => []),
      speaking: false,
      pending: false,
      paused: false
    } as any
  })

  it('isTextToSpeechSupported 应该正确检测浏览器支持', () => {
    expect(isTextToSpeechSupported()).toBe(true)
  })

  it('createTextToSpeech 应该创建新实例', () => {
    const tts1 = createTextToSpeech()
    const tts2 = createTextToSpeech()

    expect(tts1).not.toBe(tts2) // 应该是不同的实例
  })
})
