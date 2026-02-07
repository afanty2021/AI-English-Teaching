<template>
  <el-dialog
    v-model="dialogVisible"
    :title="isEditMode ? '编辑模板' : '创建模板'"
    width="700px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="formRules"
      label-width="100px"
    >
      <!-- 模板名称 -->
      <el-form-item
        label="模板名称"
        prop="name"
      >
        <el-input
          v-model="form.name"
          placeholder="请输入模板名称"
          maxlength="50"
          show-word-limit
        />
      </el-form-item>

      <!-- 模板描述 -->
      <el-form-item label="模板描述">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="请输入模板描述（可选）"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>

      <!-- 导出格式 -->
      <el-form-item
        label="导出格式"
        prop="format"
      >
        <el-radio-group
          v-model="form.format"
          :disabled="isEditMode"
        >
          <el-radio value="word">
            Word (.docx)
          </el-radio>
          <el-radio value="pdf">
            PDF
          </el-radio>
          <el-radio value="pptx">
            PowerPoint (.pptx)
          </el-radio>
        </el-radio-group>
      </el-form-item>

      <!-- 模板文件 -->
      <el-form-item
        label="模板文件"
        prop="file"
      >
        <el-upload
          :auto-upload="false"
          :on-change="handleFileChange"
          :on-remove="handleFileRemove"
          :file-list="fileList"
          :limit="1"
          accept=".docx,.pptx"
          :disabled="isEditMode && !fileChanged"
        >
          <el-button type="primary">
            <el-icon><Upload /></el-icon>
            选择文件
          </el-button>
          <template #tip>
            <div class="upload-tip">
              {{ getFormatTip() }}
            </div>
          </template>
        </el-upload>
      </el-form-item>

      <!-- 变量定义 -->
      <el-form-item label="变量定义">
        <div class="variables-editor">
          <div class="variables-header">
            <span>定义模板中可替换的变量</span>
            <el-button
              type="primary"
              size="small"
              :icon="Plus"
              @click="addVariable"
            >
              添加变量
            </el-button>
          </div>
          <div class="variables-list">
            <div
              v-for="(variable, index) in form.variables"
              :key="index"
              class="variable-item"
            >
              <el-input
                v-model="variable.name"
                placeholder="变量名"
                style="width: 150px"
              />
              <el-input
                v-model="variable.description"
                placeholder="描述"
                style="width: 200px"
              />
              <el-input
                v-model="variable.default_value"
                placeholder="默认值"
                style="width: 120px"
              />
              <el-checkbox
                v-model="variable.required"
                label="必需"
              />
              <el-button
                type="danger"
                size="small"
                :icon="Delete"
                circle
                @click="removeVariable(index)"
              />
            </div>
            <el-empty
              v-if="form.variables.length === 0"
              description="暂无变量定义"
              :image-size="60"
            />
          </div>
        </div>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">
        取消
      </el-button>
      <el-button
        type="primary"
        :loading="submitting"
        @click="handleSubmit"
      >
        {{ isEditMode ? '保存' : '创建' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules, type UploadUserFile, type UploadFile } from 'element-plus'
import { Upload, Plus, Delete } from '@element-plus/icons-vue'
import { createTemplate, updateTemplate, type CreateTemplateRequest, type UpdateTemplateRequest, type ExportTemplate, type TemplateVariable } from '@/api/template'

// 浏览器全局变量类型声明

interface Props {
  modelValue: boolean
  template?: ExportTemplate | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const isEditMode = computed(() => !!props.template)

const formRef = ref<FormInstance>()
const submitting = ref(false)
const fileChanged = ref(false)
const fileList = ref<UploadUserFile[]>([])

// 表单数据
const form = reactive({
  name: '',
  description: '',
  format: 'word' as 'word' | 'pdf' | 'pptx',
  variables: [] as TemplateVariable[],
  file: null as File | null
})

// 表单验证规则
const formRules: FormRules = {
  name: [
    { required: true, message: '请输入模板名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  format: [
    { required: true, message: '请选择导出格式', trigger: 'change' }
  ],
  file: [
    {
      required: !isEditMode.value,
      validator: (_rule, _value, callback) => {
        if (!isEditMode.value && !form.file) {
          callback(new Error('请上传模板文件'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ]
}

// 监听模板变化，编辑模式填充表单
watch(() => props.template, (template) => {
  if (template) {
    form.name = template.name
    form.description = template.description
    form.format = template.format
    form.variables = [...template.variables]
    fileChanged.value = false
  } else {
    resetForm()
  }
}, { immediate: true })

// 获取格式提示
const getFormatTip = () => {
  const tips = {
    word: '支持上传 .docx 格式的 Word 模板文件',
    pdf: 'PDF 格式暂不支持直接上传，请使用 Word 格式',
    pptx: '支持上传 .pptx 格式的 PowerPoint 模板文件'
  }
  return tips[form.format]
}

// 处理文件选择
const handleFileChange = (file: UploadFile) => {
  if (file.raw) {
    form.file = file.raw
    fileChanged.value = true
  }
}

// 处理文件移除
const handleFileRemove = () => {
  form.file = null
  fileChanged.value = true
}

// 添加变量
const addVariable = () => {
  form.variables.push({
    name: '',
    description: '',
    default_value: '',
    required: false
  })
}

// 删除变量
const removeVariable = (index: number) => {
  form.variables.splice(index, 1)
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  // 验证变量定义
  const invalidVariables = form.variables.filter(v => !v.name || !v.description)
  if (invalidVariables.length > 0) {
    ElMessage.warning('请完善所有变量定义（名称和描述不能为空）')
    return
  }

  try {
    submitting.value = true

    if (isEditMode.value && props.template) {
      // 更新模板
      const updateData: UpdateTemplateRequest = {
        name: form.name,
        description: form.description,
        variables: form.variables
      }
      if (fileChanged.value && form.file) {
        updateData.file = form.file
      }
      await updateTemplate(props.template.id, updateData)
      ElMessage.success('模板已更新')
    } else {
      // 创建模板
      if (!form.file) {
        ElMessage.error('请上传模板文件')
        return
      }
      const createData: CreateTemplateRequest = {
        name: form.name,
        description: form.description,
        format: form.format,
        variables: form.variables,
        file: form.file
      }
      await createTemplate(createData)
      ElMessage.success('模板已创建')
    }

    emit('success')
    handleClose()
  } catch (error: any) {
    console.error('提交失败:', error)
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

// 重置表单
const resetForm = () => {
  form.name = ''
  form.description = ''
  form.format = 'word'
  form.variables = []
  form.file = null
  fileChanged.value = false
  fileList.value = []
  formRef.value?.clearValidate()
}

// 关闭对话框
const handleClose = () => {
  resetForm()
  dialogVisible.value = false
}

// 导出方法供父组件调用
defineExpose({
  open: () => {
    dialogVisible.value = true
  }
})
</script>

<style scoped>
.upload-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.variables-editor {
  width: 100%;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 12px;
  background-color: #fafafa;
}

.variables-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 500;
  color: #606266;
}

.variables-list {
  max-height: 200px;
  overflow-y: auto;
}

.variable-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  padding: 8px;
  background-color: #fff;
  border-radius: 4px;
}

.variable-item:last-child {
  margin-bottom: 0;
}
</style>
