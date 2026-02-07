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

// 浏览器全局变量类型声明
interface Window {
  WebSocket: typeof WebSocket
  setInterval: (handler: TimerHandler, timeout?: number) => number
  clearInterval: (id: number) => void
  setTimeout: (handler: TimerHandler, timeout?: number) => number
  clearTimeout: (id: number) => void
  location: Location
}

interface Console {
  log(...args: any[]): void
  error(...args: any[]): void
  warn(...args: any[]): void
  info(...args: any[]): void
  debug(...args: any[]): void
}

declare const window: Window
declare const console: Console
declare const setInterval: (handler: TimerHandler, timeout?: number) => number
declare const clearInterval: (id: number) => void
declare const setTimeout: (handler: TimerHandler, timeout?: number) => number
declare const clearTimeout: (id: number) => void
