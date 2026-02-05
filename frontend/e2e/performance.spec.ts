/**
 * 推荐系统性能测试
 * 验证系统性能指标是否达到预期
 */
import { test, expect, chromium } from '@playwright/test'

/**
 * 性能测试配置
 */
const PERFORMANCE_THRESHOLDS = {
  pageLoadTime: 5000,      // 页面加载时间 < 5秒
  apiResponseTime: 2000,    // API响应时间 < 2秒
  firstContentfulPaint: 3000, // FCP < 3秒
  largestContentfulPaint: 5000, // LCP < 5秒
}

/**
 * 性能测试 Fixtures
 */
test.describe('推荐系统性能测试', () => {
  let browser: any
  let context: any

  test.beforeAll(async () => {
    browser = await chromium.launch()
    context = await browser.newContext({
      // 模拟移动设备或桌面设备
      viewport: { width: 1920, height: 1080 }
    })
  })

  test.afterAll(async () => {
    await browser.close()
  })

  /**
   * 测试1: 推荐页面加载性能
   */
  test('推荐页面加载性能', async () => {
    const page = await context.newPage()

    // 设置认证状态
    await page.evaluate(() => {
      localStorage.setItem('access_token', 'perf-test-token')
      localStorage.setItem('refresh_token', 'perf-refresh-token')
      localStorage.setItem('user', JSON.stringify({
        id: 'test-student-id',
        username: 'test_student',
        email: 'student@test.com',
        role: 'student'
      }))
    })

    const metrics: any = {}

    // 收集性能指标
    page.on('console', (msg) => {
      if (msg.type() === 'performance') {
        metrics[msg.text()] = true
      }
    })

    // 测量页面加载时间
    const startTime = Date.now()
    await page.goto('/student/recommendations')

    // 等待页面主要内容加载
    await page.waitForLoadState('domcontentloaded')
    await page.waitForTimeout(3000)

    const loadTime = Date.now() - startTime

    console.log(`推荐页面加载时间: ${loadTime}ms`)

    // 验证性能
    expect(loadTime).toBeLessThan(PERFORMANCE_THRESHOLDS.pageLoadTime)
  })

  /**
   * 测试2: 练习页面响应性能
   */
  test('练习页面响应性能', async () => {
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

    // 监听API请求
    page.on('response', async (response) => {
      if (response.url().includes('/api/v1/')) {
        const timing = response.timing()
        if (timing) {
          const responseTime = timing.receiveEnd - timing.sendStart
          responseTimes.push(responseTime)
        }
      }
    })

    // 访问练习页面
    const startTime = Date.now()
    await page.goto('/student/practice')
    await page.waitForLoadState('networkidle')

    const pageLoadTime = Date.now() - startTime

    console.log(`练习页面加载时间: ${pageLoadTime}ms`)
    console.log(`API请求数: ${responseTimes.length}`)

    if (responseTimes.length > 0) {
      const avgResponseTime = responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length
      console.log(`平均API响应时间: ${avgResponseTime.toFixed(2)}ms`)
      console.log(`最大API响应时间: ${Math.max(...responseTimes)}ms`)
      console.log(`最小API响应时间: ${Math.min(...responseTimes)}ms`)

      // 验证平均响应时间
      expect(avgResponseTime).toBeLessThan(PERFORMANCE_THRESHOLDS.apiResponseTime)
    }

    expect(pageLoadTime).toBeLessThan(PERFORMANCE_THRESHOLDS.pageLoadTime)
  })

  /**
   * 测试3: 知识图谱页面性能
   */
  test('知识图谱页面性能', async () => {
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

    const navigationStart = Date.now()
    await page.goto('/student/progress')
    await page.waitForLoadState('networkidle')

    const loadTime = Date.now() - navigationStart

    console.log(`知识图谱页面加载时间: ${loadTime}ms`)
    expect(loadTime).toBeLessThan(PERFORMANCE_THRESHOLDS.pageLoadTime)
  })

  /**
   * 测试4: API响应时间分布
   */
  test('API响应时间分布测试', async () => {
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

    // 监听所有API响应
    page.on('response', (response) => {
      if (response.url().includes('/api/v1/')) {
        const timing = response.timing()
        if (timing && timing.receiveEnd > 0) {
          const duration = timing.receiveEnd - timing.sendStart
          responseTimes.push({
            url: response.url(),
            method: response.request().method(),
            status: response.status(),
            duration: duration
          })
        }
      }
    })

    // 依次访问各个页面
    const pages = [
      '/student/recommendations',
      '/student/practice',
      '/student/progress'
    ]

    for (const pagePath of pages) {
      await page.goto(pagePath)
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(1000)
    }

    // 输出响应时间统计
    console.log('\n=== API响应时间统计 ===')

    if (responseTimes.length > 0) {
      const durations = responseTimes.map(r => r.duration)
      const avg = durations.reduce((a, b) => a + b, 0) / durations.length
      const p50 = durations.sort((a, b) => a - b)[Math.floor(durations.length * 0.5)]
      const p95 = durations.sort((a, b) => a - b)[Math.floor(durations.length * 0.95)]

      console.log(`总请求数: ${responseTimes.length}`)
      console.log(`平均响应时间: ${avg.toFixed(2)}ms`)
      console.log(`P50响应时间: ${p50.toFixed(2)}ms`)
      console.log(`P95响应时间: ${p95.toFixed(2)}ms`)
      console.log(`最大响应时间: ${Math.max(...durations)}ms`)
      console.log(`最小响应时间: ${Math.min(...durations)}ms`)

      // 验证P95响应时间
      expect(p95).toBeLessThan(5000, 'P95响应时间应小于5秒')
    }

    // 统计各API端点
    console.log('\n=== 各API端点响应时间 ===')
    const endpointStats: Record<string, number[]> = {}
    for (const response of responseTimes) {
      const endpoint = response.url.split('/api/v1/')[1] || 'unknown'
      if (!endpointStats[endpoint]) {
        endpointStats[endpoint] = []
      }
      endpointStats[endpoint].push(response.duration)
    }

    for (const [endpoint, times] of Object.entries(endpointStats)) {
      const avg = times.reduce((a, b) => a + b, 0) / times.length
      console.log(`${endpoint}: 平均 ${avg.toFixed(2)}ms (${times.length}次请求)`)
    }
  })

  /**
   * 测试5: 页面交互响应测试
   */
  test('页面交互响应测试', async () => {
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

    // 访问推荐页面
    await page.goto('/student/recommendations')
    await page.waitForLoadState('networkidle')

    // 测试按钮点击响应时间
    const startTime = Date.now()

    // 尝试点击页面上的按钮
    const buttons = page.locator('button:visible')
    const buttonCount = await buttons.count()

    if (buttonCount > 0) {
      await buttons.first().click()
      await page.waitForTimeout(500)
    }

    const interactionTime = Date.now() - startTime

    console.log(`按钮交互响应时间: ${interactionTime}ms`)
    expect(interactionTime).toBeLessThan(2000)
  })
})

/**
 * 内存使用测试
 */
test.describe('内存使用测试', () => {
  test('页面内存使用监控', async () => {
    const browser = await chromium.launch()
    const context = await browser.newContext()
    const page = await context.newPage()

    // 设置认证状态
    await page.evaluate(() => {
      localStorage.setItem('access_token', 'mem-test-token')
      localStorage.setItem('user', JSON.stringify({
        id: 'test-student-id',
        username: 'test_student',
        role: 'student'
      }))
    })

    // 获取初始内存使用
    const initialMemory = await page.evaluate(() => {
      if (performance.memory) {
        return {
          usedJSHeapSize: performance.memory.usedJSHeapSize,
          totalJSHeapSize: performance.memory.totalJSHeapSize,
          jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
        }
      }
      return null
    })

    console.log('初始内存使用:', initialMemory)

    // 多次访问页面
    for (let i = 0; i < 5; i++) {
      await page.goto('/student/recommendations')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(500)
    }

    // 获取最终内存使用
    const finalMemory = await page.evaluate(() => {
      if (performance.memory) {
        return {
          usedJSHeapSize: performance.memory.usedJSHeapSize,
          totalJSHeapSize: performance.memory.totalJSHeapSize
        }
      }
      return null
    })

    console.log('最终内存使用:', finalMemory)

    await browser.close()

    // 注意：由于内存测试依赖Chrome特定的API，这里只记录不断言
    if (initialMemory && finalMemory) {
      const memoryIncrease = finalMemory.usedJSHeapSize - initialMemory.usedJSHeapSize
      console.log(`内存增长: ${(memoryIncrease / 1024 / 1024).toFixed(2)}MB`)
    }
  })
})

/**
 * 并发请求测试
 */
test.describe('并发请求测试', () => {
  test('多个API并发请求', async () => {
    const browser = await chromium.launch()
    const context = await browser.newContext()
    const page = await context.newPage()

    // 设置认证状态
    await page.evaluate(() => {
      localStorage.setItem('access_token', 'concurrent-test-token')
      localStorage.setItem('user', JSON.stringify({
        id: 'test-student-id',
        username: 'test_student',
        role: 'student'
      }))
    })

    const responses: any[] = []

    // 监听响应
    page.on('response', (response) => {
      if (response.url().includes('/api/v1/')) {
        responses.push({
          url: response.url(),
          status: response.status(),
          timing: response.timing()
        })
      }
    })

    // 触发多个并发请求
    await page.goto('/student/recommendations')
    await page.waitForLoadState('networkidle')

    // 等待所有请求完成
    await page.waitForTimeout(3000)

    console.log(`并发请求完成数: ${responses.length}`)

    // 统计并发请求
    const successResponses = responses.filter(r => r.status >= 200 && r.status < 300)
    const errorResponses = responses.filter(r => r.status >= 400)

    console.log(`成功请求: ${successResponses.length}`)
    console.log(`错误请求: ${errorResponses.length}`)

    expect(successResponses.length).toBeGreaterThan(0)

    await browser.close()
  })
})

export { }
