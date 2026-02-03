<template>
  <div class="progress-page">
    <el-container>
      <el-header>
        <div class="header-content">
          <h1>学习进度</h1>
          <el-menu
            :default-active="activeMenu"
            mode="horizontal"
            :ellipsis="false"
            router
          >
            <el-menu-item index="/student">仪表板</el-menu-item>
            <el-menu-item index="/student/learning">学习内容</el-menu-item>
            <el-menu-item index="/student/speaking">口语练习</el-menu-item>
            <el-menu-item index="/student/progress">学习进度</el-menu-item>
            <el-menu-item index="/" @click="handleLogout">退出</el-menu-item>
          </el-menu>
        </div>
      </el-header>

      <el-main>
        <el-row :gutter="20">
          <el-col :span="16">
            <el-card>
              <template #header>
                <h3>能力评估</h3>
              </template>

              <el-empty description="暂无评估数据" />
            </el-card>
          </el-col>

          <el-col :span="8">
            <el-card>
              <template #header>
                <h3>CEFR 等级</h3>
              </template>

              <el-empty description="暂无等级数据" />
            </el-card>
          </el-col>
        </el-row>

        <el-card class="mt-2">
          <template #header>
            <h3>薄弱知识点</h3>
          </template>

          <el-empty description="暂无薄弱点分析" />
        </el-card>

        <el-card class="mt-2">
          <template #header>
            <h3>学习建议</h3>
          </template>

          <el-empty description="暂无学习建议" />
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)

async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    authStore.logout()
    router.push('/login')
  } catch {
    // 用户取消
  }
}
</script>

<style scoped>
.progress-page {
  min-height: 100vh;
  background: #f5f7fa;
}

.el-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0 20px;
}

.header-content {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-content h1 {
  margin: 0;
  font-size: 24px;
  color: white;
}

.el-main {
  padding: 20px;
}

.el-main h3 {
  margin: 0;
}
</style>
