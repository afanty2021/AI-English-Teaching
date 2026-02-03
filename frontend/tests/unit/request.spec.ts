/**
 * HTTP 请求工具测试
 * 包含正常场景和边界条件测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'
import {
  request,
  get,
  post,
  put,
  patch,
  del,
  upload,
  download,
  type RequestConfig
} from '@/utils/request'

// Mock axios
vi.mock('axios')

describe('HTTP 请求工具', () => {
  const mockAxios = axios as jest.Mocked<typeof axios>

  beforeEach(() => {
    // 清除所有 mock
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('request 基础功能', () => {
    it('应该发送 GET 请求', async () => {
      const mockResponse = { data: { id: 1, name: 'Test' } }
      mockAxios.create.mockReturnValue({
        request: vi.fn().mockResolvedValue(mockResponse)
      } as any)

      const result = await request({
        url: '/api/test',
        method: 'GET'
      })

      expect(result).toEqual(mockResponse.data)
    })

    it('应该发送 POST 请求', async () => {
      const mockResponse = { data: { success: true } }
      const mockInstance = {
        request: vi.fn().mockResolvedValue(mockResponse)
      }
      mockAxios.create.mockReturnValue(mockInstance as any)

      await request({
        url: '/api/test',
        method: 'POST',
        data: { name: 'Test' }
      })

      expect(mockInstance.request).toHaveBeenCalledWith({
        url: '/api/test',
        method: 'POST',
        data: { name: 'Test' }
      })
    })

    it('应该处理 DELETE 请求', async () => {
      const mockResponse = { data: null }
      const mockInstance = {
        request: vi.fn().mockResolvedValue(mockResponse)
      }
      mockAxios.create.mockReturnValue(mockInstance as any)

      await request({
        url: '/api/test/1',
        method: 'DELETE'
      })

      expect(mockInstance.request).toHaveBeenCalledWith({
        url: '/api/test/1',
        method: 'DELETE'
      })
    })
  })

  describe('快捷方法', () => {
    let mockInstance: any

    beforeEach(() => {
      mockInstance = {
        request: vi.fn().mockResolvedValue({ data: 'result' })
      }
      mockAxios.create.mockReturnValue(mockInstance)
    })

    it('get 方法应该发送 GET 请求', async () => {
      await get('/api/test')
      expect(mockInstance.request).toHaveBeenCalledWith({
        url: '/api/test',
        method: 'GET'
      })
    })

    it('post 方法应该发送 POST 请求', async () => {
      await post('/api/test', { data: 'test' })
      expect(mockInstance.request).toHaveBeenCalledWith({
        url: '/api/test',
        method: 'POST',
        data: { data: 'test' }
      })
    })

    it('put 方法应该发送 PUT 请求', async () => {
      await put('/api/test/1', { name: 'Updated' })
      expect(mockInstance.request).toHaveBeenCalledWith({
        url: '/api/test/1',
        method: 'PUT',
        data: { name: 'Updated' }
      })
    })

    it('patch 方法应该发送 PATCH 请求', async () => {
      await patch('/api/test/1', { status: 'active' })
      expect(mockInstance.request).toHaveBeenCalledWith({
        url: '/api/test/1',
        method: 'PATCH',
        data: { status: 'active' }
      })
    })

    it('del 方法应该发送 DELETE 请求', async () => {
      await del('/api/test/1')
      expect(mockInstance.request).toHaveBeenCalledWith({
        url: '/api/test/1',
        method: 'DELETE'
      })
    })
  })

  describe('认证处理', () => {
    it('应该自动添加 Bearer Token', async () => {
      const mockInstance = {
        request: vi.fn().mockResolvedValue({ data: {} }),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() }
        }
      }
      mockAxios.create.mockReturnValue(mockInstance)

      // 模拟 authStore
      vi.doMock('@/stores/auth', () => ({
        useAuthStore: () => ({
          accessToken: 'test-token'
        })
      }))

      await request({ url: '/api/test', method: 'GET' })

      // 验证请求拦截器被注册
      expect(mockInstance.interceptors.request.use).toHaveBeenCalled()
    })

    it('应该支持跳过认证', async () => {
      const mockInstance = {
        request: vi.fn().mockResolvedValue({ data: {} }),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() }
        }
      }
      mockAxios.create.mockReturnValue(mockInstance)

      await request({
        url: '/api/test',
        method: 'GET',
        skipAuth: true
      })
    })
  })

  describe('错误处理', () => {
    it('应该处理 401 错误', async () => {
      const mockInstance = {
        request: vi.fn().mockRejectedValue({
          response: { status: 401 }
        }),
        interceptors: {
          request: { use: vi.fn((fn: any) => fn) },
          response: { use: vi.fn((fn: any) => fn) }
        }
      }
      mockAxios.create.mockReturnValue(mockInstance as any)

      // Mock ElMessage
      const ElMessage = { error: vi.fn() }
      vi.doMock('element-plus', () => ({ ElMessage }))

      await expect(
        request({ url: '/api/test', method: 'GET' })
      ).rejects.toThrow()
    })

    it('应该处理 403 错误', async () => {
      const mockInstance = {
        request: vi.fn().mockRejectedValue({
          response: { status: 403, data: { message: 'Forbidden' } }
        }),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() }
        }
      }
      mockAxios.create.mockReturnValue(mockInstance as any)

      await expect(
        request({ url: '/api/test', method: 'GET' })
      ).rejects.toThrow()
    })

    it('应该处理 404 错误', async () => {
      const mockInstance = {
        request: vi.fn().mockRejectedValue({
          response: { status: 404 }
        }),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() }
        }
      }
      mockAxios.create.mockReturnValue(mockInstance as any)

      await expect(
        request({ url: '/api/test', method: 'GET' })
      ).rejects.toThrow()
    })

    it('应该处理 500 错误', async () => {
      const mockInstance = {
        request: vi.fn().mockRejectedValue({
          response: { status: 500 }
        }),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() }
        }
      }
      mockAxios.create.mockReturnValue(mockInstance as any)

      await expect(
        request({ url: '/api/test', method: 'GET' })
      ).rejects.toThrow()
    })

    it('应该处理网络错误', async () => {
      const mockInstance = {
        request: vi.fn().mockRejectedValue({ request: {} }),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() }
        }
      }
      mockAxios.create.mockReturnValue(mockInstance as any)

      await expect(
        request({ url: '/api/test', method: 'GET' })
      ).rejects.toThrow()
    })

    it('应该支持跳过错误处理', async () => {
      const mockInstance = {
        request: vi.fn().mockRejectedValue(new Error('Test error')),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn((success: any, error: any) => error) }
        }
      }
      mockAxios.create.mockReturnValue(mockInstance as any)

      await expect(
        request({
          url: '/api/test',
          method: 'GET',
          skipErrorHandler: true
        })
      ).rejects.toThrow()
    })
  })

  describe('文件操作', () => {
    it('upload 应该发送 FormData', async () => {
      const mockInstance = {
        request: vi.fn().mockResolvedValue({ data: {} }),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() }
        }
      }
      mockAxios.create.mockReturnValue(mockInstance as any)

      const file = new File(['content'], 'test.txt', { type: 'text/plain' })
      await upload('/api/upload', file)

      expect(mockInstance.request).toHaveBeenCalledWith({
        url: '/api/upload',
        method: 'POST',
        data: expect.any(FormData),
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
    })

    it('download 应该创建下载链接', async () => {
      const mockBlob = new Blob(['content'], { type: 'text/plain' })
      const mockInstance = {
        request: vi.fn().mockResolvedValue({ data: mockBlob }),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() }
        }
      }
      mockAxios.create.mockReturnValue(mockInstance as any)

      // Mock document methods
      const mockLink = {
        href: '',
        download: '',
        click: vi.fn(),
        style: {}
      }
      global.document.createElement = vi.fn().mockReturnValue(mockLink)
      global.URL.createObjectURL = vi.fn().mockReturnValue('blob:url')
      global.URL.revokeObjectURL = vi.fn()

      await download('/api/download/file.txt', 'file.txt')

      expect(mockLink.click).toHaveBeenCalled()
    })
  })

  describe('边界条件', () => {
    let mockInstance: any

    beforeEach(() => {
      mockInstance = {
        request: vi.fn(),
        interceptors: {
          request: { use: vi.fn((fn: any) => fn) },
          response: { use: vi.fn((fn: any) => fn) }
        }
      }
      mockAxios.create.mockReturnValue(mockInstance)
    })

    it('应该处理空 URL', async () => {
      mockInstance.request.mockResolvedValue({ data: {} })

      await expect(
        request({ url: '', method: 'GET' })
      ).resolves.toBeDefined()
    })

    it('应该处理特殊字符在 URL 中', async () => {
      mockInstance.request.mockResolvedValue({ data: {} })

      await request({
        url: '/api/test?param=value with spaces&other=测试',
        method: 'GET'
      })

      expect(mockInstance.request).toHaveBeenCalled()
    })

    it('应该处理空请求体', async () => {
      mockInstance.request.mockResolvedValue({ data: {} })

      await post('/api/test', null)

      expect(mockInstance.request).toHaveBeenCalledWith({
        url: '/api/test',
        method: 'POST',
        data: null
      })
    })

    it('应该处理 undefined 数据', async () => {
      mockInstance.request.mockResolvedValue({ data: {} })

      await post('/api/test', undefined)

      expect(mockInstance.request).toHaveBeenCalledWith({
        url: '/api/test',
        method: 'POST',
        data: undefined
      })
    })

    it('应该处理超大响应数据', async () => {
      const largeData = { items: Array(10000).fill({ id: 1, name: 'Test' }) }
      mockInstance.request.mockResolvedValue({ data: largeData })

      const result = await get('/api/large-data')

      expect(result.items).toHaveLength(10000)
    })

    it('应该处理超时设置', async () => {
      mockInstance.request.mockResolvedValue({ data: {} })

      await request({
        url: '/api/test',
        method: 'GET',
        timeout: 5000
      })

      expect(mockInstance.request).toHaveBeenCalledWith(
        expect.objectContaining({ timeout: 5000 })
      )
    })

    it('应该处理自定义 headers', async () => {
      mockInstance.request.mockResolvedValue({ data: {} })

      await request({
        url: '/api/test',
        method: 'GET',
        headers: {
          'X-Custom-Header': 'custom-value'
        }
      } as any)

      expect(mockInstance.request).toHaveBeenCalledWith(
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-Custom-Header': 'custom-value'
          })
        })
      )
    })

    it('应该处理并发请求', async () => {
      mockInstance.request.mockResolvedValue({ data: 'result' })

      const promises = [
        get('/api/test1'),
        get('/api/test2'),
        get('/api/test3')
      ]

      const results = await Promise.all(promises)

      expect(results).toHaveLength(3)
      expect(mockInstance.request).toHaveBeenCalledTimes(3)
    })
  })

  describe('类型安全', () => {
    it('应该支持泛型返回类型', async () => {
      interface User {
        id: number
        name: string
      }

      const mockInstance = {
        request: vi.fn().mockResolvedValue({ data: { id: 1, name: 'Test' } }),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() }
        }
      }
      mockAxios.create.mockReturnValue(mockInstance)

      const result = await request<User>({ url: '/api/user', method: 'GET' })

      // TypeScript 应该推断 result 为 User 类型
      expect(result.id).toBe(1)
      expect(result.name).toBe('Test')
    })
  })
})
