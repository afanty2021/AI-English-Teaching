/**
 * 班级学习状况组件测试
 * 测试ClassOverviewView.vue的功能
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ElMessage } from 'element-plus'
import ClassOverviewView from '@/views/teacher/ClassOverviewView.vue'
import teacherReportApi from '@/api/teacherReport'

// Mock dependencies
vi.mock('@/api/teacherReport')
vi.mock('element-plus', () => ({
  ElMessage: {
    error: vi.fn(),
    success: vi.fn(),
    warning: vi.fn()
  }
}))

describe('ClassOverviewView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('应该正确渲染页面标题和筛选器', async () => {
    const wrapper = mount(ClassOverviewView, {
      global: {
        stubs: {
          'el-card': true,
          'el-button': true,
          'el-form': true,
          'el-form-item': true,
          'el-select': true,
          'el-option': true,
          'el-date-picker': true
        }
      }
    })

    expect(wrapper.text()).toContain('班级学习状况')
    expect(wrapper.find('form').exists()).toBe(true)
    expect(wrapper.find('select').exists()).toBe(true)
    expect(wrapper.find('input[type="date"]').exists()).toBe(true)
  })

  it('应该正确显示班级概况统计', async () => {
    const mockSummary = {
      class_id: 'class-1',
      class_name: '高一(1)班',
      total_students: 30,
      active_students: 25,
      overall_stats: {
        avg_completion_rate: 0.82,
        avg_correct_rate: 0.78,
        total_study_hours: 150.5
      },
      ability_distribution: {
        listening: 75,
        reading: 80,
        speaking: 70,
        writing: 65,
        grammar: 72,
        vocabulary: 78
      },
      top_weak_points: [
        { knowledge_point: '时态', affected_students: 15 },
        { knowledge_point: '语序', affected_students: 12 }
      ],
      period_start: '2025-01-01T00:00:00Z',
      period_end: '2025-01-31T23:59:59Z'
    }

    vi.mocked(teacherReportApi.getClassSummary).mockResolvedValue(mockSummary)

    const wrapper = mount(ClassOverviewView, {
      global: {
        stubs: {
          'el-card': true,
          'el-button': true,
          'el-form': true,
          'el-form-item': true,
          'el-select': true,
          'el-option': true,
          'el-date-picker': true,
          'el-statistic': true,
          'el-icon': true,
          'el-progress': true
        }
      }
    })

    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('高一(1)班')
    expect(wrapper.text()).toContain('30')
    expect(wrapper.text()).toContain('25')
    expect(wrapper.text()).toContain('150.5h')
    expect(wrapper.text()).toContain('82%')
  })

  it('应该正确处理空状态', async () => {
    vi.mocked(teacherReportApi.getClassSummary).mockResolvedValue(null)

    const wrapper = mount(ClassOverviewView, {
      global: {
        stubs: {
          'el-card': true,
          'el-button': true,
          'el-form': true,
          'el-form-item': true,
          'el-select': true,
          'el-option': true,
          'el-date-picker': true,
          'el-empty': true
        }
      }
    })

    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('请选择班级查看学习状况')
  })

  it('应该正确处理加载状态', async () => {
    let resolvePromise: (value: any) => void
    const mockPromise = new Promise(resolve => {
      resolvePromise = resolve
    })

    vi.mocked(teacherReportApi.getClassSummary).mockReturnValue(mockPromise)

    const wrapper = mount(ClassOverviewView, {
      global: {
        stubs: {
          'el-card': true,
          'el-button': true,
          'el-form': true,
          'el-form-item': true,
          'el-select': true,
          'el-option': true,
          'el-date-picker': true,
          'el-skeleton': true
        }
      }
    })

    // 完成异步操作
    resolvePromise!({
      class_id: 'class-1',
      class_name: '高一(1)班',
      total_students: 30,
      active_students: 25,
      overall_stats: {
        avg_completion_rate: 0.82,
        avg_correct_rate: 0.78,
        total_study_hours: 150.5
      },
      ability_distribution: {
        listening: 75,
        reading: 80,
        speaking: 70,
        writing: 65,
        grammar: 72,
        vocabulary: 78
      },
      top_weak_points: [],
      period_start: '2025-01-01T00:00:00Z',
      period_end: '2025-01-31T23:59:59Z'
    })

    await wrapper.vm.$nextTick()

    // 检查数据是否正确加载
    expect(wrapper.text()).toContain('高一(1)班')
  })

  it('应该正确处理班级选择变化', async () => {
    const mockSummary = {
      class_id: 'class-2',
      class_name: '高一(2)班',
      total_students: 28,
      active_students: 23,
      overall_stats: {
        avg_completion_rate: 0.79,
        avg_correct_rate: 0.76,
        total_study_hours: 145.2
      },
      ability_distribution: {
        listening: 72,
        reading: 78,
        speaking: 68,
        writing: 63,
        grammar: 70,
        vocabulary: 75
      },
      top_weak_points: [],
      period_start: '2025-01-01T00:00:00Z',
      period_end: '2025-01-31T23:59:59Z'
    }

    vi.mocked(teacherReportApi.getClassSummary).mockResolvedValue(mockSummary)

    const wrapper = mount(ClassOverviewView, {
      global: {
        stubs: {
          'el-card': true,
          'el-button': true,
          'el-form': true,
          'el-form-item': true,
          'el-select': true,
          'el-option': true,
          'el-date-picker': true,
          'el-statistic': true,
          'el-icon': true
        }
      }
    })

    await wrapper.vm.$nextTick()

    // 改变班级选择
    await wrapper.find('select').setValue('class-2')

    expect(teacherReportApi.getClassSummary).toHaveBeenCalledWith({
      classId: 'class-2',
      periodStart: undefined,
      periodEnd: undefined
    })
  })

  it('应该正确处理日期范围变化', async () => {
    const mockSummary = {
      class_id: 'class-1',
      class_name: '高一(1)班',
      total_students: 30,
      active_students: 20,
      overall_stats: {
        avg_completion_rate: 0.85,
        avg_correct_rate: 0.80,
        total_study_hours: 100.5
      },
      ability_distribution: {
        listening: 75,
        reading: 80,
        speaking: 70,
        writing: 65,
        grammar: 72,
        vocabulary: 78
      },
      top_weak_points: [],
      period_start: '2025-01-15T00:00:00Z',
      period_end: '2025-01-31T23:59:59Z'
    }

    vi.mocked(teacherReportApi.getClassSummary).mockResolvedValue(mockSummary)

    const wrapper = mount(ClassOverviewView, {
      global: {
        stubs: {
          'el-card': true,
          'el-button': true,
          'el-form': true,
          'el-form-item': true,
          'el-select': true,
          'el-option': true,
          'el-date-picker': true,
          'el-statistic': true,
          'el-icon': true
        }
      }
    })

    await wrapper.vm.$nextTick()

    // 触发查询按钮
    await wrapper.find('button[type="submit"]').trigger('click')

    expect(teacherReportApi.getClassSummary).toHaveBeenCalled()
  })

  it('应该正确处理重置功能', async () => {
    const mockSummary = {
      class_id: 'class-1',
      class_name: '高一(1)班',
      total_students: 30,
      active_students: 25,
      overall_stats: {
        avg_completion_rate: 0.82,
        avg_correct_rate: 0.78,
        total_study_hours: 150.5
      },
      ability_distribution: {
        listening: 75,
        reading: 80,
        speaking: 70,
        writing: 65,
        grammar: 72,
        vocabulary: 78
      },
      top_weak_points: [],
      period_start: '2025-01-01T00:00:00Z',
      period_end: '2025-01-31T23:59:59Z'
    }

    vi.mocked(teacherReportApi.getClassSummary).mockResolvedValue(mockSummary)

    const wrapper = mount(ClassOverviewView, {
      global: {
        stubs: {
          'el-card': true,
          'el-button': true,
          'el-form': true,
          'el-form-item': true,
          'el-select': true,
          'el-option': true,
          'el-date-picker': true,
          'el-statistic': true,
          'el-icon': true
        }
      }
    })

    await wrapper.vm.$nextTick()

    // 点击重置按钮
    await wrapper.findAll('button').at(1)?.trigger('click')

    expect(teacherReportApi.getClassSummary).toHaveBeenCalledWith({
      classId: 'class-1',
      periodStart: undefined,
      periodEnd: undefined
    })
  })

  it('应该正确显示薄弱知识点列表', async () => {
    const mockSummary = {
      class_id: 'class-1',
      class_name: '高一(1)班',
      total_students: 30,
      active_students: 25,
      overall_stats: {
        avg_completion_rate: 0.82,
        avg_correct_rate: 0.78,
        total_study_hours: 150.5
      },
      ability_distribution: {
        listening: 75,
        reading: 80,
        speaking: 70,
        writing: 65,
        grammar: 72,
        vocabulary: 78
      },
      top_weak_points: [
        { knowledge_point: '时态', affected_students: 15 },
        { knowledge_point: '语序', affected_students: 12 },
        { knowledge_point: '被动语态', affected_students: 8 }
      ],
      period_start: '2025-01-01T00:00:00Z',
      period_end: '2025-01-31T23:59:59Z'
    }

    vi.mocked(teacherReportApi.getClassSummary).mockResolvedValue(mockSummary)

    const wrapper = mount(ClassOverviewView, {
      global: {
        stubs: {
          'el-card': true,
          'el-button': true,
          'el-form': true,
          'el-form-item': true,
          'el-select': true,
          'el-option': true,
          'el-date-picker': true,
          'el-statistic': true,
          'el-icon': true,
          'el-progress': true
        }
      }
    })

    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('时态')
    expect(wrapper.text()).toContain('语序')
    expect(wrapper.text()).toContain('被动语态')
    expect(wrapper.text()).toContain('影响')
  })

  it('应该正确处理API错误', async () => {
    vi.mocked(teacherReportApi.getClassSummary).mockRejectedValue(new Error('Network error'))

    const wrapper = mount(ClassOverviewView, {
      global: {
        stubs: {
          'el-card': true,
          'el-button': true,
          'el-form': true,
          'el-form-item': true,
          'el-select': true,
          'el-option': true,
          'el-date-picker': true
        }
      }
    })

    await wrapper.vm.$nextTick()

    expect(ElMessage.error).toHaveBeenCalledWith('加载班级状况失败')
  })

  it('应该正确处理未选择班级的警告', async () => {
    const wrapper = mount(ClassOverviewView, {
      global: {
        stubs: {
          'el-card': true,
          'el-button': true,
          'el-form': true,
          'el-form-item': true,
          'el-select': true,
          'el-option': true,
          'el-date-picker': true
        }
      }
    })

    await wrapper.vm.$nextTick()

    // 清空班级选择
    await wrapper.find('select').setValue('')

    // 点击查询按钮
    await wrapper.find('button[type="submit"]').trigger('click')

    expect(ElMessage.warning).toHaveBeenCalledWith('请选择班级')
  })

  it('应该正确显示默认日期范围', async () => {
    const mockSummary = {
      class_id: 'class-1',
      class_name: '高一(1)班',
      total_students: 30,
      active_students: 25,
      overall_stats: {
        avg_completion_rate: 0.82,
        avg_correct_rate: 0.78,
        total_study_hours: 150.5
      },
      ability_distribution: {
        listening: 75,
        reading: 80,
        speaking: 70,
        writing: 65,
        grammar: 72,
        vocabulary: 78
      },
      top_weak_points: [],
      period_start: '2025-01-01T00:00:00Z',
      period_end: '2025-01-31T23:59:59Z'
    }

    vi.mocked(teacherReportApi.getClassSummary).mockResolvedValue(mockSummary)

    const wrapper = mount(ClassOverviewView, {
      global: {
        stubs: {
          'el-card': true,
          'el-button': true,
          'el-form': true,
          'el-form-item': true,
          'el-select': true,
          'el-option': true,
          'el-date-picker': true,
          'el-statistic': true,
          'el-icon': true
        }
      }
    })

    await wrapper.vm.$nextTick()

    // 检查是否设置了默认班级
    const select = wrapper.find('select')
    expect(select.element.value).toBe('class-1')
  })
})
