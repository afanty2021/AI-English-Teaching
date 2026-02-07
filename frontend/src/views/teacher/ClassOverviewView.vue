<template>
  <div class="class-overview-view">
    <div class="header">
      <h1>班级学习状况</h1>
      <el-button @click="refreshData">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <!-- 筛选器 -->
    <el-card
      class="filter-card"
      shadow="never"
    >
      <el-form
        :inline="true"
        :model="filters"
        @submit.prevent="loadClassSummary"
      >
        <el-form-item label="班级">
          <el-select
            v-model="filters.classId"
            placeholder="请选择班级"
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

        <el-form-item label="统计时间">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 240px"
            @change="handleDateRangeChange"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            @click="loadClassSummary"
          >
            查询
          </el-button>
          <el-button @click="resetFilters">
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 班级概况 -->
    <el-card
      v-if="summary"
      class="overview-card"
      shadow="never"
    >
      <template #header>
        <div class="card-header">
          <h3>{{ summary.class_name }}</h3>
          <el-tag type="success">
            统计周期：{{ formatDateRange(summary.period_start, summary.period_end) }}
          </el-tag>
        </div>
      </template>

      <div class="overview-grid">
        <div class="overview-item">
          <div
            class="item-icon"
            style="background-color: #409EFF;"
          >
            <el-icon><User /></el-icon>
          </div>
          <div class="item-content">
            <div class="item-value">
              {{ summary.total_students }}
            </div>
            <div class="item-label">
              班级总人数
            </div>
          </div>
        </div>

        <div class="overview-item">
          <div
            class="item-icon"
            style="background-color: #67C23A;"
          >
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="item-content">
            <div class="item-value">
              {{ summary.active_students }}
            </div>
            <div class="item-label">
              活跃学生数
            </div>
          </div>
        </div>

        <div class="overview-item">
          <div
            class="item-icon"
            style="background-color: #E6A23C;"
          >
            <el-icon><Clock /></el-icon>
          </div>
          <div class="item-content">
            <div class="item-value">
              {{ summary.overall_stats.total_study_hours.toFixed(1) }}h
            </div>
            <div class="item-label">
              总学习时长
            </div>
          </div>
        </div>

        <div class="overview-item">
          <div
            class="item-icon"
            style="background-color: #F56C6C;"
          >
            <el-icon><Trophy /></el-icon>
          </div>
          <div class="item-content">
            <div class="item-value">
              {{ (summary.overall_stats.avg_completion_rate * 100).toFixed(1) }}%
            </div>
            <div class="item-label">
              平均完成率
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 图表区域 -->
    <div
      v-if="summary"
      class="charts-container"
    >
      <!-- 能力分布雷达图 -->
      <el-card
        class="chart-card"
        shadow="never"
      >
        <template #header>
          <h3><el-icon><PieChart /></el-icon> 班级能力分布</h3>
        </template>
        <div
          ref="radarChartRef"
          class="chart"
        ></div>
      </el-card>

      <!-- 学习完成率柱状图 -->
      <el-card
        class="chart-card"
        shadow="never"
      >
        <template #header>
          <h3><el-icon><BarChart /></el-icon> 学习完成率分布</h3>
        </template>
        <div
          ref="barChartRef"
          class="chart"
        ></div>
      </el-card>
    </div>

    <!-- 薄弱知识点 -->
    <el-card
      v-if="summary?.top_weak_points?.length"
      class="weak-points-card"
      shadow="never"
    >
      <template #header>
        <h3><el-icon><Warning /></el-icon> 班级薄弱知识点汇总</h3>
      </template>

      <div class="weak-points-list">
        <div
          v-for="wp in summary.top_weak_points"
          :key="wp.knowledge_point"
          class="weak-point-item"
        >
          <div class="point-info">
            <strong>{{ wp.knowledge_point }}</strong>
            <span class="affected-count">影响 {{ wp.affected_students }} 名学生</span>
          </div>
          <div class="progress-container">
            <el-progress
              :percentage="(wp.affected_students / summary.total_students) * 100"
              :show-text="false"
              :stroke-width="8"
            />
            <span class="percentage">
              {{ ((wp.affected_students / summary.total_students) * 100).toFixed(1) }}%
            </span>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 加载状态 -->
    <div
      v-else-if="loading"
      class="loading"
    >
      <el-skeleton
        :rows="8"
        animated
      />
    </div>

    <!-- 空状态 -->
    <el-empty
      v-else
      description="请选择班级查看学习状况"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Refresh,
  User,
  TrendCharts,
  Clock,
  Trophy,
  PieChart,
  Warning
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import teacherReportApi, { type ClassSummary } from '@/api/teacherReport'

// 状态
const loading = ref(false)
const summary = ref<ClassSummary | null>(null)
const radarChartRef = ref<HTMLElement>()
const barChartRef = ref<HTMLElement>()

// 筛选
const filters = reactive({
  classId: 'class-1'
})

const dateRange = ref<string[]>([])

// 教师班级列表（模拟数据）
const teacherClasses = ref([
  { id: 'class-1', name: '高一(1)班' },
  { id: 'class-2', name: '高一(2)班' },
  { id: 'class-3', name: '高二(1)班' },
])

// 方法
const loadClassSummary = async () => {
  if (!filters.classId) {
    ElMessage.warning('请选择班级')
    return
  }

  loading.value = true
  try {
    const [startDate, endDate] = dateRange.value || []
    const data = await teacherReportApi.getClassSummary({
      classId: filters.classId,
      periodStart: startDate,
      periodEnd: endDate
    })
    summary.value = data

    await nextTick()
    initCharts()
  } catch (error: any) {
    ElMessage.error('加载班级状况失败')
  } finally {
    loading.value = false
  }
}

const initCharts = () => {
  if (!summary.value) return

  // 初始化雷达图
  if (radarChartRef.value) {
    const radarChart = echarts.init(radarChartRef.value)

    const abilityData = summary.value.ability_distribution
    const radarOption = {
      title: {
        text: '班级整体能力水平',
        left: 'center'
      },
      radar: {
        indicator: [
          { name: '听力', max: 100 },
          { name: '阅读', max: 100 },
          { name: '口语', max: 100 },
          { name: '写作', max: 100 },
          { name: '语法', max: 100 },
          { name: '词汇', max: 100 }
        ]
      },
      series: [{
        type: 'radar',
        data: [{
          value: [
            abilityData.listening,
            abilityData.reading,
            abilityData.speaking,
            abilityData.writing,
            abilityData.grammar,
            abilityData.vocabulary
          ],
          name: '班级平均能力'
        }]
      }]
    }

    radarChart.setOption(radarOption)
  }

  // 初始化柱状图（模拟数据）
  if (barChartRef.value) {
    const barChart = echarts.init(barChartRef.value)

    const barOption = {
      title: {
        text: '学生完成率分布',
        left: 'center'
      },
      xAxis: {
        type: 'category',
        data: ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%']
      },
      yAxis: {
        type: 'value'
      },
      series: [{
        data: [2, 5, 8, 12, 6],
        type: 'bar',
        itemStyle: {
          color: '#409EFF'
        }
      }]
    }

    barChart.setOption(barOption)
  }
}

const handleClassChange = () => {
  loadClassSummary()
}

const handleDateRangeChange = (_dates: string[]) => {
  // 处理日期范围变化
}

const resetFilters = () => {
  filters.classId = 'class-1'
  dateRange.value = []
  loadClassSummary()
}

const refreshData = () => {
  loadClassSummary()
}

// 辅助方法
const formatDateRange = (startStr: string, endStr: string) => {
  const start = new Date(startStr)
  const end = new Date(endStr)
  const startFormatted = start.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  const endFormatted = end.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  return `${startFormatted} - ${endFormatted}`
}

// 监听窗口大小变化
const handleResize = () => {
  if (summary.value) {
    initCharts()
  }
}

window.addEventListener('resize', handleResize)

// 生命周期
onMounted(() => {
  // 设置默认日期范围（最近30天）
  const endDate = new Date()
  const startDate = new Date()
  startDate.setDate(endDate.getDate() - 30)
  dateRange.value = [
    startDate.toISOString().split('T')[0] ?? '',
    endDate.toISOString().split('T')[0] ?? ''
  ]

  loadClassSummary()
})
</script>

<style scoped>
.class-overview-view {
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

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.overview-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  background-color: var(--el-bg-color-page);
}

.item-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
}

.item-content {
  flex: 1;
}

.item-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--el-color-primary);
  margin-bottom: 4px;
}

.item-label {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.charts-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.chart-card {
  min-height: 400px;
}

.chart {
  width: 100%;
  height: 300px;
}

.weak-points-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.weak-point-item {
  padding: 16px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  background-color: var(--el-bg-color-page);
}

.point-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.point-info strong {
  font-size: 16px;
}

.affected-count {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.progress-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.percentage {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-color-primary);
  min-width: 50px;
  text-align: right;
}

.loading {
  padding: 20px;
}

@media (max-width: 768px) {
  .charts-container {
    grid-template-columns: 1fr;
  }

  .overview-grid {
    grid-template-columns: 1fr;
  }
}
</style>
