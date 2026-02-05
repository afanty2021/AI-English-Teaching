/**
 * 推荐系统状态管理
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { recommendationApi } from '@/api/recommendation'
import type {
  DailyRecommendations,
  StudentProfile,
  RecommendationFilter
} from '@/types/recommendation'

export const useRecommendationStore = defineStore('recommendation', () => {
  // 状态
  const dailyRecommendations = ref<DailyRecommendations | null>(null)
  const studentProfile = ref<StudentProfile | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 获取每日推荐
  const getDailyRecommendations = async (
    filter?: RecommendationFilter
  ): Promise<{
    recommendations: DailyRecommendations
    studentProfile: StudentProfile
  }> => {
    loading.value = true
    error.value = null

    try {
      const result = await recommendationApi.getDailyRecommendations(filter)
      dailyRecommendations.value = result.recommendations
      studentProfile.value = result.studentProfile
      return result
    } catch (err: any) {
      error.value = err.message || '获取推荐失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 刷新推荐
  const refreshRecommendations = async (filter?: RecommendationFilter) => {
    return await getDailyRecommendations(filter)
  }

  // 标记内容完成
  const markContentCompleted = async (contentId: string, contentType: string) => {
    try {
      await recommendationApi.markContentCompleted(contentId, contentType)
      // 刷新推荐以获得最新结果
      await refreshRecommendations()
    } catch (err: any) {
      error.value = err.message || '标记完成失败'
      throw err
    }
  }

  // 提交推荐反馈
  const submitFeedback = async (
    contentId: string,
    satisfaction: number,
    reason?: string
  ) => {
    try {
      await recommendationApi.submitFeedback(contentId, satisfaction, reason)
    } catch (err: any) {
      error.value = err.message || '提交反馈失败'
      throw err
    }
  }

  // 获取推荐历史
  const getRecommendationHistory = async (page = 1, limit = 20) => {
    loading.value = true
    error.value = null

    try {
      const result = await recommendationApi.getRecommendationHistory(page, limit)
      return result
    } catch (err: any) {
      error.value = err.message || '获取推荐历史失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 重置状态
  const reset = () => {
    dailyRecommendations.value = null
    studentProfile.value = null
    loading.value = false
    error.value = null
  }

  return {
    // 状态
    dailyRecommendations,
    studentProfile,
    loading,
    error,

    // 方法
    getDailyRecommendations,
    refreshRecommendations,
    markContentCompleted,
    submitFeedback,
    getRecommendationHistory,
    reset
  }
})
