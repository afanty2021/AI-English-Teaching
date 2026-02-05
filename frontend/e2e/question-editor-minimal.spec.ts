/**
 * 最小化题目编辑器测试
 */
import { test, expect, type Page } from '@playwright/test'

test('题目编辑器 - 页面加载', async ({ page }) => {
  // 设置认证状态
  await page.goto('/')
  await page.evaluate(() => {
    const userData = {
      id: 'test-user-id',
      username: 'test-teacher',
      email: 'teacher@test.com',
      role: 'teacher',
      organization_id: 'test-org-id'
    }
    localStorage.setItem('user', JSON.stringify(userData))
    localStorage.setItem('access_token', 'test-token')
    localStorage.setItem('refresh_token', 'test-refresh-token')
  })

  // 导航到题目编辑器页面
  await page.goto('/teacher/question-banks/test-bank/questions/new')
  await page.waitForLoadState('networkidle')

  // 等待路由跳转完成
  await page.waitForTimeout(1000)

  // 检查页面标题
  const title = await page.title()
  console.log('页面标题:', title)

  // 检查页面元素
  const hasForm = await page.locator('form').count()
  console.log('表单数量:', hasForm)

  const hasSelect = await page.locator('.el-select').count()
  console.log('选择器数量:', hasSelect)

  // 截图保存当前状态
  await page.screenshot({ path: 'test-results/question-editor-check.png' })
})

test('题目编辑器 - 题型切换', async ({ page }) => {
  await page.goto('/')
  await page.evaluate(() => {
    const userData = {
      id: 'test-user-id',
      username: 'test-teacher',
      email: 'teacher@test.com',
      role: 'teacher',
      organization_id: 'test-org-id'
    }
    localStorage.setItem('user', JSON.stringify(userData))
    localStorage.setItem('access_token', 'test-token')
    localStorage.setItem('refresh_token', 'test-refresh-token')
  })

  await page.goto('/teacher/question-banks/test-bank/questions/new')
  await page.waitForLoadState('networkidle')
  await page.waitForTimeout(1000)

  // 点击题型选择器
  const select = page.locator('.el-select').first()
  await select.click()
  await page.waitForTimeout(300)

  // 选择填空题
  const option = page.locator('text=填空题').first()
  await option.click()
  await page.waitForTimeout(300)

  // 检查是否切换成功
  const editor = page.locator('.fill-blank-editor')
  await expect(editor).toBeVisible()
})
