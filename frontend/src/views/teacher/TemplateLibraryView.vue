<!--
  教案模板库页面
  教师可以浏览、预览、应用和管理教案模板
-->
<template>
  <div class="template-library-page">
    <el-container>
      <!-- 顶部工具栏 -->
      <el-header height="auto">
        <div class="page-header">
          <div class="header-left">
            <h1>模板库</h1>
            <p class="page-description">
              使用预设模板快速创建教案，提高备课效率
            </p>
          </div>
          <div class="header-actions">
            <el-button
              type="primary"
              :icon="Plus"
              @click="showCreateDialog = true"
            >
              创建模板
            </el-button>
          </div>
        </div>

        <!-- 搜索和筛选栏 -->
        <div class="toolbar">
          <div class="search-section">
            <el-input
              v-model="searchQuery"
              placeholder="搜索模板..."
              :prefix-icon="Search"
              clearable
              style="width: 280px"
              @input="handleSearch"
            />
          </div>

          <div class="filter-section">
            <el-space wrap>
              <el-select
                v-model="filterLevel"
                placeholder="级别"
                clearable
                style="width: 100px"
                @change="loadTemplates"
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

              <el-select
                v-model="filterCategory"
                placeholder="分类"
                clearable
                style="width: 120px"
                @change="loadTemplates"
              >
                <el-option
                  v-for="cat in categories"
                  :key="cat.key"
                  :label="cat.label"
                  :value="cat.key"
                />
              </el-select>

              <el-select
                v-model="sortBy"
                style="width: 120px"
                @change="loadTemplates"
              >
                <el-option
                  label="最新"
                  value="created_at"
                />
                <el-option
                  label="最热"
                  value="usage_count"
                />
                <el-option
                  label="评分"
                  value="rating"
                />
                <el-option
                  label="名称"
                  value="name"
                />
              </el-select>

              <el-radio-group
                v-model="viewMode"
                class="view-toggle"
              >
                <el-radio-button value="grid">
                  <el-icon><Grid /></el-icon>
                </el-radio-button>
                <el-radio-button value="list">
                  <el-icon><List /></el-icon>
                </el-radio-button>
              </el-radio-group>
            </el-space>
          </div>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-main>
        <el-card v-loading="isLoading">
          <!-- 空状态 -->
          <el-empty
            v-if="!isLoading && filteredTemplates.length === 0"
            description="暂无模板"
          >
            <el-button
              type="primary"
              @click="showCreateDialog = true"
            >
              创建第一个模板
            </el-button>
          </el-empty>

          <!-- 网格视图 -->
          <div
            v-else-if="viewMode === 'grid'"
            class="templates-grid"
          >
            <TemplateCard
              v-for="template in filteredTemplates"
              :key="template.id"
              :template="template"
              :is-favorited="favoritedTemplates.has(template.id)"
              @click="handleViewTemplate(template.id)"
              @apply="handleApplyTemplate(template)"
              @preview="handlePreviewTemplate(template)"
              @edit="handleEditTemplate(template)"
              @duplicate="handleDuplicateTemplate(template)"
              @favorite="handleToggleFavorite(template)"
              @delete="handleDeleteTemplate(template)"
            />
          </div>

          <!-- 列表视图 -->
          <el-table
            v-else
            :data="filteredTemplates"
            stripe
            @row-click="handleViewTemplate"
          >
            <el-table-column
              prop="name"
              label="名称"
              min-width="200"
            />
            <el-table-column
              prop="category_label"
              label="分类"
              width="120"
            />
            <el-table-column
              label="级别"
              width="80"
            >
              <template #default="{ row }">
                <el-tag
                  size="small"
                  :type="getLevelType(row.level)"
                >
                  {{ row.level }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column
              prop="duration"
              label="时长"
              width="80"
            >
              <template #default="{ row }">
                {{ row.duration }} 分钟
              </template>
            </el-table-column>
            <el-table-column
              prop="usage_count"
              label="使用次数"
              width="90"
              align="center"
            />
            <el-table-column
              label="评分"
              width="90"
              align="center"
            >
              <template #default="{ row }">
                <span v-if="row.rating > 0">
                  <el-icon><StarFilled /></el-icon>
                  {{ row.rating.toFixed(1) }}
                </span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column
              label="操作"
              width="220"
              fixed="right"
            >
              <template #default="{ row }">
                <el-button
                  link
                  type="primary"
                  :icon="Plus"
                  @click.stop="handleApplyTemplate(row)"
                >
                  应用
                </el-button>
                <el-button
                  link
                  @click.stop="handlePreviewTemplate(row)"
                >
                  预览
                </el-button>
                <el-dropdown @click.stop>
                  <el-button link>
                    更多
                    <el-icon><ArrowDown /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item @click="handleEditTemplate(row)">
                        编辑
                      </el-dropdown-item>
                      <el-dropdown-item @click="handleDuplicateTemplate(row)">
                        复制
                      </el-dropdown-item>
                      <el-dropdown-item
                        @click="handleToggleFavorite(row)"
                      >
                        {{ favoritedTemplates.has(row.id) ? '取消收藏' : '收藏' }}
                      </el-dropdown-item>
                      <el-dropdown-item
                        divided
                        @click="handleDeleteTemplate(row)"
                      >
                        删除
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </template>
            </el-table-column>
          </el-table>

          <!-- 分页 -->
          <div
            v-if="total > pageSize"
            class="pagination"
          >
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :total="total"
              :page-sizes="[12, 24, 48, 96]"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="loadTemplates"
              @current-change="loadTemplates"
            />
          </div>
        </el-card>
      </el-main>
    </el-container>

    <!-- 预览抽屉 -->
    <TemplatePreviewDrawer
      v-model="showPreviewDrawer"
      :template-id="previewTemplateId"
      @apply="handleApplyFromPreview"
    />

    <!-- 创建/编辑对话框 -->
    <TemplateEditorDialog
      v-model="showCreateDialog"
      :template="editingTemplate"
      @saved="handleTemplateSaved"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Search,
  Plus,
  Grid,
  List,
  ArrowDown,
  StarFilled
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getTemplates,
  // getTemplate reserved for future template detail viewing
  // getTemplate,
  deleteTemplate,
  duplicateTemplate,
  toggleFavoriteTemplate,
  applyTemplate
} from '@/api/lessonTemplate'
import type { TemplateListItem, TemplateQueryParams, CEFRLevel } from '@/types/lessonTemplate'
import TemplateCard from '@/components/TemplateCard.vue'
import TemplatePreviewDrawer from './TemplateLibraryView/TemplatePreviewDrawer.vue'
import TemplateEditorDialog from './TemplateLibraryView/TemplateEditorDialog.vue'

const router = useRouter()

// 状态
const isLoading = ref(true)
const templates = ref<TemplateListItem[]>([])
const categories = ref<Array<{ key: string; label: string }>>([])
const favoritedTemplates = ref<Set<string>>(new Set())

// 搜索和筛选
const searchQuery = ref('')
const filterLevel = ref('')
const filterCategory = ref('')
const sortBy = ref('created_at')
const viewMode = ref<'grid' | 'list'>('grid')

// 分页
const currentPage = ref(1)
const pageSize = ref(24)
const total = ref(0)

// 对话框状态
const showPreviewDrawer = ref(false)
const previewTemplateId = ref('')
const showCreateDialog = ref(false)
const editingTemplate = ref<TemplateListItem | null>(null)

// 计算属性
const filteredTemplates = computed(() => {
  let result = templates.value

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(t =>
      t.name.toLowerCase().includes(query) ||
      t.description.toLowerCase().includes(query)
    )
  }

  return result
})

// 方法
const loadTemplates = async () => {
  isLoading.value = true
  try {
    const params: TemplateQueryParams = {
      page: currentPage.value,
      page_size: pageSize.value,
      level: (filterLevel.value || undefined) as CEFRLevel | undefined,
      category: filterCategory.value || undefined,
      search: searchQuery.value || undefined,
      sort_by: sortBy.value as any,
      sort_order: sortBy.value === 'name' ? 'asc' : 'desc'
    }

    const response = await getTemplates(params)
    templates.value = response.items
    total.value = response.total
  } catch (error) {
    console.error('加载模板失败:', error)
    ElMessage.error('加载模板失败')
  } finally {
    isLoading.value = false
  }
}

const loadCategories = async () => {
  try {
    // TODO: 从后端获取分类
    categories.value = [
      { key: 'speaking', label: '口语课' },
      { key: 'listening', label: '听力课' },
      { key: 'reading', label: '阅读课' },
      { key: 'writing', label: '写作课' },
      { key: 'grammar', label: '语法课' },
      { key: 'vocabulary', label: '词汇课' },
      { key: 'comprehensive', label: '综合课' }
    ]
  } catch (error) {
    console.error('加载分类失败:', error)
  }
}

const handleSearch = () => {
  // 搜索逻辑已在 computed 中处理
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

// 查看模板详情
const handleViewTemplate = async (templateId: string) => {
  previewTemplateId.value = templateId
  showPreviewDrawer.value = true
}

// 预览模板
const handlePreviewTemplate = (template: TemplateListItem) => {
  previewTemplateId.value = template.id
  showPreviewDrawer.value = true
}

// 应用模板
const handleApplyTemplate = async (template: TemplateListItem) => {
  try {
    const response = await applyTemplate(template.id, {
      title: `${template.name} - 副本`
    })
    ElMessage.success('模板已应用，正在跳转到教案编辑...')
    router.push(`/teacher/lessons/${response.lesson_plan_id}`)
  } catch (error) {
    console.error('应用模板失败:', error)
    ElMessage.error('应用模板失败')
  }
}

const handleApplyFromPreview = async (templateId: string) => {
  try {
    const response = await applyTemplate(templateId)
    ElMessage.success('模板已应用，正在跳转到教案编辑...')
    router.push(`/teacher/lessons/${response.lesson_plan_id}`)
  } catch (error) {
    console.error('应用模板失败:', error)
    ElMessage.error('应用模板失败')
  }
}

// 编辑模板
const handleEditTemplate = (template: TemplateListItem) => {
  editingTemplate.value = template
  showCreateDialog.value = true
}

// 复制模板
const handleDuplicateTemplate = async (template: TemplateListItem) => {
  try {
    await ElMessageBox.confirm('确定要复制此模板吗？', '确认', {
      type: 'warning'
    })
    await duplicateTemplate(template.id)
    ElMessage.success('模板复制成功')
    await loadTemplates()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('复制模板失败:', error)
      ElMessage.error('复制模板失败')
    }
  }
}

// 收藏/取消收藏
const handleToggleFavorite = async (template: TemplateListItem) => {
  try {
    const response = await toggleFavoriteTemplate(template.id)
    if (response.favorited) {
      favoritedTemplates.value.add(template.id)
      ElMessage.success('已收藏')
    } else {
      favoritedTemplates.value.delete(template.id)
      ElMessage.info('已取消收藏')
    }
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error('操作失败')
  }
}

// 删除模板
const handleDeleteTemplate = async (template: TemplateListItem) => {
  try {
    await ElMessageBox.confirm('确定要删除此模板吗？删除后无法恢复。', '警告', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消'
    })

    await deleteTemplate(template.id)
    ElMessage.success('模板已删除')
    await loadTemplates()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除模板失败:', error)
      ElMessage.error('删除模板失败')
    }
  }
}

// 模板保存成功回调
const handleTemplateSaved = async () => {
  showCreateDialog.value = false
  editingTemplate.value = null
  await loadTemplates()
}

// 生命周期
onMounted(() => {
  loadCategories()
  loadTemplates()
})
</script>

<style scoped>
.template-library-page {
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
  margin-bottom: 20px;
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

.toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.search-section {
  flex: 1;
  min-width: 280px;
}

.filter-section {
  display: flex;
  align-items: center;
  gap: 8px;
}

.view-toggle :deep(.el-radio-button__inner) {
  padding: 8px 12px;
}

.el-main {
  padding: 20px;
}

/* 网格视图 */
.templates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

/* 列表视图 */
.el-table {
  cursor: pointer;
}

.el-table :deep(.el-table__row):hover {
  background-color: var(--el-fill-color-light);
}

/* 分页 */
.pagination {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

/* 响应式 */
@media (max-width: 1024px) {
  .templates-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 12px;
  }

  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .search-section,
  .filter-section {
    width: 100%;
  }

  .filter-section .el-space {
    width: 100%;
    flex-wrap: wrap;
  }

  .templates-grid {
    grid-template-columns: 1fr;
  }
}
</style>
