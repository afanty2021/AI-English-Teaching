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
        <!-- 操作栏 -->
        <div class="action-bar">
          <div class="left-actions">
            <el-input
              v-model="searchText"
              placeholder="搜索学生姓名或学号"
              style="width: 250px"
              clearable
              @clear="loadStudents"
              @keyup.enter="loadStudents"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-select
              v-model="filterClassId"
              placeholder="筛选班级"
              clearable
              style="width: 180px"
              @change="loadStudents"
            >
              <el-option label="全部班级" value="" />
              <el-option
                v-for="cls in classes"
                :key="cls.id"
                :label="cls.name"
                :value="cls.id"
              />
            </el-select>
          </div>
          <div class="right-actions">
            <el-button
              type="primary"
              :disabled="selectedStudents.length === 0"
              @click="handleBatchDiagnose"
            >
              <el-icon><Monitor /></el-icon>
              批量诊断 ({{ selectedStudents.length }})
            </el-button>
            <el-button @click="loadStudents" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>

        <!-- 学生列表 -->
        <el-card shadow="never" v-loading="loading">
          <el-table
            :data="students"
            @selection-change="handleSelectionChange"
            style="width: 100%"
          >
            <el-table-column type="selection" width="55" />

            <el-table-column label="学生" min-width="200">
              <template #default="{ row }">
                <div class="student-cell">
                  <el-avatar :size="40" :style="{ backgroundColor: '#409EFF' }">
                    {{ row.username.charAt(0) }}
                  </el-avatar>
                  <div class="student-info">
                    <div class="name">{{ row.username }}</div>
                    <div class="email">{{ row.email }}</div>
                  </div>
                </div>
              </template>
            </el-table-column>

            <el-table-column prop="email" label="邮箱" min-width="180" />

            <el-table-column label="CEFR等级" width="120" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.current_cefr_level" type="success">
                  {{ row.current_cefr_level }}
                </el-tag>
                <el-tag v-else type="info">未评估</el-tag>
              </template>
            </el-table-column>

            <el-table-column label="目标考试" width="120">
              <template #default="{ row }">
                {{ row.target_exam || '-' }}
              </template>
            </el-table-column>

            <el-table-column label="目标分数" width="100" align="center">
              <template #default="{ row }">
                {{ row.target_score || '-' }}
              </template>
            </el-table-column>

            <el-table-column label="知识图谱" width="120" align="center">
              <template #default="{ row }">
                <el-button
                  link
                  type="primary"
                  :disabled="!hasKnowledgeGraph(row.id)"
                  @click="showKnowledgeGraph(row)"
                >
                  {{ hasKnowledgeGraph(row.id) ? '查看' : '未诊断' }}
                </el-button>
              </template>
            </el-table-column>

            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <el-button
                  link
                  type="primary"
                  @click="showKnowledgeGraph(row)"
                >
                  查看诊断
                </el-button>
                <el-button
                  link
                  type="success"
                  @click="diagnoseStudent(row)"
                  :loading="diagnosingStudentId === row.id"
                >
                  {{ hasKnowledgeGraph(row.id) ? '重新诊断' : '诊断' }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 分页 -->
          <div class="pagination">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :total="total"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              @current-change="loadStudents"
              @size-change="loadStudents"
            />
          </div>
        </el-card>
      </el-main>
    </el-container>

    <!-- 知识图谱抽屉 -->
    <el-drawer
      v-model="graphDrawerVisible"
      :title="`${currentStudent?.username} - 知识图谱`"
      size="60%"
      destroy-on-close
    >
      <div v-if="graphLoading" class="graph-loading">
        <el-skeleton :rows="8" animated />
      </div>

      <div v-else-if="currentGraph" class="graph-content">
        <!-- CEFR等级和基本信息 -->
        <el-card class="info-card" shadow="never">
          <div class="info-grid">
            <div class="info-item">
              <span class="label">CEFR等级：</span>
              <el-tag size="large" type="success">
                {{ currentGraph.cefr_level || '未评估' }}
              </el-tag>
            </div>
            <div class="info-item">
              <span class="label">图谱版本：</span>
              <span>v{{ currentGraph.version }}</span>
            </div>
            <div class="info-item">
              <span class="label">最后更新：</span>
              <span>{{ formatDate(currentGraph.updated_at) }}</span>
            </div>
            <div class="info-item">
              <span class="label">上次AI分析：</span>
              <span>{{ currentGraph.last_ai_analysis_at ? formatDate(currentGraph.last_ai_analysis_at) : '未执行' }}</span>
            </div>
          </div>
        </el-card>

        <!-- 能力雷达图 -->
        <el-card class="ability-card" shadow="never">
          <template #header>
            <h3><el-icon><TrendCharts /></el-icon> 能力分析</h3>
          </template>
          <div ref="radarChartRef" class="radar-chart" v-if="hasAbilityData"></div>
          <el-empty v-else description="暂无能力数据" />
        </el-card>

        <!-- 考试覆盖度 -->
        <el-card class="exam-card" shadow="never">
          <template #header>
            <h3><el-icon><DataAnalysis /></el-icon> 考试准备度</h3>
          </template>
          <div class="exam-stats">
            <div class="stat-item">
              <div class="stat-value">{{ currentGraph.exam_coverage.total_practices }}</div>
              <div class="stat-label">总练习数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ currentGraph.exam_coverage.topics_covered }}</div>
              <div class="stat-label">覆盖主题</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ currentGraph.exam_coverage.recent_activity }}</div>
              <div class="stat-label">近期活跃(7天)</div>
            </div>
          </div>
        </el-card>

        <!-- 薄弱点分析 -->
        <el-card v-if="weakPoints.length > 0" class="weak-points-card" shadow="never">
          <template #header>
            <h3><el-icon><Warning /></el-icon> 薄弱点分析</h3>
          </template>
          <div class="weak-points-list">
            <div
              v-for="(wp, index) in weakPoints"
              :key="index"
              class="weak-point-item"
            >
              <div class="wp-header">
                <span class="wp-topic">{{ wp.topic }}</span>
                <el-tag :type="getPriorityType(wp.priority)" size="small">
                  {{ getPriorityText(wp.priority) }}
                </el-tag>
              </div>
              <div class="wp-reason">{{ wp.reason }}</div>
              <div class="wp-level">当前水平：{{ wp.current_level.toFixed(1) }}</div>
            </div>
          </div>
        </el-card>

        <!-- 学习建议 -->
        <el-card v-if="recommendations.length > 0" class="recommendations-card" shadow="never">
          <template #header>
            <h3><el-icon><ReadingLamp /></el-icon> 学习建议</h3>
          </template>
          <div class="recommendations-list">
            <div
              v-for="(rec, index) in recommendations"
              :key="index"
              class="recommendation-item"
            >
              <el-tag :type="getPriorityType(rec.priority)" size="small">
                {{ getPriorityText(rec.priority) }}
              </el-tag>
              <div class="rec-content">
                <div class="rec-suggestion">{{ rec.suggestion }}</div>
                <div class="rec-ability" v-if="rec.ability">相关能力：{{ rec.ability }}</div>
              </div>
            </div>
          </div>
        </el-card>
      </div>

      <el-empty v-else description="暂无知识图谱数据，请先进行诊断" />
    </el-drawer>

    <!-- 批量诊断进度对话框 -->
    <el-dialog
      v-model="batchDiagnoseVisible"
      title="批量诊断进度"
      width="500px"
      :close-on-click-modal="false"
    >
      <div class="batch-progress">
        <el-progress
          :percentage="batchProgress"
          :status="batchStatus"
        >
          <span>{{ batchCompleted }}/{{ batchTotal }}</span>
        </el-progress>
        <div class="progress-info">
          <span>已完成：{{ batchCompleted }}</span>
          <span>失败：{{ batchFailed }}</span>
          <span>总计：{{ batchTotal }}</span>
        </div>
        <div v-if="batchCurrentStudent" class="current-student">
          正在诊断：{{ batchCurrentStudent }}
        </div>
      </div>
      <template #footer>
        <el-button @click="batchDiagnoseVisible = false" :disabled="batchDiagnosing">
          关闭
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Refresh,
  Monitor,
  TrendCharts,
  DataAnalysis,
  Warning,
  ReadingLamp
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import studentApi, { type StudentProfile, type KnowledgeGraph } from '@/api/student'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// 状态
const loading = ref(false)
const students = ref<StudentProfile[]>([])
const searchText = ref('')
const filterClassId = ref('')
const selectedStudents = ref<StudentProfile[]>([])

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 班级列表（模拟数据，实际应从API获取）
const classes = ref<Array<{ id: string; name: string }>>([
  { id: 'class-1', name: '高一(1)班' },
  { id: 'class-2', name: '高一(2)班' },
  { id: 'class-3', name: '高二(1)班' },
])

// 知识图谱相关
const graphDrawerVisible = ref(false)
const graphLoading = ref(false)
const currentStudent = ref<StudentProfile | null>(null)
const currentGraph = ref<KnowledgeGraph | null>(null)
const radarChartRef = ref<HTMLElement>()
const knowledgeGraphCache = ref<Map<string, KnowledgeGraph>>(new Map())

// 诊断相关
const diagnosingStudentId = ref<string | null>(null)

// 批量诊断相关
const batchDiagnoseVisible = ref(false)
const batchDiagnosing = ref(false)
const batchProgress = ref(0)
const batchCompleted = ref(0)
const batchFailed = ref(0)
const batchTotal = ref(0)
const batchCurrentStudent = ref('')
const batchStatus = ref<'success' | 'exception' | ''>('')

// 计算属性
const activeMenu = computed(() => route.path)

const hasAbilityData = computed(() => {
  const abilities = currentGraph.value?.abilities || {}
  return Object.keys(abilities).length > 0
})

const weakPoints = computed(() => {
  return currentGraph.value?.ai_analysis?.weak_points || []
})

const recommendations = computed(() => {
  return currentGraph.value?.ai_analysis?.recommendations || []
})

// 方法
async function loadStudents() {
  loading.value = true
  try {
    const skip = (currentPage.value - 1) * pageSize.value
    const data = await studentApi.getStudents({
      skip,
      limit: pageSize.value,
      classId: filterClassId.value || undefined
    })
    students.value = data
    // 注意：后端没有返回总数，这里假设就是返回的数量
    // 实际应该从API响应头或响应体中获取总数
    total.value = data.length >= pageSize.value ? -1 : data.length
  } catch (error: any) {
    ElMessage.error('加载学生列表失败')
    console.error('Load students error:', error)
  } finally {
    loading.value = false
  }
}

function handleSelectionChange(selection: StudentProfile[]) {
  selectedStudents.value = selection
}

function hasKnowledgeGraph(studentId: string): boolean {
  return knowledgeGraphCache.value.has(studentId)
}

async function showKnowledgeGraph(student: StudentProfile) {
  currentStudent.value = student
  graphDrawerVisible.value = true
  graphLoading.value = true

  try {
    // 先检查缓存
    if (knowledgeGraphCache.value.has(student.id)) {
      currentGraph.value = knowledgeGraphCache.value.get(student.id)!
      await nextTick()
      initRadarChart()
      return
    }

    // 从API获取
    const graph = await studentApi.getKnowledgeGraph(student.id)
    currentGraph.value = graph
    knowledgeGraphCache.value.set(student.id, graph)

    await nextTick()
    initRadarChart()
  } catch (error: any) {
    if (error.response?.status === 404) {
      ElMessage.warning('该学生暂无知识图谱，请先进行诊断')
      currentGraph.value = null
    } else {
      ElMessage.error('加载知识图谱失败')
    }
  } finally {
    graphLoading.value = false
  }
}

function initRadarChart() {
  if (!currentGraph.value?.abilities || !radarChartRef.value) return

  const chart = echarts.init(radarChartRef.value)
  const abilities = currentGraph.value.abilities

  const indicator = Object.entries(abilities).map(([name, value]) => ({
    name,
    max: 100
  }))

  const option = {
    radar: {
      indicator,
      radius: '60%'
    },
    series: [{
      type: 'radar',
      data: [{
        value: Object.values(abilities),
        name: '能力值',
        areaStyle: {
          color: 'rgba(64, 158, 255, 0.3)'
        }
      }]
    }]
  }

  chart.setOption(option)

  // 响应式
  const resizeHandler = () => chart.resize()
  window.addEventListener('resize', resizeHandler)

  // 清理
  const drawer = document.querySelector('.el-drawer')
  drawer?.addEventListener('DOMNodeRemoved', () => {
    window.removeEventListener('resize', resizeHandler)
    chart.dispose()
  })
}

async function diagnoseStudent(student: StudentProfile) {
  try {
    await ElMessageBox.confirm(
      `确定要为 ${student.username} 进行AI诊断吗？`,
      '确认诊断',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )

    diagnosingStudentId.value = student.id

    await studentApi.diagnoseStudent(student.id)

    ElMessage.success('诊断完成')

    // 清除缓存，重新加载
    knowledgeGraphCache.value.delete(student.id)

    // 自动显示知识图谱
    await showKnowledgeGraph(student)
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('诊断失败：' + (error.message || '未知错误'))
    }
  } finally {
    diagnosingStudentId.value = null
  }
}

async function handleBatchDiagnose() {
  if (selectedStudents.value.length === 0) {
    ElMessage.warning('请先选择要诊断的学生')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要为选中的 ${selectedStudents.value.length} 名学生进行批量诊断吗？`,
      '确认批量诊断',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    batchDiagnoseVisible.value = true
    batchDiagnosing.value = true
    batchTotal.value = selectedStudents.value.length
    batchCompleted.value = 0
    batchFailed.value = 0
    batchProgress.value = 0
    batchStatus.value = ''

    // 顺序执行诊断（避免服务器过载）
    for (const student of selectedStudents.value) {
      batchCurrentStudent.value = student.username
      try {
        await studentApi.diagnoseStudent(student.id)
        batchCompleted.value++
        // 清除缓存
        knowledgeGraphCache.value.delete(student.id)
      } catch (error: any) {
        batchFailed.value++
        console.error(`Diagnose ${student.username} failed:`, error)
      }
      batchProgress.value = Math.round((batchCompleted.value + batchFailed.value) / batchTotal.value * 100)
    }

    batchStatus.value = batchFailed.value === 0 ? 'success' : 'exception'
    batchDiagnosing.value = false
    batchCurrentStudent.value = ''

    if (batchFailed.value === 0) {
      ElMessage.success('批量诊断全部完成')
    } else {
      ElMessage.warning(`批量诊断完成，成功 ${batchCompleted.value}，失败 ${batchFailed.value}`)
    }

    // 刷新学生列表
    await loadStudents()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('批量诊断失败')
    }
    batchDiagnoseVisible.value = false
    batchDiagnosing.value = false
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

// 辅助方法
function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function getPriorityType(priority: string): 'danger' | 'warning' | 'info' {
  const types: Record<string, 'danger' | 'warning' | 'info'> = {
    high: 'danger',
    medium: 'warning',
    low: 'info'
  }
  return types[priority] || 'info'
}

function getPriorityText(priority: string): string {
  const texts: Record<string, string> = {
    high: '高优先级',
    medium: '中优先级',
    low: '低优先级'
  }
  return texts[priority] || priority
}

// 生命周期
onMounted(() => {
  loadStudents()
})
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

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 16px;
  background: white;
  border-radius: 8px;
}

.left-actions {
  display: flex;
  gap: 12px;
}

.right-actions {
  display: flex;
  gap: 12px;
}

.student-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.student-info {
  display: flex;
  flex-direction: column;
}

.student-info .name {
  font-weight: 600;
  color: #303133;
}

.student-info .email {
  font-size: 12px;
  color: #909399;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}

/* 知识图谱抽屉样式 */
.graph-loading {
  padding: 20px;
}

.graph-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-card .info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-item .label {
  font-weight: 600;
  color: #606266;
}

.ability-card h3,
.exam-card h3,
.weak-points-card h3,
.recommendations-card h3 {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

.radar-chart {
  width: 100%;
  height: 350px;
}

.exam-stats {
  display: flex;
  justify-content: space-around;
}

.stat-item {
  text-align: center;
}

.stat-item .stat-value {
  font-size: 32px;
  font-weight: 600;
  color: #409EFF;
}

.stat-item .stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}

.weak-points-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.weak-point-item {
  padding: 12px;
  border: 1px solid #EBEEF5;
  border-radius: 6px;
  background: #F5F7FA;
}

.wp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.wp-topic {
  font-weight: 600;
  color: #303133;
}

.wp-reason {
  font-size: 14px;
  color: #606266;
  margin-bottom: 4px;
}

.wp-level {
  font-size: 12px;
  color: #909399;
}

.recommendations-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.recommendation-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  border: 1px solid #EBEEF5;
  border-radius: 6px;
  background: #F5F7FA;
}

.rec-content {
  flex: 1;
}

.rec-suggestion {
  font-size: 14px;
  color: #303133;
  margin-bottom: 4px;
}

.rec-ability {
  font-size: 12px;
  color: #909399;
}

/* 批量诊断进度样式 */
.batch-progress {
  padding: 20px 0;
}

.progress-info {
  display: flex;
  justify-content: space-around;
  margin-top: 16px;
  font-size: 14px;
  color: #606266;
}

.current-student {
  margin-top: 12px;
  text-align: center;
  font-size: 14px;
  color: #409EFF;
}
</style>
