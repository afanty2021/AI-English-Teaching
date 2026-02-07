/**
 * 教案导出 API 客户端
 */
import request from '@/utils/request'
import type {
  ExportFormat,
  ExportOptions,
  ExportTask,
  ExportTaskStatus,
  CreateExportTaskRequest,
  BatchExportRequest,
  ExportTaskResponse,
  ExportTaskListResponse,
  ExportTemplateListResponse
} from '@/types/lessonExport'

const BASE_URL = '/api/v1/lesson-export'

/**
 * 默认导出选项
 */
export const DEFAULT_EXPORT_OPTIONS: ExportOptions = {
  format: 'word',
  sections: ['overview', 'objectives', 'vocabulary', 'grammar', 'structure'],
  include_teacher_notes: false,
  include_answers: false,
  language: 'zh',
  include_page_numbers: true,
  include_toc: true
}

/**
 * 获取导出模板列表
 */
export async function getExportTemplates(): Promise<ExportTemplateListResponse> {
  return request({
    url: `${BASE_URL}/templates`,
    method: 'GET'
  })
}

/**
 * 创建导出任务
 */
export async function createExportTask(
  data: CreateExportTaskRequest
): Promise<ExportTaskResponse> {
  return request({
    url: `${BASE_URL}/tasks`,
    method: 'POST',
    data
  })
}

/**
 * 批量创建导出任务
 */
export async function createBatchExportTasks(
  data: BatchExportRequest
): Promise<ExportTaskListResponse> {
  return request({
    url: `${BASE_URL}/tasks/batch`,
    method: 'POST',
    data
  })
}

/**
 * 获取导出任务状态
 */
export async function getExportTask(taskId: string): Promise<ExportTaskResponse> {
  return request({
    url: `${BASE_URL}/tasks/${taskId}`,
    method: 'GET'
  })
}

/**
 * 获取导出任务列表
 */
export async function getExportTasks(params?: {
  lesson_id?: string
  status?: ExportTaskStatus
  limit?: number
  offset?: number
}): Promise<ExportTaskListResponse> {
  return request({
    url: `${BASE_URL}/tasks`,
    method: 'GET',
    params
  })
}

/**
 * 取消导出任务
 */
export async function cancelExportTask(taskId: string): Promise<void> {
  return request({
    url: `${BASE_URL}/tasks/${taskId}/cancel`,
    method: 'POST'
  })
}

/**
 * 删除导出任务
 */
export async function deleteExportTask(taskId: string): Promise<void> {
  return request({
    url: `${BASE_URL}/tasks/${taskId}`,
    method: 'DELETE'
  })
}

/**
 * 下载导出文件
 */
export async function downloadExportFile(task: ExportTask): Promise<void> {
  if (!task.download_url) {
    throw new Error('下载链接不可用')
  }

  try {
    const response = await fetch(task.download_url, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
      }
    })

    if (!response.ok) {
      throw new Error('下载失败')
    }

    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url

    // 根据格式设置文件扩展名
    const extMap: Record<ExportFormat, string> = {
      word: 'docx',
      pdf: 'pdf',
      pptx: 'pptx',
      markdown: 'md'
    }
    const ext = extMap[task.format] || task.format
    link.download = `${task.lesson_title}.${ext}`

    link.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    console.error('下载文件失败:', error)
    throw error
  }
}

/**
 * 轮询任务状态直到完成
 */
export async function pollTaskUntilComplete(
  taskId: string,
  onUpdate?: (task: ExportTask) => void,
  interval: number = 1000
): Promise<ExportTask> {
  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        const response = await getExportTask(taskId)
        const task = response.task

        if (onUpdate) {
          onUpdate(task)
        }

        if (task.status === 'completed') {
          resolve(task)
        } else if (task.status === 'failed') {
          reject(new Error(task.error_message || '导出失败'))
        } else {
          // 继续轮询
          setTimeout(poll, interval)
        }
      } catch (error) {
        reject(error)
      }
    }

    poll()
  })
}

// 导出类型别名
export type {
  ExportFormat,
  ExportOptions,
  ExportTask,
  ExportTemplate
} from '@/types/lessonExport'
