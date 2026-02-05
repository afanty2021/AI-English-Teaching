/**
 * Playwright 测试辅助函数
 * 提供可重用的测试工具函数
 */
import { Page, Locator } from '@playwright/test'

/**
 * 题目类型枚举
 */
export enum QuestionType {
  CHOICE = 'choice',           // 选择题
  MULTIPLE_CHOICE = 'multiple_choice',  // 多选题
  FILL_BLANK = 'fill_blank',   // 填空题
  READING = 'reading',         // 阅读理解
  WRITING = 'writing',         // 写作题
  LISTENING = 'listening',     // 听力题
  SPEAKING = 'speaking',       // 口语题
  TRANSLATION = 'translation'  // 翻译题
}

/**
 * 题目难度枚举
 */
export enum QuestionDifficulty {
  EASY = 'easy',       // 简单
  MEDIUM = 'medium',   // 中等
  HARD = 'hard'        // 困难
}

/**
 * 测试数据生成器
 */
export class TestDataGenerator {
  /**
   * 生成随机题目标题
   */
  static randomTitle(): string {
    const prefixes = ['测试', '练习', '作业', '考试']
    const subjects = ['英语', '数学', '语文', '物理']
    const types = ['单选题', '填空题', '阅读理解']

    const prefix = prefixes[Math.floor(Math.random() * prefixes.length)]
    const subject = subjects[Math.floor(Math.random() * subjects.length)]
    const type = types[Math.floor(Math.random() * types.length)]

    return `${prefix}${subject}${type}_${Date.now()}`
  }

  /**
   * 生成选择题测试数据
   */
  static choiceQuestion() {
    return {
      title: this.randomTitle(),
      type: QuestionType.CHOICE,
      difficulty: QuestionDifficulty.MEDIUM,
      content: '这是一道测试选择题的题目内容',
      options: [
        { key: 'A', content: '选项A的内容', is_correct: false },
        { key: 'B', content: '选项B的内容', is_correct: true },
        { key: 'C', content: '选项C的内容', is_correct: false },
        { key: 'D', content: '选项D的内容', is_correct: false }
      ]
    }
  }

  /**
   * 生成填空题测试数据
   */
  static fillBlankQuestion() {
    return {
      title: this.randomTitle(),
      type: QuestionType.FILL_BLANK,
      difficulty: QuestionDifficulty.EASY,
      content: '请填入正确的单词：____ is a beautiful language.',
      correctAnswer: {
        answers: ['English', 'english', 'ENGLISH'],
        type: 'multiple'
      }
    }
  }

  /**
   * 生成阅读理解测试数据
   */
  static readingQuestion() {
    return {
      title: this.randomTitle(),
      type: QuestionType.READING,
      difficulty: QuestionDifficulty.MEDIUM,
      content: '这是一篇阅读理解文章的内容...',
      passage: 'Once upon a time, there was a little girl who loved to read books...'
    }
  }
}

/**
 * 题目编辑器页面操作助手
 */
export class QuestionEditorHelper {
  constructor(private page: Page) {}

  /**
   * 导航到新建题目页面
   */
  async gotoNewQuestion(bankId: string = 'test-bank') {
    await this.page.goto(`/teacher/question-banks/${bankId}/questions/new`)
    await this.page.waitForLoadState('networkidle')
  }

  /**
   * 导航到编辑题目页面
   */
  async gotoEditQuestion(questionId: string, bankId: string = 'test-bank') {
    await this.page.goto(`/teacher/questions/${questionId}?bankId=${bankId}`)
    await this.page.waitForLoadState('networkidle')
  }

  /**
   * 选择题目类型
   */
  async selectQuestionType(type: string): Promise<void> {
    // 打开题型选择器
    const select = this.page.locator('.el-select').first()
    await select.click()
    await this.page.waitForTimeout(200)

    // 选择指定题型
    const option = this.page.locator(`text=${type}`).first()
    if (await option.count() > 0) {
      await option.click()
      await this.page.waitForTimeout(200)
    }
  }

  /**
   * 输入题目标题
   */
  async fillTitle(title: string): Promise<void> {
    const input = this.page.locator('input[type="text"]').first()
    await input.fill(title)
  }

  /**
   * 选择题目难度
   */
  async selectDifficulty(difficulty: string): Promise<void> {
    const selector = this.page.locator('.el-select:has-text("难度"), .el-radio-group').first()

    if (await selector.count() > 0) {
      await selector.click()
      await this.page.waitForTimeout(100)

      const option = this.page.locator(`text=${difficulty}`).first()
      if (await option.count() > 0) {
        await option.click()
      }
    }
  }

  /**
   * 点击保存按钮
   */
  async clickSave(): Promise<void> {
    const button = this.page.locator('button:has-text("保存")').first()
    await button.click()
  }

  /**
   * 点击取消按钮
   */
  async clickCancel(): Promise<void> {
    const button = this.page.locator('button:has-text("取消")').first()
    await button.click()
  }

  /**
   * 获取错误消息列表
   */
  async getErrorMessages(): Promise<string[]> {
    const errors = this.page.locator('.el-form-item__error, .el-message--error')
    const count = await errors.count()
    const messages: string[] = []

    for (let i = 0; i < count; i++) {
      const text = await errors.nth(i).textContent()
      if (text) {
        messages.push(text.trim())
      }
    }

    return messages
  }

  /**
   * 等待编辑器加载完成
   */
  async waitForEditorReady(): Promise<void> {
    await this.page.waitForSelector('.question-editor, .el-form', { timeout: 5000 })
  }

  /**
   * 检查特定编辑器是否可见
   */
  async isEditorVisible(editorClass: string): Promise<boolean> {
    const editor = this.page.locator(`.${editorClass}`)
    return await editor.count() > 0 && await editor.first().isVisible()
  }
}

/**
 * 认证助手
 */
export class AuthHelper {
  constructor(private page: Page) {}

  /**
   * 执行登录操作
   */
  async login(email: string, password: string): Promise<void> {
    await this.page.goto('/login')

    // 输入邮箱
    const emailInput = this.page.locator('input[type="email"], input[name="email"]').first()
    await emailInput.fill(email)

    // 输入密码
    const passwordInput = this.page.locator('input[type="password"], input[name="password"]').first()
    await passwordInput.fill(password)

    // 点击登录按钮
    const loginButton = this.page.locator('button:has-text("登录"), button[type="submit"]').first()
    await loginButton.click()

    // 等待登录完成
    await this.page.waitForLoadState('networkidle')
    await this.page.waitForTimeout(500)
  }

  /**
   * 执行登出操作
   */
  async logout(): Promise<void> {
    const logoutButton = this.page.locator('button:has-text("退出"), button:has-text("登出")').first()

    if (await logoutButton.count() > 0) {
      await logoutButton.click()
      await this.page.waitForLoadState('networkidle')
    }
  }

  /**
   * 检查是否已登录
   */
  async isLoggedIn(): Promise<boolean> {
    // 通过检查是否存在登录/注册按钮来判断
    const loginButton = this.page.locator('a:has-text("登录"), button:has-text("登录")')
    return await loginButton.count() === 0
  }
}

/**
 * 等待条件辅助函数
 */
export class WaitHelper {
  /**
   * 等待元素出现
   */
  static async waitForVisible(page: Page, selector: string, timeout: number = 5000): Promise<boolean> {
    try {
      await page.waitForSelector(selector, { state: 'visible', timeout })
      return true
    } catch {
      return false
    }
  }

  /**
   * 等待元素消失
   */
  static async waitForHidden(page: Page, selector: string, timeout: number = 5000): Promise<boolean> {
    try {
      await page.waitForSelector(selector, { state: 'hidden', timeout })
      return true
    } catch {
      return false
    }
  }

  /**
   * 等待 URL 变化
   */
  static async waitForUrlChange(page: Page, pattern: RegExp | string, timeout: number = 5000): Promise<boolean> {
    try {
      await page.waitForURL(pattern, { timeout })
      return true
    } catch {
      return false
    }
  }
}

/**
 * 截图辅助函数
 */
export class ScreenshotHelper {
  /**
   * 在失败时截图
   */
  static async onFailure(page: Page, testName: string): Promise<void> {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
    await page.screenshot({
      path: `test-results/screenshots/failure-${testName}-${timestamp}.png`,
      fullPage: true
    })
  }

  /**
   * 创建测试步骤截图
   */
  static async step(page: Page, stepName: string): Promise<void> {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
    await page.screenshot({
      path: `test-results/screenshots/step-${stepName}-${timestamp}.png`
    })
  }
}
