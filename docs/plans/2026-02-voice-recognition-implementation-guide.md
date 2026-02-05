# 语音识别优化快速实施指南

> **创建时间**: 2026-02-05
> **适用对象**: 开发团队
> **目标**: 10天内完成语音识别优化

---

## 🚀 快速开始

### 第一步: 环境准备

```bash
# 1. 确保Node.js版本≥18
node --version

# 2. 安装依赖
cd frontend
npm install

# 3. 检查当前语音识别功能
npm run dev
# 访问 http://localhost:5173/student/conversation
```

### 第二步: 识别当前问题

```bash
# 运行Lighthouse审计
npx lighthouse http://localhost:5173/student/conversation --view

# 检查浏览器兼容性
# 打开Chrome, Firefox, Safari, Edge分别测试
```

---

## 📝 核心代码示例

### 1. 浏览器兼容性增强

#### 1.1 创建BrowserCompatibility类

**文件**: `frontend/src/utils/browserCompatibility.ts`

```typescript
/**
 * 浏览器兼容性检测
 */
export interface BrowserInfo {
  engine: 'chrome' | 'firefox' | 'safari' | 'edge' | 'unknown'
  version: string
  webSpeechSupported: boolean
  webAudioSupported: boolean
  wasmSupported: boolean
}

export class BrowserCompatibility {
  /**
   * 检测当前浏览器信息
   */
  static detect(): BrowserInfo {
    const ua = navigator.userAgent

    // 检测引擎类型
    let engine: BrowserInfo['engine'] = 'unknown'
    if (/Chrome/.test(ua) && /Google Inc/.test(navigator.vendor)) {
      engine = 'chrome'
    } else if (/Firefox/.test(ua)) {
      engine = 'firefox'
    } else if (/Safari/.test(ua) && /Apple Computer/.test(navigator.vendor)) {
      engine = 'safari'
    } else if (/Edg/.test(ua)) {
      engine = 'edge'
    }

    // 获取版本号
    const version = this.getVersion(ua)

    return {
      engine,
      version,
      webSpeechSupported: this.checkWebSpeechSupport(),
      webAudioSupported: this.checkWebAudioSupport(),
      wasmSupported: this.checkWasmSupport()
    }
  }

  /**
   * 检查Web Speech API支持
   */
  private static checkWebSpeechSupport(): boolean {
    return !!(
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition
    )
  }

  /**
   * 检查Web Audio API支持
   */
  private static checkWebAudioSupport(): boolean {
    return !!(window.AudioContext || (window as any).webkitAudioContext)
  }

  /**
   * 检查WASM支持
   */
  private static checkWasmSupport(): boolean {
    return typeof WebAssembly === 'object'
  }

  /**
   * 提取浏览器版本
   */
  private static getVersion(ua: string): string {
    const match = ua.match(/(chrome|firefox|safari|edg)\/(\d+)/i)
    return match ? match[2] : 'unknown'
  }

  /**
   * 获取兼容性评分 (0-100)
   */
  static getCompatibilityScore(browser: BrowserInfo): number {
    let score = 0

    if (browser.webSpeechSupported) score += 40
    if (browser.webAudioSupported) score += 30
    if (browser.wasmSupported) score += 20
    if (browser.engine !== 'unknown') score += 10

    return score
  }
}

/**
 * 检查浏览器是否支持语音识别
 */
export function isVoiceRecognitionSupported(): boolean {
  const browser = BrowserCompatibility.detect()
  return browser.webSpeechSupported
}

/**
 * 获取浏览器信息
 */
export function getBrowserInfo(): BrowserInfo {
  return BrowserCompatibility.detect()
}
```

#### 1.2 在VoiceRecognition中集成

**文件**: `frontend/src/utils/voiceRecognition.ts` (修改)

```typescript
import { BrowserCompatibility, getBrowserInfo } from './browserCompatibility'

export class VoiceRecognition {
  private recognition: any = null
  private status: VoiceRecognitionStatus = VoiceRecognitionStatus.Idle
  private callbacks: VoiceRecognitionCallbacks = {}
  private config: VoiceRecognitionConfig = {}
  private browserInfo = getBrowserInfo()

  constructor(config: VoiceRecognitionConfig = {}) {
    this.config = {
      language: 'en-US',
      continuous: false,
      interimResults: true,
      maxAlternatives: 1,
      ...config
    }

    // 检查浏览器兼容性
    const score = BrowserCompatibility.getCompatibilityScore(this.browserInfo)
    if (score < 50) {
      this.setStatus(VoiceRecognitionStatus.Error)
      this.triggerError({
        code: 'browser_incompatible',
        message: `当前浏览器兼容性问题 (评分: ${score}/100)，建议使用Chrome或Firefox`
      })
      return
    }

    this.initRecognition()
  }

  /**
   * 初始化语音识别（支持降级）
   */
  private initRecognition() {
    // 优先使用Web Speech API
    if (this.browserInfo.webSpeechSupported) {
      this.initWebSpeechAPI()
    } else {
      // 降级到其他方案
      this.setStatus(VoiceRecognitionStatus.Error)
      this.triggerError({
        code: 'not_supported',
        message: '您的浏览器不支持语音识别，建议升级到最新版本'
      })
    }
  }

  /**
   * 初始化Web Speech API
   */
  private initWebSpeechAPI() {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition

    if (!SpeechRecognition) {
      this.setStatus(VoiceRecognitionStatus.Error)
      this.triggerError({
        code: 'not_supported',
        message: '您的浏览器不支持语音识别功能'
      })
      return
    }

    try {
      this.recognition = new SpeechRecognition()
      this.setupRecognition()
    } catch (error) {
      this.setStatus(VoiceRecognitionStatus.Error)
      this.triggerError({
        code: 'init_failed',
        message: '语音识别初始化失败，请检查麦克风权限'
      })
    }
  }

  /**
   * 配置语音识别事件
   */
  private setupRecognition() {
    const recognition = this.recognition

    recognition.lang = this.config.language || 'en-US'
    recognition.continuous = this.config.continuous || false
    recognition.interimResults = this.config.interimResults || true
    recognition.maxAlternatives = this.config.maxAlternatives || 1

    // 开始识别
    recognition.onstart = () => {
      this.setStatus(VoiceRecognitionStatus.Listening)
      this.callbacks.onStart?.()
    }

    // 识别结束
    recognition.onend = () => {
      if (this.status === VoiceRecognitionStatus.Listening) {
        this.setStatus(VoiceRecognitionStatus.Idle)
        this.callbacks.onStop?.()
      }
    }

    // 获取结果
    recognition.onresult = (event: any) => {
      const last = event.results.length - 1
      const result = event.results[last]

      const recognitionResult: VoiceRecognitionResult = {
        transcript: result[0].transcript,
        isFinal: result.isFinal,
        confidence: result[0].confidence
      }

      if (result.isFinal) {
        this.callbacks.onResult?.(recognitionResult)
      } else {
        this.callbacks.onInterimResult?.(recognitionResult)
      }
    }

    // 错误处理
    recognition.onerror = (event: any) => {
      this.handleRecognitionError(event)
    }
  }
}
```

### 2. 语音质量增强

#### 2.1 创建AudioEnhancer类

**文件**: `frontend/src/utils/audioEnhancer.ts`

```typescript
/**
 * 音频增强工具
 */
export class AudioEnhancer {
  private audioContext: AudioContext | null = null
  private analyser: AnalyserNode | null = null
  private gainNode: GainNode | null = null

  constructor() {
    this.initAudioContext()
  }

  /**
   * 初始化音频上下文
   */
  private initAudioContext() {
    try {
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
      this.analyser = this.audioContext.createAnalyser()
      this.gainNode = this.audioContext.createGain()

      this.analyser.fftSize = 512
      this.analyser.smoothingTimeConstant = 0.8
    } catch (error) {
      console.error('AudioContext初始化失败:', error)
    }
  }

  /**
   * 增强音频流
   */
  async enhanceStream(stream: MediaStream): Promise<MediaStream> {
    if (!this.audioContext || !this.analyser || !this.gainNode) {
      console.warn('AudioContext未初始化，返回原始流')
      return stream
    }

    try {
      // 创建噪音抑制器
      const noiseSuppressor = this.audioContext.createDynamicsCompressor()
      noiseSuppressor.threshold.setValueAtTime(-50, this.audioContext.currentTime)
      noiseSuppressor.knee.setValueAtTime(40, this.audioContext.currentTime)
      noiseSuppressor.ratio.setValueAtTime(12, this.audioContext.currentTime)
      noiseSuppressor.attack.setValueAtTime(0, this.audioContext.currentTime)
      noiseSuppressor.release.setValueAtTime(0.25, this.audioContext.currentTime)

      // 创建高通滤波器（去除低频噪音）
      const highpassFilter = this.audioContext.createBiquadFilter()
      highpassFilter.type = 'highpass'
      highpassFilter.frequency.setValueAtTime(80, this.audioContext.currentTime)

      // 创建低通滤波器（去除高频噪音）
      const lowpassFilter = this.audioContext.createBiquadFilter()
      lowpassFilter.type = 'lowpass'
      lowpassFilter.frequency.setValueAtTime(8000, this.audioContext.currentTime)

      // 连接音频处理图
      const source = this.audioContext.createMediaStreamSource(stream)
      source.connect(highpassFilter)
      highpassFilter.connect(lowpassFilter)
      lowpassFilter.connect(noiseSuppressor)
      noiseSuppressor.connect(this.analyser)
      this.analyser.connect(this.gainNode)
      this.gainNode.connect(this.audioContext.destination)

      console.log('音频流增强完成')
      return stream
    } catch (error) {
      console.error('音频流增强失败:', error)
      return stream
    }
  }

  /**
   * 检测语音活动
   */
  async detectVoiceActivity(stream: MediaStream): Promise<boolean> {
    if (!this.audioContext || !this.analyser) {
      return false
    }

    return new Promise((resolve) => {
      try {
        const source = this.audioContext.createMediaStreamSource(stream)
        source.connect(this.analyser)

        const dataArray = new Uint8Array(this.analyser.frequencyBinCount)

        const check = () => {
          this.analyser!.getByteFrequencyData(dataArray)
          const average = dataArray.reduce((a, b) => a + b) / dataArray.length

          // 动态阈值 (可根据环境调整)
          const threshold = 30
          resolve(average > threshold)
        }

        check()
      } catch (error) {
        console.error('语音活动检测失败:', error)
        resolve(false)
      }
    })
  }

  /**
   * 获取当前音量级别 (0-100)
   */
  getVolumeLevel(stream: MediaStream): number {
    if (!this.audioContext || !this.analyser) {
      return 0
    }

    try {
      const source = this.audioContext.createMediaStreamSource(stream)
      source.connect(this.analyser)

      const dataArray = new Uint8Array(this.analyser.frequencyBinCount)
      this.analyser.getByteFrequencyData(dataArray)

      const sum = dataArray.reduce((a, b) => a + b)
      const average = sum / dataArray.length

      // 转换为百分比
      return Math.min(100, Math.round((average / 255) * 100))
    } catch (error) {
      console.error('音量检测失败:', error)
      return 0
    }
  }

  /**
   * 检查麦克风权限
   */
  async checkMicrophonePermission(): Promise<boolean> {
    try {
      const result = await navigator.permissions.query({ name: 'microphone' as PermissionName })
      return result.state === 'granted'
    } catch (error) {
      console.error('权限检查失败:', error)
      return false
    }
  }

  /**
   * 请求麦克风权限
   */
  async requestMicrophonePermission(): Promise<boolean> {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      stream.getTracks().forEach(track => track.stop()) // 立即停止
      return true
    } catch (error) {
      console.error('麦克风权限请求失败:', error)
      return false
    }
  }

  /**
   * 销毁资源
   */
  destroy() {
    if (this.audioContext) {
      this.audioContext.close()
      this.audioContext = null
    }
    this.analyser = null
    this.gainNode = null
  }
}

/**
 * 创建音频增强器实例
 */
export function createAudioEnhancer(): AudioEnhancer {
  return new AudioEnhancer()
}
```

### 3. 性能监控

#### 3.1 创建PerformanceMonitor类

**文件**: `frontend/src/utils/performanceMonitor.ts`

```typescript
/**
 * 语音识别性能监控
 */
export interface RecognitionMetrics {
  accuracy: number
  latency: number
  errorRate: number
  usageCount: number
  lastUsed: Date
}

export class PerformanceMonitor {
  private metrics: RecognitionMetrics = {
    accuracy: 0,
    latency: 0,
    errorRate: 0,
    usageCount: 0,
    lastUsed: new Date()
  }

  private latencyHistory: number[] = []
  private accuracyHistory: number[] = []
  private readonly maxHistorySize = 100

  /**
   * 记录一次识别
   */
  trackRecognition(
    startTime: number,
    endTime: number,
    isSuccessful: boolean,
    confidence: number = 0
  ): void {
    const latency = endTime - startTime
    const now = new Date()

    // 更新使用次数
    this.metrics.usageCount++

    // 更新延迟
    this.metrics.latency = latency
    this.latencyHistory.push(latency)
    if (this.latencyHistory.length > this.maxHistorySize) {
      this.latencyHistory.shift()
    }

    // 更新准确率
    if (isSuccessful) {
      const newAccuracy = (this.metrics.accuracy * (this.metrics.usageCount - 1) + confidence) / this.metrics.usageCount
      this.metrics.accuracy = newAccuracy
      this.accuracyHistory.push(confidence)
      if (this.accuracyHistory.length > this.maxHistorySize) {
        this.accuracyHistory.shift()
      }
    } else {
      const newErrorRate = (this.metrics.errorRate * (this.metrics.usageCount - 1) + 1) / this.metrics.usageCount
      this.metrics.errorRate = newErrorRate
    }

    // 更新最后使用时间
    this.metrics.lastUsed = now
  }

  /**
   * 获取性能指标
   */
  getMetrics(): RecognitionMetrics {
    return { ...this.metrics }
  }

  /**
   * 获取延迟统计
   */
  getLatencyStats(): { min: number; max: number; avg: number; p95: number } {
    if (this.latencyHistory.length === 0) {
      return { min: 0, max: 0, avg: 0, p95: 0 }
    }

    const sorted = [...this.latencyHistory].sort((a, b) => a - b)
    const sum = sorted.reduce((a, b) => a + b, 0)

    return {
      min: sorted[0],
      max: sorted[sorted.length - 1],
      avg: Math.round(sum / sorted.length),
      p95: sorted[Math.floor(sorted.length * 0.95)]
    }
  }

  /**
   * 获取准确率统计
   */
  getAccuracyStats(): { min: number; max: number; avg: number } {
    if (this.accuracyHistory.length === 0) {
      return { min: 0, max: 0, avg: 0 }
    }

    const sorted = [...this.accuracyHistory].sort((a, b) => a - b)
    const sum = sorted.reduce((a, b) => a + b, 0)

    return {
      min: sorted[0],
      max: sorted[sorted.length - 1],
      avg: Math.round((sum / sorted.length) * 100) / 100
    }
  }

  /**
   * 重置统计
   */
  reset(): void {
    this.metrics = {
      accuracy: 0,
      latency: 0,
      errorRate: 0,
      usageCount: 0,
      lastUsed: new Date()
    }
    this.latencyHistory = []
    this.accuracyHistory = []
  }

  /**
   * 导出性能报告
   */
  exportReport(): string {
    const latencyStats = this.getLatencyStats()
    const accuracyStats = this.getAccuracyStats()

    return `
语音识别性能报告
================
使用次数: ${this.metrics.usageCount}
最后使用: ${this.metrics.lastUsed.toLocaleString()}

延迟统计:
  平均: ${latencyStats.avg}ms
  最小: ${latencyStats.min}ms
  最大: ${latencyStats.max}ms
  95%分位: ${latencyStats.p95}ms

准确率统计:
  平均: ${accuracyStats.avg}%
  最低: ${accuracyStats.min}%
  最高: ${accuracyStats.max}%

错误率: ${Math.round(this.metrics.errorRate * 100)}%
`
  }
}

/**
 * 创建性能监控器实例
 */
export function createPerformanceMonitor(): PerformanceMonitor {
  return new PerformanceMonitor()
}
```

### 4. 自适应语音识别

#### 4.1 创建AdaptiveVoiceRecognition类

**文件**: `frontend/src/utils/adaptiveVoiceRecognition.ts`

```typescript
import { VoiceRecognition } from './voiceRecognition'
import { BrowserCompatibility } from './browserCompatibility'
import { AudioEnhancer } from './audioEnhancer'
import { PerformanceMonitor } from './performanceMonitor'

export type RecognitionEngineType = 'webspeech' | 'cloud' | 'offline'

export interface EngineInfo {
  type: RecognitionEngineType
  name: string
  accuracy: number
  latency: number
  cost: number
  offline: boolean
}

/**
 * 自适应语音识别引擎
 */
export class AdaptiveVoiceRecognition {
  private engines = new Map<RecognitionEngineType, any>()
  private currentEngine: any = null
  private currentEngineType: RecognitionEngineType | null = null
  private browserInfo = BrowserCompatibility.detect()
  private audioEnhancer = new AudioEnhancer()
  private performanceMonitor = new PerformanceMonitor()

  constructor() {
    this.initializeEngines()
  }

  /**
   * 初始化所有可用引擎
   */
  private async initializeEngines(): Promise<void> {
    // 1. Web Speech API引擎
    if (this.browserInfo.webSpeechSupported) {
      this.engines.set('webspeech', {
        type: 'webspeech' as RecognitionEngineType,
        init: () => new VoiceRecognition(),
        name: 'Web Speech API'
      })
    }

    // 2. 云端STT引擎 (待实现)
    this.engines.set('cloud', {
      type: 'cloud' as RecognitionEngineType,
      init: () => null, // 待实现
      name: 'Cloud STT'
    })

    // 3. 离线引擎 (待实现)
    this.engines.set('offline', {
      type: 'offline' as RecognitionEngineType,
      init: () => null, // 待实现
      name: 'Offline STT'
    })
  }

  /**
   * 选择最佳引擎
   */
  async selectBestEngine(): Promise<RecognitionEngineType> {
    // 评估每个引擎的可用性
    const engineScores = new Map<RecognitionEngineType, number>()

    // Web Speech API评估
    if (this.engines.has('webspeech')) {
      let score = 0
      if (this.browserInfo.engine === 'chrome' || this.browserInfo.engine === 'edge') {
        score += 50 // Chrome/Edge支持最好
      } else if (this.browserInfo.engine === 'firefox') {
        score += 30 // Firefox需要polyfill
      } else if (this.browserInfo.engine === 'safari') {
        score += 20 // Safari支持有限
      }

      // 网络质量评估
      const networkQuality = await this.measureNetworkQuality()
      if (networkQuality < 500) {
        score += 30 // 慢速网络优先本地
      }

      engineScores.set('webspeech', score)
    }

    // 云端STT评估
    const networkQuality = await this.measureNetworkQuality()
    if (networkQuality > 1000) {
      engineScores.set('cloud', 40)
    }

    // 离线引擎评估 (总是可用)
    engineScores.set('offline', 10)

    // 选择得分最高的引擎
    let bestEngine = 'webspeech' as RecognitionEngineType
    let maxScore = 0

    for (const [engine, score] of engineScores.entries()) {
      if (score > maxScore) {
        maxScore = score
        bestEngine = engine
      }
    }

    console.log(`选择语音识别引擎: ${bestEngine}, 得分: ${maxScore}`)
    return bestEngine
  }

  /**
   * 测量网络质量
   */
  private async measureNetworkQuality(): Promise<number> {
    try {
      const start = performance.now()
      await fetch('/api/health', { method: 'HEAD', cache: 'no-store' })
      const latency = performance.now() - start

      // 简单的带宽估算
      const connection = (navigator as any).connection
      if (connection && connection.downlink) {
        return connection.downlink * 1000 // 转换为kbps
      }

      return latency < 200 ? 2000 : 500
    } catch (error) {
      console.warn('网络质量检测失败:', error)
      return 100
    }
  }

  /**
   * 切换引擎
   */
  async switchEngine(engineType: RecognitionEngineType): Promise<void> {
    if (!this.engines.has(engineType)) {
      throw new Error(`引擎 ${engineType} 不可用`)
    }

    console.log(`切换语音识别引擎: ${this.currentEngineType} -> ${engineType}`)

    // 销毁当前引擎
    if (this.currentEngine && this.currentEngine.destroy) {
      this.currentEngine.destroy()
    }

    // 初始化新引擎
    const engineInfo = this.engines.get(engineType)!
    this.currentEngine = engineInfo.init()
    this.currentEngineType = engineType

    // 通知引擎切换
    this.notifyEngineChange(engineType)
  }

  /**
   * 开始识别
   */
  async start(): Promise<void> {
    if (!this.currentEngine) {
      // 自动选择最佳引擎
      const bestEngine = await this.selectBestEngine()
      await this.switchEngine(bestEngine)
    }

    if (this.currentEngine && this.currentEngine.start) {
      const startTime = performance.now()

      try {
        await this.currentEngine.start()
        this.performanceMonitor.trackRecognition(startTime, performance.now(), true, 1)
      } catch (error) {
        this.performanceMonitor.trackRecognition(startTime, performance.now(), false, 0)
        throw error
      }
    }
  }

  /**
   * 停止识别
   */
  async stop(): Promise<void> {
    if (this.currentEngine && this.currentEngine.stop) {
      await this.currentEngine.stop()
    }
  }

  /**
   * 注册回调
   */
  on(callbacks: any): void {
    if (this.currentEngine && this.currentEngine.on) {
      this.currentEngine.on(callbacks)
    }
  }

  /**
   * 获取当前引擎信息
   */
  getCurrentEngine(): EngineInfo | null {
    if (!this.currentEngineType) {
      return null
    }

    const engine = this.engines.get(this.currentEngineType)!
    return {
      type: engine.type,
      name: engine.name,
      accuracy: 85, // 待实现
      latency: 200, // 待实现
      cost: engine.type === 'cloud' ? 0.01 : 0,
      offline: engine.type === 'webspeech' || engine.type === 'offline'
    }
  }

  /**
   * 通知引擎切换
   */
  private notifyEngineChange(engineType: RecognitionEngineType): void {
    console.log(`语音识别引擎已切换为: ${engineType}`)
    // 可以在这里触发UI更新
  }

  /**
   * 获取性能指标
   */
  getMetrics(): any {
    return this.performanceMonitor.getMetrics()
  }

  /**
   * 销毁资源
   */
  destroy(): void {
    if (this.currentEngine && this.currentEngine.destroy) {
      this.currentEngine.destroy()
    }
    this.audioEnhancer.destroy()
  }
}

/**
 * 创建自适应语音识别实例
 */
export function createAdaptiveVoiceRecognition(): AdaptiveVoiceRecognition {
  return new AdaptiveVoiceRecognition()
}
```

---

## 🎨 UI组件示例

### 语音输入组件

**文件**: `frontend/src/components/VoiceInput.vue`

```vue
<template>
  <div class="voice-input-container">
    <!-- 语音波形显示 -->
    <div class="waveform" v-show="isListening">
      <div
        v-for="(bar, index) in waveformBars"
        :key="index"
        class="waveform-bar"
        :style="{ height: `${bar.height}px` }"
      ></div>
    </div>

    <!-- 主控制按钮 -->
    <button
      class="voice-button"
      :class="{ listening: isListening }"
      @click="toggleListening"
      :disabled="isProcessing"
    >
      <el-icon v-if="!isListening"><Microphone /></el-icon>
      <el-icon v-else><SwitchButton /></el-icon>
      {{ buttonText }}
    </button>

    <!-- 状态指示器 -->
    <div class="status-indicator">
      <el-tag :type="statusTagType">{{ statusText }}</el-tag>
      <div v-if="isListening" class="volume-indicator">
        <div class="volume-bar" :style="{ width: `${volumeLevel}%` }"></div>
      </div>
    </div>

    <!-- 错误提示 -->
    <el-alert
      v-if="error"
      :title="error.message"
      type="error"
      :closable="false"
      show-icon
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Microphone, SwitchButton } from '@element-plus/icons-vue'
import { AdaptiveVoiceRecognition } from '@/utils/adaptiveVoiceRecognition'

const voiceRecognition = ref<AdaptiveVoiceRecognition | null>(null)
const isListening = ref(false)
const isProcessing = ref(false)
const error = ref<{ message: string } | null>(null)
const volumeLevel = ref(0)
const waveformBars = ref<{ height: number }[]>(new Array(20).fill(0).map(() => ({ height: 10 })))

// 计算属性
const buttonText = computed(() => {
  if (isProcessing.value) return '处理中...'
  if (isListening.value) return '点击停止'
  return '点击说话'
})

const statusText = computed(() => {
  if (error.value) return '错误'
  if (isProcessing.value) return '处理中'
  if (isListening.value) return '正在听...'
  return '准备就绪'
})

const statusTagType = computed(() => {
  if (error.value) return 'danger'
  if (isProcessing.value) return 'warning'
  if (isListening.value) return 'success'
  return 'info'
})

// 方法
const toggleListening = async () => {
  try {
    if (isListening.value) {
      await voiceRecognition.value?.stop()
      isListening.value = false
    } else {
      error.value = null
      await voiceRecognition.value?.start()
      isListening.value = true
    }
  } catch (err: any) {
    error.value = { message: err.message }
    ElMessage.error(err.message)
  }
}

const updateVolumeLevel = () => {
  // 模拟音量变化 (实际应从AudioEnhancer获取)
  volumeLevel.value = Math.random() * 100
}

onMounted(() => {
  voiceRecognition.value = new AdaptiveVoiceRecognition()

  voiceRecognition.value.on({
    onStart: () => {
      isListening.value = true
      isProcessing.value = false
    },
    onStop: () => {
      isListening.value = false
    },
    onResult: (result: any) => {
      isProcessing.value = false
      console.log('识别结果:', result.transcript)
      // 处理识别结果
    },
    onError: (err: any) => {
      error.value = err
      isListening.value = false
      isProcessing.value = false
    }
  })

  // 模拟音量更新
  const volumeInterval = setInterval(updateVolumeLevel, 100)
  onUnmounted(() => clearInterval(volumeInterval))
})

onUnmounted(() => {
  voiceRecognition.value?.destroy()
})
</script>

<style scoped>
.voice-input-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  padding: 20px;
}

.voice-button {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  border: none;
  background: var(--el-color-primary);
  color: white;
  font-size: 24px;
  cursor: pointer;
  transition: all 0.3s;
}

.voice-button:hover {
  transform: scale(1.1);
}

.voice-button.listening {
  background: var(--el-color-success);
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.waveform {
  display: flex;
  gap: 4px;
  height: 40px;
  align-items: center;
}

.waveform-bar {
  width: 4px;
  background: var(--el-color-primary);
  border-radius: 2px;
  animation: waveform 1s ease-in-out infinite;
}

.waveform-bar:nth-child(2n) {
  animation-delay: 0.1s;
}

@keyframes waveform {
  0%, 100% { height: 10px; }
  50% { height: 30px; }
}

.volume-indicator {
  width: 100px;
  height: 4px;
  background: #eee;
  border-radius: 2px;
  overflow: hidden;
  margin-top: 8px;
}

.volume-bar {
  height: 100%;
  background: var(--el-color-primary);
  transition: width 0.1s;
}
</style>
```

---

## ✅ 测试检查清单

### 功能测试
- [ ] Chrome浏览器语音识别正常
- [ ] Firefox浏览器降级处理正常
- [ ] Safari浏览器提示友好
- [ ] 错误提示清晰准确
- [ ] 权限请求流程顺畅

### 性能测试
- [ ] 识别延迟<200ms
- [ ] 准确率>85%
- [ ] 内存使用<50MB
- [ ] CPU占用<20%

### 兼容性测试
- [ ] Windows Chrome
- [ ] macOS Safari
- [ ] iOS Safari
- [ ] Android Chrome
- [ ] 各种网络环境

---

## 🚨 常见问题解决

### 1. 麦克风权限被拒绝
```typescript
// 检查权限
const permission = await navigator.permissions.query({ name: 'microphone' })

if (permission.state === 'denied') {
  ElMessageBox.alert(
    '需要麦克风权限才能使用语音识别',
    '权限被拒绝',
    {
      confirmButtonText: '前往设置',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    // 引导用户打开设置
    window.open('chrome://settings/content/microphone')
  })
}
```

### 2. Web Speech API初始化失败
```typescript
// 添加重试机制
let retryCount = 0
const maxRetries = 3

const initWithRetry = async () => {
  try {
    this.initRecognition()
  } catch (error) {
    retryCount++
    if (retryCount < maxRetries) {
      setTimeout(initWithRetry, 1000 * retryCount)
    } else {
      this.triggerError({
        code: 'init_failed',
        message: '语音识别初始化失败，请刷新页面重试'
      })
    }
  }
}
```

---

**最后更新**: 2026-02-05
**版本**: v1.0
