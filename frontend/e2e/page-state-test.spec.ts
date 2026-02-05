/**
 * 页面状态测试 - 检查页面实际渲染内容
 */
import { test, expect } from '@playwright/test'

test('页面状态测试 - 检查页面内容', async ({ page }) => {
  await page.goto('/teacher/question-banks/test-bank/questions/new')

  // 等待页面加载
  await page.waitForLoadState('domcontentloaded')
  await page.waitForTimeout(1000)

  console.log('当前 URL:', page.url())

  // 获取页面文本内容
  const pageText = await page.evaluate(() => document.body.innerText)
  console.log('页面文本:', pageText.substring(0, 200))

  // 检查 DOM 结构
  const domInfo = await page.evaluate(() => {
    const app = document.querySelector('#app')
    if (!app) return { error: 'No #app element' }

    return {
      innerHTML: app.innerHTML.substring(0, 500),
      childrenCount: app.children.length,
      firstChild: app.firstElementChild?.className
    }
  })
  console.log('DOM Info:', domInfo)

  // 截图
  await page.screenshot({ path: 'test-results/page-state-screenshot.png', fullPage: true })

  // 检查是否有任何可见内容
  const hasContent = await page.locator('#app > *').count() > 0
  console.log('Has content in #app:', hasContent)
})
