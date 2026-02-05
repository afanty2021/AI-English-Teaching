<template>
  <div class="question-bank-list">
    <el-page-header @back="$router.back()">
      <template #content>
        <h2>题库管理</h2>
      </template>
      <template #extra>
        <el-button type="primary" :icon="Plus" @click="handleCreate">
          新建题库
        </el-button>
      </template>
    </el-page-header>

    <!-- 筛选栏 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="练习类型">
          <el-select v-model="filters.practice_type" placeholder="全部" clearable @change="loadBanks">
            <el-option label="阅读" value="reading" />
            <el-option label="听力" value="listening" />
            <el-option label="语法" value="grammar" />
            <el-option label="词汇" value="vocabulary" />
            <el-option label="写作" value="writing" />
            <el-option label="口语" value="speaking" />
          </el-select>
        </el-form-item>
        <el-form-item label="仅显示我的">
          <el-switch v-model="filters.onlyMine" @change="loadBanks" />
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 题库列表 -->
    <el-card v-loading="loading" class="bank-list">
      <el-empty v-if="!banks.length && !loading" description="暂无题库，点击"新建题库"开始创建" />

      <el-table v-else :data="banks" stripe @row-click="handleView">
        <el-table-column prop="name" label="题库名称" min-width="200" />
        <el-table-column prop="practice_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="getTypeTagType(row.practice_type)">
              {{ getTypeLabel(row.practice_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="difficulty_level" label="难度" width="80">
          <template #default="{ row }">
            {{ row.difficulty_level || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="question_count" label="题目数" width="80" align="center" />
        <el-table-column prop="is_public" label="公开" width="70" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_public ? 'success' : 'info'" size="small">
              {{ row.is_public ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="handleView(row)">查看</el-button>
            <el-button link type="primary" @click.stop="handleEdit(row)">编辑</el-button>
            <el-button link type="danger" @click.stop="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div v-if="total > 0" class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadBanks"
          @current-change="loadBanks"
        />
      </div>
    </el-card>

    <!-- 新建/编辑题库对话框 -->
    <el-dialog
      v-model="showEditDialog"
      :title="editMode ? '编辑题库' : '新建题库'"
      width="600px"
    >
      <el-form :model="bankForm" :rules="bankRules" ref="bankFormRef" label-width="100px">
        <el-form-item label="题库名称" prop="name">
          <el-input v-model="bankForm.name" placeholder="请输入题库名称" />
        </el-form-item>
        <el-form-item label="练习类型" prop="practice_type">
          <el-select v-model="bankForm.practice_type" placeholder="请选择练习类型" style="width: 100%">
            <el-option label="阅读" value="reading" />
            <el-option label="听力" value="listening" />
            <el-option label="语法" value="grammar" />
            <el-option label="词汇" value="vocabulary" />
            <el-option label="写作" value="writing" />
            <el-option label="口语" value="speaking" />
          </el-select>
        </el-form-item>
        <el-form-item label="难度等级" prop="difficulty_level">
          <el-select v-model="bankForm.difficulty_level" placeholder="请选择难度" clearable style="width: 100%">
            <el-option label="A1" value="A1" />
            <el-option label="A2" value="A2" />
            <el-option label="B1" value="B1" />
            <el-option label="B2" value="B2" />
            <el-option label="C1" value="C1" />
            <el-option label="C2" value="C2" />
          </el-select>
        </el-form-item>
        <el-form-item label="题库描述">
          <el-input
            v-model="bankForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入题库描述"
          />
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="tagsInput" placeholder="输入标签后按回车添加" @keyup.enter="handleAddTag" />
          <div class="tags-list">
            <el-tag
              v-for="(tag, index) in bankForm.tags"
              :key="index"
              closable
              @close="handleRemoveTag(index)"
            >
              {{ tag }}
            </el-tag>
          </div>
        </el-form-item>
        <el-form-item label="是否公开">
          <el-switch v-model="bankForm.is_public" />
          <span class="form-tip">公开题库对所有学生可见</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitBank" :loading="submitting">
          {{ editMode ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { questionBankApi } from '@/api/questionBank'
import type { QuestionBank } from '@/types/question'

const router = useRouter()

const loading = ref(false)
const submitting = ref(false)
const banks = ref<QuestionBank[]>([])
const total = ref(0)

const filters = reactive({
  practice_type: '',
  onlyMine: false
})

const pagination = reactive({
  page: 1,
  size: 20
})

const showEditDialog = ref(false)
const editMode = ref(false)
const editingId = ref<string | null>(null)
const bankFormRef = ref<FormInstance>()
const tagsInput = ref('')

const bankForm = reactive({
  name: '',
  practice_type: '',
  difficulty_level: '',
  description: '',
  tags: [] as string[],
  is_public: false
})

const bankRules: FormRules = {
  name: [{ required: true, message: '请输入题库名称', trigger: 'blur' }],
  practice_type: [{ required: true, message: '请选择练习类型', trigger: 'change' }]
}

// 获取类型标签类型
const getTypeTagType = (type: string) => {
  const typeMap: Record<string, any> = {
    reading: 'success',
    listening: 'warning',
    grammar: 'info',
    vocabulary: 'primary',
    writing: 'danger',
    speaking: 'success'
  }
  return typeMap[type] || 'info'
}

// 获取类型标签
const getTypeLabel = (type: string) => {
  const labelMap: Record<string, string> = {
    reading: '阅读',
    listening: '听力',
    grammar: '语法',
    vocabulary: '词汇',
    writing: '写作',
    speaking: '口语'
  }
  return labelMap[type] || type
}

// 格式化日期
const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

// 加载题库列表
const loadBanks = async () => {
  loading.value = true
  try {
    const response = await questionBankApi.list({
      ...filters,
      skip: (pagination.page - 1) * pagination.size,
      limit: pagination.size
    })
    banks.value = response.items
    total.value = response.total
  } catch (error) {
    ElMessage.error('加载题库失败')
  } finally {
    loading.value = false
  }
}

// 新建题库
const handleCreate = () => {
  editMode.value = false
  editingId.value = null
  Object.assign(bankForm, {
    name: '',
    practice_type: '',
    difficulty_level: '',
    description: '',
    tags: [],
    is_public: false
  })
  showEditDialog.value = true
}

// 编辑题库
const handleEdit = (bank: QuestionBank) => {
  editMode.value = true
  editingId.value = bank.id
  Object.assign(bankForm, {
    name: bank.name,
    practice_type: bank.practice_type,
    difficulty_level: bank.difficulty_level || '',
    description: bank.description || '',
    tags: bank.tags || [],
    is_public: bank.is_public
  })
  showEditDialog.value = true
}

// 查看题库
const handleView = (bank: QuestionBank) => {
  router.push({
    name: 'question-bank-detail',
    params: { bankId: bank.id }
  })
}

// 删除题库
const handleDelete = async (bank: QuestionBank) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除题库"${bank.name}"吗？删除后将无法恢复。`,
      '删除确认',
      { type: 'warning' }
    )

    await questionBankApi.delete(bank.id)
    ElMessage.success('删除成功')
    loadBanks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 添加标签
const handleAddTag = () => {
  const tag = tagsInput.value.trim()
  if (tag && !bankForm.tags.includes(tag)) {
    bankForm.tags.push(tag)
  }
  tagsInput.value = ''
}

// 移除标签
const handleRemoveTag = (index: number) => {
  bankForm.tags.splice(index, 1)
}

// 提交题库表单
const handleSubmitBank = async () => {
  const valid = await bankFormRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    if (editMode.value && editingId.value) {
      await questionBankApi.update(editingId.value, bankForm)
      ElMessage.success('更新成功')
    } else {
      await questionBankApi.create(bankForm)
      ElMessage.success('创建成功')
    }
    showEditDialog.value = false
    loadBanks()
  } catch (error) {
    ElMessage.error(editMode.value ? '更新失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadBanks()
})
</script>

<style scoped>
.question-bank-list {
  padding: 20px;
}

.filter-card {
  margin-bottom: 20px;
}

.bank-list {
  min-height: 400px;
}

.bank-list .el-table {
  cursor: pointer;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.form-tip {
  margin-left: 12px;
  font-size: 13px;
  color: #909399;
}
</style>
