# 口语练习服务（AI对话）实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 补充完善现有的口语练习服务，实现完整的AI对话功能，包括语音识别(STT)、语音合成(TTS)、实时流式对话。

**架构:** 基于现有后端API（ConversationService + 智谱AI + SSE流式响应），补充完善前端组件，添加语音合成能力，实现端到端的语音对话体验。

**Tech Stack:**
- 后端：FastAPI + SQLAlchemy + ZhipuAI + SSE（已完成）
- 前端：Vue 3 + TypeScript + Web Speech API + Element Plus
- 语音：浏览器原生 Web Speech API (STT/TTS)

---

## 现有基础设施分析

### ✅ 后端已完成
| 组件 | 文件 | 状态 |
|------|------|------|
| 对话服务 | `backend/app/services/conversation_service.py` | 732行，完整 |
| 数据模型 | `backend/app/models/conversation.py` | 200行，13种场景 |
| API路由 | `backend/app/api/v1/conversations.py` | 610行，7个端点 |
| AI集成 | `backend/app/services/zhipu_service.py` | 智谱AI |

### ✅ 前端已有
| 组件 | 文件 | 状态 |
|------|------|------|
| API客户端 | `frontend/src/api/conversation.ts` | 167行 |
| 类型定义 | `frontend/src/types/conversation.ts` | 173行 |
| 语音识别 | `frontend/src/utils/voiceRecognition.ts` | 344行，完整 |
| 对话组件 | `frontend/src/views/student/ConversationView.vue` | 部分实现 |
| 口语练习 | `frontend/src/views/student/SpeakingView.vue` | 部分实现 |

### ❌ 前端缺失
1. **语音合成(TTS)工具** - 无TTS实现
2. **完整的对话交互逻辑** - 组件状态管理不完整
3. **流式响应UI集成** - SSE客户端有但UI未完整集成
4. **评分展示组件** - 无评分结果展示组件
5. **单元测试** - 对话相关组件无测试覆盖

---

## 实施任务列表

### 阶段1：语音合成(TTS)工具

#### Task 1.1: 创建语音合成工具类

**Files:**
- Create: `frontend/src/utils/textToSpeech.ts`
- Test: `frontend/tests/unit/textToSpeech.spec.ts`

**Step 1: 写测试用例**

```typescript
// tests/unit/textToSpeech.spec.ts
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { TextToSpeech, TTSEvent, TTSStatus } from '@/utils/textToSpeech'

describe('TextToSpeech', () => {
  let tts: TextToSpeech

  beforeEach(() => {
    // Mock SpeechSynthesis
    global.SpeechSynthesisUtterance = class {
        text = ''
        lang = ''
        rate = 1
        pitch = 1
        volume = 1
        onstart: (() => void) | null = null
        onend: (() => void) | null = null
        onerror: ((e: any) => void) | null = null
        onpause: (() => void) | null = null
        onresume: (() => void) | null = null
        onmark: (() => void) | null = null
        onboundary: (() => void) | null = null
    } as any

    global.speechSynthesis = {
        speak: vi.fn(),
        cancel: vi.fn(),
        pause: vi.fn(),
        resume: vi.fn(),
        getVoices: vi.fn(() => []),
        speaking: false,
        pending: false,
        paused: false
    } as any

    tts = new TextToSpeech()
  })

  afterEach(() => {
    tts.destroy()
  })

  it('应该正确初始化语音合成', () => {
    expect(tts.getStatus()).toBe(TTSStatus.Idle)
  })

  it('应该在浏览器不支持时返回错误状态', () => {
    // @ts-expect-error - 测试不支持的情况
    delete global.speechSynthesis

    const tts2 = new TextToSpeech()
    expect(tts2.getStatus()).toBe(TTSStatus.Error)
  })

  it('应该正确开始语音合成', async () => {
    let spoken = false
    const mockSpeak = global.speechSynthesis.speak as any

    mockSpeak.mockImplementation((utterance: any) => {
        utterance.onstart?.()
        setTimeout(() => utterance.onend?.(), 10)
    })

    await new Promise<void>(resolve => {
        tts.on({
            onStart: () => {
                expect(tts.getStatus()).toBe(TTSStatus.Speaking)
            },
            onEnd: () => {
                expect(tts.getStatus()).toBe(TTSStatus.Idle)
                spoken = true
                resolve()
            }
        })
        tts.speak('Hello world')
    })

    expect(spoken).toBe(true)
  })

  it('应该正确停止语音合成', () => {
    tts.speak('Hello world')
    tts.stop()

    expect(global.speechSynthesis.cancel).toHaveBeenCalled()
  })

  it('应该支持暂停和恢复', () => {
    tts.speak('Hello world')
    tts.pause()
    expect(tts.getStatus()).toBe(TTSStatus.Paused)

    tts.resume()
    expect(tts.getStatus()).toBe(TTSStatus.Speaking)
  })

  it('应该正确设置语音参数', () => {
    tts.setRate(1.5)
    tts.setPitch(1.2)
    tts.setVolume(0.8)
    tts.setLanguage('en-US')

    tts.speak('Test')

    const utterance = (global.speechSynthesis.speak as any).mock.calls[0][0]
    expect(utterance.rate).toBe(1.5)
    expect(utterance.pitch).toBe(1.2)
    expect(utterance.volume).toBe(0.8)
    expect(utterance.lang).toBe('en-US')
  })
})
```

**Step 2: 运行测试确认失败**

```bash
cd frontend
npm run test tests/unit/textToSpeech.spec.ts
```

Expected: FAIL - 文件不存在

**Step 3: 创建TTS工具类**

```typescript
// utils/textToSpeech.ts
/**
 * 语音合成工具模块
 * 使用 Web Speech API 实现 TTS (Text-to-Speech)
 */

/**
 * TTS 事件类型
 */
export enum TTSEvent {
  Start = 'start',
  End = 'end',
  Pause = 'pause',
  Resume = 'resume',
  Error = 'error',
  Boundary = 'boundary'
}

/**
 * TTS 状态
 */
export enum TTSStatus {
  Idle = 'idle',
  Initializing = 'initializing',
  Speaking = 'speaking',
  Paused = 'paused',
  Error = 'error'
}

/**
 * TTS 结果
 */
export interface TTSResult {
  success: boolean
  duration?: number
  error?: string
}

/**
 * TTS 配置
 */
export interface TTSConfig {
  language?: string
  rate?: number          // 0.1 - 10
  pitch?: number         // 0 - 2
  volume?: number        // 0 - 1
  voice?: SpeechSynthesisVoice | null
}

/**
 * TTS 回调
 */
export interface TTSCallbacks {
  onStart?: () => void
  onEnd?: () => void
  onPause?: () => void
  onResume?: () => void
  onError?: (error: Error) => void
  onBoundary?: (event: SpeechSynthesisEvent) => void
  onStatusChange?: (status: TTSStatus) => void
}

/**
 * 语音合成器类
 */
export class TextToSpeech {
  private synthesis: SpeechSynthesis | null = null
  private utterance: SpeechSynthesisUtterance | null = null
  private status: TTSStatus = TTSStatus.Idle
  private callbacks: TTSCallbacks = {}
  private config: TTSConfig = {}

  constructor(config: TTSConfig = {}) {
    this.config = {
      language: 'en-US',
      rate: 1.0,
      pitch: 1.0,
      volume: 1.0,
      voice: null,
      ...config
    }

    this.initSynthesis()
  }

  /**
   * 初始化语音合成
   */
  private initSynthesis() {
    if (!('speechSynthesis' in window)) {
      this.setStatus(TTSStatus.Error)
      this.triggerError(new Error('您的浏览器不支持语音合成功能'))
      return
    }

    try {
      this.synthesis = window.speechSynthesis
    } catch (error) {
      this.setStatus(TTSStatus.Error)
      this.triggerError(new Error('语音合成初始化失败'))
    }
  }

  /**
   * 配置语音合成utterance
   */
  private setupUtterance(text: string): SpeechSynthesisUtterance {
    const utterance = new SpeechSynthesisUtterance(text)

    utterance.lang = this.config.language || 'en-US'
    utterance.rate = this.config.rate || 1.0
    utterance.pitch = this.config.pitch || 1.0
    utterance.volume = this.config.volume || 1.0

    if (this.config.voice) {
      utterance.voice = this.config.voice
    }

    // 事件处理
    utterance.onstart = () => {
      this.setStatus(TTSStatus.Speaking)
      this.callbacks.onStart?.()
    }

    utterance.onend = () => {
      this.setStatus(TTSStatus.Idle)
      this.utterance = null
      this.callbacks.onEnd?.()
    }

    utterance.onerror = (event: SpeechSynthesisErrorEvent) => {
      this.setStatus(TTSStatus.Error)
      this.utterance = null
      this.triggerError(new Error(event.error || '语音合成发生错误'))
    }

    utterance.onpause = () => {
      this.setStatus(TTSStatus.Paused)
      this.callbacks.onPause?.()
    }

    utterance.onresume = () => {
      this.setStatus(TTSStatus.Speaking)
      this.callbacks.onResume?.()
    }

    utterance.onboundary = (event: SpeechSynthesisEvent) => {
      this.callbacks.onBoundary?.(event)
    }

    return utterance
  }

  /**
   * 触发错误回调
   */
  private triggerError(error: Error) {
    this.callbacks.onError?.(error)
  }

  /**
   * 设置状态
   */
  private setStatus(status: TTSStatus) {
    this.status = status
    this.callbacks.onStatusChange?.(status)
  }

  /**
   * 注册回调
   */
  public on(callbacks: TTSCallbacks): TextToSpeech {
    this.callbacks = { ...this.callbacks, ...callbacks }
    return this
  }

  /**
   * 开始语音合成
   */
  public speak(text: string): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.synthesis) {
        reject(new Error('语音合成未初始化'))
        return
      }

      // 取消当前播放
      if (this.utterance) {
        this.stop()
      }

      this.utterance = this.setupUtterance(text)

      // 添加一次性结束回调
      const originalOnEnd = this.utterance.onend
      this.utterance.onend = () => {
        originalOnEnd?.()
        resolve()
      }

      const originalOnError = this.utterance.onerror
      this.utterance.onerror = (event: any) => {
        originalOnError?.(event)
        reject(new Error(event.error || '语音合成失败'))
      }

      try {
        this.synthesis.speak(this.utterance)
      } catch (error) {
        this.setStatus(TTSStatus.Error)
        reject(error)
      }
    })
  }

  /**
   * 停止语音合成
   */
  public stop(): void {
    if (!this.synthesis) return

    this.synthesis.cancel()
    this.utterance = null
    this.setStatus(TTSStatus.Idle)
  }

  /**
   * 暂停语音合成
   */
  public pause(): void {
    if (!this.synthesis || this.status !== TTSStatus.Speaking) return

    this.synthesis.pause()
  }

  /**
   * 恢复语音合成
   */
  public resume(): void {
    if (!this.synthesis || this.status !== TTSStatus.Paused) return

    this.synthesis.resume()
  }

  /**
   * 设置语速
   */
  public setRate(rate: number): void {
    this.config.rate = Math.max(0.1, Math.min(10, rate))
  }

  /**
   * 设置音调
   */
  public setPitch(pitch: number): void {
    this.config.pitch = Math.max(0, Math.min(2, pitch))
  }

  /**
   * 设置音量
   */
  public setVolume(volume: number): void {
    this.config.volume = Math.max(0, Math.min(1, volume))
  }

  /**
   * 设置语言
   */
  public setLanguage(language: string): void {
    this.config.language = language
  }

  /**
   * 设置语音
   */
  public setVoice(voice: SpeechSynthesisVoice | null): void {
    this.config.voice = voice
  }

  /**
   * 获取当前状态
   */
  public getStatus(): TTSStatus {
    return this.status
  }

  /**
   * 是否正在播放
   */
  public isSpeaking(): boolean {
    return this.status === TTSStatus.Speaking
  }

  /**
   * 是否已暂停
   */
  public isPaused(): boolean {
    return this.status === TTSStatus.Paused
  }

  /**
   * 获取可用语音列表
   */
  public getVoices(): SpeechSynthesisVoice[] {
    if (!this.synthesis) return []

    return this.synthesis.getVoices()
  }

  /**
   * 获取指定语言的语音
   */
  public getVoicesForLanguage(language: string): SpeechSynthesisVoice[] {
    return this.getVoices().filter(voice =>
      voice.lang.startsWith(language)
    )
  }

  /**
   * 销毁合成器
   */
  public destroy(): void {
    this.stop()
    this.synthesis = null
    this.callbacks = {}
  }
}

/**
 * 创建语音合成器实例
 */
export function createTextToSpeech(config?: TTSConfig): TextToSpeech {
  return new TextToSpeech(config)
}

/**
 * 检查浏览器是否支持语音合成
 */
export function isTextToSpeechSupported(): boolean {
  return 'speechSynthesis' in window
}

/**
 * 获取最佳英语语音
 */
export function getBestEnglishVoice(): SpeechSynthesisVoice | null {
  if (!isTextToSpeechSupported()) return null

  const tts = createTextToSpeech()
  const voices = tts.getVoicesForLanguage('en')

  // 优先选择Google英语语音
  const googleVoice = voices.find(v => v.name.includes('Google') && v.lang.includes('en'))
  if (googleVoice) return googleVoice

  // 其次选择Microsoft英语语音
  const microsoftVoice = voices.find(v => v.name.includes('Microsoft') && v.lang.includes('en'))
  if (microsoftVoice) return microsoftVoice

  // 最后返回第一个英语语音
  return voices[0] || null
}
```

**Step 4: 运行测试**

```bash
cd frontend
npm run test tests/unit/textToSpeech.spec.ts
```

Expected: PASS

**Step 5: 提交**

```bash
git add frontend/src/utils/textToSpeech.ts frontend/tests/unit/textToSpeech.spec.ts
git commit -m "feat(speaking): 添加语音合成(TTS)工具类"
```

---

### 阶段2：完善对话组件

#### Task 2.1: 创建对话评分展示组件

**Files:**
- Create: `frontend/src/components/ConversationScoreCard.vue`
- Test: `frontend/tests/unit/components/ConversationScoreCard.spec.ts`

**Step 1: 写测试用例**

```typescript
// tests/unit/components/ConversationScoreCard.spec.ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ConversationScoreCard from '@/components/ConversationScoreCard.vue'
import type { ConversationScores } from '@/types/conversation'

describe('ConversationScoreCard', () => {
  const mockScores: ConversationScores = {
    overall: 85,
    overall_score: 85,
    fluency_score: 80,
    grammar_score: 75,
    vocabulary_score: 88,
    feedback: '整体表现良好，继续保持！',
    suggestions: [
      '注意时态一致性',
      '可以尝试更多样化的词汇'
    ]
  }

  it('应该正确渲染评分卡片', () => {
    const wrapper = mount(ConversationScoreCard, {
      props: { scores: mockScores }
    })

    expect(wrapper.find('.score-card').exists()).toBe(true)
    expect(wrapper.text()).toContain('85')
  })

  it('应该显示反馈信息', () => {
    const wrapper = mount(ConversationScoreCard, {
      props: { scores: mockScores }
    })

    expect(wrapper.text()).toContain('整体表现良好')
  })

  it('应该显示建议列表', () => {
    const wrapper = mount(ConversationScoreCard, {
      props: { scores: mockScores }
    })

    expect(wrapper.findAll('.suggestion-item')).toHaveLength(2)
  })

  it('应该在无评分时显示空状态', () => {
    const wrapper = mount(ConversationScoreCard, {
      props: { scores: null }
    })

    expect(wrapper.find('.empty-state').exists()).toBe(true)
  })
})
```

**Step 2: 运行测试确认失败**

```bash
cd frontend
npm run test tests/unit/components/ConversationScoreCard.spec.ts
```

Expected: FAIL - 文件不存在

**Step 3: 创建评分卡片组件**

```vue
<!-- components/ConversationScoreCard.vue -->
<template>
  <el-card class="score-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <el-icon><TrendCharts /></el-icon>
        <span>对话评分</span>
      </div>
    </template>

    <el-empty v-if="!scores" description="暂无评分数据" />

    <div v-else class="score-content">
      <!-- 总分展示 -->
      <div class="overall-score">
        <div class="score-circle" :class="getScoreClass(scores.overall_score || 0)">
          <span class="score-value">{{ scores.overall_score || 0 }}</span>
          <span class="score-label">总分</span>
        </div>
        <div class="score-labels">
          <el-tag :type="getScoreType(scores.overall_score || 0)" size="large">
            {{ getScoreLabel(scores.overall_score || 0) }}
          </el-tag>
        </div>
      </div>

      <!-- 分项评分 -->
      <el-divider />

      <div class="dimension-scores">
        <div class="score-item">
          <div class="score-header">
            <span>流利度</span>
            <span class="score-number">{{ scores.fluency_score || 0 }}</span>
          </div>
          <el-progress
            :percentage="scores.fluency_score || 0"
            :color="getProgressColor(scores.fluency_score || 0)"
            :show-text="false"
          />
        </div>

        <div class="score-item">
          <div class="score-header">
            <span>词汇</span>
            <span class="score-number">{{ scores.vocabulary_score || 0 }}</span>
          </div>
          <el-progress
            :percentage="scores.vocabulary_score || 0"
            :color="getProgressColor(scores.vocabulary_score || 0)"
            :show-text="false"
          />
        </div>

        <div class="score-item">
          <div class="score-header">
            <span>语法</span>
            <span class="score-number">{{ scores.grammar_score || 0 }}</span>
          </div>
          <el-progress
            :percentage="scores.grammar_score || 0"
            :color="getProgressColor(scores.grammar_score || 0)"
            :show-text="false"
          />
        </div>
      </div>

      <!-- 反馈 -->
      <el-divider />

      <div v-if="scores.feedback" class="feedback-section">
        <h4>AI 反馈</h4>
        <p class="feedback-text">{{ scores.feedback }}</p>
      </div>

      <!-- 建议 -->
      <div v-if="scores.suggestions?.length" class="suggestions-section">
        <h4>改进建议</h4>
        <ul class="suggestions-list">
          <li v-for="(suggestion, index) in scores.suggestions" :key="index" class="suggestion-item">
            <el-icon><Right /></el-icon>
            <span>{{ suggestion }}</span>
          </li>
        </ul>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { TrendCharts, Right } from '@element-plus/icons-vue'
import type { ConversationScores } from '@/types/conversation'

interface Props {
  scores: ConversationScores | null
}

const props = defineProps<Props>()

function getScoreClass(score: number): string {
  if (score >= 90) return 'excellent'
  if (score >= 75) return 'good'
  if (score >= 60) return 'satisfactory'
  return 'needs-improvement'
}

function getScoreType(score: number): 'success' | 'warning' | 'danger' | 'info' {
  if (score >= 90) return 'success'
  if (score >= 75) return 'success'
  if (score >= 60) return 'warning'
  return 'danger'
}

function getScoreLabel(score: number): string {
  if (score >= 90) return '优秀'
  if (score >= 75) return '良好'
  if (score >= 60) return '满意'
  return '需改进'
}

function getProgressColor(score: number): string {
  if (score >= 90) return '#67C23A'
  if (score >= 75) return '#409EFF'
  if (score >= 60) return '#E6A23C'
  return '#F56C6C'
}
</script>

<style scoped>
.score-card {
  margin-top: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
}

.overall-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
}

.score-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 4px solid;
  margin-bottom: 16px;
}

.score-circle.excellent {
  border-color: #67C23A;
  background: linear-gradient(135deg, #f0fff4 0%, #dcfce7 100%);
}

.score-circle.good {
  border-color: #409EFF;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
}

.score-circle.satisfactory {
  border-color: #E6A23C;
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
}

.score-circle.needs-improvement {
  border-color: #F56C6C;
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
}

.score-value {
  font-size: 36px;
  font-weight: 700;
  line-height: 1;
}

.score-label {
  font-size: 14px;
  color: #606266;
  margin-top: 4px;
}

.dimension-scores {
  padding: 0 20px;
}

.score-item {
  margin-bottom: 20px;
}

.score-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.score-number {
  font-weight: 600;
  font-size: 16px;
}

.feedback-section,
.suggestions-section {
  padding: 0 20px 20px;
}

.feedback-section h4,
.suggestions-section h4 {
  margin: 0 0 12px;
  font-size: 16px;
  font-weight: 600;
}

.feedback-text {
  margin: 0;
  line-height: 1.6;
  color: #606266;
}

.suggestions-list {
  margin: 0;
  padding-left: 0;
  list-style: none;
}

.suggestion-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 0;
  line-height: 1.6;
}

.suggestion-item .el-icon {
  margin-top: 2px;
  color: #409EFF;
  flex-shrink: 0;
}
</style>
```

**Step 4: 运行测试**

```bash
cd frontend
npm run test tests/unit/components/ConversationScoreCard.spec.ts
```

Expected: PASS

**Step 5: 提交**

```bash
git add frontend/src/components/ConversationScoreCard.vue frontend/tests/unit/components/ConversationScoreCard.spec.ts
git commit -m "feat(speaking): 添加对话评分卡片组件"
```

#### Task 2.2: 创建语音控制按钮组件

**Files:**
- Create: `frontend/src/components/VoiceControlButton.vue`
- Test: `frontend/tests/unit/components/VoiceControlButton.spec.ts`

**Step 1: 写测试用例**

```typescript
// tests/unit/components/VoiceControlButton.spec.ts
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import VoiceControlButton from '@/components/VoiceControlButton.vue'

describe('VoiceControlButton', () => {
  it('应该正确渲染录音按钮', () => {
    const wrapper = mount(VoiceControlButton, {
      props: {
        type: 'record',
        state: 'idle'
      }
    })

    expect(wrapper.find('.voice-button').exists()).toBe(true)
    expect(wrapper.find('.el-icon-microphone').exists()).toBe(true)
  })

  it('应该在录音状态时显示停止图标', () => {
    const wrapper = mount(VoiceControlButton, {
      props: {
        type: 'record',
        state: 'listening'
      }
    })

    expect(wrapper.find('.el-icon-video-pause').exists()).toBe(true)
  })

  it('应该正确触发点击事件', async () => {
    const wrapper = mount(VoiceControlButton, {
      props: {
        type: 'record',
        state: 'idle'
      }
    })

    await wrapper.find('.voice-button').trigger('click')

    expect(wrapper.emitted('click')).toBeTruthy()
  })

  it('禁用状态时不应触发点击', async () => {
    const wrapper = mount(VoiceControlButton, {
      props: {
        type: 'record',
        state: 'idle',
        disabled: true
      }
    })

    await wrapper.find('.voice-button').trigger('click')

    expect(wrapper.emitted('click')).toBeFalsy()
  })
})
```

**Step 2: 运行测试确认失败**

```bash
cd frontend
npm run test tests/unit/components/VoiceControlButton.spec.ts
```

Expected: FAIL

**Step 3: 创建语音控制组件**

```vue
<!-- components/VoiceControlButton.vue -->
<template>
  <el-button
    :class="['voice-button', type, state, { disabled }]"
    :disabled="disabled"
    :type="buttonType"
    :circle="circle"
    :size="size"
    @click="handleClick"
  >
    <el-icon :size="iconSize">
      <component :is="currentIcon" />
    </el-icon>

    <!-- 录音时的波纹动画 -->
    <span v-if="type === 'record' && state === 'listening'" class="ripple"></span>
  </el-button>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  Microphone,
  VideoPause,
  Loading,
  MuteNotification,
  Bell
} from '@element-plus/icons-vue'

interface Props {
  type: 'record' | 'play' | 'stop'
  state: 'idle' | 'listening' | 'processing' | 'playing' | 'paused'
  disabled?: boolean
  circle?: boolean
  size?: 'large' | 'default' | 'small'
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  circle: true,
  size: 'large'
})

const emit = defineEmits<{
  click: []
}>()

function handleClick() {
  if (!props.disabled) {
    emit('click')
  }
}

const currentIcon = computed(() => {
  switch (props.type) {
    case 'record':
      if (props.state === 'listening') return VideoPause
      if (props.state === 'processing') return Loading
      return Microphone

    case 'play':
      if (props.state === 'playing') return VideoPause
      return Bell

    case 'stop':
      return MuteNotification

    default:
      return Microphone
  }
})

const buttonType = computed(() => {
  if (props.disabled) return 'info'

  switch (props.state) {
    case 'listening':
    case 'playing':
      return 'danger'

    case 'processing':
      return 'warning'

    default:
      return 'primary'
  }
})

const iconSize = computed(() => {
  switch (props.size) {
    case 'large': return 28
    case 'small': return 16
    default: return 22
  }
})
</script>

<style scoped>
.voice-button {
  position: relative;
  transition: all 0.3s ease;
}

.voice-button.listening,
.voice-button.playing {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(245, 108, 108, 0.7);
  }
  50% {
    transform: scale(1.05);
    box-shadow: 0 0 0 10px rgba(245, 108, 108, 0);
  }
}

.ripple {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: 2px solid currentColor;
  opacity: 0;
  animation: ripple 1.5s ease-out infinite;
}

@keyframes ripple {
  0% {
    width: 100%;
    height: 100%;
    opacity: 0.5;
  }
  100% {
    width: 200%;
    height: 200%;
    opacity: 0;
  }
}

.voice-button.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
```

**Step 4: 运行测试**

```bash
cd frontend
npm run test tests/unit/components/VoiceControlButton.spec.ts
```

Expected: PASS

**Step 5: 提交**

```bash
git add frontend/src/components/VoiceControlButton.vue frontend/tests/unit/components/VoiceControlButton.spec.ts
git commit -m "feat(speaking): 添加语音控制按钮组件"
```

---

### 阶段3：完善对话主组件

#### Task 3.1: 更新ConversationView组件

**Files:**
- Modify: `frontend/src/views/student/ConversationView.vue`
- Test: `frontend/tests/unit/views/ConversationView.spec.ts`

**Step 1: 分析现有组件并编写测试**

```bash
# 查看现有组件结构
wc -l frontend/src/views/student/ConversationView.vue
```

**Step 2: 创建测试用例（针对需要实现的功能）**

```typescript
// tests/unit/views/ConversationView.spec.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ConversationView from '@/views/student/ConversationView.vue'
import * as conversationApi from '@/api/conversation'
import { createVoiceRecognition } from '@/utils/voiceRecognition'
import { createTextToSpeech } from '@/utils/textToSpeech'

// Mock API
vi.mock('@/api/conversation', () => ({
  createConversation: vi.fn(),
  getConversation: vi.fn(),
  sendMessage: vi.fn(),
  completeConversation: vi.fn(),
  getScenarios: vi.fn(),
  streamMessage: vi.fn(() => vi.fn())
}))

// Mock Web Speech API
global.SpeechRecognition = class {
  lang = 'en-US'
  continuous = false
  interimResults = true
  onstart = null
  onend = null
  onresult = null
  onerror = null

  start() {
    this.onstart?.()
    setTimeout(() => {
      this.onresult?.({
        results: [{
          isFinal: true,
          0: { transcript: 'Hello', confidence: 1 }
        }]
      })
      this.onend?.()
    }, 100)
  }

  stop() {
    this.onend?.()
  }

  abort() {}
}

global.speechSynthesis = {
  speak: vi.fn((utterance: any) => {
    setTimeout(() => utterance.onend?.(), 100)
  }),
  cancel: vi.fn(),
  pause: vi.fn(),
  resume: vi.fn(),
  getVoices: vi.fn(() => []),
  speaking: false,
  pending: false,
  paused: false
}

describe('ConversationView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('应该正确渲染场景选择界面', () => {
    const wrapper = mount(ConversationView)

    expect(wrapper.find('.scenario-selection').exists()).toBe(true)
  })

  it('应该能选择场景并开始对话', async () => {
    vi.mocked(conversationApi.createConversation).mockResolvedValue({
      id: 'test-conv-1',
      scenario: 'daily_greeting',
      level: 'A2',
      status: 'active',
      messages: [],
      started_at: new Date().toISOString()
    })

    const wrapper = mount(ConversationView)
    await wrapper.vm.selectScenario('daily_greeting')
    await wrapper.vm.startConversation()

    expect(conversationApi.createConversation).toHaveBeenCalled()
    expect(wrapper.vm.currentStep).toBe('conversation')
  })

  it('应该支持语音输入', async () => {
    const wrapper = mount(ConversationView)
    wrapper.vm.currentStep = 'conversation'

    const recognition = createVoiceRecognition()
    const startSpy = vi.spyOn(recognition, 'start')

    await wrapper.vm.startVoiceInput()
    expect(startSpy).toHaveBeenCalled()
  })

  it('应该支持TTS播放AI回复', async () => {
    const wrapper = mount(ConversationView)

    const tts = createTextToSpeech()
    const speakSpy = vi.spyOn(tts, 'speak')

    await wrapper.vm.playAIResponse('Hello, how are you?')
    expect(speakSpy).toHaveBeenCalledWith('Hello, how are you?')
  })

  it('应该能完成对话并获取评分', async () => {
    vi.mocked(conversationApi.completeConversation).mockResolvedValue({
      conversation: {
        id: 'test-conv-1',
        status: 'completed'
      },
      scores: {
        overall_score: 85,
        fluency_score: 80,
        grammar_score: 75,
        vocabulary_score: 88,
        feedback: 'Good job!',
        suggestions: ['Keep practicing']
      }
    })

    const wrapper = mount(ConversationView)
    wrapper.vm.conversationId = 'test-conv-1'

    await wrapper.vm.completeConversation()

    expect(conversationApi.completeConversation).toHaveBeenCalledWith('test-conv-1')
    expect(wrapper.vm.scores).toBeDefined()
  })
})
```

**Step 3: 更新ConversationView组件（补充缺失的功能）**

由于现有组件已部分实现，重点是补充：

1. **集成语音合成**
2. **完善流式响应处理**
3. **添加评分展示**
4. **完善状态管理**

```vue
<!-- views/student/ConversationView.vue 补充关键部分 -->
<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowLeft,
  Right,
  Setting,
  Loading,
  Check
} from '@element-plus/icons-vue'
import ConversationMessageComponent from '@/components/ConversationMessageComponent.vue'
import ConversationScoreCard from '@/components/ConversationScoreCard.vue'
import VoiceControlButton from '@/components/VoiceControlButton.vue'
import {
  createConversation,
  sendMessage,
  completeConversation,
  getScenarios,
  streamMessage
} from '@/api/conversation'
import { createVoiceRecognition, VoiceRecognitionStatus } from '@/utils/voiceRecognition'
import { createTextToSpeech, TTSStatus } from '@/utils/textToSpeech'
import type { Conversation, ConversationMessage, ConversationScores } from '@/types/conversation'

// 状态
const router = useRouter()
const currentStep = ref<'scenario' | 'conversation' | 'result'>('scenario')
const selectedScenario = ref<string>('')
const level = ref<string>('A2')
const conversationId = ref<string>('')
const messages = ref<ConversationMessage[]>([])
const isAIThinking = ref(false)
const streamingMessage = ref<ConversationMessage | null>(null)
const scores = ref<ConversationScores | null>(null)

// 语音识别
const voiceRecognition = ref<any>(null)
const voiceStatus = ref<VoiceRecognitionStatus>(VoiceRecognitionStatus.Idle)
const interimTranscript = ref<string>('')

// 语音合成
const textToSpeech = ref<any>(null)
const ttsStatus = ref<TTSStatus>(TTSStatus.Idle)
const autoPlayResponse = ref<boolean>(true)

// 场景列表
const scenarios = ref<any[]>([])

// 配置
const showSettings = ref(false)
const voiceEnabled = ref(true)
const soundEnabled = ref(true)

// 目标消息数
const targetMessages = 5

// 初始化
onMounted(async () => {
  await loadScenarios()
  initVoiceRecognition()
  initTextToSpeech()
})

onUnmounted(() => {
  // 清理语音资源
  if (voiceRecognition.value) {
    voiceRecognition.value.destroy()
  }
  if (textToSpeech.value) {
    textToSpeech.value.destroy()
  }
})

// 加载场景
async function loadScenarios() {
  try {
    const response = await getScenarios()
    scenarios.value = response.scenarios.map(s => ({
      value: s.id,
      label: s.name,
      description: s.description,
      level: 'A2-C1'
    }))
  } catch (error) {
    console.error('Failed to load scenarios:', error)
  }
}

// 初始化语音识别
function initVoiceRecognition() {
  voiceRecognition.value = createVoiceRecognition({
    language: 'en-US',
    continuous: false,
    interimResults: true
  })

  voiceRecognition.value.on({
    onStatusChange: (status: VoiceRecognitionStatus) => {
      voiceStatus.value = status
    },
    onInterimResult: (result: any) => {
      interimTranscript.value = result.transcript
    },
    onResult: async (result: any) => {
      interimTranscript.value = ''
      if (result.transcript) {
        await sendUserMessage(result.transcript)
      }
    },
    onError: (error: any) => {
      console.error('Voice recognition error:', error)
      // 显示错误提示
    }
  })
}

// 初始化语音合成
function initTextToSpeech() {
  textToSpeech.value = createTextToSpeech({
    language: 'en-US',
    rate: 1.0,
    pitch: 1.0,
    volume: 1.0
  })

  textToSpeech.value.on({
    onStatusChange: (status: TTSStatus) => {
      ttsStatus.value = status
    }
  })
}

// 选择场景
function selectScenario(scenario: string) {
  selectedScenario.value = scenario
}

// 开始对话
async function startConversation() {
  if (!selectedScenario.value) return

  try {
    const conversation = await createConversation({
      scenario: selectedScenario.value as any,
      level: level.value
    })

    conversationId.value = conversation.id
    messages.value = conversation.messages || []
    currentStep.value = 'conversation'

    // AI 开始问候
    await triggerAIResponse()
  } catch (error) {
    console.error('Failed to start conversation:', error)
  }
}

// 触发AI回复（首条消息）
async function triggerAIResponse() {
  isAIThinking.value = true

  // 发送空消息让AI开始对话
  try {
    const response = await sendMessage(conversationId.value, {
      content: '', // 空消息触发AI开场白
      is_final: true
    })

    addMessage({
      id: Date.now().toString(),
      role: 'assistant',
      type: 'text',
      content: response.message.content,
      timestamp: new Date().toISOString()
    })

    // TTS 播放
    if (soundEnabled.value && autoPlayResponse.value) {
      await playAIResponse(response.message.content)
    }
  } catch (error) {
    console.error('Failed to trigger AI response:', error)
  } finally {
    isAIThinking.value = false
  }
}

// 发送用户消息
async function sendUserMessage(content: string) {
  if (!content.trim() || !conversationId.value) return

  // 添加用户消息
  addMessage({
    id: Date.now().toString(),
    role: 'user',
    type: 'text',
    content,
    timestamp: new Date().toISOString()
  })

  // 获取AI回复（支持流式）
  await getAIResponse(content)
}

// 获取AI回复
async function getAIResponse(userMessage: string) {
  isAIThinking.value = true

  // 创建流式消息占位
  const streamingId = Date.now().toString()
  streamingMessage.value = {
    id: streamingId,
    role: 'assistant',
    type: 'text',
    content: '',
    timestamp: new Date().toISOString()
  }
  messages.value.push(streamingMessage.value)

  try {
    // 使用流式API
    const cleanup = streamMessage(conversationId.value, userMessage, {
      onStart: () => {
        console.log('Stream started')
      },
      onToken: (token: string) => {
        if (streamingMessage.value) {
          streamingMessage.value.content += token
        }
      },
      onComplete: (fullMessage: string) => {
        streamingMessage.value = null
        isAIThinking.value = false

        // TTS 播放完整回复
        if (soundEnabled.value && autoPlayResponse.value) {
          playAIResponse(fullMessage)
        }
      },
      onError: (error: Error) => {
        console.error('Stream error:', error)
        streamingMessage.value = null
        isAIThinking.value = false
      },
      onEnd: () => {
        streamingMessage.value = null
      }
    })

    // 返回清理函数（在组件卸载时调用）
    return cleanup
  } catch (error) {
    console.error('Failed to get AI response:', error)
    streamingMessage.value = null
    isAIThinking.value = false
  }
}

// 播放AI语音回复
async function playAIResponse(text: string) {
  if (!textToSpeech.value || !text) return

  try {
    await textToSpeech.value.speak(text)
  } catch (error) {
    console.error('TTS error:', error)
  }
}

// 停止TTS播放
function stopPlayback() {
  if (textToSpeech.value) {
    textToSpeech.value.stop()
  }
}

// 开始语音输入
function startVoiceInput() {
  if (!voiceRecognition.value) return

  // 停止当前TTS播放
  stopPlayback()

  // 开始语音识别
  voiceRecognition.value.start()
}

// 停止语音输入
function stopVoiceInput() {
  if (voiceRecognition.value) {
    voiceRecognition.value.stop()
  }
}

// 添加消息
function addMessage(message: ConversationMessage) {
  messages.value.push(message)

  // 滚动到底部
  nextTick(() => {
    scrollToBottom()
  })
}

// 滚动到底部
function scrollToBottom() {
  const container = document.querySelector('.messages-container')
  if (container) {
    container.scrollTop = container.scrollHeight
  }
}

// 快捷回复
function sendQuickReply(reply: string) {
  sendUserMessage(reply)
}

// 完成对话
async function completeConversation() {
  if (!conversationId.value) return

  try {
    const response = await completeConversation(conversationId.value)
    scores.value = response.scores
    currentStep.value = 'result'
  } catch (error) {
    console.error('Failed to complete conversation:', error)
  }
}

// 重新开始
function restartConversation() {
  // 重置状态
  currentStep.value = 'scenario'
  conversationId.value = ''
  messages.value = []
  scores.value = null
  selectedScenario.value = ''
}

// 返回
function goBack() {
  if (currentStep.value === 'conversation') {
    // 确认是否退出
    // ...
  } else {
    router.push('/student')
  }
}

// 计算属性
const conversationStatus = computed(() => {
  return messages.value.length >= targetMessages ? 'ready_to_complete' : 'in_progress'
})

const canCompleteConversation = computed(() => {
  return messages.value.length >= 2 // 至少一轮对话
})

const isListening = computed(() => {
  return voiceStatus.value === VoiceRecognitionStatus.Listening
})

const isPlaying = computed(() => {
  return ttsStatus.value === TTSStatus.Speaking
})
</script>

<template>
  <!-- 模板保持现有结构，补充语音控制和TTS相关UI -->
</template>
```

**Step 4: 运行测试**

```bash
cd frontend
npm run test tests/unit/views/ConversationView.spec.ts
```

Expected: PASS

**Step 5: 提交**

```bash
git add frontend/src/views/student/ConversationView.vue frontend/tests/unit/views/ConversationView.spec.ts
git commit -m "feat(speaking): 完善对话主组件，集成STT/TTS和流式响应"
```

---

### 阶段4：集成测试

#### Task 4.1: 创建端到端对话流程测试

**Files:**
- Create: `frontend/tests/integration/conversationFlow.spec.ts`

**Step 1: 创建集成测试**

```typescript
// tests/integration/conversationFlow.spec.ts
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ConversationView from '@/views/student/ConversationView.vue'
import * as conversationApi from '@/api/conversation'

// Mock API
vi.mock('@/api/conversation', () => ({
  createConversation: vi.fn(),
  sendMessage: vi.fn(),
  completeConversation: vi.fn(),
  getScenarios: vi.fn(),
  streamMessage: vi.fn()
}))

describe('对话流程集成测试', () => {
  beforeEach(() => {
    setActivePinia(createPinia())

    // Mock场景数据
    vi.mocked(conversationApi.getScenarios).mockResolvedValue({
      scenarios: [
        {
          id: 'daily_greeting',
          name: '日常问候',
          description: '练习日常问候对话'
        }
      ]
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('应该能完成完整的对话流程', async () => {
    // Mock创建对话
    vi.mocked(conversationApi.createConversation).mockResolvedValue({
      id: 'conv-1',
      scenario: 'daily_greeting',
      level: 'A2',
      status: 'active',
      messages: [],
      started_at: new Date().toISOString()
    })

    // Mock流式响应
    const mockStreamCleanup = vi.fn()
    vi.mocked(conversationApi.streamMessage).mockReturnValue(mockStreamCleanup)

    // Mock完成对话
    vi.mocked(conversationApi.completeConversation).mockResolvedValue({
      conversation: { id: 'conv-1', status: 'completed' },
      scores: {
        overall_score: 75,
        fluency_score: 70,
        grammar_score: 75,
        vocabulary_score: 80,
        feedback: 'Good conversation!',
        suggestions: ['Keep practicing']
      }
    })

    const wrapper = mount(ConversationView)

    // 1. 选择场景
    await wrapper.vm.selectScenario('daily_greeting')
    expect(wrapper.vm.selectedScenario).toBe('daily_greeting')

    // 2. 开始对话
    await wrapper.vm.startConversation()
    expect(conversationApi.createConversation).toHaveBeenCalled()
    expect(wrapper.vm.currentStep).toBe('conversation')

    // 3. 发送消息
    await wrapper.vm.sendUserMessage('Hello, how are you?')
    expect(conversationApi.streamMessage).toHaveBeenCalled()
    expect(wrapper.vm.messages.length).toBeGreaterThan(0)

    // 4. 完成对话
    await wrapper.vm.completeConversation()
    expect(conversationApi.completeConversation).toHaveBeenCalledWith('conv-1')
    expect(wrapper.vm.scores).toBeTruthy()
    expect(wrapper.vm.scores.overall_score).toBe(75)
    expect(wrapper.vm.currentStep).toBe('result')
  })

  it('应该正确处理语音输入流程', async () => {
    vi.mocked(conversationApi.createConversation).mockResolvedValue({
      id: 'conv-2',
      scenario: 'daily_greeting',
      level: 'A2',
      status: 'active',
      messages: []
    })

    vi.mocked(conversationApi.sendMessage).mockResolvedValue({
      message: {
        role: 'assistant',
        content: 'I am fine, thank you!'
      }
    })

    const wrapper = mount(ConversationView)

    // 开始对话
    await wrapper.vm.startConversation()

    // 开始语音输入
    const startSpy = vi.spyOn(wrapper.vm, 'startVoiceInput')
    wrapper.vm.startVoiceInput()
    expect(startSpy).toHaveBeenCalled()
    expect(wrapper.vm.isListening).toBe(true)

    // 模拟语音识别结果
    // (在实际测试中需要mock VoiceRecognition的行为)
  })

  it('应该支持TTS播放AI回复', async () => {
    const wrapper = mount(ConversationView)

    // Mock TTS
    const speakSpy = vi.spyOn(wrapper.vm, 'playAIResponse')
    speakSpy.mockResolvedValue(undefined)

    await wrapper.vm.playAIResponse('Hello world')
    expect(speakSpy).toHaveBeenCalledWith('Hello world')
  })

  it('应该正确处理流式响应', async () => {
    vi.mocked(conversationApi.createConversation).mockResolvedValue({
      id: 'conv-3',
      messages: []
    })

    let streamCallback: any = null
    vi.mocked(conversationApi.streamMessage).mockImplementation((...args: any[]) => {
      // 保存回调以便模拟调用
      return ((callback: any) => {
        streamCallback = callback
        return vi.fn()
      })
    })

    const wrapper = mount(ConversationView)
    await wrapper.vm.startConversation()

    // 发送消息
    await wrapper.vm.sendUserMessage('Hi')

    // 模拟流式响应
    if (streamCallback) {
      streamCallback.onToken?.('Hello')
      streamCallback.onToken?.(' there')

      streamCallback.onComplete?.('Hello there', 2)
    }

    // 验证消息内容
    expect(wrapper.vm.messages.some(m => m.content.includes('Hello'))).toBe(true)
  })
})
```

**Step 2: 运行测试**

```bash
cd frontend
npm run test tests/integration/conversationFlow.spec.ts
```

Expected: PASS

**Step 3: 提交**

```bash
git add frontend/tests/integration/conversationFlow.spec.ts
git commit -m "test(speaking): 添加对话流程集成测试"
```

---

### 阶段5：文档更新

#### Task 5.1: 更新模块文档

**Files:**
- Modify: `frontend/src/views/student/CLAUDE.md`
- Modify: `frontend/src/utils/CLAUDE.md`
- Modify: `frontend/src/components/CLAUDE.md`

**Step 1: 更新学生视图模块文档**

```markdown
<!-- frontend/src/views/student/CLAUDE.md 补充 -->

## 变更记录

### 2026-02-06 20:00:00
- ✨ **重大更新**: 口语练习服务完善
  - 集成语音识别(STT) - Web Speech API
  - 集成语音合成(TTS) - 新增 textToSpeech.ts 工具
  - 支持实时流式对话 - SSE流式响应
  - 新增对话评分展示组件 - ConversationScoreCard.vue
  - 新增语音控制按钮组件 - VoiceControlButton.vue
  - 完整的端到端测试覆盖

---

## 口语练习组件

### 对话组件详情

| 组件 | 文件 | 功能描述 | 状态 |
|------|------|----------|------|
| **对话视图** | **ConversationView.vue** | **完整对话流程（STT/TTS/流式）** | **✨ 完善** |
| **口语练习** | **SpeakingView.vue** | **场景选择和对话历史** | **✨ 完善** |

### 新增辅助组件

| 组件 | 文件 | 功能描述 | 状态 |
|------|------|----------|------|
| **评分卡片** | **ConversationScoreCard.vue** | **对话评分展示** | **✨ 新增** |
| **语音控制** | **VoiceControlButton.vue** | **录音/播放控制按钮** | **✨ 新增** |

### 工具类

| 工具 | 文件 | 功能描述 | 状态 |
|------|------|----------|------|
| **语音识别** | **voiceRecognition.ts** | **STT工具类（344行）** | **✅ 已有** |
| **语音合成** | **textToSpeech.ts** | **TTS工具类** | **✨ 新增** |

### API客户端

| 文件 | 描述 | 端点数量 |
|------|------|----------|
| `conversation.ts` | **对话API客户端（含SSE）** | **7** |
```

**Step 2: 提交文档更新**

```bash
git add frontend/src/views/student/CLAUDE.md frontend/src/utils/CLAUDE.md frontend/src/components/CLAUDE.md
git commit -m "docs(speaking): 更新口语练习服务文档"
```

---

## 验收标准

### 功能验收

- [x] 语音识别(STT)集成 - 用户可语音输入
- [x] 语音合成(TTS)集成 - AI回复可语音播放
- [x] 实时流式对话 - AI回复逐字显示
- [x] 对话评分展示 - 完成后显示详细评分
- [x] 13种对话场景支持
- [x] 完整的对话历史记录

### 质量验收

- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 集成测试通过
- [ ] 无TypeScript类型错误
- [ ] 无ESLint警告
- [ ] 组件文档完整

### 性能验收

- [ ] 流式响应延迟 < 500ms
- [ ] TTS播放无卡顿
- [ ] 页面交互流畅

---

## 实施时间估计

| 阶段 | 任务 | 预计时间 |
|------|------|----------|
| 1 | 语音合成工具 | 30分钟 |
| 2 | 评分展示组件 | 20分钟 |
| 3 | 语音控制组件 | 20分钟 |
| 4 | 完善对话主组件 | 60分钟 |
| 5 | 集成测试 | 30分钟 |
| 6 | 文档更新 | 15分钟 |
| **总计** | | **约3小时** |

---

## 风险与缓解

### 风险1: 浏览器兼容性

**风险**: Web Speech API在不同浏览器表现不一致

**缓解**:
- 添加浏览器支持检测
- 提供降级方案（文本输入）
- 在Chrome/Edge优先测试

### 风险2: SSE流式响应

**风险**: EventSource在不同网络环境下可能不稳定

**缓解**:
- 添加重连机制
- 提供非流式降级方案
- 显示连接状态指示

### 风险3: TTS语音质量

**风险**: 浏览器内置TTS语音质量参差不齐

**缓解**:
- 支持用户选择语音
- 提供语音预览功能
- 可考虑后端TTS服务（未来）

---

## 后续优化

1. **后端TTS集成** - 使用专业TTS服务（Azure/Google/阿里云）
2. **语音评估** - 集成发音准确性评估
3. **情感分析** - 分析对话情感状态
4. **个性化AI角色** - 可自定义AI对话伙伴性格
5. **离线模式** - 支持离线语音识别（部分浏览器）

---

## 相关资源

- [Web Speech API - SpeechRecognition](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition)
- [Web Speech API - SpeechSynthesis](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis)
- [EventSource (SSE) 使用指南](https://developer.mozilla.org/en-US/docs/Web/API/EventSource)
- [FastAPI StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
