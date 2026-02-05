/**
 * 改进的题目编辑器 E2E 测试
 * 修复认证状态和测试稳定性问题
 */
import { test, expect } from '@playwright/test'
import { setupTestAuth, verifyAuth } from './auth-helpers'

test.describe('题目编辑器 - 修复版测试', () => {
  test.beforeEach(async ({ page }) => {
    // 设置认证状态
    await setupTestAuth(page)

    // 验证认证状态
    await verifyAuth(page)
  })

  test('应该显示题目编辑器界面', async ({ page }) => {
    // 导航到题目编辑器页面
    await page.goto('/teacher/question-banks/test-bank/questions/new')
    await page.waitForLoadState('networkidle')

    // 检查页面标题
    const title = await page.title()
    expect(title).toContain('新建题目')

    // 检查页面元素
    const pageHeader = page.locator('.el-page-header')
    await expect(pageHeader).toBeVisible()

    const questionForm = page.locator('.question-form')
    await expect(questionForm).toBeVisible()

    const questionTypeSelect = page.locator('.el-select').first()
    await expect(questionTypeSelect).toBeVisible()

    console.log('✅ 题目编辑器界面显示正常')
  })

  test('应该切换题目类型', async ({ page }) => {
    await page.goto('/teacher/question-banks/test-bank/questions/new')
    await page.waitForLoadState('networkidle')

    // 点击题型选择器
    const typeSelect = page.locator('.el-select').first()
    await expect(typeSelect).toBeVisible()

    // 点击选择框
    await typeSelect.click()
    await page.waitForTimeout(300)

    // 选择填空题
    const fillBlankOption = page.locator('text=填空题').first()
    await fillBlankOption.click()

    await page.waitForTimeout(300)

    // 检查是否显示填空题编辑器
    const fillBlankEditor = page.locator('.fill-blank-editor')
    await expect(fillBlankEditor).toBeVisible()

    console.log('✅ 题型切换成功')
  })

  test('应该显示选择题编辑器', async ({ page }) => {
    await page.goto('/teacher/question-banks/test-bank/questions/new')
    await page.waitForLoadState('networkidle')

    // 验证选择题编辑器显示（默认是选择题）
    const choiceEditor = page.locator('.choice-editor')
    await expect(choiceEditor).toBeVisible()

    // 检查四个选项
    await expect(page.locator('text=/选项.*A/')).toBeVisible()
    await expect(page.locator('text=/选项.*B/')).toBeVisible()
    await expect(page.locator('text=/选项.*C/')).toBeVisible()
    await expect(page.locator('text=/选项.*D/')).toBeVisible()

    console.log('✅ 选择题编辑器显示正常')
  })
})
