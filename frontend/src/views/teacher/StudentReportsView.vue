<template>
  <div class="student-reports-view">
    <div class="header">
      <h1>学生报告</h1>
      <el-button type="primary" @click="refreshData">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <!-- 筛选器 -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters" @submit.prevent="loadStudents">
        <el-form-item label="班级">
          <el-select
            v-model="filters.classId"
            placeholder="全部班级"
            clearable
            style="width: 200px"
            @change="handleClassChange"
          >
            <el-option
              v-for="cls in teacherClasses"
              :key="cls.id"
              :label="cls.name"
              :value="cls.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="loadStudents">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 学生列表 -->
    <el-card class="student-list" shadow="never" v-loading="loading">
      <template v-if="students.length === 0 && !loading">
        <el-empty description="暂无学生数据">
          <el-button type="primary" @click="refreshData">刷新数据</el-button>
        </el-empty>
      </template>

      <div v-else class="student-cards">
        <div
          v-for="student in students"
          :key="student.student_id"
          class="student-card"
          @click="viewStudentReports(student)"
        >
          <div class="card-header">
            <div class="student-info">
              <el-avatar :size="40" :style="{ backgroundColor: '#409EFF' }">
                {{ student.student_name.charAt(0) }}
              </el-avatar>
              <div class="student-details">
                <h3>{{ student.student_name }}</h3>
                <p class="student-meta">
                  {{ student.student_number }} | {{ student.class_name }}
                  <el-tag v-if="student.grade" size="small" style="margin-left: 8px">
                    {{ student.grade }}
                  </el-tag>
                </p>
              </div>
            </div>
            <el-tag :type="student.has_reports ? 'success' : 'info'">
              {{ student.has_reports ? '有报告' : '无报告' }}
            </el-tag>
          </div>

          <div class="card-body">
            <div v-if="student.latest_report" class="latest-report">
              <div class="report-info">
                <el-icon><Document /></el-icon>
                <span>{{ formatReportType(student.latest_report.report_type) }}</span>
              </div>
              <div class="report-time">
                <el-icon><Clock /></el-icon>
                <span>{{ formatTime(student.latest_report.created_at) }}</span>
              </div>
            </div>
            <div v-else class="no-report">
              <el-empty :image-size="30" description="暂无学习报告">
                <el-button
                  type="primary"
                  size="small"
                  @click.stop="generateReport(student.student_id)"
                  :loading="generatingStudentId === student.student_id"
                >
                  生成报告
                </el-button>
              </el-empty>
            </div>
          </div>
        </div>
      </div>

      <div v-if="total > 0" class="pagination">
        <el-pagination
          :current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          @current-change="handlePageChange"
          layout="prev, pager, next, jumper, ->, total"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document, Clock, Refresh } from '@element-plus/icons-vue'
import teacherReportApi, { type StudentReportSummary } from '@/api/teacherReport'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()

// 状态
const loading = ref(false)
const students = ref<StudentReportSummary[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const generatingStudentId = ref<string | null>(null)

// 筛选
const filters = reactive({
  classId: undefined as string | undefined
})

// 教师班级列表（模拟数据，实际应从API获取）
const teacherClasses = ref<Array<{ id: string; name: string }>>([
  { id: 'class-1', name: '高一(1)班' },
  { id: 'class-2', name: '高一(2)班' },
  { id: 'class-3', name: '高二(1)班' },
])

// 方法
const loadStudents = async () => {
  loading.value = true
  try {
    const response = await teacherReportApi.getStudents({
      classId: filters.classId,
      page: currentPage.value,
      limit: pageSize.value
    })
    students.value = response.students
    total.value = response.total
  } catch (error: any) {
    ElMessage.error('加载学生列表失败')
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.classId = undefined
  currentPage.value = 1
  loadStudents()
}

const handleClassChange = () => {
  currentPage.value = 1
  loadStudents()
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  loadStudents()
}

const refreshData = () => {
  loadStudents()
}

const viewStudentReports = (student: StudentReportSummary) => {
  // 跳转到学生报告列表页面
  router.push(`/teacher/reports/students/${student.student_id}`)
}

const generateReport = async (studentId: string) => {
  try {
    generatingStudentId.value = studentId
    await teacherReportApi.generateStudentReport(studentId, {
      report_type: 'custom'
    })
    ElMessage.success('报告生成成功')
    loadStudents()
  } catch (error: any) {
    ElMessage.error('生成报告失败')
  } finally {
    generatingStudentId.value = null
  }
}

// 辅助方法
const formatReportType = (type: string) => {
  const types: Record<string, string> = {
    weekly: '周报',
    monthly: '月报',
    custom: '自定义报告'
  }
  return types[type] || type
}

const formatTime = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN')
}

// 生命周期
onMounted(() => {
  loadStudents()
})
</script>

<style scoped>
.student-reports-view {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.filter-card {
  margin-bottom: 20px;
}

.student-list {
  min-height: 400px;
}

.student-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 16px;
}

.student-card {
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s;
}

.student-card:hover {
  border-color: var(--el-color-primary);
  box-shadow: var(--el-box-shadow-light);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.student-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.student-details h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.student-meta {
  margin: 4px 0 0 0;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.card-body {
  min-height: 80px;
}

.latest-report {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.report-info,
.report-time {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.no-report {
  text-align: center;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>
