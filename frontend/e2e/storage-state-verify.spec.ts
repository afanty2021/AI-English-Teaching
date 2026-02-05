/**
 * 验证 storageState 配置
 */
import { test, expect } from '@playwright/test'

test.use({
  storageState: 'e2e/.auth/storage-state.json'
})

test('storageState 应该包含所有认证数据', async ({ page }) => {
  // 直接检查 localStorage
  const localStore = await page.evaluate(() => {
    return {
      accessToken: localStorage.getItem('access_token'),
      refreshToken: localStorage.getItem('refresh_token'),
      user: localStorage.getItem('user'),
      allKeys: Object.keys(localStorage)
    }
  })

  console.log('StorageState check:', localStore)

  // 验证所有数据都存在
  expect(localStore.accessToken).toBeTruthy()
  expect(localStore.refreshToken).toBeTruthy()
  expect(localStore.user).toBeTruthy()
})
