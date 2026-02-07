<!--
  教案选择器组件
  用于在导出页面选择要导出的教案
-->
<template>
  <div class="lesson-selector">
    <!-- 搜索和筛选 -->
    <div class="selector-toolbar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索教案..."
        :prefix-icon="Search"
        clearable
        style="width: 280px"
        @input="handleSearch"
      />
      <el-select
        v-model="filterLevel"
        placeholder="筛选难度"
        clearable
        style="width: 120px"
        @change="loadLessons"
      >
        <el-option
          label="A1"
          value="A1"
        />
        <el-option
          label="A2"
          value="A2"
        />
        <el-option
          label="B1"
          value="B1"
        />
        <el-option
          label="B2"
          value="B2"
        />
        <el-option
          label="C1"
          value="C1"
        />
        <el-option
          label="C2"
          value="C2"
        />
      </el-select>
    </div>

    <!-- 教案列表 -->
    <div
      v-loading="isLoading"
      class="lessons-list"
    >
      <el-empty
        v-if="!isLoading && filteredLessons.length === 0"
        description="暂无教案"
      />

      <div
        v-else
        class="lessons-grid"
      >
        <div
          v-for="lesson in filteredLessons"
          :key="lesson.id"
          class="lesson-select-item"
          :class="{ 'is-selected': isSelected(lesson.id) }"
          @click="toggleLesson(lesson)"
        >
          <div class="lesson-checkbox">
            <el-checkbox
              :model-value="isSelected(lesson.id)"
              @change="toggleLesson(lesson)"
            />
          </div>

          <div class="lesson-content">
            <h4 class="lesson-title">
              {{ lesson.title }}
            </h4>
            <p class="lesson-topic">
              {{ lesson.topic || '未设置主题' }}
            </p>
            <div class="lesson-meta">
              <el-tag
                size="small"
                :type="getLevelType(lesson.level)"
              >
                {{ lesson.level }}
              </el-tag>
              <span class="lesson-duration">{{ lesson.duration }} 分钟</span>
              <span class="lesson-date">{{ formatDate(lesson.created_at) }}</span>
            </div>
          </div>

          <div class="lesson-status">
            <el-icon
              v-if="isSelected(lesson.id)"
              :size="20"
              color="#409eff"
            >
              <CircleCheck />
            </el-icon>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div
        v-if="total > pageSize"
        class="pagination"
      >
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[12, 24, 48]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadLessons"
          @current-change="loadLessons"
        />
      </div>
    </div>

    <!-- 底部操作 -->
    <div class="selector-footer">
      <el-space>
        <span class="selection-count">
          已选择 {{ selectedCount }} 个教案
        </span>
        <el-button @click="handleCancel">
          取消
        </el-button>
        <el-button
          type="primary"
          :disabled="selectedCount === 0"
          @click="handleConfirm"
        >
          确认选择
        </el-button>
      </el-space>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Search, CircleCheck } from '@element-plus/icons-vue'
import { getLessonPlans } from '@/api/lesson'
import type { LessonPlan } from '@/types/lesson'

interface Props {
  /** 要排除的教案ID列表（已选的） */
  exclude?: string[]
}

interface Emits {
  /** 确认选择 */
  confirm: [lessons: LessonPlan[]]
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 状态
const isLoading = ref(false)
const lessons = ref<LessonPlan[]>([])
const searchQuery = ref('')
const filterLevel = ref('')
const currentPage = ref(1)
const pageSize = ref(24)
const total = ref(0)
const selectedIds = ref<Set<string>>(new Set())

// 计算属性
const filteredLessons = computed(() => {
  let result = lessons.value

  // 排除已选择的
  if (props.exclude && props.exclude.length > 0) {
    result = result.filter(l => !props.exclude?.includes(l.id))
  }

  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(l =>
      l.title.toLowerCase().includes(query) ||
      l.topic?.toLowerCase().includes(query)
    )
  }

  // 级别过滤
  if (filterLevel.value) {
    result = result.filter(l => l.level === filterLevel.value)
  }

  return result
})

const selectedCount = computed(() => selectedIds.value.size)

// 方法
const loadLessons = async () => {
  isLoading.value = true
  try {
    const response = await getLessonPlans({
      page: currentPage.value,
      page_size: pageSize.value,
      level: filterLevel.value || undefined
    })

    // Cast LessonPlanSummary[] to LessonPlan[] with proper status type assertion
    lessons.value = response.lesson_plans.map(plan => ({
      ...plan,
      status: plan.status as 'completed' | 'draft' | 'archived'
    }))
    total.value = response.total
  } catch (error) {
    console.error('加载教案失败:', error)
  } finally {
    isLoading.value = false
  }
}

const handleSearch = () => {
  // 搜索逻辑已在 computed 中处理
}

const isSelected = (id: string) => {
  return selectedIds.value.has(id)
}

const toggleLesson = (lesson: LessonPlan) => {
  if (selectedIds.value.has(lesson.id)) {
    selectedIds.value.delete(lesson.id)
  } else {
    selectedIds.value.add(lesson.id)
  }
}

const getLevelType = (level: string) => {
  const types: Record<string, any> = {
    A1: 'danger',
    A2: 'warning',
    B1: 'primary',
    B2: 'success',
    C1: 'info',
    C2: ''
  }
  return types[level] || 'info'
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

const handleCancel = () => {
  // 触发父组件关闭对话框
  emit('confirm', [])
}

const handleConfirm = () => {
  const selectedLessons = lessons.value.filter(l => selectedIds.value.has(l.id))
  emit('confirm', selectedLessons)
}

// 初始化
loadLessons()
</script>

<style scoped>
.lesson-selector {
  display: flex;
  flex-direction: column;
  min-height: 500px;
}

/* 工具栏 */
.selector-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

/* 教案列表 */
.lessons-list {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.lessons-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.lesson-select-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: var(--el-fill-color-blank);
  border: 2px solid var(--el-border-color-lighter);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.lesson-select-item:hover {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}

.lesson-select-item.is-selected {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}

.lesson-checkbox {
  padding-top: 2px;
}

.lesson-content {
  flex: 1;
  min-width: 0;
}

.lesson-title {
  margin: 0 0 4px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.lesson-topic {
  margin: 0 0 8px 0;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.lesson-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

/* 底部 */
.selector-footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.selection-count {
  font-size: 14px;
  color: var(--el-text-color-regular);
  margin-right: auto;
}

/* 响应式 */
@media (max-width: 768px) {
  .lessons-grid {
    grid-template-columns: 1fr;
  }

  .selector-footer .el-space {
    flex-direction: column-reverse;
    width: 100%;
  }

  .selector-footer .el-button {
    width: 100%;
  }

  .selection-count {
    margin-bottom: 8px;
  }
}
</style>
