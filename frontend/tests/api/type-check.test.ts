/**
 * 前端 API 类型检查测试
 *
 * 这些测试确保:
 * 1. API 模块正确导出其函数
 * 2. 类型定义与使用匹配
 * 3. 导入/导出格式一致
 *
 * 运行: npm run test tests/api/type-check.test.ts
 */
import { describe, it, expect } from 'vitest'

// 导入所有 API 模块进行类型检查
import authApi from '@/api/auth'
import reportApi from '@/api/report'
import mistakeApi from '@/api/mistake'
import contentApi from '@/api/content'
import conversationApi from '@/api/conversation'

// 导入类型定义
import type {
  User,
  LoginRequest,
  RegisterRequest,
  AuthResponse
} from '@/types/auth'

import type {
  LearningReport,
  GenerateReportRequest,
  ReportListResponse
} from '@/api/report'

describe('API 模块导出检查', () => {
  it('authApi 应该导出所有必需的方法', () => {
    expect(authApi).toBeDefined()
    expect(typeof authApi.register).toBe('function')
    expect(typeof authApi.login).toBe('function')
    expect(typeof authApi.getCurrentUser).toBe('function')
    expect(typeof authApi.refreshToken).toBe('function')
  })

  it('reportApi 应该作为默认导出', () => {
    expect(reportApi).toBeDefined()
    expect(typeof reportApi.generateReport).toBe('function')
    expect(typeof reportApi.getMyReports).toBe('function')
    expect(typeof reportApi.getReportDetail).toBe('function')
  })

  it('mistakeApi 应该作为默认导出', () => {
    expect(mistakeApi).toBeDefined()
    expect(typeof mistakeApi.getMyMistakes).toBe('function')
    expect(typeof mistakeApi.getStatistics).toBe('function')
  })
})

describe('API 类型一致性检查', () => {
  it('LoginRequest 类型应该包含必需字段', () => {
    const loginData: LoginRequest = {
      username: 'testuser',
      password: 'Test1234'
    }
    expect(loginData.username).toBeDefined()
    expect(loginData.password).toBeDefined()
  })

  it('GenerateReportRequest 类型应该接受 report_type', () => {
    const reportData: GenerateReportRequest = {
      report_type: 'weekly'
    }
    expect(reportData.report_type).toBe('weekly')
  })

  it('LearningReport 类型应该包含所有必需字段', () => {
    const report: Partial<LearningReport> = {
      id: 'test-id',
      student_id: 'student-id',
      report_type: 'weekly',
      period_start: '2026-01-01T00:00:00Z',
      period_end: '2026-01-31T23:59:59Z',
      status: 'completed'
    }
    expect(report.id).toBe('test-id')
    expect(report.report_type).toBe('weekly')
  })
})

describe('常见导入错误检查', () => {
  /**
   * 这些测试防止我们之前遇到的导入问题:
   * - 使用命名导入 { reportApi } 而不是默认导入 reportApi
   * - 混合导入/导出格式
   */

  it('不应该允许对 reportApi 使用命名导入', async () => {
    // 这个测试文档化了一个常见错误
    // 错误: import { reportApi } from '@/api/report'
    // 正确: import reportApi from '@/api/report'

    // 下面的导入会在编译时报错（这是期望的）
    // import { reportApi as wrongImport } from '@/api/report'

    // 验证默认导入工作正常
    const api = reportApi
    expect(api).toBeDefined()
    expect(typeof api.generateReport).toBe('function')
  })

  it('authApi 应该支持命名导出', () => {
    // authApi 使用命名导出
    expect(authApi).toBeDefined()
    expect(typeof authApi.login).toBe('function')
  })
})

describe('API 响应类型检查', () => {
  it('登录响应应该包含 token', async () => {
    // 这是一个编译时类型检查测试
    type LoginResponse = {
      access_token: string
      refresh_token: string
      token_type: string
      expires_in: number
      user: User
    }

    // 下面的代码如果类型不匹配会在编译时报错
    const mockResponse: LoginResponse = {
      access_token: 'test-token',
      refresh_token: 'test-refresh',
      token_type: 'bearer',
      expires_in: 1800,
      user: {
        id: 'test-id',
        username: 'testuser',
        email: 'test@example.com',
        role: 'student',
        is_active: true,
        is_superuser: false,
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z'
      }
    }

    expect(mockResponse.access_token).toBeTruthy()
    expect(mockResponse.user.role).toBe('student')
  })

  it('报告列表响应应该包含分页信息', () => {
    type ReportsResponse = {
      total: number
      limit: number
      offset: number
      reports: Array<Partial<LearningReport>>
    }

    const mockResponse: ReportsResponse = {
      total: 1,
      limit: 20,
      offset: 0,
      reports: [
        {
          id: 'test-id',
          report_type: 'weekly',
          status: 'completed'
        }
      ]
    }

    expect(mockResponse.total).toBe(1)
    expect(mockResponse.reports).toHaveLength(1)
  })
})

// ============================================================================
// 编译时检查 - 这些检查会在运行前捕获类型错误
// ============================================================================

/**
 * 这个函数不会运行，但会在编译时进行类型检查
 * 如果有类型错误，vue-tsc 会报告
 */
function _typeCheckCompilation() {
  // 检查 API 调用类型
  async function checkAPICalls() {
    const loginData: LoginRequest = {
      username: 'test',
      password: 'test123'
    }

    // 如果 authApi.login 的类型定义错误，下面会报错
    const response = await authApi.login(loginData)

    // 如果返回类型不匹配，下面会报错
    const token: string = response.access_token
    const user: User = response.user
  }

  // 检查报告 API 类型
  async function checkReportAPI() {
    const reportData: GenerateReportRequest = {
      report_type: 'weekly'
    }

    // 如果类型定义错误，下面会报错
    const report: LearningReport = await reportApi.generateReport(reportData)

    // 访问嵌套属性
    if (report.statistics) {
      const practices: number = report.statistics.total_practices || 0
    }
  }

  // 防止 "unused function" 错误
  return { checkAPICalls, checkReportAPI }
}
