<template>
  <div class="ability-radar-chart">
    <!-- 头部控制栏 -->
    <div class="chart-header">
      <el-radio-group v-model="compareMode" @change="handleCompareChange" size="small">
        <el-radio-button label="none">当前水平</el-radio-button>
        <el-radio-button label="class_avg">班级对比</el-radio-button>
        <el-radio-button label="history">历史对比</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 图表和详情布局 -->
    <div class="chart-content">
      <!-- 雷达图 - 添加错误边界 -->
      <ErrorBoundary>
        <div ref="chartRef" class="radar-container"></div>
      </ErrorBoundary>

      <!-- 能力详情面板 -->
      <div v-if="showDetails && selectedAbility" class="ability-details">
        <div class="detail-header">
          <h4>{{ selectedAbility.name }}</h4>
          <el-button text @click="selectedAbility = null">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>

        <div class="detail-content">
          <div class="detail-score">
            <span class="label">当前水平</span>
            <span class="value">{{ selectedAbility.value.toFixed(1) }}</span>
            <el-progress
              :percentage="selectedAbility.value"
              :stroke-width="8"
              :color="getScoreColor(selectedAbility.value)"
            />
          </div>

          <div v-if="compareMode === 'class_avg' && classAverage" class="detail-comparison">
            <span class="label">班级平均</span>
            <span class="value">{{ (classAverage[selectedAbility.key] || 0).toFixed(1) }}</span>
          </div>

          <div v-if="selectedAbility.history?.length" class="detail-history">
            <span class="label">历史趋势</span>
            <div class="history-dots">
              <span
                v-for="(h, idx) in selectedAbility.history"
                :key="idx"
                class="history-dot"
                :style="{ backgroundColor: getScoreColor(h) }"
              />
            </div>
          </div>

          <div v-if="selectedAbility.relatedTopics?.length" class="detail-topics">
            <span class="label">相关知识点</span>
            <div class="topic-tags">
              <el-tag
                v-for="topic in selectedAbility.relatedTopics.slice(0, 5)"
                :key="topic"
                size="small"
                type="info"
              >
                {{ topic }}
              </el-tag>
            </div>
          </div>

          <div v-if="selectedAbility.recommendedContent?.length" class="detail-recommendations">
            <span class="label">推荐练习</span>
            <div class="recommendation-list">
              <div
                v-for="content in selectedAbility.recommendedContent.slice(0, 3)"
                :key="content.contentId"
                class="recommendation-item"
                @click="handleContentClick(content)"
              >
                <span class="title">{{ content.title }}</span>
                <el-tag size="small">{{ content.difficulty }}</el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 能力概览 -->
    <div class="ability-overview">
      <div class="overview-item">
        <span class="label">最强项</span>
        <span class="value highlight-green">{{ strongestPoint?.name || '暂无' }}</span>
        <span class="score">{{ strongestPoint?.value?.toFixed(1) || 0 }}</span>
      </div>
      <div class="overview-item">
        <span class="label">最弱项</span>
        <span class="value highlight-red">{{ weakestPoint?.name || '暂无' }}</span>
        <span class="score">{{ weakestPoint?.value?.toFixed(1) || 0 }}</span>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>加载数据中...</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import * as echarts from 'echarts'
import { Loading, Close } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { AbilityRadarData, ContentRecommendation } from '@/types/report'
import ErrorBoundary from '@/components/ErrorBoundary.vue'

// Props
interface Props {
  studentId: string
  reportId?: string
  showDetails?: boolean
  height?: number | string
}

const props = withDefaults(defineProps<Props>(), {
  showDetails: true,
  height: 400
})

// Emits
const emit = defineEmits<{
  (e: 'abilityClick', ability: any): void
  (e: 'contentClick', content: ContentRecommendation): void
}>()

// Refs
const chartRef = ref<HTMLElement>()
const loading = ref(false)
const compareMode = ref<'none' | 'class_avg' | 'history'>('none')
const radarData = ref<AbilityRadarData | null>(null)
const selectedAbility = ref<any>(null)
let chartInstance: echarts.ECharts | null = null

// 计算属性
const strongestPoint = computed(() => radarData.value?.strongestPoint)
const weakestPoint = computed(() => radarData.value?.weakestPoint)
const classAverage = computed(() => radarData.value?.classAverage)

// 能力名称映射
const abilityLabels: Record<string, string> = {
  vocabulary: '词汇',
  grammar: '语法',
  reading: '阅读',
  listening: '听力',
  speaking: '口语',
  writing: '写作'
}

// 获取数据
async function fetchData() {
  if (!props.studentId) return

  loading.value = true
  try {
    const params = new URLSearchParams({
      compare_with: compareMode.value
    })

    const response = await fetch(
      `/api/v1/reports/${props.reportId || 'latest'}/charts/ability-radar?${params}`,
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
      radarData.value = result.data
      updateChart()
    } else {
      throw new Error(result.message || '获取数据失败')
    }
  } catch (error) {
    console.error('获取能力雷达图数据失败:', error)
    ElMessage.error('加载能力数据失败')
  } finally {
    loading.value = false
  }
}

// 更新图表
function updateChart() {
  if (!chartInstance || !radarData.value) return

  const abilities = radarData.value.abilities || []

  // 构建雷达图指标
  const indicator = abilities.map(a => ({
    name: a.name,
    max: 100,
    min: 0
  }))

  // 当前数据
  const currentData = abilities.map(a => a.value)

  // 对比数据
  const comparisonData = compareMode.value === 'class_avg' && radarData.value.classAverage
    ? indicator.map((_, idx) => {
        const abilityKey = Object.keys(abilityLabels).find(
          key => abilityLabels[key] === abilities[idx]?.name
        ) || abilities[idx]?.name?.toLowerCase()
        return radarData.value?.classAverage?.[abilityKey] || 0
      })
    : []

  const seriesData: any[] = [
    {
      value: currentData,
      name: '当前水平',
      areaStyle: {
        color: new echarts.graphic.RadialGradient(0.5, 0.5, 0.5, [
          { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
          { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
        ])
      },
      lineStyle: {
        width: 3,
        color: '#409EFF'
      },
      itemStyle: {
        color: '#409EFF'
      }
    }
  ]

  if (comparisonData.length > 0) {
    seriesData.push({
      value: comparisonData,
      name: compareMode.value === 'class_avg' ? '班级平均' : '历史数据',
      lineStyle: {
        width: 2,
        type: 'dashed',
        color: '#E6A23C'
      },
      itemStyle: {
        color: '#E6A23C'
      }
    })
  }

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'item',
      formatter: function (params) {
        const ability = abilities[params.dataIndex]
        if (!ability) return ''

        let result = `<div style="font-weight: bold; margin-bottom: 8px;">${ability.name}</div>`
        result += `<div>当前水平: ${ability.value.toFixed(1)}</div>`

        if (params.seriesIndex === 1) {
          const compValue = comparisonData[params.dataIndex]
          result += `<div>对比数据: ${compValue?.toFixed(1) || '-'}</div>`
        }

        return result
      }
    },
    legend: {
      data: seriesData.map(s => s.name),
      bottom: 0
    },
    radar: {
      indicator: indicator,
      shape: 'polygon',
      splitNumber: 5,
      axisName: {
        color: '#606266',
        fontSize: 12
      },
      splitArea: {
        areaStyle: {
          color: ['rgba(64, 158, 255, 0.02)', 'rgba(64, 158, 255, 0.05)']
        }
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(64, 158, 255, 0.1)'
        }
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(64, 158, 255, 0.2)'
        }
      }
    },
    series: [
      {
        type: 'radar',
        data: seriesData,
        emphasis: {
          lineStyle: {
            width: 4
          }
        }
      }
    ]
  }

  chartInstance.setOption(option, true)
}

// 获取分数颜色
function getScoreColor(score: number): string {
  if (score >= 80) return '#67C23A'
  if (score >= 60) return '#409EFF'
  if (score >= 40) return '#E6A23C'
  return '#F56C6C'
}

// 处理对比模式变化
function handleCompareChange() {
  fetchData()
}

// 处理能力点击
function handleAbilityClick(params: any) {
  if (!radarData.value?.abilities) return

  const ability = radarData.value.abilities[params.dataIndex]
  if (!ability) return

  // 添加key属性用于详情面板
  const abilityKey = Object.keys(abilityLabels).find(
    key => abilityLabels[key] === ability.name
  ) || ability.name?.toLowerCase()

  selectedAbility.value = {
    ...ability,
    key: abilityKey
  }

  emit('abilityClick', ability)
}

// 处理推荐内容点击
function handleContentClick(content: ContentRecommendation) {
  emit('contentClick', content)
  ElMessage.info(`跳转到: ${content.title}`)
}

// 初始化图表
function initChart() {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)
  chartInstance.on('click', handleAbilityClick)

  window.addEventListener('resize', handleResize)
}

// 处理窗口大小变化
function handleResize() {
  chartInstance?.resize()
}

// 暴露方法
defineExpose({
  resize: handleResize,
  getChartInstance: () => chartInstance
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
watch(radarData, () => {
  updateChart()
}, { deep: true })
</script>

<style scoped lang="scss">
.ability-radar-chart {
  position: relative;
  width: 100%;
  background: #fff;
  border-radius: 8px;
  padding: 16px;
}

.chart-header {
  margin-bottom: 16px;
  display: flex;
  justify-content: center;
}

.chart-content {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.radar-container {
  width: 400px;
  height: v-bind('props.height + "px"');
  flex-shrink: 0;
  margin: 0 auto;
}

.ability-details {
  flex: 1;
  min-width: 280px;
  background: #f5f7fa;
  border-radius: 8px;
  padding: 16px;

  .detail-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #e4e7ed;

    h4 {
      margin: 0;
      font-size: 16px;
      color: #303133;
    }
  }

  .detail-content {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .detail-score,
  .detail-comparison,
  .detail-history,
  .detail-topics,
  .detail-recommendations {
    .label {
      display: block;
      font-size: 12px;
      color: #909399;
      margin-bottom: 6px;
    }

    .value {
      font-size: 24px;
      font-weight: bold;
      color: #409EFF;
    }
  }

  .detail-comparison {
    .value {
      font-size: 18px;
      color: #E6A23C;
    }
  }

  .detail-history {
    .history-dots {
      display: flex;
      gap: 4px;
      margin-top: 8px;
    }

    .history-dot {
      width: 12px;
      height: 12px;
      border-radius: 50%;
    }
  }

  .topic-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 8px;
  }

  .recommendation-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 8px;
  }

  .recommendation-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    background: #fff;
    border-radius: 4px;
    cursor: pointer;
    transition: background 0.2s;

    &:hover {
      background: #ecf5ff;
    }

    .title {
      font-size: 13px;
      color: #303133;
    }
  }
}

.ability-overview {
  display: flex;
  justify-content: center;
  gap: 48px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;

  .overview-item {
    text-align: center;

    .label {
      display: block;
      font-size: 12px;
      color: #909399;
      margin-bottom: 4px;
    }

    .value {
      font-size: 16px;
      font-weight: 500;
      margin-right: 8px;

      &.highlight-green {
        color: #67C23A;
      }

      &.highlight-red {
        color: #F56C6C;
      }
    }

    .score {
      font-size: 18px;
      font-weight: bold;
      color: #303133;
    }
  }
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

@media (max-width: 768px) {
  .radar-container {
    width: 100%;
    height: 300px;
  }

  .ability-details {
    min-width: 100%;
  }
}
</style>
