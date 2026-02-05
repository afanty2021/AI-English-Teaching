/**
 * 学生报告列表组件测试
 * 测试StudentReportsView.vue的功能
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'
import StudentReportsView from '@/views/teacher/StudentReportsView.vue'
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

// Mock router
const mockRouter = {
  push: vi.fn()
}

vi.mock('vue-router', () => ({
  useRouter: () => mockRouter,
  useRoute: () => ({
    params: {}
  })
}))

describe('StudentReportsView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('应该正确渲染页面标题和筛选器', async () => {
    const wrapper = mount(StudentReportsView, {
      global: {
        stubs: {
          'el-card': true,
          'el-button': true,
          'el-form': true,
          'el-form-item': true,
          'el-select': true,
          'el-option': true
        }
      }
    })

    expect(wrapper.text()).toContain('学生报告')
    expect(wrapper.find('form').exists()).toBe(true)
    expect(wrapper.find('select').exists()).toBe(true)
  })

  it('应该正确显示学生卡片列表', async () => {
    const mockStudents = [
      {
        student_id: '1',
        student_number: 'S2024001',
        student_name: '张三',
        email: 'zhangsan@example.com',
        class_id: 'class-1',
        class_name: '高一(1)班',
        grade: '高一',
        has_reports: true,
        latest_report: {
          report_id: 'report-1',
          created_at: '2025-01-15T10:00:00Z',
          report_type: 'weekly'
        }
      },
      {
        student_id: '2',
        student_number: 'S2024002',
        student_name: '李四',
        email: 'lisi@example.com',
        class_id: 'class-1',
        class_name: '高一(1)班',
        grade: '高一',
        has_reports: false,
        latest_report: null
      }
    ]

    vi.mocked(teacherReportApi.getStudents).mockResolvedValue({
      total: 2,
      limit: 20,
      offset: 0,
      students: mockStudents
    })

    const wrapper = mount(StudentReportsView, {
      global: {
        stubs: {
          'el-card': true,
          'el-button': true,
          'el-form': true,
          'el-form-item': true,
          'el-select': true,
          'el-option': true,
          'el-avatar': true,
          'el-tag': true,
          'el-empty': true,
          'el-icon': true
        }
      }
    })

    // 等待异步加载完成
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('张三')
    expect(wrapper.text()).toContain('李四')
    expect(wrapper.text()).toContain('有报告')
    expect(wrapper.text()).toContain('无报告')
  })

  it('应该正确处理空状态', async () => {
    vi.mocked(teacherReportApi.getStudents).mockResolvedValue({
      total: 0,
      limit: 20,
      offset: 0,
      students: []
    })

    const wrapper = mount(StudentReportsView, {
      global: {
        stubs: {
          'el-card': true,
          'el-button': true,
          'el-form': true,
          'el-form-item': true,
          'el-select': true,
          'el-option': true,
          'el-empty': true
        }
      }
    })

    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('暂无学生数据')
  })

  it('应该正确处理加载状态', async () => {
    let resolvePromise: (value: any) => void
    const mockPromise = new Promise(resolve => {
      resolvePromise = resolve
    })

    vi.mocked(teacherReportApi.getStudents).mockReturnValue(mockPromise)

    const wrapper = mount(StudentReportsView, {
      global: {
        stubs: {
          'el-card': true,
          'el-button': true,
          'el-form': true,
          'el-form-item': true,
          'el-select': true,
          'el-option': true,
          'el-avatar': true,
          'el-tag': true
        }
      }
    })

    // 检查加载状态
    const card = wrapper.findComponent({ name: 'ElCard' })
    expect(card.props('loading')).toBe(true)

    // 完成异步操作
    resolvePromise!({
      total: 0,
      limit: 20,
      offset: 0,
      students: []
    })

    await wrapper.vm.$nextTick()

    expect(card.props('loading')).toBe(false)
  })

  it('应该正确处理筛选功能', async () => {
    vi.mocked(teacherReportApi.getStudents).mockResolvedValue({
      total: 1,
      limit: 20,
      offset: 0,
      students: [{
        student_id: '1',
        student_number: 'S2024001',
        student_name: '张三',
        email: 'zhangsan@example.com',
        class_id: 'class-1',
        class_name: '高一(1)班',
        grade: '高一',
        has_reports: true,
        latest_report: {
          report_id: 'report-1',
          created_at: '2025-01-15T10:00:00Z',
          report_type: 'weekly'
        }
      }]
    })

    const wrapper = mount(StudentReportsView, {
      global: {
        stubs: {
          'el-card': true,
          'el-button': true,
          'el-form': true,
          'el-form-item': true,
          'el-select': true,
          'el-option': true,
          'el-avatar': true,
          'el-tag': true
        }
      }
    })

    await wrapper.vm.$nextTick()

    // 触发筛选
    await wrapper.find('select').setValue('class-1')
    await wrapper.find('button[type="submit"]').trigger('click')

    expect(teacherReportApi.getStudents).toHaveBeenCalledWith({
      classId: 'class-1',
      page: 1,
      limit: 20
    })
  })

  it('应该正确处理重置筛选', async () => {
    vi.mocked(teacherReportApi.getStudents).mockResolvedValue({
      total: 2,
      limit: 20,
      offset: 0,
      students: []
    })

    const wrapper = mount(StudentReportsView, {
      global: {
        stubs: {
          'el-card': true,
          'el-button': true,
          'el-form': true,
          'el-form-item': true,
          'el-select': true,
          'el-option': true
        }
      }
    })

    await wrapper.vm.$nextTick()

    // 点击重置按钮
    await wrapper.findAll('button').at(1)?.trigger('click')

    expect(teacherReportApi.getStudents).toHaveBeenCalledWith({
      classId: undefined,
      page: 1,
      limit: 20
    })
  })

  it('应该正确处理学生卡片点击', async () => {
    const mockStudent = {
      student_id: '1',
      student_number: 'S2024001',
      student_name: '张三',
      email: 'zhangsan@example.com',
      class_id: 'class-1',
      class_name: '高一(1)班',
      grade: '高一',
      has_reports: true,
      latest_report: {
        report_id: 'report-1',
        created_at: '2025-01-15T10:00:00Z',
        report_type: 'weekly'
      }
    }

    vi.mocked(teacherReportApi.getStudents).mockResolvedValue({
      total: 1,
      limit: 20,
      offset: 0,
      students: [mockStudent]
    })

    const wrapper = mount(StudentReportsView, {
      global: {
        stubs: {
          'el-card': true,
          'el-button': true,
          'el-form': true,
          'el-form-item': true,
          'el-select': true,
          'el-option': true,
          'el-avatar': true,
          'el-tag': true
        }
      }
    })

    await wrapper.vm.$nextTick()

    // 点击学生卡片
    await wrapper.find('.student-card').trigger('click')

    expect(mockRouter.push).toHaveBeenCalledWith('/teacher/reports/students/1')
  })

  it('应该正确处理生成报告功能', async () => {
    vi.mocked(teacherReportApi.getStudents).mockResolvedValue({
      total: 1,
      limit: 20,
      offset: 0,
      students: [{
        student_id: '1',
        student_number: 'S2024001',
        student_name: '张三',
        email: 'zhangsan@example.com',
        class_id: 'class-1',
        class_name: '高一(1)班',
        grade: '高一',
        has_reports: false,
        latest_report: null
      }]
    })

    vi.mocked(teacherReportApi.generateStudentReport).mockResolvedValue({})

    const wrapper = mount(StudentReportsView, {
      global: {
        stubs: {
          'el-card': true,
          'el-button': true,
          'el-form': true,
          'el-form-item': true,
          'el-select': true,
          'el-option': true,
          'el-avatar': true,
          'el-tag': true,
          'el-empty': true
        }
      }
    })

    await wrapper.vm.$nextTick()

    // 点击生成报告按钮
    await wrapper.findAll('button').at(1)?.trigger('click')

    expect(teacherReportApi.generateStudentReport).toHaveBeenCalledWith('1', {
      report_type: 'custom'
    })
    expect(ElMessage.success).toHaveBeenCalledWith('报告生成成功')
  })

  it('应该正确处理API错误', async () => {
    vi.mocked(teacherReportApi.getStudents).mockRejectedValue(new Error('Network error'))

    const wrapper = mount(StudentReportsView, {
      global: {
        stubs: {
          'el-card': true,
          'el-button': true,
          'el-form': true,
          'el-form-item': true,
          'el-select': true,
          'el-option': true
        }
      }
    })

    await wrapper.vm.$nextTick()

    expect(ElMessage.error).toHaveBeenCalledWith('加载学生列表失败')
  })

  it('应该正确显示分页', async () => {
    const mockStudents = Array.from({ length: 25 }, (_, i) => ({
      student_id: `${i + 1}`,
      student_number: `S202400${i + 1}`,
      student_name: `学生${i + 1}`,
      email: `student${i + 1}@example.com`,
      class_id: 'class-1',
      class_name: '高一(1)班',
      grade: '高一',
      has_reports: true,
      latest_report: {
        report_id: `report-${i + 1}`,
        created_at: '2025-01-15T10:00:00Z',
        report_type: 'weekly'
      }
    }))

    vi.mocked(teacherReportApi.getStudents).mockResolvedValue({
      total: 25,
      limit: 20,
      offset: 0,
      students: mockStudents.slice(0, 20)
    })

    const wrapper = mount(StudentReportsView, {
      global: {
        stubs: {
          'el-card': true,
          'el-button': true,
          'el-form': true,
          'el-form-item': true,
          'el-select': true,
          'el-option': true,
          'el-avatar': true,
          'el-tag': true,
          'el-pagination': true
        }
      }
    })

    await wrapper.vm.$nextTick()

    // 检查是否显示分页组件
    expect(wrapper.findComponent({ name: 'ElPagination' }).exists()).toBe(true)
  })

  it('应该正确处理分页切换', async () => {
    vi.mocked(teacherReportApi.getStudents).mockResolvedValue({
      total: 25,
      limit: 20,
      offset: 20,
      students: []
    })

    const wrapper = mount(StudentReportsView, {
      global: {
        stubs: {
          'el-card': true,
          'el-button': true,
          'el-form': true,
          'el-form-item': true,
          'el-select': true,
          'el-option': true,
          'el-pagination': {
            props: ['current-page', 'page-size', 'total'],
            emits: ['current-change']
          }
        }
      }
    })

    await wrapper.vm.$nextTick()

    // 触发分页切换
    await wrapper.findComponent({ name: 'ElPagination' }).emit('current-change', 2)

    expect(teacherReportApi.getStudents).toHaveBeenCalledWith({
      classId: undefined,
      page: 2,
      limit: 20
    })
  })
})
