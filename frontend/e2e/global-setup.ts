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

    // 在 localStorage 中设置测试认证状态
    await page.evaluate(() => {
      const testData = {
        access_token: 'test-token-' + Date.now(),
        refresh_token: 'test-refresh-token-' + Date.now(),
        user: JSON.stringify({
          id: 'test-user-id',
          username: 'test-teacher',
          email: 'teacher@test.com',
          role: 'teacher',
          organization_id: 'test-org-id'
        })
      }

      // 设置 localStorage
      localStorage.setItem('access_token', testData.access_token)
      localStorage.setItem('refresh_token', testData.refresh_token)
      localStorage.setItem('user', testData.user)

      return testData
    })

    // 保存 storage state 到文件
    await context.storageState({ path: 'e2e/.auth/storage-state.json' })
    console.log('✅ 测试认证状态已保存到 e2e/.auth/storage-state.json')

  } catch (error) {
    console.error('❌ 设置测试环境失败:', error)
  } finally {
    await browser.close()
  }
}

export default globalSetup
