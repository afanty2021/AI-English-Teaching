<template>
  <div class="home-container">
    <el-container>
      <el-header>
        <div class="header-content">
          <h1>AI英语教学系统</h1>
          <div class="user-info">
            <el-button link @click="$router.push('/settings')">
              <el-icon><Setting /></el-icon>
              通知设置
            </el-button>
            <span>{{ authStore.user?.full_name || authStore.user?.username }}</span>
            <el-button @click="handleLogout" type="danger" size="small">退出登录</el-button>
          </div>
        </div>
      </el-header>

      <el-main>
        <el-row :gutter="20">
          <el-col :span="24" v-if="authStore.isStudent">
            <el-card class="welcome-card">
              <h2>欢迎回来，{{ authStore.user?.full_name }}同学！</h2>
              <p class="subtitle">开始你的英语学习之旅</p>
              <el-space wrap>
                <el-button type="primary" size="large" @click="$router.push('/student/learning')">
                  开始学习
                </el-button>
                <el-button type="success" size="large" @click="$router.push('/student/speaking')">
                  口语练习
                </el-button>
                <el-button type="info" size="large" @click="$router.push('/student/progress')">
                  学习进度
                </el-button>
              </el-space>
            </el-card>
          </el-col>

          <el-col :span="24" v-else-if="authStore.isTeacher">
            <el-card class="welcome-card">
              <h2>欢迎回来，{{ authStore.user?.full_name }}老师！</h2>
              <p class="subtitle">管理您的教学内容和学生</p>
              <el-space wrap>
                <el-button type="primary" size="large" @click="$router.push('/teacher/lessons')">
                  教案管理
                </el-button>
                <el-button type="success" size="large" @click="$router.push('/teacher/shared-lessons')">
                  分享的教案
                </el-button>
                <el-button type="warning" size="large" @click="$router.push('/teacher/students')">
                  学生管理
                </el-button>
                <el-button type="info" size="large" @click="$router.push('/teacher/ai-planning')">
                  AI 备课
                </el-button>
              </el-space>
            </el-card>
          </el-col>
        </el-row>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { Setting } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

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
.home-container {
  min-height: 100vh;
  background: #f5f7fa;
}

.el-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h1 {
  margin: 0;
  font-size: 24px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.el-main {
  padding: 40px 20px;
}

.welcome-card {
  max-width: 800px;
  margin: 0 auto;
  text-align: center;
  padding: 40px;
}

.welcome-card h2 {
  font-size: 32px;
  color: #333;
  margin-bottom: 12px;
}

.subtitle {
  font-size: 18px;
  color: #666;
  margin-bottom: 32px;
}
</style>
