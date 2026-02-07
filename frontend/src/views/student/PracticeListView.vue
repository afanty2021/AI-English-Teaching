<template>
  <div class="practice-list">
    <el-page-header @back="$router.back()">
      <template #content>
        <h2>练习中心</h2>
      </template>
    </el-page-header>

    <!-- 筛选栏 -->
    <el-card class="filter-card">
      <el-form
        :inline="true"
        :model="filters"
      >
        <el-form-item label="练习类型">
          <el-select
            v-model="filters.practice_type"
            placeholder="全部"
            clearable
            @change="handleFilter"
          >
            <el-option
              label="阅读"
              value="reading"
            />
            <el-option
              label="听力"
              value="listening"
            />
            <el-option
              label="语法"
              value="grammar"
            />
            <el-option
              label="词汇"
              value="vocabulary"
            />
            <el-option
              label="写作"
              value="writing"
            />
            <el-option
              label="口语"
              value="speaking"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="难度等级">
          <el-select
            v-model="filters.difficulty_level"
            placeholder="全部"
            clearable
            @change="handleFilter"
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
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 题库列表 -->
    <div
      v-loading="loading"
      class="bank-list"
    >
      <el-empty
        v-if="!banks.length && !loading"
        description="暂无可用的题库"
      />

      <el-row :gutter="16">
        <el-col
          v-for="bank in banks"
          :key="bank.id"
          :xs="24"
          :sm="12"
          :md="8"
          :lg="6"
        >
          <el-card
            class="bank-card"
            shadow="hover"
            @click="handleStartPractice(bank)"
          >
            <div class="bank-header">
              <h3>{{ bank.name }}</h3>
              <el-tag
                size="small"
                :type="getTypeTagType(bank.practice_type)"
              >
                {{ getTypeLabel(bank.practice_type) }}
              </el-tag>
            </div>
            <p
              v-if="bank.description"
              class="bank-description"
            >
              {{ bank.description }}
            </p>
            <div class="bank-info">
              <span><el-icon><Document /></el-icon> {{ bank.question_count }} 题</span>
              <span v-if="bank.difficulty_level">
                <el-icon><TrendCharts /></el-icon> {{ bank.difficulty_level }}
              </span>
            </div>
            <div class="bank-footer">
              <el-button
                type="primary"
                plain
              >
                开始练习
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 分页 -->
      <div
        v-if="total > 0"
        class="pagination"
      >
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="total"
          :page-sizes="[12, 24, 48]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadBanks"
          @current-change="loadBanks"
        />
      </div>
    </div>

    <!-- 开始练习对话框 -->
    <el-dialog
      v-model="showStartDialog"
      title="开始练习"
      width="500px"
    >
      <el-form
        :model="practiceForm"
        label-width="100px"
      >
        <el-form-item label="练习模式">
          <el-radio-group v-model="practiceForm.mode">
            <el-radio label="all">
              全部题目
            </el-radio>
            <el-radio label="random">
              随机题目
            </el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item
          v-if="practiceForm.mode === 'random'"
          label="题目数量"
        >
          <el-input-number
            v-model="practiceForm.count"
            :min="5"
            :max="50"
          />
        </el-form-item>
        <el-form-item label="会话标题">
          <el-input
            v-model="practiceForm.title"
            placeholder="可选，便于后续查找"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showStartDialog = false">
          取消
        </el-button>
        <el-button
          type="primary"
          @click="confirmStartPractice"
        >
          开始练习
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document, TrendCharts } from '@element-plus/icons-vue'
import { questionBankApi } from '@/api/questionBank'
import { practiceSessionApi } from '@/api/practiceSession'
import type { QuestionBank } from '@/types/question'

const router = useRouter()

const loading = ref(false)
const banks = ref<QuestionBank[]>([])
const total = ref(0)

const filters = reactive({
  practice_type: '',
  difficulty_level: ''
})

const pagination = reactive({
  page: 1,
  size: 12
})

const showStartDialog = ref(false)
const selectedBank = ref<QuestionBank | null>(null)
const practiceForm = reactive({
  mode: 'all',
  count: 10,
  title: ''
})

// 获取练习类型标签类型
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

// 获取练习类型标签
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

// 加载题库列表
const loadBanks = async () => {
  loading.value = true
  try {
    const response = await questionBankApi.list({
      ...filters,
      is_public: true,
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

// 筛选处理
const handleFilter = () => {
  pagination.page = 1
  loadBanks()
}

// 开始练习
const handleStartPractice = (bank: QuestionBank) => {
  selectedBank.value = bank
  practiceForm.title = `${bank.name} - ${new Date().toLocaleDateString()}`
  showStartDialog.value = true
}

// 确认开始练习
const confirmStartPractice = async () => {
  if (!selectedBank.value) return

  try {
    const response = await practiceSessionApi.start({
      question_source: 'bank',
      question_bank_id: selectedBank.value.id,
      title: practiceForm.title || undefined
    })

    ElMessage.success('练习会话创建成功')
    router.push({
      name: 'practice',
      params: { sessionId: response.id }
    })
  } catch (error) {
    ElMessage.error('创建练习会话失败')
  }
}

onMounted(() => {
  loadBanks()
})
</script>

<style scoped>
.practice-list {
  padding: 20px;
}

.filter-card {
  margin-bottom: 20px;
}

.bank-list {
  min-height: 400px;
}

.bank-card {
  margin-bottom: 16px;
  cursor: pointer;
  transition: transform 0.2s;
}

.bank-card:hover {
  transform: translateY(-4px);
}

.bank-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.bank-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.bank-description {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #606266;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 40px;
}

.bank-info {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  font-size: 14px;
  color: #909399;
}

.bank-info span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.bank-footer {
  text-align: center;
}

.pagination {
  margin-top: 20px;
  text-align: center;
}
</style>
