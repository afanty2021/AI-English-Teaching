/**
 * 首页测试 - 检查应用是否正常
 */
import { test, expect } from '@playwright/test'

test('首页测试 - 检查 Vue 应用是否正常', async ({ page }) => {
  // 监听错误
  const errors: string[] = []
  page.on('pageerror', error => {
    errors.push(error.toString())
    console.log('Error:', error.toString())
  })

  // 访问首页
  await page.goto('/')
  await page.waitForLoadState('domcontentloaded')
  await page.waitForTimeout(1000)

  console.log('首页 URL:', page.url())
  console.log('Errors:', errors)

  // 检查 #app 内容
  const appContent = await page.evaluate(() => {
    const app = document.querySelector('#app')
    return {
      innerHTML: app?.innerHTML?.substring(0, 200) || '',
      hasChildren: app?.children.length || 0
    }
  })

  console.log('首页 App 内容:', appContent)

  await page.screenshot({ path: 'test-results/homepage-screenshot.png' })
})

test('教师端首页测试', async ({ page }) => {
  await page.goto('/teacher')
  await page.waitForLoadState('domcontentloaded')
  await page.waitForTimeout(1000)

  console.log('教师端 URL:', page.url())

  const appContent = await page.evaluate(() => {
    const app = document.querySelector('#app')
    return {
      innerHTML: app?.innerHTML?.substring(0, 200) || '',
      hasChildren: app?.children.length || 0
    }
  })

  console.log('教师端 App 内容:', appContent)

  await page.screenshot({ path: 'test-results/teacher-screenshot.png' })
})
