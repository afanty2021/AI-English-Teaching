// tests/unit/components/VoiceControlButton.spec.ts
/**
 * 语音控制按钮组件单元测试
 * TDD方式实现
 */
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import VoiceControlButton from '@/components/VoiceControlButton.vue'

// Mock Element Plus icons
vi.mock('@element-plus/icons-vue', () => ({
  Microphone: {
    template: '<div class="el-icon-microphone"></div>',
    name: 'Microphone'
  },
  VideoPause: {
    template: '<div class="el-icon-video-pause"></div>',
    name: 'VideoPause'
  },
  Loading: {
    template: '<div class="el-icon-loading"></div>',
    name: 'Loading'
  },
  MuteNotification: {
    template: '<div class="el-icon-mute-notification"></div>',
    name: 'MuteNotification'
  },
  Bell: {
    template: '<div class="el-icon-bell"></div>',
    name: 'Bell'
  }
}))

const defaultStubs = {
  'el-button': {
    template: '<button class="voice-button" :class="[type, state, { disabled, circle }]" :disabled="disabled" :type="buttonType" :circle="circle" :size="size" @click="$emit(\'click\')"><slot></slot></button>',
    props: ['type', 'disabled', 'circle', 'size', 'state', 'buttonType']
  },
  'el-icon': {
    template: '<div class="el-icon" :size="iconSize"><slot></slot></div>',
    props: ['size']
  }
}

describe('VoiceControlButton', () => {
  it('应该正确渲染录音按钮', () => {
    const wrapper = mount(VoiceControlButton, {
      props: {
        type: 'record',
        state: 'idle'
      },
      global: {
        stubs: defaultStubs
      }
    })

    expect(wrapper.find('.voice-button').exists()).toBe(true)
    expect(wrapper.find('.el-icon-microphone').exists()).toBe(true)
  })

  it('应该在录音状态时显示停止图标', () => {
    const wrapper = mount(VoiceControlButton, {
      props: {
        type: 'record',
        state: 'listening'
      },
      global: {
        stubs: defaultStubs
      }
    })

    expect(wrapper.find('.el-icon-video-pause').exists()).toBe(true)
  })

  it('应该正确触发点击事件', async () => {
    const wrapper = mount(VoiceControlButton, {
      props: {
        type: 'record',
        state: 'idle'
      },
      global: {
        stubs: defaultStubs
      }
    })

    await wrapper.find('.voice-button').trigger('click')

    expect(wrapper.emitted('click')).toBeTruthy()
  })

  it('禁用状态时不应触发点击', async () => {
    const wrapper = mount(VoiceControlButton, {
      props: {
        type: 'record',
        state: 'idle',
        disabled: true
      },
      global: {
        stubs: defaultStubs
      }
    })

    await wrapper.find('.voice-button').trigger('click')

    expect(wrapper.emitted('click')).toBeFalsy()
  })

  it('应该在处理状态时显示加载图标', () => {
    const wrapper = mount(VoiceControlButton, {
      props: {
        type: 'record',
        state: 'processing'
      },
      global: {
        stubs: defaultStubs
      }
    })

    expect(wrapper.find('.el-icon-loading').exists()).toBe(true)
  })

  it('应该在播放状态时显示停止图标', () => {
    const wrapper = mount(VoiceControlButton, {
      props: {
        type: 'play',
        state: 'playing'
      },
      global: {
        stubs: defaultStubs
      }
    })

    expect(wrapper.find('.el-icon-video-pause').exists()).toBe(true)
  })

  it('应该在暂停状态时显示播放图标', () => {
    const wrapper = mount(VoiceControlButton, {
      props: {
        type: 'play',
        state: 'paused'
      },
      global: {
        stubs: defaultStubs
      }
    })

    expect(wrapper.find('.el-icon-bell').exists()).toBe(true)
  })

  it('应该在录音时显示波纹动画', () => {
    const wrapper = mount(VoiceControlButton, {
      props: {
        type: 'record',
        state: 'listening'
      },
      global: {
        stubs: defaultStubs
      }
    })

    expect(wrapper.find('.ripple').exists()).toBe(true)
  })

  it('应该在非录音状态时不显示波纹动画', () => {
    const wrapper = mount(VoiceControlButton, {
      props: {
        type: 'record',
        state: 'idle'
      },
      global: {
        stubs: defaultStubs
      }
    })

    expect(wrapper.find('.ripple').exists()).toBe(false)
  })

  it('应该在非圆形模式时正确渲染', () => {
    const wrapper = mount(VoiceControlButton, {
      props: {
        type: 'record',
        state: 'idle',
        circle: false
      },
      global: {
        stubs: defaultStubs
      }
    })

    expect(wrapper.find('.voice-button').exists()).toBe(true)
    expect(wrapper.find('.voice-button').classes()).not.toContain('circle')
  })

  it('应该支持不同尺寸', () => {
    const sizes = ['large', 'default', 'small'] as const

    sizes.forEach(size => {
      const wrapper = mount(VoiceControlButton, {
        props: {
          type: 'record',
          state: 'idle',
          size
        },
        global: {
          stubs: defaultStubs
        }
      })

      expect(wrapper.find('.voice-button').exists()).toBe(true)
    })
  })
})
