<template>
  <div class="daily-recommendations">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <el-icon><Calendar /></el-icon>
          每日推荐
        </h1>
        <p class="page-subtitle">
          基于您的学习进度和知识图谱，为您推荐个性化学习内容
        </p>
      </div>
      <div class="header-actions">
        <el-button @click="refreshRecommendations" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新推荐
        </el-button>
      </div>
    </div>

    <!-- 学生画像概览 -->
    <el-card class="profile-card" v-if="studentProfile">
      <template #header>
        <div class="card-header">
          <span>学习画像</span>
        </div>
      </template>
      <div class="profile-content">
        <div class="profile-item">
          <label>当前水平：</label>
          <el-tag type="primary">{{ studentProfile.current_cefr_level || '未评估' }}</el-tag>
        </div>
        <div class="profile-item">
          <label>目标考试：</label>
          <el-tag type="success">{{ studentProfile.target_exam || '无' }}</el-tag>
        </div>
        <div class="profile-item">
          <label>目标分数：</label>
          <el-tag type="warning">{{ studentProfile.target_score || '未设置' }}</el-tag>
        </div>
      </div>
    </el-card>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="8" animated />
    </div>

    <!-- 推荐内容 -->
    <div v-else class="recommendations-content">
      <!-- 阅读推荐 -->
      <el-card class="recommendation-section" v-if="recommendations.reading?.length">
        <template #header>
          <div class="section-header">
            <h3>
              <el-icon><Document /></el-icon>
              阅读推荐 ({{ recommendations.reading.length }})
            </h3>
            <el-tag type="info">建议用时：{{ getReadingTime(recommendations.reading) }}分钟</el-tag>
          </div>
        </template>
        <div class="recommendation-list">
          <div
            v-for="item in recommendations.reading"
            :key="item.content_id"
            class="recommendation-item"
          >
            <div class="item-header">
              <h4 class="item-title">{{ item.title }}</h4>
              <div class="item-meta">
                <el-tag size="small">{{ item.difficulty_level }}</el-tag>
                <el-tag size="small" type="info">{{ item.word_count }}词</el-tag>
                <el-tag size="small" type="success" v-if="item.topic">{{ item.topic }}</el-tag>
              </div>
            </div>
            <p class="item-description">{{ item.description }}</p>
            <div class="item-reason">
              <el-icon><Star /></el-icon>
              <span>{{ item.recommendation_reason }}</span>
            </div>
            <div class="item-actions">
              <el-button type="primary" size="small" @click="startReading(item)">
                开始阅读
              </el-button>
              <el-button size="small" @click="previewContent(item)">
                预览
              </el-button>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 听力推荐 -->
      <el-card class="recommendation-section" v-if="recommendations.listening?.length">
        <template #header>
          <div class="section-header">
            <h3>
              <el-icon><Headphone /></el-icon>
              听力推荐 ({{ recommendations.listening.length }})
            </h3>
            <el-tag type="info">建议用时：{{ getListeningTime(recommendations.listening) }}分钟</el-tag>
          </div>
        </template>
        <div class="recommendation-list">
          <div
            v-for="item in recommendations.listening"
            :key="item.content_id"
            class="recommendation-item"
          >
            <div class="item-header">
              <h4 class="item-title">{{ item.title }}</h4>
              <div class="item-meta">
                <el-tag size="small">{{ item.difficulty_level }}</el-tag>
                <el-tag size="small" type="info">{{ item.duration }}秒</el-tag>
              </div>
            </div>
            <p class="item-description">{{ item.description }}</p>
            <div class="item-actions">
              <el-button type="primary" size="small" @click="startListening(item)">
                开始听力
              </el-button>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 词汇推荐 -->
      <el-card class="recommendation-section" v-if="recommendations.vocabulary?.length">
        <template #header>
          <div class="section-header">
            <h3>
              <el-icon><EditPen /></el-icon>
              词汇推荐 ({{ recommendations.vocabulary.length }})
            </h3>
            <el-tag type="info">{{ recommendations.vocabulary.length }}个词汇</el-tag>
          </div>
        </template>
        <div class="vocabulary-grid">
          <div
            v-for="item in recommendations.vocabulary"
            :key="item.vocabulary_id"
            class="vocabulary-item"
          >
            <div class="word">{{ item.word }}</div>
            <div class="phonetic">{{ item.phonetic }}</div>
            <div class="definition">{{ item.definition }}</div>
            <div class="example">{{ item.example }}</div>
            <el-button size="small" @click="markVocabularyKnown(item)">
              已掌握
            </el-button>
          </div>
        </div>
      </el-card>

      <!-- 语法推荐 -->
      <el-card class="recommendation-section" v-if="recommendations.grammar?.length">
        <template #header>
          <div class="section-header">
            <h3>
              <el-icon><Edit /></el-icon>
              语法推荐 ({{ recommendations.grammar.length }})
            </h3>
            <el-tag type="info">{{ recommendations.grammar.length }}个语法点</el-tag>
          </div>
        </template>
        <div class="grammar-list">
          <div
            v-for="item in recommendations.grammar"
            :key="item.grammar_point"
            class="grammar-item"
          >
            <h4 class="grammar-title">{{ item.grammar_point }}</h4>
            <p class="grammar-rule">{{ item.rule }}</p>
            <div class="grammar-examples">
              <div v-for="example in item.examples" :key="example" class="example-item">
                {{ example }}
              </div>
            </div>
            <el-button type="primary" size="small" @click="startGrammarPractice(item)">
              练习语法
            </el-button>
          </div>
        </div>
      </el-card>

      <!-- 口语推荐 -->
      <el-card class="recommendation-section" v-if="recommendations.speaking">
        <template #header>
          <div class="section-header">
            <h3>
              <el-icon><Microphone /></el-icon>
              口语练习
            </h3>
          </div>
        </template>
        <div class="speaking-content">
          <div class="scenario-info">
            <h4>{{ recommendations.speaking.scenario_name }}</h4>
            <p>难度：{{ recommendations.speaking.level }}</p>
            <p>{{ recommendations.speaking.description }}</p>
          </div>
          <el-button type="primary" @click="startSpeaking(recommendations.speaking)">
            开始对话
          </el-button>
        </div>
      </el-card>

      <!-- 空状态 -->
      <el-empty
        v-if="!hasAnyRecommendations"
        description="暂无推荐内容"
      >
        <el-button type="primary" @click="refreshRecommendations">
          刷新推荐
        </el-button>
      </el-empty>
    </div>

    <!-- 推荐反馈对话框 -->
    <el-dialog
      v-model="feedbackDialogVisible"
      title="推荐反馈"
      width="400px"
    >
      <el-form :model="feedbackForm" label-width="80px">
        <el-form-item label="满意度">
          <el-rate v-model="feedbackForm.satisfaction" :max="5" />
        </el-form-item>
        <el-form-item label="理由">
          <el-input
            v-model="feedbackForm.reason"
            type="textarea"
            :rows="3"
            placeholder="请说明您的理由"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="feedbackDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitFeedback">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Calendar,
  Refresh,
  Document,
  EditPen,
  Edit,
  Microphone,
  Star
} from '@element-plus/icons-vue'
import { useRecommendationStore } from '@/stores/recommendation'
import type { DailyRecommendations, StudentProfile } from '@/types/recommendation'

const router = useRouter()
const recommendationStore = useRecommendationStore()

// 响应式数据
const loading = ref(false)
const recommendations = ref<DailyRecommendations>({
  reading: [],
  listening: [],
  vocabulary: [],
  grammar: [],
  speaking: null
})
const studentProfile = ref<StudentProfile | null>(null)
const feedbackDialogVisible = ref(false)
const feedbackForm = reactive({
  contentId: '',
  satisfaction: 0,
  reason: ''
})

// 计算属性
const hasAnyRecommendations = computed(() => {
  return (
    recommendations.value.reading?.length > 0 ||
    recommendations.value.listening?.length > 0 ||
    recommendations.value.vocabulary?.length > 0 ||
    recommendations.value.grammar?.length > 0 ||
    recommendations.value.speaking
  )
})

// 方法
const refreshRecommendations = async () => {
  loading.value = true
  try {
    // 获取推荐内容
    const result = await recommendationStore.getDailyRecommendations()
    recommendations.value = result.recommendations
    studentProfile.value = result.studentProfile

    ElMessage.success('推荐内容已更新')
  } catch (error) {
    console.error('获取推荐失败:', error)
    ElMessage.error('获取推荐内容失败')
  } finally {
    loading.value = false
  }
}

const getReadingTime = (items: any[]) => {
  // 根据字数估算阅读时间（每分钟200词）
  const totalWords = items.reduce((sum, item) => sum + (item.word_count || 0), 0)
  return Math.ceil(totalWords / 200)
}

const getListeningTime = (items: any[]) => {
  // 听力时间总和
  const totalSeconds = items.reduce((sum, item) => sum + (item.duration || 0), 0)
  return Math.ceil(totalSeconds / 60)
}

const startReading = (item: any) => {
  router.push(`/student/reading/${item.content_id}`)
}

const previewContent = (item: any) => {
  // 预览内容
  ElMessageBox.confirm(
    `<div style="max-height: 400px; overflow-y: auto;">
      <h4>${item.title}</h4>
      <p>${item.content_preview || '暂无预览'}</p>
    </div>`,
    '内容预览',
    {
      confirmButtonText: '开始阅读',
      cancelButtonText: '关闭',
      dangerouslyUseHTMLString: true
    }
  ).then(() => {
    startReading(item)
  })
}

const startListening = (item: any) => {
  router.push(`/student/listening/${item.content_id}`)
}

const startGrammarPractice = (item: any) => {
  router.push(`/student/practice?type=grammar&point=${encodeURIComponent(item.grammar_point)}`)
}

const startSpeaking = (item: any) => {
  router.push(`/student/speaking?scenario=${encodeURIComponent(item.scenario)}`)
}

const markVocabularyKnown = (item: any) => {
  ElMessage.success(`已标记"${item.word}"为已掌握`)
  // TODO: 调用API标记词汇为已掌握
}

// showFeedbackDialog reserved for future feedback functionality
// const _showFeedbackDialog = (contentId: string) => {
//   feedbackForm.contentId = contentId
//   feedbackForm.satisfaction = 0
//   feedbackForm.reason = ''
//   feedbackDialogVisible.value = true
// }

const submitFeedback = () => {
  if (feedbackForm.satisfaction === 0) {
    ElMessage.warning('请选择满意度评分')
    return
  }

  // TODO: 调用API提交反馈
  ElMessage.success('反馈已提交，感谢您的建议！')
  feedbackDialogVisible.value = false
}

// 生命周期
onMounted(() => {
  refreshRecommendations()
})
</script>

<style scoped>
.daily-recommendations {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.header-content {
  flex: 1;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.page-subtitle {
  color: #606266;
  font-size: 14px;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.profile-card {
  margin-bottom: 24px;
}

.profile-content {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.profile-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.profile-item label {
  font-weight: 500;
  color: #606266;
}

.loading-container {
  margin: 40px 0;
}

.recommendations-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.recommendation-section {
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.recommendation-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.recommendation-item {
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  transition: all 0.3s;
}

.recommendation-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.item-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.item-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.item-description {
  color: #606266;
  line-height: 1.6;
  margin: 0 0 12px 0;
}

.item-reason {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #909399;
  font-size: 14px;
  margin-bottom: 12px;
}

.item-actions {
  display: flex;
  gap: 8px;
}

.vocabulary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 16px;
}

.vocabulary-item {
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  text-align: center;
}

.vocabulary-item .word {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.vocabulary-item .phonetic {
  color: #909399;
  font-size: 14px;
  margin-bottom: 8px;
}

.vocabulary-item .definition {
  color: #606266;
  margin-bottom: 8px;
}

.vocabulary-item .example {
  color: #909399;
  font-size: 14px;
  font-style: italic;
  margin-bottom: 12px;
}

.grammar-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.grammar-item {
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
}

.grammar-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.grammar-rule {
  color: #606266;
  line-height: 1.6;
  margin: 0 0 12px 0;
}

.grammar-examples {
  margin-bottom: 12px;
}

.example-item {
  padding: 8px;
  background-color: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 4px;
  font-size: 14px;
  color: #606266;
}

.speaking-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
}

.scenario-info h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.scenario-info p {
  margin: 4px 0;
  color: #606266;
}

@media (max-width: 768px) {
  .daily-recommendations {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
  }

  .profile-content {
    flex-direction: column;
    gap: 16px;
  }

  .item-header {
    flex-direction: column;
    gap: 8px;
    align-items: flex-start;
  }

  .vocabulary-grid {
    grid-template-columns: 1fr;
  }

  .speaking-content {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
}
</style>
