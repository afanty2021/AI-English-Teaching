<template>
  <div class="writing-editor">
    <div class="section-header">
      <h4>{{ title }}参考答案</h4>
      <el-tag size="small">
        {{ charCount }} 字符
      </el-tag>
    </div>

    <el-input
      v-model="content"
      type="textarea"
      :rows="6"
      :placeholder="placeholder"
      :maxlength="maxLength"
      show-word-limit
      @input="handleInput"
    />

    <!-- 答案提示 -->
    <div class="answer-hint">
      <el-icon><InfoFilled /></el-icon>
      <span>{{ hint }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { InfoFilled } from '@element-plus/icons-vue'

interface Props {
  modelValue?: string
  type: 'writing' | 'speaking'
  maxLength?: number
}

interface Emits {
  (e: 'update:modelValue', value: string): void
}

const props = withDefaults(defineProps<Props>(), {
  maxLength: 2000
})

const emit = defineEmits<Emits>()

const content = ref(props.modelValue || '')

// 根据类型设置标题和提示
const title = computed(() => {
  return props.type === 'writing' ? '写作' : '口语'
})

const placeholder = computed(() => {
  return props.type === 'writing'
    ? '请输入写作参考答案，可以包括写作要点、范文结构等...'
    : '请输入口语参考答案，可以包括关键表达、示例对话等...'
})

const hint = computed(() => {
  return props.type === 'writing'
    ? '此答案将作为学生答题的参考标准'
    : '此答案将作为学生口语练习的参考范例'
})

// 字符计数
const charCount = computed(() => {
  return content.value.length
})

// 监听外部变化
watch(() => props.modelValue, (newVal) => {
  content.value = newVal || ''
})

const handleInput = () => {
  emit('update:modelValue', content.value)
}

// 暴露验证方法
defineExpose({
  validate: () => {
    if (!content.value.trim()) {
      return { valid: false, message: '请输入参考答案内容' }
    }
    return { valid: true }
  },
  getContent: () => content.value
})
</script>

<style scoped>
.writing-editor {
  padding: 16px 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.answer-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  padding: 8px 12px;
  background: #f0f9ff;
  border-radius: 4px;
  font-size: 13px;
  color: #409eff;
}
</style>
