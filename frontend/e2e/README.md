# Playwright E2E 测试

本项目使用 Playwright 进行端到端测试，确保题目编辑器和关键用户流程正常工作。

## 测试文件结构

```
e2e/
├── example.spec.ts              # 基础示例测试
├── question-editor.spec.ts      # 题目编辑器核心功能测试
├── question-editor-dialog.spec.ts  # 对话框模式测试
├── question-editor-advanced.spec.ts # 高级功能测试
├── helpers.ts                   # 测试辅助函数和工具类
└── README.md                    # 本文档
```

## 快速开始

### 1. 安装 Playwright 浏览器

首次运行前，需要安装 Playwright 浏览器：

```bash
npx playwright install chromium
```

如需安装所有浏览器：

```bash
npx playwright install
```

### 2. 运行测试

```bash
# 运行所有 E2E 测试（无头模式）
npm run test:e2e

# 运行测试并显示浏览器窗口
npm run test:e2e:headed

# 使用 Playwright UI 模式运行
npm run test:e2e:ui

# 调试模式运行
npm run test:e2e:debug
```

### 3. 查看测试报告

测试运行后，HTML 报告位于 `test-results/index.html`：

```bash
# macOS
open test-results/index.html

# Linux
xdg-open test-results/index.html

# Windows
start test-results/index.html
```

## 测试覆盖范围

### 基础功能测试 (`example.spec.ts`)
- 页面导航
- 登录页面可访问性
- 教师端路由可访问性
- Vue 应用挂载验证
- Element Plus 组件渲染

### 题目编辑器测试 (`question-editor.spec.ts`)
- 题目类型切换
- 选择题编辑（4选项、正确答案标记）
- 填空题编辑（等效答案添加）
- 阅读理解编辑（文章内容、词数统计）
- 富文本编辑（加粗格式）
- 实时预览
- 批量导入对话框
- 表单验证
- 自动保存草稿

### 对话框模式测试 (`question-editor-dialog.spec.ts`)
- 从题库页打开新建对话框
- 对话框表单字段完整性
- 对话框关闭功能
- 编辑现有题目跳转
- 题型切换交互
- JSON/Excel 导入切换

### 高级功能测试 (`question-editor-advanced.spec.ts`)
- 使用辅助函数创建题目
- 表单验证（必填字段、选项内容）
- 异步操作等待
- 页面导航流程
- 批量操作
- 键盘导航
- 视觉反馈

## 辅助工具类

### `QuestionEditorHelper`
题目编辑器操作助手，提供：
- `gotoNewQuestion(bankId)` - 导航到新建页面
- `gotoEditQuestion(questionId, bankId)` - 导航到编辑页面
- `selectQuestionType(type)` - 选择题型
- `fillTitle(title)` - 填写标题
- `selectDifficulty(difficulty)` - 选择难度
- `clickSave()` / `clickCancel()` - 点击保存/取消
- `getErrorMessages()` - 获取错误消息
- `waitForEditorReady()` - 等待编辑器就绪
- `isEditorVisible(editorClass)` - 检查编辑器可见性

### `TestDataGenerator`
测试数据生成器，提供：
- `randomTitle()` - 随机题目标题
- `choiceQuestion()` - 选择题测试数据
- `fillBlankQuestion()` - 填空题测试数据
- `readingQuestion()` - 阅读理解测试数据

### `AuthHelper`
认证助手，提供：
- `login(email, password)` - 执行登录
- `logout()` - 执行登出
- `isLoggedIn()` - 检查登录状态

### `WaitHelper`
等待条件辅助函数：
- `waitForVisible(page, selector, timeout)` - 等待元素可见
- `waitForHidden(page, selector, timeout)` - 等待元素隐藏
- `waitForUrlChange(page, pattern, timeout)` - 等待 URL 变化

### `ScreenshotHelper`
截图辅助函数：
- `onFailure(page, testName)` - 失败时截图
- `step(page, stepName)` - 测试步骤截图

## 测试配置

配置文件：`playwright.config.ts`

```typescript
{
  testDir: './e2e',
  baseURL: 'http://localhost:5173',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html'],
    ['junit', { outputFile: 'test-results/junit.xml' }]
  ],
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  }
}
```

## 测试环境准备

### 方式一：手动启动开发服务器

```bash
# 终端 1：启动前端开发服务器
npm run dev

# 终端 2：运行 E2E 测试
npm run test:e2e
```

### 方式二：使用 Playwright webServer（推荐）

取消注释 `playwright.config.ts` 中的 webServer 配置：

```typescript
webServer: {
  command: 'npm run dev',
  port: 5173,
  reuseExistingServer: !process.env.CI
}
```

然后直接运行测试，Playwright 会自动启动开发服务器。

## 编写新测试

### 基本测试模板

```typescript
import { test, expect } from '@playwright/test'
import { QuestionEditorHelper, TestDataGenerator } from './helpers'

test.describe('测试组名称', () => {
  test('测试用例名称', async ({ page }) => {
    // 1. 导航到页面
    await page.goto('/teacher/question-banks/test-bank/questions/new')

    // 2. 执行操作
    const helper = new QuestionEditorHelper(page)
    await helper.fillTitle('测试题目')

    // 3. 验证结果
    await expect(page.locator('input[type="text"]')).toHaveValue('测试题目')
  })
})
```

### 使用辅助函数

```typescript
test('使用辅助函数的测试', async ({ page }) => {
  const helper = new QuestionEditorHelper(page)
  const testData = TestDataGenerator.choiceQuestion()

  await helper.gotoNewQuestion()
  await helper.fillTitle(testData.title)
  await helper.selectQuestionType('单选题')

  // 验证编辑器可见
  expect(await helper.isEditorVisible('choice-editor')).toBe(true)
})
```

### 添加截图

```typescript
test('带截图的测试', async ({ page }) => {
  // 测试步骤...
  await ScreenshotHelper.step(page, 'after-action')

  // 失败时自动截图
  test.fail(true) // 标记为预期失败
  await ScreenshotHelper.onFailure(page, 'test-name')
})
```

## 常见问题

### 1. 测试超时

如果测试超时，可以增加超时时间：

```typescript
test.setTimeout(60000) // 60 秒超时
```

### 2. 元素查找失败

使用等待辅助函数：

```typescript
await WaitHelper.waitForVisible(page, '.my-element', 5000)
```

### 3. 测试不稳定

- 使用 `waitForLoadState('networkidle')` 等待页面加载完成
- 使用 `page.waitForTimeout(ms)` 添加短暂延迟
- 增加重试次数（在配置文件中）

### 4. CI 环境运行

确保在 CI 环境中安装浏览器：

```yaml
- name: Install Playwright Browsers
  run: npx playwright install --with-deps
```

## 调试技巧

### 1. 使用 UI 模式

```bash
npm run test:e2e:ui
```

提供可视化界面，可以：
- 单独运行某个测试
- 查看每一步的截图
- 时间旅行调试
- 查看网络请求

### 2. 使用调试模式

```bash
npm run test:e2e:debug
```
- 以 headed 模式运行
- 自动打开 Playwright Inspector
- 可以逐步执行测试

### 3. 使用 headed 模式

```bash
npm run test:e2e:headed
```
可以看到浏览器操作过程

### 4. 代码中暂停

```typescript
await page.pause() // 暂停执行，打开 Playwright Inspector
```

## 持续集成

### GitHub Actions 示例

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright Browsers
        run: npx playwright install --with-deps

      - name: Run E2E tests
        run: npm run test:e2e

      - name: Upload test report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: test-results/
```

## 相关资源

- [Playwright 官方文档](https://playwright.dev)
- [Playwright 最佳实践](https://playwright.dev/docs/best-practices)
- [Playwright 调试指南](https://playwright.dev/docs/debug)
