<template>
  <div v-if="error" class="error-boundary">
    <el-result
      icon="error"
      title="页面出错了"
      :sub-title="errorMessage"
    >
      <template #extra>
        <el-button type="primary" @click="handleRetry">
          刷新重试
        </el-button>
        <el-button @click="handleReload">
          重新加载页面
        </el-button>
      </template>
    </el-result>
  </div>
  <slot v-else />
</template>

<script setup lang="ts">
import { ref, onErrorCaptured, computed } from 'vue'

/**
 * 错误边界组件
 *
 * 捕获子组件中的渲染错误，防止错误传播导致整个应用崩溃。
 * 显示友好的错误提示，并提供恢复操作。
 *
 * 使用方式：
 * <ErrorBoundary>
 *   <YourComponent />
 * </ErrorBoundary>
 */

interface ErrorInfo {
  message: string
  stack?: string
  componentName?: string
}

const error = ref<ErrorInfo | null>(null)

const errorMessage = computed(() => {
  if (!error.value) return ''
  return error.value.message || '发生未知错误'
})

/**
 * 捕获子组件错误
 */
onErrorCaptured((err: Error, instance, info) => {
  console.error('[ErrorBoundary] 捕获到错误:', err)

  error.value = {
    message: err.message || '发生错误',
    stack: err.stack,
    componentName: instance?.$options?.name || '未知组件'
  }

  // 阻止错误继续传播
  return false
})

/**
 * 重试 - 清除错误状态，让子组件重新渲染
 */
const handleRetry = () => {
  error.value = null
}

/**
 * 重新加载页面
 */
const handleReload = () => {
  window.location.reload()
}
</script>

<style scoped>
.error-boundary {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}
</style>
