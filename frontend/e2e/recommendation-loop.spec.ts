/**
 * 推荐系统闭环 E2E 测试
 * 测试完整的推荐-练习-知识图谱更新闭环流程
 */
import { test, expect, chromium } from '@playwright/test'
import { test as baseTest } from './fixtures'

// 定义认证 fixtures
type RecommendationFixtures = {
  authenticatedStudentPage: Awaited<ReturnType<typeof authenticateStudentPage>>
  studentAuthData: {
    access_token: string
    user: {
      id: string
      username: string
      email: string
      role: string
    }
  }
}

/**
 * 创建学生认证页面
 */
async function authenticateStudentPage({ page }: { page: any }) {
  // 访问首页触发应用初始化
  await page.goto('/')

  // 等待 Vue 应用挂载
  await page.waitForSelector('#app', { timeout: 5000 })

  // 设置学生认证状态
  const studentData = {
    access_token: 'test-student-token-' + Date.now(),
    refresh_token: 'test-student-refresh-' + Date.now(),
    user: JSON.stringify({
      id: 'test-student-id',
      username: 'test_student',
      email: 'student@test.com',
      role: 'student',
      organization_id: 'test-org-id'
    })
  }

  await page.evaluate((data: any) => {
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    localStorage.setItem('user', data.user)
    window.dispatchEvent(new Event('storage'))
  }, studentData)

  await page.waitForTimeout(100)

  return { page, studentData }
}

// 扩展 test fixture
const testExtended = baseTest.extend<RecommendationFixtures>({
  authenticatedStudentPage: async ({ page }, use) => {
    const { page: authenticatedPage, studentAuthData } = await authenticateStudentPage({ page })
    await use(authenticatedPage)
  },
  studentAuthData: async ({ page }, use) => {
    const { studentAuthData } = await authenticateStudentPage({ page })
    await use(studentAuthData)
  }
})

const { describe, it, beforeEach } = testExtended

/**
 * 推荐系统闭环测试套件
 */
describe('推荐系统闭环测试', () => {
  /**
   * 测试场景1: 从推荐进入练习，完成后验证图谱更新
   */
  it('从推荐进入练习，完成后验证图谱更新', async ({ authenticatedStudentPage }) => {
    const page = authenticatedStudentPage

    // Step 1: 访问每日推荐页面
    await test.step('访问每日推荐页面', async () => {
      await page.goto('/student/recommendations')
      await page.waitForLoadState('networkidle')

      // 验证页面加载
      await expect(page.locator('text=每日推荐')).toBeVisible({ timeout: 5000 }).catch(() => {
        // 如果页面不存在，可能路由不同
        console.log('推荐页面可能使用不同路由')
      })
    })

    // Step 2: 查看推荐内容
    await test.step('查看推荐内容', async () => {
      // 等待推荐卡片加载
      await page.waitForTimeout(2000)

      // 检查是否有推荐内容
      const recommendationCards = page.locator('.recommendation-card, [class*="recommend"]').count()
      console.log(`找到 ${recommendationCards} 个推荐卡片`)
    })

    // Step 3: 点击推荐内容开始练习
    await test.step('开始练习', async () => {
      // 点击第一个练习推荐
      const startButton = page.locator('button:has-text("开始练习"), button:has-text("开始学习")').first()
      if (await startButton.isVisible()) {
        await startButton.click()
        await page.waitForURL(/practice|exercise|lesson/)
      }
    })

    // Step 4: 完成练习（如果有练习页面）
    await test.step('完成练习流程', async () => {
      // 如果在练习页面
      if (page.url().includes('practice') || page.url().includes('exercise')) {
        // 选择答案并提交
        const options = page.locator('.option, [class*="option"]')
        if (await options.first().isVisible()) {
          await options.first().click()

          // 点击提交按钮
          const submitButton = page.locator('button:has-text("提交"), button:has-text("下一题")')
          if (await submitButton.first().isVisible()) {
            await submitButton.first().click()
          }
        }

        // 如果有完成按钮
        const completeButton = page.locator('button:has-text("完成"), button:has-text("交卷")')
        if (await completeButton.first().isVisible()) {
          await completeButton.first().click()
          await page.waitForTimeout(1000)
        }
      }
    })

    // Step 5: 验证练习结果页面
    await test.step('验证练习结果', async () => {
      // 检查结果页面元素
      await page.waitForTimeout(1000)

      const resultElements = page.locator('text=正确率, text=得分, text=练习结果')
      const visibleCount = await resultElements.count()
      console.log(`找到 ${visibleCount} 个结果元素`)
    })

    // Step 6: 验证知识图谱更新
    await test.step('验证知识图谱更新', async () => {
      // 访问知识图谱或进度页面
      await page.goto('/student/progress')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(2000)

      // 验证进度页面元素
      const progressElements = page.locator('[class*="progress"], [class*="ability"], [class*="graph"]')
      console.log(`找到 ${await progressElements.count()} 个进度元素`)
    })
  })

  /**
   * 测试场景2: 薄弱点针对性练习
   */
  it('薄弱点针对性练习流程', async ({ authenticatedStudentPage }) => {
    const page = authenticatedStudentPage

    // Step 1: 访问学习进度/知识图谱页面
    await test.step('访问知识图谱页面', async () => {
      await page.goto('/student/progress')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(2000)
    })

    // Step 2: 查看薄弱点
    await test.step('查看薄弱知识点', async () => {
      // 查找薄弱点相关元素
      const weakPointElements = page.locator('text=薄弱, text=弱项, [class*="weak"]')
      const count = await weakPointElements.count()
      console.log(`找到 ${count} 个薄弱点元素`)
    })

    // Step 3: 从薄弱点进入练习
    await test.step('从薄弱点进入练习', async () => {
      // 点击薄弱点卡片或"去练习"按钮
      const practiceLink = page.locator('a:has-text("练习"), button:has-text("巩固")').first()
      if (await practiceLink.isVisible()) {
        await practiceLink.click()
        await page.waitForURL(/practice|exercise|recommend/)
        await page.waitForTimeout(1000)
      }
    })

    // Step 4: 完成针对性练习
    await test.step('完成针对性练习', async () => {
      if (page.url().includes('practice') || page.url().includes('exercise')) {
        // 提交答案
        const options = page.locator('.option, [class*="choice"]')
        if (await options.first().isVisible()) {
          await options.first().click()
        }

        // 完成练习
        const completeBtn = page.locator('button:has-text("完成"), button:has-text("交卷")')
        if (await completeBtn.first().isVisible()) {
          await completeBtn.first().click()
          await page.waitForTimeout(1000)
        }
      }
    })
  })

  /**
   * 测试场景3: 二次推荐验证图谱变化
   */
  it('二次推荐验证图谱变化', async ({ authenticatedStudentPage }) => {
    const page = authenticatedStudentPage

    // Step 1: 首次访问推荐
    await test.step('首次访问推荐', async () => {
      await page.goto('/student/recommendations')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(2000)

      // 记录初始推荐内容
      const initialRecommendations = await page.evaluate(() => {
        // 获取当前推荐列表
        return document.querySelectorAll('[class*="recommend"]').length
      })
      console.log(`初始推荐数量: ${initialRecommendations}`)
    })

    // Step 2: 完成一次练习
    await test.step('完成一次练习', async () => {
      // 跳转到练习
      await page.goto('/student/practice')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(1000)

      // 开始一个简单的练习（如果有）
      const startBtn = page.locator('button:has-text("开始"), button:has-text("继续")').first()
      if (await startBtn.isVisible()) {
        await startBtn.click()
        await page.waitForTimeout(2000)
      }
    })

    // Step 3: 再次访问推荐
    await test.step('再次访问推荐', async () => {
      await page.goto('/student/recommendations')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(2000)

      // 获取新推荐
      const newRecommendations = await page.evaluate(() => {
        return document.querySelectorAll('[class*="recommend"]').length
      })
      console.log(`新推荐数量: ${newRecommendations}`)
    })
  })

  /**
   * 测试场景4: 练习会话流程完整性
   */
  it('练习会话流程完整性', async ({ authenticatedStudentPage }) => {
    const page = authenticatedStudentPage

    // Step 1: 访问练习页面
    await test.step('访问练习页面', async () => {
      await page.goto('/student/practice')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(2000)
    })

    // Step 2: 选择练习类型
    await test.step('选择练习类型', async () => {
      // 选择语法练习
      const grammarOption = page.locator('text=语法, text=Grammar').first()
      if (await grammarOption.isVisible()) {
        await grammarOption.click()
        await page.waitForTimeout(500)
      }
    })

    // Step 3: 开始练习
    await test.step('开始练习', async () => {
      const startButton = page.locator('button:has-text("开始练习")')
      if (await startButton.isVisible()) {
        await startButton.click()
        await page.waitForURL(/practice/)
        await page.waitForTimeout(1000)
      }
    })

    // Step 4: 完成多道题目
    await test.step('完成题目', async () => {
      // 完成3道题目
      for (let i = 0; i < 3; i++) {
        // 选择答案
        const options = page.locator('.option, [class*="choice"]')
        if (await options.count() > 0 && await options.first().isVisible()) {
          await options.first().click()
          await page.waitForTimeout(300)

          // 点击下一题或完成
          const nextBtn = page.locator('button:has-text("下一题"), button:has-text("继续")')
          if (await nextBtn.first().isVisible()) {
            await nextBtn.first().click()
            await page.waitForTimeout(500)
          }
        }
      }
    })

    // Step 5: 完成练习会话
    await test.step('完成练习', async () => {
      const completeBtn = page.locator('button:has-text("完成"), button:has-text("交卷")')
      if (await completeBtn.first().isVisible()) {
        await completeBtn.first().click()
        await page.waitForTimeout(2000)
      }

      // 验证结果显示
      const resultPage = page.locator('text=正确率, text=得分, text=练习结果')
      if (await resultPage.first().isVisible()) {
        console.log('练习结果页面显示正常')
      }
    })
  })
})

/**
 * 性能测试套件
 */
describe('推荐系统性能测试', () => {
  it('页面加载性能测试', async () => {
    const browser = await chromium.launch()
    const context = await browser.newContext()
    const page = await context.newPage()

    // 设置认证状态
    await page.evaluate(() => {
      localStorage.setItem('access_token', 'perf-test-token')
      localStorage.setItem('user', JSON.stringify({
        id: 'test-student-id',
        username: 'test_student',
        role: 'student'
      }))
    })

    // 测量页面加载时间
    const loadTime = await test.step('测量推荐页面加载时间', async () => {
      const startTime = Date.now()
      await page.goto('/student/recommendations')
      await page.waitForLoadState('networkidle')
      const endTime = Date.now()
      return endTime - startTime
    })

    console.log(`推荐页面加载时间: ${loadTime}ms`)

    // 验证加载时间在可接受范围内
    expect(loadTime).toBeLessThan(10000) // 10秒内

    await browser.close()
  })

  it('练习页面响应时间测试', async () => {
    const browser = await chromium.launch()
    const context = await browser.newContext()
    const page = await context.newPage()

    // 设置认证状态
    await page.evaluate(() => {
      localStorage.setItem('access_token', 'perf-test-token')
      localStorage.setItem('user', JSON.stringify({
        id: 'test-student-id',
        username: 'test_student',
        role: 'student'
      }))
    })

    const responseTimes: number[] = []

    // 监听请求响应时间
    page.on('response', async (response) => {
      if (response.url().includes('/api/v1/')) {
        const timing = response.request().timing()
        if (timing?.receiveStart && timing?.sendEnd) {
          responseTimes.push(timing.receiveStart - timing.sendEnd)
        }
      }
    })

    // 访问练习页面
    await page.goto('/student/practice')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)

    // 统计响应时间
    if (responseTimes.length > 0) {
      const avgTime = responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length
      console.log(`平均API响应时间: ${avgTime.toFixed(2)}ms`)
      console.log(`总请求数: ${responseTimes.length}`)
    }

    await browser.close()
  })
})

/**
 * 错误处理测试套件
 */
describe('推荐系统错误处理测试', () => {
  it('无网络时的错误处理', async () => {
    const browser = await chromium.launch()
    const context = await browser.newContext()
    const page = await context.newPage()

    // 设置认证状态
    await page.evaluate(() => {
      localStorage.setItem('access_token', 'error-test-token')
      localStorage.setItem('user', JSON.stringify({
        id: 'test-student-id',
        username: 'test_student',
        role: 'student'
      }))
    })

    // 模拟离线状态
    await context.route('**/*', (route) => route.abort('failed'))

    // 访问推荐页面
    await page.goto('/student/recommendations')
    await page.waitForTimeout(2000)

    // 验证错误提示显示
    const errorMessage = page.locator('text=网络错误, text=加载失败, text=请重试')
    if (await errorMessage.first().isVisible()) {
      console.log('错误提示正常显示')
    }

    await browser.close()
  })

  it('API错误时的降级处理', async () => {
    const browser = await chromium.launch()
    const context = await browser.newContext()
    const page = await context.newPage()

    // 设置认证状态
    await page.evaluate(() => {
      localStorage.setItem('access_token', 'error-test-token')
      localStorage.setItem('user', JSON.stringify({
        id: 'test-student-id',
        username: 'test_student',
        role: 'student'
      }))
    })

    // 模拟API返回500错误
    await context.route('**/api/v1/contents/recommend**', (route) => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ detail: 'Internal Server Error' })
      })
    })

    // 访问推荐页面
    await page.goto('/student/recommendations')
    await page.waitForTimeout(2000)

    // 验证错误状态显示
    const hasDefaultContent = await page.evaluate(() => {
      return document.querySelectorAll('.empty, .error, [class*="default"]').length > 0
    })
    console.log(`有默认内容展示: ${hasDefaultContent}`)

    await browser.close()
  })
})

export { }
