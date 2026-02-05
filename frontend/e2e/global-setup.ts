/**
 * Playwright 全局测试设置
 * 在所有测试运行前执行，用于设置测试环境
 */
import { chromium, FullConfig } from '@playwright/test'

async function globalSetup(config: FullConfig) {
  console.log('🔧 设置 E2E 测试环境...')

  // 启动浏览器并设置测试认证状态
  const browser = await chromium.launch()
  const context = await browser.newContext()
  const page = await context.newPage()

  try {
    // 访问首页
    await page.goto('http://localhost:5174')
    await page.waitForSelector('#app', { timeout: 5000 })

    // 设置教师认证状态
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

    await page.evaluate((data: any) => {
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      localStorage.setItem('user', data.user)
    }, teacherData)

    // 保存教师 storage state
    await context.storageState({ path: 'e2e/.auth/teacher-storage-state.json' })
    console.log('✅ 教师认证状态已保存')

    // 创建新上下文设置学生认证
    const studentContext = await browser.newContext()
    const studentPage = await studentContext.newPage()

    await studentPage.goto('http://localhost:5174')
    await studentPage.waitForSelector('#app', { timeout: 5000 })

    // 设置学生认证状态
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

    await studentPage.evaluate((data: any) => {
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      localStorage.setItem('user', data.user)
    }, studentData)

    // 保存学生 storage state
    await studentContext.storageState({ path: 'e2e/.auth/student-storage-state.json' })
    console.log('✅ 学生认证状态已保存')

    await studentContext.close()

    console.log('✅ E2E 测试环境设置完成')

  } catch (error) {
    console.error('❌ 设置测试环境失败:', error)
  } finally {
    await browser.close()
  }
}

export default globalSetup
