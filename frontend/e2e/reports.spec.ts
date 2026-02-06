/**
 * 报告系统 E2E 测试 - AI英语教学系统
 * 使用 Playwright 测试学习报告功能
 */
import { test, expect } from '@playwright/test';

// ============ 测试配置 ============

test.describe('学习报告系统 E2E 测试', () => {
  // 测试报告列表页面
  test.describe('报告列表页面', () => {
    test.beforeEach(async ({ page }) => {
      // 登录测试用户
      await page.goto('/login');
      await page.fill('input[placeholder*="邮箱"]', 'test_student@test.com');
      await page.fill('input[placeholder*="密码"]', 'Test1234');
      await page.click('button:has-text("登录")');
      await page.waitForURL(/\/student/);
    });

    test('应该显示报告列表页面', async ({ page }) => {
      // 导航到报告页面
      await page.goto('/student/reports');
      await page.waitForLoadState('networkidle');

      // 验证页面标题
      await expect(page.locator('h1')).toContainText('学习报告');
    });

    test('应该能够生成新报告', async ({ page }) => {
      await page.goto('/student/reports');
      await page.waitForLoadState('networkidle');

      // 点击生成报告按钮
      const generateButton = page.locator('button:has-text("生成报告")');
      await expect(generateButton).toBeVisible();

      await generateButton.click();

      // 选择报告类型
      const reportTypeSelect = page.locator('.el-select:has-text("报告类型")');
      await reportTypeSelect.click();
      await page.locator('li:has-text("周报")').click();

      // 确认生成
      await page.locator('button:has-text("确认生成")').click();

      // 等待任务创建成功
      await expect(page.locator('text=任务已创建')).toBeVisible({ timeout: 5000 });
    });

    test('应该显示任务列表', async ({ page }) => {
      await page.goto('/student/reports');
      await page.waitForLoadState('networkidle');

      // 点击任务管理tab
      await page.locator('text=任务管理').click();

      // 验证任务列表显示
      await expect(page.locator('text=待处理')).toBeVisible();
      await expect(page.locator('text=已完成')).toBeVisible();
    });
  });

  // 测试报告详情页面
  test.describe('报告详情页面', () => {
    const testReportId = 'test-report-id';

    test.beforeEach(async ({ page }) => {
      await page.goto('/login');
      await page.fill('input[placeholder*="邮箱"]', 'test_student@test.com');
      await page.fill('input[placeholder*="密码"]', 'Test1234');
      await page.click('button:has-text("登录")');
      await page.waitForURL(/\/student/);
    });

    test('应该显示报告详情', async ({ page }) => {
      await page.goto(`/student/reports/${testReportId}`);
      await page.waitForLoadState('networkidle');

      // 验证页面结构
      await expect(page.locator('h1')).toContainText('学习报告');
      await expect(page.locator('text=统计概览')).toBeVisible();
      await expect(page.locator('text=能力分析')).toBeVisible();
    });

    test('应该显示图表数据', async ({ page }) => {
      await page.goto(`/student/reports/${testReportId}`);
      await page.waitForLoadState('networkidle');

      // 验证能力雷达图显示
      const radarChart = page.locator('.ability-radar-chart');
      await expect(radarChart).toBeVisible();

      // 验证趋势图显示
      const trendChart = page.locator('.learning-trend-chart');
      await expect(trendChart).toBeVisible();
    });

    test('应该能够切换tab', async ({ page }) => {
      await page.goto(`/student/reports/${testReportId}`);
      await page.waitForLoadState('networkidle');

      // 测试各个tab切换
      await page.locator('text=薄弱点').click();
      await expect(page.locator('text=知识点掌握情况')).toBeVisible();

      await page.locator('text=学习建议').click();
      await expect(page.locator('text=推荐练习')).toBeVisible();
    });
  });

  // 测试导出功能
  test.describe('报告导出功能', () => {
    const testReportId = 'test-report-id';

    test.beforeEach(async ({ page }) => {
      await page.goto('/login');
      await page.fill('input[placeholder*="邮箱"]', 'test_student@test.com');
      await page.fill('input[placeholder*="密码"]', 'Test1234');
      await page.click('button:has-text("登录")');
      await page.waitForURL(/\/student/);
    });

    test('应该能够导出PDF', async ({ page }) => {
      await page.goto(`/student/reports/${testReportId}`);
      await page.waitForLoadState('networkidle');

      // 点击导出按钮
      const exportButton = page.locator('button:has-text("导出")');
      await expect(exportButton).toBeVisible();

      await exportButton.click();

      // 选择PDF格式
      await page.locator('text=PDF文档').click();

      // 确认导出
      await page.locator('button:has-text("确认导出")').click();

      // 等待任务创建
      await expect(page.locator('text=导出任务已提交')).toBeVisible({ timeout: 5000 });
    });

    test('应该显示导出进度', async ({ page }) => {
      await page.goto(`/student/reports/${testReportId}`);
      await page.waitForLoadState('networkidle');

      // 触发导出
      await page.locator('button:has-text("导出")').click();
      await page.locator('text=PDF文档').click();
      await page.locator('button:has-text("确认导出")').click();

      // 验证进度显示
      await expect(page.locator('text=正在导出')).toBeVisible({ timeout: 3000 });
      await expect(page.locator('.el-progress')).toBeVisible();
    });

    test('导出完成后应该显示下载链接', async ({ page }) => {
      await page.goto(`/student/reports/${testReportId}`);
      await page.waitForLoadState('networkidle');

      // 触发导出并等待完成
      await page.locator('button:has-text("导出")').click();
      await page.locator('text=PDF文档').click();
      await page.locator('button:has-text("确认导出")').click();

      // 等待导出完成
      await expect(page.locator('text=导出完成')).toBeVisible({ timeout: 10000 });
      await expect(page.locator('text=下载文件')).toBeVisible();
    });
  });

  // 测试图表组件
  test.describe('图表组件', () => {
    const testReportId = 'test-report-id';

    test.beforeEach(async ({ page }) => {
      await page.goto('/login');
      await page.fill('input[placeholder*="邮箱"]', 'test_student@test.com');
      await page.fill('input[placeholder*="密码"]', 'Test1234');
      await page.click('button:has-text("登录")');
      await page.waitForURL(/\/student/);
    });

    test('能力雷达图应该可交互', async ({ page }) => {
      await page.goto(`/student/reports/${testReportId}`);
      await page.waitForLoadState('networkidle');

      // 点击雷达图区域
      const radarChart = page.locator('.ability-radar-chart');
      await radarChart.click();

      // 验证详情面板显示
      await expect(page.locator('.ability-details')).toBeVisible();
    });

    test('应该能够切换对比模式', async ({ page }) => {
      await page.goto(`/student/reports/${testReportId}`);
      await page.waitForLoadState('networkidle');

      // 切换到班级对比
      await page.locator('label:has-text("班级对比")').click();

      // 验证图表更新
      await expect(page.locator('text=班级平均')).toBeVisible();
    });

    test('学习趋势图应该支持时间筛选', async ({ page }) => {
      await page.goto(`/student/reports/${testReportId}`);
      await page.waitForLoadState('networkidle');

      // 切换到90天
      await page.locator('button:has-text("90天")').click();

      // 验证图表更新
      const chart = page.locator('.learning-trend-chart');
      await expect(chart).toBeVisible();
    });

    test('知识热力图应该可筛选', async ({ page }) => {
      await page.goto(`/student/reports/${testReportId}`);
      await page.waitForLoadState('networkidle');

      // 点击知识热力图tab
      await page.locator('text=知识图谱').click();

      // 验证筛选器
      await expect(page.locator('.filter-bar')).toBeVisible();

      // 选择能力类型筛选
      await page.locator('.el-select:has-text("能力类型")').click();
      await page.locator('li:has-text("词汇")').click();
    });
  });

  // 测试响应式布局
  test.describe('响应式布局', () => {
    test('应该在移动端正确显示', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('/login');
      await page.fill('input[placeholder*="邮箱"]', 'test_student@test.com');
      await page.fill('input[placeholder*="密码"]', 'Test1234');
      await page.click('button:has-text("登录")');
      await page.waitForURL(/\/student/);

      // 导航到报告页面
      await page.goto('/student/reports');
      await page.waitForLoadState('networkidle');

      // 验证移动端布局
      await expect(page.locator('h1')).toContainText('学习报告');

      // 移动端可能显示移动端特有的菜单
      const menuButton = page.locator('.el-icon-menu').first();
      if (await menuButton.isVisible()) {
        await menuButton.click();
      }
    });
  });
});

// ============ 性能测试 ============

test.describe('性能测试', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[placeholder*="邮箱"]', 'test_student@test.com');
    await page.fill('input[placeholder*="密码"]', 'Test1234');
    await page.click('button:has-text("登录")');
    await page.waitForURL(/\/student/);
  });

  test('页面加载应该在3秒内完成', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/student/reports');
    await page.waitForLoadState('networkidle');

    const loadTime = Date.now() - startTime;
    console.log(`页面加载时间: ${loadTime}ms`);

    expect(loadTime).toBeLessThan(3000);
  });

  test('图表渲染应该在2秒内完成', async ({ page }) => {
    const testReportId = 'test-report-id';

    await page.goto(`/student/reports/${testReportId}`);
    await page.waitForLoadState('networkidle');

    const startTime = Date.now();

    // 等待图表渲染完成
    await expect(page.locator('.ability-radar-chart canvas')).toBeVisible();

    const renderTime = Date.now() - startTime;
    console.log(`图表渲染时间: ${renderTime}ms`);

    expect(renderTime).toBeLessThan(2000);
  });
});

// ============ 错误处理测试 ============

test.describe('错误处理', () => {
  test('网络错误应该显示友好提示', async ({ page }) => {
    // 模拟网络断开
    await page.route('**/api/v1/reports/**', route => route.abort('failed'));

    await page.goto('/login');
    await page.fill('input[placeholder*="邮箱"]', 'test_student@test.com');
    await page.fill('input[placeholder*="密码"]', 'Test1234');
    await page.click('button:has-text("登录")');
    await page.waitForURL(/\/student/);

    await page.goto('/student/reports');
    await page.waitForLoadState('networkidle');

    // 应该显示错误提示
    await expect(page.locator('text=网络错误')).toBeVisible();
  });

  test('404错误应该显示友好页面', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[placeholder*="邮箱"]', 'test_student@test.com');
    await page.fill('input[placeholder*="密码"]', 'Test1234');
    await page.click('button:has-text("登录")');
    await page.waitForURL(/\/student/);

    // 访问不存在的报告
    await page.goto('/student/reports/non-existent-id');
    await page.waitForLoadState('networkidle');

    // 应该显示404错误
    await expect(page.locator('text=报告不存在')).toBeVisible();
  });
});
