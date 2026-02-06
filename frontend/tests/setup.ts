import { vi } from 'vitest'
import { config } from '@vue/test-utils'

// 全局 mock 配置
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  takeRecords() {
    return []
  }
  unobserve() {}
} as any

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
} as any

// Mock contenteditable
document.execCommand = vi.fn(() => true)
document.queryCommandState = vi.fn(() => false)

// 配置 Vue Test Utils 全局 stubs
config.global.stubs = {
  'el-icon': true,
  'el-button': true,
  'el-input': true,
  'el-input-number': true,
  'el-select': true,
  'el-option': true,
  'el-checkbox': true,
  'el-tag': true,
  'el-form': true,
  'el-form-item': true,
  'el-divider': true,
  'el-row': true,
  'el-col': true,
  'el-dialog': true,
  'el-drawer': true,
  'el-upload': true,
  'el-alert': true,
  'el-card': true,
  'el-empty': true,
  'el-progress': true,
  'el-message': {
    error: vi.fn(),
    success: vi.fn(),
    warning: vi.fn(),
    info: vi.fn()
  }
}

// Mock Element Plus icons
vi.mock('@element-plus/icons-vue', () => ({
  TrendCharts: {
    template: '<svg></svg>'
  },
  Right: {
    template: '<svg></svg>'
  }
}))

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString()
    },
    removeItem: (key: string) => {
      delete store[key]
    },
    clear: () => {
      store = {}
    }
  }
})()

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
})
