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
        :aria-label="buttonText"
        tabindex="0"
        role="button"
        @click="handleButtonClick"
        @keydown.enter.prevent="handleKeyPress"
        @keydown.space.prevent="handleKeyPress"
        @mousedown="handleMouseDown"
        @mouseup="handleMouseUp"
        @touchstart.prevent="handleTouchStart"
        @touchend.prevent="handleTouchEnd"
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
import {
  createVoiceRecognition,
  VoiceRecognition,
  VoiceRecognitionCallbacks,
  VoiceRecognitionConfig,
  VoiceRecognitionStatus,
  VoiceRecognitionResult
} from '../utils/voiceRecognition'

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

// 语音识别器
let recognition: VoiceRecognition | null = null
let recognitionConfig: VoiceRecognitionConfig = {
  language: 'zh-CN',
  continuous: false,
  interimResults: true
}

// 音频流引用（用于内存管理）
const audioStream = ref<MediaStream | null>(null)

// 状态
const isListening = ref(false)
const isProcessing = ref(false)
const hasError = ref(false)
const errorMessage = ref('')
const showSettings = ref(false)
const recognitionConfidence = ref(0)
const interimTranscript = ref('') // 临时识别结果
const finalTranscript = ref('') // 最终识别结果

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
let progressInterval: ReturnType<typeof setInterval> | null = null
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
  if (isListening.value) return '松开结束'
  if (hasError.value) return '重新开始'
  return '按住说话'
})

const secondaryText = computed(() => {
  if (isListening.value) return interimTranscript.value || '正在监听...'
  if (isProcessing.value) return '正在处理语音...'
  if (hasError.value) return errorMessage.value
  return '按住按钮开始语音输入'
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
  console.log('[VoiceInput] 🖱️ handleMouseDown 触发')
  if (voiceButtonRef.value) {
    voiceButtonRef.value.classList.add('pressed')
    console.log('[VoiceInput] ✅ 添加 pressed 样式类')
  }
  // 开始语音识别
  console.log('[VoiceInput] 🎤️ 调用 startListening')
  startListening()
}

const handleMouseUp = () => {
  console.log('[VoiceInput] 🖱️📍 handleMouseUp 触发')
  if (voiceButtonRef.value) {
    voiceButtonRef.value.classList.remove('pressed')
    console.log('[VoiceInput] ✅ 移除 pressed 样式类')
  }
  // 停止语音识别
  console.log('[VoiceInput] ⏸️ 调用 stopListening')
  stopListening()
}

const handleTouchStart = () => {
  handleMouseDown()
}

const handleTouchEnd = () => {
  handleMouseUp()
}

// 键盘处理函数
const handleKeyPress = () => {
  if (isDisabled.value || isProcessing.value) return

  if (isListening.value) {
    stopListening()
  } else {
    startListening()
  }
}

const startListening = async () => {
  console.log('[VoiceInput] 🎤️ ===== startListening 开始 =====')
  try {
    hasError.value = false
    errorMessage.value = ''
    recognitionConfidence.value = 0
    interimTranscript.value = ''
    finalTranscript.value = ''

    // 检查浏览器支持
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    console.log('[VoiceInput] 🔍 检查浏览器支持:', !!SpeechRecognition)

    if (!SpeechRecognition) {
      console.log('[VoiceInput] ❌ 浏览器不支持语音识别')
      handleError('您的浏览器不支持语音识别，请使用 Chrome 或 Edge 浏览器')
      return
    }

    console.log('[VoiceInput] 🔍 检查是否已有 recognition 实例:', !!recognition)

    // 初始化语音识别器
    if (!recognition) {
      console.log('[VoiceInput] 🔧 需要初始化 recognition，调用 initVoiceRecognition')
      initVoiceRecognition()
    } else {
      console.log('[VoiceInput] ✅ recognition 已存在，跳过初始化')
    }

    // 检查麦克风权限
    console.log('[VoiceInput] 🎤️ 请求麦克风权限...')
    audioStream.value = await navigator.mediaDevices.getUserMedia({ audio: true })
    console.log('[VoiceInput] ✅ 麦克风权限已获取, stream:', audioStream.value)

    // 设置音频源到波形显示
    if (waveformRef.value && audioStream.value) {
      waveformRef.value.setAudioSource(audioStream.value)
      console.log('[VoiceInput] ✅ 音频已设置到波形显示')
    }

    // 启动语音识别
    console.log('[VoiceInput] 🎙️ 调用 recognition.start()')
    recognition?.start()
    console.log('[VoiceInput] ✅ ===== startListening 完成 =====')

  } catch (error: any) {
    console.error('[VoiceInput] ❌ 启动语音识别失败:', error)
    console.error('[VoiceInput] 错误名称:', error.name)
    console.error('[VoiceInput] 错误信息:', error.message)

    if (error.name === 'NotAllowedError') {
      console.log('[VoiceInput] ❌ 用户拒绝了麦克风权限')
      handleError('未授权使用麦克风，请在浏览器设置中允许麦克风权限')
    } else if (error.name === 'NotFoundError') {
      console.log('[VoiceInput] ❌ 没有找到麦克风设备')
      handleError('未找到麦克风设备，请确保已连接麦克风')
    } else {
      console.log('[VoiceInput] ❌ 其他麦克风错误')
      handleError('无法访问麦克风：' + (error.message || '未知错误'))
    }
  }
}

const stopListening = () => {
  console.log('[VoiceInput] 🛑 ===== stopListening 开始 =====')
  console.log('[VoiceInput] 🔍 recognition 实例:', recognition)
  console.log('[VoiceInput] 🔍 recognition.isListening():', recognition?.isListening())

  if (recognition && recognition.isListening()) {
    console.log('[VoiceInput] 🛑 停止语音识别器')
    recognition?.stop()
  } else {
    console.log('[VoiceInput] ℹ️ recognition 未运行或不存在，无需停止')
  }

  isListening.value = false
  interimTranscript.value = ''
  console.log('[VoiceInput] ✅ ===== stopListening 完成 =====')
}

// 初始化语音识别
const initVoiceRecognition = () => {
  try {
    recognition = createVoiceRecognition(recognitionConfig)

    const callbacks: VoiceRecognitionCallbacks = {
      onStart: () => {
        console.log('[VoiceInput] 语音识别开始')
        isListening.value = true
        emit('start', new Float32Array(0))
      },
      onStop: () => {
        console.log('[VoiceInput] 语音识别停止')
        isListening.value = false
      },
      onResult: (result: VoiceRecognitionResult) => {
        console.log('[VoiceInput] 识别结果:', result)
        handleRecognitionResult(result)
      },
      onInterimResult: (result: VoiceRecognitionResult) => {
        console.log('[VoiceInput] 临时识别结果:', result)
        interimTranscript.value = result.transcript
        recognitionConfidence.value = result.confidence || 0.5
      },
      onError: (error: any) => {
        console.error('[VoiceInput] 识别错误:', error)
        handleError(error.message || '语音识别失败')
      },
      onStatusChange: (status: VoiceRecognitionStatus) => {
        console.log('[VoiceInput] 状态变化:', status)
        if (status === VoiceRecognitionStatus.Error) {
          hasError.value = true
        }
      }
    }

    recognition.on(callbacks)
  } catch (error: any) {
    console.error('[VoiceInput] 初始化语音识别失败:', error)
    handleError('语音识别初始化失败，请检查浏览器支持')
  }
}

// 处理识别结果
const handleRecognitionResult = (result: VoiceRecognitionResult) => {
  // 先清理之前的定时器
  if (progressInterval) {
    clearInterval(progressInterval)
    progressInterval = null
  }

  if (result.isFinal) {
    finalTranscript.value = result.transcript
    interimTranscript.value = ''

    isProcessing.value = true
    processingProgress.value = 0

    // 模拟处理进度
    progressInterval = setInterval(() => {
      processingProgress.value += 20

      if (processingProgress.value >= 100) {
        clearInterval(progressInterval)
        progressInterval = null
        processingProgress.value = 100

        emit('end', result.transcript)

        isProcessing.value = false
        recognitionConfidence.value = 0
        processingProgress.value = 0
      }
    }, 100)
  }
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
  console.log('[VoiceInput] 🏗️ ===== onMounted 组件挂载 =====')
  console.log('[VoiceInput] 📋 props:', {
    disabled: props.disabled,
    showWaveform: props.showWaveform,
    language: props.language,
    engine: props.engine,
    continuous: props.continuous,
    autoStart: props.autoStart
  })

  updateCompatibilityInfo()
  testNetworkQuality()

  if (props.autoStart) {
    console.log('[VoiceInput] 🚀 autoStart=true，自动启动语音识别')
    startListening()
  } else {
    console.log('[VoiceInput] ℹ️ autoStart=false，等待用户操作')
  }
  console.log('[VoiceInput] ✅ ===== onMounted 完成 =====')
})

onUnmounted(() => {
  // 清理定时器
  if (progressInterval) {
    clearInterval(progressInterval)
    progressInterval = null
  }

  // 释放音频流
  if (audioStream.value) {
    audioStream.value.getTracks().forEach(track => track.stop())
    audioStream.value = null
  }

  // 销毁识别器（这会触发 onStop 回调）
  recognition?.destroy()
})

// 监听属性变化
watch(() => props.language, (newLang) => {
  selectedLanguage.value = newLang
  recognitionConfig.language = newLang

  if (recognition) {
    recognition.updateConfig({ language: newLang })
  }
})

watch(() => props.engine, (newEngine) => {
  selectedEngine.value = newEngine
})

watch(() => props.continuous, (newVal) => {
  continuous.value = newVal
  if (recognition) {
    recognition.updateConfig({ continuous: newVal })
  }
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