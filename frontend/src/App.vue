<template>
  <el-config-provider :locale="zhCn">
    <div id="app">
      <ErrorBoundary>
        <router-view />
      </ErrorBoundary>
    </div>
  </el-config-provider>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import ErrorBoundary from '@/components/ErrorBoundary.vue'

const authStore = useAuthStore()

// 应用初始化时检查认证状态
onMounted(async () => {
  await authStore.checkAuth()
})
</script>

<style>
/* 全局样式重置 */
*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html,
body,
#app {
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue',
    Arial, 'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol',
    'Noto Color Emoji';
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #555;
}

/* Element Plus 样式覆盖 */
.el-card {
  border-radius: 8px;
}

.el-button {
  border-radius: 6px;
}

.el-input__wrapper {
  border-radius: 6px;
}

/* 工具类 */
.text-center {
  text-align: center;
}

.text-right {
  text-align: right;
}

.mt-1 {
  margin-top: 8px;
}

.mt-2 {
  margin-top: 16px;
}

.mt-3 {
  margin-top: 24px;
}

.mb-1 {
  margin-bottom: 8px;
}

.mb-2 {
  margin-bottom: 16px;
}

.mb-3 {
  margin-bottom: 24px;
}

.p-1 {
  padding: 8px;
}

.p-2 {
  padding: 16px;
}

.p-3 {
  padding: 24px;
}
</style>
