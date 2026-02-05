<template>
  <div class="translation-editor">
    <div class="translation-content">
      <div class="section-header">
        <h4>翻译内容设置</h4>
      </div>

      <!-- 原文 -->
      <div class="field-group">
        <label class="field-label">原文 <span class="required">*</span></label>
        <el-input
          v-model="sourceText"
          type="textarea"
          :rows="3"
          placeholder="请输入需要翻译的原文内容..."
          @input="handleSourceChange"
        />
      </div>

      <!-- 参考译文 -->
      <div class="field-group">
        <label class="field-label">参考译文</label>
        <el-input
          v-model="targetText"
          type="textarea"
          :rows="3"
          placeholder="请输入参考译文..."
          @input="handleTargetChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

interface Props {
  sourceTextValue?: string
  targetTextValue?: string
}

interface Emits {
  (e: 'update:sourceText', value: string): void
  (e: 'update:targetText', value: string): void
}

const props = defineProps<Props>()

const emit = defineEmits<Emits>()

const sourceText = ref(props.sourceTextValue || '')
const targetText = ref(props.targetTextValue || '')

// 监听外部变化
watch(() => props.sourceTextValue, (newVal) => {
  sourceText.value = newVal || ''
})

watch(() => props.targetTextValue, (newVal) => {
  targetText.value = newVal || ''
})

const handleSourceChange = () => {
  emit('update:sourceText', sourceText.value)
}

const handleTargetChange = () => {
  emit('update:targetText', targetText.value)
}

// 获取正确答案对象
const getCorrectAnswer = () => {
  return {
    source: sourceText.value,
    target: targetText.value
  }
}

// 暴露验证方法
defineExpose({
  validate: () => {
    if (!sourceText.value.trim()) {
      return { valid: false, message: '请输入原文内容' }
    }
    return { valid: true }
  },
  getCorrectAnswer
})
</script>

<style scoped>
.translation-editor {
  padding: 16px 0;
}

.translation-content h4 {
  margin: 0 0 16px 0;
  font-size: 14px;
  font-weight: 600;
}

.field-group {
  margin-bottom: 20px;
}

.field-label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.required {
  color: #f56c6c;
}
</style>
