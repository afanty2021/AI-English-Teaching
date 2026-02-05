/**
 * 题目编辑器高级 E2E 测试
 * 使用辅助函数和测试数据生成器
 */
import { test, expect } from '@playwright/test'
import {
  QuestionEditorHelper,
  TestDataGenerator,
  AuthHelper,
  WaitHelper,
  ScreenshotHelper,
  QuestionType,
  QuestionDifficulty
} from './helpers'

/**
 * 使用辅助函数的测试组
 */
test.describe('题目编辑器 - 高级功能测试', () => {
  let editorHelper: QuestionEditorHelper

  test.beforeEach(async ({ page }) => {
    editorHelper = new QuestionEditorHelper(page)
    await editorHelper.gotoNewQuestion()
  })

  test('使用辅助函数创建选择题', async ({ page }) => {
    // 使用测试数据生成器
    const testData = TestDataGenerator.choiceQuestion()

    // 填写标题
    await editorHelper.fillTitle(testData.title)

    // 选择题型
    await editorHelper.selectQuestionType('单选题')

    // 等待编辑器准备就绪
    await editorHelper.waitForEditorReady()

    // 验证选择题编辑器可见
    const isVisible = await editorHelper.isEditorVisible('choice-editor')
    expect(isVisible).toBe(true)

    // 截图记录
    await ScreenshotHelper.step(page, 'choice-editor-loaded')
  })

  test('使用辅助函数创建填空题', async ({ page }) => {
    const testData = TestDataGenerator.fillBlankQuestion()

    await editorHelper.fillTitle(testData.title)
    await editorHelper.selectQuestionType('填空题')

    await editorHelper.waitForEditorReady()

    const isVisible = await editorHelper.isEditorVisible('fill-blank-editor')
    expect(isVisible).toBe(true)
  })

  test('使用辅助函数选择难度', async ({ page }) => {
    await editorHelper.selectDifficulty('中等')

    // 等待选择生效
    await page.waitForTimeout(500)

    // 可以添加验证逻辑
  })
})

/**
 * 表单验证测试组
 */
test.describe('题目编辑器 - 表单验证', () => {
  test('应该验证必填字段', async ({ page }) => {
    const editorHelper = new QuestionEditorHelper(page)
    await editorHelper.gotoNewQuestion()

    // 不填写任何内容，直接保存
    await editorHelper.clickSave()

    // 等待验证提示
    await page.waitForTimeout(500)

    // 获取错误消息
    const errors = await editorHelper.getErrorMessages()

    // 应该有错误消息（具体数量取决于验证规则）
    expect(errors.length).toBeGreaterThan(0)

    // 截图记录失败场景
    await ScreenshotHelper.onFailure(page, 'validation-errors')
  })

  test('应该验证选择题选项内容', async ({ page }) => {
    const editorHelper = new QuestionEditorHelper(page)
    await editorHelper.gotoNewQuestion()

    // 选择选择题
    await editorHelper.selectQuestionType('单选题')
    await editorHelper.waitForEditorReady()

    // 填写标题
    await editorHelper.fillTitle('测试选择题')

    // 不填写选项内容，直接保存
    await editorHelper.clickSave()

    // 等待验证
    await page.waitForTimeout(500)

    // 应该有验证错误
    const errors = await editorHelper.getErrorMessages()
    expect(errors.length).toBeGreaterThan(0)
  })
})

/**
 * 等待条件测试
 */
test.describe('题目编辑器 - 异步操作', () => {
  test('应该等待编辑器组件加载', async ({ page }) => {
    await page.goto('/teacher/question-banks/test-bank/questions/new')

    // 使用等待辅助函数
    const isReady = await WaitHelper.waitForVisible(page, '.question-editor', 5000)

    expect(isReady).toBe(true)
  })

  test('应该等待题型切换完成', async ({ page }) => {
    const editorHelper = new QuestionEditorHelper(page)
    await editorHelper.gotoNewQuestion()

    // 选择题型
    await editorHelper.selectQuestionType('阅读理解')

    // 等待对应编辑器出现
    const isReadingEditorVisible = await WaitHelper.waitForVisible(page, '.reading-editor', 3000)

    expect(isReadingEditorVisible).toBe(true)
  })
})

/**
 * 页面导航测试
 */
test.describe('题目编辑器 - 页面导航', () => {
  test('应该能从题库页面导航到新建题目', async ({ page }) => {
    // 从题库详情页开始
    await page.goto('/teacher/question-banks/test-bank')
    await page.waitForLoadState('networkidle')

    // 点击新建题目按钮（如果存在）
    const createButton = page.locator('button:has-text("新建题目")').first()

    if (await createButton.count() > 0) {
      await createButton.click()

      // 验证对话框或页面跳转
      await page.waitForTimeout(500)

      const dialogVisible = await page.locator('.el-dialog').count() > 0
      const urlChanged = page.url().includes('/questions/new')

      expect(dialogVisible || urlChanged).toBe(true)
    }
  })

  test('应该能从题目列表跳转到编辑页面', async ({ page }) => {
    // 假设从题库详情页有题目列表
    await page.goto('/teacher/question-banks/test-bank')
    await page.waitForLoadState('networkidle')

    // 查找编辑按钮
    const editButtons = page.locator('button:has-text("编辑")')

    if (await editButtons.count() > 0) {
      await editButtons.first().click()

      // 验证 URL 变化
      const urlChanged = await WaitHelper.waitForUrlChange(page, /\/teacher\/questions\/[a-zA-Z0-9-]+/, 3000)

      expect(urlChanged).toBe(true)
    }
  })
})

/**
 * 批量操作测试
 */
test.describe('题目编辑器 - 批量操作', () => {
  test('应该能打开批量导入对话框', async ({ page }) => {
    await page.goto('/teacher/question-banks/test-bank')
    await page.waitForLoadState('networkidle')

    // 查找批量导入按钮
    const importButton = page.locator('button:has-text("批量导入")').first()

    if (await importButton.count() > 0) {
      await importButton.click()

      // 等待对话框出现
      const dialogVisible = await WaitHelper.waitForVisible(page, '.el-dialog', 3000)

      expect(dialogVisible).toBe(true)
    }
  })

  test('应该能在 JSON 和 Excel 导入之间切换', async ({ page }) => {
    await page.goto('/teacher/question-banks/test-bank')
    await page.waitForLoadState('networkidle')

    const importButton = page.locator('button:has-text("批量导入")').first()

    if (await importButton.count() > 0) {
      await importButton.click()

      // 点击 JSON 标签
      const jsonTab = page.locator('text=JSON').first()
      if (await jsonTab.count() > 0) {
        await jsonTab.click()
        await page.waitForTimeout(200)

        // 验证 JSON 输入区域可见
        const jsonInputVisible = await page.locator('textarea').count() > 0
        expect(jsonInputVisible).toBe(true)

        // 点击 Excel 标签
        const excelTab = page.locator('text=Excel').first()
        if (await excelTab.count() > 0) {
          await excelTab.click()
          await page.waitForTimeout(200)

          // 验证上传区域可见
          const uploadVisible = await page.locator('.el-upload').count() > 0
          expect(uploadVisible).toBe(true)
        }
      }
    }
  })
})

/**
 * 用户体验测试
 */
test.describe('题目编辑器 - 用户体验', () => {
  test('应该支持键盘导航', async ({ page }) => {
    const editorHelper = new QuestionEditorHelper(page)
    await editorHelper.gotoNewQuestion()

    // 使用 Tab 键导航
    await page.keyboard.press('Tab')
    await page.keyboard.press('Tab')

    // 聚焦的元素应该是可聚焦的表单元素
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName)

    expect(['INPUT', 'TEXTAREA', 'SELECT', 'BUTTON']).toContain(focusedElement)
  })

  test('应该提供视觉反馈', async ({ page }) => {
    const editorHelper = new QuestionEditorHelper(page)
    await editorHelper.gotoNewQuestion()

    // 聚焦标题输入框
    const titleInput = page.locator('input[type="text"]').first()
    await titleInput.focus()

    // 检查是否有焦点样式（Element Plus 通常添加 focus 类）
    const hasFocus = await titleInput.evaluate(el =>
      el.classList.contains('is-focus') || document.activeElement === el
    )

    expect(hasFocus).toBe(true)
  })
})
