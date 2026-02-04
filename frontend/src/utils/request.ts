/**
 * HTTP 请求工具模块
 * 基于 Axios 封装，提供统一的请求接口和错误处理
 */
// @ts-check
import axios from 'axios'
import type { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

/**
 * 请求配置接口
 */
interface RequestConfig extends InternalAxiosRequestConfig {
  skipAuth?: boolean
  skipErrorHandler?: boolean
}

/**
 * API 响应接口
 */
interface ApiResponse<T = any> {
  data: T
  message?: string
  code?: number
}

/**
 * 创建 Axios 实例
 */
const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'

const instance: AxiosInstance = axios.create({
  baseURL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

/**
 * 请求拦截器
 * 自动添加认证令牌
 */
instance.interceptors.request.use(
  (config: RequestConfig) => {
    // 如果不跳过认证，添加访问令牌
    if (!config.skipAuth && config.headers) {
      const authStore = useAuthStore()
      const token = authStore.accessToken
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
    return config
  },
  (error: any) => {
    return Promise.reject(error)
  }
)

/**
 * 响应拦截器
 * 处理认证错误和通用错误
 */
instance.interceptors.response.use(
  (response: any) => {
    // 直接返回响应数据
    return response.data
  },
  (error: AxiosError) => {
    // 如果跳过错误处理，直接抛出
    if (error.config?.skipErrorHandler) {
      return Promise.reject(error)
    }

    // 处理不同类型的错误
    if (error.response) {
      // 服务器返回错误状态码
      const status = error.response.status
      const data = error.response.data as ApiResponse

      switch (status) {
        case 401:
          // 未认证 - 清除认证状态并跳转登录
          const authStore = useAuthStore()
          authStore.logout()
          ElMessage.error('登录已过期，请重新登录')
          window.location.href = '/login'
          break

        case 403:
          // 无权限
          ElMessage.error(data.message || '您没有权限执行此操作')
          break

        case 404:
          // 资源不存在
          ElMessage.error(data.message || '请求的资源不存在')
          break

        case 422:
          // 请求参数验证失败
          ElMessage.error(data.message || '请求参数不正确')
          break

        case 500:
          // 服务器错误
          ElMessage.error(data.message || '服务器错误，请稍后重试')
          break

        default:
          ElMessage.error(data.message || `请求失败 (${status})`)
      }
    } else if (error.request) {
      // 请求已发送但没有收到响应
      ElMessage.error('网络连接失败，请检查您的网络')
    } else {
      // 请求配置错误
      ElMessage.error('请求配置错误')
    }

    return Promise.reject(error)
  }
)

/**
 * 发送请求
 * @param config 请求配置
 * @returns Promise<T>
 */
export function request<T = any>(config: RequestConfig): Promise<T> {
  return instance.request<T>(config)
}

/**
 * GET 请求
 * @param url 请求地址
 * @param config 请求配置
 * @returns Promise<T>
 */
export function get<T = any>(url: string, config?: RequestConfig): Promise<T> {
  return request<T>({ ...config, method: 'GET', url })
}

/**
 * POST 请求
 * @param url 请求地址
 * @param data 请求数据
 * @param config 请求配置
 * @returns Promise<T>
 */
export function post<T = any>(url: string, data?: any, config?: RequestConfig): Promise<T> {
  return request<T>({ ...config, method: 'POST', url, data })
}

/**
 * PUT 请求
 * @param url 请求地址
 * @param data 请求数据
 * @param config 请求配置
 * @returns Promise<T>
 */
export function put<T = any>(url: string, data?: any, config?: RequestConfig): Promise<T> {
  return request<T>({ ...config, method: 'PUT', url, data })
}

/**
 * PATCH 请求
 * @param url 请求地址
 * @param data 请求数据
 * @param config 请求配置
 * @returns Promise<T>
 */
export function patch<T = any>(url: string, data?: any, config?: RequestConfig): Promise<T> {
  return request<T>({ ...config, method: 'PATCH', url, data })
}

/**
 * DELETE 请求
 * @param url 请求地址
 * @param config 请求配置
 * @returns Promise<T>
 */
export function del<T = any>(url: string, config?: RequestConfig): Promise<T> {
  return request<T>({ ...config, method: 'DELETE', url })
}

/**
 * 文件上传
 * @param url 请求地址
 * @param file 文件对象
 * @param config 请求配置
 * @returns Promise<T>
 */
export function upload<T = any>(
  url: string,
  file: File | Blob,
  config?: RequestConfig
): Promise<T> {
  const formData = new FormData()
  formData.append('file', file)

  return request<T>({
    ...config,
    method: 'POST',
    url,
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 下载文件
 * @param url 请求地址
 * @param filename 文件名
 * @param config 请求配置
 */
export function download(
  url: string,
  filename: string,
  config?: RequestConfig
): Promise<void> {
  return request<Blob>({
    ...config,
    method: 'GET',
    url,
    responseType: 'blob'
  }).then((data) => {
    const blob = new Blob([data])
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = filename
    link.click()
    URL.revokeObjectURL(link.href)
  })
}

export default request
