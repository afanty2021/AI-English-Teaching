/**
 * 教案导出功能 E2E 测试
 *
 * 测试场景:
 * 1. 完整导出流程 - 从选择教案到下载
 * 2. 模板创建和使用流程
 * 3. WebSocket 实时进度推送
 * 4. 多格式并发导出
 * 5. 错误处理和重试
 */

import { test, expect } from '@playwright/test'
import { AuthHelper } from './helpers'

/**
 * 教案导出测试套件
 */
test.describe('教案导出 E2E', () => {
  /**
   * 测试前准备 - 登录并导航到导出页面
   */
  test.beforeEach(async ({ page }) => {
    const authHelper = new AuthHelper(page)

    // 登录教师账号
    await authHelper.login('teacher@example.com', 'password123')

    // 等待跳转到仪表板
    await page.waitForURL('**/dashboard', { timeout: 10000 })
  })

  /**
   * 场景1: 完整导出流程
   * 1. 进入教案导出页面
   * 2. 选择教案
   * 3. 配置导出选项
   * 4. 开始导出
   * 5. 等待 WebSocket 进度更新
   * 6. 下载文件
   */
  test('完整导出流程 - Word格式', async ({ page }) => {
    // 1. 进入教案导出页面
    await page.goto('/teacher/lesson-export')
    await page.waitForLoadState('networkidle')

    // 2. 选择教案
    const addLessonButton = page.getByRole('button', { name: /添加教案|选择教案/ })
    await expect(addLessonButton).toBeVisible()
    await addLessonButton.click()

    // 等待教案列表对话框
    await page.waitForSelector('.el-dialog, .lesson-list', { timeout: 5000 })

    // 选择第一个教案
    const firstLesson = page.locator('.lesson-item, .lesson-card').first()
    await expect(firstLesson).toBeVisible()
    await firstLesson.click()

    // 确认选择
    const confirmButton = page.getByRole('button', { name: /确认|确定/ })
    await confirmButton.click()

    // 3. 配置导出选项 - 选择 Word 格式
    const wordFormatRadio = page.locator('input[value="word"], .el-radio-button:has-text("Word")')
    await expect(wordFormatRadio).toBeVisible()
    await wordFormatRadio.click()

    // 选择导出章节
    const overviewCheckbox = page.locator('input[value="overview"], .el-checkbox:has-text("课程概述")')
    await overviewCheckbox.check()

    const objectivesCheckbox = page.locator('input[value="objectives"], .el-checkbox:has-text("教学目标")')
    await objectivesCheckbox.check()

    // 4. 开始导出
    const exportButton = page.getByRole('button', { name: /开始导出|导出/ })
    await expect(exportButton).toBeVisible()
    await exportButton.click()

    // 5. 等待进度对话框出现
    await page.waitForSelector('.export-progress, .el-dialog:has-text("导出进度")', {
      timeout: 10000
    })

    // 6. 验证进度条可见
    const progressBar = page.locator('.el-progress, .progress-bar')
    await expect(progressBar).toBeVisible()

    // 等待进度更新（WebSocket 推送）
    await page.waitForFunction(() => {
      const progressElement = document.querySelector('.el-progress__text, .progress-text')
      if (progressElement) {
        const text = progressElement.textContent || ''
        const match = text.match(/(\d+)%/)
        return match && parseInt(match[1]) > 0
      }
      return false
    }, { timeout: 30000 })

    // 7. 等待导出完成
    await page.waitForSelector('.complete-actions, .el-button:has-text("立即下载")', {
      timeout: 60000
    })

    // 验证下载按钮可见
    const downloadButton = page.getByRole('button', { name: /立即下载|下载/ })
    await expect(downloadButton).toBeVisible()

    // 8. 点击下载并验证文件
    const downloadPromise = page.waitForEvent('download', { timeout: 10000 })
    await downloadButton.click()

    const download = await downloadPromise
    expect(download.suggestedFilename()).toMatch(/\.(docx|word)$/)

    // 关闭进度对话框
    const closeButton = page.getByRole('button', { name: /关闭/ })
    await closeButton.click()
  })

  /**
   * 场景2: PDF 格式导出
   */
  test('PDF格式导出', async ({ page }) => {
    await page.goto('/teacher/lesson-export')
    await page.waitForLoadState('networkidle')

    // 选择并导出为 PDF
    const addLessonButton = page.getByRole('button', { name: /添加教案/ })
    await addLessonButton.click()

    await page.waitForSelector('.lesson-item')
    await page.locator('.lesson-item').first().click()

    const confirmButton = page.getByRole('button', { name: /确认/ })
    await confirmButton.click()

    // 选择 PDF 格式
    const pdfFormatRadio = page.locator('input[value="pdf"], .el-radio-button:has-text("PDF")')
    await pdfFormatRadio.click()

    // 开始导出
    const exportButton = page.getByRole('button', { name: /开始导出/ })
    await exportButton.click()

    // 等待完成
    await page.waitForSelector('.complete-actions', { timeout: 60000 })

    // 验证下载文件格式
    const downloadButton = page.getByRole('button', { name: /立即下载/ })
    const downloadPromise = page.waitForEvent('download')
    await downloadButton.click()

    const download = await downloadPromise
    expect(download.suggestedFilename()).toMatch(/\.pdf$/)
  })

  /**
   * 场景3: 模板创建和使用流程
   */
  test('创建自定义模板并使用', async ({ page }) => {
    await page.goto('/teacher/lesson-export')
    await page.waitForLoadState('networkidle')

    // 1. 打开模板管理对话框
    const templateManagerButton = page.getByRole('button', { name: /管理模板/ })
    await templateManagerButton.click()

    // 等待模板管理对话框
    await page.waitForSelector('.el-dialog:has-text("模板管理")', { timeout: 5000 })

    // 2. 创建新模板
    const createTemplateButton = page.getByRole('button', { name: /新建模板|创建模板/ })
    await createTemplateButton.click()

    // 填写模板信息
    const templateNameInput = page.locator('input[name="name"], input[placeholder*="模板名称"]')
    await templateNameInput.fill('E2E测试模板')

    // 选择格式
    const formatSelect = page.locator('.el-select:has-text("格式")')
    await formatSelect.click()
    await page.locator('.el-select-dropdown__item:has-text("Word")').click()

    // 添加变量
    const addVariableButton = page.getByRole('button', { name: /添加变量/ })
    await addVariableButton.click()

    const variableNameInput = page.locator('input[placeholder*="变量名"]').last()
    await variableNameInput.fill('custom_title')

    // 保存模板
    const saveButton = page.getByRole('button', { name: /保存模板|保存/ })
    await saveButton.click()

    // 等待成功消息
    await page.waitForSelector('.el-message--success', { timeout: 5000 })

    // 关闭模板管理对话框
    const closeButton = page.locator('.el-dialog:has-text("模板管理") .el-dialog__headerbtn')
    await closeButton.click()

    // 3. 使用新创建的模板进行导出
    const addLessonButton = page.getByRole('button', { name: /添加教案/ })
    await addLessonButton.click()
    await page.locator('.lesson-item').first().click()
    await page.getByRole('button', { name: /确认/ }).click()

    // 选择自定义模板
    const templateSelect = page.locator('.el-select:has-text("模板")')
    await templateSelect.click()
    await page.locator('.el-select-dropdown__item:has-text("E2E测试模板")').click()

    // 开始导出
    const exportButton = page.getByRole('button', { name: /开始导出/ })
    await exportButton.click()

    // 验证导出开始
    await page.waitForSelector('.export-progress', { timeout: 10000 })
  })

  /**
   * 场景4: WebSocket 断线重连
   */
  test('WebSocket断线重连机制', async ({ page }) => {
    await page.goto('/teacher/lesson-export')
    await page.waitForLoadState('networkidle')

    // 选择教案并开始导出
    const addLessonButton = page.getByRole('button', { name: /添加教案/ })
    await addLessonButton.click()
    await page.locator('.lesson-item').first().click()
    await page.getByRole('button', { name: /确认/ }).click()

    const exportButton = page.getByRole('button', { name: /开始导出/ })
    await exportButton.click()

    // 等待进度对话框
    await page.waitForSelector('.export-progress', { timeout: 10000 })

    // 检查连接状态指示器
    const connectionStatus = page.locator('.connection-status, [data-status]')
    await expect(connectionStatus).toBeVisible()

    // 模拟网络中断（通过离线模式）
    await page.context().setOffline(true)
    await page.waitForTimeout(2000)

    // 验证显示断连状态
    await expect(connectionStatus).toHaveAttribute('data-status', /disconnected|error/)

    // 恢复网络连接
    await page.context().setOffline(false)
    await page.waitForTimeout(2000)

    // 验证自动重连
    await expect(connectionStatus).toHaveAttribute('data-status', /connected|reconnected/)

    // 等待导出完成
    await page.waitForSelector('.complete-actions', { timeout: 60000 })
  })

  /**
   * 场景5: 多格式并发导出
   */
  test('多格式并发导出', async ({ page }) => {
    await page.goto('/teacher/lesson-export')
    await page.waitForLoadState('networkidle')

    // 选择教案
    const addLessonButton = page.getByRole('button', { name: /添加教案/ })
    await addLessonButton.click()
    await page.locator('.lesson-item').first().click()
    await page.getByRole('button', { name: /确认/ }).click()

    // 同时选择多个格式（如果UI支持）
    const wordRadio = page.locator('input[value="word"]')
    const pdfRadio = page.locator('input[value="pdf"]')

    // 如果支持多选，则同时选择
    if (await wordRadio.count() > 0 && await pdfRadio.count() > 0) {
      await wordRadio.click()
      await pdfRadio.click()
    }

    // 开始导出
    const exportButton = page.getByRole('button', { name: /开始导出/ })
    await exportButton.click()

    // 等待进度对话框
    await page.waitForSelector('.export-progress', { timeout: 10000 })

    // 等待完成
    await page.waitForSelector('.complete-actions', { timeout: 60000 })

    // 验证多个下载按钮或一个压缩包下载
    const downloadButtons = page.getByRole('button', { name: /下载/ })
    const count = await downloadButtons.count()
    expect(count).toBeGreaterThan(0)
  })

  /**
   * 场景6: 导出失败和重试
   */
  test('导出失败处理和重试', async ({ page }) => {
    await page.goto('/teacher/lesson-export')
    await page.waitForLoadState('networkidle')

    // 使用无效的教案ID触发错误
    // 这个测试需要后端支持模拟失败场景

    // 选择教案
    const addLessonButton = page.getByRole('button', { name: /添加教案/ })
    await addLessonButton.click()

    // 如果有模拟失败数据的选项
    const mockErrorButton = page.getByRole('button', { name: /模拟错误/ })
    if (await mockErrorButton.count() > 0) {
      await mockErrorButton.click()
    }

    await page.locator('.lesson-item').first().click()
    await page.getByRole('button', { name: /确认/ }).click()

    // 开始导出
    const exportButton = page.getByRole('button', { name: /开始导出/ })
    await exportButton.click()

    // 等待错误状态
    await page.waitForSelector('.error-actions, .el-alert--error', { timeout: 30000 })

    // 验证错误消息显示
    const errorMessage = page.locator('.el-alert__title, .error-message')
    await expect(errorMessage).toBeVisible()

    // 点击重试按钮
    const retryButton = page.getByRole('button', { name: /重试|重新导出/ })
    await expect(retryButton).toBeVisible()
    await retryButton.click()

    // 验证重新开始导出
    await page.waitForSelector('.export-progress', { timeout: 10000 })
  })

  /**
   * 场景7: 导出选项持久化
   */
  test('导出选项持久化', async ({ page }) => {
    await page.goto('/teacher/lesson-export')
    await page.waitForLoadState('networkidle')

    // 配置导出选项
    const objectivesCheckbox = page.locator('input[value="objectives"]')
    await objectivesCheckbox.check()

    const teacherNotesCheckbox = page.locator('input[value="teacher_notes"], .el-checkbox:has-text("教师备注")')
    await teacherNotesCheckbox.check()

    // 刷新页面
    await page.reload()
    await page.waitForLoadState('networkidle')

    // 验证选项被保存
    await expect(objectivesCheckbox).toBeChecked()
    await expect(teacherNotesCheckbox).toBeChecked()
  })
})

/**
 * 性能测试套件
 */
test.describe('教案导出性能测试', () => {
  test.use({ launchOptions: {
    args: ['--enable-precise-memory-info', '--js-flags=--max-old-space-size=4096']
  }})

  test('导出性能基准测试', async ({ page }) => {
    // 登录
    const authHelper = new AuthHelper(page)
    await authHelper.login('teacher@example.com', 'password123')
    await page.waitForURL('**/dashboard')

    // 导航到导出页面并测量加载时间
    const loadStartTime = Date.now()
    await page.goto('/teacher/lesson-export')
    await page.waitForLoadState('networkidle')
    const loadTime = Date.now() - loadStartTime

    // 页面加载应在 5 秒内完成
    expect(loadTime).toBeLessThan(5000)

    // 选择教案
    const addLessonButton = page.getByRole('button', { name: /添加教案/ })
    await addLessonButton.click()
    await page.locator('.lesson-item').first().click()
    await page.getByRole('button', { name: /确认/ }).click()

    // 测量导出响应时间
    const exportStartTime = Date.now()
    const exportButton = page.getByRole('button', { name: /开始导出/ })
    await exportButton.click()

    // 等待进度对话框
    await page.waitForSelector('.export-progress', { timeout: 10000 })
    const responseTime = Date.now() - exportStartTime

    // 导出响应应在 3 秒内开始
    expect(responseTime).toBeLessThan(3000)

    // 测量完整导出时间
    const completeStartTime = Date.now()
    await page.waitForSelector('.complete-actions', { timeout: 60000 })
    const completeTime = Date.now() - completeStartTime

    // 完整导出应在 60 秒内完成
    expect(completeTime).toBeLessThan(60000)
  })

  test('内存泄漏检测', async ({ page }) => {
    // 登录
    const authHelper = new AuthHelper(page)
    await authHelper.login('teacher@example.com', 'password123')

    // 获取初始内存使用
    const initialMetrics = await page.evaluate(() => {
      return (performance as any).memory || { usedJSHeapSize: 0 }
    })

    // 执行多次导出操作
    for (let i = 0; i < 5; i++) {
      await page.goto('/teacher/lesson-export')
      await page.waitForLoadState('networkidle')

      const addLessonButton = page.getByRole('button', { name: /添加教案/ })
      await addLessonButton.click()
      await page.locator('.lesson-item').first().click()
      await page.getByRole('button', { name: /确认/ }).click()

      const exportButton = page.getByRole('button', { name: /开始导出/ })
      await exportButton.click()

      await page.waitForSelector('.complete-actions', { timeout: 60000 })

      // 关闭对话框
      const closeButton = page.getByRole('button', { name: /关闭/ })
      if (await closeButton.count() > 0) {
        await closeButton.click()
      }
    }

    // 获取最终内存使用
    const finalMetrics = await page.evaluate(() => {
      return (performance as any).memory || { usedJSHeapSize: 0 }
    })

    // 内存增长不应超过 50MB
    const memoryGrowth = (finalMetrics.usedJSHeapSize || 0) - (initialMetrics.usedJSHeapSize || 0)
    expect(memoryGrowth).toBeLessThan(50 * 1024 * 1024) // 50MB
  })
})

/**
 * 可访问性测试套件
 */
test.describe('教案导出可访问性测试', () => {
  test('键盘导航支持', async ({ page }) => {
    // 登录
    const authHelper = new AuthHelper(page)
    await authHelper.login('teacher@example.com', 'password123')
    await page.goto('/teacher/lesson-export')
    await page.waitForLoadState('networkidle')

    // 使用 Tab 键导航到导出按钮
    await page.keyboard.press('Tab')
    await page.keyboard.press('Tab')

    // 按 Enter 键触发
    await page.keyboard.press('Enter')

    // 验证对话框打开
    await page.waitForSelector('.el-dialog', { timeout: 5000 })
  })

  test('屏幕阅读器支持', async ({ page }) => {
    // 登录
    const authHelper = new AuthHelper(page)
    await authHelper.login('teacher@example.com', 'password123')
    await page.goto('/teacher/lesson-export')
    await page.waitForLoadState('networkidle')

    // 检查 ARIA 标签
    const exportButton = page.getByRole('button', { name: /开始导出/ })
    await expect(exportButton).toHaveAttribute('aria-label')

    // 检查进度条的 aria 值
    const progressBar = page.locator('.el-progress[role="progressbar"]')
    if (await progressBar.count() > 0) {
      await expect(progressBar).toHaveAttribute('aria-valuenow')
    }
  })
})
