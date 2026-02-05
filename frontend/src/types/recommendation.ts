/**
 * 推荐系统类型定义
 */

// 学生画像
export interface StudentProfile {
  student_id: string
  target_exam?: string
  target_score?: number
  current_cefr_level?: string
  abilities: {
    vocabulary: number
    grammar: number
    reading: number
    listening: number
    speaking: number
    writing: number
  }
  mastered_points: string[]
  weak_points: string[]
  learning_points: string[]
  preferred_topics: string[]
  preferred_content_types: string[]
  completed_content_count: number
  total_study_time: number
}

// 推荐过滤条件
export interface RecommendationFilter {
  contentTypes?: string[]
  difficultyLevels?: string[]
  topics?: string[]
  examTypes?: string[]
  maxRecommendations?: number
}

// 阅读推荐
export interface ReadingRecommendation {
  content_id: string
  title: string
  description?: string
  difficulty_level: string
  topic?: string
  word_count?: number
  estimated_time: number
  recommendation_reason: string
  content_preview?: string
}

// 听力推荐
export interface ListeningRecommendation {
  content_id: string
  title: string
  description?: string
  difficulty_level: string
  duration: number
  audio_url?: string
  transcript?: string
}

// 词汇推荐
export interface VocabularyRecommendation {
  vocabulary_id: string
  word: string
  phonetic?: string
  definition: string
  example?: string
  difficulty_level: string
  topic?: string
}

// 语法推荐
export interface GrammarRecommendation {
  grammar_point: string
  rule: string
  examples: string[]
  difficulty_level: string
  topic?: string
  practice_questions?: number
}

// 口语推荐
export interface SpeakingRecommendation {
  scenario: string
  scenario_name: string
  level: string
  description: string
  conversation_id?: string
}

// 每日推荐
export interface DailyRecommendations {
  reading: ReadingRecommendation[]
  listening: ListeningRecommendation[]
  vocabulary: VocabularyRecommendation[]
  grammar: GrammarRecommendation[]
  speaking: SpeakingRecommendation | null
}

// 内容完成请求
export interface ContentCompletionRequest {
  content_id: string
  content_type: string
  completed_at: string
  score?: number
  time_spent?: number
}

// 反馈请求
export interface FeedbackRequest {
  content_id: string
  satisfaction: number
  reason?: string
  feedback_type: 'recommendation' | 'content' | 'difficulty'
}

// 推荐历史
export interface RecommendationHistoryItem {
  id: string
  content_id: string
  content_type: string
  title: string
  recommended_at: string
  completed_at?: string
  satisfaction?: number
  feedback?: string
}

export interface RecommendationHistory {
  items: RecommendationHistoryItem[]
  total: number
  page: number
  limit: number
  has_more: boolean
}

// 推荐统计
export interface RecommendationStats {
  total_recommendations: number
  completion_rate: number
  average_satisfaction: number
  most_popular_topics: string[]
  improvement_areas: string[]
}

// 内容搜索结果
export interface ContentSearchResult {
  id: string
  title: string
  content_type: string
  difficulty_level: string
  topic?: string
  description?: string
  match_score: number
}

// 学习路径节点
export interface LearningPathNode {
  id: string
  type: 'vocabulary' | 'grammar' | 'reading' | 'listening' | 'speaking' | 'writing'
  name: string
  level: string
  status: 'mastered' | 'learning' | 'needs_practice'
  prerequisites: string[]
  estimated_time: number
}

// 学习路径边
export interface LearningPathEdge {
  source: string
  target: string
  relationship: 'prerequisite' | 'similar' | 'progress'
  strength: number
}

// 学习路径
export interface LearningPath {
  student_id: string
  nodes: LearningPathNode[]
  edges: LearningPathEdge[]
  current_focus: string[]
  recommended_next: string[]
  completion_rate: number
}

// 薄弱点分析
export interface WeaknessAnalysis {
  total_weak_points: number
  by_category: Record<string, number>
  by_difficulty: Record<string, number>
  top_weak_points: {
    point: string
    category: string
    severity: number
    affected_areas: string[]
  }[]
}

// 学习建议
export interface LearningRecommendation {
  category: string
  priority: 'high' | 'medium' | 'low'
  title: string
  description: string
  estimated_time: number
  resources: string[]
  target_abilities: string[]
}

// 能力评估
export interface AbilityAssessment {
  vocabulary: {
    level: string
    score: number
    word_count: number
    strength_areas: string[]
    weak_areas: string[]
  }
  grammar: {
    level: string
    score: number
    mastered_rules: string[]
    weak_rules: string[]
  }
  reading: {
    level: string
    score: number
    comprehension_rate: number
    speed_wpm: number
  }
  listening: {
    level: string
    score: number
    comprehension_rate: number
  }
  speaking: {
    level: string
    score: number
    fluency: number
    pronunciation: number
  }
  writing: {
    level: string
    score: number
    grammar_score: number
    vocabulary_score: number
  }
}

// 考试准备度
export interface ExamReadiness {
  exam_type: string
  overall_readiness: number
  section_scores: Record<string, number>
  recommended_study_plan: {
    duration_weeks: number
    weekly_hours: number
    focus_areas: string[]
  }
  weak_sections: string[]
  strengths: string[]
}

// AI分析结果
export interface AIAnalysisResult {
  cefr_level: string
  abilities: AbilityAssessment
  weak_points: WeaknessAnalysis
  learning_recommendations: LearningRecommendation[]
  exam_readiness?: ExamReadiness
  learning_style?: string
  personality_insights?: string
  next_milestones: string[]
  confidence_score: number
}
