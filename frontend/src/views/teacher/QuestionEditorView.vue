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
      <!-- 编辑表单 -->
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
        class="question-form"
      >
        <!-- 基础信息 -->
        <el-divider content-position="left">基础信息</el-divider>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="题目类型" prop="question_type">
              <el-select
                v-model="formData.question_type"
                placeholder="请选择题目类型"
                :disabled="isEditMode"
                @change="handleTypeChange"
              >
                <el-option label="选择题" value="choice" />
                <el-option label="填空题" value="fill_blank" />
                <el-option label="阅读理解" value="reading" />
                <el-option label="写作题" value="writing" />
                <el-option label="口语题" value="speaking" />
                <el-option label="听力题" value="listening" />
                <el-option label="翻译题" value="translation" />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="难度等级" prop="difficulty_level">
              <el-select v-model="formData.difficulty_level" placeholder="请选择难度">
                <el-option label="A1" value="A1" />
                <el-option label="A2" value="A2" />
                <el-option label="B1" value="B1" />
                <el-option label="B2" value="B2" />
                <el-option label="C1" value="C1" />
                <el-option label="C2" value="C2" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="主题分类" prop="topic">
          <el-input v-model="formData.topic" placeholder="如：语法、词汇、阅读理解等" />
        </el-form-item>

        <el-form-item label="知识点标签">
          <el-select
            v-model="formData.knowledge_points"
            multiple
            filterable
            allow-create
            placeholder="请选择或输入知识点标签"
            style="width: 100%"
          >
            <el-option
              v-for="point in commonKnowledgePoints"
              :key="point"
              :label="point"
              :value="point"
            />
          </el-select>
        </el-form-item>

        <!-- 题目内容 -->
        <el-divider content-position="left">题目内容</el-divider>

        <!-- 题目文本内容（富文本） -->
        <el-form-item label="题目内容" prop="content_text">
          <RichTextEditor
            v-model="formData.content_text"
            placeholder="请输入题目内容..."
            :max-length="2000"
          />
        </el-form-item>

        <!-- 题型特定区域 -->
        <div class="type-specific">
          <!-- 选择题 -->
          <ChoiceEditor
            v-if="formData.question_type === 'choice'"
            v-model="formData.options!"
            :correct-answer="formData.correct_answer"
            @update:correct-answer="handleCorrectAnswerUpdate"
          />

          <!-- 填空题 -->
          <FillBlankEditor
            v-else-if="formData.question_type === 'fill_blank'"
            v-model="fillBlankAnswers"
            @update:model-value="handleFillBlankAnswersUpdate"
          />

          <!-- 阅读理解 -->
          <ReadingEditor
            v-else-if="formData.question_type === 'reading'"
            v-model="passageContent"
            @update:model-value="handlePassageUpdate"
          />

          <!-- 听力题 -->
          <AudioEditor
            v-else-if="formData.question_type === 'listening'"
            v-model="audioUrl"
            @update:model-value="handleAudioUrlUpdate"
          />

          <!-- 写作题 -->
          <WritingEditor
            v-else-if="formData.question_type === 'writing'"
            v-model="sampleAnswer"
            type="writing"
          />

          <!-- 口语题 -->
          <WritingEditor
            v-else-if="formData.question_type === 'speaking'"
            v-model="sampleAnswer"
            type="speaking"
          />

          <!-- 翻译题 -->
          <TranslationEditor
            v-else-if="formData.question_type === 'translation'"
            :source-text-value="translationSource"
            :target-text-value="translationTarget"
            @update:source-text="handleTranslationSourceUpdate"
            @update:target-text="handleTranslationTargetUpdate"
          />
        </div>

        <!-- 解析说明 -->
        <el-divider content-position="left">答案解析</el-divider>

        <el-form-item label="题目解析">
          <RichTextEditor
            v-model="formData.explanation!"
            placeholder="请输入题目解析，可包含答案说明、知识点讲解等..."
          />
        </el-form-item>
      </el-form>

      <!-- 底部操作栏 -->
      <div class="form-footer">
        <div class="footer-left">
          <el-checkbox v-model="autoSave">自动保存草稿</el-checkbox>
          <span v-if="lastSaveTime" class="save-time">
            上次保存: {{ lastSaveTime }}
          </span>
        </div>
        <div class="footer-right">
          <el-button @click="$router.back()">取消</el-button>
          <!-- @vue-ignore  handleSave is defined in script setup -->
          <el-button type="primary" :loading="saving" @click="handleSave">
            保存题目
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 批量导入对话框 -->
    <!-- @vue-ignore  handleImportSuccess is defined in script setup -->
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
// Question type imported but not currently used - reserved for future type checking
// import type { Question } from '@/types/question'

const router = useRouter()
const route = useRoute()

const questionId = route.params.questionId as string
const questionBankId = route.query.bankId as string | undefined

// Form ref for template reference
const formRef = ref<FormInstance>()

const loading = ref(false)
const saving = ref(false)
const showImportDialog = ref(false)
const autoSave = ref(true)
const lastSaveTime = ref('')

// 是否为编辑模式
const isEditMode = computed(() => !!questionId && questionId !== 'new')

// 表单数据
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

// 题型特定数据
const fillBlankAnswers = ref<string[]>([])
const passageContent = ref('')
const audioUrl = ref('')
const sampleAnswer = ref('')
const translationSource = ref('')
const translationTarget = ref('')

// 常用知识点
const commonKnowledgePoints = [
  '时态', '语态', '从句', '非谓语动词', '定语从句',
  '名词性从句', '状语从句', '虚拟语气', '倒装句',
  '介词', '冠词', '连词', '代词'
]

// 表单验证规则
const formRules: FormRules = {
  question_type: [{ required: true, message: '请选择题目类型', trigger: 'change' }],
  content_text: [{ required: true, message: '请输入题目内容', trigger: 'blur' }]
}

// 加载题目数据（编辑模式）
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

    // 填空题特殊处理
    if (question.question_type === 'fill_blank') {
      const ans = question.correct_answer as any
      if (ans?.type === 'multiple') {
        fillBlankAnswers.value = ans.answers || []
      }
    }

    // 翻译题特殊处理
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

// 题型切换处理
const handleTypeChange = () => {
  if (isEditMode.value) {
    ElMessage.warning('编辑模式下不能修改题目类型')
    return
  }

  // 重置题型特定数据
  formData.correct_answer = {}
  fillBlankAnswers.value = []
  passageContent.value = ''
  audioUrl.value = ''
  sampleAnswer.value = ''
  translationSource.value = ''
  translationTarget.value = ''
}

// 选择题正确答案更新
const handleCorrectAnswerUpdate = (value: any) => {
  formData.correct_answer = value
}

// 填空题答案更新
const handleFillBlankAnswersUpdate = (value: string[]) => {
  formData.correct_answer = { answers: value, type: 'multiple' }
}

// 阅读理解文章更新
const handlePassageUpdate = (value: string) => {
  passageContent.value = value
  formData.passage_content = value
}

// 音频URL更新
const handleAudioUrlUpdate = (value: string) => {
  audioUrl.value = value
  formData.audio_url = value
}

// 翻译题原文更新
const handleTranslationSourceUpdate = (value: string) => {
  translationSource.value = value
  formData.correct_answer = { source: value, target: translationTarget.value }
}

// 翻译题译文更新
const handleTranslationTargetUpdate = (value: string) => {
  translationTarget.value = value
  formData.correct_answer = { source: translationSource.value, target: value }
}

// 自动保存草稿
const saveDraft = () => {
  if (!autoSave.value) return

  const draft = {
    ...formData,
    fillBlankAnswers: fillBlankAnswers.value,
    passageContent: passageContent.value,
    audioUrl: audioUrl.value,
    sampleAnswer: sampleAnswer.value,
    translationSource: translationSource.value,
    translationTarget: translationTarget.value,
    savedAt: new Date().toISOString()
  }

  const key = isEditMode.value ? `question_draft_${questionId}` : 'new_question_draft'
  localStorage.setItem(key, JSON.stringify(draft))
  lastSaveTime.value = new Date().toLocaleTimeString()
}

// loadDraft function reserved for future draft restoration functionality
// const loadDraft = () => {
  const key = isEditMode.value ? `question_draft_${questionId}` : 'new_question_draft'
  const draftStr = localStorage.getItem(key)

  if (draftStr) {
    try {
      const draft = JSON.parse(draftStr)

      // 恢复表单数据（排除已保存时间）
      const { savedAt, ...draftData } = draft
      Object.assign(formData, draftData)

      // 恢复题型特定数据
      if (draft.fillBlankAnswers) fillBlankAnswers.value = draft.fillBlankAnswers
      if (draft.passageContent) passageContent.value = draft.passageContent
      if (draft.audioUrl) audioUrl.value = draft.audioUrl
      if (draft.sampleAnswer) sampleAnswer.value = draft.sampleAnswer
      if (draft.translationSource) translationSource.value = draft.translationSource
      if (draft.translationTarget) translationTarget.value = draft.translationTarget

      ElMessage.info('已加载上次保存的草稿')
    } catch (error) {
      console.error('Failed to load draft:', error)
    // }
  // }
// }

// 清除草稿
const clearDraft = () => {
  const key = isEditMode.value ? `question_draft_${questionId}` : 'new_question_draft'
  localStorage.removeItem(key)
}

// 保存题目
const handleSave = async () => {
  // Use the template ref variable defined above
  const formEl = formRef.value
  const valid = await formEl?.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    if (isEditMode.value) {
      await questionApi.update(questionId, formData)
      ElMessage.success('题目更新成功')
    } else {
      await questionApi.create(formData)
      ElMessage.success('题目创建成功')
    }

    clearDraft()
    router.back()
  } catch (error) {
    ElMessage.error(isEditMode.value ? '更新失败' : '创建失败')
  } finally {
    saving.value = false
  }
}

// 导入成功处理
const handleImportSuccess = () => {
  showImportDialog.value = false
  if (isEditMode.value) {
    loadQuestion() // 重新加载以更新题目列表
  }
}

// 自动保存定时器
let autoSaveTimer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  loadQuestion()

  // 开启自动保存
  if (autoSave.value) {
    autoSaveTimer = setInterval(saveDraft, 30000)
  }
})

onUnmounted(() => {
  if (autoSaveTimer) {
    clearInterval(autoSaveTimer)
  }
})

// Explicitly expose functions to template (vue-tsc workaround)
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
