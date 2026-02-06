/**
 * 对话评分卡片组件单元测试
 * TDD方式实现
 */
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ConversationScoreCard from '@/components/ConversationScoreCard.vue'
import type { ConversationScores } from '@/types/conversation'

// Mock Element Plus icons
vi.mock('@element-plus/icons-vue', () => ({
  TrendCharts: {
    template: '<div class="mock-icon-trend"></div>',
    name: 'TrendCharts'
  },
  Right: {
    template: '<div class="mock-icon-right"></div>',
    name: 'Right'
  }
}))

describe('ConversationScoreCard', () => {
  const mockScores: ConversationScores = {
    overall: 85,
    overall_score: 85,
    fluency_score: 80,
    grammar_score: 75,
    vocabulary_score: 88,
    feedback: '整体表现良好，继续保持！',
    suggestions: [
      '注意时态一致性',
      '可以尝试更多样化的词汇'
    ]
  }

  const defaultStubs = {
    'el-card': {
      template: '<div class="score-card"><slot name="header"></slot><slot></slot></div>'
    },
    'el-empty': {
      template: '<div class="empty-state"><slot></slot></div>',
      props: ['description']
    },
    'el-divider': {
      template: '<div class="el-divider"></div>'
    },
    'el-tag': {
      template: '<div class="el-tag"><slot></slot></div>',
      props: ['type', 'size']
    },
    'el-progress': {
      template: '<div class="el-progress"></div>',
      props: ['percentage', 'color', 'showText']
    },
    'el-icon': {
      template: '<div class="el-icon"><slot></slot></div>'
    }
  }

  it('应该正确渲染评分卡片', () => {
    const wrapper = mount(ConversationScoreCard, {
      props: { scores: mockScores },
      global: {
        stubs: defaultStubs
      }
    })

    expect(wrapper.find('.score-card').exists()).toBe(true)
    expect(wrapper.text()).toContain('85')
  })

  it('应该显示反馈信息', () => {
    const wrapper = mount(ConversationScoreCard, {
      props: { scores: mockScores },
      global: {
        stubs: defaultStubs
      }
    })

    expect(wrapper.text()).toContain('整体表现良好')
  })

  it('应该显示建议列表', () => {
    const wrapper = mount(ConversationScoreCard, {
      props: { scores: mockScores },
      global: {
        stubs: defaultStubs
      }
    })

    expect(wrapper.findAll('.suggestion-item')).toHaveLength(2)
  })

  it('应该在无评分时显示空状态', () => {
    const wrapper = mount(ConversationScoreCard, {
      props: { scores: null },
      global: {
        stubs: defaultStubs
      }
    })

    expect(wrapper.find('.empty-state').exists()).toBe(true)
  })

  it('应该正确计算评分等级类名', () => {
    const wrapper = mount(ConversationScoreCard, {
      props: { scores: mockScores },
      global: {
        stubs: defaultStubs
      }
    })

    // 85分属于'good'等级
    expect(wrapper.find('.score-circle').classes()).toContain('good')
  })

  it('应该显示总分圆圈', () => {
    const wrapper = mount(ConversationScoreCard, {
      props: { scores: mockScores },
      global: {
        stubs: defaultStubs
      }
    })

    expect(wrapper.find('.score-circle').exists()).toBe(true)
    expect(wrapper.find('.score-value').exists()).toBe(true)
    expect(wrapper.find('.score-value').text()).toBe('85')
  })

  it('应该显示分项评分进度条', () => {
    const wrapper = mount(ConversationScoreCard, {
      props: { scores: mockScores },
      global: {
        stubs: defaultStubs
      }
    })

    // 应该有三个维度评分
    expect(wrapper.findAll('.score-item').length).toBeGreaterThanOrEqual(3)
  })

  it('应该正确处理优秀分数(>=90)', () => {
    const excellentScores: ConversationScores = {
      ...mockScores,
      overall: 95,
      overall_score: 95,
      fluency_score: 92,
      grammar_score: 90,
      vocabulary_score: 95
    }

    const wrapper = mount(ConversationScoreCard, {
      props: { scores: excellentScores },
      global: {
        stubs: defaultStubs
      }
    })

    expect(wrapper.find('.score-circle').classes()).toContain('excellent')
    expect(wrapper.text()).toContain('优秀')
  })

  it('应该正确处理需改进分数(<60)', () => {
    const poorScores: ConversationScores = {
      ...mockScores,
      overall: 45,
      overall_score: 45,
      fluency_score: 50,
      grammar_score: 40,
      vocabulary_score: 45
    }

    const wrapper = mount(ConversationScoreCard, {
      props: { scores: poorScores },
      global: {
        stubs: defaultStubs
      }
    })

    expect(wrapper.find('.score-circle').classes()).toContain('needs-improvement')
    expect(wrapper.text()).toContain('需改进')
  })

  it('应该正确处理空建议数组', () => {
    const noSuggestionsScores: ConversationScores = {
      ...mockScores,
      suggestions: []
    }

    const wrapper = mount(ConversationScoreCard, {
      props: { scores: noSuggestionsScores },
      global: {
        stubs: defaultStubs
      }
    })

    // 不应该显示建议列表
    expect(wrapper.findAll('.suggestion-item')).toHaveLength(0)
  })

  it('应该正确处理无反馈文本', () => {
    const noFeedbackScores: ConversationScores = {
      ...mockScores,
      feedback: undefined
    }

    const wrapper = mount(ConversationScoreCard, {
      props: { scores: noFeedbackScores },
      global: {
        stubs: defaultStubs
      }
    })

    // 不应该显示反馈部分
    expect(wrapper.find('.feedback-section').exists()).toBe(false)
  })
})
