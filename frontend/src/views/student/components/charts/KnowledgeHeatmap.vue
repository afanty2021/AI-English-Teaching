<template>
  <div class="knowledge-heatmap">
    <!-- 筛选控制栏 -->
    <div class="filter-bar">
      <div class="filter-group">
        <span class="filter-label">能力类型</span>
        <el-select
          v-model="selectedAbility"
          placeholder="全部"
          clearable
          size="small"
          @change="handleFilterChange"
        >
          <el-option
            v-for="ability in abilityOptions"
            :key="ability.value"
            :label="ability.label"
            :value="ability.value"
          />
        </el-select>
      </div>

      <div class="filter-group">
        <span class="filter-label">主题</span>
        <el-select
          v-model="selectedTopic"
          placeholder="全部"
          clearable
          size="small"
          @change="handleFilterChange"
        >
          <el-option
            v-for="topic in topicOptions"
            :key="topic"
            :label="topic"
            :value="topic"
          />
        </el-select>
      </div>

      <div class="filter-group">
        <span class="filter-label">难度</span>
        <el-select
          v-model="selectedDifficulty"
          placeholder="全部"
          clearable
          size="small"
          @change="handleFilterChange"
        >
          <el-option
            v-for="diff in difficultyOptions"
            :key="diff.value"
            :label="diff.label"
            :value="diff.value"
          />
        </el-select>
      </div>
    </div>

    <!-- 热力图表格 -->
    <div
      v-if="!loading"
      class="heatmap-container"
    >
      <div
        v-for="topic in heatmapData?.topics || []"
        :key="topic.id"
        class="heatmap-topic"
      >
        <div
          class="topic-header"
          @click="toggleTopic(topic.id)"
        >
          <el-icon :class="{ expanded: expandedTopics.includes(topic.id) }">
            <ArrowRight />
          </el-icon>
          <span class="topic-name">{{ topic.name }}</span>
          <span class="topic-count">{{ topic.abilities.length }} 个能力点</span>
        </div>

        <div
          v-show="expandedTopics.includes(topic.id)"
          class="topic-details"
        >
          <div class="abilities-grid">
            <div
              v-for="ability in topic.abilities"
              :key="ability.name"
              class="ability-cell"
              :style="{ backgroundColor: getMasteryColor(ability.masteryRate) }"
              @click="handleCellClick(topic, ability)"
              @mouseenter="showCellDetail($event, topic, ability)"
              @mouseleave="hideCellDetail"
            >
              <span class="ability-name">{{ ability.name }}</span>
              <span class="ability-rate">{{ ability.masteryRate.toFixed(0) }}%</span>
              <span
                class="ability-trend"
                :class="ability.trend"
              >
                <el-icon v-if="ability.trend === 'up'"><Top /></el-icon>
                <el-icon v-else-if="ability.trend === 'down'"><Bottom /></el-icon>
                <el-icon v-else><Remove /></el-icon>
              </span>
            </div>
          </div>
        </div>
      </div>

      <el-empty
        v-if="!heatmapData?.topics?.length"
        description="暂无知识点数据"
      />
    </div>

    <!-- 加载状态 -->
    <div
      v-else
      class="loading-state"
    >
      <el-icon class="is-loading">
        <Loading />
      </el-icon>
      <span>加载数据中...</span>
    </div>

    <!-- 单元格详情悬浮框 -->
    <div
      v-if="cellDetail.visible"
      class="cell-detail-popover"
      :style="{ left: cellDetail.x + 'px', top: cellDetail.y + 'px' }"
    >
      <div class="popover-header">
        <span class="ability-name">{{ cellDetail.data?.ability?.name }}</span>
        <span class="topic-name">{{ cellDetail.data?.topic?.name }}</span>
      </div>
      <div class="popover-content">
        <div class="detail-row">
          <span class="label">掌握率</span>
          <span class="value">{{ cellDetail.data?.ability?.masteryRate?.toFixed(1) }}%</span>
        </div>
        <div class="detail-row">
          <span class="label">练习次数</span>
          <span class="value">{{ cellDetail.data?.ability?.practiceCount }}</span>
        </div>
        <div class="detail-row">
          <span class="label">难度</span>
          <el-tag size="small">
            {{ cellDetail.data?.ability?.difficulty }}
          </el-tag>
        </div>
        <div class="detail-row">
          <span class="label">趋势</span>
          <span
            class="trend-value"
            :class="cellDetail.data?.ability?.trend"
          >
            <el-icon v-if="cellDetail.data?.ability?.trend === 'up'"><Top /></el-icon>
            <el-icon v-else-if="cellDetail.data?.ability?.trend === 'down'"><Bottom /></el-icon>
            <el-icon v-else><Remove /></el-icon>
            {{ getTrendLabel(cellDetail.data?.ability?.trend) }}
          </span>
        </div>
      </div>
    </div>

    <!-- 图例 -->
    <div class="heatmap-legend">
      <span class="legend-label">掌握率</span>
      <div class="legend-gradient">
        <div class="gradient-bar"></div>
        <span class="gradient-0">0%</span>
        <span class="gradient-50">50%</span>
        <span class="gradient-100">100%</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, ArrowRight, Top, Bottom, Remove } from '@element-plus/icons-vue'
import type { KnowledgeHeatmapData } from '@/types/report'

// Props
interface Props {
  studentId: string
  reportId?: string
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  (e: 'cellClick', data: { topic: any; ability: any }): void
}>()

// Refs
const loading = ref(false)
const heatmapData = ref<KnowledgeHeatmapData | null>(null)
const selectedAbility = ref('')
const selectedTopic = ref('')
const selectedDifficulty = ref('')
const expandedTopics = ref<string[]>([])

// 单元格详情
const cellDetail = ref({
  visible: false,
  x: 0,
  y: 0,
  data: null as { topic: any; ability: any } | null
})

// 选项列表
const abilityOptions = [
  { value: 'vocabulary', label: '词汇' },
  { value: 'grammar', label: '语法' },
  { value: 'reading', label: '阅读' },
  { value: 'listening', label: '听力' },
  { value: 'speaking', label: '口语' },
  { value: 'writing', label: '写作' }
]

const difficultyOptions = [
  { value: 'easy', label: '简单' },
  { value: 'medium', label: '中等' },
  { value: 'hard', label: '困难' },
  { value: 'expert', label: '专家' }
]

// 计算主题选项
const topicOptions = computed(() => {
  const topics = heatmapData.value?.topics || []
  return topics.map(t => t.name)
})

// 获取数据
async function fetchData() {
  if (!props.studentId) return

  loading.value = true
  try {
    const params = new URLSearchParams()
    if (selectedAbility.value) params.append('filter_by_ability', selectedAbility.value)
    if (selectedTopic.value) params.append('filter_by_topic', selectedTopic.value)
    if (selectedDifficulty.value) params.append('filter_by_difficulty', selectedDifficulty.value)

    const response = await fetch(
      `/api/v1/reports/${props.reportId || 'latest'}/charts/knowledge-heatmap?${params}`,
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
      heatmapData.value = result.data
      // 默认展开第一个主题
      if (result.data.topics?.length && !expandedTopics.value.length) {
        expandedTopics.value = [result.data.topics[0].id]
      }
    } else {
      throw new Error(result.message || '获取数据失败')
    }
  } catch (error) {
    console.error('获取知识点热力图数据失败:', error)
    ElMessage.error('加载知识点数据失败')
  } finally {
    loading.value = false
  }
}

// 获取掌握率颜色
function getMasteryColor(rate: number): string {
  if (rate >= 80) return 'rgba(103, 194, 58, 0.8)'
  if (rate >= 60) return 'rgba(64, 158, 255, 0.7)'
  if (rate >= 40) return 'rgba(230, 162, 60, 0.7)'
  if (rate >= 20) return 'rgba(245, 108, 108, 0.6)'
  return 'rgba(144, 147, 153, 0.5)'
}

// 获取趋势标签
function getTrendLabel(trend: string | undefined): string {
  const labels: Record<string, string> = {
    up: '上升',
    down: '下降',
    stable: '稳定'
  }
  return labels[trend || 'stable'] || '稳定'
}

// 切换主题展开/收起
function toggleTopic(topicId: string) {
  const idx = expandedTopics.value.indexOf(topicId)
  if (idx === -1) {
    expandedTopics.value.push(topicId)
  } else {
    expandedTopics.value.splice(idx, 1)
  }
}

// 处理筛选变化
function handleFilterChange() {
  fetchData()
}

// 处理单元格点击
function handleCellClick(topic: any, ability: any) {
  emit('cellClick', { topic, ability })
  ElMessage.info(`查看 ${ability.name} 详细分析`)
}

// 显示单元格详情
function showCellDetail(event: MouseEvent, topic: any, ability: any) {
  cellDetail.value = {
    visible: true,
    x: event.clientX + 15,
    y: event.clientY + 15,
    data: { topic, ability }
  }
}

// 隐藏单元格详情
function hideCellDetail() {
  cellDetail.value.visible = false
}

// 初始化
onMounted(() => {
  fetchData()
})
</script>

<style scoped lang="scss">
.knowledge-heatmap {
  position: relative;
  width: 100%;
  background: #fff;
  border-radius: 8px;
  padding: 16px;
}

.filter-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;

  .filter-group {
    display: flex;
    align-items: center;
    gap: 8px;

    .filter-label {
      font-size: 13px;
      color: #606266;
      white-space: nowrap;
    }
  }
}

.heatmap-container {
  min-height: 200px;
}

.heatmap-topic {
  margin-bottom: 12px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  overflow: hidden;

  .topic-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 16px;
    background: #f5f7fa;
    cursor: pointer;
    user-select: none;

    .el-icon {
      transition: transform 0.2s;

      &.expanded {
        transform: rotate(90deg);
      }
    }

    .topic-name {
      font-weight: 500;
      color: #303133;
    }

    .topic-count {
      font-size: 12px;
      color: #909399;
      margin-left: auto;
    }

    &:hover {
      background: #ecf5ff;
    }
  }

  .topic-details {
    padding: 12px;
  }
}

.abilities-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 8px;
}

.ability-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 12px 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  position: relative;

  &:hover {
    transform: scale(1.05);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  }

  .ability-name {
    font-size: 12px;
    color: #fff;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
    text-align: center;
    line-height: 1.2;
  }

  .ability-rate {
    font-size: 16px;
    font-weight: bold;
    color: #fff;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
    margin: 4px 0;
  }

  .ability-trend {
    font-size: 12px;

    &.up {
      color: #67C23A;
    }

    &.down {
      color: #F56C6C;
    }

    &.stable {
      color: #909399;
    }
  }
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-height: 200px;
  color: #409EFF;

  .el-icon {
    font-size: 32px;
  }
}

.cell-detail-popover {
  position: fixed;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  padding: 12px;
  z-index: 1000;
  min-width: 180px;

  .popover-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 8px;
    margin-bottom: 8px;
    border-bottom: 1px solid #ebeef5;

    .ability-name {
      font-weight: 500;
      color: #303133;
    }

    .topic-name {
      font-size: 12px;
      color: #909399;
    }
  }

  .popover-content {
    .detail-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 6px;
      font-size: 13px;

      .label {
        color: #909399;
      }

      .value {
        color: #303133;
        font-weight: 500;
      }

      .trend-value {
        display: flex;
        align-items: center;
        gap: 4px;

        &.up {
          color: #67C23A;
        }

        &.down {
          color: #F56C6C;
        }

        &.stable {
          color: #909399;
        }
      }
    }
  }
}

.heatmap-legend {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #ebeef5;

  .legend-label {
    font-size: 12px;
    color: #606266;
  }

  .legend-gradient {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;

    .gradient-bar {
      flex: 1;
      height: 12px;
      background: linear-gradient(
        to right,
        rgba(144, 147, 153, 0.5),
        rgba(245, 108, 108, 0.6),
        rgba(230, 162, 60, 0.7),
        rgba(64, 158, 255, 0.7),
        rgba(103, 194, 58, 0.8)
      );
      border-radius: 6px;
    }

    .gradient-0,
    .gradient-50,
    .gradient-100 {
      font-size: 11px;
      color: #909399;
    }
  }
}
</style>
