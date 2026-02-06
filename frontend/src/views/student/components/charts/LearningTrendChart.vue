<template>
  <div class="learning-trend-chart">
    <!-- 时间范围选择器 -->
    <div class="chart-header">
      <el-radio-group v-model="selectedPeriod" @change="handlePeriodChange" size="small">
        <el-radio-button v-for="option in periodOptions" :key="option.value" :label="option.value">
          {{ option.label }}
        </el-radio-button>
      </el-radio-group>

      <!-- 指标切换 -->
      <div class="metric-toggles">
        <el-checkbox-group v-model="selectedMetrics" @change="handleMetricsChange" size="small">
          <el-checkbox label="practices">练习数量</el-checkbox>
          <el-checkbox label="correctRate">正确率</el-checkbox>
          <el-checkbox label="duration">学习时长</el-checkbox>
        </el-checkbox-group>
      </div>
    </div>

    <!-- 图表容器 -->
    <div ref="chartRef" class="chart-container"></div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>加载数据中...</span>
    </div>

    <!-- 空数据状态 -->
    <el-empty v-if="!loading && !hasData" description="暂无学习趋势数据" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import * as echarts from 'echarts'
import { Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { LearningTrendData, TimeRangeOption } from '@/types/report'

// Props
interface Props {
  studentId: string
  reportId?: string
  defaultPeriod?: '7d' | '30d' | '90d'
  height?: number | string
  showLegend?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  defaultPeriod: '30d',
  height: 350,
  showLegend: true
})

// Emits
const emit = defineEmits<{
  (e: 'trendClick', data: { date: string; metrics: Record<string, number> }): void
  (e: 'periodChange', period: string): void
}>()

// Refs
const chartRef = ref<HTMLElement>()
const loading = ref(false)
const selectedPeriod = ref(props.defaultPeriod)
const selectedMetrics = ref<string[]>(['practices', 'correctRate'])
const chartData = ref<LearningTrendData | null>(null)
let chartInstance: echarts.ECharts | null = null

// 时间范围选项
const periodOptions: TimeRangeOption[] = [
  { value: '7d', label: '近7天', days: 7 },
  { value: '30d', label: '近30天', days: 30 },
  { value: '90d', label: '近90天', days: 90 }
]

// 是否有数据
const hasData = computed(() => {
  if (!chartData.value?.metrics) return false
  const metrics = chartData.value.metrics
  return (
    (metrics.practices?.length || 0) > 0 ||
    (metrics.correctRate?.length || 0) > 0 ||
    (metrics.duration?.length || 0) > 0
  )
})

// 获取数据
async function fetchData() {
  if (!props.studentId) return

  loading.value = true
  try {
    const period = periodOptions.find(p => p.value === selectedPeriod.value)
    if (!period) return

    const params = new URLSearchParams({
      period: selectedPeriod.value,
      metrics: selectedMetrics.value.join(',')
    })

    const response = await fetch(
      `/api/v1/reports/${props.reportId || 'latest'}/charts/learning-trend?${params}`,
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      }
    )

    if (!response.ok) {
      throw new Error('获取数据失败')
    }

    const result = await response.json()
    if (result.code === 0) {
      chartData.value = result.data
      updateChart()
    } else {
      throw new Error(result.message || '获取数据失败')
    }
  } catch (error) {
    console.error('获取学习趋势数据失败:', error)
    ElMessage.error('加载学习趋势数据失败')
  } finally {
    loading.value = false
  }
}

// 更新图表
function updateChart() {
  if (!chartInstance || !chartData.value) return

  const metrics = chartData.value.metrics

  // 构建数据系列
  const series: echarts.SeriesOption[] = []
  const dates = [...new Set([
    ...(metrics.practices?.map(p => p.date) || []),
    ...(metrics.correctRate?.map(p => p.date) || []),
    ...(metrics.duration?.map(p => p.date) || [])
  ])].sort()

  if (selectedMetrics.value.includes('practices') && metrics.practices?.length) {
    const practiceData = dates.map(date => {
      const item = metrics.practices?.find(p => p.date === date)
      return item?.count || 0
    })

    series.push({
      name: '练习数量',
      type: 'line',
      smooth: true,
      data: practiceData,
      itemStyle: { color: '#409EFF' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
          { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
        ])
      }
    })
  }

  if (selectedMetrics.value.includes('correctRate') && metrics.correctRate?.length) {
    const rateData = dates.map(date => {
      const item = metrics.correctRate?.find(p => p.date === date)
      return item?.rate || null
    })

    series.push({
      name: '正确率(%)',
      type: 'line',
      smooth: true,
      data: rateData,
      itemStyle: { color: '#67C23A' },
      yAxisIndex: 1
    })
  }

  if (selectedMetrics.value.includes('duration') && metrics.duration?.length) {
    const durationData = dates.map(date => {
      const item = metrics.duration?.find(p => p.date === date)
      return item?.minutes || 0
    })

    series.push({
      name: '学习时长(分钟)',
      type: 'bar',
      data: durationData,
      itemStyle: { color: '#E6A23C' }
    })
  }

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: function (params) {
        if (!Array.isArray(params)) return ''
        let result = `<div style="font-weight: bold; margin-bottom: 8px;">${params[0]?.axisValue || ''}</div>`
        params.forEach(param => {
          if (param.value !== undefined && param.value !== null) {
            const unit = param.seriesName.includes('率') ? '%' : ''
            result += `<div style="display: flex; justify-content: space-between; min-width: 120px; margin: 4px 0;">
              <span style="color: ${param.color}; margin-right: 8px;">●</span>
              <span>${param.seriesName}:</span>
              <span style="font-weight: bold;">${param.value}${unit}</span>
            </div>`
          }
        })
        return result
      }
    },
    legend: {
      show: props.showLegend && selectedMetrics.value.length > 1,
      data: selectedMetrics.value.map(m => {
        const map: Record<string, string> = {
          practices: '练习数量',
          correctRate: '正确率(%)',
          duration: '学习时长(分钟)'
        }
        return map[m] || m
      }),
      bottom: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: props.showLegend && selectedMetrics.value.length > 1 ? '15%' : '3%',
      top: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates,
      axisLabel: {
        formatter: (value: string) => {
          const date = new Date(value)
          return `${date.getMonth() + 1}/${date.getDate()}`
        }
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '数量',
        min: 0,
        axisLabel: {
          formatter: '{value}'
        }
      },
      {
        type: 'value',
        name: '正确率(%)',
        min: 0,
        max: 100,
        axisLabel: {
          formatter: '{value}%'
        },
        show: selectedMetrics.value.includes('correctRate')
      }
    ],
    series: series
  }

  chartInstance.setOption(option, true)
}

// 初始化图表
function initChart() {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)
  chartInstance.on('click', (params) => {
    if (params.componentType === 'series') {
      const date = params.name
      const metrics: Record<string, number> = {}
      if (chartData.value?.metrics.practices) {
        const item = chartData.value.metrics.practices.find(p => p.date === date)
        if (item) metrics.practices = item.count
      }
      emit('trendClick', { date, metrics })
    }
  })

  // 响应窗口变化
  window.addEventListener('resize', handleResize)
}

// 处理窗口大小变化
function handleResize() {
  chartInstance?.resize()
}

// 时间范围变化
function handlePeriodChange(value: string) {
  emit('periodChange', value)
  fetchData()
}

// 指标变化
function handleMetricsChange() {
  updateChart()
}

// 导出图片
async function exportImage(): Promise<Blob> {
  if (!chartInstance) {
    throw new Error('图表未初始化')
  }

  const url = chartInstance.getDataURL({
    type: 'png',
    pixelRatio: 2,
    backgroundColor: '#fff'
  })

  const response = await fetch(url)
  return await response.blob()
}

// 暴露方法
defineExpose({
  exportImage,
  resize: handleResize
})

// 生命周期
onMounted(() => {
  initChart()
  fetchData()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})

// 监听数据变化
watch(chartData, () => {
  updateChart()
}, { deep: true })
</script>

<style scoped lang="scss">
.learning-trend-chart {
  position: relative;
  width: 100%;
  background: #fff;
  border-radius: 8px;
  padding: 16px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;

  .metric-toggles {
    display: flex;
    align-items: center;
  }
}

.chart-container {
  width: 100%;
  height: v-bind('props.height + "px"');
  min-height: 250px;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 12px;
  color: #409EFF;
  font-size: 14px;

  .el-icon {
    font-size: 32px;
  }
}
</style>
