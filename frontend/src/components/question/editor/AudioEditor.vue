<template>
  <div class="audio-editor">
    <div class="audio-upload">
      <el-upload
        class="audio-uploader"
        :action="uploadUrl"
        :headers="uploadHeaders"
        :show-file-list="false"
        :before-upload="beforeUpload"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        accept="audio/*"
      >
        <el-button
          type="primary"
          :icon="Upload"
        >
          点击上传音频
        </el-button>
        <template #tip>
          <div class="el-upload__tip">
            支持 mp3/wav/ogg 格式，文件大小不超过 10MB
          </div>
        </template>
      </el-upload>

      <div
        v-if="audioUrl"
        class="audio-preview"
      >
        <div class="preview-header">
          <span>音频预览</span>
          <el-button
            link
            type="danger"
            :icon="Delete"
            @click="handleRemoveAudio"
          >
            删除
          </el-button>
        </div>
        <audio
          :src="audioUrl"
          controls
          style="width: 100%; max-width: 500px;"
        >
          您的浏览器不支持音频播放
        </audio>
      </div>
    </div>

    <!-- 或者直接输入URL -->
    <div class="url-input">
      <el-divider>或</el-divider>
      <el-input
        v-model="audioUrl"
        placeholder="或输入音频文件URL"
        @input="handleUrlChange"
      >
        <template #prepend>
          URL
        </template>
      </el-input>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { Upload, Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

interface Props {
  modelValue?: string
}

interface Emits {
  (e: 'update:modelValue', value: string): void
}

const props = defineProps<Props>()

const emit = defineEmits<Emits>()

const audioUrl = ref(props.modelValue || '')

// 上传URL（需要配置实际的API地址）
const uploadUrl = computed(() => {
  // TODO: 从环境变量或配置获取
  return '/api/v1/upload/audio'
})

// 上传请求头
const uploadHeaders = computed(() => {
  const authStore = useAuthStore()
  return {
    Authorization: `Bearer ${authStore.accessToken}`
  }
})

// 监听外部变化
watch(() => props.modelValue, (newVal) => {
  audioUrl.value = newVal || ''
})

// 上传前验证
const beforeUpload = (file: File) => {
  const isAudio = file.type.startsWith('audio/')
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isAudio) {
    ElMessage.error('只能上传音频文件！')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('音频文件大小不能超过 10MB！')
    return false
  }

  return true
}

// 上传成功
const handleUploadSuccess = (response: any) => {
  // 假设返回格式为 { url: '...' }
  if (response.url) {
    audioUrl.value = response.url
    handleUrlChange()
    ElMessage.success('音频上传成功')
  } else {
    ElMessage.error('上传失败，返回格式错误')
  }
}

// 上传失败
const handleUploadError = () => {
  ElMessage.error('音频上传失败')
}

// URL变化处理
const handleUrlChange = () => {
  emit('update:modelValue', audioUrl.value)
}

// 删除音频
const handleRemoveAudio = () => {
  audioUrl.value = ''
  handleUrlChange()
}

// 暴露验证方法
defineExpose({
  validate: () => {
    if (!audioUrl.value) {
      return { valid: false, message: '请上传或输入音频URL' }
    }
    return { valid: true }
  },
  getAudioUrl: () => audioUrl.value
})
</script>

<style scoped>
.audio-editor {
  padding: 16px 0;
}

.audio-uploader {
  text-align: left;
}

.audio-preview {
  margin-top: 16px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 4px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 600;
}

.url-input {
  margin-top: 16px;
}
</style>
