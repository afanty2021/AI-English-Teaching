<!--
  教案导出页面
  支持单个和批量导出教案，提供丰富的导出选项
-->
<template>
  <div class="lesson-export-page">
    <el-container>
      <!-- 顶部 -->
      <el-header height="auto">
        <div class="page-header">
          <div class="header-left">
            <h1>教案导出</h1>
            <p class="page-description">选择教案并配置导出选项，批量生成文档</p>
          </div>
          <div class="header-actions">
            <el-button @click="goBack">
              <el-icon><ArrowLeft /></el-icon>
              返回
            </el-button>
          </div>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-main>
        <el-row :gutter="20">
          <!-- 左侧：教案选择和导出选项 -->
          <el-col :span="16">
            <!-- 选择教案 -->
            <el-card class="selection-card" shadow="never">
              <template #header>
                <div class="card-header">
                  <span>选择要导出的教案</span>
                  <el-button
                    text
                    type="primary"
                    @click="openLessonSelector"
                  >
                    <el-icon><Plus /></el-icon>
                    添加教案
                  </el-button>
                </div>
              </template>

              <!-- 已选教案列表 -->
              <div v-if="selectedLessons.length > 0" class="selected-lessons">
                <el-space wrap>
                  <el-tag
                    v-for="lesson in selectedLessons"
                    :key="lesson.id"
                    closable
                    size="large"
                    @close="removeLesson(lesson.id)"
                  >
                    <div class="lesson-tag">
                      <span class="lesson-name">{{ lesson.title }}</span>
                      <span class="lesson-meta">{{ lesson.level }} · {{ lesson.duration }}分钟</span>
                    </div>
                  </el-tag>
                </el-space>
              </div>

              <el-empty
                v-else
                description="暂未选择教案"
                :image-size="80"
              >
                <el-button type="primary" @click="openLessonSelector">
                  选择教案
                </el-button>
              </el-empty>
            </el-card>

            <!-- 导出选项配置 -->
            <el-card v-if="selectedLessons.length > 0" class="options-card" shadow="never">
              <template #header>
                <span>导出配置</span>
              </template>

              <ExportOptionsPanel v-model="exportOptions" />
            </el-card>

            <!-- 导出操作 -->
            <div v-if="selectedLessons.length > 0" class="export-actions">
              <el-space>
                <el-button
                  type="primary"
                  size="large"
                  :disabled="isExporting"
                  @click="handleExport"
                >
                  <el-icon><Download /></el-icon>
                  开始导出 ({{ selectedLessons.length }} 个教案)
                </el-button>
                <el-button
                  size="large"
                  :disabled="isExporting"
                  @click="handleClear"
                >
                  清空选择
                </el-button>
              </el-space>
            </div>
          </el-col>

          <!-- 右侧：导出任务状态 -->
          <el-col :span="8">
            <el-card class="tasks-card" shadow="never">
              <template #header>
                <div class="card-header">
                  <span>导出任务</span>
                  <el-badge :value="pendingTaskCount" :hidden="pendingTaskCount === 0">
                    <el-button
                      text
                      @click="refreshTasks"
                    >
                      <el-icon><Refresh /></el-icon>
                    </el-button>
                  </el-badge>
                </div>
              </template>

              <!-- 任务统计 -->
              <div v-if="tasks.length > 0" class="task-stats">
                <el-row :gutter="8">
                  <el-col :span="6">
                    <div class="stat-item">
                      <div class="stat-value">{{ getStatusCount('processing') }}</div>
                      <div class="stat-label">处理中</div>
                    </div>
                  </el-col>
                  <el-col :span="6">
                    <div class="stat-item">
                      <div class="stat-value success">{{ getStatusCount('completed') }}</div>
                      <div class="stat-label">已完成</div>
                    </div>
                  </el-col>
                  <el-col :span="6">
                    <div class="stat-item">
                      <div class="stat-value info">{{ getStatusCount('failed') }}</div>
                      <div class="stat-label">失败</div>
                    </div>
                  </el-col>
                  <el-col :span="6">
                    <div class="stat-item">
                      <div class="stat-value">{{ getStatusCount('pending') }}</div>
                      <div class="stat-label">等待中</div>
                    </div>
                  </el-col>
                </el-row>
              </div>

              <!-- 任务列表 -->
              <ExportTaskList
                :tasks="tasks"
                @download="handleDownload"
                @cancel="handleCancelTask"
                @retry="handleRetryTask"
                @delete="handleDeleteTask"
              />
            </el-card>
          </el-col>
        </el-row>
      </el-main>
    </el-container>

    <!-- 教案选择对话框 -->
    <el-dialog
      v-model="showSelectorDialog"
      title="选择教案"
      width="70%"
    >
      <LessonSelector
        v-if="showSelectorDialog"
        :exclude="selectedLessons.map(l => l.id)"
        @confirm="handleLessonsSelected"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowLeft,
  Plus,
  Download,
  Refresh
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getExportTasks,
  createExportTask,
  createBatchExportTasks,
  cancelExportTask,
  deleteExportTask,
  downloadExportFile,
  DEFAULT_EXPORT_OPTIONS
} from '@/api/lessonExport'
import ExportOptionsPanel from '@/components/ExportOptionsPanel.vue'
import ExportTaskList from '@/components/ExportTaskList.vue'
import LessonSelector from './LessonExportView/LessonSelector.vue'
import type { ExportTask, ExportOptions } from '@/types/lessonExport'
import type { LessonPlan } from '@/types/lesson'

const router = useRouter()

// 状态
const selectedLessons = ref<LessonPlan[]>([])
const exportOptions = ref<ExportOptions>({ ...DEFAULT_EXPORT_OPTIONS })
const tasks = ref<ExportTask[]>([])
const isExporting = ref(false)
const showSelectorDialog = ref(false)

// 轮询定时器
let pollingTimer: ReturnType<typeof setInterval> | null = null

// 计算属性
const pendingTaskCount = computed(() => {
  return tasks.value.filter(t =>
    t.status === 'pending' || t.status === 'processing'
  ).length
})

// 方法
const goBack = () => {
  router.back()
}

const openLessonSelector = () => {
  showSelectorDialog.value = true
}

const handleLessonsSelected = (lessons: LessonPlan[]) => {
  selectedLessons.value = [...selectedLessons.value, ...lessons]
  showSelectorDialog.value = false
}

const removeLesson = (lessonId: string) => {
  selectedLessons.value = selectedLessons.value.filter(l => l.id !== lessonId)
}

const handleClear = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有已选教案吗？', '确认', {
      type: 'warning'
    })
    selectedLessons.value = []
  } catch {
    // 用户取消
  }
}

// 执行导出
const handleExport = async () => {
  if (selectedLessons.value.length === 0) {
    ElMessage.warning('请先选择要导出的教案')
    return
  }

  isExporting.value = true
  try {
    const lessonIds = selectedLessons.value.map(l => l.id)

    if (lessonIds.length === 1) {
      // 单个导出
      const lessonId = lessonIds[0]
      if (!lessonId) {
        throw new Error('未选择教案')
      }
      const response = await createExportTask({
        lesson_id: lessonId,
        format: exportOptions.value.format,
        options: exportOptions.value
      })
      tasks.value.unshift(response.task)
    } else {
      // 批量导出
      const response = await createBatchExportTasks({
        lesson_ids: lessonIds,
        format: exportOptions.value.format,
        options: exportOptions.value
      })
      tasks.value = [...response.tasks, ...tasks.value]
    }

    ElMessage.success(`已创建 ${lessonIds.length} 个导出任务`)
    selectedLessons.value = []
  } catch (error) {
    console.error('创建导出任务失败:', error)
    ElMessage.error('创建导出任务失败')
  } finally {
    isExporting.value = false
  }
}

// 刷新任务列表
const refreshTasks = async () => {
  try {
    const response = await getExportTasks()
    tasks.value = response.tasks
  } catch (error) {
    console.error('刷新任务列表失败:', error)
  }
}

// 获取状态统计
const getStatusCount = (status: string) => {
  return tasks.value.filter(t => t.status === status).length
}

// 下载文件
const handleDownload = async (task: ExportTask) => {
  try {
    await downloadExportFile(task)
    ElMessage.success('下载成功')
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败')
  }
}

// 取消任务
const handleCancelTask = async (task: ExportTask) => {
  try {
    await cancelExportTask(task.id)
    // 更新本地状态
    const index = tasks.value.findIndex(t => t.id === task.id)
    if (index !== -1) {
      tasks.value.splice(index, 1)
    }
    ElMessage.success('任务已取消')
  } catch (error) {
    console.error('取消任务失败:', error)
    ElMessage.error('取消任务失败')
  }
}

// 重试任务
const handleRetryTask = async (task: ExportTask) => {
  try {
    const response = await createExportTask({
      lesson_id: task.lesson_id,
      format: task.format,
      options: task.options
    })
    // 移除旧任务，添加新任务
    const index = tasks.value.findIndex(t => t.id === task.id)
    if (index !== -1) {
      tasks.value.splice(index, 1)
    }
    tasks.value.unshift(response.task)
    ElMessage.success('已重新创建导出任务')
  } catch (error) {
    console.error('重试失败:', error)
    ElMessage.error('重试失败')
  }
}

// 删除任务
const handleDeleteTask = async (task: ExportTask) => {
  try {
    await deleteExportTask(task.id)
    const index = tasks.value.findIndex(t => t.id === task.id)
    if (index !== -1) {
      tasks.value.splice(index, 1)
    }
    ElMessage.success('任务已删除')
  } catch (error) {
    console.error('删除任务失败:', error)
    ElMessage.error('删除任务失败')
  }
}

// 开始轮询任务状态
const startPolling = () => {
  pollingTimer = setInterval(async () => {
    if (pendingTaskCount.value > 0) {
      await refreshTasks()
    }
  }, 2000)
}

// 停止轮询
const stopPolling = () => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
}

// 生命周期
onMounted(() => {
  refreshTasks()
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.lesson-export-page {
  min-height: 100vh;
  background: #f5f7fa;
}

.el-header {
  background: #fff;
  padding: 20px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.header-left h1 {
  margin: 0 0 4px 0;
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.page-description {
  margin: 0;
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.el-main {
  padding: 20px;
}

/* 卡片样式 */
.selection-card,
.options-card,
.tasks-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

/* 已选教案 */
.selected-lessons {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.lesson-tag {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.lesson-name {
  font-weight: 600;
}

.lesson-meta {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

/* 导出操作 */
.export-actions {
  padding: 20px 0;
  text-align: center;
}

/* 任务统计 */
.task-stats {
  margin-bottom: 16px;
  padding: 12px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.stat-value.success {
  color: var(--el-color-success);
}

.stat-value.info {
  color: var(--el-color-info);
}

.stat-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

/* 响应式 */
@media (max-width: 1200px) {
  .el-col {
    margin-bottom: 20px;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 12px;
  }

  .export-actions .el-space {
    flex-direction: column;
    width: 100%;
  }

  .export-actions .el-button {
    width: 100%;
  }
}
</style>
