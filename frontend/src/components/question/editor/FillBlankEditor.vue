<template>
  <div class="fill-blank-editor">
    <div class="answers-section">
      <div class="section-header">
        <h4>正确答案设置</h4>
        <el-button size="small" :icon="Plus" @click="addAnswer">添加答案</el-button>
      </div>

      <div class="answers-list">
        <div v-for="(_answer, index) in answers" :key="index" class="answer-item">
          <el-input
            v-model="answers[index]"
            placeholder="请输入正确答案"
            @input="handleAnswersChange"
          >
            <template #append>
              <el-button
                :icon="Close"
                :disabled="answers.length <= 1"
                @click="removeAnswer(index)"
              />
            </template>
          </el-input>
          <el-tag v-if="index === 0" type="success" size="small">主要答案</el-tag>
          <el-tag v-else type="info" size="small">等价答案 {{ index }}</el-tag>
        </div>
      </div>

      <div class="answer-hint">
        <el-icon><InfoFilled /></el-icon>
        <span>多个答案将被视为等价，学生回答其中任意一个即可</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { Plus, Close, InfoFilled } from '@element-plus/icons-vue'
import type { CorrectAnswer } from '@/types/question'

interface Props {
  modelValue?: string[]
}

interface Emits {
  (e: 'update:modelValue', value: string[]): void
}

const props = defineProps<Props>()

const emit = defineEmits<Emits>()

const answers = ref<string[]>([''])

// 监听外部变化
watch(() => props.modelValue, (newVal) => {
  if (newVal && newVal.length > 0) {
    answers.value = [...newVal]
  }
}, { immediate: true })

// 添加答案
const addAnswer = () => {
  if (answers.value.length >= 10) {
    return
  }
  answers.value.push('')
}

// 移除答案
const removeAnswer = (index: number) => {
  if (answers.value.length <= 1) {
    return
  }
  answers.value.splice(index, 1)
  handleAnswersChange()
}

// 答案变化
const handleAnswersChange = () => {
  const validAnswers = answers.value.filter(a => a.trim())
  emit('update:modelValue', validAnswers)
}

// 获取正确答案对象
const getCorrectAnswer = (): CorrectAnswer => {
  const validAnswers = answers.value.filter(a => a.trim())
  return {
    answers: validAnswers,
    type: 'multiple'
  }
}

// 暴露验证方法和数据获取
defineExpose({
  validate: () => {
    const hasAnswer = answers.value.some(a => a.trim())

    if (!hasAnswer) {
      return { valid: false, message: '请至少填写一个正确答案' }
    }

    return { valid: true }
  },
  getCorrectAnswer
})
</script>

<style scoped>
.fill-blank-editor {
  padding: 16px 0;
}

.answers-section {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 4px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.answers-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.answer-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.answer-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding: 8px 12px;
  background: #fff;
  border-radius: 4px;
  font-size: 13px;
  color: #909399;
}
</style>
