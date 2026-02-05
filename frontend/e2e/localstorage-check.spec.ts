/**
 * 直接检查 localStorage 和路由守卫
 */
import { test, expect } from '@playwright/test'

test('直接检查 localStorage', async ({ page }) => {
  // 访问任意页面
  await page.goto('/')

  // 检查 localStorage 内容
  const localStore = await page.evaluate(() => {
    return {
      accessToken: localStorage.getItem('access_token'),
      user: localStorage.getItem('user'),
      keys: Object.keys(localStorage)
    }
  })

  console.log('LocalStorage:', localStore)

  // 尝试手动设置并导航
  await page.evaluate(() => {
    localStorage.setItem('access_token', 'manual-token-' + Date.now())
    localStorage.setItem('user', JSON.stringify({
      id: 'manual-user-id',
      username: 'manual-teacher',
      email: 'manual@test.com',
      role: 'teacher',
      organization_id: 'manual-org-id'
    }))
  })

  // 重新导航
  await page.goto('/teacher/question-banks/manual-bank/questions/new')
  await page.waitForLoadState('networkidle')

  console.log('After manual set, URL:', page.url())

  // 截图
  await page.screenshot({ path: 'test-results/manual-localstorage-test.png' })

  const url = page.url()
  const hasQuestionsNew = url.includes('/questions/new')
  const isLoginPage = url.includes('/login')

  console.log('Has questions/new:', hasQuestionsNew)
  console.log('Is login page:', isLoginPage)
})
