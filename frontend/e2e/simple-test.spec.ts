/**
 * 简单测试题目编辑器页面
 */
import { test, expect } from '@playwright/test'

test.use({
  storageState: 'e2e/.auth/storage-state.json'
})

test('题目编辑器页面加载', async ({ page }) => {
  // 导航到页面
  await page.goto('/teacher/question-banks/test-bank/questions/new')

  // 等待页面加载
  await page.waitForLoadState('networkidle')

  // 手动设置用户数据（如果 storageState 没有加载）
  await page.evaluate(() => {
    const userData = {
      id: 'test-user-id',
      username: 'test-teacher',
      email: 'teacher@test.com',
      role: 'teacher',
      organization_id: 'test-org-id'
    };
    localStorage.setItem('user', JSON.stringify(userData));
  })

  // 刷新页面以应用 localStorage 更改
  await page.reload()
  await page.waitForLoadState('networkidle')

  // 检查页面标题
  const title = await page.title()
  console.log('页面标题:', title)

  // 检查页面内容
  const bodyText = await page.textContent('body')
  console.log('页面内容长度:', bodyText?.length)

  // 检查是否存在页面元素
  const hasPageHeader = await page.locator('.el-page-header').count()
  console.log('页面标题栏数量:', hasPageHeader)

  const hasForm = await page.locator('form').count()
  console.log('表单数量:', hasForm)

  // 检查所有文本内容
  const allText = await page.locator('*').allTextContents()
  console.log('页面所有文本内容前100个字符:', allText.join(' ').substring(0, 100))
})
