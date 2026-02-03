/**
 * 教案相关类型定义
 */

// ==================== 基础类型 ====================

/**
 * 词汇项
 */
export interface VocabularyItem {
  word: string
  phonetic?: string
  part_of_speech: string
  meaning_cn: string
  meaning_en?: string
  example_sentence: string
  example_translation: string
  collocations: string[]
  synonyms: string[]
  antonyms: string[]
  difficulty: string
}

/**
 * 语法点
 */
export interface GrammarPoint {
  name: string
  description: string
  rule: string
  examples: string[]
  common_mistakes: string[]
  practice_tips: string[]
}

/**
 * 教学步骤
 */
export interface TeachingStep {
  phase: string
  title: string
  duration: number
  description: string
  activities: string[]
  teacher_actions: string[]
  student_actions: string[]
  materials: string[]
}

/**
 * 分层材料
 */
export interface LeveledMaterial {
  level: string
  title: string
  content: string
  word_count: number
  vocabulary_list: VocabularyItem[]
  comprehension_questions: string[]
  difficulty_notes: string
}

/**
 * 练习题
 */
export interface ExerciseItem {
  id: string
  type: string
  question: string
  options?: string[]
  correct_answer: string
  explanation: string
  points: number
  difficulty: string
}

/**
 * PPT幻灯片
 */
export interface PPTSlide {
  slide_number: number
  title: string
  content: string[]
  notes?: string
  layout: string
}

/**
 * 教学目标
 */
export interface LessonPlanObjectives {
  language_knowledge: string[]
  language_skills: Record<string, string[]>
  learning_strategies: string[]
  cultural_awareness: string[]
  emotional_attitudes: string[]
}

/**
 * 教学结构
 */
export interface LessonPlanStructure {
  warm_up?: TeachingStep
  presentation?: TeachingStep
  practice: TeachingStep[]
  production?: TeachingStep
  summary?: TeachingStep
  homework?: TeachingStep
}

/**
 * 教学材料
 */
export interface TeachingMaterial {
  type: 'image' | 'video' | 'document' | 'audio'
  title: string
  description: string
  url: string
}

// ==================== 请求类型 ====================

/**
 * 生成教案请求
 */
export interface GenerateLessonPlanRequest {
  title: string
  topic: string
  level: string
  duration?: number
  target_exam?: string
  student_count?: number
  focus_areas?: string[]
  learning_objectives?: string[]
  include_leveled_materials?: boolean
  leveled_levels?: string[]
  include_exercises?: boolean
  exercise_count?: number
  exercise_types?: string[]
  include_ppt?: boolean
  template_id?: string
  additional_requirements?: string
}

/**
 * 更新教案请求
 */
export interface UpdateLessonPlanRequest {
  title?: string
  topic?: string
  level?: string
  duration?: number
  target_exam?: string
  status?: string
  teaching_notes?: string
  resources?: Record<string, unknown>
}

// ==================== 响应类型 ====================

/**
 * 教案详情
 */
export interface LessonPlanDetail {
  id: string
  title: string
  topic: string
  level: string
  duration: number
  target_exam?: string
  status: string
  objectives: LessonPlanObjectives
  vocabulary: Record<string, VocabularyItem[]>
  grammar_points: GrammarPoint[]
  structure: LessonPlanStructure
  leveled_materials: LeveledMaterial[]
  exercises: Record<string, ExerciseItem[]>
  ppt_outline: PPTSlide[]
  resources: Record<string, unknown>
  teaching_notes?: string
  generation_time_ms?: number
  last_generated_at?: string
  created_at: string
  updated_at: string
}

/**
 * 教案摘要（列表视图）
 */
export interface LessonPlanSummary {
  id: string
  title: string
  topic: string
  level: string
  duration: number
  target_exam?: string
  status: string
  created_at: string
  updated_at: string
}

/**
 * 教案响应
 */
export interface LessonPlanResponse {
  lesson_plan: LessonPlanDetail
  teacher_id: string
}

/**
 * 教案列表响应
 */
export interface LessonPlanListResponse {
  lesson_plans: LessonPlanSummary[]
  total: number
  page: number
  page_size: number
}

// ==================== 兼容类型（用于现有组件） ====================

/**
 * 简化的教案类型（用于 LessonsView 组件）
 * 兼容原有组件中使用的数据结构
 */
export interface LessonPlan {
  id: string
  title: string
  topic: string
  level: string
  duration: number
  student_count?: number
  focus_areas?: string[]
  status: 'draft' | 'completed' | 'archived'
  objectives?: {
    language_knowledge?: string[]
    language_skills?: Record<string, string[]>
  }
  vocabulary?: {
    noun?: Array<{ word: string; meaning_cn: string; pronunciation?: string; example?: string }>
    verb?: Array<{ word: string; meaning_cn: string; pronunciation?: string; example?: string }>
    adjective?: Array<{ word: string; meaning_cn: string; pronunciation?: string; example?: string }>
  }
  grammar_points?: Array<{
    name: string
    description: string
    rule?: string
    examples?: string[]
  }>
  structure?: Array<{
    title: string
    duration?: number
    description?: string
    activities?: string[]
    tips?: string[]
  }>
  materials?: Array<{
    type: 'image' | 'video' | 'document' | 'audio'
    title: string
    description: string
    url: string
  }>
  created_at: string
  updated_at: string
}

/**
 * 教案列表查询参数
 */
export interface LessonPlanListParams {
  skip?: number
  limit?: number
  level?: string
  status?: string
  search?: string
  page?: number
  page_size?: number
}

/**
 * 导出教案响应
 */
export interface LessonPlanExportResponse {
  download_url: string
  filename: string
}
