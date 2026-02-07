<template>
  <el-dialog
    v-model="visible"
    title="批量导入题目"
    width="600px"
    @close="handleClose"
  >
    <el-tabs
      v-model="activeTab"
      @tab-change="handleTabChange"
    >
      <!-- JSON导入 -->
      <el-tab-pane
        label="JSON导入"
        name="json"
      >
        <div class="json-import">
          <el-form label-width="80px">
            <el-form-item label="导入方式">
              <el-radio-group v-model="jsonImportMode">
                <el-radio label="paste">
                  粘贴JSON
                </el-radio>
                <el-radio label="file">
                  上传文件
                </el-radio>
              </el-radio-group>
            </el-form-item>

            <!-- 粘贴JSON -->
            <div
              v-if="jsonImportMode === 'paste'"
              class="json-paste"
            >
              <el-input
                v-model="jsonContent"
                type="textarea"
                :rows="12"
                placeholder="请粘贴JSON格式的题目数据，每行一个题目对象..."
                @input="handleJsonInput"
              />
              <div class="json-hint">
                <strong>格式示例：</strong>
                <pre>{{ jsonExample }}</pre>
              </div>
            </div>

            <!-- 上传JSON文件 -->
            <div
              v-else
              class="json-file"
            >
              <el-upload
                class="upload-area"
                drag
                action="#"
                :auto-upload="false"
                accept=".json"
                :on-change="handleJsonFileChange"
              >
                <el-icon class="el-icon--upload">
                  <Upload />
                </el-icon>
                <div class="el-upload__text">
                  拖拽JSON文件到此处或<em>点击上传</em>
                </div>
              </el-upload>
            </div>
          </el-form>
        </div>
      </el-tab-pane>

      <!-- Excel导入 -->
      <el-tab-pane
        label="Excel导入"
        name="excel"
      >
        <div class="excel-import">
          <el-alert
            type="info"
            :closable="false"
            show-icon
          >
            <template #default>
              <div>
                <strong>Excel导入说明：</strong>
                <ul style="margin: 8px 0 0 16px; padding: 0;">
                  <li>第一行为表头，从第二行开始是题目数据</li>
                  <li>必填列：question_type（题目类型）、content_text（题目内容）</li>
                  <li>选择题需要options列，格式为JSON数组</li>
                  <li>支持下载模板</li>
                </ul>
              </div>
            </template>
          </el-alert>

          <div class="excel-actions">
            <el-button
              :icon="Download"
              @click="downloadTemplate"
            >
              下载模板
            </el-button>
          </div>

          <el-upload
            class="upload-area"
            drag
            action="#"
            :auto-upload="false"
            accept=".xlsx,.xls"
            :on-change="handleExcelFileChange"
          >
            <el-icon class="el-icon--upload">
              <Upload />
            </el-icon>
            <div class="el-upload__text">
              拖拽Excel文件到此处或<em>点击上传</em>
            </div>
          </el-upload>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 导入结果预览 -->
    <div
      v-if="parsedQuestions.length > 0"
      class="preview-section"
    >
      <div class="preview-header">
        <h4>已解析 {{ parsedQuestions.length }} 道题目</h4>
        <el-button
          type="primary"
          size="small"
          @click="handleImport"
        >
          确认导入
        </el-button>
      </div>
      <div class="questions-preview">
        <div
          v-for="(question, index) in parsedQuestions"
          :key="index"
          class="question-preview-item"
        >
          <div class="question-header">
            <span class="question-index">第 {{ index + 1 }} 题</span>
            <el-tag size="small">
              {{ getQuestionTypeLabel(question.question_type) }}
            </el-tag>
          </div>
          <div class="question-content">
            {{ question.content_text }}
          </div>
          <div
            v-if="question.options?.length"
            class="question-options"
          >
            <span
              v-for="option in question.options"
              :key="option.key"
              class="option-tag"
            >
              {{ option.key }}. {{ option.content }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部操作 -->
    <template #footer>
      <el-button @click="handleClose">
        取消
      </el-button>
      <el-button
        type="primary"
        :loading="importing"
        :disabled="parsedQuestions.length === 0"
        @click="handleImport"
      >
        确认导入
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload, Download } from '@element-plus/icons-vue'
import { questionApi } from '@/api/question'
import type { CreateQuestionRequest, QuestionType } from '@/types/question'

interface Props {
  modelValue: boolean
  questionBankId?: string
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const visible = ref(props.modelValue)
const activeTab = ref<'json' | 'excel'>('json')
const importing = ref(false)

const jsonImportMode = ref<'paste' | 'file'>('paste')
const jsonContent = ref('')
const parsedQuestions = ref<CreateQuestionRequest[]>([])

// JSON示例
const jsonExample = `[
  {
    "question_type": "choice",
    "content_text": "What is the capital of France?",
    "difficulty_level": "A1",
    "topic": "地理",
    "knowledge_points": ["地理", "首都"],
    "options": [
      {"key": "A", "content": "London"},
      {"key": "B", "content": "Paris"},
      {"key": "C", "content": "Berlin"},
      {"key": "D", "content": "Madrid"}
    ],
    "correct_answer": {"key": "B"},
    "explanation": "Paris是法国的首都。"
  },
  {
    "question_type": "fill_blank",
    "content_text": "Complete the sentence: I _____ to school every day.",
    "difficulty_level": "A1",
    "topic": "日常",
    "knowledge_points": ["词汇", "时态"],
    "correct_answer": {"answers": ["go", "goes"], "type": "multiple"},
    "explanation": "一般现在时第三人称单数用goes。"
  }
]`

// JSON输入处理
const handleJsonInput = () => {
  try {
    const lines = jsonContent.value.trim().split('\n')
    const questions: CreateQuestionRequest[] = []

    for (const line of lines) {
      if (!line.trim()) continue
      const question = JSON.parse(line)

      // 基本验证
      if (!question.question_type || !question.content_text) {
        throw new Error('题目必须包含 question_type 和 content_text')
      }

      questions.push({
        ...question,
        question_bank_id: props.questionBankId
      })
    }

    parsedQuestions.value = questions
    ElMessage.success(`成功解析 ${questions.length} 道题目`)
  } catch (error) {
    parsedQuestions.value = []
    if (jsonContent.value.trim()) {
      ElMessage.error('JSON格式错误，请检查格式是否正确')
    }
  }
}

// JSON文件上传处理
const handleJsonFileChange = (file: any) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const content = e.target?.result as string
      jsonContent.value = content
      handleJsonInput()
    } catch (error) {
      ElMessage.error('文件读取失败')
    }
  }
  reader.readAsText(file.raw)
}

// Excel文件上传处理
const handleExcelFileChange = (_file: any) => {
  ElMessage.info('Excel导入功能开发中，请使用JSON导入或手动创建题目')
  // TODO: 集成xlsx库解析Excel文件
}

// 下载Excel模板
const downloadTemplate = () => {
  const template = [
    {
      question_type: 'choice',
      content_text: '题目内容',
      difficulty_level: 'A1',
      topic: '主题',
      knowledge_points: '知识点1,知识点2',
      options: '[{"key":"A","content":"选项A"},{"key":"B","content":"选项B"},{"key":"C","content":"选项C"},{"key":"D","content":"选项D"}]',
      correct_answer: '{"key":"B"}',
      explanation: '答案解析'
    },
    {
      question_type: 'fill_blank',
      content_text: '填空题内容',
      difficulty_level: 'A2',
      topic: '语法',
      knowledge_points: '知识点',
      correct_answer: '[{"answers":["答案1","答案2"],"type":"multiple"}]',
      explanation: '解析'
    },
    {
      question_type: 'reading',
      content_text: '题目内容',
      difficulty_level: 'B1',
      passage_content: '阅读文章内容...',
      options: '[{"key":"A","content":"A"},{"key":"B","content":"B"},{"key":"C","content":"C"},{"key":"D","content":"D"}]',
      correct_answer: '{"key":"A"}',
      explanation: '解析'
    }
  ]

  const csvContent = template.map(row => Object.values(row).join(',')).join('\n')
  const blob = new Blob([csvContent], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'questions_template.csv'
  a.click()
  URL.revokeObjectURL(url)
}

// 标签页切换
const handleTabChange = () => {
  parsedQuestions.value = []
}

// 获取题目类型标签
const getQuestionTypeLabel = (type: QuestionType) => {
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

// 确认导入
const handleImport = async () => {
  if (parsedQuestions.value.length === 0) {
    ElMessage.warning('请先选择要导入的题目数据')
    return
  }

  importing.value = true
  try {
    await questionApi.batchCreate({
      questions: parsedQuestions.value,
      question_bank_id: props.questionBankId
    })

    ElMessage.success(`成功导入 ${parsedQuestions.value.length} 道题目`)
    emit('success')
    handleClose()
  } catch (error) {
    ElMessage.error('导入失败')
  } finally {
    importing.value = false
  }
}

// 关闭对话框
const handleClose = () => {
  visible.value = false
  jsonContent.value = ''
  parsedQuestions.value = []
  emit('update:modelValue', false)
}
</script>

<style scoped>
.json-import,
.excel-import {
  padding: 16px 0;
}

.json-paste {
  margin-top: 16px;
}

.json-hint {
  margin-top: 16px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

.json-hint pre {
  margin: 8px 0 0 0;
  padding: 8px;
  background: #fff;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.4;
  color: #606266;
}

.json-file,
.excel-actions {
  margin-top: 16px;
}

.upload-area {
  width: 100%;
}

.preview-section {
  margin-top: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 4px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.preview-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.questions-preview {
  max-height: 300px;
  overflow-y: auto;
}

.question-preview-item {
  padding: 12px;
  background: #fff;
  border-radius: 4px;
  margin-bottom: 12px;
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.question-index {
  font-weight: 600;
  color: #606266;
}

.question-content {
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 8px;
}

.question-options {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.option-tag {
  padding: 4px 8px;
  background: #f0f9ff;
  border-radius: 4px;
  font-size: 13px;
}
</style>
