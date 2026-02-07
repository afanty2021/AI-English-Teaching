<template>
  <div class="question-renderer">
    <!-- 题目元信息 -->
    <div
      v-if="showMeta"
      class="question-meta"
    >
      <el-tag
        v-if="question.difficulty_level"
        size="small"
        type="info"
      >
        难度：{{ question.difficulty_level }}
      </el-tag>
      <el-tag
        v-if="question.topic"
        size="small"
        type="success"
        style="margin-left: 8px"
      >
        主题：{{ question.topic }}
      </el-tag>
      <div
        v-if="question.knowledge_points?.length"
        class="knowledge-points"
      >
        <el-tag
          v-for="point in question.knowledge_points"
          :key="point"
          size="small"
          style="margin-left: 4px"
        >
          {{ point }}
        </el-tag>
      </div>
    </div>

    <!-- 音频播放器（听力题） -->
    <div
      v-if="question.audio_url"
      class="audio-player"
    >
      <audio
        controls
        :src="question.audio_url"
      >
        您的浏览器不支持音频播放
      </audio>
    </div>

    <!-- 根据题目类型渲染不同组件 -->
    <ChoiceQuestion
      v-if="isChoiceType"
      :question="question"
      :model-value="modelValue"
      :submitted="submitted"
      :show-result="showResult"
      @update:model-value="$emit('update:modelValue', $event)"
      @submit="$emit('submit', $event)"
    />
    <FillBlankQuestion
      v-else-if="question.question_type === 'fill_blank'"
      :question="question"
      :model-value="modelValue"
      :submitted="submitted"
      :show-result="showResult"
      @update:model-value="$emit('update:modelValue', $event)"
      @submit="$emit('submit', $event)"
    />
    <ReadingQuestion
      v-else-if="question.question_type === 'reading'"
      :question="question"
      :model-value="modelValue"
      :submitted="submitted"
      :show-result="showResult"
      @update:model-value="$emit('update:modelValue', $event)"
      @submit="$emit('submit', $event)"
    />
    <div
      v-else
      class="unsupported-type"
    >
      <el-empty description="暂不支持此题型">
        <template #image>
          <el-icon :size="60">
            <Warning />
          </el-icon>
        </template>
      </el-empty>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Warning } from '@element-plus/icons-vue'
import ChoiceQuestion from './ChoiceQuestion.vue'
import FillBlankQuestion from './FillBlankQuestion.vue'
import ReadingQuestion from './ReadingQuestion.vue'
import type { Question } from '@/types/question'

interface Props {
  question: Question
  modelValue?: any
  submitted?: boolean
  showResult?: boolean
  showMeta?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: any): void
  (e: 'submit', answer: any): void
}

const props = withDefaults(defineProps<Props>(), {
  submitted: false,
  showResult: false,
  showMeta: true
})

defineEmits<Emits>()

// 判断是否为选择题类型
const isChoiceType = computed(() => {
  return props.question.question_type === 'choice' ||
         props.question.question_type === 'listening' ||
         props.question.question_type === 'reading'
})
</script>

<style scoped>
.question-renderer {
  padding: 16px;
}

.question-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  margin-bottom: 16px;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.knowledge-points {
  display: flex;
  flex-wrap: wrap;
  margin-left: 8px;
}

.audio-player {
  margin-bottom: 16px;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
  text-align: center;
}

.audio-player audio {
  width: 100%;
  max-width: 500px;
}

.unsupported-type {
  padding: 40px;
  text-align: center;
}
</style>
