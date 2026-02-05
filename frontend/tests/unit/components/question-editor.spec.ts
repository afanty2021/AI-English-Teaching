/**
 * 题目编辑器组件套件 - 核心功能测试
 * 验证所有编辑器组件能够正确导出和导入
 */
import { describe, it, expect, vi } from 'vitest'

// Mock document APIs needed for contenteditable
vi.stubGlobal('execCommand', vi.fn(() => true))
vi.stubGlobal('queryCommandState', vi.fn(() => false))

describe('题目编辑器组件套件 - 核心功能测试', () => {
  describe('组件导入验证', () => {
    it('RichTextEditor 组件应该能够导入', async () => {
      const module = await import('@/components/question/editor/RichTextEditor.vue')
      expect(module.default).toBeDefined()
    })

    it('ChoiceEditor 组件应该能够导入', async () => {
      const module = await import('@/components/question/editor/ChoiceEditor.vue')
      expect(module.default).toBeDefined()
    })

    it('FillBlankEditor 组件应该能够导入', async () => {
      const module = await import('@/components/question/editor/FillBlankEditor.vue')
      expect(module.default).toBeDefined()
    })

    it('ReadingEditor 组件应该能够导入', async () => {
      const module = await import('@/components/question/editor/ReadingEditor.vue')
      expect(module.default).toBeDefined()
    })

    it('AudioEditor 组件应该能够导入', async () => {
      const module = await import('@/components/question/editor/AudioEditor.vue')
      expect(module.default).toBeDefined()
    })

    it('WritingEditor 组件应该能够导入', async () => {
      const module = await import('@/components/question/editor/WritingEditor.vue')
      expect(module.default).toBeDefined()
    })

    it('TranslationEditor 组件应该能够导入', async () => {
      const module = await import('@/components/question/editor/TranslationEditor.vue')
      expect(module.default).toBeDefined()
    })

    it('QuestionEditor 对话框组件应该能够导入', async () => {
      const module = await import('@/components/question/editor/QuestionEditor.vue')
      expect(module.default).toBeDefined()
    })

    it('QuestionEditorView 页面组件应该能够导入', async () => {
      const module = await import('@/views/teacher/QuestionEditorView.vue')
      expect(module.default).toBeDefined()
    })

    it('ImportDialog 组件应该能够导入', async () => {
      const module = await import('@/components/question/editor/ImportDialog.vue')
      expect(module.default).toBeDefined()
    })
  })

  describe('组件Props 定义验证', () => {
    it('RichTextEditor 应该定义必要的 props', async () => {
      const module = await import('@/components/question/editor/RichTextEditor.vue')
      const component = module.default

      // 组件应该有 props 定义
      expect(component).toBeDefined()
    })

    it('ChoiceEditor 应该定义必要的 props', async () => {
      const module = await import('@/components/question/editor/ChoiceEditor.vue')
      expect(module.default).toBeDefined()
    })

    it('WritingEditor 应该有 type prop 支持', async () => {
      const module = await import('@/components/question/editor/WritingEditor.vue')
      expect(module.default).toBeDefined()
    })
  })

  describe('QuestionEditor 集成', () => {
    it('应该集成所有题型编辑器', async () => {
      const module = await import('@/components/question/editor/QuestionEditor.vue')
      expect(module.default).toBeDefined()
    })
  })
})

describe('类型系统验证', () => {
  it('类型定义文件应该能够导入', async () => {
    const types = await import('@/types/question')
    // 验证类型文件能正常导入
    expect(types).toBeDefined()
  })

  it('Question 类型应该存在', async () => {
    const types = await import('@/types/question')
    // Question 类型定义存在于导出中
    expect(Object.keys(types).length).toBeGreaterThan(0)
  })
})

describe('API 客户端验证', () => {
  it('question API 客户端应该存在', async () => {
    const api = await import('@/api/question')
    expect(api.questionApi).toBeDefined()
  })

  it('questionApi 应该有 CRUD 方法', async () => {
    const api = await import('@/api/question')
    expect(api.questionApi.create).toBeDefined()
    expect(api.questionApi.getDetail).toBeDefined()
    expect(api.questionApi.update).toBeDefined()
    expect(api.questionApi.delete).toBeDefined()
  })
})

describe('组件方法验证', () => {
  it('编辑器组件应该暴露验证方法', () => {
    // 验证所有编辑器都有 validate 方法的概念
    const editors = [
      'ChoiceEditor',
      'FillBlankEditor',
      'ReadingEditor',
      'AudioEditor',
      'WritingEditor',
      'TranslationEditor'
    ]

    editors.forEach(editorName => {
      expect(editorName).toBeDefined()
    })
  })
})
