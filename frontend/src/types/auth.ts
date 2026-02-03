/**
 * 用户认证相关类型定义
 */
export interface User {
  id: string
  username: string
  email: string
  role: 'admin' | 'teacher' | 'student' | 'parent'
  full_name: string
  organization_id?: string
  profile?: Record<string, any>
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  confirm_password: string
  role: 'teacher' | 'student'
  organization_name?: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface AuthResponse {
  user: User
  access_token: string
  refresh_token: string
}

export interface RefreshTokenRequest {
  refresh_token: string
}

/**
 * 内容推荐相关类型
 */
export interface ContentItem {
  id: string
  title: string
  type: string
  level: string
  word_count: number
  subjects: string[]
  exam_tags: string[]
  created_at: string
}

export interface DailyRecommendation {
  reading: ContentItem[]
  exercises: ExerciseItem[]
  speaking: {
    scenario: string
    level: string
    topic: string
  }
}

export interface ExerciseItem {
  id: string
  type: string
  focus: string
  title: string
  question_count: number
}

/**
 * 对话相关类型
 */
export interface Conversation {
  id: string
  student_id: string
  scenario: string
  level: string
  status: string
  message_count: number
  started_at: string
  completed_at?: string
}

export interface ConversationDetail {
  id: string
  student_id: string
  scenario: string
  level: string
  status: string
  messages: Message[]
  started_at: string
  completed_at?: string
  scores?: ConversationScores
}

export interface Message {
  role: string
  content: string
  timestamp?: string
}

export interface ConversationScores {
  fluency_score?: number
  vocabulary_score?: number
  grammar_score?: number
  overall_score?: number
  feedback?: string
}

export interface CreateConversationRequest {
  scenario: string
  level: string
}

export interface SendMessageRequest {
  message: string
}

/**
 * 教案相关类型
 */
export interface LessonPlan {
  id: string
  teacher_id: string
  title: string
  topic: string
  level: string
  duration: number
  status: string
  created_at: string
  updated_at: string
}

/**
 * 知识图谱类型
 */
export interface KnowledgeGraph {
  id: string
  student_id: string
  cefr_level: string
  abilities: Record<string, any>
  weak_points: string[]
  recommendations: string[]
}

/**
 * API 响应包装
 */
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}
