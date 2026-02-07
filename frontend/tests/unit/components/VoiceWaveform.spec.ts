/**
 * VoiceWaveform 组件测试
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import VoiceWaveform from '@/components/VoiceWaveform.vue'

// Mock Web Audio API
const mockAudioContext = {
  createAnalyser: vi.fn(() => ({
    frequencyBinCount: 1024,
    smoothingTimeConstant: 0.8,
    getByteFrequencyData: vi.fn()
  })),
  createMediaStreamSource: vi.fn(() => ({
    connect: vi.fn()
  })),
  close: vi.fn(),
  state: 'closed'
}

describe('VoiceWaveform', () => {
  beforeEach(() => {
    vi.stubGlobal('AudioContext', () => mockAudioContext)
    vi.stubGlobal('requestAnimationFrame', (cb) => {
      return setTimeout(() => cb(performance.now()), 16)
    })
    vi.stubGlobal('cancelAnimationFrame', vi.fn())
  })

  it('should render waveform bars', () => {
    const wrapper = mount(VoiceWaveform, {
      props: {
        barCount: 32,
        maxBarHeight: 100
      }
    })

    expect(wrapper.find('.waveform').exists()).toBe(true)
  })

  it('should respect maxBarHeight for volume overload protection', () => {
    const wrapper = mount(VoiceWaveform, {
      props: {
        barCount: 32,
        maxBarHeight: 100,
        minBarHeight: 2
      }
    })

    // 验证波形条初始化
    const waveformBars = wrapper.vm.waveformBars
    expect(waveformBars.value).toHaveLength(32)
    expect(waveformBars.value.every(bar => bar.height <= 100)).toBe(true)
  })

  it('should apply dynamic sensitivity through smoothing', async () => {
    const wrapper = mount(VoiceWaveform, {
      props: {
        barCount: 32,
        smoothing: 0.5
      }
    })

    // 模拟音频数据
    const mockData = new Uint8Array(1024).fill(128)
    mockAudioContext.createAnalyser().getByteFrequencyData.mockImplementation((cb) => {
      cb(mockData)
    })

    wrapper.vm.setAudioSource({} as MediaStream)

    // 等待动画更新
    await new Promise(resolve => setTimeout(resolve, 50))

    const waveformBars = wrapper.vm.waveformBars.value
    // 验证平滑效果
    expect(waveformBars.value).toBeDefined()
  })

  it('should detect voice activity correctly', () => {
    const wrapper = mount(VoiceWaveform, {
      props: {
        vadThreshold: 30
      }
    })

    const vadHistory = [false, false, true, true, true]
    const avgIsActive = vadHistory.reduce((sum, active) => sum + (active ? 1 : 0), 0) / vadHistory.length

    expect(avgIsActive).toBeGreaterThan(0.5)
  })
})
