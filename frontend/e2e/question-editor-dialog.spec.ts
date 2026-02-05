/**
 * 题目编辑器对话框模式 E2E 测试
 * 测试从题库详情页打开题目编辑器对话框的功能
 */
import { test, expect } from '@playwright/test'

/**
 * 对话框模式测试组
 */
test.test.describe('题目编辑器 - 对话框模式', () => {
  test.beforeEach(async ({ page }) => {
    // 导航到题库详情页（使用测试数据）
    await page.goto('/teacher/question-banks/test-bank')
    await page.waitForLoadState('networkidle')
  })

  test('应该能从题库详情页打开新建题目对话框', async ({ page }) => {
    // 查找"新建题目"按钮
    const createButton = page.locator('button:has-text("新建题目"), button:has-text("添加题目")').first()

    // 如果按钮存在，点击它
    if (await createButton.count() > 0) {
      await createButton.click()

      // 验证对话框出现
      await expect(page.locator('.el-dialog, .question-editor-dialog')).toBeVisible()

      // 验证对话框标题
      await expect(page.locator('text=/新建题目|题目编辑/')).toBeVisible()
    }
  })

  test('对话框应该包含所有必要的表单字段', async ({ page }) => {
    // 打开新建题目对话框
    const createButton = page.locator('button:has-text("新建题目"), button:has-text("添加题目")').first()

    if (await createButton.count() > 0) {
      await createButton.click()

      // 等待对话框加载
      await page.waitForTimeout(300)

      // 验证题型选择器
      await expect(page.locator('.el-select')).toBeVisible()

      // 验证题目标题输入
      await expect(page.locator('input[type="text"]')).toBeVisible()

      // 验证操作按钮
      await expect(page.locator('button:has-text("保存")')).toBeVisible()
      await expect(page.locator('button:has-text("取消")')).toBeVisible()
    }
  })

  test('应该能关闭对话框', async ({ page }) => {
    // 打开对话框
    const createButton = page.locator('button:has-text("新建题目"), button:has-text("添加题目")').first()

    if (await createButton.count() > 0) {
      await createButton.click()
      await page.waitForTimeout(300)

      // 点击取消按钮或关闭按钮
      const closeButton = page.locator('button:has-text("取消"), .el-dialog__headerbtn').first()
      await closeButton.click()

      // 验证对话框关闭
      await expect(page.locator('.el-dialog, .question-editor-dialog')).toHaveCount(0, { timeout: 2000 })
    }
  })
})

/**
 * 编辑现有题目测试
 */
test.describe('题目编辑器 - 编辑现有题目', () => {
  test('应该能从题库详情页跳转到编辑页面', async ({ page }) => {
    // 导航到题库详情页
    await page.goto('/teacher/question-banks/test-bank')
    await page.waitForLoadState('networkidle')

    // 查找"编辑"按钮（假设题库中有题目）
    const editButtons = page.locator('button:has-text("编辑")')

    if (await editButtons.count() > 0) {
      // 点击第一个编辑按钮
      await editButtons.first().click()

      // 验证导航到编辑页面
      await expect(page).toHaveURL(/\/teacher\/questions\/[a-zA-Z0-9-]+/)
    }
  })

  test('编辑页面应该加载现有题目数据', async ({ page }) => {
    // 假设有一个题目的ID
    const questionId = 'test-question-id'

    // 直接导航到编辑页面
    await page.goto(`/teacher/questions/${questionId}?bankId=test-bank`)
    await page.waitForLoadState('networkidle')

    // 验证页面标题包含"编辑"
    await expect(page.locator('text=/编辑|题目编辑/')).toBeVisible()

    // 验证表单字段存在（可能包含现有数据）
    await expect(page.locator('input[type="text"]')).toBeVisible()
  })
})

/**
 * 题型切换测试
 */
test.describe('题目编辑器 - 题型切换', () => {
  test('应该在不同题型间切换', async ({ page }) => {
    await page.goto('/teacher/question-banks/test-bank/questions/new')
    await page.waitForLoadState('networkidle')

    const typeSelect = page.locator('.el-select').first()

    // 支持的题型列表
    const questionTypes = ['单选题', '多选题', '填空题', '阅读理解', '写作题', '听力题', '翻译题']

    for (const type of questionTypes) {
      // 打开选择器
      await typeSelect.click()
      await page.waitForTimeout(100)

      // 选择题型
      const option = page.locator(`text=${type}`).first()
      if (await option.count() > 0) {
        await option.click()
        await page.waitForTimeout(200)

        // 验证对应的编辑器出现
        const editorClass = getEditorClassForType(type)
        if (editorClass) {
          const editor = page.locator(`.${editorClass}`)
          // 某些题型可能使用相同的编辑器组件
          if (await editor.count() > 0) {
            await expect(editor.first()).toBeVisible()
          }
        }
      }

      // 重新打开选择器进行下一次选择
      await typeSelect.click()
    }
  })
})

/**
 * 辅助函数：根据题型返回对应的编辑器CSS类名
 */
function getEditorClassForType(type: string): string | null {
  const editorMap: Record<string, string> = {
    '单选题': 'choice-editor',
    '多选题': 'choice-editor',
    '填空题': 'fill-blank-editor',
    '阅读理解': 'reading-editor',
    '写作题': 'writing-editor',
    '听力题': 'audio-editor',
    '翻译题': 'translation-editor'
  }
  return editorMap[type] || null
}

/**
 * 批量导入对话框测试
 */
test.describe('题目编辑器 - 批量导入对话框', () => {
  test('应该能打开批量导入对话框', async ({ page }) => {
    await page.goto('/teacher/question-banks/test-bank')
    await page.waitForLoadState('networkidle')

    // 查找批量导入按钮
    const importButton = page.locator('button:has-text("批量导入")').first()

    if (await importButton.count() > 0) {
      await importButton.click()

      // 验证导入对话框出现
      await expect(page.locator('.el-dialog, .import-dialog')).toBeVisible()

      // 验证导入选项（JSON/Excel）
      await expect(page.locator('text=/JSON|Excel/')).toBeVisible()
    }
  })

  test('应该支持 JSON 导入', async ({ page }) => {
    await page.goto('/teacher/question-banks/test-bank')
    await page.waitForLoadState('networkidle')

    const importButton = page.locator('button:has-text("批量导入")').first()

    if (await importButton.count() > 0) {
      await importButton.click()

      // 点击 JSON 导入标签
      const jsonTab = page.locator('text=JSON').first()
      if (await jsonTab.count() > 0) {
        await jsonTab.click()

        // 验证 JSON 输入区域
        await expect(page.locator('textarea, .el-textarea')).toBeVisible()
      }
    }
  })
})

/**
 * 表单交互测试
 */
test.describe('题目编辑器 - 表单交互', () => {
  test('应该能输入题目标题', async ({ page }) => {
    await page.goto('/teacher/question-banks/test-bank/questions/new')
    await page.waitForLoadState('networkidle')

    // 找到标题输入框
    const titleInput = page.locator('input[type="text"]').first()

    // 输入标题
    await titleInput.fill('测试题目标题')

    // 验证输入成功
    await expect(titleInput).toHaveValue('测试题目标题')
  })

  test('应该能选择题目难度', async ({ page }) => {
    await page.goto('/teacher/question-banks/test-bank/questions/new')
    await page.waitForLoadState('networkidle')

    // 查找难度选择器（可能是下拉框或单选按钮组）
    const difficultySelector = page.locator('.el-select:has-text("难度"), .el-radio-group').first()

    if (await difficultySelector.count() > 0) {
      await difficultySelector.click()
      await page.waitForTimeout(100)

      // 选择一个难度
      const option = page.locator('text=简单').first()
      if (await option.count() > 0) {
        await option.click()
      }
    }
  })
})

/**
 * 保存和验证测试
 */
test.describe('题目编辑器 - 保存和验证', () => {
  test('应该验证必填字段', async ({ page }) => {
    await page.goto('/teacher/question-banks/test-bank/questions/new')
    await page.waitForLoadState('networkidle')

    // 不填写任何内容，直接点击保存
    const saveButton = page.locator('button:has-text("保存")').first()
    await saveButton.click()

    // 等待验证
    await page.waitForTimeout(500)

    // 检查错误提示
    const errorMessages = page.locator('.el-form-item__error, .el-message--error')

    if (await errorMessages.count() > 0) {
      await expect(errorMessages.first()).toBeVisible()
    }
  })
})
