<template>
  <div class="register-container">
    <el-card class="register-card">
      <template #header>
        <h2>AI英语教学系统 - 注册</h2>
      </template>

      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="100px"
        @submit.prevent="handleRegister"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="formData.username"
            placeholder="请输入用户名"
            :prefix-icon="User"
          />
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="formData.email"
            type="email"
            placeholder="请输入邮箱"
            :prefix-icon="Message"
          />
        </el-form-item>

        <el-form-item label="角色" prop="role">
          <el-radio-group v-model="formData.role">
            <el-radio-button value="student">学生</el-radio-button>
            <el-radio-button value="teacher">教师</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item
          v-if="formData.role === 'teacher'"
          label="机构名称"
          prop="organization_name"
        >
          <el-input
            v-model="formData.organization_name"
            placeholder="请输入机构名称（可选）"
            :prefix-icon="OfficeBuilding"
          />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="formData.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-form-item label="确认密码" prop="confirm_password">
          <el-input
            v-model="formData.confirm_password"
            type="password"
            placeholder="请再次输入密码"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            native-type="submit"
            :loading="loading"
            style="width: 100%"
            size="large"
          >
            注册
          </el-button>
        </el-form-item>

        <el-form-item>
          <div class="login-link">
            已有账号？
            <router-link to="/login">立即登录</router-link>
          </div>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock, Message, OfficeBuilding } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import type { RegisterRequest } from '@/types/auth'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref<FormInstance>()
const loading = ref(false)

const formData = reactive<RegisterRequest>({
  username: '',
  email: '',
  password: '',
  confirm_password: '',
  role: 'student',
  organization_name: ''
})

// 自定义验证规则
const validateConfirmPassword = (
  rule: unknown,
  value: string,
  callback: (error?: Error) => void
) => {
  if (value !== formData.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度3-50位', trigger: 'blur' },
    {
      pattern: /^[a-zA-Z0-9_]+$/,
      message: '用户名只能包含字母、数字和下划线',
      trigger: 'blur'
    }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    {
      type: 'email',
      message: '请输入正确的邮箱格式',
      trigger: 'blur'
    }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 50, message: '密码长度6-50位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

async function handleRegister() {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    loading.value = true

    await authStore.register(formData)

    ElMessage.success('注册成功')

    // 根据角色跳转
    if (authStore.isStudent) {
      router.push('/student')
    } else if (authStore.isTeacher) {
      router.push('/teacher')
    } else {
      router.push('/')
    }
  } catch (error: any) {
    if (error?.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else if (error instanceof Error) {
      ElMessage.error(error.message)
    } else {
      ElMessage.error('注册失败，请稍后重试')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.register-card {
  width: 480px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

h2 {
  margin: 0;
  text-align: center;
  color: #333;
}

.login-link {
  text-align: center;
  color: #666;
}

.login-link a {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
}

.login-link a:hover {
  text-decoration: underline;
}
</style>
