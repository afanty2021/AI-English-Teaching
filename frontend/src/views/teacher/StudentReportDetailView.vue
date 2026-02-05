<template>
  <div class="student-report-detail-view">
    <!-- 页面头部 -->
    <div class="header">
      <div class="breadcrumb">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ path: '/teacher/reports' }">
            学生报告
          </el-breadcrumb-item>
          <el-breadcrumb-item>{{ studentInfo?.student_name || '学生报告详情' }}</el-breadcrumb-item>
        </el-breadcrumb>
      </div>
      <div class="actions">
        <el-button @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <el-button @click="exportReport" :loading="exporting">
          <el-icon><Download /></el-icon>
          导出报告
        </el-button>
      </div>
    </div>

    <!-- 学生信息 -->
    <el-card class="student-info-card" shadow="never" v-if="studentInfo">
      <div class="student-profile">
        <el-avatar :size="60" :style="{ backgroundColor: '#409EFF' }">
          {{ studentInfo.student_name.charAt(0) }}
        </el-avatar>
        <div class="student-details">
          <h2>{{ studentInfo.student_name }}</h2>
          <div class="info-grid">
            <span class="info-item">
              <el-icon><User /></el-icon>
              学号：{{ studentInfo.student_number }}
            </span>
            <span class="info-item">
              <el-icon><OfficeBuilding /></el-icon>
              班级：{{ studentInfo.class_name }}
            </span>
            <span class="info-item" v-if="studentInfo.grade">
              <el-icon><Calendar /></el-icon>
              年级：{{ studentInfo.grade }}
            </span>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 报告内容 -->
    <div v-if="report" class="report-content">
      <!-- 报告基本信息 -->
      <el-card class="report-header" shadow="never">
        <template #header>
          <div class="card-header">
            <div class="header-left">
              <h3>{{ report.title || `${formatReportType(report.report_type)}报告` }}</h3>
              <el-tag :type="getStatusColor(report.status)">
                {{ getStatusText(report.status) }}
              </el-tag>
            </div>
            <div class="header-right">
              <span class="period">
                <el-icon><Calendar /></el-icon>
                {{ formatDateRange(report.period_start, report.period_end) }}
              </span>
            </div>
          </div>
        </template>
        <p v-if="report.description" class="report-description">{{ report.description }}</p>
      </el-card>

      <!-- 学习统计 -->
      <el-card v-if="report.statistics" class="statistics-card" shadow="never">
        <template #header>
          <h3><el-icon><TrendCharts /></el-icon> 学习统计</h3>
        </template>
        <div class="statistics-grid">
          <div class="stat-item">
            <div class="stat-value">{{ report.statistics.total_practices }}</div>
            <div class="stat-label">总练习数</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ report.statistics.completed_practices }}</div>
            <div class="stat-label">已完成</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ (report.statistics.completion_rate * 100).toFixed(1) }}%</div>
            <div class="stat-label">完成率</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ (report.statistics.avg_correct_rate * 100).toFixed(1) }}%</div>
            <div class="stat-label">平均正确率</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ report.statistics.total_duration_hours.toFixed(1) }}h</div>
            <div class="stat-label">总学习时长</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ report.statistics.total_mistakes }}</div>
            <div class="stat-label">错题总数</div>
          </div>
        </div>
      </el-card>

      <!-- 能力雷达图 -->
      <el-card v-if="report.ability_analysis?.ability_radar?.length" class="ability-card" shadow="never">
        <template #header>
          <h3><el-icon><PieChart /></el-icon> 能力分析</h3>
        </template>
        <div class="ability-content">
          <div ref="radarChartRef" class="radar-chart"></div>
          <div class="ability-summary">
            <div v-if="report.ability_analysis.strongest_area" class="ability-item strong">
              <strong>最强项：</strong>
              {{ report.ability_analysis.strongest_area.name }}
              ({{ report.ability_analysis.strongest_area.level }}分)
            </div>
            <div v-if="report.ability_analysis.weakest_area" class="ability-item weak">
              <strong>待提升：</strong>
              {{ report.ability_analysis.weakest_area.name }}
              ({{ report.ability_analysis.weakest_area.level }}分)
            </div>
          </div>
        </div>
      </el-card>

      <!-- 薄弱点分析 -->
      <el-card v-if="report.weak_points" class="weak-points-card" shadow="never">
        <template #header>
          <h3><el-icon><Warning /></el-icon> 薄弱点分析</h3>
        </template>
        <div class="weak-points-content">
          <el-alert
            :title="`共有 ${report.weak_points.total_unmastered} 个未掌握知识点`"
            type="warning"
            :closable="false"
            show-icon
            style="margin-bottom: 16px"
          />

          <div class="weak-points-grid">
            <div class="weak-points-list">
              <h4>高频薄弱点</h4>
              <div class="weak-point-item" v-for="wp in report.weak_points.top_weak_points" :key="wp.point">
                <span>{{ wp.point }}</span>
                <el-tag size="small">{{ wp.count }}次</el-tag>
              </div>
            </div>

            <div class="topic-distribution">
              <h4>按主题分布</h4>
              <div class="topic-item" v-for="(count, topic) in report.weak_points.by_topic" :key="topic">
                <span>{{ topic }}</span>
                <el-progress
                  :percentage="(count / report.weak_points.total_unmastered) * 100"
                  :show-text="false"
                  :stroke-width="8"
                />
                <span>{{ count }}</span>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 学习建议 -->
      <el-card v-if="report.recommendations" class="recommendations-card" shadow="never">
        <template #header>
          <h3><el-icon><Lightbulb /></el-icon> 学习建议</h3>
        </template>
        <div class="recommendations-content">
          <div v-if="report.recommendations.rule_based?.length" class="recommendation-section">
            <h4>系统建议</h4>
            <div class="recommendation-list">
              <div
                v-for="rec in report.recommendations.rule_based"
                :key="rec.title"
                class="recommendation-item"
              >
                <el-tag :type="getPriorityColor(rec.priority)" size="small">
                  {{ getPriorityText(rec.priority) }}
                </el-tag>
                <div class="rec-content">
                  <strong>{{ rec.title }}</strong>
                  <p>{{ rec.description }}</p>
                </div>
              </div>
            </div>
          </div>

          <div v-if="report.recommendations.ai_generated?.length" class="recommendation-section">
            <h4>AI个性化建议</h4>
            <div class="recommendation-list">
              <div
                v-for="rec in report.recommendations.ai_generated"
                :key="rec.title"
                class="recommendation-item ai"
              >
                <el-tag type="success" size="small">
                  AI ({{ (rec.confidence * 100).toFixed(0) }}%)
                </el-tag>
                <div class="rec-content">
                  <strong>{{ rec.title }}</strong>
                  <p>{{ rec.description }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- AI洞察 -->
      <el-card v-if="report.ai_insights" class="ai-insights-card" shadow="never">
        <template #header>
          <h3><el-icon><Robot /></el-icon> AI洞察</h3>
        </template>
        <div class="ai-insights-content">
          <pre class="insights-text">{{ JSON.stringify(report.ai_insights, null, 2) }}</pre>
        </div>
      </el-card>
    </div>

    <!-- 加载状态 -->
    <div v-else-if="loading" class="loading">
      <el-skeleton :rows="10" animated />
    </div>

    <!-- 空状态 -->
    <el-empty v-else description="报告不存在或已被删除" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft,
  Download,
  User,
  OfficeBuilding,
  Calendar,
  TrendCharts,
  PieChart,
  Warning
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import teacherReportApi, { type LearningReport, type StudentReportSummary } from '@/api/teacherReport'

const route = useRoute()
const router = useRouter()

// 状态
const loading = ref(false)
const exporting = ref(false)
const report = ref<LearningReport | null>(null)
const studentInfo = ref<StudentReportSummary | null>(null)
const radarChartRef = ref<HTMLElement>()

// 获取路由参数
const studentId = route.params.studentId as string
const reportId = route.params.reportId as string

// 方法
const loadReport = async () => {
  loading.value = true
  try {
    // 这里需要先获取学生信息，然后再获取报告详情
    // 实际应用中可能需要调用不同的API
    const data = await teacherReportApi.getStudentReport(studentId, reportId)
    report.value = data

    // 模拟学生信息（实际应从API获取）
    studentInfo.value = {
      student_id: data.student_id,
      student_number: 'S2024001',
      student_name: '张三',
      email: 'zhangsan@example.com',
      class_id: 'class-1',
      class_name: '高一(1)班',
      grade: '高一',
      has_reports: true
    }
  } catch (error: any) {
    ElMessage.error('加载报告详情失败')
  } finally {
    loading.value = false
  }
}

const initRadarChart = () => {
  if (!report.value?.ability_analysis?.ability_radar || !radarChartRef.value) return

  const chart = echarts.init(radarChartRef.value)

  const option = {
    title: {
      text: '能力雷达图'
    },
    radar: {
      indicator: report.value.ability_analysis.ability_radar.map(item => ({
        name: item.name,
        max: 100
      }))
    },
    series: [{
      type: 'radar',
      data: [{
        value: report.value.ability_analysis.ability_radar.map(item => item.value),
        name: '能力值'
      }]
    }]
  }

  chart.setOption(option)

  // 响应式
  window.addEventListener('resize', () => {
    chart.resize()
  })
}

const goBack = () => {
  router.push('/teacher/reports')
}

const exportReport = async () => {
  if (!report.value) return

  exporting.value = true
  try {
    const blob = await teacherReportApi.exportStudentReport(studentId, reportId, 'pdf')

    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${studentInfo.value?.student_name}_学习报告_${formatDate(report.value.period_end)}.pdf`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('报告导出成功')
  } catch (error: any) {
    ElMessage.error('导出报告失败')
  } finally {
    exporting.value = false
  }
}

// 辅助方法
const formatReportType = (type: string) => {
  const types: Record<string, string> = {
    weekly: '周',
    monthly: '月',
    custom: '自定义'
  }
  return types[type] || type
}

const getStatusColor = (status: string) => {
  const colors: Record<string, any> = {
    draft: 'info',
    completed: 'success',
    archived: 'warning'
  }
  return colors[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    draft: '草稿',
    completed: '已完成',
    archived: '已归档'
  }
  return texts[status] || status
}

const getPriorityColor = (priority: string) => {
  const colors: Record<string, any> = {
    high: 'danger',
    medium: 'warning',
    low: 'info'
  }
  return colors[priority] || 'info'
}

const getPriorityText = (priority: string) => {
  const texts: Record<string, string> = {
    high: '高优先级',
    medium: '中优先级',
    low: '低优先级'
  }
  return texts[priority] || priority
}

const formatDateRange = (startStr: string, endStr: string) => {
  const start = new Date(startStr)
  const end = new Date(endStr)
  const startFormatted = start.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  const endFormatted = end.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  return `${startFormatted} - ${endFormatted}`
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

// 生命周期
onMounted(async () => {
  await loadReport()
  await nextTick()
  initRadarChart()
})
</script>

<style scoped>
.student-report-detail-view {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.breadcrumb {
  flex: 1;
}

.actions {
  display: flex;
  gap: 12px;
}

.student-info-card {
  margin-bottom: 20px;
}

.student-profile {
  display: flex;
  align-items: center;
  gap: 16px;
}

.student-details h2 {
  margin: 0 0 12px 0;
  font-size: 20px;
  font-weight: 600;
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--el-text-color-secondary);
}

.report-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.header-right {
  color: var(--el-text-color-secondary);
}

.report-description {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-style: italic;
}

.statistics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 20px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: var(--el-color-primary);
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.ability-content {
  display: flex;
  gap: 20px;
}

.radar-chart {
  flex: 1;
  height: 300px;
}

.ability-summary {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ability-item {
  padding: 12px;
  border-radius: 6px;
  background-color: var(--el-bg-color-page);
}

.ability-item.strong {
  background-color: #f0f9ff;
  border-left: 4px solid var(--el-color-success);
}

.ability-item.weak {
  background-color: #fef0f0;
  border-left: 4px solid var(--el-color-warning);
}

.weak-points-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.weak-points-list h4,
.topic-distribution h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
}

.weak-point-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--el-border-color-light);
}

.topic-item {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 12px;
  align-items: center;
  padding: 8px 0;
}

.recommendations-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.recommendation-section h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
}

.recommendation-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.recommendation-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  background-color: var(--el-bg-color-page);
}

.rec-content {
  flex: 1;
}

.rec-content strong {
  display: block;
  margin-bottom: 4px;
}

.rec-content p {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.ai-insights-content {
  background-color: var(--el-bg-color-page);
  padding: 16px;
  border-radius: 6px;
}

.insights-text {
  margin: 0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.5;
  color: var(--el-text-color-primary);
  white-space: pre-wrap;
  word-wrap: break-word;
}

.loading {
  padding: 20px;
}

@media (max-width: 768px) {
  .ability-content {
    flex-direction: column;
  }

  .weak-points-grid {
    grid-template-columns: 1fr;
  }
}
</style>
