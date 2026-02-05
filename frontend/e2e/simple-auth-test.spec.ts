/**
 * 简单认证测试 - 验证路由守卫修复
 */
import { test, expect } from '@playwright/test'

test('认证状态修复验证', async ({ page }) => {
  // 1. 导航到首页
  await page.goto('/')
  await page.waitForLoadState('networkidle')

  // 2. 检查当前页面状态
  const initialUrl = page.url()
  console.log('初始URL:', initialUrl)

  // 3. 设置认证数据（模拟存储状态）
  await page.evaluate(() => {
    localStorage.setItem('user', JSON.stringify({
      id: 'test-user-id',
      username: 'test-teacher',
      email: 'teacher@test.com',
      role: 'teacher',
      organization_id: 'test-org-id'
    }))
    localStorage.setItem('access_token', 'test-token-' + Date.now())
    localStorage.setItem('refresh_token', 'test-refresh-token-' + Date.now())
  })

  // 4. 等待路由守卫重新检查（给时间让重试机制生效）
  await page.waitForTimeout(3000)

  // 5. 访问题目编辑器页面
  await page.goto('/teacher/question-banks/test-bank/questions/new')
  await page.waitForLoadState('networkidle')

  // 6. 等待页面加载和路由跳转
  await page.waitForTimeout(2000)

  // 7. 检查结果
  const finalUrl = page.url()
  console.log('最终URL:', finalUrl)

  // 验证是否成功访问
  if (finalUrl.includes('/teacher/question-banks/test-bank/questions/new')) {
    console.log('✅ 成功访问题目编辑器页面')

    // 检查页面元素
    const hasPageHeader = await page.locator('.el-page-header').count()
    console.log('页面标题栏数量:', hasPageHeader)

    expect(hasPageHeader).toBeGreaterThan(0)
  } else {
    // 记录当前状态用于调试
    const pageTitle = await page.title()
    console.log('页面标题:', pageTitle)
    console.log('仍在:', finalUrl)

    // 如果仍在登录页面，尝试另一种方法
    if (finalUrl.includes('/login')) {
      console.log('仍在登录页面，尝试手动导航')

      // 直接修改 URL 并刷新
      await page.evaluate(() => {
        window.location.href = '/teacher/question-banks/test-bank/questions/new'
      })

      await page.waitForTimeout(3000)
      const retryUrl = page.url()
      console.log('重试后URL:', retryUrl)

      if (retryUrl.includes('/teacher/question-banks/test-bank/questions/new')) {
        console.log('✅ 重试后成功访问')
        expect(true).toBe(true) // 测试通过
      } else {
        console.log('❌ 重试后仍无法访问')
        expect(false).toBe(true) // 测试失败
      }
    } else {
      expect(finalUrl).toContain('/teacher/question-banks/test-bank/questions/new')
    }
  }
})
