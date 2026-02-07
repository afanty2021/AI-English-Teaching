<template>
  <el-dialog
    v-model="visible"
    title="语音识别功能提示"
    width="500px"
    :close-on-click-modal="false"
    :show-close="false"
  >
    <div class="unsupported-content">
      <el-result
        icon="warning"
        title="当前浏览器不支持语音识别"
        sub-title="推荐使用以下浏览器获得最佳体验"
      >
        <template #extra>
          <div class="browser-recommendations">
            <div class="browser-item" @click="openBrowserLink('chrome')">
              <el-icon :size="32"><Platform /></el-icon>
              <div class="browser-info">
                <div class="browser-name">Google Chrome</div>
                <div class="browser-desc">推荐 ⭐⭐⭐⭐⭐</div>
              </div>
            </div>
            <div class="browser-item" @click="openBrowserLink('edge')">
              <el-icon :size="32"><Platform /></el-icon>
              <div class="browser-info">
                <div class="browser-name">Microsoft Edge</div>
                <div class="browser-desc">推荐 ⭐⭐⭐⭐⭐</div>
              </div>
            </div>
          </div>
        </template>
      </el-result>

      <div class="alternative-actions">
        <el-divider>替代方案</el-divider>
        <p>您也可以使用以下方式进行对话：</p>
        <ul>
          <li><strong>文本输入</strong>：直接在输入框中输入您的回复</li>
          <li><strong>快捷回复</strong>：使用预设的常用回复选项</li>
        </ul>
      </div>

      <el-button type="primary" @click="handleConfirm">
        我知道了，继续使用文本输入
      </el-button>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Platform } from '@element-plus/icons-vue'

interface Emits {
  (e: 'confirm'): void
}

const emit = defineEmits<Emits>()
const visible = ref(false)

const show = (showDialog: boolean) => {
  visible.value = showDialog
}

const openBrowserLink = (browser: 'chrome' | 'edge') => {
  const urls: Record<string, string> = {
    chrome: 'https://www.google.com/chrome/',
    edge: 'https://www.microsoft.com/edge'
  }
  window.open(urls[browser], '_blank')
}

const handleConfirm = () => {
  visible.value = false
  emit('confirm')
}

defineExpose({ show })
</script>

<style scoped>
.unsupported-content {
  text-align: center;
  padding: 20px 0;
}

.browser-recommendations {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin: 20px 0;
}

.browser-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.browser-item:hover {
  border-color: var(--el-color-primary);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
}

.browser-info {
  text-align: left;
}

.browser-name {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.browser-desc {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 2px;
}

.alternative-actions {
  text-align: left;
  margin: 20px 0;
  padding: 16px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
}

.alternative-actions p {
  margin: 0 0 12px 0;
  color: var(--el-text-color-regular);
}

.alternative-actions ul {
  margin: 0;
  padding-left: 20px;
}

.alternative-actions li {
  margin: 8px 0;
  color: var(--el-text-color-regular);
}
</style>
