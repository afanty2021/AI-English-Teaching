<template>
  <div class="voice-waveform-container">
    <div class="waveform" ref="waveformRef">
      <div
        v-for="(bar, index) in waveformBars"
        :key="index"
        class="waveform-bar"
        :class="{ active: bar.isActive }"
        :style="{
          height: `${bar.height}px`,
          backgroundColor: bar.isActive ? activeColor : inactiveColor,
          opacity: bar.opacity
        }"
      ></div>
    </div>

    <!-- 音频频谱分析 -->
    <div class="spectrum-analyzer" v-if="showSpectrum">
      <div
        v-for="(freq, index) in frequencyData"
        :key="index"
        class="spectrum-bar"
        :style="{ height: `${freq}px` }"
      ></div>
    </div>

    <!-- 音量指示器 -->
    <div class="volume-indicator" v-if="showVolume">
      <div class="volume-meter">
        <div
          class="volume-fill"
          :style="{ width: `${volumeLevel}%` }"
          :class="volumeClass"
        ></div>
      </div>
      <div class="volume-label">{{ volumeLabel }}</div>
    </div>

    <!-- 语音活动指示 -->
    <div class="voice-activity" v-if="showVAD">
      <div
        class="vad-indicator"
        :class="{ active: isVoiceActive }"
      >
        <div class="pulse-ring" v-if="isVoiceActive"></div>
        <div class="vad-dot"></div>
      </div>
      <div class="vad-label">{{ vadLabel }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

// Props
interface Props {
  audioContext?: AudioContext
  analyserNode?: AnalyserNode
  showSpectrum?: boolean
  showVolume?: boolean
  showVAD?: boolean
  barCount?: number
  smoothing?: number
  minBarHeight?: number
  maxBarHeight?: number
  vadThreshold?: number
}

const props = withDefaults(defineProps<Props>(), {
  showSpectrum: true,
  showVolume: true,
  showVAD: true,
  barCount: 64,
  smoothing: 0.8,
  minBarHeight: 2,
  maxBarHeight: 100,
  vadThreshold: 30
})

// Emits
interface Emits {
  (e: 'voiceStart'): void
  (e: 'voiceEnd'): void
  (e: 'volumeChange', volume: number): void
  (e: 'vadChange', isActive: boolean): void
}

const emit = defineEmits<Emits>()

// Refs
const waveformRef = ref<HTMLDivElement | null>(null)
const audioContext = ref<AudioContext | null>(props.audioContext || null)
const analyserNode = ref<AnalyserNode | null>(props.analyserNode || null)
const animationFrameId = ref<number | null>(null)

// 波形数据
const waveformBars = ref<Array<{ height: number; isActive: boolean; opacity: number }>>([])
const frequencyData = ref<number[]>([])

// 音量数据
const volumeLevel = ref(0)
const volumeData = ref<number[]>([])

// 语音活动检测
const isVoiceActive = ref(false)
const vadHistory = ref<boolean[]>([])

// 颜色配置
const activeColor = ref('#409EFF') // Element Plus 主色
const inactiveColor = ref('#E4E7ED') // Element Plus 边框色

// 计算属性
const volumeLabel = computed(() => {
  if (volumeLevel.value === 0) return '静音'
  if (volumeLevel.value < 30) return '低'
  if (volumeLevel.value < 70) return '中'
  return '高'
})

const volumeClass = computed(() => {
  if (volumeLevel.value < 30) return 'volume-low'
  if (volumeLevel.value < 70) return 'volume-medium'
  return 'volume-high'
})

const vadLabel = computed(() => {
  return isVoiceActive.value ? '正在说话' : '等待语音'
})

// 初始化波形数据
const initializeWaveform = () => {
  waveformBars.value = Array.from({ length: props.barCount }, () => ({
    height: props.minBarHeight,
    isActive: false,
    opacity: 0.3
  }))

  frequencyData.value = Array.from({ length: props.barCount }, () => 0)
}

// 更新波形数据
const updateWaveform = () => {
  if (!analyserNode.value) return

  const bufferLength = analyserNode.value.frequencyBinCount
  const dataArray = new Uint8Array(bufferLength)
  analyserNode.value.getByteFrequencyData(dataArray)

  // 计算频域数据
  const step = Math.floor(bufferLength / props.barCount)
  for (let i = 0; i < props.barCount; i++) {
    const start = i * step
    const end = start + step
    const slice = dataArray.slice(start, end)

    // 计算平均值
    const average = slice.reduce((sum, value) => sum + value, 0) / slice.length
    const normalizedValue = (average / 255) * props.maxBarHeight

    // 应用平滑
    const currentBar = waveformBars.value[i]
    const smoothedHeight = currentBar.height * (1 - props.smoothing) + normalizedValue * props.smoothing

    // 更新波形条
    waveformBars.value[i] = {
      height: Math.max(props.minBarHeight, smoothedHeight),
      isActive: smoothedHeight > props.vadThreshold,
      opacity: 0.3 + (smoothedHeight / props.maxBarHeight) * 0.7
    }

    // 更新频谱数据
    frequencyData.value[i] = smoothedHeight
  }

  // 检测语音活动
  detectVoiceActivity(dataArray)
}

// 检测语音活动
const detectVoiceActivity = (dataArray: Uint8Array) => {
  // 计算当前音量
  const currentVolume = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length
  volumeLevel.value = Math.round((currentVolume / 255) * 100)

  // 更新音量历史
  volumeData.value.push(currentVolume)
  if (volumeData.value.length > 10) {
    volumeData.value.shift()
  }

  // VAD 检测
  const isActive = currentVolume > props.vadThreshold
  vadHistory.value.push(isActive)

  // 保持历史记录在合理范围内
  if (vadHistory.value.length > 5) {
    vadHistory.value.shift()
  }

  // 计算平均状态，减少误检
  const avgIsActive = vadHistory.value.reduce((sum, active) => sum + (active ? 1 : 0), 0) / vadHistory.value.length

  if (avgIsActive > 0.5 && !isVoiceActive.value) {
    isVoiceActive.value = true
    emit('voiceStart')
  } else if (avgIsActive < 0.5 && isVoiceActive.value) {
    isVoiceActive.value = false
    emit('voiceEnd')
  }

  // 发送事件
  emit('volumeChange', volumeLevel.value)
  emit('vadChange', isVoiceActive.value)
}

// 动画循环
const animate = () => {
  updateWaveform()
  animationFrameId.value = requestAnimationFrame(animate)
}

// 开始/停止动画
const startAnimation = () => {
  if (animationFrameId.value) {
    cancelAnimationFrame(animationFrameId.value)
  }
  animate()
}

const stopAnimation = () => {
  if (animationFrameId.value) {
    cancelAnimationFrame(animationFrameId.value)
    animationFrameId.value = null
  }
}

// 设置音频源
const setAudioSource = (stream: MediaStream) => {
  if (!audioContext.value) {
    audioContext.value = new AudioContext()
  }

  // 创建分析节点
  analyserNode.value = audioContext.value.createAnalyser()
  analyserNode.value.fftSize = 2048
  analyserNode.value.smoothingTimeConstant = props.smoothing

  // 连接音频源
  const source = audioContext.value.createMediaStreamSource(stream)
  source.connect(analyserNode.value)

  // 开始动画
  startAnimation()
}

// 重置波形
const resetWaveform = () => {
  initializeWaveform()
  volumeLevel.value = 0
  isVoiceActive.value = false
  vadHistory.value = []
}

// 销毁
const cleanup = () => {
  stopAnimation()

  if (audioContext.value && audioContext.value.state !== 'closed') {
    audioContext.value.close()
  }
}

// 生命周期
onMounted(() => {
  initializeWaveform()

  if (props.analyserNode) {
    startAnimation()
  }
})

onUnmounted(() => {
  cleanup()
})

// 暴露方法
defineExpose({
  setAudioSource,
  resetWaveform,
  startAnimation,
  stopAnimation,
  cleanup
})

// 监听属性变化
watch(() => props.analyserNode, (newAnalyser) => {
  if (newAnalyser) {
    startAnimation()
  } else {
    stopAnimation()
  }
})
</script>

<style scoped>
.voice-waveform-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

/* 波形显示 */
.waveform {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 120px;
  width: 100%;
  max-width: 400px;
  padding: 10px;
  background: white;
  border-radius: 6px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.waveform-bar {
  flex: 1;
  min-width: 3px;
  border-radius: 2px;
  transition: all 0.1s ease;
  transform-origin: bottom;
}

.waveform-bar.active {
  transform: scaleY(1.1);
  box-shadow: 0 0 8px rgba(64, 158, 255, 0.5);
}

/* 频谱分析器 */
.spectrum-analyzer {
  display: flex;
  align-items: flex-end;
  gap: 1px;
  height: 60px;
  width: 100%;
  max-width: 400px;
  padding: 10px;
  background: white;
  border-radius: 6px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.spectrum-bar {
  flex: 1;
  min-width: 2px;
  background: linear-gradient(to top, #409EFF, #66b1ff);
  border-radius: 1px;
  transition: height 0.1s ease;
}

/* 音量指示器 */
.volume-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  width: 100%;
  max-width: 200px;
}

.volume-meter {
  width: 100%;
  height: 8px;
  background: #e4e7ed;
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.volume-fill {
  height: 100%;
  transition: width 0.2s ease, background-color 0.2s ease;
  border-radius: 4px;
}

.volume-low {
  background: linear-gradient(90deg, #67c23a, #95de64);
}

.volume-medium {
  background: linear-gradient(90deg, #e6a23c, #ffd666);
}

.volume-high {
  background: linear-gradient(90deg, #f56c6c, #ff7875);
}

.volume-label {
  font-size: 12px;
  color: #606266;
  font-weight: 500;
}

/* 语音活动指示 */
.voice-activity {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.vad-indicator {
  position: relative;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.vad-dot {
  width: 12px;
  height: 12px;
  background: #909399;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.vad-indicator.active .vad-dot {
  background: #67c23a;
  transform: scale(1.2);
  box-shadow: 0 0 12px rgba(103, 194, 58, 0.6);
}

.pulse-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 2px solid #67c23a;
  border-radius: 50%;
  animation: pulse 1.5s ease-out infinite;
}

@keyframes pulse {
  0% {
    transform: scale(0.8);
    opacity: 1;
  }
  100% {
    transform: scale(1.4);
    opacity: 0;
  }
}

.vad-label {
  font-size: 12px;
  color: #606266;
  font-weight: 500;
  text-align: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .voice-waveform-container {
    padding: 16px;
  }

  .waveform,
  .spectrum-analyzer {
    max-width: 300px;
  }

  .volume-indicator {
    max-width: 150px;
  }
}
</style>