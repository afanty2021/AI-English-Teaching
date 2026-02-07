<template>
  <div class="reports-view">
    <div class="header">
      <h1>学习报告</h1>
      <el-button type="primary" @click="showGenerateDialog = true">
        <el-icon><Document /></el-icon>
        生成新报告
      </el-button>
    </div>

    <!-- 筛选器 -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters" @submit.prevent="loadReports">
        <el-form-item label="报告类型">
          <el-select v-model="filters.report_type" placeholder="全部" clearable style="width: 150px">
            <el-option label="周报" value="weekly" />
            <el-option label="月报" value="monthly" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="loadReports">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 报告列表 -->
    <el-card class="report-list" shadow="never" v-loading="loading">
      <template v-if="reports.length === 0 && !loading">
        <el-empty description="暂无学习报告，点击上方按钮生成第一份报告">
          <el-button type="primary" @click="showGenerateDialog = true">立即生成</el-button>
        </el-empty>
      </template>

      <div v-else class="report-cards">
        <div
          v-for="report in reports"
          :key="report.id"
          class="report-card"
          @click="viewReport(report.id)"
        >
          <div class="card-header">
            <el-tag :type="getReportTypeColor(report.report_type)">
              {{ getReportTypeName(report.report_type) }}
            </el-tag>
            <span class="report-title">{{ report.title || formatDate(report.period_end) }}</span>
            <el-tag v-if="report.status === 'completed'" type="success" size="small">已完成</el-tag>
          </div>

          <div class="card-body">
            <div class="period">
              <el-icon><Calendar /></el-icon>
              {{ formatDateRange(report.period_start, report.period_end) }}
            </div>
            <div class="time">
              <el-icon><Clock /></el-icon>
              {{ formatTime(report.created_at) }}
            </div>
          </div>
        </div>
      </div>

      <div v-if="total > 0" class="pagination">
        <el-pagination
          :current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          @current-change="loadReports"
          layout="prev, pager, next"
        />
      </div>
    </el-card>

    <!-- 生成报告对话框 -->
    <el-dialog
      v-model="showGenerateDialog"
      title="生成学习报告"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="generateForm" :rules="generateRules" ref="generateFormRef" label-width="100px">
        <el-form-item label="报告类型" prop="report_type">
          <el-select v-model="generateForm.report_type" placeholder="请选择报告类型">
            <el-option label="周报" value="weekly" />
            <el-option label="月报" value="monthly" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>

        <el-form-item label="开始日期" prop="period_start">
          <el-date-picker
            v-model="generateForm.period_start"
            type="date"
            placeholder="选择开始日期"
            style="width: 100%"
            :disabled-date="disabledStartDate"
          />
        </el-form-item>

        <el-form-item label="结束日期" prop="period_end">
          <el-date-picker
            v-model="generateForm.period_end"
            type="date"
            placeholder="选择结束日期"
            style="width: 100%"
            :disabled-date="disabledEndDate"
          />
        </el-form-item>

        <el-alert
          v-if="generateForm.report_type === 'weekly'"
          title="提示"
          type="info"
          :closable="false"
          show-icon
        >
          周报将统计最近7天的学习数据
        </el-alert>

        <el-alert
          v-if="generateForm.report_type === 'monthly'"
          title="提示"
          type="info"
          :closable="false"
          show-icon
        >
          月报将统计最近30天的学习数据
        </el-alert>
      </el-form>

      <template #footer>
        <el-button @click="showGenerateDialog = false">取消</el-button>
        <el-button type="primary" @click="generateReport" :loading="generating">
          生成报告
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document, Calendar, Clock } from '@element-plus/icons-vue'
import reportApi, { type GenerateReportRequest } from '@/api/report'

const router = useRouter()

// 状态
const loading = ref(false)
const reports = ref<Array<{
  id: string
  report_type: string
  period_start: string
  period_end: string
  status: string
  title?: string
  created_at: string
}>>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const showGenerateDialog = ref(false)
const generating = ref(false)

// 筛选
const filters = reactive({
  report_type: undefined as string | undefined
})

// 生成表单
const generateForm = reactive<GenerateReportRequest>({
  report_type: 'custom',
  period_start: undefined,
  period_end: undefined
})

const generateFormRef = ref()

const generateRules = {
  report_type: [{ required: true, message: '请选择报告类型', trigger: 'change' }]
}

// 方法
const loadReports = async () => {
  loading.value = true
  try {
    const response = await reportApi.getMyReports({
      report_type: filters.report_type,
      limit: pageSize.value,
      offset: (currentPage.value - 1) * pageSize.value
    })
    reports.value = response.reports
    total.value = response.total
  } catch (error: any) {
    ElMessage.error('加载报告列表失败')
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.report_type = undefined
  currentPage.value = 1
  loadReports()
}

const generateReport = async () => {
  if (!generateFormRef.value) return

  const valid = await generateFormRef.value.validate()
  if (!valid) return

  generating.value = true
    try {
      // 转换日期格式
      const data: GenerateReportRequest = {
        report_type: generateForm.report_type!,
        period_start: generateForm.period_start
          ? new Date(generateForm.period_start).toISOString().split('T')[0]
          : undefined,
        period_end: generateForm.period_end
          ? new Date(generateForm.period_end).toISOString().split('T')[0]
          : undefined
      }

      await reportApi.generateReport(data)

      ElMessage.success('报告生成成功')
      showGenerateDialog.value = false

      // 重新加载列表
      currentPage.value = 1
      await loadReports()

      // 查看新报告详情
      if (reports.value.length > 0 && reports.value[0]) {
        viewReport(reports.value[0].id)
      }
    } catch (error: any) {
      ElMessage.error('生成报告失败')
    } finally {
      generating.value = false
    }
}

const viewReport = (reportId: string) => {
  // 跳转到报告详情页
  router.push(`/student/reports/${reportId}`)
}

// 辅助方法
const getReportTypeName = (type: string) => {
  const names: Record<string, string> = {
    weekly: '周报',
    monthly: '月报',
    custom: '自定义'
  }
  return names[type] || type
}

const getReportTypeColor = (type: string) => {
  const colors: Record<string, any> = {
    weekly: '',
    monthly: 'warning',
    custom: 'info'
  }
  return colors[type] || 'info'
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
}

const formatDateRange = (startStr: string, endStr: string) => {
  const start = new Date(startStr)
  const end = new Date(endStr)
  const startFormatted = start.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  const endFormatted = end.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  return `${startFormatted} - ${endFormatted}`
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

const disabledStartDate = (date: Date) => {
  if (generateForm.period_end) {
    return date > new Date(generateForm.period_end)
  }
  return false
}

const disabledEndDate = (date: Date) => {
  if (generateForm.period_start) {
    return date < new Date(generateForm.period_start)
  }
  return date > new Date()
}

// 生命周期
onMounted(() => {
  loadReports()
})
</script>

<style scoped>
.reports-view {
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

.report-list {
  min-height: 400px;
}

.report-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.report-card {
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s;
}

.report-card:hover {
  border-color: var(--el-color-primary);
  box-shadow: var(--el-box-shadow-light);
}

.card-header {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 12px;
}

.report-title {
  flex: 1;
  font-weight: 600;
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  color: var(--el-text-color-secondary);
}

.period, .time {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>
