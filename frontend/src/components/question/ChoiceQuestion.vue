<template>
  <div class="choice-question">
    <!-- 题目内容 -->
    <div class="question-content">
      <h4>{{ question.content_text }}</h4>
    </div>

    <!-- 选项列表 -->
    <el-radio-group v-model="selectedAnswer" @change="handleChange">
      <div v-for="option in question.options" :key="option.key" class="option-item">
        <el-radio :label="option.key" :disabled="submitted">
          <span class="option-label">{{ option.key }}.</span>
          <span class="option-content">{{ option.content }}</span>
        </el-radio>
      </div>
    </el-radio-group>

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
        <div v-if="question.explanation" class="explanation">
          <strong>解析：</strong>{{ question.explanation }}
        </div>
      </el-alert>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Question } from '@/types/question'

interface Props {
  question: Question
  modelValue?: any
  submitted?: boolean
  showResult?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: any): void
  (e: 'submit', answer: any): void
}

const props = withDefaults(defineProps<Props>(), {
  submitted: false,
  showResult: false
})

const emit = defineEmits<Emits>()

const selectedAnswer = ref(props.modelValue || null)

// 是否正确
const isCorrect = computed(() => {
  if (!props.showResult || !selectedAnswer.value) return false
  return selectedAnswer.value === props.question.correct_answer.key
})

const handleChange = (value: any) => {
  emit('update:modelValue', value)
  if (!props.submitted) {
    emit('submit', value)
  }
}
</script>

<style scoped>
.choice-question {
  padding: 20px;
}

.question-content h4 {
  margin: 0 0 20px 0;
  font-size: 16px;
  line-height: 1.6;
}

.option-item {
  margin-bottom: 12px;
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  transition: all 0.3s;
}

.option-item:hover {
  background-color: #f5f7fa;
}

.option-label {
  font-weight: 600;
  margin-right: 8px;
}

.option-content {
  font-size: 14px;
}

.result-section {
  margin-top: 20px;
}

.explanation {
  margin-top: 10px;
  font-size: 14px;
  line-height: 1.6;
}
</style>
