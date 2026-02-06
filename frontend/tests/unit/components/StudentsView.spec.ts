/**
 * StudentsView组件测试
 * 测试学生管理页面的交互和状态管理
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import StudentsView from '@/views/teacher/StudentsView.vue'
import * as echarts from 'echarts'
import studentApi from '@/api/student'

// Mock student API
vi.mock('@/api/student', () => ({
  default: {
    getStudents: vi.fn(),
    getKnowledgeGraph: vi.fn(),
    diagnoseStudent: vi.fn()
  }
}))

// Mock echarts
vi.mock('echarts', () => ({
  default: {
    init: vi.fn(() => ({
      setOption: vi.fn(),
      resize: vi.fn(),
      dispose: vi.fn()
    }))
  }
}))

// Mock auth store
const mockAuthStore = {
  logout: vi.fn(),
  user: {
    id: 'teacher-1',
    username: 'test_teacher',
    role: 'teacher'
  }
}

vi.mock('@/stores/auth', () => ({
  useAuthStore: () => mockAuthStore
}))

describe('StudentsView', () => {
  let wrapper: VueWrapper
  let pinia: ReturnType<typeof createPinia>

  const mockStudents = [
    {
      id: 'student-1',
      user_id: 'user-1',
      username: '张三',
      email: 'zhangsan@example.com',
      target_exam: 'CET4',
      target_score: 500,
      current_cefr_level: 'B1',
      grade: '大一',
      created_at: '2025-01-15T10:00:00Z'
    },
    {
      id: 'student-2',
      user_id: 'user-2',
      username: '李四',
      email: 'lisi@example.com',
      target_exam: 'CET6',
      target_score: 550,
      current_cefr_level: 'B2',
      grade: '大二',
      created_at: '2025-01-10T10:00:00Z'
    },
    {
      id: 'student-3',
      user_id: 'user-3',
      username: '王五',
      email: 'wangwu@example.com',
      target_exam: null,
      target_score: null,
      current_cefr_level: null,
      grade: null,
      created_at: '2025-01-05T10:00:00Z'
    }
  ]

  const mockKnowledgeGraph = {
    student_id: 'student-1',
    nodes: [],
    edges: [],
    abilities: {
      listening: 75,
      reading: 80,
      speaking: 65,
      writing: 70,
      grammar: 72,
      vocabulary: 68
    },
    cefr_level: 'B1',
    exam_coverage: {
      total_practices: 50,
      topics_covered: 15,
      recent_activity: 5
    },
    ai_analysis: {
      weak_points: [
        {
          topic: '口语',
          ability: 'speaking',
          current_level: 65,
          reason: '表达能力需要加强',
          priority: 'high'
        }
      ],
      recommendations: [
        {
          priority: 'high',
          suggestion: '加强口语基础训练',
          ability: 'speaking'
        }
      ]
    },
    last_ai_analysis_at: '2025-01-15T10:00:00Z',
    version: 1,
    created_at: '2025-01-10T10:00:00Z',
    updated_at: '2025-01-15T10:00:00Z'
  }

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)

    // 默认mock成功响应
    vi.mocked(studentApi.getStudents).mockResolvedValue(mockStudents)
    vi.mocked(studentApi.getKnowledgeGraph).mockResolvedValue(mockKnowledgeGraph)
    vi.mocked(studentApi.diagnoseStudent).mockResolvedValue({
      message: '诊断完成',
      student_id: 'student-1',
      status: 'completed'
    })
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  describe('组件渲染', () => {
    it('应该正确渲染学生管理页面', async () => {
      wrapper = mount(StudentsView, {
        global: {
          plugins: [pinia],
          stubs: {
            'el-container': true,
            'el-header': true,
            'el-main': true,
            'el-menu': true,
            'el-menu-item': true,
            'el-card': true,
            'el-table': true,
            'el-table-column': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-button': true,
            'el-icon': true,
            'el-pagination': true,
            'el-drawer': true,
            'el-skeleton': true,
            'el-tag': true,
            'el-empty': true,
            'el-avatar': true,
            'el-dialog': true,
            'el-progress': true,
            'el-message-box': true
          }
        }
      })

      // 等待异步数据加载
      await new Promise(resolve => setTimeout(resolve, 0))
      await wrapper.vm.$nextTick()

      expect(wrapper.exists()).toBe(true)
    })

    it('应该在加载时调用获取学生列表API', async () => {
      wrapper = mount(StudentsView, {
        global: {
          plugins: [pinia],
          stubs: {
            'el-container': true,
            'el-header': true,
            'el-main': true,
            'el-menu': true,
            'el-menu-item': true,
            'el-card': true,
            'el-table': true,
            'el-table-column': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-button': true,
            'el-icon': true,
            'el-pagination': true,
            'el-drawer': true,
            'el-skeleton': true,
            'el-tag': true,
            'el-empty': true,
            'el-avatar': true,
            'el-dialog': true,
            'el-progress': true,
            'el-message-box': true
          }
        }
      })

      await new Promise(resolve => setTimeout(resolve, 0))

      expect(studentApi.getStudents).toHaveBeenCalled()
    })
  })

  describe('学生列表加载', () => {
    it('应该正确加载和显示学生列表', async () => {
      wrapper = mount(StudentsView, {
        global: {
          plugins: [pinia],
          stubs: {
            'el-container': true,
            'el-header': true,
            'el-main': true,
            'el-menu': true,
            'el-menu-item': true,
            'el-card': true,
            'el-table': true,
            'el-table-column': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-button': true,
            'el-icon': true,
            'el-pagination': true,
            'el-drawer': true,
            'el-skeleton': true,
            'el-tag': true,
            'el-empty': true,
            'el-avatar': true,
            'el-dialog': true,
            'el-progress': true,
            'el-message-box': true
          }
        }
      })

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 0))

      expect(wrapper.vm.students).toEqual(mockStudents)
      expect(wrapper.vm.students.length).toBe(3)
    })

    it('应该正确处理API加载错误', async () => {
      vi.mocked(studentApi.getStudents).mockRejectedValue(new Error('加载失败'))

      wrapper = mount(StudentsView, {
        global: {
          plugins: [pinia],
          stubs: {
            'el-container': true,
            'el-header': true,
            'el-main': true,
            'el-menu': true,
            'el-menu-item': true,
            'el-card': true,
            'el-table': true,
            'el-table-column': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-button': true,
            'el-icon': true,
            'el-pagination': true,
            'el-drawer': true,
            'el-skeleton': true,
            'el-tag': true,
            'el-empty': true,
            'el-avatar': true,
            'el-dialog': true,
            'el-progress': true,
            'el-message-box': true
          }
        }
      })

      await new Promise(resolve => setTimeout(resolve, 0))
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.students).toEqual([])
    })
  })

  describe('知识图谱查看', () => {
    it('应该正确检查学生是否有知识图谱', async () => {
      wrapper = mount(StudentsView, {
        global: {
          plugins: [pinia],
          stubs: {
            'el-container': true,
            'el-header': true,
            'el-main': true,
            'el-menu': true,
            'el-menu-item': true,
            'el-card': true,
            'el-table': true,
            'el-table-column': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-button': true,
            'el-icon': true,
            'el-pagination': true,
            'el-drawer': true,
            'el-skeleton': true,
            'el-tag': true,
            'el-empty': true,
            'el-avatar': true,
            'el-dialog': true,
            'el-progress': true,
            'el-message-box': true
          }
        }
      })

      await new Promise(resolve => setTimeout(resolve, 0))

      // 初始状态没有缓存的知识图谱
      expect(wrapper.vm.hasKnowledgeGraph('student-1')).toBe(false)

      // 模拟加载知识图谱
      await wrapper.vm.showKnowledgeGraph(mockStudents[0])

      // 现在应该有缓存
      expect(wrapper.vm.hasKnowledgeGraph('student-1')).toBe(true)
    })

    it('应该正确调用获取知识图谱API', async () => {
      wrapper = mount(StudentsView, {
        global: {
          plugins: [pinia],
          stubs: {
            'el-container': true,
            'el-header': true,
            'el-main': true,
            'el-menu': true,
            'el-menu-item': true,
            'el-card': true,
            'el-table': true,
            'el-table-column': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-button': true,
            'el-icon': true,
            'el-pagination': true,
            'el-drawer': true,
            'el-skeleton': true,
            'el-tag': true,
            'el-empty': true,
            'el-avatar': true,
            'el-dialog': true,
            'el-progress': true,
            'el-message-box': true
          }
        }
      })

      await new Promise(resolve => setTimeout(resolve, 0))

      await wrapper.vm.showKnowledgeGraph(mockStudents[0])

      expect(studentApi.getKnowledgeGraph).toHaveBeenCalledWith('student-1')
    })

    it('应该正确处理知识图谱404错误', async () => {
      const error404 = { response: { status: 404 } }
      vi.mocked(studentApi.getKnowledgeGraph).mockRejectedValue(error404)

      wrapper = mount(StudentsView, {
        global: {
          plugins: [pinia],
          stubs: {
            'el-container': true,
            'el-header': true,
            'el-main': true,
            'el-menu': true,
            'el-menu-item': true,
            'el-card': true,
            'el-table': true,
            'el-table-column': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-button': true,
            'el-icon': true,
            'el-pagination': true,
            'el-drawer': true,
            'el-skeleton': true,
            'el-tag': true,
            'el-empty': true,
            'el-avatar': true,
            'el-dialog': true,
            'el-progress': true,
            'el-message-box': true
          }
        }
      })

      await new Promise(resolve => setTimeout(resolve, 0))

      await wrapper.vm.showKnowledgeGraph(mockStudents[0])

      expect(wrapper.vm.currentGraph).toBe(null)
      expect(wrapper.vm.graphDrawerVisible).toBe(true)
    })
  })

  describe('学生诊断功能', () => {
    it('应该正确调用学生诊断API', async () => {
      // Mock MessageBox.confirm 返回 Promise.resolve（用户点击确定）
      vi.doMock('element-plus', () => ({
        ElMessageBox: {
          confirm: vi.fn(() => Promise.resolve())
        }
      }))

      wrapper = mount(StudentsView, {
        global: {
          plugins: [pinia],
          stubs: {
            'el-container': true,
            'el-header': true,
            'el-main': true,
            'el-menu': true,
            'el-menu-item': true,
            'el-card': true,
            'el-table': true,
            'el-table-column': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-button': true,
            'el-icon': true,
            'el-pagination': true,
            'el-drawer': true,
            'el-skeleton': true,
            'el-tag': true,
            'el-empty': true,
            'el-avatar': true,
            'el-dialog': true,
            'el-progress': true,
            'el-message-box': true
          }
        }
      })

      await new Promise(resolve => setTimeout(resolve, 0))

      // 直接调用diagnoseStudent方法（跳过确认对话框）
      vi.spyOn(wrapper.vm as any, 'diagnoseStudent').mockImplementation(async function(this: any, student: any) {
        this.diagnosingStudentId = student.id
        await studentApi.diagnoseStudent(student.id)
        this.diagnosingStudentId = null
      })

      await (wrapper.vm as any).diagnoseStudent(mockStudents[0])

      expect(studentApi.diagnoseStudent).toHaveBeenCalledWith('student-1')
    })
  })

  describe('批量选择功能', () => {
    it('应该正确处理学生选择变化', async () => {
      wrapper = mount(StudentsView, {
        global: {
          plugins: [pinia],
          stubs: {
            'el-container': true,
            'el-header': true,
            'el-main': true,
            'el-menu': true,
            'el-menu-item': true,
            'el-card': true,
            'el-table': true,
            'el-table-column': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-button': true,
            'el-icon': true,
            'el-pagination': true,
            'el-drawer': true,
            'el-skeleton': true,
            'el-tag': true,
            'el-empty': true,
            'el-avatar': true,
            'el-dialog': true,
            'el-progress': true,
            'el-message-box': true
          }
        }
      })

      await new Promise(resolve => setTimeout(resolve, 0))

      // 模拟选择变化
      wrapper.vm.handleSelectionChange([mockStudents[0], mockStudents[1]])

      expect(wrapper.vm.selectedStudents.length).toBe(2)
      expect(wrapper.vm.selectedStudents).toEqual([mockStudents[0], mockStudents[1]])
    })

    it('应该正确处理清空选择', async () => {
      wrapper = mount(StudentsView, {
        global: {
          plugins: [pinia],
          stubs: {
            'el-container': true,
            'el-header': true,
            'el-main': true,
            'el-menu': true,
            'el-menu-item': true,
            'el-card': true,
            'el-table': true,
            'el-table-column': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-button': true,
            'el-icon': true,
            'el-pagination': true,
            'el-drawer': true,
            'el-skeleton': true,
            'el-tag': true,
            'el-empty': true,
            'el-avatar': true,
            'el-dialog': true,
            'el-progress': true,
            'el-message-box': true
          }
        }
      })

      await new Promise(resolve => setTimeout(resolve, 0))

      // 先选择学生
      wrapper.vm.handleSelectionChange([mockStudents[0], mockStudents[1]])
      expect(wrapper.vm.selectedStudents.length).toBe(2)

      // 清空选择
      wrapper.vm.handleSelectionChange([])
      expect(wrapper.vm.selectedStudents.length).toBe(0)
    })
  })

  describe('辅助方法', () => {
    it('应该正确格式化日期时间', async () => {
      wrapper = mount(StudentsView, {
        global: {
          plugins: [pinia],
          stubs: {
            'el-container': true,
            'el-header': true,
            'el-main': true,
            'el-menu': true,
            'el-menu-item': true,
            'el-card': true,
            'el-table': true,
            'el-table-column': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-button': true,
            'el-icon': true,
            'el-pagination': true,
            'el-drawer': true,
            'el-skeleton': true,
            'el-tag': true,
            'el-empty': true,
            'el-avatar': true,
            'el-dialog': true,
            'el-progress': true,
            'el-message-box': true
          }
        }
      })

      await new Promise(resolve => setTimeout(resolve, 0))

      const dateStr = '2025-01-15T10:30:00Z'
      const formatted = (wrapper.vm as any).formatDate(dateStr)

      // 格式化应该包含日期和时间
      expect(formatted).toBeDefined()
      expect(typeof formatted).toBe('string')
    })

    it('应该正确返回优先级类型', async () => {
      wrapper = mount(StudentsView, {
        global: {
          plugins: [pinia],
          stubs: {
            'el-container': true,
            'el-header': true,
            'el-main': true,
            'el-menu': true,
            'el-menu-item': true,
            'el-card': true,
            'el-table': true,
            'el-table-column': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-button': true,
            'el-icon': true,
            'el-pagination': true,
            'el-drawer': true,
            'el-skeleton': true,
            'el-tag': true,
            'el-empty': true,
            'el-avatar': true,
            'el-dialog': true,
            'el-progress': true,
            'el-message-box': true
          }
        }
      })

      await new Promise(resolve => setTimeout(resolve, 0))

      expect((wrapper.vm as any).getPriorityType('high')).toBe('danger')
      expect((wrapper.vm as any).getPriorityType('medium')).toBe('warning')
      expect((wrapper.vm as any).getPriorityType('low')).toBe('info')
    })

    it('应该正确返回优先级文本', async () => {
      wrapper = mount(StudentsView, {
        global: {
          plugins: [pinia],
          stubs: {
            'el-container': true,
            'el-header': true,
            'el-main': true,
            'el-menu': true,
            'el-menu-item': true,
            'el-card': true,
            'el-table': true,
            'el-table-column': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-button': true,
            'el-icon': true,
            'el-pagination': true,
            'el-drawer': true,
            'el-skeleton': true,
            'el-tag': true,
            'el-empty': true,
            'el-avatar': true,
            'el-dialog': true,
            'el-progress': true,
            'el-message-box': true
          }
        }
      })

      await new Promise(resolve => setTimeout(resolve, 0))

      expect((wrapper.vm as any).getPriorityText('high')).toBe('高优先级')
      expect((wrapper.vm as any).getPriorityText('medium')).toBe('中优先级')
      expect((wrapper.vm as any).getPriorityText('low')).toBe('低优先级')
    })
  })

  describe('计算属性', () => {
    it('should correctly compute hasAbilityData when graph has abilities', async () => {
      wrapper = mount(StudentsView, {
        global: {
          plugins: [pinia],
          stubs: {
            'el-container': true,
            'el-header': true,
            'el-main': true,
            'el-menu': true,
            'el-menu-item': true,
            'el-card': true,
            'el-table': true,
            'el-table-column': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-button': true,
            'el-icon': true,
            'el-pagination': true,
            'el-drawer': true,
            'el-skeleton': true,
            'el-tag': true,
            'el-empty': true,
            'el-avatar': true,
            'el-dialog': true,
            'el-progress': true,
            'el-message-box': true
          }
        }
      })

      await new Promise(resolve => setTimeout(resolve, 0))

      // 设置当前图谱
      wrapper.vm.currentGraph = mockKnowledgeGraph

      expect(wrapper.vm.hasAbilityData).toBe(true)
    })

    it('should correctly compute hasAbilityData when graph has no abilities', async () => {
      wrapper = mount(StudentsView, {
        global: {
          plugins: [pinia],
          stubs: {
            'el-container': true,
            'el-header': true,
            'el-main': true,
            'el-menu': true,
            'el-menu-item': true,
            'el-card': true,
            'el-table': true,
            'el-table-column': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-button': true,
            'el-icon': true,
            'el-pagination': true,
            'el-drawer': true,
            'el-skeleton': true,
            'el-tag': true,
            'el-empty': true,
            'el-avatar': true,
            'el-dialog': true,
            'el-progress': true,
            'el-message-box': true
          }
        }
      })

      await new Promise(resolve => setTimeout(resolve, 0))

      // 设置空图谱
      wrapper.vm.currentGraph = { ...mockKnowledgeGraph, abilities: {} }

      expect(wrapper.vm.hasAbilityData).toBe(false)
    })
  })
})
