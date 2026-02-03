/**
 * 认证 API 客户端
 * 处理用户注册、登录、token刷新等认证相关操作
 */
import axios from 'axios'
import type {
  RegisterRequest,
  LoginRequest,
  AuthResponse,
  User,
  RefreshTokenRequest
} from '@/types/auth'

// 创建 axios 实例
const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器：添加 token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器：处理错误
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      // 清除 token，跳转登录
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

/**
 * 认证 API
 */
export const authApi = {
  /**
   * 用户注册
   */
  async register(data: RegisterRequest): Promise<AuthResponse> {
    return api.post('/auth/register', data)
  },

  /**
   * 用户登录
   */
  async login(data: LoginRequest): Promise<AuthResponse> {
    return api.post('/auth/login', data)
  },

  /**
   * 刷新 token
   */
  async refreshToken(data: RefreshTokenRequest): Promise<{ access_token: string }> {
    return api.post('/auth/refresh', data)
  },

  /**
   * 获取当前用户信息
   */
  async getCurrentUser(): Promise<{ user: User }> {
    return api.get('/auth/me')
  },

  /**
   * 修改密码
   */
  async changePassword(data: {
    old_password: string
    new_password: string
  }): Promise<void> {
    return api.post('/auth/change-password', data)
  }
}
