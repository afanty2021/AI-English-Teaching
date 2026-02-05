/**
 * 测试认证设置 - 验证 Playwright storageState 是否工作
 */
import { test, expect } from '@playwright/test'

test('认证测试 - storageState 应该提供认证', async ({ page }) => {
  console.log('当前页面 URL:', page.url())

  // 直接访问教师端页面（使用 storageState 中保存的认证状态）
  await page.goto('/teacher/question-banks/test-bank/questions/new')

  // 等待页面加载
  await page.waitForLoadState('networkidle')

  console.log('导航后 URL:', page.url())

  // 截图查看实际状态
  await page.screenshot({ path: 'test-results/auth-test-storage-state.png' })

  // 检查是否被重定向到登录页
  const isLoginPage = page.url().includes('/login')
  const hasLoginForm = await page.locator('input[placeholder*="用户名"]').count() > 0

  console.log('Is Login Page:', isLoginPage)
  console.log('Has Login Form:', hasLoginForm)

  // 如果是登录页，测试失败
  if (isLoginPage || hasLoginForm) {
    console.log('❌ storageState 认证失败')
  } else {
    console.log('✅ storageState 认证成功')
  }

  // 断言：不应该在登录页
  expect(isLoginPage).toBe(false)
})
