<!--
  模板编辑器对话框组件
  用于创建和编辑教案模板
-->
<template>
  <el-dialog
    :model-value="modelValue"
    :title="template ? '编辑模板' : '创建模板'"
    width="600px"
    @update:model-value="$emit('update:modelValue', $event)"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
    >
      <el-form-item label="模板名称" prop="name">
        <el-input
          v-model="formData.name"
          placeholder="请输入模板名称"
          maxlength="50"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="分类" prop="category_key">
        <el-select v-model="formData.category_key" placeholder="请选择分类">
          <el-option label="口语课" value="speaking" />
          <el-option label="听力课" value="listening" />
          <el-option label="阅读课" value="reading" />
          <el-option label="写作课" value="writing" />
          <el-option label="语法课" value="grammar" />
          <el-option label="词汇课" value="vocabulary" />
          <el-option label="综合课" value="comprehensive" />
        </el-select>
      </el-form-item>

      <el-form-item label="难度级别" prop="level">
        <el-select v-model="formData.level" placeholder="请选择级别">
          <el-option label="A1" value="A1" />
          <el-option label="A2" value="A2" />
          <el-option label="B1" value="B1" />
          <el-option label="B2" value="B2" />
          <el-option label="C1" value="C1" />
          <el-option label="C2" value="C2" />
        </el-select>
      </el-form-item>

      <el-form-item label="建议时长" prop="duration">
        <el-input-number
          v-model="formData.duration"
          :min="15"
          :max="180"
          :step="15"
          :controls-position="'right'"
        />
        <span style="margin-left: 8px">分钟</span>
      </el-form-item>

      <el-form-item label="描述" prop="description">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="3"
          placeholder="请输入模板描述"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="公开模板">
        <el-switch v-model="formData.is_public" />
        <span style="margin-left: 12px; color: var(--el-text-color-secondary)">
          公开后其他教师也可以使用此模板
        </span>
      </el-form-item>

      <!-- 结构配置（简化版） -->
      <el-form-item label="结构配置">
        <el-alert
          title="完整的结构编辑器正在开发中"
          type="info"
          :closable="false"
          show-icon
        />
        <div style="margin-top: 12px">
          <el-text size="small" type="info">
            当前使用默认教学结构，后续版本将支持自定义结构配置
          </el-text>
        </div>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="submitting">
        {{ template ? '保存' : '创建' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import type { TemplateListItem, CreateTemplateRequest } from '@/types/lessonTemplate'
import { createTemplate, updateTemplate } from '@/api/lessonTemplate'

interface Props {
  modelValue: boolean
  template?: TemplateListItem | null
}

interface Emits {
  'update:modelValue': [value: boolean]
  saved: []
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 表单引用
const formRef = ref<FormInstance>()

// 提交状态
const submitting = ref(false)

// 表单数据
const formData = reactive({
  name: '',
  category_key: '',
  level: 'B1' as const,
  duration: 45,
  description: '',
  is_public: false
})

// 表单验证规则
const formRules: FormRules = {
  name: [
    { required: true, message: '请输入模板名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  category_key: [
    { required: true, message: '请选择分类', trigger: 'change' }
  ],
  level: [
    { required: true, message: '请选择难度级别', trigger: 'change' }
  ],
  duration: [
    { required: true, message: '请输入建议时长', trigger: 'blur' }
  ],
  description: [
    { max: 200, message: '描述不能超过 200 个字符', trigger: 'blur' }
  ]
}

// 重置表单
const resetForm = () => {
  formData.name = ''
  formData.category_key = ''
  formData.level = 'B1'
  formData.duration = 45
  formData.description = ''
  formData.is_public = false
  formRef.value?.clearValidate()
}

// 填充表单（编辑模式）
const fillForm = (template: TemplateListItem) => {
  formData.name = template.name
  formData.category_key = template.category_key
  formData.level = template.level
  formData.duration = template.duration
  formData.description = template.description
  formData.is_public = template.is_public
}

// 监听模板变化
watch(() => props.template, (newTemplate) => {
  if (newTemplate) {
    fillForm(newTemplate)
  } else {
    resetForm()
  }
}, { immediate: true })

// 监听对话框打开
watch(() => props.modelValue, (isOpen) => {
  if (!isOpen && !props.template) {
    resetForm()
  }
})

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    // TODO: 添加完整的结构配置
    const data: CreateTemplateRequest = {
      name: formData.name,
      category_key: formData.category_key,
      level: formData.level,
      duration: formData.duration,
      description: formData.description,
      is_public: formData.is_public,
      structure: {
        sections: [
          { key: 'warm_up', label: '热身', duration: 5, required: true },
          { key: 'presentation', label: '呈现', duration: 10, required: true },
          { key: 'practice', label: '练习', duration: 20, required: true },
          { key: 'production', label: '产出', duration: 8, required: true },
          { key: 'summary', label: '总结', duration: 2, required: true }
        ],
        objectives: [],
        vocabulary: { nouns: 10, verbs: 8, adjectives: 5 },
        grammar_points: []
      }
    }

    if (props.template) {
      await updateTemplate(props.template.id, data)
      ElMessage.success('模板更新成功')
    } else {
      await createTemplate(data)
      ElMessage.success('模板创建成功')
    }

    emit('saved')
    resetForm()
  } catch (error) {
    console.error('保存模板失败:', error)
    ElMessage.error('保存模板失败')
  } finally {
    submitting.value = false
  }
}

// 关闭对话框
const handleClose = () => {
  emit('update:modelValue', false)
}
</script>

<style scoped>
.el-form {
  padding: 0 20px;
}
</style>
