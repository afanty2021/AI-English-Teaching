<!-- components/VoiceControlButton.vue -->
<template>
  <el-button
    :class="['voice-button', type, state, { disabled, circle }]"
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
    <span
      v-if="type === 'record' && state === 'listening'"
      class="ripple"
    ></span>
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
