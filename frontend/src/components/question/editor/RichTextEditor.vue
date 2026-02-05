<template>
  <div class="rich-text-editor">
    <!-- 工具栏 -->
    <div class="toolbar">
      <el-button-group>
        <el-button
          :type="isActive.bold ? 'primary' : ''"
          size="small"
          @click="toggleBold"
        >
          <strong>B</strong>
          加粗
        </el-button>
        <el-button
          size="small"
          @click="handleImageUpload"
        >
          <el-icon><Picture /></el-icon>
          图片
        </el-button>
      </el-button-group>
    </div>

    <!-- 编辑区域 -->
    <div
      ref="editorRef"
      class="editor-content"
      contenteditable="true"
      @input="handleInput"
      @blur="handleBlur"
    ></div>

    <!-- 隐藏的文件上传输入 -->
    <input
      ref="fileInputRef"
      type="file"
      accept="image/*"
      style="display: none"
      @change="handleFileChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Picture } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

interface Props {
  modelValue: string
  placeholder?: string
  maxLength?: number
}

interface Emits {
  (e: 'update:modelValue', value: string): void
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '请输入内容...',
  maxLength: undefined
})

const emit = defineEmits<Emits>()

const editorRef = ref<HTMLDivElement>()
const fileInputRef = ref<HTMLInputElement>()
const isActive = computed(() => {
  return {
    bold: document.queryCommandState('bold') === true
  }
})

// 初始化内容
watch(() => props.modelValue, (newVal) => {
  if (editorRef.value && editorRef.value.innerHTML !== newVal) {
    editorRef.value.innerHTML = newVal
  }
}, { immediate: true })

const handleInput = () => {
  const content = editorRef.value?.innerHTML || ''

  // 长度验证
  if (props.maxLength && content.length > props.maxLength) {
    editorRef.value!.innerHTML = content.substring(0, props.maxLength)
    ElMessage.warning(`内容不能超过 ${props.maxLength} 个字符`)
    return
  }

  emit('update:modelValue', content)
}

const handleBlur = () => {
  emit('update:modelValue', editorRef.value?.innerHTML || '')
}

// 切换加粗
const toggleBold = () => {
  document.execCommand('bold', false)
  editorRef.value?.focus()
}

// 处理图片上传
const handleImageUpload = () => {
  fileInputRef.value?.click()
}

const handleFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]

  if (!file) return

  // 验证文件类型
  if (!file.type.startsWith('image/')) {
    ElMessage.error('请上传图片文件')
    return
  }

  // 验证文件大小（5MB）
  if (file.size > 5 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过5MB')
    return
  }

  try {
    // TODO: 上传到服务器，这里先使用DataURL
    const reader = new FileReader()
    reader.onload = (e) => {
      const imgSrc = e.target?.result as string
      document.execCommand('insertImage', false, imgSrc)
      handleInput()
    }
    reader.readAsDataURL(file)

    ElMessage.success('图片添加成功')
  } catch (error) {
    ElMessage.error('图片添加失败')
  }

  // 清空input
  target.value = ''
}

// 暴露方法给父组件
defineExpose({
  focus: () => editorRef.value?.focus(),
  getContent: () => editorRef.value?.innerHTML || '',
  setContent: (content: string) => {
    if (editorRef.value) {
      editorRef.value.innerHTML = content
    }
  }
})
</script>

<style scoped>
.rich-text-editor {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}

.toolbar {
  padding: 8px;
  background: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;
}

.editor-content {
  min-height: 120px;
  padding: 12px;
  background: #fff;
  outline: none;
  line-height: 1.6;
}

.editor-content:empty::before {
  content: attr(placeholder);
  color: #909399;
}

.editor-content img {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 8px 0;
}
</style>
