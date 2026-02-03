<template>
  <div class="students-page">
    <el-container>
      <el-header>
        <div class="header-content">
          <h1>学生管理</h1>
          <el-menu
            :default-active="activeMenu"
            mode="horizontal"
            :ellipsis="false"
            router
          >
            <el-menu-item index="/teacher">仪表板</el-menu-item>
            <el-menu-item index="/teacher/lessons">教案管理</el-menu-item>
            <el-menu-item index="/teacher/students">学生管理</el-menu-item>
            <el-menu-item index="/teacher/ai-planning">AI 备课</el-menu-item>
            <el-menu-item index="/" @click="handleLogout">退出</el-menu-item>
          </el-menu>
        </div>
      </el-header>

      <el-main>
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>学生列表</h3>
              <el-input
                v-model="searchText"
                placeholder="搜索学生"
                style="width: 200px"
                clearable
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </div>
          </template>

          <el-empty description="暂无学生" />
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)
const searchText = ref('')

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
.students-page {
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

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
}
</style>
