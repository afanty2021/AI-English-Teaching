<template>
  <el-dialog
    v-model="visible"
    :title="isEditMode ? '编辑题目' : '新建题目'"
    width="900px"
    :close-on-click-modal="false"
    class="question-editor-dialog"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
      class="question-form"
    >
      <!-- 基础信息 -->
      <el-divider content-position="left">
        基础信息
      </el-divider>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item
            label="题目类型"
            prop="question_type"
          >
            <el-select
              v-model="formData.question_type"
              placeholder="请选择题目类型"
              :disabled="isEditMode"
              @change="handleTypeChange"
            >
              <el-option
                label="选择题"
                value="choice"
              />
              <el-option
                label="填空题"
                value="fill_blank"
              />
              <el-option
                label="阅读理解"
                value="reading"
              />
              <el-option
                label="写作题"
                value="writing"
              />
              <el-option
                label="口语题"
                value="speaking"
              />
              <el-option
                label="听力题"
                value="listening"
              />
              <el-option
                label="翻译题"
                value="translation"
              />
            </el-select>
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item
            label="难度等级"
            prop="difficulty_level"
          >
            <el-select
              v-model="formData.difficulty_level"
              placeholder="请选择难度"
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
        </el-col>
      </el-row>

      <el-form-item
        label="主题分类"
        prop="topic"
      >
        <el-input
          v-model="formData.topic"
          placeholder="如：语法、词汇、阅读理解等"
        />
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
      <el-divider content-position="left">
        题目内容
      </el-divider>

      <!-- 题目文本内容（富文本） -->
      <el-form-item
        label="题目内容"
        prop="content_text"
      >
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
          v-model="optionsList"
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
      <el-divider content-position="left">
        答案解析
      </el-divider>

      <el-form-item label="题目解析">
        <RichTextEditor
          v-model="explanationText"
          placeholder="请输入题目解析，可包含答案说明、知识点讲解等..."
        />
      </el-form-item>
    </el-form>

    <!-- 底部操作栏 -->
    <template #footer>
      <div class="dialog-footer">
        <div class="footer-left">
          <el-checkbox v-model="autoSave">
            自动保存草稿
          </el-checkbox>
          <span
            v-if="lastSaveTime"
            class="save-time"
          >
            上次保存: {{ lastSaveTime }}
          </span>
        </div>
        <div class="footer-right">
          <el-button @click="handleClose">
            取消
          </el-button>
          <el-button
            type="primary"
            :loading="saving"
            @click="handleSave"
          >
            保存题目
          </el-button>
        </div>
      </div>
    </template>

    <!-- 实时预览（侧边抽屉） -->
    <el-drawer
      v-model="showPreview"
      title="实时预览"
      direction="rtl"
      size="45%"
    >
      <div class="preview-container">
        <QuestionRenderer
          v-if="previewQuestion"
          :question="previewQuestion"
          :show-meta="true"
        />
        <el-empty
          v-else
          description="填写题目内容后可查看预览"
        />
      </div>
    </el-drawer>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onUnmounted } from 'vue'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import RichTextEditor from './RichTextEditor.vue'
import ChoiceEditor from './ChoiceEditor.vue'
import FillBlankEditor from './FillBlankEditor.vue'
import ReadingEditor from './ReadingEditor.vue'
import AudioEditor from './AudioEditor.vue'
import WritingEditor from './WritingEditor.vue'
import TranslationEditor from './TranslationEditor.vue'
import QuestionRenderer from '../QuestionRenderer.vue'
import { questionApi } from '@/api/question'
import type { Question, CreateQuestionRequest, QuestionType, QuestionOption } from '@/types/question'

interface Props {
  modelValue: boolean
  questionId?: string
  questionBankId?: string
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const visible = ref(props.modelValue)
const formRef = ref<FormInstance>()
const saving = ref(false)
const showPreview = ref(false)
const autoSave = ref(true)
const lastSaveTime = ref('')

// 是否为编辑模式
const isEditMode = computed(() => !!props.questionId)

// 表单数据
const formData = reactive<CreateQuestionRequest>({
  question_type: 'choice' as QuestionType,
  content_text: '',
  question_bank_id: props.questionBankId,
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
const explanationText = ref('')
const optionsList = ref<QuestionOption[]>([
  { key: 'A', content: '' },
  { key: 'B', content: '' },
  { key: 'C', content: '' },
  { key: 'D', content: '' }
])

// 监听 options 变化同步到 formData
watch(() => optionsList.value, (newVal) => {
  formData.options = newVal
}, { deep: true })

// 监听 explanation 变化同步到 formData
watch(() => explanationText.value, (newVal) => {
  formData.explanation = newVal || undefined
})

// 监听 formData.explanation 变化同步回本地
watch(() => formData.explanation, (newVal) => {
  if (newVal !== explanationText.value) {
    explanationText.value = newVal || ''
  }
})

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

// 预览题目数据
const previewQuestion = computed<Question>(() => ({
  id: 'preview',
  question_type: formData.question_type,
  content_text: formData.content_text,
  difficulty_level: formData.difficulty_level,
  topic: formData.topic,
  knowledge_points: formData.knowledge_points || [],
  options: optionsList.value,
  correct_answer: formData.correct_answer || {},
  explanation: formData.explanation || '',
  passage_content: passageContent.value || '',
  audio_url: audioUrl.value || '',
  sample_answer: sampleAnswer.value || '',
  order_index: 0,
  is_active: true,
  has_audio: !!audioUrl.value,
  created_by: '',
  created_at: '',
  updated_at: ''
}))

// 题型切换处理
const handleTypeChange = () => {
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
    explanationText: explanationText.value,
    optionsList: optionsList.value,
    savedAt: new Date().toISOString()
  }

  const key = isEditMode.value ? `question_draft_${props.questionId}` : 'new_question_draft'
  localStorage.setItem(key, JSON.stringify(draft))
}

// 加载草稿
const loadDraft = () => {
  const key = isEditMode.value ? `question_draft_${props.questionId}` : 'new_question_draft'
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
      if (draft.explanationText !== undefined) explanationText.value = draft.explanationText
      if (draft.optionsList) optionsList.value = draft.optionsList

      ElMessage.info('已加载上次保存的草稿')
    } catch (error) {
      console.error('Failed to load draft:', error)
    }
  }
}

// 清除草稿
const clearDraft = () => {
  const key = isEditMode.value ? `question_draft_${props.questionId}` : 'new_question_draft'
  localStorage.removeItem(key)
}

// 保存题目
const handleSave = async () => {
  // 验证基础表单
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  // 验证题型特定组件
  // TODO: 集成题型编辑器组件的验证
  // const typeEditor = getTypeEditorRef()
  // if (typeEditor?.validate) {
  //   const typeValid = typeEditor.validate()
  //   if (!typeValid.valid) {
  //     ElMessage.error(typeValid.message || '请完善题目信息')
  //     return
  //   }
  // }

  saving.value = true
  try {
    if (isEditMode.value && props.questionId) {
      await questionApi.update(props.questionId, formData)
      ElMessage.success('题目更新成功')
    } else {
      await questionApi.create(formData)
      ElMessage.success('题目创建成功')
    }

    // 清除草稿
    clearDraft()
    lastSaveTime.value = new Date().toLocaleTimeString()

    emit('success')
    handleClose()
  } catch (error) {
    ElMessage.error(isEditMode.value ? '更新失败' : '创建失败')
  } finally {
    saving.value = false
  }
}

// 关闭对话框
const handleClose = () => {
  visible.value = false
  emit('update:modelValue', false)
}

// 自动保存定时器
let autoSaveTimer: ReturnType<typeof setInterval> | null = null

// 监听可见性
watch(visible, (newVal) => {
  if (newVal) {
    loadDraft()

    // 开启自动保存
    if (autoSave.value) {
      autoSaveTimer = setInterval(saveDraft, 30000) // 每30秒保存一次
    }
  } else {
    // 清理定时器
    if (autoSaveTimer) {
      clearInterval(autoSaveTimer)
      autoSaveTimer = null
    }
  }
})

onUnmounted(() => {
  if (autoSaveTimer) {
    clearInterval(autoSaveTimer)
  }
})
</script>

<style scoped>
.question-form {
  max-height: 60vh;
  overflow-y: auto;
}

.type-specific {
  margin: 20px 0;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 4px;
}

.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
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

.preview-container {
  padding: 20px;
}
</style>

<style>
.question-editor-dialog .el-dialog__body {
  padding-bottom: 0;
}
</style>
