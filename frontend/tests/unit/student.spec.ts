/**
 * 学生管理API测试
 * 测试student API客户端的功能
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { get, post } from '@/utils/request'
import studentApi from '@/api/student'

// Mock utils/request
vi.mock('@/utils/request', () => ({
  get: vi.fn(),
  post: vi.fn()
}))

describe('studentApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getStudents', () => {
    it('应该正确调用获取学生列表API（无参数）', async () => {
      const mockResponse: ReturnType<typeof studentApi.getStudents> = [
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
        }
      ]

      vi.mocked(get).mockResolvedValue(mockResponse)

      const result = await studentApi.getStudents()

      expect(get).toHaveBeenCalledWith('/api/v1/students')
      expect(result).toEqual(mockResponse)
    })

    it('应该正确处理分页参数', async () => {
      const mockResponse: ReturnType<typeof studentApi.getStudents> = []

      vi.mocked(get).mockResolvedValue(mockResponse)

      const params = {
        skip: 20,
        limit: 20
      }

      await studentApi.getStudents(params)

      expect(get).toHaveBeenCalledWith('/api/v1/students?skip=20&limit=20')
    })

    it('应该正确处理班级筛选参数', async () => {
      const mockResponse: ReturnType<typeof studentApi.getStudents> = []

      vi.mocked(get).mockResolvedValue(mockResponse)

      const params = {
        skip: 0,
        limit: 20,
        classId: 'class-1'
      }

      await studentApi.getStudents(params)

      expect(get).toHaveBeenCalledWith('/api/v1/students?skip=0&limit=20&class_id=class-1')
    })

    it('应该正确处理完整参数', async () => {
      const mockResponse: ReturnType<typeof studentApi.getStudents> = []

      vi.mocked(get).mockResolvedValue(mockResponse)

      const params = {
        skip: 40,
        limit: 50,
        classId: 'class-2'
      }

      await studentApi.getStudents(params)

      expect(get).toHaveBeenCalledWith('/api/v1/students?skip=40&limit=50&class_id=class-2')
    })

    it('应该正确处理undefined的classId参数', async () => {
      const mockResponse: ReturnType<typeof studentApi.getStudents> = []

      vi.mocked(get).mockResolvedValue(mockResponse)

      const params = {
        skip: 0,
        limit: 20,
        classId: undefined
      }

      await studentApi.getStudents(params)

      expect(get).toHaveBeenCalledWith('/api/v1/students?skip=0&limit=20')
    })
  })

  describe('getStudent', () => {
    it('应该正确调用获取学生详情API', async () => {
      const mockResponse = {
        id: 'student-1',
        user_id: 'user-1',
        username: '张三',
        email: 'zhangsan@example.com',
        target_exam: 'CET4',
        target_score: 500,
        current_cefr_level: 'B1',
        grade: '大一',
        created_at: '2025-01-15T10:00:00Z'
      }

      vi.mocked(get).mockResolvedValue(mockResponse)

      const studentId = 'student-1'
      const result = await studentApi.getStudent(studentId)

      expect(get).toHaveBeenCalledWith(`/api/v1/students/${studentId}`)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getKnowledgeGraph', () => {
    it('应该正确调用获取学生知识图谱API', async () => {
      const mockResponse = {
        student_id: 'student-1',
        nodes: [
          {
            id: 'ability_listening',
            type: 'ability',
            label: '听力',
            value: 75,
            level: 'intermediate'
          }
        ],
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

      vi.mocked(get).mockResolvedValue(mockResponse)

      const studentId = 'student-1'
      const result = await studentApi.getKnowledgeGraph(studentId)

      expect(get).toHaveBeenCalledWith(`/api/v1/students/${studentId}/knowledge-graph`)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('diagnoseStudent', () => {
    it('应该正确调用触发诊断API（无练习数据）', async () => {
      const mockResponse = {
        message: '诊断完成',
        student_id: 'student-1',
        status: 'completed',
        cefr_level: 'B1',
        abilities: {
          listening: 75,
          reading: 80
        }
      }

      vi.mocked(post).mockResolvedValue(mockResponse)

      const studentId = 'student-1'
      const result = await studentApi.diagnoseStudent(studentId)

      expect(post).toHaveBeenCalledWith(`/api/v1/students/${studentId}/diagnose`, {})
      expect(result).toEqual(mockResponse)
    })

    it('应该正确传递练习数据', async () => {
      const mockResponse = {
        message: '诊断完成',
        student_id: 'student-1',
        status: 'completed'
      }

      vi.mocked(post).mockResolvedValue(mockResponse)

      const studentId = 'student-1'
      const practiceData = [
        {
          content_id: 'content-1',
          topic: '听力',
          difficulty: 'intermediate',
          score: 85,
          correct_rate: 0.85,
          time_spent: 300
        }
      ]

      await studentApi.diagnoseStudent(studentId, { practice_data: practiceData })

      expect(post).toHaveBeenCalledWith(
        `/api/v1/students/${studentId}/diagnose`,
        { practice_data: practiceData }
      )
    })
  })

  describe('getStudentProgress', () => {
    it('应该正确调用获取学生进度API', async () => {
      const mockResponse = {
        student_id: 'student-1',
        target_exam: 'CET4',
        target_score: 500,
        current_cefr_level: 'B1',
        conversation_count: 10,
        practice_count: 50,
        average_score: 82.5
      }

      vi.mocked(get).mockResolvedValue(mockResponse)

      const studentId = 'student-1'
      const result = await studentApi.getStudentProgress(studentId)

      expect(get).toHaveBeenCalledWith(`/api/v1/students/${studentId}/progress`)
      expect(result).toEqual(mockResponse)
    })
  })
})
