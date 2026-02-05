# 题目编辑器 E2E 测试分析与改进建议

## 📊 测试现状总结

### ✅ 已完成的配置工作

1. **Playwright 配置优化**
   - 端口配置正确：`baseURL: http://localhost:5174`
   - storageState 路径正确：`e2e/.auth/storage-state.json`
   - 全局设置脚本已配置

2. **认证数据结构验证**
   - storage-state.json 包含完整的认证数据
   - localStorage 格式正确（user、access_token、refresh_token）
   - origin 匹配正确端口

3. **测试环境准备**
   - 前端服务器正常运行（端口 5174）
   - 后端 API 服务正常
   - 题目编辑器页面可手动访问

### ❌ 存在的核心问题

**主要问题：认证状态同步失败**

1. **localStorage 设置时机问题**
   - Playwright 测试中设置 localStorage 后，应用可能还没有完全初始化
   - Vue Pinia store 初始化时 localStorage 可能为空
   - 路由守卫检查时机过早

2. **应用生命周期问题**
   - 应用启动 → 路由守卫检查 → localStorage 仍为空 → 重定向到登录页
   - 即使手动设置 localStorage，应用也不会重新检查认证状态

3. **测试稳定性问题**
   - 页面刷新后认证状态丢失
   - 页面导航时认证状态不同步

## 🔍 根本原因分析

### 1. Vue 应用初始化时序

```
应用启动
    ↓
Pinia store 初始化（检查 localStorage → 空）
    ↓
路由守卫检查（认证失败 → 重定向登录页）
    ↓
测试设置 localStorage（此时已太晚）
    ↓
页面刷新/重新导航 → 重新循环上述过程
```

### 2. 认证检查机制

- **Store 级别**：在组件创建时检查 localStorage
- **路由守卫级别**：每次路由跳转时检查认证状态
- **时间窗口**：应用启动到测试设置 localStorage 之间存在空窗期

## 💡 解决方案建议

### 方案 1：修改应用启动逻辑（推荐）

在 Vue 应用中添加认证状态检查延迟：

```typescript
// src/main.ts 或路由守卫中
const initializeAuth = async () => {
  // 等待可能的认证数据加载
  await new Promise(resolve => setTimeout(resolve, 100))

  // 检查 localStorage 中是否有认证数据
  const token = localStorage.getItem('access_token')
  const userStr = localStorage.getItem('user')

  if (token && userStr) {
    try {
      const user = JSON.parse(userStr)
      // 手动初始化 Pinia store
      const authStore = useAuthStore()
      authStore.user = user
      authStore.accessToken = token
      authStore.refreshToken = localStorage.getItem('refresh_token')
    } catch (error) {
      console.error('Failed to restore auth state:', error)
    }
  }
}
```

### 方案 2：改进测试设置逻辑

在测试中更早设置认证状态：

```typescript
test.beforeEach(async ({ context }) => {
  // 在创建页面之前就设置认证状态
  await context.addInitScript(() => {
    localStorage.setItem('user', JSON.stringify({
      id: 'test-user-id',
      role: 'teacher'
    }))
    localStorage.setItem('access_token', 'test-token')
  })
})
```

### 方案 3：使用浏览器上下文持久化

```typescript
test.use({
  storageState: 'e2e/.auth/storage-state.json',
  // 确保在每个测试中强制加载认证状态
  contextOptions: {
    ignoreHTTPSErrors: true,
    javaScriptEnabled: true
  }
})
```

### 方案 4：模拟登录 API 调用

创建一个测试专用的登录 API：

```typescript
// 测试中直接调用模拟登录 API
test.beforeEach(async ({ page }) => {
  // 模拟后端 API 响应
  await page.route('/api/auth/login', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        user: { id: '1', role: 'teacher' },
        access_token: 'test-token',
        refresh_token: 'test-refresh'
      })
    })
  })

  // 执行登录
  await page.goto('/login')
  await page.fill('[name=email]', 'test@example.com')
  await page.fill('[name=password]', 'password')
  await page.click('button[type=submit]')
})
```

## 📝 临时解决方案

为了快速验证测试功能，可以采用以下临时方案：

### 1. 修改路由守卫（开发环境）

```typescript
// src/router/index.ts
if (import.meta.env.DEV && import.meta.env.VITE_E2E_TEST) {
  // E2E 测试环境：跳过认证检查
  console.log('E2E test mode: skipping auth check')
  return next()
}
```

### 2. 添加测试标记

在测试中添加特殊标记，让应用识别测试环境：

```typescript
test.beforeEach(async ({ page }) => {
  // 设置测试标记
  await page.addInitScript(() => {
    window.__PLAYWRIGHT_TEST__ = true
    localStorage.setItem('test_mode', 'true')
  })
})
```

## 🎯 优先级建议

1. **高优先级**：修改应用启动逻辑（方案 1）
2. **中优先级**：改进测试设置逻辑（方案 2）
3. **低优先级**：使用浏览器上下文持久化（方案 3）

## 📊 成功标准

测试成功的标志：
- ✅ 能够访问题目编辑器页面
- ✅ 页面显示正确的标题和表单
- ✅ 能够切换题型
- ✅ 编辑器组件正常渲染
- ✅ 测试结果稳定可重现

## 📋 待办事项

- [ ] 实施应用启动逻辑改进
- [ ] 验证改进后的测试稳定性
- [ ] 编写测试用例文档
- [ ] 集成到 CI/CD 流水线
- [ ] 监控测试成功率
