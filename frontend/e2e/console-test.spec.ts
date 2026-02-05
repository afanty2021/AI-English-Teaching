/**
 * 控制台错误检查
 */
import { test, expect } from '@playwright/test'

test('控制台检查 - 查看浏览器错误', async ({ page }) => {
  // 监听控制台消息
  const errors: string[] = []
  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(msg.text())
      console.log('Console Error:', msg.text())
    }
  })

  // 监听页面错误
  const pageErrors: string[] = []
  page.on('pageerror', error => {
    pageErrors.push(error.toString())
    console.log('Page Error:', error.toString())
  })

  await page.goto('/teacher/question-banks/test-bank/questions/new')

  // 等待
  await page.waitForLoadState('domcontentloaded')
  await page.waitForTimeout(2000)

  console.log('Total console errors:', errors.length)
  console.log('Total page errors:', pageErrors.length)

  // 检查 #app 元素
  const appContent = await page.evaluate(() => {
    const app = document.querySelector('#app')
    return {
      exists: !!app,
      innerHTML: app?.innerHTML || '',
      hasChildren: app?.children.length || 0
    }
  })

  console.log('App element:', appContent)
})
