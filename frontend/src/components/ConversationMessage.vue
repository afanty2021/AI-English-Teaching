<template>
  <div
    :class="['conversation-message', `message-${message.role}`, { 'message-highlight': isHighlighted }]"
  >
    <!-- 头像区域 -->
    <div class="message-avatar">
      <el-avatar v-if="message.role === 'user'" :icon="User" />
      <el-avatar v-else :icon="ChatDotRound" />
    </div>

    <!-- 消息内容区域 -->
    <div class="message-content-wrapper">
      <!-- 消息头部（显示时间戳和状态） -->
      <div v-if="showHeader" class="message-header">
        <span class="message-time">{{ formatTime(message.timestamp) }}</span>
        <el-tag v-if="message.is_final" type="success" size="small">最终回复</el-tag>
      </div>

      <!-- 消息主体 -->
      <div :class="['message-body', { 'streaming-body': isStreaming }]">
        <!-- 文本内容 -->
        <div v-if="message.type === 'text'" class="message-text">
          <span v-html="highlightedContent"></span>
          <span v-if="isStreaming" class="typing-cursor"></span>
        </div>

        <!-- 音频内容 -->
        <div v-else-if="message.type === 'audio'" class="message-audio">
          <el-button :icon="VideoPlay" circle @click="playAudio" />
          <audio v-if="message.audio_url" ref="audioRef" :src="message.audio_url" />
        </div>

        <!-- 系统消息 -->
        <div v-else class="message-system">
          <el-icon><InfoFilled /></el-icon>
          <span>{{ message.content }}</span>
        </div>
      </div>

      <!-- AI 评分（助手消息） -->
      <div v-if="showScores" class="message-scores">
        <div class="scores-header">
          <el-icon><Trophy /></el-icon>
          <span>AI 评分</span>
        </div>
        <div class="scores-grid">
          <div
            v-for="score in flattenedScores"
            :key="score.name"
            :class="['score-item', getScoreClass(score.score, score.max_score)]"
          >
            <span class="score-name">{{ score.name }}</span>
            <span class="score-value">{{ score.score }}/{{ score.max_score }}</span>
          </div>
        </div>
      </div>

      <!-- 语法错误反馈 -->
      <div v-if="message.grammar_errors && message.grammar_errors.length > 0" class="grammar-feedback">
        <div class="feedback-header">
          <el-icon><Document /></el-icon>
          <span>语法建议</span>
        </div>
        <div class="grammar-errors">
          <div
            v-for="(error, index) in message.grammar_errors"
            :key="index"
            class="grammar-error-item"
          >
            <span class="error-original">{{ error.original }}</span>
            <el-icon><Right /></el-icon>
            <span class="error-correction">{{ error.correction }}</span>
            <el-tooltip :content="error.explanation" placement="top">
              <el-icon><QuestionFilled /></el-icon>
            </el-tooltip>
          </div>
        </div>
      </div>

      <!-- 发音反馈 -->
      <div v-if="message.pronunciation_feedback && message.pronunciation_feedback.length > 0" class="pronunciation-feedback">
        <div class="feedback-header">
          <el-icon><Microphone /></el-icon>
          <span>发音反馈</span>
        </div>
        <div class="pronunciation-items">
          <div
            v-for="(feedback, index) in message.pronunciation_feedback"
            :key="index"
            :class="['pronunciation-item', getScoreClass(feedback.score, 100)]"
          >
            <span class="pronunciation-word">{{ feedback.word }}</span>
            <span class="pronunciation-phonetic">/{{ feedback.phonetic }}/</span>
            <span class="pronunciation-score">{{ feedback.score }}</span>
            <el-icon v-if="feedback.audio_url" class="play-icon" @click="playPronunciationAudio(feedback.audio_url)">
              <VideoPlay />
            </el-icon>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  User,
  ChatDotRound,
  VideoPlay,
  Trophy,
  Document,
  Right,
  QuestionFilled,
  Microphone,
  InfoFilled
} from '@element-plus/icons-vue'
import type { ConversationMessage, ScoreDimension } from '@/types/conversation'

interface Props {
  message: ConversationMessage
  showHeader?: boolean
  isHighlighted?: boolean
  isStreaming?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showHeader: true,
  isHighlighted: false,
  isStreaming: false
})

const audioRef = ref<HTMLAudioElement>()

// 格式化时间
const formatTime = (timestamp: string) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// 高亮显示内容（处理语法错误）
const highlightedContent = computed(() => {
  if (props.message.role === 'user' || !props.message.grammar_errors) {
    return props.message.content
  }

  let content = props.message.content
  const errors = [...props.message.grammar_errors].sort((a, b) =>
    (b.position?.start || 0) - (a.position?.start || 0)
  )

  errors.forEach(error => {
    const before = content.substring(0, error.position?.start || 0)
    const errorText = content.substring(
      error.position?.start || 0,
      error.position?.end || content.length
    )
    const after = content.substring(error.position?.end || content.length)

    content = `${before}<mark class="error-highlight" title="${error.explanation}">${errorText}</mark>${after}`
  })

  return content
})

// 是否显示评分
const showScores = computed(() => {
  return props.message.role === 'assistant' &&
         props.message.scores &&
         props.message.scores.length > 0
})

// 展平评分数据
const flattenedScores = computed(() => {
  if (!props.message.scores) return []

  const scores: ScoreDimension[] = []
  props.message.scores.forEach((dimension: any) => {
    if (typeof dimension === 'object' && 'name' in dimension) {
      scores.push(dimension)
    }
  })
  return scores
})

// 获取评分等级样式
const getScoreClass = (score: number, maxScore: number) => {
  const percentage = (score / maxScore) * 100
  if (percentage >= 80) return 'score-excellent'
  if (percentage >= 60) return 'score-good'
  if (percentage >= 40) return 'score-fair'
  return 'score-poor'
}

// 播放音频
const playAudio = () => {
  if (audioRef.value) {
    audioRef.value.currentTime = 0
    audioRef.value.play()
  }
}

// 播放发音反馈音频
const playPronunciationAudio = (url: string) => {
  const audio = new Audio(url)
  audio.play()
}
</script>

<style scoped>
.conversation-message {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  animation: messageIn 0.3s ease-out;
}

@keyframes messageIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-user {
  flex-direction: row-reverse;
}

.message-assistant {
  flex-direction: row;
}

.message-avatar {
  flex-shrink: 0;
}

.message-content-wrapper {
  max-width: 70%;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.message-user .message-content-wrapper {
  align-items: flex-end;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.message-user .message-header {
  flex-direction: row-reverse;
}

.message-body {
  padding: 12px 16px;
  border-radius: 12px;
  word-break: break-word;
}

.message-user .message-body {
  background: var(--el-color-primary);
  color: var(--el-color-primary-light-9);
}

.message-assistant .message-body {
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color);
}

.message-text {
  line-height: 1.6;
}

.message-text :deep(.error-highlight) {
  background: var(--el-color-danger-light-9);
  border-radius: 2px;
  padding: 0 2px;
}

/* 流式消息样式 */
.streaming-body {
  animation: messageIn 0.3s ease-out;
}

.typing-cursor {
  display: inline-block;
  width: 2px;
  height: 1em;
  background: var(--el-color-primary);
  margin-left: 2px;
  animation: cursorBlink 1s step-end infinite;
  vertical-align: text-bottom;
}

@keyframes cursorBlink {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0;
  }
}

.message-audio {
  display: flex;
  align-items: center;
  gap: 8px;
}

.message-system {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--el-fill-color-blank);
  border-radius: 8px;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.message-scores {
  padding: 12px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  border-radius: 8px;
}

.scores-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 14px;
  color: var(--el-text-color-primary);
  margin-bottom: 8px;
}

.scores-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 8px;
}

.score-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 10px;
  background: white;
  border-radius: 6px;
  font-size: 13px;
}

.score-name {
  font-weight: 500;
}

.score-value {
  font-weight: 600;
}

.score-excellent { color: var(--el-color-success); }
.score-good { color: var(--el-color-primary); }
.score-fair { color: var(--el-color-warning); }
.score-poor { color: var(--el-color-danger); }

.grammar-feedback,
.pronunciation-feedback {
  padding: 12px;
  background: var(--el-fill-color-blank);
  border-radius: 8px;
  border-left: 3px solid var(--el-color-warning);
}

.feedback-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 8px;
  color: var(--el-text-color-primary);
}

.grammar-errors {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.grammar-error-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: white;
  border-radius: 6px;
  font-size: 13px;
}

.error-original {
  color: var(--el-color-danger);
  text-decoration: line-through;
}

.error-correction {
  color: var(--el-color-success);
  font-weight: 500;
}

.pronunciation-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.pronunciation-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: white;
  border-radius: 6px;
  font-size: 13px;
}

.pronunciation-word {
  font-weight: 500;
}

.pronunciation-phonetic {
  color: var(--el-text-color-secondary);
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.pronunciation-score {
  margin-left: auto;
  font-weight: 600;
}

.play-icon {
  cursor: pointer;
  color: var(--el-color-primary);
  transition: color 0.2s;
}

.play-icon:hover {
  color: var(--el-color-primary-light-3);
}

.message-highlight {
  animation: highlightPulse 2s ease-in-out;
}

@keyframes highlightPulse {
  0%, 100% {
    background-color: transparent;
  }
  50% {
    background-color: var(--el-color-primary-light-9);
  }
}
</style>
