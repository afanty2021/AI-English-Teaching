<template>
  <div class="reading-editor">
    <!-- 文章编辑区 -->
    <div class="passage-section">
      <div class="section-header">
        <h4>文章内容</h4>
        <el-tag size="small">{{ wordCount }} / 800 词</el-tag>
      </div>
      <el-input
        v-model="passage"
        type="textarea"
        :rows="8"
        placeholder="请输入阅读理解文章内容..."
        :maxlength="8000"
        show-word-limit
        @input="handlePassageChange"
      />
    </div>

    <!-- 文章预览区 -->
    <div v-if="passage" class="passage-preview">
      <div class="preview-header">文章预览</div>
      <div class="preview-content">{{ passage }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'

interface Props {
  modelValue?: string
}

interface Emits {
  (e: 'update:modelValue', value: string): void
}

const props = defineProps<Props>()

const emit = defineEmits<Emits>()

const passage = ref(props.modelValue || '')

// 监听外部变化
watch(() => props.modelValue, (newVal) => {
  passage.value = newVal || ''
})

// 计算词数（简单按空格分割）
const wordCount = computed(() => {
  if (!passage.value) return 0
  const text = passage.value.trim()
  if (!text) return 0
  // 按空格分割计算单词数
  return text.split(/\s+/).length
})

// 文章变化处理
const handlePassageChange = () => {
  const text = passage.value || ''

  // 简单的词数限制验证（约800词）
  const words = text.trim().split(/\s+/)
  if (words.length > 800) {
    ElMessage.warning('文章内容不能超过800个单词')
    // 截断到800词
    passage.value = words.slice(0, 800).join(' ')
  }

  emit('update:modelValue', passage.value)
}

// 暴露验证方法
defineExpose({
  validate: () => {
    if (!passage.value.trim()) {
      return { valid: false, message: '请输入文章内容' }
    }

    if (wordCount.value > 800) {
      return { valid: false, message: '文章内容不能超过800个单词' }
    }

    return { valid: true }
  },
  getPassage: () => passage.value
})
</script>

<style scoped>
.reading-editor {
  padding: 16px 0;
}

.passage-section {
  margin-bottom: 20px;
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

.passage-preview {
  padding: 16px;
  background: #f5f7fa;
  border-radius: 4px;
}

.preview-header {
  font-size: 14px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 12px;
}

.preview-content {
  font-size: 15px;
  line-height: 1.8;
  color: #303133;
  white-space: pre-wrap;
}
</style>
