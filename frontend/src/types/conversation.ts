/**
 * 对话相关类型定义
 */

/**
 * 对话场景枚举
 */
export enum ConversationScenario {
  CAFE_ORDER = 'cafe_order',
  RESTAURANT = 'restaurant',
  SHOPPING = 'shopping',
  ASKING_DIRECTION = 'asking_direction',
  JOB_INTERVIEW = 'job_interview',
  TALKING_ABOUT_HOBBIES = 'talking_about_hobbies',
  DESCRIBING_PICTURE = 'describing_picture',
  FREE_TALK = 'free_talk',
}

/**
 * 对话场景显示名称映射
 */
export const ScenarioNames: Record<ConversationScenario, string> = {
  [ConversationScenario.CAFE_ORDER]: '咖啡店点餐',
  [ConversationScenario.RESTAURANT]: '餐厅用餐',
  [ConversationScenario.SHOPPING]: '购物',
  [ConversationScenario.ASKING_DIRECTION]: '问路',
  [ConversationScenario.JOB_INTERVIEW]: '求职面试',
  [ConversationScenario.TALKING_ABOUT_HOBBIES]: '谈论爱好',
  [ConversationScenario.DESCRIBING_PICTURE]: '描述图片',
  [ConversationScenario.FREE_TALK]: '自由对话',
}

/**
 * 对话状态枚举
 */
export enum ConversationStatus {
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  ABANDONED = 'abandoned',
}

/**
 * 对话状态显示名称
 */
export const StatusNames: Record<ConversationStatus, string> = {
  [ConversationStatus.IN_PROGRESS]: '进行中',
  [ConversationStatus.COMPLETED]: '已完成',
  [ConversationStatus.ABANDONED]: '已放弃',
}

/**
 * 消息角色
 */
export enum MessageRole {
  USER = 'user',
  ASSISTANT = 'assistant',
  SYSTEM = 'system',
}

/**
 * 消息类型
 */
export enum MessageType {
  TEXT = 'text',
  AUDIO = 'audio',
  SYSTEM = 'system',
}

/**
 * 评分维度
 */
export interface ScoreDimension {
  name: string
  score: number
  max_score: number
  feedback: string
  suggestions: string[]
}

/**
 * 语法错误
 */
export interface GrammarError {
  type: 'grammar' | 'vocabulary' | 'pronunciation'
  original: string
  correction: string
  explanation: string
  position?: { start: number; end: number }
}

/**
 * 发音反馈
 */
export interface PronunciationFeedback {
  word: string
  phonetic: string
  score: number
  feedback: string
  audio_url?: string
}

/**
 * 对话消息
 */
export interface ConversationMessage {
  id: string
  role: MessageRole
  type: MessageType
  content: string
  audio_url?: string
  grammar_errors?: GrammarError[]
  pronunciation_feedback?: PronunciationFeedback[]
  scores?: ScoreDimension[]
  timestamp: string
  is_final?: boolean
}

/**
 * 对话评分
 */
export interface ConversationScores {
  overall: number
  overall_score?: number  // 后端返回的字段名
  fluency: ScoreDimension
  fluency_score?: number
  grammar: ScoreDimension
  grammar_score?: number
  vocabulary: ScoreDimension
  vocabulary_score?: number
  pronunciation: ScoreDimension
  pronunciation_score?: number
  communication: ScoreDimension
  communication_score?: number
  feedback?: string
  suggestions: string[]
}

/**
 * 对话会话
 */
export interface Conversation {
  id: string
  student_id: string
  scenario: ConversationScenario
  level: string
  status: ConversationStatus
  messages: ConversationMessage[]
  message_count?: number
  scores?: ConversationScores
  duration?: number
  duration_seconds?: number
  started_at: string
  completed_at?: string
  created_at: string
}

/**
 * 创建对话请求
 */
export interface CreateConversationRequest {
  scenario: ConversationScenario
  level?: string
}

/**
 * 发送消息请求
 */
export interface SendMessageRequest {
  content: string
  audio_url?: string
  is_final?: boolean
}
