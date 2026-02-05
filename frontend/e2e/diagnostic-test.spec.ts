/**
 * 诊断测试 - 检查 Pinia store 状态
 */
import { test, expect } from '@playwright/test'

test('诊断测试 - 检查认证和角色状态', async ({ page }) => {
  // 访问教师端页面
  await page.goto('/teacher/question-banks/test-bank/questions/new')

  // 等待页面加载
  await page.waitForLoadState('networkidle')

  console.log('当前 URL:', page.url())

  // 截图
  await page.screenshot({ path: 'test-results/diagnostic-screenshot.png' })

  // 在浏览器上下文中检查 Pinia store 状态
  const storeState = await page.evaluate(() => {
    // @ts-ignore - 访问 window 上的 Vue 应用实例
    const app = window.__VUE_APP__ || document.querySelector('#app')?.__vue_app__

    // 检查 localStorage
    const localStorageData = {
      access_token: localStorage.getItem('access_token'),
      refresh_token: localStorage.getItem('refresh_token'),
      user: localStorage.getItem('user')
    }

    return {
      url: window.location.href,
      localStorage: localStorageData,
      hasVueApp: !!app
    }
  })

  console.log('Store State:', JSON.stringify(storeState, null, 2))

  // 检查是否在首页
  const isHomePage = page.url().endsWith('/') || page.url().endsWith('/#')
  const isLoginPage = page.url().includes('/login')
  const isTargetPage = page.url().includes('/teacher/question-banks')

  console.log('Is Home Page:', isHomePage)
  console.log('Is Login Page:', isLoginPage)
  console.log('Is Target Page:', isTargetPage)

  if (isHomePage) {
    console.log('⚠️ 被重定向到首页 - 可能是角色检查失败')
  } else if (isLoginPage) {
    console.log('❌ 被重定向到登录页 - 认证失败')
  } else if (isTargetPage) {
    console.log('✅ 成功到达目标页面')
  }

  // 至少应该不在登录页
  expect(isLoginPage).toBe(false)
})
