<template>
  <div class="teacher-dashboard">
    <el-container>
      <el-header>
        <div class="header-content">
          <div class="header-left">
            <h1>教师中心</h1>
            <p class="welcome-text">欢迎回来，{{ teacherName }}！准备好今天的教学了吗？</p>
          </div>
          <el-menu
            :default-active="activeMenu"
            mode="horizontal"
            :ellipsis="false"
            router
          >
            <el-menu-item index="/teacher">仪表板</el-menu-item>
            <el-menu-item index="/teacher/lessons">教案管理</el-menu-item>
            <el-menu-item index="/teacher/students">学生管理</el-menu-item>
            <el-menu-item index="/teacher/reports">学生报告</el-menu-item>
            <el-menu-item index="/teacher/ai-planning">AI 备课</el-menu-item>
            <el-menu-item index="/" @click="handleLogout">退出</el-menu-item>
          </el-menu>
        </div>
      </el-header>

      <el-main>
        <!-- 统计卡片 -->
        <el-row :gutter="20">
          <el-col :span="6">
            <el-card class="stat-card" shadow="hover" @click="goTo('/teacher/students')">
              <el-statistic
                title="学生总数"
                :value="stats.studentCount"
                :value-style="{ color: '#409eff' }"
              >
                <template #prefix>
                  <el-icon><User /></el-icon>
                </template>
              </el-statistic>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card" shadow="hover" @click="goTo('/teacher/lessons')">
              <el-statistic
                title="教案数量"
                :value="stats.lessonCount"
                :value-style="{ color: '#67c23a' }"
              >
                <template #prefix>
                  <el-icon><Document /></el-icon>
                </template>
              </el-statistic>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card" shadow="hover">
              <el-statistic
                title="今日活跃"
                :value="stats.todayActive"
                :value-style="{ color: '#e6a23c' }"
              >
                <template #prefix>
                  <el-icon><TrendCharts /></el-icon>
                </template>
              </el-statistic>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card" shadow="hover">
              <el-statistic
                title="本周生成"
                :value="stats.weeklyGenerated"
                :value-style="{ color: '#f56c6c' }"
              >
                <template #prefix>
                  <el-icon><MagicStick /></el-icon>
                </template>
              </el-statistic>
            </el-card>
          </el-col>
        </el-row>

        <el-row :gutter="20" class="mt-3">
          <!-- 最近教案 -->
          <el-col :span="12">
            <el-card>
              <template #header>
                <div class="card-header">
                  <h3>最近教案</h3>
                  <el-button type="primary" link @click="goTo('/teacher/lessons')">
                    查看全部
                    <el-icon><ArrowRight /></el-icon>
                  </el-button>
                </div>
              </template>

              <el-empty v-if="loading" description="加载中..." />
              <el-empty v-else-if="recentLessons.length === 0" description="暂无教案，去AI备课创建一个吧！">
                <el-button type="primary" @click="goTo('/teacher/ai-planning')">
                  <el-icon><Plus /></el-icon>
                  创建教案
                </el-button>
              </el-empty>

              <div v-else>
                <div
                  v-for="lesson in recentLessons"
                  :key="lesson.id"
                  class="lesson-item"
                  @click="goTo(`/teacher/lessons?id=${lesson.id}`)"
                >
                  <div class="lesson-header">
                    <div class="lesson-info">
                      <el-tag :type="getStatusType(lesson.status)" size="small">
                        {{ getStatusText(lesson.status) }}
                      </el-tag>
                      <span class="lesson-title">{{ lesson.title }}</span>
                    </div>
                    <span class="lesson-time">{{ formatDate(lesson.created_at) }}</span>
                  </div>
                  <div class="lesson-meta">
                    <span>{{ lesson.topic }}</span>
                    <el-divider direction="vertical" />
                    <span>{{ lesson.level }}</span>
                    <el-divider direction="vertical" />
                    <span>{{ lesson.duration }}分钟</span>
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>

          <!-- 快速操作 -->
          <el-col :span="12">
            <el-card>
              <template #header>
                <h3>快速操作</h3>
              </template>

              <div class="quick-actions">
                <el-button
                  type="primary"
                  size="large"
                  :icon="MagicStick"
                  @click="goTo('/teacher/ai-planning')"
                  class="action-btn"
                >
                  AI 生成教案
                </el-button>
                <el-button
                  size="large"
                  :icon="Document"
                  @click="goTo('/teacher/lessons')"
                  class="action-btn"
                >
                  管理教案
                </el-button>
                <el-button
                  size="large"
                  :icon="User"
                  @click="goTo('/teacher/students')"
                  class="action-btn"
                >
                  学生管理
                </el-button>
              </div>

              <!-- 教案统计图表 -->
              <div class="mt-3">
                <h4>本周教案生成趋势</h4>
                <div class="chart-placeholder">
                  <el-progress
                    v-for="(item, index) in chartData"
                    :key="index"
                    class="chart-item"
                  >
                    <span class="chart-label">{{ item.day }}</span>
                    <el-progress
                      :percentage="item.percentage"
                      :show-text="false"
                      :stroke-width="12"
                      :color="item.color"
                    />
                    <span class="chart-value">{{ item.count }}</span>
                  </el-progress>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User,
  Document,
  TrendCharts,
  MagicStick,
  ArrowRight,
  Plus
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)
const teacherName = ref('老师')
const loading = ref(false)

// 统计数据
const stats = ref({
  studentCount: 0,
  lessonCount: 0,
  todayActive: 0,
  weeklyGenerated: 0
})

// 最近教案
const recentLessons = ref<any[]>([])

// 图表数据
const chartData = ref([
  { day: '周一', count: 2, percentage: 40, color: '#409eff' },
  { day: '周二', count: 3, percentage: 60, color: '#67c23a' },
  { day: '周三', count: 1, percentage: 20, color: '#e6a23c' },
  { day: '周四', count: 4, percentage: 80, color: '#f56c6c' },
  { day: '今天', count: 1, percentage: 20, color: '#909399' }
])

async function loadData() {
  loading.value = true
  try {
    const token = localStorage.getItem('access_token')

    // 并行请求多个API
    const [lessonsResp] = await Promise.all([
      axios.get('http://localhost:8000/api/v1/lesson-plans/', {
        headers: { Authorization: `Bearer ${token}` },
        params: { page: 1, page_size: 5 }
      })
    ])

    // 更新统计数据
    const lessons = lessonsResp.data.lesson_plans || []
    recentLessons.value = lessons.slice(0, 5)
    stats.value.lessonCount = lessonsResp.data.total || 0

    // 模拟其他数据
    stats.value.studentCount = 15
    stats.value.todayActive = 8
    stats.value.weeklyGenerated = lessonsResp.data.total || 0

  } catch (error) {
    console.error('加载数据失败:', error)
    // 使用模拟数据
    recentLessons.value = [
      {
        id: '1',
        title: '基础词汇课',
        topic: 'numbers',
        level: 'A1',
        duration: 30,
        status: 'generated',
        created_at: new Date().toISOString()
      },
      {
        id: '2',
        title: 'Daily Routines',
        topic: 'daily_routines',
        level: 'A2',
        duration: 45,
        status: 'generated',
        created_at: new Date(Date.now() - 86400000).toISOString()
      }
    ]
    stats.value = {
      studentCount: 15,
      lessonCount: 11,
      todayActive: 8,
      weeklyGenerated: 11
    }
  } finally {
    loading.value = false
  }
}

function goTo(path: string) {
  router.push(path)
}

function getStatusType(status: string) {
  const types: Record<string, string> = {
    generated: 'success',
    draft: 'info',
    published: 'primary'
  }
  return types[status] || 'info'
}

function getStatusText(status: string) {
  const texts: Record<string, string> = {
    generated: '已生成',
    draft: '草稿',
    published: '已发布'
  }
  return texts[status] || status
}

function formatDate(dateStr: string) {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) {
    const hours = Math.floor(diff / (1000 * 60 * 60))
    if (hours === 0) {
      const minutes = Math.floor(diff / (1000 * 60))
      return `${minutes}分钟前`
    }
    return `${hours}小时前`
  } else if (days === 1) {
    return '昨天'
  } else if (days < 7) {
    return `${days}天前`
  } else {
    return date.toLocaleDateString('zh-CN')
  }
}

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

onMounted(() => {
  const user = authStore.user
  if (user) {
    teacherName.value = user.full_name || user.username || '老师'
  }
  loadData()
})
</script>

<style scoped>
.teacher-dashboard {
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

.header-left h1 {
  margin: 0;
  font-size: 24px;
  color: white;
}

.welcome-text {
  margin: 4px 0 0;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
}

.el-main {
  padding: 20px;
}

.stat-card {
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
}

.mt-3 {
  margin-top: 20px;
}

.lesson-item {
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 8px;
  border: 1px solid #ebeef5;
}

.lesson-item:hover {
  background: #f5f7fa;
  border-color: #667eea;
}

.lesson-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.lesson-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.lesson-title {
  font-weight: 500;
  color: #333;
}

.lesson-time {
  color: #999;
  font-size: 12px;
}

.lesson-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #666;
  font-size: 14px;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-btn {
  width: 100%;
}

.chart-placeholder {
  margin-top: 16px;
}

.chart-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.chart-label {
  width: 40px;
  color: #666;
}

.chart-item .el-progress {
  flex: 1;
}

.chart-value {
  width: 30px;
  text-align: right;
  font-weight: 600;
  color: #333;
}
</style>
