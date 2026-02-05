/**
 * 学生认证 Fixture
 * 为推荐系统测试提供学生认证支持
 */
import { test as base } from '@playwright/test'

type StudentAuthFixtures = {
  studentPage: Awaited<ReturnType<typeof createStudentAuthenticatedPage>>
  teacherPage: Awaited<ReturnType<typeof createTeacherAuthenticatedPage>>
}

/**
 * 创建学生认证页面
 */
async function createStudentAuthenticatedPage({ page }: { page: any }) {
  const studentData = {
    access_token: 'test-student-token-' + Date.now(),
    refresh_token: 'test-student-refresh-' + Date.now(),
    user: JSON.stringify({
      id: 'test-student-id',
      username: 'test_student',
      email: 'student@test.com',
      role: 'student',
      organization_id: 'test-org-id',
      target_exam: 'CET4',
      current_cefr_level: 'B1'
    })
  }

  // 访问首页触发应用初始化
  await page.goto('/')
  await page.waitForSelector('#app', { timeout: 5000 })

  // 设置 localStorage
  await page.evaluate((data: any) => {
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    localStorage.setItem('user', data.user)
    window.dispatchEvent(new Event('storage'))
  }, studentData)

  // 等待认证状态生效
  await page.waitForTimeout(200)

  return { page, studentData }
}

/**
 * 创建教师认证页面（用于对比测试）
 */
async function createTeacherAuthenticatedPage({ page }: { page: any }) {
  const teacherData = {
    access_token: 'test-teacher-token-' + Date.now(),
    refresh_token: 'test-teacher-refresh-' + Date.now(),
    user: JSON.stringify({
      id: 'test-teacher-id',
      username: 'test_teacher',
      email: 'teacher@test.com',
      role: 'teacher',
      organization_id: 'test-org-id'
    })
  }

  // 访问首页触发应用初始化
  await page.goto('/')
  await page.waitForSelector('#app', { timeout: 5000 })

  // 设置 localStorage
  await page.evaluate((data: any) => {
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    localStorage.setItem('user', data.user)
    window.dispatchEvent(new Event('storage'))
  }, teacherData)

  // 等待认证状态生效
  await page.waitForTimeout(200)

  return { page, teacherData }
}

/**
 * 导出带学生认证的 test
 */
export const test = base.extend<StudentAuthFixtures>({
  studentPage: async ({ page }, use) => {
    const studentPage = await createStudentAuthenticatedPage({ page })
    await use(studentPage)
  },
  teacherPage: async ({ page }, use) => {
    const teacherPage = await createTeacherAuthenticatedPage({ page })
    await use(teacherPage)
  }
})

export { expect } from '@playwright/test'
