/**
 * E2E 测试全局认证设置
 * 为测试环境配置模拟的已登录状态
 */
import { test as base } from '@playwright/test'

export const test = base.extend<{
  authenticatedPage: typeof base.prototype.page
}>({
  authenticatedPage: async ({ page }, use) => {
    // 设置模拟的认证状态
    await page.goto('/')

    // 在 localStorage 中设置认证状态
    await page.evaluate(() => {
      localStorage.setItem('access_token', 'test-token-' + Date.now())
      localStorage.setItem('refresh_token', 'test-refresh-token-' + Date.now())
      localStorage.setItem('user', JSON.stringify({
        id: 'test-user-id',
        username: 'test-teacher',
        email: 'teacher@test.com',
        role: 'teacher',
        organization_id: 'test-org-id'
      }))
    })

    // 重新加载页面，让认证状态生效
    await page.goto('/')

    await use(page)
  }
})

export { expect } from '@playwright/test'
