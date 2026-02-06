/**
 * 应用入口文件
 * 初始化 Vue 应用、插件和全局配置
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

import App from './App.vue'
import router from './router'

// 创建 Vue 应用实例
const app = createApp(App)

// 创建 Pinia 状态管理
const pinia = createPinia()

// 注册插件
app.use(pinia)
app.use(router)
app.use(ElementPlus, {
  locale: zhCn
})

// 注册所有 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 挂载应用
app.mount('#app')

/**
 * 全局错误处理
 *
 * 1. Vue 错误处理 - 捕获组件渲染错误
 * 2. Promise 错误处理 - 捕获未处理的 Promise 拒绝
 * 3. window 错误处理 - 捕获全局 JavaScript 错误
 */

// Vue 组件错误处理
app.config.errorHandler = (err, instance, info) => {
  console.error('[Vue Error]', err)
  console.error('[Vue Error Component]', instance)
  console.error('[Vue Error Info]', info)

  // 可以在这里集成错误报告服务
  // reportErrorToService(err, info)
}

// Promise 未捕获错误处理
window.addEventListener('unhandledrejection', (event) => {
  console.error('[Promise Error]', event.reason)
  event.preventDefault()
})

// 全局 JavaScript 错误处理
window.addEventListener('error', (event) => {
  console.error('[Global Error]', event.error)
})
