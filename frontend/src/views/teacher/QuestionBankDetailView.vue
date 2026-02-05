<template>
  <div class="question-bank-detail">
    <el-page-header @back="$router.back()">
      <template #content>
        <h2>{{ bank?.name || '题库详情' }}</h2>
      </template>
      <template #extra>
        <el-button :icon="Edit" @click="handleEditBank">编辑题库</el-button>
        <el-button type="primary" :icon="Plus" @click="showCreateQuestion = true">新建题目</el-button>
      </template>
    </el-page-header>

    <el-card v-loading="loading" class="bank-info">
      <el-empty v-if="!bank && !loading" description="题库不存在" />

      <el-descriptions v-else :column="3" border>
        <el-descriptions-item label="题库名称">{{ bank?.name }}</el-descriptions-item>
        <el-descriptions-item label="练习类型">
          <el-tag v-if="bank" :type="getTypeTagType(bank.practice_type)">
            {{ getTypeLabel(bank.practice_type) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="难度等级">{{ bank?.difficulty_level || '-' }}</el-descriptions-item>
        <el-descriptions-item label="题目数量">{{ bank?.question_count }}</el-descriptions-item>
        <el-descriptions-item label="是否公开">
          <el-tag v-if="bank" :type="bank.is_public ? 'success' : 'info'">
            {{ bank.is_public ? '公开' : '私有' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ bank ? formatDate(bank.created_at) : '' }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="3">
          {{ bank?.description || '暂无描述' }}
        </el-descriptions-item>
        <el-descriptions-item v-if="bank?.tags?.length" label="标签" :span="3">
          <el-tag v-for="tag in bank?.tags" :key="tag" style="margin-right: 8px">
            {{ tag }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 题目列表 -->
    <el-card v-loading="questionsLoading" class="questions-section">
      <template #header>
        <div class="section-header">
          <h3>题目列表 ({{ totalQuestions }})</h3>
          <el-button link :icon="Refresh" @click="loadQuestions">刷新</el-button>
        </div>
      </template>

      <el-empty v-if="!questions.length && !questionsLoading" description="暂无题目，点击&#34;添加题目&#34;开始创建" />

      <el-table v-else :data="questions" stripe>
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="content_text" label="题目内容" min-width="300">
          <template #default="{ row }">
            <div class="question-content">{{ row.content_text }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="question_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ getQuestionTypeLabel(row.question_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="difficulty_level" label="难度" width="80">
          <template #default="{ row }">
            {{ row.difficulty_level || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="order_index" label="排序" width="80" align="center" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEditQuestion(row)">编辑</el-button>
            <el-button link @click="handleViewQuestion(row)">查看</el-button>
            <el-button link type="danger" @click="handleRemoveQuestion(row)">移除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div v-if="totalQuestions > 0" class="pagination">
        <el-pagination
          v-model:current-page="questionPagination.page"
          v-model:page-size="questionPagination.size"
          :total="totalQuestions"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadQuestions"
          @current-change="loadQuestions"
        />
      </div>
    </el-card>

    <!-- 新建题目对话框 -->
    <QuestionEditor
      v-model="showCreateQuestion"
      :question-bank-id="bankId"
      @success="handleQuestionCreated"
    />

    <!-- 查看题目对话框 -->
    <el-dialog
      v-model="showViewDialog"
      title="题目详情"
      width="700px"
    >
      <QuestionRenderer
        v-if="viewingQuestion"
        :question="viewingQuestion"
        :show-meta="false"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Edit, Plus, Refresh } from '@element-plus/icons-vue'
import { questionBankApi } from '@/api/questionBank'
import QuestionRenderer from '@/components/question/QuestionRenderer.vue'
import QuestionEditor from '@/components/question/editor/QuestionEditor.vue'
import type { QuestionBank, Question } from '@/types/question'

const router = useRouter()
const route = useRoute()

const bankId = route.params.bankId as string

const loading = ref(false)
const questionsLoading = ref(false)

const bank = ref<QuestionBank | null>(null)
const questions = ref<Question[]>([])
const totalQuestions = ref(0)

const questionPagination = reactive({
  page: 1,
  size: 20
})

const showCreateQuestion = ref(false)
const showViewDialog = ref(false)
const viewingQuestion = ref<Question | null>(null)

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

// 获取题目类型标签
const getQuestionTypeLabel = (type: string) => {
  const labelMap: Record<string, string> = {
    choice: '选择题',
    fill_blank: '填空题',
    reading: '阅读理解',
    writing: '写作题',
    speaking: '口语题',
    listening: '听力题',
    translation: '翻译题'
  }
  return labelMap[type] || type
}

// 格式化日期
const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

// 加载题库详情
const loadBank = async () => {
  loading.value = true
  try {
    bank.value = await questionBankApi.getDetail(bankId)
  } catch (error) {
    ElMessage.error('加载题库失败')
  } finally {
    loading.value = false
  }
}

// 加载题目列表
const loadQuestions = async () => {
  questionsLoading.value = true
  try {
    const response = await questionBankApi.getQuestions(bankId, {
      skip: (questionPagination.page - 1) * questionPagination.size,
      limit: questionPagination.size
    })
    questions.value = response.items
    totalQuestions.value = response.total
  } catch (error) {
    ElMessage.error('加载题目失败')
  } finally {
    questionsLoading.value = false
  }
}

// 编辑题库
const handleEditBank = () => {
  router.push({
    name: 'question-bank-edit',
    params: { bankId }
  })
}

// 新建题目成功回调
const handleQuestionCreated = () => {
  loadBank() // 更新题目计数
  loadQuestions() // 刷新题目列表
}

// 编辑题目 - 跳转到编辑页面
const handleEditQuestion = (question: Question) => {
  router.push({
    name: 'question-edit',
    params: { questionId: question.id },
    query: { bankId }
  })
}

// 查看题目
const handleViewQuestion = (question: Question) => {
  viewingQuestion.value = question
  showViewDialog.value = true
}

// 移除题目
const handleRemoveQuestion = async (question: Question) => {
  try {
    await ElMessageBox.confirm(
      `确定要将此题目从题库中移除吗？`,
      '移除确认',
      { type: 'warning' }
    )

    await questionBankApi.removeQuestion(bankId, question.id)
    ElMessage.success('移除成功')
    loadBank()
    loadQuestions()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('移除失败')
    }
  }
}

onMounted(() => {
  loadBank()
  loadQuestions()
})
</script>

<style scoped>
.question-bank-detail {
  padding: 20px;
}

.bank-info {
  margin-bottom: 20px;
}

.questions-section {
  min-height: 400px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.question-content {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.5;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}
</style>
