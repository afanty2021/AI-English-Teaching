/**
 * 题库与练习系统类型定义
 */

/**
 * 题目类型枚举
 */
export enum QuestionType {
  CHOICE = "choice",                      // 选择题
  FILL_BLANK = "fill_blank",              // 填空题
  READING_COMPREHENSION = "reading",      // 阅读理解
  WRITING = "writing",                    // 写作题
  SPEAKING = "speaking",                  // 口语题
  LISTENING = "listening",                // 听力题
  TRANSLATION = "translation",            // 翻译题
}

/**
 * CEFR难度等级枚举
 */
export enum CEFRLevel {
  A1 = "A1",
  A2 = "A2",
  B1 = "B1",
  B2 = "B2",
  C1 = "C1",
  C2 = "C2",
}

/**
 * 练习类型枚举
 */
export enum PracticeType {
  READING = "reading",        // 阅读
  LISTENING = "listening",    // 听力
  GRAMMAR = "grammar",        // 语法
  VOCABULARY = "vocabulary",  // 词汇
  WRITING = "writing",        // 写作
  SPEAKING = "speaking",      // 口语
}

/**
 * 会话状态枚举
 */
export enum SessionStatus {
  IN_PROGRESS = "in_progress",  // 进行中
  PAUSED = "paused",            // 已暂停
  COMPLETED = "completed",      // 已完成
  ABANDONED = "abandoned",      // 已放弃
}

/**
 * 题目选项类型
 */
export interface QuestionOption {
  key: string
  content: string
  is_correct?: boolean  // 用于编辑器中标识正确答案
}

/**
 * 正确答案类型
 */
export type CorrectAnswer =
  | { key: string }  // 选择题
  | { answers: string[]; type: 'multiple' }  // 填空题（多个等价答案）
  | { source: string; target: string }  // 翻译题

/**
 * 题目接口
 */
export interface Question {
  id: string
  question_type: QuestionType
  content_text: string
  question_bank_id?: string
  difficulty_level?: CEFRLevel
  topic?: string
  knowledge_points: string[]
  options: QuestionOption[]
  correct_answer: Record<string, any>
  explanation?: string
  order_index: number
  passage_content?: string      // 阅读理解文章内容
  audio_url?: string            // 听力音频URL
  sample_answer?: string        // 写作/口语参考答案
  extra_metadata?: Record<string, any>
  is_active: boolean
  has_audio: boolean
  created_by: string
  created_at: string
  updated_at: string
}

/**
 * 创建题目请求
 */
export interface CreateQuestionRequest {
  question_type: QuestionType
  content_text: string
  question_bank_id?: string
  difficulty_level?: CEFRLevel
  topic?: string
  knowledge_points?: string[]
  options?: QuestionOption[]
  correct_answer?: Record<string, any>
  explanation?: string
  order_index?: number
  passage_content?: string
  audio_url?: string
  sample_answer?: string
  extra_metadata?: Record<string, any>
}

/**
 * 更新题目请求
 */
export interface UpdateQuestionRequest {
  content_text?: string
  difficulty_level?: CEFRLevel
  topic?: string
  knowledge_points?: string[]
  options?: QuestionOption[]
  correct_answer?: Record<string, any>
  explanation?: string
  is_active?: boolean
  passage_content?: string
  audio_url?: string
  sample_answer?: string
  extra_metadata?: Record<string, any>
}

/**
 * 题库接口
 */
export interface QuestionBank {
  id: string
  name: string
  description?: string
  practice_type: PracticeType
  difficulty_level?: CEFRLevel
  tags: string[]
  is_public: boolean
  question_count: number
  created_by: string
  created_at: string
  updated_at: string
}

/**
 * 创建题库请求
 */
export interface CreateQuestionBankRequest {
  name: string
  description?: string
  practice_type: PracticeType
  difficulty_level?: CEFRLevel
  tags?: string[]
  is_public?: boolean
}

/**
 * 更新题库请求
 */
export interface UpdateQuestionBankRequest {
  name?: string
  description?: string
  difficulty_level?: CEFRLevel
  tags?: string[]
  is_public?: boolean
}

/**
 * 题目列表响应
 */
export interface QuestionsListResponse {
  total: number
  items: Question[]
}

/**
 * 题库列表响应
 */
export interface QuestionBanksListResponse {
  total: number
  items: QuestionBank[]
}

/**
 * 练习会话接口
 */
export interface PracticeSession {
  id: string
  title?: string
  status: SessionStatus
  total_questions: number
  current_question_index: number
  question_count: number
  correct_count: number
  progress_percentage: number
  current_correct_rate: number
  question_bank_id?: string
  created_at: string
  updated_at: string
  completed_at?: string
}

/**
 * 当前题目响应
 */
export interface CurrentQuestionResponse {
  session_id: string
  question_index: number
  total_questions: number
  is_answered: boolean
  previous_answer?: any
  question: Question
}

/**
 * 提交答案请求
 */
export interface SubmitAnswerRequest {
  answer: any
  question_index?: number
}

/**
 * 提交答案响应
 */
export interface SubmitAnswerResponse {
  is_correct: boolean
  correct_answer: any
  explanation?: string
  current_question_index: number
  correct_count: number
  question_count: number
  is_completed: boolean
}

/**
 * 练习结果统计
 */
export interface PracticeStatistics {
  by_type: Record<string, { total: number; correct: number }>
  by_difficulty: Record<string, { total: number; correct: number }>
  by_topic: Record<string, { total: number; correct: number }>
}

/**
 * 错题记录
 */
export interface WrongQuestion {
  question_id: string
  question_type: QuestionType
  content_text: string
  user_answer: any
  correct_answer: any
  explanation?: string
  knowledge_points: string[]
}

/**
 * 完成会话响应
 */
export interface CompleteSessionResponse {
  session_id: string
  practice_id?: string
  total_questions: number
  answered_questions: number
  correct_count: number
  correct_rate: number
  statistics: PracticeStatistics
  wrong_questions: WrongQuestion[]
  completed_at: string
}

/**
 * 开始练习会话请求
 */
export interface StartPracticeSessionRequest {
  question_source: "bank" | "questions" | "random"
  question_bank_id?: string
  question_ids?: string[]
  practice_type?: PracticeType
  difficulty_level?: CEFRLevel
  count?: number
  title?: string
}

/**
 * 练习会话列表响应
 */
export interface PracticeSessionsListResponse {
  total: number
  items: PracticeSession[]
}

/**
 * 导航请求
 */
export interface NavigateRequest {
  direction: "next" | "previous"
}
