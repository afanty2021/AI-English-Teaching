/**
 * 教案服务 API 客户端
 */
import { request } from '@/utils/request'
import type {
  LessonPlan,
  LessonPlanListResponse,
  LessonPlanResponse,
  GenerateLessonPlanRequest,
  UpdateLessonPlanRequest
} from '@/types/lesson'

const BASE_URL = '/api/v1/lesson-plans'

/**
 * 获取教案列表
 */
export async function getLessonPlans(params?: {
  page?: number
  page_size?: number
  level?: string
  status?: string
  target_exam?: string
  search?: string
}): Promise<LessonPlanListResponse> {
  return request({
    url: BASE_URL,
    method: 'GET',
    params
  })
}

/**
 * 获取教案详情
 */
export async function getLessonPlan(lessonId: string): Promise<LessonPlanResponse> {
  return request({
    url: `${BASE_URL}/${lessonId}`,
    method: 'GET'
  })
}

/**
 * 创建教案（AI 生成）
 */
export async function createLessonPlan(data: GenerateLessonPlanRequest): Promise<LessonPlanResponse> {
  return request({
    url: BASE_URL,
    method: 'POST',
    data,
    timeout: 300000 // 5分钟超时
  })
}

/**
 * AI 生成教案
 */
export async function generateLessonPlan(data: GenerateLessonPlanRequest): Promise<LessonPlanResponse> {
  return createLessonPlan(data)
}

/**
 * 更新教案
 */
export async function updateLessonPlan(
  lessonId: string,
  data: UpdateLessonPlanRequest
): Promise<LessonPlanResponse> {
  return request({
    url: `${BASE_URL}/${lessonId}`,
    method: 'PUT',
    data
  })
}

/**
 * 删除教案
 */
export async function deleteLessonPlan(lessonId: string): Promise<void> {
  return request({
    url: `${BASE_URL}/${lessonId}`,
    method: 'DELETE',
    responseType: 'text'
  })
}

/**
 * 重新生成教案
 */
export async function regenerateLessonPlan(lessonId: string): Promise<LessonPlanResponse> {
  return request({
    url: `${BASE_URL}/${lessonId}/regenerate`,
    method: 'POST',
    timeout: 300000
  })
}

/**
 * 更新教案内容（在线编辑）
 * 更新教案的教学笔记字段
 */
export async function updateLessonContent(
  lessonId: string,
  teachingNotes: string
): Promise<LessonPlanResponse> {
  return updateLessonPlan(lessonId, { teaching_notes: teachingNotes })
}

/**
 * 导出教案
 * 直接下载文件
 */
export async function exportLessonPlan(
  lessonId: string,
  format: 'docx' | 'pptx' | 'pdf'
): Promise<{ download_url: string; filename: string }> {
  // 后端直接返回文件流，使用不同的处理方式
  const response = await request<{
    download_url: string
    filename: string
  }>({
    url: `${BASE_URL}/${lessonId}/export/${format}`,
    method: 'GET',
    responseType: 'blob'
  })

  // 如果返回的是 blob，创建下载链接
  if (response instanceof Blob) {
    const url = URL.createObjectURL(response)
    const filename = `lesson-plan-${lessonId}.${format}`
    return { download_url: url, filename }
  }

  return response
}

/**
 * 获取导出文件 URL
 * 返回直接下载链接，用于文件下载
 */
export function getExportUrl(lessonId: string, format: 'docx' | 'pptx' | 'pdf'): string {
  return `${BASE_URL}/${lessonId}/export/${format}`
}

/**
 * 导出为 Markdown（前端实现）
 */
export async function exportToMarkdown(lesson: LessonPlan): Promise<string> {
  const markdown = generateMarkdown(lesson)
  return markdown
}

/**
 * 生成 Markdown 格式
 */
function generateMarkdown(lesson: LessonPlan): string {
  const getSkillTypeName = (type: string) => {
    const names: Record<string, string> = {
      'speaking': '口语',
      'listening': '听力',
      'reading': '阅读',
      'writing': '写作'
    }
    return names[type] || type
  }

  // 辅助函数：生成语法点Markdown
  const formatGrammarPoint = (gp: any): string => {
    let result = `### ${gp.name}
${gp.description}
`
    if (gp.rule) {
      result += `**规则**: ${gp.rule}`
    }
    return result
  }

  // 辅助函数：生成教学流程Markdown
  const formatStructurePhase = (phase: any, i: number): string => {
    return `### ${i + 1}. ${phase.title} (${phase.duration || 0}分钟)
${phase.description || ''}`
  }

  return `# ${lesson.title}

## 概览信息

- **主题**: ${lesson.topic || '未设置'}
- **级别**: ${lesson.level}
- **时长**: ${lesson.duration} 分钟

## 教学目标

${lesson.objectives?.language_knowledge?.map(obj => `- ${obj}`).join('\n') || ''}

${lesson.objectives?.language_skills ? Object.entries(lesson.objectives.language_skills).map(([type, skills]) =>
  `- **${getSkillTypeName(type)}**: ${skills.join('、')}`
).join('\n') : ''}

## 核心词汇

${lesson.vocabulary?.noun?.map(v => `- **${v.word}** (${v.meaning_cn})`).join('\n') || ''}

## 语法点

${lesson.grammar_points?.map(gp => formatGrammarPoint(gp)).join('\n') || ''}

## 教学流程

${lesson.structure?.map((phase, i) => formatStructurePhase(phase, i)).join('\n') || ''}

---

*由 AI 英语教学系统生成*
`
}
