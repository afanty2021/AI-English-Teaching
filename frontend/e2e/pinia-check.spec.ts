/**
 * 检查 Pinia store 状态
 */
import { test, expect } from '@playwright/test'

test('检查 Pinia store 状态', async ({ page }) => {
  // 先设置 localStorage
  await page.goto('/')

  await page.evaluate(() => {
    localStorage.setItem('access_token', 'test-token')
    localStorage.setItem('user', JSON.stringify({
      id: 'test-user-id',
      username: 'test-teacher',
      email: 'test@test.com',
      role: 'teacher'
    }))
  })

  // 重新加载页面以触发 Pinia 初始化
  await page.reload()

  // 等待页面加载
  await page.waitForLoadState('networkidle')

  console.log('After reload URL:', page.url())

  // 检查 Pinia store 状态
  const storeInfo = await page.evaluate(() => {
    // @ts-ignore
    const app = document.querySelector('#app')?.__vue_app__
    return {
      hasVueApp: !!app,
      // 尝试访问 pinia
      hasPinia: !!(window as any).__PINIA__
    }
  })

  console.log('Store info:', storeInfo)

  // 截图
  await page.screenshot({ path: 'test-results/pinia-store-check.png' })
})
