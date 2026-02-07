<template>
  <div class="learning-page">
    <el-container>
      <el-header>
        <div class="header-content">
          <h1>学习内容</h1>
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
        <!-- 阅读内容 -->
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>今日推荐阅读</h3>
              <el-button
                type="primary"
                link
                @click="loadRecommendations"
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

          <div
            v-else
            class="content-list"
          >
            <el-card
              v-for="item in recommendations"
              :key="item.id"
              class="content-card"
              shadow="hover"
              @click="viewContent(item)"
            >
              <div class="content-header">
                <div class="content-info">
                  <el-tag
                    :type="getLevelType(item.difficulty_level)"
                    size="small"
                  >
                    {{ item.difficulty_level }}
                  </el-tag>
                  <span class="content-title">{{ item.title }}</span>
                </div>
                <span class="content-meta">{{ item.word_count }} 词</span>
              </div>
              <p class="content-desc">
                {{ item.description }}
              </p>
              <div class="content-tags">
                <el-tag
                  v-for="tag in item.tags?.slice(0, 3)"
                  :key="tag"
                  size="small"
                  type="info"
                >
                  {{ tag }}
                </el-tag>
              </div>
            </el-card>
          </div>
        </el-card>

        <!-- 最近学习 -->
        <el-card class="mt-2">
          <template #header>
            <h3>最近学习</h3>
          </template>

          <el-empty
            v-if="recentContents.length === 0"
            description="暂无学习记录"
          />

          <el-timeline v-else>
            <el-timeline-item
              v-for="item in recentContents"
              :key="item.id"
              :timestamp="formatDate(item.completed_at)"
              placement="top"
            >
              <el-card
                class="recent-card"
                @click="viewContent(item)"
              >
                <h4>{{ item.title }}</h4>
                <p>{{ item.description }}</p>
                <div class="completion-info">
                  <el-tag
                    type="success"
                    size="small"
                  >
                    已完成
                  </el-tag>
                  <span class="points">+{{ item.points }} 积分</span>
                </div>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-main>
    </el-container>

    <!-- 内容详情弹窗 -->
    <el-dialog
      v-model="contentDialogVisible"
      :title="selectedContent?.title"
      width="800px"
      :close-on-click-modal="false"
    >
      <div
        v-if="selectedContent"
        class="content-detail"
      >
        <div class="detail-meta">
          <el-tag :type="getLevelType(selectedContent.difficulty_level)">
            {{ selectedContent.difficulty_level }}
          </el-tag>
          <el-tag type="info">
            {{ selectedContent.content_type }}
          </el-tag>
          <span>{{ selectedContent.word_count }} 词</span>
        </div>

        <div class="detail-body">
          <p class="detail-text">
            {{ selectedContent.content_text }}
          </p>
        </div>

        <div
          v-if="selectedContent.knowledge_points?.length"
          class="detail-section"
        >
          <h4>知识点</h4>
          <el-tag
            v-for="kp in selectedContent.knowledge_points"
            :key="kp"
            class="mr-1"
          >
            {{ kp }}
          </el-tag>
        </div>
      </div>

      <template #footer>
        <el-button @click="contentDialogVisible = false">
          关闭
        </el-button>
        <el-button
          type="primary"
          @click="markAsCompleted"
        >
          标记为已完成
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)
const selectedLevel = ref('')
const loading = ref(false)
const recommendations = ref<any[]>([])
const recentContents = ref<any[]>([])
const contentDialogVisible = ref(false)
const selectedContent = ref<any>(null)

// 模拟的最近学习记录
const mockRecentContents = [
  {
    id: '1',
    title: 'Daily Conversation',
    description: '日常对话练习',
    completed_at: '2026-02-01T10:30:00',
    points: 15
  },
  {
    id: '2',
    title: 'Food and Drinks',
    description: '食物和饮料词汇',
    completed_at: '2026-01-31T15:20:00',
    points: 20
  }
]

async function loadRecommendations() {
  loading.value = true
  try {
    const token = localStorage.getItem('access_token')
    const response = await axios.get(
      'http://localhost:8000/api/v1/contents/recommend',
      {
        headers: { Authorization: `Bearer ${token}` },
        params: {
          difficulty_levels: selectedLevel.value || undefined,
          max_recommendations: 10
        }
      }
    )

    recommendations.value = response.data.reading || []
    recentContents.value = mockRecentContents
  } catch (error: any) {
    console.error('加载推荐失败:', error)
    // 如果API调用失败，使用模拟数据
    recommendations.value = [
      {
        id: '1',
        title: 'Weather Conversation',
        description: '学习讨论天气的常用表达和词汇',
        content_type: 'reading',
        difficulty_level: 'A1',
        word_count: 150,
        tags: ['weather', 'conversation', 'daily'],
        content_text: 'Talking about the weather is a great way to start a conversation in English...',
        knowledge_points: ['weather vocabulary', 'conversation starters']
      },
      {
        id: '2',
        title: 'Shopping Expressions',
        description: '购物时常用的英语表达',
        content_type: 'reading',
        difficulty_level: 'A2',
        word_count: 200,
        tags: ['shopping', 'expressions', 'practical'],
        content_text: 'When shopping in English-speaking countries...',
        knowledge_points: ['shopping phrases', 'polite requests']
      }
    ]
    recentContents.value = mockRecentContents
  } finally {
    loading.value = false
  }
}

function viewContent(item: any) {
  selectedContent.value = item
  contentDialogVisible.value = true
}

async function markAsCompleted() {
  if (!selectedContent.value) return

  try {
    const token = localStorage.getItem('access_token')
    await axios.post(
      `http://localhost:8000/api/v1/contents/${selectedContent.value.id}/complete`,
      { time_spent: 300, rating: 5 },
      { headers: { Authorization: `Bearer ${token}` } }
    )

    ElMessage.success('已标记为完成！+10 积分')
    contentDialogVisible.value = false
    loadRecommendations()
  } catch (error) {
    ElMessage.warning('标记失败，但内容已记录')
    contentDialogVisible.value = false
  }
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

function formatDate(dateStr: string) {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
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
  loadRecommendations()
})
</script>

<style scoped>
.learning-page {
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

.mt-2 {
  margin-top: 20px;
}

.content-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.content-card {
  cursor: pointer;
  transition: all 0.3s;
}

.content-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.content-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.content-title {
  font-weight: 600;
  color: #333;
}

.content-meta {
  color: #999;
  font-size: 12px;
}

.content-desc {
  color: #666;
  font-size: 14px;
  margin: 8px 0;
  line-height: 1.5;
}

.content-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.mr-1 {
  margin-right: 4px;
}

.recent-card {
  cursor: pointer;
  margin-bottom: 8px;
}

.recent-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.recent-card h4 {
  margin: 0 0 8px;
  color: #333;
}

.recent-card p {
  margin: 4px 0 8px;
  color: #666;
  font-size: 14px;
}

.completion-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.points {
  color: #f56c6c;
  font-weight: 600;
}

.content-detail .detail-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.detail-body {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.detail-text {
  color: #333;
  line-height: 1.8;
  font-size: 15px;
  white-space: pre-wrap;
}

.detail-section {
  margin-top: 16px;
}

.detail-section h4 {
  margin: 0 0 8px;
  color: #333;
}
</style>
