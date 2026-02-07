<!--
  模板预览抽屉组件
  展示模板的详细信息和结构
-->
<template>
  <el-drawer
    :model-value="modelValue"
    :title="template?.name || '模板预览'"
    direction="rtl"
    size="50%"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <div
      v-if="isLoading"
      v-loading="true"
      style="height: 200px"
    ></div>

    <div
      v-else-if="template"
      class="preview-content"
    >
      <!-- 操作按钮 -->
      <div class="preview-actions">
        <el-button
          type="primary"
          :icon="Plus"
          @click="handleApply"
        >
          应用此模板
        </el-button>
        <el-button
          :icon="Edit"
          @click="handleEdit"
        >
          编辑
        </el-button>
        <el-button
          :icon="CopyDocument"
          @click="handleDuplicate"
        >
          复制
        </el-button>
      </div>

      <!-- 基本信息 -->
      <el-descriptions
        :column="2"
        border
        class="info-section"
      >
        <el-descriptions-item label="模板名称">
          {{ template.name }}
        </el-descriptions-item>
        <el-descriptions-item label="分类">
          <el-tag>{{ template.category.label }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="难度级别">
          <el-tag :type="getLevelType(template.level)">
            {{ template.level }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="建议时长">
          {{ template.duration }} 分钟
        </el-descriptions-item>
        <el-descriptions-item label="使用次数">
          {{ template.usage_count }} 次
        </el-descriptions-item>
        <el-descriptions-item label="评分">
          <el-rate
            v-model="template.rating"
            disabled
            show-score
          />
        </el-descriptions-item>
        <el-descriptions-item
          label="状态"
          :span="2"
        >
          <el-space>
            <el-tag
              v-if="template.is_official"
              type="warning"
            >
              官方模板
            </el-tag>
            <el-tag
              v-if="template.is_public"
              type="success"
            >
              公开
            </el-tag>
            <el-tag
              v-else
              type="info"
            >
              私有
            </el-tag>
          </el-space>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 描述 -->
      <div class="description-section">
        <h3>模板描述</h3>
        <p>{{ template.description }}</p>
      </div>

      <!-- 结构说明 -->
      <div class="structure-section">
        <h3>教学结构</h3>
        <el-timeline>
          <el-timeline-item
            v-for="(section, index) in template.structure.sections"
            :key="index"
            :timestamp="`${section.duration}分钟`"
            placement="top"
          >
            <div class="section-item">
              <h4>{{ section.label }}</h4>
              <el-tag
                v-if="section.required"
                size="small"
                type="danger"
              >
                必需
              </el-tag>
            </div>
          </el-timeline-item>
        </el-timeline>
      </div>

      <!-- 包含内容 -->
      <div class="includes-section">
        <h3>包含内容</h3>
        <el-row :gutter="16">
          <el-col :span="12">
            <div class="include-item">
              <el-icon><Aim /></el-icon>
              <span>教学目标</span>
              <el-tag
                size="small"
                type="success"
              >
                {{ template.structure.objectives?.length || 0 }} 个
              </el-tag>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="include-item">
              <el-icon><CollectionTag /></el-icon>
              <span>词汇</span>
              <el-tag
                size="small"
                type="success"
              >
                {{ getVocabularyCount() }} 个
              </el-tag>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="include-item">
              <el-icon><Notebook /></el-icon>
              <span>语法点</span>
              <el-tag
                size="small"
                type="success"
              >
                {{ template.structure.grammar_points?.length || 0 }} 个
              </el-tag>
            </div>
          </el-col>
        </el-row>
      </div>
    </div>

    <el-empty
      v-else
      description="加载失败"
    />
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import {
  Plus,
  Edit,
  CopyDocument,
  Aim,
  CollectionTag,
  Notebook
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getTemplate } from '@/api/lessonTemplate'
import type { LessonTemplate } from '@/types/lessonTemplate'

interface Props {
  modelValue: boolean
  templateId: string
}

interface Emits {
  'update:modelValue': [value: boolean]
  apply: [templateId: string]
  edit: [template: LessonTemplate]
  duplicate: [templateId: string]
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 状态
const isLoading = ref(false)
const template = ref<LessonTemplate | null>(null)

// 加载模板详情
const loadTemplate = async () => {
  if (!props.templateId) return

  isLoading.value = true
  try {
    const response = await getTemplate(props.templateId)
    template.value = response.template
  } catch (error) {
    console.error('加载模板失败:', error)
    ElMessage.error('加载模板失败')
  } finally {
    isLoading.value = false
  }
}

// 监听 templateId 变化
watch(() => props.templateId, () => {
  if (props.templateId) {
    loadTemplate()
  }
}, { immediate: true })

// 获取级别对应的标签类型
const getLevelType = (level: string) => {
  const types: Record<string, any> = {
    A1: 'danger',
    A2: 'warning',
    B1: 'primary',
    B2: 'success',
    C1: 'info',
    C2: ''
  }
  return types[level] || 'info'
}

// 获取词汇数量
const getVocabularyCount = () => {
  if (!template.value?.structure.vocabulary) return 0
  const { nouns, verbs, adjectives } = template.value.structure.vocabulary
  return (nouns || 0) + (verbs || 0) + (adjectives || 0)
}

// 事件处理
const handleApply = () => {
  emit('apply', props.templateId)
}

const handleEdit = () => {
  if (template.value) {
    emit('edit', template.value)
  }
}

const handleDuplicate = () => {
  emit('duplicate', props.templateId)
}
</script>

<style scoped>
.preview-content {
  padding: 0 20px;
}

.preview-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.info-section {
  margin-bottom: 24px;
}

.description-section,
.structure-section,
.includes-section {
  margin-bottom: 24px;
}

.description-section h3,
.structure-section h3,
.includes-section h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.description-section p {
  margin: 0;
  color: var(--el-text-color-regular);
  line-height: 1.6;
}

.section-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-item h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.include-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: var(--el-fill-color-blank);
  border-radius: 8px;
  margin-bottom: 8px;
}

.include-item span {
  flex: 1;
}
</style>
