/**
 * 测试辅助函数 - 设置认证状态
 */
import { test as base, expect, type Page } from '@playwright/test'

// 扩展 test 类型以包含认证设置
export const test = base.extend<{
  authenticatedPage: Page
}>({
  authenticatedPage: async ({ page }, use) => {
    // 导航到页面
    await page.goto('/')

    // 手动设置认证状态
    await page.evaluate(() => {
      const userData = {
        id: 'test-user-id',
        username: 'test-teacher',
        email: 'teacher@test.com',
        role: 'teacher',
        organization_id: 'test-org-id'
      }

      localStorage.setItem('user', JSON.stringify(userData))
      localStorage.setItem('access_token', 'test-token-' + Date.now())
      localStorage.setItem('refresh_token', 'test-refresh-token-' + Date.now())
    })

    // 刷新页面以应用更改
    await page.reload()

    await use(page)
  }
})

export { expect }
