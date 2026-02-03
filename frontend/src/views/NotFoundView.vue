<template>
  <div class="not-found-container">
    <div class="not-found-content">
      <h1>404</h1>
      <p>抱歉，您访问的页面不存在</p>
      <el-button type="primary" @click="goBack">返回首页</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

function goBack() {
  router.push('/')
}
</script>

<style scoped>
.not-found-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f5f7fa;
}

.not-found-content {
  text-align: center;
}

.not-found-content h1 {
  font-size: 120px;
  font-weight: bold;
  color: #667eea;
  margin: 0;
}

.not-found-content p {
  font-size: 18px;
  color: #666;
  margin: 20px 0 40px;
}
</style>
