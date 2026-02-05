/**
 * 简化版题目编辑器测试
 */
import { test, expect } from './test-setup'

test.describe('题目编辑器 - 简化测试', () => {
  test('应该能够访问题目编辑器页面', async ({ authenticatedPage }) => {
    // 导航到题目编辑器页面
    await authenticatedPage.goto('/teacher/question-banks/test-bank/questions/new')

    // 等待页面加载
    await authenticatedPage.waitForLoadState('networkidle')

    // 检查页面标题
    const title = await authenticatedPage.title()
    expect(title).toContain('新建题目')

    // 检查页面元素
    const pageHeader = authenticatedPage.locator('.el-page-header')
    await expect(pageHeader).toBeVisible()

    // 检查题目类型选择器
    const questionTypeSelect = authenticatedPage.locator('.el-select').first()
    await expect(questionTypeSelect).toBeVisible()

    // 检查选择题编辑器
    const choiceEditor = authenticatedPage.locator('.choice-editor')
    await expect(choiceEditor).toBeVisible()

    // 检查四个选项
    const optionA = authenticatedPage.locator('text=/选项.*A/')
    await expect(optionA).toBeVisible()

    const optionB = authenticatedPage.locator('text=/选项.*B/')
    await expect(optionB).toBeVisible()

    console.log('✅ 题目编辑器页面加载成功')
  })

  test('应该能够切换题型', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/teacher/question-banks/test-bank/questions/new')
    await authenticatedPage.waitForLoadState('networkidle')

    // 点击题目类型选择器
    const typeSelect = authenticatedPage.locator('.el-select').first()
    await typeSelect.click()

    // 等待选项出现
    await authenticatedPage.waitForTimeout(200)

    // 选择填空题
    const fillBlankOption = authenticatedPage.locator('text=填空题').first()
    await fillBlankOption.click()

    await authenticatedPage.waitForTimeout(200)

    // 检查是否显示填空题编辑器
    const fillBlankEditor = authenticatedPage.locator('.fill-blank-editor')
    await expect(fillBlankEditor).toBeVisible()

    console.log('✅ 题型切换成功')
  })
})
