<template>
  <div class="question-editor-page">
    <el-page-header @back="$router.back()">
      <template #content>
        <h2>{{ isEditMode ? '编辑题目' : '新建题目' }}</h2>
      </template>
      <template #extra>
        <el-button :icon="Upload" @click="showImportDialog = true">
          批量导入
        </el-button>
      </template>
    </el-page-header>

    <el-card v-loading="loading" class="editor-container">
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
        class="question-form"
      >
        <el-divider content-position="left">基础信息</el-divider>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="题目类型" prop="question_type">
              <el-select
                v-model="formData.question_type"
                placeholder="选择题目类型"
                style="width: 100%"
                :disabled="isEditMode"
              >
                <el-option label="选择题" value="choice" />
                <el-option label="填空题" value="fill_blank" />
                <el-option label="阅读理解" value="reading" />
                <el-option label="听力题" value="audio" />
                <el-option label="写作题" value="writing" />
                <el-option label="翻译题" value="translation" />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="难度等级" prop="difficulty_level">
              <el-select
                v-model="formData.difficulty_level"
                placeholder="选择难度"
                style="width: 100%"
              >
                <el-option label="简单" value="easy" />
                <el-option label="中等" value="medium" />
                <el-option label="困难" value="hard" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="知识点" prop="topic">
          <el-select
            v-model="formData.topic"
            placeholder="选择或输入知识点"
            allow-create
            filterable
            default-first-option
            style="width: 100%"
          >
            <el-option label="时态" value="时态" />
            <el-option label="语态" value="语态" />
            <el-option label="从句" value="从句" />
            <el-option label="非谓语动词" value="非谓语动词" />
            <el-option label="定语从句" value="定语从句" />
            <el-option label="名词性从句" value="名词性从句" />
            <el-option label="状语从句" value="状语从句" />
            <el-option label="虚拟语气" value="虚拟语气" />
            <el-option label="倒装句" value="倒装句" />
            <el-option label="介词" value="介词" />
            <el-option label="冠词" value="冠词" />
            <el-option label="连词" value="连词" />
            <el-option label="代词" value="代词" />
          </el-select>
        </el-form-item>

        <el-form-item label="题目内容" prop="content_text">
          <el-input
            v-model="formData.content_text"
            type="textarea"
            :rows="4"
            placeholder="请输入题目内容"
          />
        </el-form-item>

        <RichTextEditor
          v-model="formData.content_text"
          placeholder="请输入题目内容（支持富文本）"
        />

        <ChoiceEditor
          v-if="formData.question_type === 'choice'"
          v-model="formData.options"
          :correct-answer="formData.correct_answer as Record<string, string>"
          @update:correct-answer="formData.correct_answer = $event"
        />

        <FillBlankEditor
          v-if="formData.question_type === 'fill_blank'"
          :answers="fillBlankAnswers"
          :correct-answer="formData.correct_answer as Record<string, any>"
          @update:answers="fillBlankAnswers = $event"
          @update:correct-answer="formData.correct_answer = $event"
        />

        <ReadingEditor
          v-if="formData.question_type === 'reading'"
          v-model="formData.passage_content"
          :correct-answer="formData.correct_answer as Record<string, any>"
          @update:correct-answer="formData.correct_answer = $event"
        />

        <AudioEditor
          v-if="formData.question_type === 'audio'"
          v-model="formData.audio_url"
          :correct-answer="formData.correct_answer as Record<string, string>"
          @update:correct-answer="formData.correct_answer = $event"
        />

        <WritingEditor
          v-if="formData.question_type === 'writing'"
          :sample-answer="formData.sample_answer"
          :correct-answer="formData.correct_answer as Record<string, string>"
          @update:sample-answer="formData.sample_answer = $event"
          @update:correct-answer="formData.correct_answer = $event"
        />

        <TranslationEditor
          v-if="formData.question_type === 'translation'"
          :source-text-value="translationSource"
          :target-text-value="translationTarget"
          @update:source-text="handleTranslationSourceUpdate"
          @update:target-text="handleTranslationTargetUpdate"
        />

        <el-divider content-position="left">答案解析</el-divider>

        <el-form-item label="题目解析">
          <RichTextEditor
            v-model="formData.explanation"
            placeholder="请输入题目解析，可包含答案说明、知识点讲解等..."
          />
        </el-form-item>
      </el-form>

      <div class="form-footer">
        <div class="footer-left">
          <el-checkbox v-model="autoSave">自动保存草稿</el-checkbox>
          <span v-if="lastSaveTime" class="save-time">
            上次保存: {{ lastSaveTime }}
          </span>
        </div>
        <div class="footer-right">
          <el-button @click="$router.back()">取消</el-button>
          <el-button type="primary" :loading="saving" @click="handleSave">
            保存题目
          </el-button>
        </div>
      </div>
    </el-card>

    <ImportDialog
      v-model="showImportDialog"
      :question-bank-id="questionBankId"
      @success="handleImportSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'
import RichTextEditor from '@/components/question/editor/RichTextEditor.vue'
import ChoiceEditor from '@/components/question/editor/ChoiceEditor.vue'
import FillBlankEditor from '@/components/question/editor/FillBlankEditor.vue'
import ReadingEditor from '@/components/question/editor/ReadingEditor.vue'
import AudioEditor from '@/components/question/editor/AudioEditor.vue'
import WritingEditor from '@/components/question/editor/WritingEditor.vue'
import TranslationEditor from '@/components/question/editor/TranslationEditor.vue'
import ImportDialog from '@/components/question/editor/ImportDialog.vue'
import { questionApi } from '@/api/question'
import type { CreateQuestionRequest, QuestionType } from '@/types/question'

const router = useRouter()
const route = useRoute()

const questionId = route.params.questionId as string
const questionBankId = route.query.bankId as string | undefined

const formRef = ref<FormInstance>()
const loading = ref(false)
const saving = ref(false)
const showImportDialog = ref(false)
const autoSave = ref(true)
const lastSaveTime = ref('')
const isEditMode = computed(() => !!questionId)
let autoSaveTimer: ReturnType<typeof setInterval> | null = null

const formData = reactive<CreateQuestionRequest>({
  question_type: 'choice' as QuestionType,
  content_text: '',
  question_bank_id: questionBankId,
  difficulty_level: undefined,
  topic: '',
  knowledge_points: [],
  options: [
    { key: 'A', content: '' },
    { key: 'B', content: '' },
    { key: 'C', content: '' },
    { key: 'D', content: '' }
  ],
  correct_answer: {},
  explanation: '',
  passage_content: '',
  audio_url: '',
  sample_answer: ''
})

const fillBlankAnswers = ref<string[]>([])
const passageContent = ref('')
const audioUrl = ref('')
const sampleAnswer = ref('')
const translationSource = ref('')
const translationTarget = ref('')

const commonKnowledgePoints = [
  '时态', '语态', '从句', '非谓语动词', '定语从句',
  '名词性从句', '状语从句', '虚拟语气', '倒装句',
  '介词', '冠词', '连词', '代词'
]

const formRules: FormRules = {
  question_type: [{ required: true, message: '请选择题目类型', trigger: 'change' }],
  content_text: [{ required: true, message: '请输入题目内容', trigger: 'blur' }]
}

const handleTranslationSourceUpdate = (val: string) => {
  translationSource.value = val
  if (!formData.correct_answer || typeof formData.correct_answer === 'string') {
    formData.correct_answer = {}
  }
  ;(formData.correct_answer as Record<string, any>).source = val
}

const handleTranslationTargetUpdate = (val: string) => {
  translationTarget.value = val
  if (!formData.correct_answer || typeof formData.correct_answer === 'string') {
    formData.correct_answer = {}
  }
  ;(formData.correct_answer as Record<string, any>).target = val
}

const loadQuestion = async () => {
  if (!isEditMode.value) return

  loading.value = true
  try {
    const question = await questionApi.getDetail(questionId)

    Object.assign(formData, {
      question_type: question.question_type,
      content_text: question.content_text,
      difficulty_level: question.difficulty_level,
      topic: question.topic,
      knowledge_points: question.knowledge_points || [],
      options: question.options || [],
      correct_answer: question.correct_answer || {},
      explanation: question.explanation || '',
      passage_content: question.passage_content || '',
      audio_url: question.audio_url || '',
      sample_answer: question.sample_answer || ''
    })

    if (question.question_type === 'fill_blank') {
      const ans = question.correct_answer as any
      if (ans?.type === 'multiple') {
        fillBlankAnswers.value = ans.answers || []
      }
    }

    if (question.question_type === 'translation') {
      const ans = question.correct_answer as any
      if (ans) {
        translationSource.value = ans.source || ''
        translationTarget.value = ans.target || ''
      }
    }
  } catch (error) {
    ElMessage.error('加载题目失败')
  } finally {
    loading.value = false
  }
}

const handleTypeChange = () => {
  if (isEditMode.value) {
    ElMessage.warning('编辑模式下不能修改题目类型')
    return
  }

  formData.correct_answer = {}
  fillBlankAnswers.value = []
  passageContent.value = ''
  audioUrl.value = ''
  sampleAnswer.value = ''
  translationSource.value = ''
  translationTarget.value = ''
}

const formatDateTime = (date: Date) => {
  return date.toLocaleString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
}

const handleSave = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    saving.value = true

    const data: CreateQuestionRequest = {
      question_type: formData.question_type,
      content_text: formData.content_text,
      difficulty_level: formData.difficulty_level,
      topic: formData.topic,
      knowledge_points: formData.knowledge_points,
      options: formData.options,
      correct_answer: formData.correct_answer,
      explanation: formData.explanation,
      passage_content: formData.passage_content,
      audio_url: formData.audio_url,
      sample_answer: formData.sample_answer
    }

    if (isEditMode.value) {
      await questionApi.update(questionId, data)
      ElMessage.success('更新成功')
    } else {
      await questionApi.create(data)
      ElMessage.success('创建成功')
      router.push('/teacher/question-banks')
    }
  } catch (error) {
    console.error('保存失败:', error)
  } finally {
    saving.value = false
  }
}

const handleImportSuccess = () => {
  showImportDialog.value = false
  loadQuestion()
}

const startAutoSave = () => {
  if (!autoSave.value || isEditMode.value) return

  autoSaveTimer = setInterval(async () => {
    if (!formData.content_text.trim()) return

    try {
      const data: CreateQuestionRequest = {
        question_type: formData.question_type,
        content_text: formData.content_text,
        difficulty_level: formData.difficulty_level,
        topic: formData.topic,
        knowledge_points: formData.knowledge_points,
        options: formData.options,
        correct_answer: formData.correct_answer,
        explanation: formData.explanation,
        passage_content: formData.passage_content,
        audio_url: formData.audio_url,
        sample_answer: formData.sample_answer
      }

      if (questionBankId) {
        data.question_bank_id = questionBankId
      }

      const result = await questionApi.create(data)
      lastSaveTime.value = formatDateTime(new Date())
      ElMessage.success('草稿已自动保存')
    } catch (error) {
      console.error('自动保存失败:', error)
    }
  }, 60000)
}

onMounted(() => {
  loadQuestion()
  startAutoSave()
})

onUnmounted(() => {
  if (autoSaveTimer) {
    clearInterval(autoSaveTimer)
  }
})

defineExpose({
  handleSave,
  handleImportSuccess
})
</script>

<style scoped>
.question-editor-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.editor-container {
  min-height: 60vh;
}

.question-form {
  max-height: none;
}

.type-specific {
  margin: 20px 0;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 4px;
}

.form-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #dcdfe6;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.save-time {
  font-size: 13px;
  color: #909399;
}

.footer-right {
  display: flex;
  gap: 12px;
}
</style>
