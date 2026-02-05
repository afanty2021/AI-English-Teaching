/**
 * 认证辅助函数 - 确保测试环境中的认证状态正确
 */
import { type Page } from '@playwright/test'

/**
 * 设置测试认证状态
 */
export async function setupTestAuth(page: Page) {
  // 导航到首页
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
  await page.waitForLoadState('networkidle')

  // 等待路由守卫完成
  await page.waitForTimeout(1000)
}

/**
 * 验证认证状态
 */
export async function verifyAuth(page: Page) {
  // 检查当前URL
  const currentUrl = page.url()
  console.log('当前URL:', currentUrl)

  // 检查是否在登录页面
  const isLoginPage = currentUrl.includes('/login') || currentUrl.includes('login')
  if (isLoginPage) {
    throw new Error('认证失败，仍在登录页面')
  }

  // 检查localStorage中的用户数据
  const userData = await page.evaluate(() => {
    return {
      user: localStorage.getItem('user'),
      accessToken: localStorage.getItem('access_token'),
      refreshToken: localStorage.getItem('refresh_token')
    }
  })

  if (!userData.user || !userData.accessToken) {
    throw new Error('认证数据缺失')
  }

  console.log('✅ 认证状态验证通过')
}
