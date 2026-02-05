/**
 * E2E 测试 Fixtures
 * 提供测试用的辅助功能和认证处理
 */
import { test as base } from '@playwright/test'

type AuthFixtures = {
  authenticatedPage: Awaited<ReturnType<typeof authenticatePage>>
  skipAuth: void
}

/**
 * 创建已认证的页面
 * 在测试前设置认证状态并确保 Pinia store 正确初始化
 */
async function authenticatePage({ page }: { page: Parameters<typeof authenticatePage>[0] }) {
  // 首先访问首页触发 Vue 应用初始化
  await page.goto('/')

  // 等待 Vue 应用挂载
  await page.waitForSelector('#app', { timeout: 5000 })

  // 在页面上下文中设置认证状态
  await page.evaluate(() => {
    // 设置 localStorage
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

    localStorage.setItem('access_token', testData.access_token)
    localStorage.setItem('refresh_token', testData.refresh_token)
    localStorage.setItem('user', testData.user)

    // 触发自定义事件通知 Pinia store 更新
    window.dispatchEvent(new Event('storage'))

    return testData
  })

  // 等待一下让状态生效
  await page.waitForTimeout(100)

  return page
}

export const test = base.extend<AuthFixtures>({
  // 已认证的页面 fixture
  authenticatedPage: async ({ page }, use) => {
    await authenticatePage({ page })
    await use(page)
  },

  // 跳过认证的标记 fixture（用于测试登录页面本身）
  skipAuth: async ({}, use) => {
    await use()
  }
})

export { expect } from '@playwright/test'
