<template>
  <div class="report-detail-view">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="5" animated />
    </div>

    <!-- 报告内容 -->
    <div v-else-if="report" class="report-content">
      <!-- 头部 -->
      <div class="report-header">
        <div class="header-left">
          <el-button link @click="goBack">
            <el-icon><ArrowLeft /></el-icon>
            返回列表
          </el-button>
          <h1 class="report-title">{{ report.title || '学习报告' }}</h1>
          <div class="report-meta">
            <el-tag :type="getReportTypeColor(report.report_type)">
              {{ getReportTypeName(report.report_type) }}
            </el-tag>
            <span class="period">
              <el-icon><Calendar /></el-icon>
              {{ formatDateRange(report.period_start, report.period_end) }}
            </span>
          </div>
        </div>
        <div class="header-actions">
          <el-button @click="exportReport('pdf')" :loading="exporting">
            <el-icon><Download /></el-icon>
            导出 PDF
          </el-button>
          <el-button @click="exportReport('image')" :loading="exporting">
            <el-icon><Picture /></el-icon>
            导出图片
          </el-button>
          <el-button type="danger" plain @click="confirmDelete">
            <el-icon><Delete /></el-icon>
            删除
          </el-button>
        </div>
      </div>

      <!-- 学习统计卡片 -->
      <el-card class="stats-section" shadow="never">
        <template #header>
          <h3>学习概况</h3>
        </template>
        <el-row :gutter="20" v-if="report.statistics">
          <el-col :span="6">
            <div class="stat-card">
              <div class="stat-icon" style="background: #ecf5ff">
                <el-icon color="#409eff"><Document /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ report.statistics.total_practices }}</div>
                <div class="stat-label">练习次数</div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-card">
              <div class="stat-icon" style="background: #f0f9ff">
                <el-icon color="#67c23a"><CircleCheck /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ report.statistics.completion_rate }}%</div>
                <div class="stat-label">完成率</div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-card">
              <div class="stat-icon" style="background: #fef0f0">
                <el-icon color="#f56c6c"><TrendCharts /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ report.statistics.avg_correct_rate }}%</div>
                <div class="stat-label">平均正确率</div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-card">
              <div class="stat-icon" style="background: #fdf6ec">
                <el-icon color="#e6a23c"><Clock /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ report.statistics.total_duration_hours?.toFixed(1) || 0 }}</div>
                <div class="stat-label">学习小时</div>
              </div>
            </div>
          </el-col>
        </el-row>

        <!-- 错题状态分布 -->
        <el-divider />
        <div v-if="report.statistics?.mistake_by_status" class="mistake-status">
          <h4>错题状态分布</h4>
          <div class="status-tags">
            <el-tag
              v-for="(count, status) in report.statistics.mistake_by_status"
              :key="status"
              :type="getStatusType(status)"
              size="large"
            >
              {{ getStatusName(status) }}: {{ count }} 道
            </el-tag>
          </div>
        </div>
      </el-card>

      <!-- 能力分析 -->
      <el-card class="ability-section" shadow="never" v-if="report.ability_analysis">
        <template #header>
          <h3>能力分析</h3>
        </template>

        <el-row :gutter="20">
          <!-- 能力雷达图 -->
          <el-col :span="12">
            <div class="radar-container">
              <div ref="radarChartRef" class="radar-chart"></div>
              <div v-if="!radarChartLoaded" class="chart-placeholder">
                <el-icon size="48"><Loading /></el-icon>
                <p>图表加载中...</p>
              </div>
            </div>
          </el-col>

          <!-- 能力评估 -->
          <el-col :span="12">
            <div class="ability-assessment">
              <div v-if="report.ability_analysis.strongest_area" class="assessment-item best">
                <div class="assessment-icon">
                  <el-icon color="#67c23a" :size="32"><Trophy /></el-icon>
                </div>
                <div class="assessment-content">
                  <div class="assessment-label">最强项</div>
                  <div class="assessment-value">
                    {{ report.ability_analysis.strongest_area.name }}
                    <span class="level">(水平: {{ report.ability_analysis.strongest_area.level?.toFixed(0) }})</span>
                  </div>
                </div>
              </div>

              <div v-if="report.ability_analysis.weakest_area" class="assessment-item weak">
                <div class="assessment-icon">
                  <el-icon color="#f56c6c" :size="32"><Warning /></el-icon>
                </div>
                <div class="assessment-content">
                  <div class="assessment-label">待提升</div>
                  <div class="assessment-value">
                    {{ report.ability_analysis.weakest_area.name }}
                    <span class="level">(水平: {{ report.ability_analysis.weakest_area.level?.toFixed(0) }})</span>
                  </div>
                </div>
              </div>

              <!-- 能力列表 -->
              <div class="ability-list">
                <h4>各项能力详情</h4>
                <div
                  v-for="item in report.ability_analysis.ability_radar"
                  :key="item.name"
                  class="ability-item"
                >
                  <div class="ability-name">{{ item.name }}</div>
                  <el-progress
                    :percentage="item.value"
                    :color="getAbilityColor(item.value)"
                    :show-text="true"
                  />
                </div>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 薄弱环节分析 -->
      <el-card class="weak-points-section" shadow="never" v-if="report.weak_points">
        <template #header>
          <h3>薄弱环节分析</h3>
        </template>

        <!-- 需要重点关注的知识点 -->
        <div v-if="report.weak_points.top_weak_points?.length" class="top-weak-points">
          <h4>需要重点关注的知识点</h4>
          <el-table :data="report.weak_points.top_weak_points.slice(0, 10)" stripe>
            <el-table-column type="index" label="排名" width="80" />
            <el-table-column prop="point" label="知识点" />
            <el-table-column prop="count" label="出错次数" width="120" align="center">
              <template #default="{ row }">
                <el-tag type="danger">{{ row.count }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 按主题分类 -->
        <el-divider />
        <div v-if="report.weak_points.by_topic" class="by-topic">
          <h4>按主题分类</h4>
          <div class="topic-list">
            <div
              v-for="(count, topic) in Object.entries(report.weak_points.by_topic).sort((a, b) => b[1] - a[1])"
              :key="topic"
              class="topic-item"
            >
              <span class="topic-name">{{ topic }}</span>
              <el-tag size="small">{{ count }} 个错题</el-tag>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 学习建议 -->
      <el-card class="recommendations-section" shadow="never" v-if="report.recommendations">
        <template #header>
          <div class="section-header">
            <h3>学习建议</h3>
            <el-tag type="info">共 {{ report.recommendations.total_count }} 条</el-tag>
          </div>
        </template>

        <div class="recommendations-list">
          <div
            v-for="(rec, index) in report.recommendations.recommendations"
            :key="index"
            class="recommendation-item"
            :class="`priority-${rec.priority}`"
          >
            <div class="recommendation-header">
              <el-tag :type="getPriorityType(rec.priority)" size="small">
                {{ getPriorityName(rec.priority) }}
              </el-tag>
              <el-tag type="info" size="small">{{ rec.category }}</el-tag>
            </div>
            <h4 class="recommendation-title">{{ rec.title }}</h4>
            <p class="recommendation-description">{{ rec.description }}</p>
          </div>
        </div>

        <!-- 优先级统计 -->
        <el-divider />
        <div class="priority-stats">
          <span>建议分布：</span>
          <el-tag type="danger">高优先级: {{ report.recommendations.priority_count.high }}</el-tag>
          <el-tag type="warning">中优先级: {{ report.recommendations.priority_count.medium }}</el-tag>
          <el-tag type="success">低优先级: {{ report.recommendations.priority_count.low }}</el-tag>
        </div>
      </el-card>

      <!-- AI 学习洞察 -->
      <el-card class="ai-insights-section" shadow="never" v-if="report.ai_insights">
        <template #header>
          <div class="section-header">
            <h3>
              <el-icon><MagicStick /></el-icon>
              AI 学习洞察
            </h3>
          </div>
        </template>
        <div class="ai-insights-content">
          {{ report.ai_insights }}
        </div>
      </el-card>
    </div>

    <!-- 错误状态 -->
    <el-empty v-else description="报告不存在或已被删除" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'
import {
  ArrowLeft,
  Calendar,
  Download,
  Picture,
  Delete,
  Document,
  CircleCheck,
  TrendCharts,
  Clock,
  Trophy,
  Warning,
  MagicStick,
  Loading
} from '@element-plus/icons-vue'
import reportApi, { type LearningReport } from '@/api/report'

const route = useRoute()
const router = useRouter()

// 状态
const loading = ref(true)
const exporting = ref(false)
const report = ref<LearningReport | null>(null)
const radarChartLoaded = ref(false)
const radarChartRef = ref<HTMLElement>()
let radarChart: echarts.ECharts | null = null

// 方法
const loadReport = async () => {
  const reportId = route.params.id as string
  if (!reportId) {
    ElMessage.error('报告 ID 不存在')
    goBack()
    return
  }

  loading.value = true
  try {
    const data = await reportApi.getReportDetail(reportId)
    report.value = data

    // 渲染图表
    await nextTick()
    if (data.ability_analysis?.ability_radar) {
      renderRadarChart(data.ability_analysis.ability_radar)
    }
  } catch (error: any) {
    ElMessage.error('加载报告失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const renderRadarChart = (radarData: Array<{ name: string; value: number; confidence: number }>) => {
  if (!radarChartRef.value) return

  try {
    radarChart = echarts.init(radarChartRef.value)

    const option: EChartsOption = {
      tooltip: {
        trigger: 'item'
      },
      radar: {
        indicator: radarData.map(item => ({
          name: item.name,
          max: 100
        })),
        radius: '65%',
        axisName: {
          color: '#666'
        },
        splitArea: {
          areaStyle: {
            color: ['#f5f7fa', '#ffffff']
          }
        }
      },
      series: [
        {
          type: 'radar',
          data: [
            {
              value: radarData.map(item => item.value),
              name: '能力水平',
              areaStyle: {
                color: 'rgba(64, 158, 255, 0.3)'
              },
              lineStyle: {
                color: '#409eff',
                width: 2
              },
              itemStyle: {
                color: '#409eff'
              }
            }
          ]
        }
      ]
    }

    radarChart.setOption(option)
    radarChartLoaded.value = true

    // 响应式调整
    window.addEventListener('resize', handleResize)
  } catch (error) {
    console.error('雷达图渲染失败:', error)
    radarChartLoaded.value = false
  }
}

const handleResize = () => {
  if (radarChart) {
    radarChart.resize()
  }
}

const exportReport = async (format: 'pdf' | 'image') => {
  if (!report.value) return

  exporting.value = true
  try {
    const blob = await reportApi.exportReport(report.value.id, format)

    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url

    const title = report.value.title || '学习报告'
    const date = new Date(report.value.period_end).toISOString().split('T')[0]
    link.download = `${title}_${date}.${format === 'pdf' ? 'pdf' : 'png'}`

    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success(`导出${format === 'pdf' ? 'PDF' : '图片'}成功`)
  } catch (error: any) {
    ElMessage.error('导出失败')
    console.error(error)
  } finally {
    exporting.value = false
  }
}

const confirmDelete = async () => {
  if (!report.value) return

  try {
    await ElMessageBox.confirm(
      '删除后无法恢复，确定要删除这份报告吗？',
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await reportApi.deleteReport(report.value.id)
    ElMessage.success('删除成功')
    goBack()
  } catch {
    // 用户取消
  }
}

const goBack = () => {
  router.push('/student/reports')
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

const formatDateRange = (startStr: string, endStr: string) => {
  const start = new Date(startStr)
  const end = new Date(endStr)
  const startFormatted = start.toLocaleDateString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' })
  const endFormatted = end.toLocaleDateString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' })
  return `${startFormatted} - ${endFormatted}`
}

const getStatusName = (status: string) => {
  const names: Record<string, string> = {
    pending: '待复习',
    reviewing: '复习中',
    mastered: '已掌握',
    ignored: '已忽略'
  }
  return names[status] || status
}

const getStatusType = (status: string) => {
  const types: Record<string, any> = {
    pending: 'warning',
    reviewing: 'primary',
    mastered: 'success',
    ignored: 'info'
  }
  return types[status] || 'info'
}

const getAbilityColor = (value: number) => {
  if (value >= 80) return '#67c23a'
  if (value >= 60) return '#e6a23c'
  return '#f56c6c'
}

const getPriorityType = (priority: string) => {
  const types: Record<string, any> = {
    high: 'danger',
    medium: 'warning',
    low: 'success'
  }
  return types[priority] || 'info'
}

const getPriorityName = (priority: string) => {
  const names: Record<string, string> = {
    high: '高优先级',
    medium: '中优先级',
    low: '低优先级'
  }
  return names[priority] || priority
}

// 生命周期
onMounted(() => {
  loadReport()
})

onUnmounted(() => {
  if (radarChart) {
    radarChart.dispose()
    radarChart = null
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.report-detail-view {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.loading-container {
  padding: 40px;
}

.report-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 头部 */
.report-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.header-left {
  flex: 1;
}

.report-title {
  margin: 12px 0;
  font-size: 28px;
  font-weight: 600;
}

.report-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  color: #666;
}

.period {
  display: flex;
  align-items: center;
  gap: 6px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

/* 统计卡片 */
.stats-section {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 4px;
}

.mistake-status {
  margin-top: 16px;
}

.mistake-status h4 {
  margin: 0 0 12px;
  font-size: 16px;
}

.status-tags {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

/* 能力分析 */
.ability-section {
  margin-bottom: 20px;
}

.radar-container {
  position: relative;
  height: 360px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.radar-chart {
  width: 100%;
  height: 100%;
}

.chart-placeholder {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #999;
}

.ability-assessment {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.assessment-item {
  display: flex;
  gap: 16px;
  padding: 16px;
  border-radius: 8px;
  background: #f5f7fa;
}

.assessment-item.best {
  background: #f0f9ff;
  border: 1px solid #d1ecf1;
}

.assessment-item.weak {
  background: #fef0f0;
  border: 1px solid #f5c6c6;
}

.assessment-content {
  flex: 1;
}

.assessment-label {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.assessment-value {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.level {
  font-size: 14px;
  font-weight: 400;
  color: #666;
  margin-left: 8px;
}

.ability-list h4 {
  margin: 0 0 16px;
  font-size: 16px;
}

.ability-item {
  margin-bottom: 12px;
}

.ability-name {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

/* 薄弱环节 */
.weak-points-section {
  margin-bottom: 20px;
}

.top-weak-points h4 {
  margin: 0 0 16px;
  font-size: 16px;
}

.by-topic {
  margin-top: 20px;
}

.by-topic h4 {
  margin: 0 0 16px;
  font-size: 16px;
}

.topic-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.topic-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

.topic-name {
  font-weight: 500;
}

/* 学习建议 */
.recommendations-section {
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-header h3 {
  margin: 0;
}

.recommendations-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.recommendation-item {
  padding: 16px;
  border-radius: 8px;
  border-left: 4px solid;
  background: #f5f7fa;
}

.recommendation-item.priority-high {
  border-left-color: #f56c6c;
  background: #fef0f0;
}

.recommendation-item.priority-medium {
  border-left-color: #e6a23c;
  background: #fdf6ec;
}

.recommendation-item.priority-low {
  border-left-color: #67c23a;
  background: #f0f9ff;
}

.recommendation-header {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.recommendation-title {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 600;
}

.recommendation-description {
  margin: 0;
  color: #666;
  line-height: 1.6;
}

.priority-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #666;
  font-size: 14px;
}

/* AI 洞察 */
.ai-insights-section {
  margin-bottom: 20px;
}

.ai-insights-section h3 {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ai-insights-content {
  line-height: 1.8;
  color: #333;
  font-size: 15px;
  white-space: pre-wrap;
}

/* 响应式 */
@media (max-width: 768px) {
  .report-header {
    flex-direction: column;
    gap: 16px;
  }

  .header-actions {
    width: 100%;
  }

  .header-actions .el-button {
    flex: 1;
  }

  .stat-card {
    margin-bottom: 12px;
  }
}
</style>
