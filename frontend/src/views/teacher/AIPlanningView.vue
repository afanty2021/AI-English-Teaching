<template>
  <div class="ai-planning-page">
    <el-container>
      <el-header>
        <div class="header-content">
          <h1>AI 备课</h1>
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
        <el-row :gutter="20">
          <el-col :span="8">
            <el-card>
              <template #header>
                <h3>创建新教案</h3>
              </template>

              <el-form :model="planForm" label-width="100px">
                <el-form-item label="教案标题" required>
                  <el-input
                    v-model="planForm.title"
                    placeholder="例如：日常对话教学、商务英语基础..."
                  />
                </el-form-item>

                <el-form-item label="主题" required>
                  <el-input
                    v-model="planForm.topic"
                    placeholder="例如：daily_conversation, business..."
                  />
                </el-form-item>

                <el-form-item label="难度级别">
                  <el-select v-model="planForm.level" placeholder="请选择">
                    <el-option label="A1 - 入门" value="A1" />
                    <el-option label="A2 - 基础" value="A2" />
                    <el-option label="B1 - 进阶" value="B1" />
                    <el-option label="B2 - 高级" value="B2" />
                    <el-option label="C1 - 精通" value="C1" />
                    <el-option label="C2 - 专家" value="C2" />
                  </el-select>
                </el-form-item>

                <el-form-item label="时长（分钟）">
                  <el-input-number
                    v-model="planForm.duration"
                    :min="15"
                    :max="180"
                    :step="15"
                  />
                </el-form-item>

                <el-form-item label="学生人数">
                  <el-input-number
                    v-model="planForm.studentCount"
                    :min="1"
                    :max="50"
                  />
                </el-form-item>

                <el-form-item label="教学重点">
                  <el-checkbox-group v-model="planForm.focus">
                    <el-checkbox label="speaking">口语</el-checkbox>
                    <el-checkbox label="listening">听力</el-checkbox>
                    <el-checkbox label="reading">阅读</el-checkbox>
                    <el-checkbox label="writing">写作</el-checkbox>
                    <el-checkbox label="grammar">语法</el-checkbox>
                    <el-checkbox label="vocabulary">词汇</el-checkbox>
                  </el-checkbox-group>
                </el-form-item>

                <el-form-item label="补充说明">
                  <el-input
                    v-model="planForm.notes"
                    type="textarea"
                    :rows="3"
                    placeholder="其他要求或特殊说明..."
                  />
                </el-form-item>

                <el-form-item>
                  <el-button
                    type="primary"
                    @click="generatePlan"
                    :loading="generating"
                    style="width: 100%"
                  >
                    <el-icon v-if="!generating"><MagicStick /></el-icon>
                    {{ generating ? '生成中...' : 'AI 生成教案' }}
                  </el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </el-col>

          <el-col :span="16">
            <el-card>
              <template #header>
                <div class="card-header">
                  <h3>生成的教案</h3>
                  <div v-if="generatedPlan">
                    <el-button @click="editPlan">编辑</el-button>
                    <el-button type="primary" @click="savePlan">保存</el-button>
                  </div>
                </div>
              </template>

              <el-empty v-if="!generatedPlan" description="请在左侧填写信息并生成教案" />

              <div v-else class="plan-content">
                <h2>{{ generatedPlan.title }}</h2>
                <el-descriptions :column="2" border class="mb-2">
                  <el-descriptions-item label="主题">{{ generatedPlan.topic }}</el-descriptions-item>
                  <el-descriptions-item label="级别">{{ generatedPlan.level }}</el-descriptions-item>
                  <el-descriptions-item label="时长">{{ generatedPlan.duration }} 分钟</el-descriptions-item>
                  <el-descriptions-item label="ID">{{ generatedPlan.id?.slice(0, 8) }}...</el-descriptions-item>
                </el-descriptions>

                <el-divider content-position="left">教学目标</el-divider>
                <div v-if="generatedPlan.objectives">
                  <div v-if="generatedPlan.objectives.language_knowledge" class="mb-2">
                    <strong>语言知识：</strong>
                    <ul class="inline-list">
                      <li v-for="(obj, i) in generatedPlan.objectives.language_knowledge" :key="i">{{ obj }}</li>
                    </ul>
                  </div>
                  <div v-if="generatedPlan.objectives.language_skills" class="mb-2">
                    <strong>语言技能：</strong>
                    <div v-for="item in languageSkillsList" :key="item.type" class="ml-3">
                      <span class="skill-tag">{{ item.type }}:</span>
                      <span v-for="(skill, i) in item.skills" :key="i">{{ skill }}{{ i < item.skills.length - 1 ? '、' : '' }}</span>
                    </div>
                  </div>
                </div>

                <el-divider content-position="left">核心词汇</el-divider>
                <div v-if="generatedPlan.vocabulary?.noun?.length" class="vocab-list">
                  <el-tag
                    v-for="(vocab, index) in generatedPlan.vocabulary.noun.slice(0, 8)"
                    :key="index"
                    class="mr-1 mb-1"
                    type="success"
                  >
                    {{ vocab.word }}: {{ vocab.meaning_cn }}
                  </el-tag>
                </div>
                <el-empty v-else description="暂无词汇数据" :image-size="60" />

                <el-divider content-position="left">语法点</el-divider>
                <div v-if="generatedPlan.grammarPoints?.length">
                  <el-card
                    v-for="(gp, index) in generatedPlan.grammarPoints"
                    :key="index"
                    class="mb-2 grammar-card"
                  >
                    <template #header>
                      <strong>{{ gp.name }}</strong>
                    </template>
                    <p>{{ gp.description }}</p>
                    <p v-if="gp.rule" class="rule-text"><strong>规则：</strong>{{ gp.rule }}</p>
                  </el-card>
                </div>
                <el-empty v-else description="暂无语法点数据" :image-size="60" />

                <el-divider content-position="left">教学流程</el-divider>
                <div v-if="generatedPlan.structure">
                  <el-timeline>
                    <el-timeline-item
                      v-for="item in structureItems"
                      :key="item.key"
                      :timestamp="`${item.duration}分钟`"
                      placement="top"
                    >
                      <h4>{{ item.title }}</h4>
                      <p v-if="item.description">{{ item.description }}</p>
                    </el-timeline-item>
                  </el-timeline>
                </div>
                <el-empty v-else description="暂无教学流程数据" :image-size="60" />
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { MagicStick } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)
const generating = ref(false)
const generatedPlan = ref<any>(null)

const planForm = reactive({
  title: '',
  topic: '',
  level: 'B1',
  duration: 45,
  studentCount: 10,
  focus: ['speaking'],
  notes: ''
})

// 计算属性：处理语言技能数据
const languageSkillsList = computed(() => {
  if (!generatedPlan.value?.objectives?.language_skills) return []
  const result: Array<{ type: string; skills: string[] }> = []
  for (const [type, skills] of Object.entries(generatedPlan.value.objectives.language_skills)) {
    if (Array.isArray(skills)) {
      result.push({ type, skills })
    }
  }
  return result
})

// 计算属性：处理教学流程数据
const structureItems = computed(() => {
  if (!generatedPlan.value?.structure) return []
  const result: Array<{ key: string; duration: number; title: string; description?: string }> = []
  for (const [key, value] of Object.entries(generatedPlan.value.structure)) {
    if (typeof value === 'object' && value !== null && 'title' in value) {
      result.push({
        key,
        duration: (value as any).duration || 0,
        title: (value as any).title || '',
        description: (value as any).description
      })
    }
  }
  return result
})

async function generatePlan() {
  if (!planForm.topic) {
    ElMessage.warning('请输入教案主题')
    return
  }

  generating.value = true

  try {
    const token = localStorage.getItem('access_token')
    const response = await axios.post(
      'http://localhost:8000/api/v1/lesson-plans/',
      {
        title: planForm.title || `${planForm.topic} - ${planForm.level}课程`,
        topic: planForm.topic,
        level: planForm.level,
        duration: planForm.duration,
        student_count: planForm.studentCount,
        focus_areas: planForm.focus,
        learning_objectives: planForm.notes ? [planForm.notes] : []
      },
      {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 300000 // 5分钟超时
      }
    )

    const data = response.data.lesson_plan
    generatedPlan.value = {
      id: data.id,
      title: data.title,
      topic: data.topic,
      level: data.level,
      duration: data.duration,
      objectives: data.objectives,
      vocabulary: data.vocabulary,
      grammarPoints: data.grammar_points,
      structure: data.structure,
      materials: []
    }

    ElMessage.success('教案生成成功')
  } catch (error: any) {
    console.error('生成失败:', error)
    ElMessage.error(error.response?.data?.detail || '生成失败，请重试')
  } finally {
    generating.value = false
  }
}

function editPlan() {
  if (generatedPlan.value?.id) {
    router.push(`/teacher/lessons/${generatedPlan.value.id}`)
  } else {
    ElMessage.info('请先生成教案')
  }
}

async function savePlan() {
  if (!generatedPlan.value?.id) {
    ElMessage.warning('请先生成教案')
    return
  }

  try {
    await ElMessageBox.confirm('教案已保存到系统中，是否前往教案管理页面？', '提示', {
      confirmButtonText: '前往',
      cancelButtonText: '留在此页',
      type: 'info'
    })

    router.push('/teacher/lessons')
  } catch {
    // 用户选择留在此页
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
</script>

<style scoped>
.ai-planning-page {
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

.plan-content h2 {
  color: #333;
  margin-bottom: 16px;
}

.plan-content p {
  color: #666;
  line-height: 1.6;
}

.mr-1 {
  margin-right: 8px;
  margin-bottom: 8px;
}

.mb-1 {
  margin-bottom: 8px;
}

.mb-2 {
  margin-bottom: 16px;
}

.ml-3 {
  margin-left: 12px;
}

.inline-list {
  list-style: none;
  padding: 0;
  display: inline;
}

.inline-list li {
  display: inline-block;
  margin-right: 8px;
}

.skill-tag {
  font-weight: bold;
  color: #409eff;
  margin-right: 4px;
}

.vocab-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.grammar-card {
  margin-bottom: 12px;
}

.grammar-card p {
  margin: 8px 0;
}

.rule-text {
  color: #606266;
  font-size: 14px;
}
</style>
