<template>
  <div class="fill-blank-question">
    <!-- 题目内容 -->
    <div class="question-content">
      <h4>{{ question.content_text }}</h4>
    </div>

    <!-- 答案输入 -->
    <div class="answer-input">
      <el-input
        v-model="answer"
        type="textarea"
        :rows="3"
        placeholder="请输入答案..."
        :disabled="submitted"
        @blur="handleSubmit"
      />
    </div>

    <!-- 提交后显示解析 -->
    <div v-if="showResult" class="result-section">
      <el-alert
        :type="isCorrect ? 'success' : 'error'"
        :closable="false"
        show-icon
      >
        <template #title>
          {{ isCorrect ? '回答正确！' : '回答错误' }}
        </template>
        <div class="correct-answer">
          <strong>正确答案：</strong>{{ question.correct_answer }}
        </div>
        <div v-if="question.explanation" class="explanation">
          <strong>解析：</strong>{{ question.explanation }}
        </div>
      </el-alert>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { Question } from '@/types/question'

interface Props {
  question: Question
  modelValue?: string
  submitted?: boolean
  showResult?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: string): void
  (e: 'submit', answer: string): void
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  submitted: false,
  showResult: false
})

const emit = defineEmits<Emits>()

const answer = ref(props.modelValue || '')

// 监听外部值变化
watch(() => props.modelValue, (newVal) => {
  answer.value = newVal || ''
})

// 是否正确（简单判断，实际需要根据题型处理）
const isCorrect = computed(() => {
  if (!props.showResult || !answer.value) return false
  const correctAnswer = props.question.correct_answer as string
  return answer.value.trim().toLowerCase() === correctAnswer.toLowerCase()
})

const handleSubmit = () => {
  emit('update:modelValue', answer.value)
  if (!props.submitted && answer.value.trim()) {
    emit('submit', answer.value)
  }
}
</script>

<style scoped>
.fill-blank-question {
  padding: 20px;
}

.question-content h4 {
  margin: 0 0 20px 0;
  font-size: 16px;
  line-height: 1.6;
}

.answer-input {
  margin-bottom: 20px;
}

.result-section {
  margin-top: 20px;
}

.correct-answer,
.explanation {
  margin-top: 10px;
  font-size: 14px;
  line-height: 1.6;
}
</style>
