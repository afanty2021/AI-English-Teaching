/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

// Element Plus locale
declare module 'element-plus/dist/locale/zh-cn.mjs' {
  const locale: any
  export default locale
}

// Axios 类型扩展
declare module 'axios' {
  export interface AxiosInstance {
    (config: any): any
    get(url: string, config?: any): any
    post(url: string, data?: any, config?: any): any
    put(url: string, data?: any, config?: any): any
    delete(url: string, config?: any): any
    request<T = any>(config: any): Promise<T>
    interceptors: {
      request: any
      response: any
    }
  }
  export interface AxiosHeaders {
    [key: string]: any
    Authorization?: string
    'Content-Type'?: string
  }
  export interface AxiosError extends Error {
    config?: any
    request?: any
    response?: any
  }
  export interface InternalAxiosRequestConfig {
    url?: string
    method?: string
    data?: any
    params?: any
    responseType?: string
    timeout?: number
    headers?: AxiosHeaders
    skipAuth?: boolean
    skipErrorHandler?: boolean
  }
  export const axios: {
    create(config?: any): AxiosInstance
    get(url: string, config?: any): any
    post(url: string, data?: any, config?: any): any
  }
  export default axios
}
