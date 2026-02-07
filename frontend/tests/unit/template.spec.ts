/**
 * 导出模板管理API测试
 * 测试template API客户端的功能
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import request from '@/utils/request'

// Mock utils/request
vi.mock('@/utils/request', () => ({
  default: vi.fn()
}))

// 导入API函数
import {
  getTemplates,
  getTemplate,
  createTemplate,
  updateTemplate,
  deleteTemplate,
  setDefaultTemplate,
  previewTemplate,
  duplicateTemplate,
  type ExportTemplate,
  type TemplateFormat,
  type TemplateVariable
} from '@/api/template'

describe('templateApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getTemplates', () => {
    it('应该正确调用获取模板列表API（无参数）', async () => {
      const mockResponse = {
        templates: [
          {
            id: 'template-1',
            name: '标准教案模板',
            description: '标准教案格式',
            format: 'word' as TemplateFormat,
            type: 'system',
            file_url: 'https://example.com/template.docx',
            variables: [],
            usage_count: 10,
            is_default: true,
            created_at: '2025-01-15T10:00:00Z',
            updated_at: '2025-01-15T10:00:00Z'
          }
        ],
        total: 1
      }

      vi.mocked(request).mockResolvedValue(mockResponse)

      const result = await getTemplates()

      expect(request).toHaveBeenCalledWith({
        url: '/api/v1/export-templates',
        method: 'GET',
        params: undefined
      })
      expect(result).toEqual(mockResponse)
    })

    it('应该正确处理筛选参数', async () => {
      const mockResponse = { templates: [], total: 0 }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const params = {
        format: 'word' as TemplateFormat,
        type: 'custom' as const,
        search: '教案',
        skip: 0,
        limit: 20
      }

      await getTemplates(params)

      expect(request).toHaveBeenCalledWith({
        url: '/api/v1/export-templates',
        method: 'GET',
        params
      })
    })
  })

  describe('getTemplate', () => {
    it('应该正确调用获取模板详情API', async () => {
      const mockTemplate: ExportTemplate = {
        id: 'template-1',
        name: '标准教案模板',
        description: '标准教案格式',
        format: 'word',
        type: 'system',
        file_url: 'https://example.com/template.docx',
        variables: [
          {
            name: 'lesson_title',
            description: '课程标题',
            default_value: '',
            required: true
          }
        ],
        usage_count: 10,
        is_default: true,
        created_at: '2025-01-15T10:00:00Z',
        updated_at: '2025-01-15T10:00:00Z'
      }

      vi.mocked(request).mockResolvedValue({ template: mockTemplate })

      const result = await getTemplate('template-1')

      expect(request).toHaveBeenCalledWith({
        url: '/api/v1/export-templates/template-1',
        method: 'GET'
      })
      expect(result.template).toEqual(mockTemplate)
    })
  })

  describe('createTemplate', () => {
    it('应该正确调用创建模板API', async () => {
      const mockTemplate: ExportTemplate = {
        id: 'template-new',
        name: '新模板',
        description: '新模板描述',
        format: 'word',
        type: 'custom',
        file_url: 'https://example.com/new.docx',
        variables: [],
        usage_count: 0,
        is_default: false,
        creator_id: 'user-1',
        created_at: '2025-01-15T10:00:00Z',
        updated_at: '2025-01-15T10:00:00Z'
      }

      vi.mocked(request).mockResolvedValue({ template: mockTemplate })

      const createData = {
        name: '新模板',
        description: '新模板描述',
        format: 'word' as TemplateFormat,
        variables: [],
        file: new File([''], 'template.docx')
      }

      const result = await createTemplate(createData)

      expect(request).toHaveBeenCalledWith({
        url: '/api/v1/export-templates',
        method: 'POST',
        data: expect.any(FormData),
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      expect(result.template.id).toBe('template-new')
    })
  })

  describe('updateTemplate', () => {
    it('应该正确调用更新模板API', async () => {
      const mockTemplate: ExportTemplate = {
        id: 'template-1',
        name: '更新后的模板',
        description: '更新描述',
        format: 'word',
        type: 'custom',
        file_url: 'https://example.com/template.docx',
        variables: [],
        usage_count: 5,
        is_default: false,
        creator_id: 'user-1',
        created_at: '2025-01-15T10:00:00Z',
        updated_at: '2025-01-15T11:00:00Z'
      }

      vi.mocked(request).mockResolvedValue({ template: mockTemplate })

      const updateData = {
        name: '更新后的模板',
        description: '更新描述',
        variables: []
      }

      const result = await updateTemplate('template-1', updateData)

      expect(request).toHaveBeenCalledWith({
        url: '/api/v1/export-templates/template-1',
        method: 'PUT',
        data: expect.any(FormData),
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      expect(result.template.name).toBe('更新后的模板')
    })
  })

  describe('deleteTemplate', () => {
    it('应该正确调用删除模板API', async () => {
      vi.mocked(request).mockResolvedValue(undefined)

      await deleteTemplate('template-1')

      expect(request).toHaveBeenCalledWith({
        url: '/api/v1/export-templates/template-1',
        method: 'DELETE'
      })
    })
  })

  describe('setDefaultTemplate', () => {
    it('应该正确调用设置默认模板API', async () => {
      vi.mocked(request).mockResolvedValue(undefined)

      await setDefaultTemplate('template-1')

      expect(request).toHaveBeenCalledWith({
        url: '/api/v1/export-templates/template-1/set-default',
        method: 'POST'
      })
    })
  })

  describe('previewTemplate', () => {
    it('应该正确调用预览模板API', async () => {
      const mockResponse = {
        preview_url: 'https://example.com/preview/abc123',
        expires_at: '2025-01-15T11:00:00Z'
      }

      vi.mocked(request).mockResolvedValue(mockResponse)

      const result = await previewTemplate('template-1')

      expect(request).toHaveBeenCalledWith({
        url: '/api/v1/export-templates/template-1/preview',
        method: 'POST'
      })
      expect(result.preview_url).toBe('https://example.com/preview/abc123')
    })
  })

  describe('duplicateTemplate', () => {
    it('应该正确调用复制模板API', async () => {
      const mockTemplate: ExportTemplate = {
        id: 'template-copy',
        name: '标准教案模板 (副本)',
        description: '标准教案格式',
        format: 'word',
        type: 'custom',
        file_url: 'https://example.com/template.docx',
        variables: [],
        usage_count: 0,
        is_default: false,
        creator_id: 'user-1',
        created_at: '2025-01-15T10:00:00Z',
        updated_at: '2025-01-15T10:00:00Z'
      }

      vi.mocked(request).mockResolvedValue({ template: mockTemplate })

      const result = await duplicateTemplate('template-1')

      expect(request).toHaveBeenCalledWith({
        url: '/api/v1/export-templates/template-1/duplicate',
        method: 'POST'
      })
      expect(result.template.id).toBe('template-copy')
      expect(result.template.type).toBe('custom')
    })
  })
})
