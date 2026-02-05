/**
 * 认证状态管理
 * 使用 Pinia 管理用户认证状态和token
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types/auth'
import type { RegisterRequest, LoginRequest } from '@/types/auth'
import { authApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  // State - 从 localStorage 恢复认证状态
  const getUserFromStorage = (): User | null => {
    try {
      const userStr = localStorage.getItem('user')
      return userStr ? JSON.parse(userStr) : null
    } catch {
      return null
    }
  }

  const user = ref<User | null>(getUserFromStorage())
  const accessToken = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))

  // Computed
  const isAuthenticated = computed(() => !!accessToken.value)
  const isTeacher = computed(() => user.value?.role === 'teacher')
  const isStudent = computed(() => user.value?.role === 'student')
  const isAdmin = computed(() => user.value?.role === 'admin')

  /**
   * 用户注册
   */
  async function register(data: RegisterRequest) {
    const response = await authApi.register(data)

    user.value = response.user
    accessToken.value = response.access_token
    refreshToken.value = response.refresh_token

    // 保存到 localStorage
    localStorage.setItem('access_token', response.access_token)
    localStorage.setItem('refresh_token', response.refresh_token)
  }

  /**
   * 用户登录
   */
  async function login(data: LoginRequest) {
    const response = await authApi.login(data)

    user.value = response.user
    accessToken.value = response.access_token
    refreshToken.value = response.refresh_token

    // 保存到 localStorage
    localStorage.setItem('access_token', response.access_token)
    localStorage.setItem('refresh_token', response.refresh_token)
  }

  /**
   * 获取当前用户信息
   */
  async function fetchCurrentUser() {
    try {
      const response = await authApi.getCurrentUser()
      user.value = response.user
    } catch (error) {
      // token 无效，清除状态
      logout()
    }
  }

  /**
   * 刷新 access token
   */
  async function refreshAccessToken() {
    if (!refreshToken.value) {
      throw new Error('No refresh token available')
    }

    const response = await authApi.refreshToken({
      refresh_token: refreshToken.value
    })

    accessToken.value = response.access_token
    localStorage.setItem('access_token', response.access_token)
  }

  /**
   * 登出
   */
  function logout() {
    user.value = null
    accessToken.value = null
    refreshToken.value = null

    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  /**
   * 检查并刷新认证状态
   */
  async function checkAuth(): Promise<boolean> {
    if (!accessToken.value) {
      return false
    }

    try {
      await fetchCurrentUser()
      return true
    } catch {
      logout()
      return false
    }
  }

  return {
    // State
    user,
    accessToken,

    // Computed
    isAuthenticated,
    isTeacher,
    isStudent,
    isAdmin,

    // Actions
    register,
    login,
    fetchCurrentUser,
    refreshAccessToken,
    logout,
    checkAuth
  }
})
