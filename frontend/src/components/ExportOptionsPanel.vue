<!--
  教案导出选项面板组件
  用于配置导出格式、内容选项等
-->
<template>
  <div class="export-options-panel">
    <!-- 导出格式选择 -->
    <div class="option-section">
      <h4 class="section-title">
        <el-icon><Document /></el-icon>
        导出格式
      </h4>
      <el-radio-group v-model="localOptions.format" class="format-selector">
        <el-radio-button value="word">
          <div class="format-option">
            <el-icon><Document /></el-icon>
            <span>Word</span>
          </div>
        </el-radio-button>
        <el-radio-button value="pdf">
          <div class="format-option">
            <el-icon><Tickets /></el-icon>
            <span>PDF</span>
          </div>
        </el-radio-button>
        <el-radio-button value="pptx">
          <div class="format-option">
            <el-icon><Notebook /></el-icon>
            <span>PPT</span>
          </div>
        </el-radio-button>
        <el-radio-button value="markdown">
          <div class="format-option">
            <el-icon><DocumentCopy /></el-icon>
            <span>Markdown</span>
          </div>
        </el-radio-button>
      </el-radio-group>
    </div>

    <!-- 内容选择 -->
    <div class="option-section">
      <h4 class="section-title">
        <el-icon><List /></el-icon>
        导出内容
      </h4>
      <el-checkbox-group v-model="localOptions.sections" class="sections-grid">
        <el-checkbox value="overview">概览信息</el-checkbox>
        <el-checkbox value="objectives">教学目标</el-checkbox>
        <el-checkbox value="vocabulary">核心词汇</el-checkbox>
        <el-checkbox value="grammar">语法点</el-checkbox>
        <el-checkbox value="structure">教学流程</el-checkbox>
        <el-checkbox value="materials">教学材料</el-checkbox>
        <el-checkbox value="exercises">练习题</el-checkbox>
      </el-checkbox-group>
    </div>

    <!-- 高级选项 -->
    <el-collapse class="advanced-options">
      <el-collapse-item name="advanced" title="高级选项">
        <!-- 语言设置 -->
        <div class="option-item">
          <span class="option-label">导出语言：</span>
          <el-radio-group v-model="localOptions.language" size="small">
            <el-radio-button value="zh">中文</el-radio-button>
            <el-radio-button value="en">英文</el-radio-button>
            <el-radio-button value="bilingual">双语</el-radio-button>
          </el-radio-group>
        </div>

        <!-- 包含选项 -->
        <div class="option-item">
          <el-space direction="vertical" :size="8">
            <el-checkbox v-model="localOptions.include_teacher_notes">
              包含教师备注
            </el-checkbox>
            <el-checkbox v-model="localOptions.include_answers">
              包含练习答案
            </el-checkbox>
            <el-checkbox v-model="localOptions.include_page_numbers">
              包含页码
            </el-checkbox>
            <el-checkbox v-model="localOptions.include_toc">
              包含目录
            </el-checkbox>
          </el-space>
        </div>

        <!-- 样式模板 -->
        <div class="option-item">
          <span class="option-label">样式模板：</span>
          <el-select v-model="localOptions.template_id" placeholder="选择模板" style="width: 200px">
            <el-option label="默认模板" value="" />
            <el-option label="简约模板" value="minimal" />
            <el-option label="详细模板" value="detailed" />
            <el-option label="彩色模板" value="colorful" />
          </el-select>
        </div>
      </el-collapse-item>
    </el-collapse>

    <!-- 预设模板 -->
    <div class="option-section">
      <h4 class="section-title">
        <el-icon><MagicStick /></el-icon>
        快捷预设
      </h4>
      <el-space wrap>
        <el-button size="small" @click="applyPreset('complete')">
          完整导出
        </el-button>
        <el-button size="small" @click="applyPreset('minimal')">
          精简导出
        </el-button>
        <el-button size="small" @click="applyPreset('print')">
          打印版
        </el-button>
        <el-button size="small" @click="applyPreset('archive')">
          归档版
        </el-button>
      </el-space>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'
import {
  Document,
  Tickets,
  Notebook,
  DocumentCopy,
  List,
  MagicStick
} from '@element-plus/icons-vue'
import type { ExportOptions, ExportSection } from '@/types/lessonExport'

interface Props {
  modelValue: ExportOptions
}

interface Emits {
  'update:modelValue': [value: ExportOptions]
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 本地选项（用于双向绑定）
const localOptions = reactive<ExportOptions>({ ...props.modelValue })

// 监听变化，同步到父组件
watch(localOptions, (newOptions) => {
  emit('update:modelValue', { ...newOptions })
}, { deep: true })

// 监听父组件变化
watch(() => props.modelValue, (newOptions) => {
  Object.assign(localOptions, newOptions)
}, { deep: true })

// 应用预设
const applyPreset = (preset: string) => {
  const allSections: ExportSection[] = [
    'overview', 'objectives', 'vocabulary', 'grammar',
    'structure', 'materials', 'exercises'
  ]

  switch (preset) {
    case 'complete':
      localOptions.sections = allSections
      localOptions.include_teacher_notes = true
      localOptions.include_answers = true
      localOptions.include_page_numbers = true
      localOptions.include_toc = true
      break
    case 'minimal':
      localOptions.sections = ['overview', 'structure']
      localOptions.include_teacher_notes = false
      localOptions.include_answers = false
      localOptions.include_page_numbers = false
      localOptions.include_toc = false
      break
    case 'print':
      localOptions.sections = ['overview', 'objectives', 'vocabulary', 'structure']
      localOptions.include_teacher_notes = false
      localOptions.include_answers = false
      localOptions.include_page_numbers = true
      localOptions.include_toc = true
      break
    case 'archive':
      localOptions.sections = allSections
      localOptions.include_teacher_notes = true
      localOptions.include_answers = true
      localOptions.include_page_numbers = true
      localOptions.include_toc = true
      break
  }
}
</script>

<style scoped>
.export-options-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.option-section {
  padding: 16px;
  background: var(--el-fill-color-blank);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

/* 格式选择器 */
.format-selector {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.format-option {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 章节网格 */
.sections-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 8px;
}

/* 高级选项 */
.advanced-options {
  border: none;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
}

.option-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--el-text-color-regular);
  min-width: 80px;
}

/* 响应式 */
@media (max-width: 768px) {
  .sections-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .format-selector {
    flex-direction: column;
  }

  .format-selector .el-radio-button {
    width: 100%;
  }
}
</style>
