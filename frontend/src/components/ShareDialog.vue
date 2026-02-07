<template>
  <el-dialog
    v-model="dialogVisible"
    title="分享教案"
    width="500px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      label-width="80px"
    >
      <!-- 选择接收教师 -->
      <el-form-item
        label="分享给"
        required
      >
        <el-select
          v-model="form.shared_to"
          filterable
          remote
          reserve-keyword
          placeholder="搜索教师姓名或邮箱"
          :remote-method="searchTeachers"
          :loading="searchLoading"
          style="width: 100%"
        >
          <el-option
            v-for="teacher in teacherOptions"
            :key="teacher.id"
            :label="teacher.label"
            :value="teacher.id"
          >
            <div class="teacher-option">
              <span class="teacher-name">{{ teacher.name }}</span>
              <span class="teacher-email">{{ teacher.email }}</span>
            </div>
          </el-option>
        </el-select>
      </el-form-item>

      <!-- 分享权限 -->
      <el-form-item
        label="权限"
        required
      >
        <el-radio-group v-model="form.permission">
          <el-radio
            v-for="perm in SHARE_PERMISSIONS"
            :key="perm.value"
            :label="perm.value"
          >
            {{ perm.label }}
          </el-radio>
        </el-radio-group>
      </el-form-item>

      <!-- 分享附言 -->
      <el-form-item label="附言">
        <el-input
          v-model="form.message"
          type="textarea"
          :rows="3"
          placeholder="添加分享附言（可选）"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>

      <!-- 有效期 -->
      <el-form-item label="有效期">
        <el-radio-group v-model="expiresType">
          <el-radio label="">
            永久有效
          </el-radio>
          <el-radio label="custom">
            自定义天数
          </el-radio>
        </el-radio-group>
        <el-input-number
          v-if="expiresType === 'custom'"
          v-model="form.expires_days"
          :min="1"
          :max="365"
          placeholder="天数"
          style="width: 150px; margin-left: 10px"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">
        取消
      </el-button>
      <el-button
        type="primary"
        :loading="sharing"
        @click="handleShare"
      >
        分享
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { shareLessonPlan, SHARE_PERMISSIONS } from '@/api/lessonShare'

interface Props {
  modelValue: boolean
  lessonPlanId: string
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

const sharing = ref(false)
const searchLoading = ref(false)

// 表单数据
const form = reactive({
  shared_to: '',
  permission: 'view',
  message: '',
  expires_days: null
})

const expiresType = ref('')

// 教师选项（搜索结果）
const teacherOptions = ref<Array<{ id: string; name: string; email: string; label: string }>>([])

// 搜索教师
const searchTeachers = async (query: string) => {
  if (!query) {
    teacherOptions.value = []
    return
  }

  searchLoading.value = true
  try {
    // 调用真实的教师搜索API
    const { searchUsers } = await import('@/api/user')
    const response = await searchUsers({
      q: query,
      role: 'teacher',
      limit: 10
    })

    teacherOptions.value = response.users.map(t => ({
      id: t.id,
      name: t.full_name || t.username,
      email: t.email,
      label: `${t.full_name || t.username} (${t.email})`
    }))
  } catch (error) {
    console.error('搜索教师失败:', error)
    ElMessage.error('搜索教师失败')
  } finally {
    searchLoading.value = false
  }
}

// 分享教案
const handleShare = async () => {
  // 验证表单
  if (!form.shared_to) {
    ElMessage.warning('请选择要分享的教师')
    return
  }

  try {
    sharing.value = true

    await shareLessonPlan(props.lessonPlanId, {
      shared_to: form.shared_to,
      permission: form.permission,
      message: form.message || undefined,
      expires_days: expiresType.value === 'custom' ? (form.expires_days ?? undefined) : undefined
    })

    ElMessage.success('教案已分享')
    emit('success')
    handleClose()
  } catch (error: any) {
    console.error('分享失败:', error)
    ElMessage.error(error.response?.data?.detail || '分享失败')
  } finally {
    sharing.value = false
  }
}

// 关闭对话框
const handleClose = () => {
  // 重置表单
  form.shared_to = ''
  form.permission = 'view'
  form.message = ''
  form.expires_days = null
  expiresType.value = ''
  teacherOptions.value = []

  dialogVisible.value = false
}

// 导出供父组件使用的方法
defineExpose({
  open: (teacherId?: string, permission?: string) => {
    dialogVisible.value = true
    if (teacherId) {
      form.shared_to = teacherId
    }
    if (permission) {
      form.permission = permission
    }
  }
})
</script>

<style scoped>
.teacher-option {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.teacher-name {
  font-weight: 500;
  color: #303133;
}

.teacher-email {
  font-size: 12px;
  color: #909399;
}
</style>
