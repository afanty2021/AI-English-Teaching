<template>
  <div class="choice-editor">
    <!-- 选项编辑区 -->
    <div class="options-list">
      <h4>选项设置（固定4项）</h4>
      <div
        v-for="(option, index) in options"
        :key="index"
        class="option-item"
      >
        <div class="option-label">
          <el-tag :type="isCorrectAnswer(option.key) ? 'success' : 'info'">
            {{ option.key }}
          </el-tag>
          <el-checkbox
            v-model="option.is_correct"
            @change="handleCorrectChange(index)"
          >
            设为正确答案
          </el-checkbox>
        </div>
        <el-input
          v-model="option.content"
          placeholder="请输入选项内容"
          @input="handleOptionsChange"
        />
        <el-button
          link
          type="danger"
          :disabled="index < 2"
          @click="handleClearOption(index)"
        >
          清空
        </el-button>
      </div>
    </div>

    <!-- 正确答案预览 -->
    <div class="answer-preview">
      <span class="preview-label">正确答案：</span>
      <el-tag type="success">
        {{ correctAnswerKey || '未设置' }}
      </el-tag>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { QuestionOption } from '@/types/question'

interface Props {
  modelValue: QuestionOption[]
  correctAnswer?: Record<string, any>
}

interface Emits {
  (e: 'update:modelValue', value: QuestionOption[]): void
  (e: 'update:correctAnswer', value: Record<string, any>): void
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: () => [{ key: 'A', content: '' }, { key: 'B', content: '' }, { key: 'C', content: '' }, { key: 'D', content: '' }],
  correctAnswer: undefined
})

const emit = defineEmits<Emits>()

const options = ref<QuestionOption[]>([
  { key: 'A', content: '' },
  { key: 'B', content: '' },
  { key: 'C', content: '' },
  { key: 'D', content: '' }
])

// 监听外部变化
watch(() => props.modelValue, (newVal) => {
  if (newVal && newVal.length === 4) {
    options.value = [...newVal]
  }
}, { immediate: true })

// 判断是否为正确答案
const isCorrectAnswer = (key: string) => {
  return props.correctAnswer?.key === key
}

// 正确答案key
const correctAnswerKey = computed(() => {
  return props.correctAnswer?.key || ''
})

// 处理正确答案变化
const handleCorrectChange = (index: number) => {
  const newOptions = [...options.value]
  // 重置所有选项
  newOptions.forEach((opt, i) => {
    opt.is_correct = i === index
  })
  options.value = newOptions

  // 发送正确答案更新
  const correctOption = newOptions[index]
  if (correctOption) {
    emit('update:correctAnswer', { key: correctOption.key })
  }
  handleOptionsChange()
}

// 清空选项
const handleClearOption = (index: number) => {
  const option = options.value[index]
  if (option) {
    option.content = ''
  }
  handleOptionsChange()
}

// 选项变化时同步到父组件
const handleOptionsChange = () => {
  emit('update:modelValue', [...options.value])
}

// 暴露验证方法
defineExpose({
  validate: () => {
    const hasContent = options.value.some(opt => opt.content.trim())
    const hasCorrect = options.value.some(opt => opt.is_correct)

    if (!hasContent) {
      return { valid: false, message: '请至少填写一个选项内容' }
    }

    if (!hasCorrect) {
      return { valid: false, message: '请设置正确答案' }
    }

    return { valid: true }
  }
})
</script>

<style scoped>
.choice-editor {
  padding: 16px 0;
}

.options-list h4 {
  margin: 0 0 16px 0;
  font-size: 14px;
  font-weight: 600;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

.option-label {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 80px;
}

.option-label .el-checkbox {
  margin: 0;
}

.answer-preview {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f0f9ff;
  border-radius: 4px;
}

.preview-label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}
</style>
