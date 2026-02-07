<template>
  <el-dialog
    v-model="dialogVisible"
    title="模板管理"
    width="900px"
    :close-on-click-modal="false"
    @open="handleOpen"
  >
    <!-- 工具栏 -->
    <div class="toolbar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索模板名称"
        :prefix-icon="Search"
        style="width: 200px"
        clearable
        @input="handleSearch"
      />
      <el-select
        v-model="filterFormat"
        placeholder="全部格式"
        style="width: 120px"
        clearable
        @change="loadTemplates"
      >
        <el-option
          label="Word"
          value="word"
        />
        <el-option
          label="PDF"
          value="pdf"
        />
        <el-option
          label="PowerPoint"
          value="pptx"
        />
      </el-select>
      <el-select
        v-model="filterType"
        placeholder="全部类型"
        style="width: 120px"
        clearable
        @change="loadTemplates"
      >
        <el-option
          label="系统模板"
          value="system"
        />
        <el-option
          label="自定义"
          value="custom"
        />
      </el-select>
      <div class="toolbar-spacer" />
      <el-button
        type="primary"
        :icon="Plus"
        @click="handleCreate"
      >
        新建模板
      </el-button>
    </div>

    <!-- 模板表格 -->
    <el-table
      v-loading="loading"
      :data="templates"
      style="width: 100%"
      height="400"
    >
      <el-table-column
        prop="name"
        label="模板名称"
        min-width="150"
      />
      <el-table-column
        label="格式"
        width="100"
      >
        <template #default="{ row }">
          <el-tag
            :type="getFormatTagType(row.format)"
            size="small"
          >
            {{ getFormatLabel(row.format) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        label="类型"
        width="100"
      >
        <template #default="{ row }">
          <el-tag
            :type="row.type === 'system' ? 'info' : 'success'"
            size="small"
          >
            {{ row.type === 'system' ? '系统' : '自定义' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        prop="usage_count"
        label="使用次数"
        width="100"
        align="center"
      >
        <template #default="{ row }">
          <el-badge
            :value="row.usage_count"
            :max="99"
          />
        </template>
      </el-table-column>
      <el-table-column
        label="默认"
        width="80"
        align="center"
      >
        <template #default="{ row }">
          <el-tag
            v-if="row.is_default"
            type="warning"
            size="small"
          >
            默认
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        label="操作"
        width="280"
        fixed="right"
      >
        <template #default="{ row }">
          <el-button
            link
            type="primary"
            :icon="View"
            @click="handlePreview(row)"
          >
            预览
          </el-button>
          <el-button
            link
            type="primary"
            :icon="Edit"
            @click="handleEdit(row)"
          >
            编辑
          </el-button>
          <el-button
            v-if="!row.is_default"
            link
            type="warning"
            :icon="Star"
            @click="handleSetDefault(row)"
          >
            设为默认
          </el-button>
          <el-button
            v-if="row.type === 'custom'"
            link
            type="danger"
            :icon="Delete"
            @click="handleDelete(row)"
          >
            删除
          </el-button>
          <el-button
            v-if="row.type === 'system'"
            link
            :icon="DocumentCopy"
            @click="handleDuplicate(row)"
          >
            复制
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @size-change="loadTemplates"
        @current-change="loadTemplates"
      />
    </div>

    <template #footer>
      <el-button @click="dialogVisible = false">
        关闭
      </el-button>
    </template>

    <!-- 编辑器对话框 -->
    <TemplateEditorDialog
      v-model="editorVisible"
      :template="editingTemplate"
      @success="handleEditorSuccess"
    />
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, View, Edit, Delete, Star, DocumentCopy } from '@element-plus/icons-vue'
import TemplateEditorDialog from './TemplateEditorDialog.vue'
import {
  getTemplates,
  deleteTemplate,
  setDefaultTemplate,
  duplicateTemplate,
  previewTemplate,
  type ExportTemplate
} from '@/api/template'

// 浏览器全局变量类型声明

interface Props {
  modelValue: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'change'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const loading = ref(false)
const templates = ref<ExportTemplate[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchKeyword = ref('')
const filterFormat = ref<'word' | 'pdf' | 'pptx' | ''>('')
const filterType = ref<'system' | 'custom' | ''>('')

// 编辑器相关
const editorVisible = ref(false)
const editingTemplate = ref<ExportTemplate | null>(null)

// 获取格式标签类型
const getFormatTagType = (format: string) => {
  const types: Record<string, any> = {
    word: 'primary',
    pdf: 'success',
    pptx: 'warning'
  }
  return types[format] || 'info'
}

// 获取格式标签
const getFormatLabel = (format: string) => {
  const labels: Record<string, string> = {
    word: 'Word',
    pdf: 'PDF',
    pptx: 'PPTX'
  }
  return labels[format] || format
}

// 加载模板列表
const loadTemplates = async () => {
  loading.value = true
  try {
    const response = await getTemplates({
      format: filterFormat.value || undefined,
      type: filterType.value || undefined,
      search: searchKeyword.value || undefined,
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value
    })
    templates.value = response.templates
    total.value = response.total
  } catch (error: any) {
    console.error('加载模板列表失败:', error)
    ElMessage.error('加载模板列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索处理（防抖）
let searchTimer: number | null = null
const handleSearch = () => {
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
  searchTimer = window.setTimeout(() => {
    currentPage.value = 1
    loadTemplates()
  }, 300)
}

// 打开对话框时加载数据
const handleOpen = () => {
  loadTemplates()
}

// 创建模板
const handleCreate = () => {
  editingTemplate.value = null
  editorVisible.value = true
}

// 编辑模板
const handleEdit = (template: ExportTemplate) => {
  if (template.type === 'system') {
    ElMessage.warning('系统模板不可编辑，请先复制为自定义模板')
    return
  }
  editingTemplate.value = template
  editorVisible.value = true
}

// 预览模板
const handlePreview = async (template: ExportTemplate) => {
  try {
    const response = await previewTemplate(template.id)
    window.open(response.preview_url, '_blank')
  } catch (error: any) {
    console.error('预览失败:', error)
    ElMessage.error('预览失败')
  }
}

// 设置默认模板
const handleSetDefault = async (template: ExportTemplate) => {
  try {
    await setDefaultTemplate(template.id)
    ElMessage.success('已设置为默认模板')
    loadTemplates()
    emit('change')
  } catch (error: any) {
    console.error('设置默认模板失败:', error)
    ElMessage.error('设置默认模板失败')
  }
}

// 删除模板
const handleDelete = async (template: ExportTemplate) => {
  if (template.type === 'system') {
    ElMessage.warning('系统模板不可删除')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除模板"${template.name}"吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await deleteTemplate(template.id)
    ElMessage.success('模板已删除')
    loadTemplates()
    emit('change')
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除模板失败:', error)
      ElMessage.error('删除模板失败')
    }
  }
}

// 复制模板
const handleDuplicate = async (template: ExportTemplate) => {
  try {
    await duplicateTemplate(template.id)
    ElMessage.success('模板已复制')
    loadTemplates()
    emit('change')
  } catch (error: unknown) {
    console.error('复制模板失败:', error)
    ElMessage.error('复制模板失败')
  }
}

// 编辑器成功回调
const handleEditorSuccess = () => {
  loadTemplates()
  emit('change')
}
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.toolbar-spacer {
  flex: 1;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
