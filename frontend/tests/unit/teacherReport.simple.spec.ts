/**
 * 教师端学习报告API简化测试
 * 测试teacherReport API客户端的核心功能
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import teacherReportApi from '@/api/teacherReport'

// Mock utils/request
vi.mock('@/utils/request', () => ({
  get: vi.fn(),
  post: vi.fn()
}))

describe('teacherReportApi 核心功能测试', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('✅ getStudents - 应该正确构建API调用', async () => {
    const mockResponse = {
      total: 10,
      limit: 20,
      offset: 0,
      students: []
    }

    const { get } = await import('@/utils/request')
    vi.mocked(get).mockResolvedValue(mockResponse)

    const result = await teacherReportApi.getStudents({
      classId: 'class-1',
      page: 1,
      limit: 20
    })

    expect(get).toHaveBeenCalledWith('/reports/teacher/students?class_id=class-1&offset=0&limit=20')
    expect(result).toEqual(mockResponse)
  })

  it('✅ getStudentReport - 应该正确调用报告详情API', async () => {
    const mockResponse = {
      id: 'report-1',
      student_id: '1',
      report_type: 'weekly',
      statistics: {},
      ability_analysis: {},
      weak_points: {},
      recommendations: {}
    }

    const { get } = await import('@/utils/request')
    vi.mocked(get).mockResolvedValue(mockResponse)

    const result = await teacherReportApi.getStudentReport('1', 'report-1')

    expect(get).toHaveBeenCalledWith('/reports/teacher/students/1/reports/report-1')
    expect(result).toEqual(mockResponse)
  })

  it('✅ getClassSummary - 应该正确调用班级汇总API', async () => {
    const mockResponse = {
      class_id: 'class-1',
      class_name: '高一(1)班',
      total_students: 30,
      active_students: 25,
      overall_stats: {
        avg_completion_rate: 0.82,
        avg_correct_rate: 0.78,
        total_study_hours: 150.5
      }
    }

    const { get } = await import('@/utils/request')
    vi.mocked(get).mockResolvedValue(mockResponse)

    const result = await teacherReportApi.getClassSummary({
      classId: 'class-1',
      periodStart: '2025-01-01',
      periodEnd: '2025-01-31'
    })

    expect(get).toHaveBeenCalledWith(
      '/reports/teacher/class-summary?class_id=class-1&period_start=2025-01-01&period_end=2025-01-31'
    )
    expect(result).toEqual(mockResponse)
  })

  it('✅ generateStudentReport - 应该正确调用生成报告API', async () => {
    const mockResponse = {
      report: { id: 'report-new' },
      message: '学习报告生成成功'
    }

    const { post } = await import('@/utils/request')
    vi.mocked(post).mockResolvedValue(mockResponse)

    const result = await teacherReportApi.generateStudentReport('1', {
      report_type: 'custom',
      period_start: '2025-01-01',
      period_end: '2025-01-31'
    })

    expect(post).toHaveBeenCalledWith('/reports/generate', {
      report_type: 'custom',
      period_start: '2025-01-01',
      period_end: '2025-01-31'
    })
    expect(result).toEqual(mockResponse)
  })

  it('✅ exportStudentReport - 应该正确调用导出报告API', async () => {
    const mockBlob = new Blob(['PDF content'], { type: 'application/pdf' })

    const { post } = await import('@/utils/request')
    vi.mocked(post).mockResolvedValue(mockBlob)

    const result = await teacherReportApi.exportStudentReport('1', 'report-1', 'pdf')

    expect(post).toHaveBeenCalledWith(
      '/reports/report-1/export?format_type=pdf',
      {},
      expect.objectContaining({ responseType: 'blob' })
    )
    expect(result).toEqual(mockBlob)
  })

  it('✅ TypeScript类型检查 - 应该正确导出接口类型', () => {
    // 测试类型导出
    const studentType: import('@/api/teacherReport').StudentReportSummary = {
      student_id: '1',
      student_number: 'S2024001',
      student_name: '张三',
      email: 'test@example.com',
      class_id: 'class-1',
      class_name: '高一(1)班',
      grade: '高一',
      has_reports: true
    }

    expect(studentType.student_id).toBe('1')
    expect(studentType.has_reports).toBe(true)

    // 测试班级汇总类型
    const classType: import('@/api/teacherReport').ClassSummary = {
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

    expect(classType.total_students).toBe(30)
    expect(classType.overall_stats.avg_completion_rate).toBe(0.82)
  })
})

describe('API错误处理测试', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('✅ 应该正确处理网络错误', async () => {
    const { get } = await import('@/utils/request')
    const networkError = new Error('Network error')
    vi.mocked(get).mockRejectedValue(networkError)

    try {
      await teacherReportApi.getStudents({ page: 1, limit: 20 })
      expect(false).toBe(true) // 不应该到达这里
    } catch (error) {
      expect(error).toBe(networkError)
    }
  })

  it('✅ 应该正确处理无效参数', async () => {
    const { get } = await import('@/utils/request')
    const errorResponse = { message: 'Invalid parameter', code: 400 }
    vi.mocked(get).mockRejectedValue(errorResponse)

    try {
      await teacherReportApi.getStudents({ page: -1, limit: 200 })
      expect(false).toBe(true) // 不应该到达这里
    } catch (error) {
      expect(error).toBe(errorResponse)
    }
  })
})
