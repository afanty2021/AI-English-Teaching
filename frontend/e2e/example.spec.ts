/**
 * Playwright E2E 示例测试
 * 用于验证 Playwright 配置和基本功能
 */
import { test, expect } from '@playwright/test'

test.describe('基础功能测试', () => {
  test('页面基本导航测试', async ({ page }) => {
    // 导航到首页
    await page.goto('/')

    // 验证页面标题
    await expect(page).toHaveTitle(/AI 英语教学系统|English Teaching/)

    // 验证页面加载成功
    await page.waitForLoadState('networkidle')
  })

  test('登录页面可访问', async ({ page }) => {
    // 导航到登录页
    await page.goto('/login')

    // 验证登录表单存在
    await expect(page.locator('input[type="email"], input[type="text"]')).toBeVisible()

    // 验证登录按钮存在
    await expect(page.locator('button:has-text("登录"), button:has-text("Login")')).toBeVisible()
  })

  test('教师端路由可访问', async ({ page }) => {
    // 导航到教师端
    await page.goto('/teacher')

    // 页面可能重定向到登录或显示教师仪表板
    await page.waitForLoadState('networkidle')

    // 验证页面没有崩溃
    const errors = page.locator('.error, .error-page')
    await expect(errors).toHaveCount(0)
  })
})

test.describe('组件渲染测试', () => {
  test('Element Plus 组件正常渲染', async ({ page }) => {
    await page.goto('/')

    // 查找 Element Plus 组件类
    const elComponents = page.locator('[class*="el-"]')

    // 至少应该有一些 Element Plus 组件
    await expect(elComponents.first()).toBeVisible()
  })

  test('Vue 应用成功挂载', async ({ page }) => {
    await page.goto('/')

    // 检查 Vue 应用是否挂载（查找 #app 根元素）
    const appElement = page.locator('#app')

    // #app 元素应该存在
    await expect(appElement).toBeVisible()
  })
})
