/**
 * 路由测试 - 验证路由配置是否正确
 */
import { test, expect } from '@playwright/test'

test('路由测试 - 验证题目编辑器路由', async ({ page }) => {
  // 测试不同的路由
  const routes = [
    '/teacher/question-banks/test-bank/questions/new',
    '/teacher/question-banks/abc123/questions/new',
    '/teacher/question-banks/1/questions/new'
  ]

  for (const route of routes) {
    console.log(`测试路由: ${route}`)
    await page.goto(route)
    await page.waitForLoadState('networkidle')

    console.log(`  当前 URL: ${page.url()}`)

    // 检查页面标题
    const title = await page.title()
    console.log(`  页面标题: ${title}`)

    // 检查是否有题目编辑器相关的元素
    const hasEditor = await page.locator('.question-editor, .el-form').count() > 0
    const hasBankDetail = await page.locator('text=题库详情').count() > 0

    console.log(`  有编辑器: ${hasEditor}, 有题库详情: ${hasBankDetail}`)
  }
})

test('路由测试 - 直接访问测试路由', async ({ page }) => {
  // 使用一个更具体的路由
  await page.goto('/teacher/question-banks/bank-001/questions/new')
  await page.waitForLoadState('networkidle')

  console.log('当前 URL:', page.url())

  // 截图
  await page.screenshot({ path: 'test-results/route-test-screenshot.png' })

  // 检查 URL 是否包含预期路径
  const url = page.url()
  const hasQuestionsNew = url.includes('/questions/new')
  const hasBankDetail = url.includes('/test-bank') && !url.includes('/questions')

  console.log('URL 包含 /questions/new:', hasQuestionsNew)
  console.log('URL 是题库详情:', hasBankDetail)

  expect(hasQuestionsNew).toBe(true)
})
