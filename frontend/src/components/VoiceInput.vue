<template>
  <div class="voice-input-container">
    <!-- 波形显示 -->
    <VoiceWaveform
      v-if="showWaveform"
      ref="waveformRef"
      :show-spectrum="true"
      :show-volume="true"
      :show-vad="true"
      :bar-count="64"
      :vad-threshold="0.3"
      @voice-start="onVoiceStart"
      @voice-end="onVoiceEnd"
      @volume-change="onVolumeChange"
      @vad-change="onVadChange"
    />

    <!-- 主控制按钮 -->
    <div class="voice-button-container">
      <button
        ref="voiceButtonRef"
        class="voice-button"
        :class="{
          'listening': isListening,
          'processing': isProcessing,
          'error': hasError,
          'disabled': isDisabled
        }"
        :disabled="isDisabled || isProcessing"
        @click="handleButtonClick"
        @mousedown="handleMouseDown"
        @mouseup="handleMouseUp"
        @touchstart="handleTouchStart"
        @touchend="handleTouchEnd"
      >
        <!-- 图标 -->
        <div class="button-icon">
          <el-icon
            v-if="!isListening && !isProcessing"
            size="32"
          >
            <Microphone />
          </el-icon>
          <el-icon
            v-else-if="isProcessing"
            size="32"
          >
            <Loading />
          </el-icon>
          <el-icon
            v-else
            size="32"
          >
            <SwitchButton />
          </el-icon>
        </div>

        <!-- 状态文字 -->
        <div class="button-text">
          <span class="primary-text">{{ buttonText }}</span>
          <span
            v-if="secondaryText"
            class="secondary-text"
          >{{ secondaryText }}</span>
        </div>

        <!-- 动画效果 -->
        <div
          v-if="isListening"
          class="button-ripple"
        ></div>
        <div
          v-if="isListening"
          class="button-glow"
        ></div>
      </button>

      <!-- 状态指示器 -->
      <div class="status-indicator">
        <el-tag
          :type="statusTagType"
          :effect="statusEffect"
          size="small"
          round
        >
          <el-icon
            v-if="isProcessing"
            class="status-icon"
          >
            <Loading />
          </el-icon>
          <el-icon
            v-else-if="isListening"
            class="status-icon"
          >
            <Microphone />
          </el-icon>
          <el-icon
            v-else-if="hasError"
            class="status-icon"
          >
            <Warning />
          </el-icon>
          <el-icon
            v-else
            class="status-icon"
          >
            <CircleCheck />
          </el-icon>
          {{ statusText }}
        </el-tag>

        <!-- 置信度显示 -->
        <RecognitionConfidence
          v-if="(isListening || isProcessing) && recognitionConfidence > 0"
          :confidence="recognitionConfidence"
          class="confidence-display"
        />
      </div>

      <!-- 进度条 -->
      <el-progress
        v-if="isProcessing"
        :percentage="processingProgress"
        :show-text="false"
        :stroke-width="4"
        :color="progressColor"
        class="processing-progress"
      />

      <!-- 错误提示 -->
      <el-alert
        v-if="hasError && errorMessage"
        :title="errorMessage"
        type="error"
        :closable="true"
        show-icon
        class="error-alert"
        @close="clearError"
      />

      <!-- 提示信息 -->
      <el-tooltip
        v-if="tooltipText"
        :content="tooltipText"
        placement="top"
      >
        <el-icon class="help-icon">
          <QuestionFilled />
        </el-icon>
      </el-tooltip>
    </div>

    <!-- 设置面板 -->
    <el-drawer
      v-model="showSettings"
      title="语音识别设置"
      direction="rtl"
      :size="settingsDrawerSize"
    >
      <div class="settings-content">
        <!-- 语言选择 -->
        <div class="setting-section">
          <h4>识别语言</h4>
          <el-select
            v-model="selectedLanguage"
            placeholder="选择语言"
            style="width: 100%"
            @change="onLanguageChange"
          >
            <el-option
              v-for="lang in supportedLanguages"
              :key="lang.code"
              :label="lang.name"
              :value="lang.code"
            >
              <span>{{ lang.name }}</span>
              <small style="color: #999; margin-left: 8px">{{ lang.code }}</small>
            </el-option>
          </el-select>
        </div>

        <!-- 引擎选择 -->
        <div class="setting-section">
          <h4>识别引擎</h4>
          <el-radio-group
            v-model="selectedEngine"
            @change="onEngineChange"
          >
            <el-radio label="adaptive">
              智能切换
            </el-radio>
            <el-radio label="webspeech">
              Web Speech API
            </el-radio>
            <el-radio label="cloud">
              云端识别
            </el-radio>
            <el-radio label="offline">
              离线识别
            </el-radio>
          </el-radio-group>
          <p class="setting-hint">
            {{ engineHint }}
          </p>
        </div>

        <!-- 音频设置 -->
        <div class="setting-section">
          <h4>音频设置</h4>
          <div class="setting-item">
            <span>噪音抑制</span>
            <el-switch v-model="audioSettings.noiseReduction" />
          </div>
          <div class="setting-item">
            <span>语音活动检测</span>
            <el-switch v-model="audioSettings.voiceActivityDetection" />
          </div>
          <div class="setting-item">
            <span>音量显示</span>
            <el-switch v-model="audioSettings.volumeIndicator" />
          </div>
        </div>

        <!-- 性能设置 -->
        <div class="setting-section">
          <h4>性能设置</h4>
          <div class="setting-item">
            <span>自动降级</span>
            <el-switch v-model="performanceSettings.autoFallback" />
          </div>
          <div class="setting-item">
            <span>连续识别</span>
            <el-switch v-model="performanceSettings.continuous" />
          </div>
          <div class="setting-item">
            <span>结果缓存</span>
            <el-switch v-model="performanceSettings.enableCache" />
          </div>
        </div>

        <!-- 兼容性信息 -->
        <div class="setting-section">
          <h4>兼容性信息</h4>
          <div class="compatibility-info">
            <div class="info-item">
              <span>浏览器:</span>
              <el-tag
                :type="compatibilityInfo.browserSupported ? 'success' : 'danger'"
                size="small"
              >
                {{ compatibilityInfo.browser }}
              </el-tag>
            </div>
            <div class="info-item">
              <span>兼容性评分:</span>
              <el-tag
                :type="compatibilityInfo.score >= 80 ? 'success' : 'warning'"
                size="small"
              >
                {{ compatibilityInfo.score }}/100
              </el-tag>
            </div>
            <div class="info-item">
              <span>网络质量:</span>
              <el-tag
                :type="compatibilityInfo.networkQuality.type"
                size="small"
              >
                {{ compatibilityInfo.networkQuality.label }}
              </el-tag>
            </div>
          </div>
        </div>

        <!-- 按钮组 -->
        <div class="settings-actions">
          <el-button @click="resetToDefaults">
            恢复默认
          </el-button>
          <el-button
            type="primary"
            @click="saveSettings"
          >
            保存设置
          </el-button>
        </div>
      </div>
    </el-drawer>

    <!-- 设置按钮 -->
    <el-button
      class="settings-button"
      circle
      @click="showSettings = true"
    >
      <el-icon><Setting /></el-icon>
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Microphone,
  SwitchButton,
  Loading,
  Warning,
  CircleCheck,
  Setting,
  QuestionFilled
} from '@element-plus/icons-vue'
import VoiceWaveform from './VoiceWaveform.vue'
import RecognitionConfidence from './RecognitionConfidence.vue'
import { BrowserCompatibility } from '../utils/browserCompatibility'

// Props
interface Props {
  disabled?: boolean
  showWaveform?: boolean
  language?: string
  engine?: 'adaptive' | 'webspeech' | 'cloud' | 'offline'
  continuous?: boolean
  autoStart?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  showWaveform: true,
  language: 'zh-CN',
  engine: 'adaptive',
  continuous: false,
  autoStart: false
})

// Emits
interface Emits {
  (e: 'start', audioData: Float32Array | Blob): void
  (e: 'end', result: string): void
  (e: 'error', error: string): void
  (e: 'volumeChange', volume: number): void
  (e: 'vadChange', isActive: boolean): void
  (e: 'engineChange', engine: string): void
  (e: 'languageChange', language: string): void
}

const emit = defineEmits<Emits>()

// Refs
const waveformRef = ref<InstanceType<typeof VoiceWaveform> | null>(null)
const voiceButtonRef = ref<HTMLButtonElement | null>(null)

// 状态
const isListening = ref(false)
const isProcessing = ref(false)
const hasError = ref(false)
const errorMessage = ref('')
const showSettings = ref(false)
const recognitionConfidence = ref(0) // 语音识别置信度

// 配置
const selectedLanguage = ref(props.language)
const selectedEngine = ref(props.engine)
const continuous = ref(props.continuous)

// 支持的语言
const supportedLanguages = [
  { code: 'zh-CN', name: '中文（简体）' },
  { code: 'zh-TW', name: '中文（繁体）' },
  { code: 'en-US', name: 'English (US)' },
  { code: 'en-GB', name: 'English (UK)' },
  { code: 'ja-JP', name: '日本語' },
  { code: 'ko-KR', name: '한국어' },
  { code: 'fr-FR', name: 'Français' },
  { code: 'es-ES', name: 'Español' },
  { code: 'de-DE', name: 'Deutsch' },
  { code: 'it-IT', name: 'Italiano' },
  { code: 'pt-BR', name: 'Português' },
  { code: 'ru-RU', name: 'Русский' },
  { code: 'ar-SA', name: 'العربية' }
]

// 音频设置
const audioSettings = ref({
  noiseReduction: true,
  voiceActivityDetection: true,
  volumeIndicator: true
})

// 性能设置
const performanceSettings = ref({
  autoFallback: true,
  continuous: false,
  enableCache: true
})

// 进度和统计
const processingProgress = ref(0)
const networkQuality = ref({ bandwidth: 0, latency: 0 })

// 兼容性信息
const compatibilityInfo = ref({
  browser: '',
  browserSupported: false,
  score: 0,
  networkQuality: { type: 'info', label: '未知' }
})

// 计算属性
const isDisabled = computed(() => {
  return props.disabled || isProcessing.value || hasError.value
})

const buttonText = computed(() => {
  if (isProcessing.value) return '识别中...'
  if (isListening.value) return '点击停止'
  if (hasError.value) return '重新开始'
  return '点击说话'
})

const secondaryText = computed(() => {
  if (isListening.value) return '正在监听...'
  if (isProcessing.value) return '正在处理语音...'
  if (hasError.value) return errorMessage.value
  return '按住按钮或点击开始'
})

const statusText = computed(() => {
  if (isProcessing.value) return '处理中'
  if (isListening.value) return '录音中'
  if (hasError.value) return '错误'
  return '就绪'
})

const statusTagType = computed(() => {
  if (isProcessing.value) return 'info'
  if (isListening.value) return 'success'
  if (hasError.value) return 'danger'
  return 'success'
})

const statusEffect = computed(() => {
  return isListening.value || isProcessing.value ? 'dark' : 'light'
})

const progressColor = computed(() => {
  if (isListening.value) return '#67c23a'
  if (isProcessing.value) return '#409EFF'
  return '#909399'
})

const tooltipText = computed(() => {
  if (hasError.value) return '点击查看错误详情'
  if (!compatibilityInfo.value.browserSupported) return '当前浏览器支持有限'
  return ''
})

const engineHint = computed(() => {
  switch (selectedEngine.value) {
    case 'webspeech':
      return '快速响应，但准确率依赖浏览器'
    case 'cloud':
      return '高精度识别，需要网络连接'
    case 'offline':
      return '无需网络，但模型较大'
    case 'adaptive':
      return '智能选择最佳引擎（推荐）'
    default:
      return ''
  }
})

const settingsDrawerSize = computed(() => {
  return window.innerWidth < 768 ? '80%' : '400px'
})

// 方法
const handleButtonClick = async () => {
  if (isListening.value) {
    await stopListening()
  } else {
    await startListening()
  }
}

const handleMouseDown = () => {
  if (voiceButtonRef.value) {
    voiceButtonRef.value.classList.add('pressed')
  }
}

const handleMouseUp = () => {
  if (voiceButtonRef.value) {
    voiceButtonRef.value.classList.remove('pressed')
  }
}

const handleTouchStart = () => {
  handleMouseDown()
}

const handleTouchEnd = () => {
  handleMouseUp()
}

const startListening = async () => {
  try {
    hasError.value = false
    errorMessage.value = ''
    recognitionConfidence.value = 0 // 重置置信度

    // 检查权限
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

    // 初始化音频分析器
    if (waveformRef.value) {
      waveformRef.value.setAudioSource(stream)
    }

    isListening.value = true

    // 模拟置信度更新（实际应该来自语音识别服务）
    const confidenceInterval = setInterval(() => {
      if (!isListening.value && !isProcessing.value) {
        clearInterval(confidenceInterval)
        return
      }
      // 模拟置信度波动（0.5 到 1.0 之间）
      recognitionConfidence.value = 0.5 + Math.random() * 0.5
    }, 500)

    // 如果启用连续识别，设置自动停止
    if (continuous.value) {
      setTimeout(() => {
        stopListening()
        clearInterval(confidenceInterval)
      }, 5000) // 5秒后自动停止
    }

  } catch (error) {
    handleError('无法访问麦克风，请检查权限设置')
  }
}

const stopListening = async () => {
  isListening.value = false

  // 模拟处理延迟
  isProcessing.value = true
  processingProgress.value = 0

  // 模拟处理进度和置信度更新
  const progressInterval = setInterval(() => {
    processingProgress.value += 10
    // 处理过程中置信度逐渐提高
    recognitionConfidence.value = Math.min(0.95, recognitionConfidence.value + 0.05)

    if (processingProgress.value >= 100) {
      clearInterval(progressInterval)
      processingProgress.value = 100

      // 模拟识别结果
      const mockResult = '这是模拟的语音识别结果'
      emit('end', mockResult)
      isProcessing.value = false
      recognitionConfidence.value = 0 // 重置置信度
    }
  }, 100)
}

const onVoiceStart = () => {
  console.log('语音开始检测')
}

const onVoiceEnd = () => {
  console.log('语音结束检测')
  if (!continuous.value) {
    stopListening()
  }
}

const onVolumeChange = (volume: number) => {
  emit('volumeChange', volume)
}

const onVadChange = (isActive: boolean) => {
  emit('vadChange', isActive)
}

const onLanguageChange = (language: string) => {
  emit('languageChange', language)
}

const onEngineChange = (engine: string) => {
  emit('engineChange', engine)
}

const handleError = (message: string) => {
  hasError.value = true
  errorMessage.value = message
  emit('error', message)
}

const clearError = () => {
  hasError.value = false
  errorMessage.value = ''
}

const resetToDefaults = () => {
  selectedLanguage.value = 'zh-CN'
  selectedEngine.value = 'adaptive'
  audioSettings.value = {
    noiseReduction: true,
    voiceActivityDetection: true,
    volumeIndicator: true
  }
  performanceSettings.value = {
    autoFallback: true,
    continuous: false,
    enableCache: true
  }
}

const saveSettings = () => {
  ElMessage.success('设置已保存')
  showSettings.value = false
}

const updateCompatibilityInfo = () => {
  const browser = BrowserCompatibility.detect()
  const result = BrowserCompatibility.getCompatibilityResult()

  compatibilityInfo.value = {
    browser: `${browser.engine} ${browser.version}`,
    browserSupported: result.isSupported,
    score: result.score,
    networkQuality: {
      type: networkQuality.value.latency < 200 ? 'success' : 'warning',
      label: networkQuality.value.latency < 200 ? '良好' : '一般'
    }
  }
}

const testNetworkQuality = async () => {
  try {
    // 简化版网络测试
    const start = performance.now()
    await fetch('/favicon.ico', { cache: 'no-cache' })
    const end = performance.now()

    networkQuality.value = {
      bandwidth: 1000, // 简化值
      latency: end - start
    }

    updateCompatibilityInfo()
  } catch (error) {
    console.warn('网络质量测试失败:', error)
  }
}

// 生命周期
onMounted(() => {
  updateCompatibilityInfo()
  testNetworkQuality()

  if (props.autoStart) {
    startListening()
  }
})

onUnmounted(() => {
  if (isListening.value) {
    stopListening()
  }
})

// 监听属性变化
watch(() => props.language, (newLang) => {
  selectedLanguage.value = newLang
})

watch(() => props.engine, (newEngine) => {
  selectedEngine.value = newEngine
})

watch(() => props.disabled, (newDisabled) => {
  if (newDisabled && isListening.value) {
    stopListening()
  }
})

// 暴露方法
defineExpose({
  startListening,
  stopListening,
  clearError,
  updateCompatibilityInfo
})
</script>

<style scoped>
.voice-input-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  padding: 24px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  max-width: 500px;
  margin: 0 auto;
}

/* 语音按钮容器 */
.voice-button-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  position: relative;
}

/* 主语音按钮 */
.voice-button {
  position: relative;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  border: none;
  background: linear-gradient(135deg, #409EFF 0%, #66b1ff 100%);
  color: white;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.3);
  overflow: hidden;
}

.voice-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(64, 158, 255, 0.4);
}

.voice-button:active:not(:disabled) {
  transform: translateY(0);
}

.voice-button.pressed {
  transform: scale(0.95);
}

.voice-button.listening {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
  box-shadow: 0 4px 16px rgba(103, 194, 58, 0.4);
  animation: pulse-glow 2s infinite;
}

.voice-button.processing {
  background: linear-gradient(135deg, #e6a23c 0%, #ebb563 100%);
  box-shadow: 0 4px 16px rgba(230, 162, 60, 0.4);
}

.voice-button.error {
  background: linear-gradient(135deg, #f56c6c 0%, #ff7875 100%);
  box-shadow: 0 4px 16px rgba(245, 108, 108, 0.4);
}

.voice-button.disabled {
  background: #909399;
  cursor: not-allowed;
  opacity: 0.6;
  box-shadow: none;
}

/* 按钮内容 */
.button-icon {
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
}

.button-text {
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  line-height: 1.2;
}

.primary-text {
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
}

.secondary-text {
  font-size: 11px;
  opacity: 0.9;
  margin-top: 2px;
}

/* 动画效果 */
.button-ripple {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transform: translate(-50%, -50%);
  animation: ripple 2s infinite;
  z-index: 1;
}

.button-glow {
  position: absolute;
  top: -10px;
  left: -10px;
  right: -10px;
  bottom: -10px;
  border-radius: 50%;
  background: linear-gradient(135deg, #409EFF, #66b1ff);
  opacity: 0.2;
  animation: glow-pulse 2s infinite;
  z-index: 1;
}

@keyframes pulse-glow {
  0%, 100% {
    box-shadow: 0 4px 16px rgba(103, 194, 58, 0.4);
  }
  50% {
    box-shadow: 0 4px 24px rgba(103, 194, 58, 0.6);
  }
}

@keyframes ripple {
  0% {
    width: 0;
    height: 0;
    opacity: 1;
  }
  100% {
    width: 200px;
    height: 200px;
    opacity: 0;
  }
}

@keyframes glow-pulse {
  0%, 100% {
    opacity: 0.2;
    transform: scale(1);
  }
  50% {
    opacity: 0.4;
    transform: scale(1.1);
  }
}

/* 状态指示器 */
.status-indicator {
  position: absolute;
  top: -12px;
  right: -12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-icon {
  margin-right: 4px;
}

/* 置信度显示 */
.confidence-display {
  font-size: 11px;
}

/* 进度条 */
.processing-progress {
  width: 200px;
}

/* 错误提示 */
.error-alert {
  max-width: 300px;
}

/* 帮助图标 */
.help-icon {
  color: #909399;
  cursor: help;
  margin-left: 8px;
}

/* 设置按钮 */
.settings-button {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 32px;
  height: 32px;
}

/* 设置面板 */
.settings-content {
  padding: 20px;
}

.setting-section {
  margin-bottom: 24px;
}

.setting-section h4 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 14px;
  font-weight: 600;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #f5f7fa;
}

.setting-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.setting-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
}

.compatibility-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}

.settings-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #f5f7fa;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .voice-input-container {
    padding: 16px;
    gap: 16px;
  }

  .voice-button {
    width: 100px;
    height: 100px;
  }

  .primary-text {
    font-size: 12px;
  }

  .secondary-text {
    font-size: 10px;
  }

  .processing-progress {
    width: 150px;
  }
}
</style>