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
          <el-button @click="handleExport('pdf')" :loading="exporting">
            <el-icon><Download /></el-icon>
            导出 PDF
          </el-button>
          <el-button @click="handleExport('image')" :loading="exporting">
            <el-icon><Picture /></el-icon>
            导出图片
          </el-button>
          <el-button type="danger" plain @click="confirmDelete">
            <el-icon><Delete /></el-icon>
            删除
          </el-button>
        </div>
      </div>

      <!-- Tab 导航 -->
      <div class="tab-navigation">
        <el-tabs v-model="activeTab" @tab-change="handleTabChange">
          <el-tab-pane label="概览" name="overview">
            <template #label>
              <el-icon><DataAnalysis /></el-icon>
              <span>概览</span>
            </template>
          </el-tab-pane>
          <el-tab-pane label="学习趋势" name="trends">
            <template #label>
              <el-icon><TrendCharts /></el-icon>
              <span>学习趋势</span>
            </template>
          </el-tab-pane>
          <el-tab-pane label="能力分析" name="abilities">
            <template #label>
              <el-icon><Odometer /></el-icon>
              <span>能力分析</span>
            </template>
          </el-tab-pane>
          <el-tab-pane label="知识点" name="knowledge">
            <template #label>
              <el-icon><Grid /></el-icon>
              <span>知识点</span>
            </template>
          </el-tab-pane>
          <el-tab-pane label="建议" name="recommendations">
            <template #label>
              <el-icon><ChatLineRound /></el-icon>
              <span>学习建议</span>
            </template>
          </el-tab-pane>
        </el-tabs>
      </div>

      <!-- Tab 内容 -->
      <div class="tab-content">
        <!-- 概览 Tab -->
        <div v-show="activeTab === 'overview'" class="tab-pane overview-tab">
          <!-- 学习统计卡片 -->
          <el-card class="stats-section" shadow="never">
            <template #header>
              <h3>学习概况</h3>
            </template>
            <el-row :gutter="20" v-if="report.statistics">
              <el-col :xs="12" :sm="6" v-for="stat in overviewStats" :key="stat.label">
                <div class="stat-card">
                  <div class="stat-icon" :style="{ background: stat.bgColor }">
                    <el-icon :color="stat.color" v-html="stat.icon" />
                  </div>
                  <div class="stat-content">
                    <div class="stat-value">{{ stat.value }}</div>
                    <div class="stat-label">{{ stat.label }}</div>
                  </div>
                </div>
              </el-col>
            </el-row>
          </el-card>

          <!-- 能力雷达图（简化版） -->
          <el-card class="ability-preview-section" shadow="never" v-if="report.ability_analysis">
            <template #header>
              <div class="section-header">
                <h3>能力分布</h3>
                <el-button text type="primary" @click="activeTab = 'abilities'">
                  查看详情 <el-icon><ArrowRight /></el-icon>
                </el-button>
              </div>
            </template>
            <div class="radar-mini-container">
              <div ref="radarMiniRef" class="radar-mini-chart"></div>
            </div>
          </el-card>

          <!-- 薄弱点预览 -->
          <el-card class="weak-preview-section" shadow="never" v-if="report.weak_points?.top_weak_points?.length">
            <template #header>
              <div class="section-header">
                <h3>薄弱知识点</h3>
                <el-button text type="primary" @click="activeTab = 'knowledge'">
                  查看详情 <el-icon><ArrowRight /></el-icon>
                </el-button>
              </div>
            </template>
            <div class="weak-points-preview">
              <el-tag
                v-for="(item, idx) in report.weak_points.top_weak_points.slice(0, 6)"
                :key="idx"
                type="danger"
                size="large"
                effect="plain"
              >
                {{ item.point }} ({{ item.count }}次)
              </el-tag>
            </div>
          </el-card>
        </div>

        <!-- 学习趋势 Tab -->
        <div v-show="activeTab === 'trends'" class="tab-pane trends-tab">
          <LearningTrendChart
            :student-id="report.student_id"
            :report-id="report.id"
            height="450"
            @trend-click="handleTrendClick"
            @period-change="handlePeriodChange"
          />
        </div>

        <!-- 能力分析 Tab -->
        <div v-show="activeTab === 'abilities'" class="tab-pane abilities-tab">
          <AbilityRadarChart
            :student-id="report.student_id"
            :report-id="report.id"
            :show-details="true"
            height="500"
            @ability-click="handleAbilityClick"
            @content-click="handleContentClick"
          />
        </div>

        <!-- 知识点 Tab -->
        <div v-show="activeTab === 'knowledge'" class="tab-pane knowledge-tab">
          <KnowledgeHeatmap
            :student-id="report.student_id"
            :report-id="report.id"
            @cell-click="handleCellClick"
          />
        </div>

        <!-- 学习建议 Tab -->
        <div v-show="activeTab === 'recommendations'" class="tab-pane recommendations-tab">
          <!-- AI 洞察 -->
          <el-card class="ai-insights-section" shadow="never" v-if="report.ai_insights">
            <template #header>
              <h3>
                <el-icon><MagicStick /></el-icon>
                AI 学习洞察
              </h3>
            </template>
            <div class="ai-insights-content">
              {{ report.ai_insights }}
            </div>
          </el-card>

          <!-- 学习建议列表 -->
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
        </div>
      </div>
    </div>

    <!-- 错误状态 -->
    <el-empty v-else description="报告不存在或已被删除" />

    <!-- 导出进度组件 -->
    <ExportProgress
      v-if="showExportProgress"
      ref="exportProgressRef"
      :task-id="currentTaskId"
      :show-backdrop="true"
      :show-close="true"
      @close="handleExportProgressClose"
      @download="handleExportDownload"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, shallowRef } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'
import {
  ArrowLeft,
  ArrowRight,
  Calendar,
  Download,
  Picture,
  Delete,
  Document,
  CircleCheck,
  TrendCharts,
  Clock,
  MagicStick,
  DataAnalysis,
  Odometer,
  Grid,
  ChatLineRound
} from '@element-plus/icons-vue'
import reportApi from '@/api/report'
import LearningTrendChart from './components/charts/LearningTrendChart.vue'
import AbilityRadarChart from './components/charts/AbilityRadarChart.vue'
import KnowledgeHeatmap from './components/charts/KnowledgeHeatmap.vue'
import ExportProgress from './components/report/ExportProgress.vue'

const route = useRoute()
const router = useRouter()

// 状态
const loading = ref(true)
const exporting = ref(false)
const report = ref<any>(null)
const activeTab = ref('overview')
const radarMiniRef = ref<HTMLElement>()
const radarMiniChart = shallowRef<echarts.ECharts | null>(null)

// 导出进度相关
const showExportProgress = ref(false)
const currentTaskId = ref('')
const exportProgressRef = ref()

// 计算概览统计数据
const overviewStats = computed(() => {
  if (!report.value?.statistics) return []

  const stats = report.value.statistics
  return [
    {
      label: '练习次数',
      value: stats.total_practices || 0,
      icon: '<Document />',
      color: '#409eff',
      bgColor: '#ecf5ff'
    },
    {
      label: '完成率',
      value: (stats.completion_rate || 0) + '%',
      icon: '<CircleCheck />',
      color: '#67c23a',
      bgColor: '#f0f9eb'
    },
    {
      label: '平均正确率',
      value: (stats.avg_correct_rate || 0) + '%',
      icon: '<TrendCharts />',
      color: '#f56c6c',
      bgColor: '#fef0f0'
    },
    {
      label: '学习时长',
      value: (stats.total_duration_hours?.toFixed(1) || 0) + 'h',
      icon: '<Clock />',
      color: '#e6a23c',
      bgColor: '#fdf6ec'
    }
  ]
})

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

    // 渲染简化的雷达图
    await nextTick()
    if (data.ability_analysis?.ability_radar) {
      renderRadarMini(data.ability_analysis.ability_radar)
    }
  } catch (error: any) {
    ElMessage.error('加载报告失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 渲染简化版雷达图
const renderRadarMini = (radarData: Array<{ name: string; value: number; confidence: number }>) => {
  if (!radarMiniRef.value) return

  try {
    radarMiniChart.value = echarts.init(radarMiniRef.value)

    const option: EChartsOption = {
      tooltip: {
        trigger: 'item'
      },
      radar: {
        indicator: radarData.map(item => ({
          name: item.name,
          max: 100
        })),
        radius: '60%',
        axisName: {
          color: '#666',
          fontSize: 11
        },
        splitArea: {
          areaStyle: {
            color: ['rgba(64, 158, 255, 0.02)', 'rgba(64, 158, 255, 0.05)']
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

    radarMiniChart.value.setOption(option)
  } catch (error) {
    console.error('雷达图渲染失败:', error)
  }
}

// 处理导出
const handleExport = async (format: 'pdf' | 'image') => {
  if (!report.value) return

  exporting.value = true
  try {
    // 检测是否需要异步模式（大报告）
    const isLargeReport = shouldUseAsyncMode()

    if (isLargeReport) {
      // 使用异步导出
      const response = await fetch('/api/v1/reports/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          report_id: report.value.id,
          export_format: format,
          report_type: 'full',
          async_mode: true
        })
      })

      const result = await response.json()
      if (result.code === 0) {
        currentTaskId.value = result.data.taskId
        showExportProgress.value = true
        exporting.value = false
        return
      }
    }

    // 同步导出（小报告）
    const blob = await reportApi.exportReport(report.value.id, format)
    downloadBlob(blob, format)
    ElMessage.success(`导出${format === 'pdf' ? 'PDF' : '图片'}成功`)
  } catch (error: any) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败，请稍后重试')
  } finally {
    exporting.value = false
  }
}

// 判断是否使用异步模式
const shouldUseAsyncMode = (): boolean => {
  // 超过30天的报告使用异步模式
  if (!report.value) return false
  const start = new Date(report.value.period_start)
  const end = new Date(report.value.period_end)
  const days = (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)
  return days > 30
}

// 下载文件
const downloadBlob = (blob: Blob, format: string) => {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url

  const title = report.value?.title || '学习报告'
  const date = new Date(report.value?.period_end).toISOString().split('T')[0]
  link.download = `${title}_${date}.${format === 'pdf' ? 'pdf' : 'png'}`

  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

// 处理导出进度关闭
const handleExportProgressClose = () => {
  showExportProgress.value = false
}

// 处理导出下载
const handleExportDownload = (url: string) => {
  window.open(url, '_blank')
}

// Tab 切换
const handleTabChange = (tab: string) => {
  // 触发图表resize
  nextTick(() => {
    window.dispatchEvent(new Event('resize'))
  })
}

// 趋势点击
const handleTrendClick = (data: { date: string; metrics: Record<string, number> }) => {
  console.log('趋势数据点击:', data)
}

// 时间范围变化
const handlePeriodChange = (period: string) => {
  console.log('时间范围变化:', period)
}

// 能力点击
const handleAbilityClick = (ability: any) => {
  console.log('能力点击:', ability)
}

// 内容点击
const handleContentClick = (content: any) => {
  ElMessage.info(`跳转到: ${content.title}`)
}

// 知识点单元格点击
const handleCellClick = (data: { topic: any; ability: any }) => {
  console.log('知识点单元格点击:', data)
}

// 确认删除
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

// 返回列表
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

// 窗口大小变化处理
const handleResize = () => {
  radarMiniChart.value?.resize()
}

// 生命周期
onMounted(() => {
  loadReport()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  radarMiniChart.value?.dispose()
})
</script>

<style scoped lang="scss">
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

/* Tab 导航 */
.tab-navigation {
  background: #fff;
  border-radius: 8px;
  padding: 8px 16px;
  margin-bottom: 16px;

  :deep(.el-tabs__nav-wrap::after) {
    display: none;
  }

  :deep(.el-tabs__item) {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 14px;

    .el-icon {
      margin-bottom: 0;
    }
  }
}

.tab-content {
  min-height: 400px;
}

.tab-pane {
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
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

  &:hover {
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
    font-size: 24px;
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
}

/* 章节头部 */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
  }
}

/* 能力预览 */
.radar-mini-container {
  height: 280px;
}

.radar-mini-chart {
  width: 100%;
  height: 100%;
}

/* 薄弱点预览 */
.weak-points-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* 学习建议 */
.recommendations-section {
  margin-bottom: 20px;
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

  &.priority-high {
    border-left-color: #f56c6c;
    background: #fef0f0;
  }

  &.priority-medium {
    border-left-color: #e6a23c;
    background: #fdf6ec;
  }

  &.priority-low {
    border-left-color: #67c23a;
    background: #f0f9eb;
  }
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

  h3 {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0;
    font-size: 16px;
    font-weight: 600;
  }
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
    flex-wrap: wrap;

    .el-button {
      flex: 1;
      min-width: 80px;
    }
  }

  .tab-navigation {
    overflow-x: auto;

    :deep(.el-tabs__item) {
      padding: 0 12px;
    }
  }

  .stat-card {
    margin-bottom: 12px;
  }
}
</style>
