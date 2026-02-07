<template>
  <div class="student-dashboard">
    <el-container>
      <el-header>
        <div class="header-content">
          <div class="header-left">
            <h1>学生中心</h1>
            <p class="welcome-text">
              欢迎回来，{{ studentName }}！继续你的英语学习之旅。
            </p>
          </div>
          <el-menu
            :default-active="activeMenu"
            mode="horizontal"
            :ellipsis="false"
            router
          >
            <el-menu-item index="/student">
              仪表板
            </el-menu-item>
            <el-menu-item index="/student/learning">
              学习内容
            </el-menu-item>
            <el-menu-item index="/student/speaking">
              口语练习
            </el-menu-item>
            <el-menu-item index="/student/mistakes">
              错题本
            </el-menu-item>
            <el-menu-item index="/student/reports">
              学习报告
            </el-menu-item>
            <el-menu-item index="/student/progress">
              学习进度
            </el-menu-item>
            <el-menu-item
              index="/"
              @click="handleLogout"
            >
              退出
            </el-menu-item>
          </el-menu>
        </div>
      </el-header>

      <el-main>
        <!-- 统计卡片 -->
        <el-row :gutter="20">
          <el-col :span="6">
            <el-card
              class="stat-card"
              shadow="hover"
            >
              <el-statistic
                title="今日学习时长"
                :value="stats.todayMinutes"
                suffix="分钟"
                :value-style="{ color: '#409eff' }"
              >
                <template #prefix>
                  <el-icon><Clock /></el-icon>
                </template>
              </el-statistic>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card
              class="stat-card"
              shadow="hover"
            >
              <el-statistic
                title="完成练习"
                :value="stats.completedExercises"
                suffix="个"
                :value-style="{ color: '#67c23a' }"
              >
                <template #prefix>
                  <el-icon><CircleCheck /></el-icon>
                </template>
              </el-statistic>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card
              class="stat-card"
              shadow="hover"
            >
              <el-statistic
                title="口语对话"
                :value="stats.conversations"
                suffix="次"
                :value-style="{ color: '#e6a23c' }"
              >
                <template #prefix>
                  <el-icon><ChatDotRound /></el-icon>
                </template>
              </el-statistic>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card
              class="stat-card"
              shadow="hover"
            >
              <el-statistic
                title="学习积分"
                :value="stats.points"
                :value-style="{ color: '#f56c6c' }"
              >
                <template #prefix>
                  <el-icon><Trophy /></el-icon>
                </template>
              </el-statistic>
            </el-card>
          </el-col>
        </el-row>

        <el-row
          :gutter="20"
          class="mt-3"
        >
          <!-- 今日推荐学习 -->
          <el-col :span="16">
            <el-card>
              <template #header>
                <div class="card-header">
                  <h3>今日推荐学习</h3>
                  <el-button
                    type="primary"
                    link
                    @click="loadData"
                  >
                    <el-icon><Refresh /></el-icon>
                    刷新
                  </el-button>
                </div>
              </template>

              <el-empty
                v-if="loading"
                description="加载中..."
              />
              <el-empty
                v-else-if="recommendations.length === 0"
                description="暂无推荐内容"
              />

              <div v-else>
                <div
                  v-for="item in recommendations.slice(0, 4)"
                  :key="item.id"
                  class="recommend-item"
                  @click="goToContent(item)"
                >
                  <div class="item-left">
                    <el-tag
                      :type="getLevelType(item.difficulty_level)"
                      size="small"
                    >
                      {{ item.difficulty_level }}
                    </el-tag>
                    <span class="item-title">{{ item.title }}</span>
                  </div>
                  <div class="item-right">
                    <span class="item-meta">{{ item.word_count }} 词</span>
                    <el-icon class="arrow-icon">
                      <ArrowRight />
                    </el-icon>
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>

          <!-- 学习动态 -->
          <el-col :span="8">
            <el-card>
              <template #header>
                <h3>学习动态</h3>
              </template>

              <el-timeline>
                <el-timeline-item
                  v-for="activity in activities"
                  :key="activity.id"
                  :timestamp="activity.time"
                  placement="top"
                >
                  <div class="activity-item">
                    <el-tag
                      :type="activity.type"
                      size="small"
                    >
                      {{ activity.label }}
                    </el-tag>
                    <p>{{ activity.description }}</p>
                  </div>
                </el-timeline-item>
              </el-timeline>
            </el-card>

            <!-- 学习目标 -->
            <el-card class="mt-2">
              <template #header>
                <h3>本周目标</h3>
              </template>

              <div class="goal-list">
                <div
                  v-for="goal in goals"
                  :key="goal.id"
                  class="goal-item"
                >
                  <div class="goal-header">
                    <span class="goal-title">{{ goal.title }}</span>
                    <span class="goal-progress">{{ goal.progress }}%</span>
                  </div>
                  <el-progress
                    :percentage="goal.progress"
                    :status="goal.progress >= 100 ? 'success' : ''"
                    :stroke-width="8"
                  />
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
import { ElMessageBox } from 'element-plus'
import {
  Clock,
  CircleCheck,
  ChatDotRound,
  Trophy,
  Refresh,
  ArrowRight
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)
const studentName = ref('同学')
const loading = ref(false)

// 统计数据
const stats = ref({
  todayMinutes: 25,
  completedExercises: 12,
  conversations: 5,
  points: 180
})

// 推荐内容
const recommendations = ref<any[]>([])

// 学习动态
const activities = ref([
  {
    id: '1',
    label: '阅读',
    type: 'primary',
    time: '10分钟前',
    description: '完成了《Daily Conversation》阅读'
  },
  {
    id: '2',
    label: '练习',
    type: 'success',
    time: '1小时前',
    description: '完成了5道词汇练习题'
  },
  {
    id: '3',
    label: '口语',
    type: 'warning',
    time: '昨天',
    description: '进行了购物场景对话练习'
  },
  {
    id: '4',
    label: '成就',
    type: 'danger',
    time: '2天前',
    description: '获得"连续学习7天"徽章'
  }
])

// 学习目标
const goals = ref([
  { id: '1', title: '完成3篇阅读', progress: 66 },
  { id: '2', title: '练习20个单词', progress: 45 },
  { id: '3', title: '口语对话5次', progress: 80 }
])

async function loadData() {
  loading.value = true
  try {
    const token = localStorage.getItem('access_token')
    const response = await axios.get(
      '/api/v1/contents/recommend',
      {
        headers: { Authorization: `Bearer ${token}` },
        params: { max_recommendations: 4 }
      }
    )

    recommendations.value = response.data.reading || []

    // 更新统计数据
    stats.value.completedExercises = response.data.exercises?.length || 0
  } catch (error) {
    console.error('加载数据失败:', error)
    // 使用模拟数据
    recommendations.value = [
      {
        id: '1',
        title: 'Weather Conversation',
        description: '学习讨论天气的常用表达',
        content_type: 'reading',
        difficulty_level: 'A1',
        word_count: 150
      },
      {
        id: '2',
        title: 'Shopping Vocabulary',
        description: '购物相关词汇学习',
        content_type: 'reading',
        difficulty_level: 'A2',
        word_count: 200
      },
      {
        id: '3',
        title: 'Daily Routines',
        description: '日常作息表达',
        content_type: 'reading',
        difficulty_level: 'A1',
        word_count: 180
      },
      {
        id: '4',
        title: 'Food and Drinks',
        description: '食物和饮料话题',
        content_type: 'reading',
        difficulty_level: 'A2',
        word_count: 220
      }
    ]
  } finally {
    loading.value = false
  }
}

function goToContent(_item: any) {
  // 跳转到学习内容页面并查看详情
  router.push('/student/learning')
}

function getLevelType(level: string) {
  const types: Record<string, string> = {
    A1: '',
    A2: 'success',
    B1: 'warning',
    B2: 'danger',
    C1: 'info',
    C2: 'primary'
  }
  return types[level] || ''
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
  // 获取用户信息
  const user = authStore.user
  if (user) {
    studentName.value = user.full_name || user.username || '同学'
  }
  loadData()
})
</script>

<style scoped>
.student-dashboard {
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

.mt-2 {
  margin-top: 20px;
}

.mt-3 {
  margin-top: 30px;
}

.recommend-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 8px;
}

.recommend-item:hover {
  background: #f5f7fa;
}

.item-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.item-title {
  font-weight: 500;
  color: #333;
}

.item-right {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #999;
  font-size: 12px;
}

.arrow-icon {
  transition: transform 0.3s;
}

.recommend-item:hover .arrow-icon {
  transform: translateX(4px);
  color: #409eff;
}

.activity-item {
  padding: 4px 0;
}

.activity-item p {
  margin: 4px 0 0;
  color: #666;
  font-size: 14px;
}

.goal-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.goal-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.goal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
}

.goal-title {
  color: #333;
  font-weight: 500;
}

.goal-progress {
  color: #409eff;
  font-weight: 600;
}
</style>
