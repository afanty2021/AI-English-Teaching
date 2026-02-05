/**
 * 教师端学习报告API测试
 * 测试teacherReport API客户端的功能
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { get, post } from '@/utils/request'
import teacherReportApi from '@/api/teacherReport'

// Mock utils/request
vi.mock('@/utils/request', () => ({
  get: vi.fn(),
  post: vi.fn()
}))

describe('teacherReportApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getStudents', () => {
    it('应该正确调用获取学生列表API', async () => {
      const mockResponse = {
        total: 10,
        limit: 20,
        offset: 0,
        students: [
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
          }
        ]
      }

      vi.mocked(get).mockResolvedValue(mockResponse)

      const params = {
        classId: 'class-1',
        page: 1,
        limit: 20
      }

      const result = await teacherReportApi.getStudents(params)

      expect(get).toHaveBeenCalledWith('/reports/teacher/students?class_id=class-1&offset=0&limit=20')
      expect(result).toEqual(mockResponse)
    })

    it('应该正确处理无班级筛选参数', async () => {
      const mockResponse = {
        total: 5,
        limit: 20,
        offset: 0,
        students: []
      }

      vi.mocked(get).mockResolvedValue(mockResponse)

      const params = {
        page: 1,
        limit: 20
      }

      const result = await teacherReportApi.getStudents(params)

      expect(get).toHaveBeenCalledWith('/reports/teacher/students?offset=0&limit=20')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getStudentReport', () => {
    it('应该正确调用获取学生报告详情API', async () => {
      const mockResponse = {
        id: 'report-1',
        student_id: '1',
        report_type: 'weekly',
        period_start: '2025-01-01T00:00:00Z',
        period_end: '2025-01-07T23:59:59Z',
        status: 'completed',
        title: '周学习报告',
        statistics: {
          total_practices: 50,
          completion_rate: 0.8,
          avg_correct_rate: 0.75
        },
        ability_analysis: {
          ability_radar: [
            { name: '听力', value: 80, confidence: 0.9 },
            { name: '阅读', value: 85, confidence: 0.8 }
          ]
        },
        weak_points: {
          total_unmastered: 5,
          knowledge_points: { '语法错误': 3, '时态': 2 }
        },
        recommendations: {
          rule_based: [
            {
              category: '语法',
              priority: 'high',
              title: '加强语法练习',
              description: '建议多做语法相关练习'
            }
          ]
        }
      }

      vi.mocked(get).mockResolvedValue(mockResponse)

      const result = await teacherReportApi.getStudentReport('1', 'report-1')

      expect(get).toHaveBeenCalledWith('/reports/teacher/students/1/reports/report-1')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getStudentReports', () => {
    it('应该正确调用获取学生所有报告API', async () => {
      const mockResponse = {
        total: 3,
        limit: 20,
        offset: 0,
        reports: [
          {
            id: 'report-3',
            report_type: 'weekly',
            period_start: '2025-01-15T00:00:00Z',
            period_end: '2025-01-21T23:59:59Z',
            status: 'completed',
            title: '第3周报告',
            created_at: '2025-01-22T10:00:00Z'
          }
        ]
      }

      vi.mocked(get).mockResolvedValue(mockResponse)

      const params = {
        reportType: 'weekly',
        page: 1,
        limit: 20
      }

      const result = await teacherReportApi.getStudentReports('1', params)

      expect(get).toHaveBeenCalledWith('/reports/teacher/students/1?report_type=weekly&offset=0&limit=20')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getClassSummary', () => {
    it('应该正确调用获取班级学习状况汇总API', async () => {
      const mockResponse = {
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

      vi.mocked(get).mockResolvedValue(mockResponse)

      const params = {
        classId: 'class-1',
        periodStart: '2025-01-01',
        periodEnd: '2025-01-31'
      }

      const result = await teacherReportApi.getClassSummary(params)

      expect(get).toHaveBeenCalledWith(
        '/reports/teacher/class-summary?class_id=class-1&period_start=2025-01-01&period_end=2025-01-31'
      )
      expect(result).toEqual(mockResponse)
    })

    it('应该正确处理无时间范围参数', async () => {
      const mockResponse = {
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

      vi.mocked(get).mockResolvedValue(mockResponse)

      const params = {
        classId: 'class-1'
      }

      const result = await teacherReportApi.getClassSummary(params)

      expect(get).toHaveBeenCalledWith('/reports/teacher/class-summary?class_id=class-1')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('generateStudentReport', () => {
    it('应该正确调用生成学生报告API', async () => {
      const mockResponse = {
        report: {
          id: 'report-new',
          student_id: '1',
          report_type: 'custom',
          status: 'completed'
        },
        message: '学习报告生成成功'
      }

      vi.mocked(post).mockResolvedValue(mockResponse)

      const data = {
        report_type: 'custom' as const,
        period_start: '2025-01-01',
        period_end: '2025-01-31'
      }

      const result = await teacherReportApi.generateStudentReport('1', data)

      expect(post).toHaveBeenCalledWith('/reports/generate', data)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('exportStudentReport', () => {
    it('应该正确调用导出学生报告API', async () => {
      const mockBlob = new Blob(['PDF content'], { type: 'application/pdf' })

      vi.mocked(post).mockResolvedValue(mockBlob)

      const result = await teacherReportApi.exportStudentReport('1', 'report-1', 'pdf')

      expect(post).toHaveBeenCalledWith(
        '/reports/report-1/export?format_type=pdf',
        {},
        expect.objectContaining({
          responseType: 'blob'
        })
      )
      expect(result).toEqual(mockBlob)
    })

    it('应该正确处理图片格式导出', async () => {
      const mockBlob = new Blob(['Image content'], { type: 'image/png' })

      vi.mocked(post).mockResolvedValue(mockBlob)

      const result = await teacherReportApi.exportStudentReport('1', 'report-1', 'image')

      expect(post).toHaveBeenCalledWith(
        '/reports/report-1/export?format_type=image',
        {},
        expect.objectContaining({
          responseType: 'blob'
        })
      )
      expect(result).toEqual(mockBlob)
    })
  })
})

describe('TypeScript 类型定义', () => {
  it('应该正确导出所有接口类型', () => {
    // 测试 StudentReportSummary 接口
    const mockStudent: import('@/api/teacherReport').StudentReportSummary = {
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

    expect(mockStudent.student_id).toBe('1')
    expect(mockStudent.has_reports).toBe(true)

    // 测试 ClassSummary 接口
    const mockClass: import('@/api/teacherReport').ClassSummary = {
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

    expect(mockClass.total_students).toBe(30)
    expect(mockClass.overall_stats.avg_completion_rate).toBe(0.82)
  })
})
