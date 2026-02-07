<template>
  <div class="mistake-book-page">
    <!-- 页面头部 -->
    <el-page-header
      class="mb-4"
      @back="$router.go(-1)"
    >
      <template #content>
        <div class="flex items-center">
          <el-icon class="mr-2">
            <Document />
          </el-icon>
          <span class="text-lg font-medium">我的错题本</span>
        </div>
      </template>
    </el-page-header>

    <!-- 统计卡片 -->
    <el-row
      :gutter="20"
      class="mb-6"
    >
      <el-col
        :xs="12"
        :sm="6"
      >
        <el-card
          shadow="hover"
          class="stat-card"
        >
          <div class="stat-content">
            <div class="stat-icon total">
              <el-icon><Collection /></el-icon>
            </div>
            <div class="stat-text">
              <div class="stat-value">
                {{ statistics.total_mistakes }}
              </div>
              <div class="stat-label">
                总错题数
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col
        :xs="12"
        :sm="6"
      >
        <el-card
          shadow="hover"
          class="stat-card"
        >
          <div class="stat-content">
            <div class="stat-icon pending">
              <el-icon><Clock /></el-icon>
            </div>
            <div class="stat-text">
              <div class="stat-value">
                {{ statistics.need_review_count }}
              </div>
              <div class="stat-label">
                待复习
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col
        :xs="12"
        :sm="6"
      >
        <el-card
          shadow="hover"
          class="stat-card"
        >
          <div class="stat-content">
            <div class="stat-icon mastered">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="stat-text">
              <div class="stat-value">
                {{ Math.round(statistics.mastery_rate * 100) }}%
              </div>
              <div class="stat-label">
                掌握率
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col
        :xs="12"
        :sm="6"
      >
        <el-card
          shadow="hover"
          class="stat-card"
        >
          <div class="stat-content">
            <div class="stat-icon frequent">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="stat-text">
              <div class="stat-value">
                {{ statistics.frequent_mistakes_count }}
              </div>
              <div class="stat-label">
                高频错题
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 智能复习提醒卡片 -->
    <el-row
      v-if="todayReviewData"
      :gutter="20"
      class="mb-6"
    >
      <el-col :span="24">
        <el-card
          shadow="hover"
          class="review-reminder-card"
        >
          <template #header>
            <div class="review-header">
              <div class="review-title">
                <el-icon class="mr-2">
                  <Clock />
                </el-icon>
                <span>今日智能复习提醒</span>
              </div>
              <el-tag
                :type="todayReviewData.overdue_count > 0 ? 'danger' : 'success'"
                size="small"
              >
                {{ todayReviewData.overdue_count }}道已过期
              </el-tag>
            </div>
          </template>
          <el-row :gutter="16">
            <el-col
              :xs="8"
              :sm="4"
              class="text-center"
            >
              <div class="review-count overdue">
                <div class="count-value">
                  {{ todayReviewData.overdue_count }}
                </div>
                <div class="count-label">
                  已过期
                </div>
              </div>
            </el-col>
            <el-col
              :xs="8"
              :sm="4"
              class="text-center"
            >
              <div class="review-count urgent">
                <div class="count-value">
                  {{ todayReviewData.urgent_count }}
                </div>
                <div class="count-label">
                  即将过期
                </div>
              </div>
            </el-col>
            <el-col
              :xs="8"
              :sm="4"
              class="text-center"
            >
              <div class="review-count today">
                <div class="count-value">
                  {{ todayReviewData.today_count }}
                </div>
                <div class="count-label">
                  今日复习
                </div>
              </div>
            </el-col>
            <el-col
              :xs="12"
              :sm="6"
            >
              <el-progress
                type="circle"
                :percentage="Math.round((todayReviewData.today_count / Math.max(todayReviewData.total_count, 1)) * 100)"
                :width="80"
              >
                <div class="progress-text">
                  <div class="progress-value">
                    {{ todayReviewData.today_count }}
                  </div>
                  <div class="progress-label">
                    今日任务
                  </div>
                </div>
              </el-progress>
            </el-col>
            <el-col
              :xs="12"
              :sm="6"
              class="flex items-center"
            >
              <div class="review-actions">
                <el-button
                  type="primary"
                  @click="showSmartReview = true"
                >
                  <el-icon><MagicStick /></el-icon>
                  开始复习
                </el-button>
                <el-button @click="showReviewCalendar = true">
                  <el-icon><Calendar /></el-icon>
                  复习日历
                </el-button>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>

    <!-- 筛选和操作栏 -->
    <el-card class="mb-4">
      <el-row
        :gutter="16"
        align="middle"
      >
        <el-col
          :xs="24"
          :sm="6"
        >
          <el-select
            v-model="filters.status"
            placeholder="状态筛选"
            clearable
            class="w-full"
            @change="loadMistakes"
          >
            <el-option
              label="待复习"
              value="pending"
            />
            <el-option
              label="复习中"
              value="reviewing"
            />
            <el-option
              label="已掌握"
              value="mastered"
            />
            <el-option
              label="已忽略"
              value="ignored"
            />
          </el-select>
        </el-col>
        <el-col
          :xs="24"
          :sm="6"
        >
          <el-select
            v-model="filters.mistake_type"
            placeholder="类型筛选"
            clearable
            class="w-full"
            @change="loadMistakes"
          >
            <el-option
              label="语法"
              value="grammar"
            />
            <el-option
              label="词汇"
              value="vocabulary"
            />
            <el-option
              label="阅读"
              value="reading"
            />
            <el-option
              label="听力"
              value="listening"
            />
            <el-option
              label="写作"
              value="writing"
            />
            <el-option
              label="口语"
              value="speaking"
            />
          </el-select>
        </el-col>
        <el-col
          :xs="24"
          :sm="6"
        >
          <el-input
            v-model="filters.topic"
            placeholder="主题筛选"
            clearable
            @change="loadMistakes"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col
          :xs="24"
          :sm="6"
        >
          <el-button-group class="w-full">
            <el-button
              class="flex-1"
              @click="showReviewPlan = true"
            >
              <el-icon class="mr-1">
                <Calendar />
              </el-icon>
              复习计划
            </el-button>
            <el-button
              class="flex-1"
              @click="handleCollectFromPractice"
            >
              <el-icon class="mr-1">
                <Download />
              </el-icon>
              收集错题
            </el-button>
          </el-button-group>
        </el-col>
        <el-col
          :xs="24"
          :sm="6"
          class="text-right"
        >
          <el-dropdown
            class="mr-2"
            @command="handleBatchAction"
          >
            <el-button
              type="primary"
              :loading="batchAnalyzing"
              :disabled="statistics.need_review_count === 0"
            >
              <el-icon class="mr-1">
                <MagicStick />
              </el-icon>
              AI批量分析
              <el-icon class="ml-1">
                <ArrowDown />
              </el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="analyze">
                  <el-icon><MagicStick /></el-icon>
                  批量AI分析
                </el-dropdown-item>
                <el-dropdown-item
                  divided
                  command="export_markdown"
                >
                  <el-icon><Document /></el-icon>
                  导出为Markdown
                </el-dropdown-item>
                <el-dropdown-item command="export_pdf">
                  <el-icon><Tickets /></el-icon>
                  导出为PDF
                </el-dropdown-item>
                <el-dropdown-item command="export_word">
                  <el-icon><Memo /></el-icon>
                  导出为Word
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </el-col>
      </el-row>
    </el-card>

    <!-- 错题列表 -->
    <el-card v-loading="loading">
      <template v-if="mistakes.length === 0 && !loading">
        <el-empty description="暂无错题记录">
          <el-button
            type="primary"
            @click="handleCollectFromPractice"
          >
            从练习中收集错题
          </el-button>
        </el-empty>
      </template>
      <template v-else>
        <div
          v-for="mistake in mistakes"
          :key="mistake.id"
          class="mistake-item"
        >
          <el-card
            shadow="hover"
            class="mistake-card"
          >
            <div class="mistake-header">
              <div class="mistake-badges">
                <el-tag
                  :type="getStatusType(mistake.status)"
                  size="small"
                >
                  {{ getStatusText(mistake.status) }}
                </el-tag>
                <el-tag
                  :type="getTypeTagType(mistake.mistake_type)"
                  size="small"
                  class="ml-2"
                >
                  {{ getTypeText(mistake.mistake_type) }}
                </el-tag>
                <el-tag
                  v-if="mistake.topic"
                  type="info"
                  size="small"
                  class="ml-2"
                >
                  {{ mistake.topic }}
                </el-tag>
              </div>
              <div class="mistake-actions">
                <el-button
                  link
                  type="primary"
                  @click="handleViewDetail(mistake)"
                >
                  查看详情
                </el-button>
                <el-button
                  v-if="!mistake.ai_suggestion"
                  link
                  type="warning"
                  :loading="analyzingMistakeId === mistake.id"
                  @click="handleAnalyze(mistake)"
                >
                  <el-icon class="mr-1">
                    <MagicStick />
                  </el-icon>
                  AI分析
                </el-button>
                <el-button
                  link
                  type="success"
                  @click="handleRetry(mistake)"
                >
                  重做
                </el-button>
              </div>
            </div>

            <div class="mistake-question mt-3">
              <div class="question-label">
                题目：
              </div>
              <div class="question-content">
                {{ mistake.question }}
              </div>
            </div>

            <div class="mistake-answers mt-3">
              <el-row :gutter="16">
                <el-col :span="12">
                  <div class="answer-item wrong">
                    <div class="answer-label">
                      我的答案：
                    </div>
                    <div class="answer-content">
                      {{ mistake.wrong_answer }}
                    </div>
                  </div>
                </el-col>
                <el-col :span="12">
                  <div class="answer-item correct">
                    <div class="answer-label">
                      正确答案：
                    </div>
                    <div class="answer-content">
                      {{ mistake.correct_answer }}
                    </div>
                  </div>
                </el-col>
              </el-row>
            </div>

            <div
              v-if="mistake.explanation"
              class="mistake-explanation mt-3"
            >
              <el-alert
                type="info"
                :closable="false"
              >
                <template #title>
                  <div class="explanation-title">
                    <el-icon><InfoFilled /></el-icon>
                    <span>解析</span>
                  </div>
                </template>
                <div class="explanation-content">
                  {{ mistake.explanation }}
                </div>
              </el-alert>
            </div>

            <div class="mistake-footer mt-3">
              <div class="mistake-stats">
                <span class="mr-4">
                  <el-icon><Document /></el-icon>
                  错误 {{ mistake.mistake_count }} 次
                </span>
                <span class="mr-4">
                  <el-icon><View /></el-icon>
                  复习 {{ mistake.review_count }} 次
                </span>
                <span>
                  <el-icon><TrendCharts /></el-icon>
                  掌握度 {{ Math.round(mistake.mastery_level * 100) }}%
                </span>
              </div>
              <div class="mistake-date">
                最后错误：{{ formatDate(mistake.last_mistaken_at) }}
              </div>
            </div>
          </el-card>
        </div>

        <!-- 分页 -->
        <div class="pagination-wrapper mt-4">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :total="pagination.total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="loadMistakes"
            @current-change="loadMistakes"
          />
        </div>
      </template>
    </el-card>

    <!-- 错题详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      title="错题详情"
      width="700px"
    >
      <div v-if="currentMistake">
        <div class="detail-section">
          <h4>题目</h4>
          <p class="detail-content">
            {{ currentMistake.question }}
          </p>
        </div>

        <div class="detail-section">
          <h4>答案对比</h4>
          <el-row :gutter="16">
            <el-col :span="12">
              <div class="answer-comparison wrong">
                <div class="label">
                  我的答案
                </div>
                <div class="content">
                  {{ currentMistake.wrong_answer }}
                </div>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="answer-comparison correct">
                <div class="label">
                  正确答案
                </div>
                <div class="content">
                  {{ currentMistake.correct_answer }}
                </div>
              </div>
            </el-col>
          </el-row>
        </div>

        <div
          v-if="currentMistake.explanation"
          class="detail-section"
        >
          <h4>解析</h4>
          <p class="detail-content">
            {{ currentMistake.explanation }}
          </p>
        </div>

        <div
          v-if="currentMistake.knowledge_points?.length"
          class="detail-section"
        >
          <h4>知识点</h4>
          <div class="knowledge-points">
            <el-tag
              v-for="point in currentMistake.knowledge_points"
              :key="point"
              type="info"
              size="small"
              class="mr-2"
            >
              {{ point }}
            </el-tag>
          </div>
        </div>

        <div
          v-if="currentMistake.ai_suggestion"
          class="detail-section"
        >
          <h4>
            <el-icon class="mr-1">
              <MagicStick />
            </el-icon>
            AI 学习建议
          </h4>

          <!-- AI鼓励语 -->
          <div class="ai-encouragement mb-4">
            <el-alert
              type="success"
              :closable="false"
            >
              <template #title>
                <span class="encouragement-text">{{ currentMistake.ai_suggestion.split('\n')[0] }}</span>
              </template>
            </el-alert>
          </div>

          <!-- AI详细分析 -->
          <div
            v-if="currentMistake.ai_analysis && Object.keys(currentMistake.ai_analysis).length > 0"
            class="ai-analysis-details"
          >
            <!-- 错误分类和严重程度 -->
            <div class="analysis-item mb-3">
              <div class="analysis-label">
                错误分类：
              </div>
              <el-tag :type="getSeverityTagType(String(currentMistake.ai_analysis?.severity || ''))">
                {{ currentMistake.ai_analysis?.mistake_category || '-' }}
              </el-tag>
              <el-tag
                type="info"
                class="ml-2"
              >
                {{ getSeverityText(String(currentMistake.ai_analysis?.severity || '')) }}
              </el-tag>
            </div>

            <!-- 详细解释 -->
            <div
              v-if="currentMistake.ai_analysis.explanation"
              class="analysis-item mb-3"
            >
              <div class="analysis-label">
                错误解释：
              </div>
              <div class="analysis-content">
                {{ currentMistake.ai_analysis.explanation }}
              </div>
            </div>

            <!-- 正确方法 -->
            <div
              v-if="currentMistake.ai_analysis.correct_approach"
              class="analysis-item mb-3"
            >
              <div class="analysis-label">
                正确方法：
              </div>
              <div class="analysis-content">
                {{ currentMistake.ai_analysis.correct_approach }}
              </div>
            </div>

            <!-- 学习建议列表 -->
            <div
              v-if="currentMistake.ai_analysis.recommendations && currentMistake.ai_analysis.recommendations.length > 0"
              class="analysis-item mb-3"
            >
              <div class="analysis-label">
                学习建议：
              </div>
              <div class="recommendations-list">
                <div
                  v-for="(rec, idx) in currentMistake.ai_analysis.recommendations"
                  :key="idx"
                  class="recommendation-item"
                >
                  <div class="rec-priority">
                    <el-tag
                      :type="getPriorityTagType(rec.priority)"
                      size="small"
                    >
                      优先级 {{ rec.priority }}
                    </el-tag>
                    <span class="rec-category ml-2">{{ rec.category }}</span>
                  </div>
                  <div class="rec-title">
                    {{ rec.title }}
                  </div>
                  <div class="rec-description">
                    {{ rec.description }}
                  </div>
                  <div
                    v-if="rec.resources && rec.resources.length"
                    class="rec-resources mt-2"
                  >
                    <div class="resources-label">
                      推荐资源：
                    </div>
                    <div class="resources-list">
                      <div
                        v-for="(res, ridx) in rec.resources"
                        :key="ridx"
                        class="resource-item"
                      >
                        • {{ res }}
                      </div>
                    </div>
                  </div>
                  <div
                    v-if="rec.practice_exercises && rec.practice_exercises.length"
                    class="rec-exercises mt-2"
                  >
                    <div class="exercises-label">
                      练习建议：
                    </div>
                    <div class="exercises-list">
                      <div
                        v-for="(ex, eidx) in rec.practice_exercises"
                        :key="eidx"
                        class="exercise-item"
                      >
                        • {{ ex }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 复习计划 -->
            <div
              v-if="currentMistake.ai_analysis.review_plan"
              class="analysis-item"
            >
              <div class="analysis-label">
                复习计划：
              </div>
              <div class="review-plan-details">
                <div class="plan-item">
                  <span class="plan-label">复习频率：</span>
                  <span class="plan-value">{{ currentMistake.ai_analysis.review_plan.review_frequency }}</span>
                </div>
                <div class="plan-item">
                  <span class="plan-label">复习间隔：</span>
                  <span class="plan-value">{{ Array.isArray(currentMistake.ai_analysis?.review_plan?.next_review_days) ? currentMistake.ai_analysis.review_plan.next_review_days.join('天、') : currentMistake.ai_analysis?.review_plan?.next_review_days }}天</span>
                </div>
                <div class="plan-item">
                  <span class="plan-label">掌握标准：</span>
                  <span class="plan-value">{{ currentMistake.ai_analysis.review_plan.mastery_criteria }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <h4>统计信息</h4>
          <el-descriptions
            :column="2"
            border
          >
            <el-descriptions-item label="错误次数">
              {{ currentMistake.mistake_count }} 次
            </el-descriptions-item>
            <el-descriptions-item label="复习次数">
              {{ currentMistake.review_count }} 次
            </el-descriptions-item>
            <el-descriptions-item label="掌握程度">
              {{ Math.round(currentMistake.mastery_level * 100) }}%
            </el-descriptions-item>
            <el-descriptions-item label="首次错误">
              {{ formatDate(currentMistake.first_mistaken_at) }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showDetailDialog = false">关闭</el-button>
          <el-dropdown
            class="ml-2"
            @command="handleExportSingle"
          >
            <el-button
              type="success"
              :loading="exporting"
            >
              <el-icon><Download /></el-icon>
              导出此题
              <el-icon class="ml-1"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="markdown">
                  <el-icon><Document /></el-icon>
                  Markdown格式
                </el-dropdown-item>
                <el-dropdown-item command="pdf">
                  <el-icon><Tickets /></el-icon>
                  PDF格式
                </el-dropdown-item>
                <el-dropdown-item command="word">
                  <el-icon><Memo /></el-icon>
                  Word格式
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button
            type="primary"
            @click="handleRetry(currentMistake!)"
          >
            重做此题
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 重做对话框 -->
    <el-dialog
      v-model="showRetryDialog"
      title="重做错题"
      width="600px"
    >
      <div v-if="currentMistake">
        <div class="retry-question">
          <h4>题目</h4>
          <p>{{ currentMistake.question }}</p>
        </div>

        <el-form
          :model="retryForm"
          label-width="80px"
        >
          <el-form-item label="你的答案">
            <el-input
              v-model="retryForm.user_answer"
              type="textarea"
              :rows="3"
              placeholder="请输入你的答案"
            />
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <el-button @click="showRetryDialog = false">
          取消
        </el-button>
        <el-button
          type="primary"
          :loading="retryLoading"
          @click="handleSubmitRetry"
        >
          提交答案
        </el-button>
      </template>
    </el-dialog>

    <!-- 复习计划对话框 -->
    <el-dialog
      v-model="showReviewPlan"
      title="复习计划"
      width="800px"
    >
      <div v-if="reviewPlan">
        <el-alert
          type="warning"
          :closable="false"
          class="mb-4"
        >
          基于遗忘曲线和错题优先级为您生成的个性化复习计划
        </el-alert>

        <el-tabs v-model="activeReviewTab">
          <el-tab-pane
            label="紧急复习"
            name="urgent"
          >
            <div
              v-if="reviewPlan.urgent.length === 0"
              class="text-center text-gray py-4"
            >
              暂无紧急复习的错题
            </div>
            <div v-else>
              <div
                v-for="item in reviewPlan.urgent"
                :key="item.id"
                class="review-item"
              >
                <el-card shadow="hover">
                  <div class="review-question">
                    {{ item.question }}
                  </div>
                  <div class="review-meta">
                    <el-tag size="small">
                      {{ getTypeText(item.type) }}
                    </el-tag>
                  </div>
                </el-card>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane
            label="今日复习"
            name="today"
          >
            <div
              v-if="reviewPlan.today.length === 0"
              class="text-center text-gray py-4"
            >
              今日已无待复习错题
            </div>
            <div v-else>
              <div
                v-for="item in reviewPlan.today"
                :key="item.id"
                class="review-item"
              >
                <el-card shadow="hover">
                  <div class="review-question">
                    {{ item.question }}
                  </div>
                  <div class="review-meta">
                    <el-tag size="small">
                      {{ getTypeText(item.type) }}
                    </el-tag>
                  </div>
                </el-card>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane
            label="本周复习"
            name="week"
          >
            <div
              v-if="reviewPlan.week.length === 0"
              class="text-center text-gray py-4"
            >
              本周暂无待复习错题
            </div>
            <div v-else>
              <div
                v-for="item in reviewPlan.week"
                :key="item.id"
                class="review-item"
              >
                <el-card shadow="hover">
                  <div class="review-question">
                    {{ item.question }}
                  </div>
                  <div class="review-meta">
                    <el-tag size="small">
                      {{ getTypeText(item.type) }}
                    </el-tag>
                  </div>
                </el-card>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane
            label="重点知识点"
            name="knowledge"
          >
            <div
              v-if="reviewPlan.knowledge_points.length === 0"
              class="text-center text-gray py-4"
            >
              暂无知识点统计
            </div>
            <div v-else>
              <div
                v-for="[point, count] in reviewPlan.knowledge_points"
                :key="point"
                class="knowledge-point-item"
              >
                <div class="point-name">
                  {{ point }}
                </div>
                <el-progress
                  :percentage="Math.min(count * 10, 100)"
                  :format="() => `${count}题`"
                />
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>

    <!-- 智能复习对话框 -->
    <el-dialog
      v-model="showSmartReview"
      title="智能复习提醒"
      width="900px"
    >
      <div v-if="todayReviewData">
        <el-tabs v-model="smartReviewActiveTab">
          <!-- 紧急复习 -->
          <el-tab-pane
            label="🔴 紧急复习"
            name="overdue"
          >
            <div
              v-if="todayReviewData.review_list.filter((r: any) => r.review_type === 'overdue').length === 0"
              class="text-center text-gray py-8"
            >
              <el-icon
                :size="48"
                class="mb-4"
              >
                <CircleCheck />
              </el-icon>
              <div>暂无紧急复习任务，继续保持！</div>
            </div>
            <div v-else>
              <el-empty
                v-if="todayReviewData.review_list.filter((r: any) => r.review_type === 'overdue').length === 0"
                description="暂无紧急复习"
              />
              <div v-else>
                <div
                  v-for="item in todayReviewData.review_list.filter((r: any) => r.review_type === 'overdue')"
                  :key="item.id"
                  class="smart-review-item"
                >
                  <el-card
                    shadow="hover"
                    :class="{ 'overdue-item': item.is_overdue }"
                  >
                    <div class="review-item-header">
                      <el-tag
                        type="danger"
                        size="small"
                      >
                        过期{{ item.overdue_hours }}小时
                      </el-tag>
                      <el-tag size="small">
                        {{ getTypeText(item.mistake_type) }}
                      </el-tag>
                      <el-tag
                        v-if="item.topic"
                        type="info"
                        size="small"
                      >
                        {{ item.topic }}
                      </el-tag>
                    </div>
                    <div class="review-item-content">
                      {{ item.question_preview }}
                    </div>
                    <div class="review-item-footer">
                      <span class="priority">
                        <el-icon><Top /></el-icon>
                        优先级: {{ Math.round(item.priority_score) }}分
                      </span>
                      <el-button
                        type="primary"
                        size="small"
                        @click="handleStartReview(item)"
                      >
                        开始复习
                      </el-button>
                    </div>
                  </el-card>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- 即将过期 -->
          <el-tab-pane
            label="🟡 即将过期"
            name="urgent"
          >
            <div
              v-if="todayReviewData.review_list.filter((r: any) => r.review_type === 'urgent').length === 0"
              class="text-center text-gray py-8"
            >
              <el-icon
                :size="48"
                class="mb-4"
              >
                <CircleCheck />
              </el-icon>
              <div>暂无即将过期的复习任务！</div>
            </div>
            <div v-else>
              <div
                v-for="item in todayReviewData.review_list.filter((r: any) => r.review_type === 'urgent')"
                :key="item.id"
                class="smart-review-item"
              >
                <el-card shadow="hover">
                  <div class="review-item-header">
                    <el-tag
                      type="warning"
                      size="small"
                    >
                      即将过期
                    </el-tag>
                    <el-tag size="small">
                      {{ getTypeText(item.mistake_type) }}
                    </el-tag>
                  </div>
                  <div class="review-item-content">
                    {{ item.question_preview }}
                  </div>
                  <div class="review-item-footer">
                    <span class="priority">
                      <el-icon><Top /></el-icon>
                      优先级: {{ Math.round(item.priority_score) }}分
                    </span>
                    <el-button
                      type="primary"
                      size="small"
                      @click="handleStartReview(item)"
                    >
                      开始复习
                    </el-button>
                  </div>
                </el-card>
              </div>
            </div>
          </el-tab-pane>

          <!-- 推荐复习 -->
          <el-tab-pane
            label="📚 推荐复习"
            name="recommend"
          >
            <div
              v-if="recommendData.recommendations.length === 0"
              class="text-center text-gray py-8"
            >
              <el-empty description="暂无推荐复习内容" />
            </div>
            <div v-else>
              <div
                v-for="item in recommendData.recommendations"
                :key="item.id"
                class="smart-review-item"
              >
                <el-card shadow="hover">
                  <div class="review-item-header">
                    <el-progress
                      :percentage="Math.round(item.priority_score)"
                      :stroke-width="3"
                      :show-text="false"
                      style="width: 60px;"
                    />
                    <el-tag size="small">
                      {{ getTypeText(item.mistake_type) }}
                    </el-tag>
                  </div>
                  <div class="review-item-content">
                    {{ item.question_preview }}
                  </div>
                  <div class="review-item-footer">
                    <span class="priority">
                      <el-icon><Clock /></el-icon>
                      下次复习: {{ item.next_review_at }}
                    </span>
                    <el-button
                      type="success"
                      size="small"
                      @click="handleStartReview(item)"
                    >
                      立即复习
                    </el-button>
                  </div>
                </el-card>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>

    <!-- 复习日历对话框 -->
    <el-dialog
      v-model="showReviewCalendar"
      title="复习日历"
      width="900px"
    >
      <div v-if="reviewCalendarData">
        <div class="calendar-header mb-4">
          <el-button-group>
            <el-button @click="changeCalendarMonth(-1)">
              <el-icon><ArrowLeft /></el-icon>
            </el-button>
            <el-button>{{ calendarMonth }}</el-button>
            <el-button @click="changeCalendarMonth(1)">
              <el-icon><ArrowRight /></el-icon>
            </el-button>
          </el-button-group>
        </div>

        <div class="calendar-grid">
          <div class="calendar-weekday">
            <div
              v-for="day in ['日', '一', '二', '三', '四', '五', '六']"
              :key="day"
            >
              {{ day }}
            </div>
          </div>
          <div class="calendar-days">
            <div
              v-for="(day, index) in calendarDays"
              :key="index"
              :class="['calendar-day', {
                'other-month': !day.currentMonth,
                'today': day.isToday,
                'has-tasks': day.tasks.length > 0
              }]"
            >
              <div class="day-number">
                {{ day.date }}
              </div>
              <div
                v-if="day.tasks.length > 0"
                class="day-tasks"
              >
                <el-tag
                  type="warning"
                  size="mini"
                >
                  {{ day.tasks.length }}题
                </el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 收集错题对话框 -->
    <el-dialog
      v-model="showCollectDialog"
      title="从练习中收集错题"
      width="500px"
    >
      <el-alert
        type="info"
        :closable="false"
        class="mb-4"
      >
        输入已完成的练习ID，系统将自动收集错题添加到错题本
      </el-alert>

      <el-form
        :model="collectForm"
        label-width="100px"
      >
        <el-form-item label="练习ID">
          <el-input
            v-model="collectForm.practice_id"
            placeholder="请输入练习ID"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCollectDialog = false">
          取消
        </el-button>
        <el-button
          type="primary"
          :loading="collectLoading"
          @click="handleSubmitCollect"
        >
          开始收集
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus'
import {
  Document,
  Collection,
  Clock,
  CircleCheck,
  Warning,
  Calendar,
  Download,
  Search,
  InfoFilled,
  View,
  TrendCharts,
  MagicStick,
  ArrowDown,
  Tickets,
  Memo,
  ArrowLeft,
  ArrowRight,
  Top
} from '@element-plus/icons-vue'
import mistakeApi, {
  type Mistake,
  type MistakeStatistics,
  type ReviewPlan,
  type RetryMistakeRequest,
  type TodayReviewResponse,
  type RecommendReviewResponse,
  type ReviewCalendarResponse,
  type ReviewItem,
  MistakeStatus,
  MistakeType
} from '@/api/mistake'

// AI分析类型定义
interface AIAnalysis {
  severity: 'low' | 'medium' | 'high'
  mistake_category: string
  explanation?: string
  correct_approach?: string
  recommendations?: AIRecommendation[]
  grammar_explanation?: string
  vocabulary_notes?: string
  practice_exercises?: PracticeExercise[]
  review_plan?: {
    review_frequency: string
    next_review_days: number | number[]
    mastery_criteria: string
  }
}

interface AIRecommendation {
  priority: 'high' | 'medium' | 'low'
  category: string
  title: string
  description: string
  resources?: string[]
  practice_exercises?: PracticeExercise[]
}

interface PracticeExercise {
  type: string
  question: string
  options?: string[]
  answer: string
}

// 数据状态
const loading = ref(false)
const mistakes = ref<Mistake[]>([])
const statistics = ref<MistakeStatistics>({
  student_id: '',
  total_mistakes: 0,
  by_status: {},
  by_type: {},
  by_topic: {},
  mastery_rate: 0,
  need_review_count: 0,
  recent_mistakes_count: 0,
  frequent_mistakes_count: 0
})
const reviewPlan = ref<ReviewPlan | null>(null)

// 智能复习数据
const todayReviewData = ref<TodayReviewResponse | null>(null)
const recommendData = ref<RecommendReviewResponse>({
  student_id: '',
  recommended_count: 0,
  recommendations: []
})
const reviewCalendarData = ref<ReviewCalendarResponse | null>(null)

// 智能复习对话框状态
const showSmartReview = ref(false)
const showReviewCalendar = ref(false)
const smartReviewActiveTab = ref('overdue')
const calendarMonth = ref('')

// AI分析状态
const analyzingMistakeId = ref<string | null>(null)
const batchAnalyzing = ref(false)

// 筛选条件
const filters = reactive({
  status: '',
  mistake_type: '',
  topic: ''
})

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 对话框状态
const showDetailDialog = ref(false)
const showRetryDialog = ref(false)
const showReviewPlan = ref(false)
const showCollectDialog = ref(false)
const currentMistake = ref<Mistake & { ai_analysis?: AIAnalysis } | null>(null)

// 重做表单
const retryForm = reactive({
  user_answer: ''
})
const retryLoading = ref(false)

// 收集表单
const collectForm = reactive({
  practice_id: ''
})
const collectLoading = ref(false)

// 复习计划当前标签
const activeReviewTab = ref('urgent')

// 加载错题列表
const loadMistakes = async () => {
  loading.value = true
  try {
    const offset = (pagination.page - 1) * pagination.pageSize
    const response = await mistakeApi.getMyMistakes({
      status: filters.status as MistakeStatus || undefined,
      mistake_type: filters.mistake_type as MistakeType || undefined,
      topic: filters.topic || undefined,
      limit: pagination.pageSize,
      offset
    })

    mistakes.value = response.mistakes
    pagination.total = response.total
  } catch (error) {
    console.error('加载错题列表失败:', error)
    ElMessage.error('加载错题列表失败')
  } finally {
    loading.value = false
  }
}

// 加载统计数据
const loadStatistics = async () => {
  try {
    const data = await mistakeApi.getStatistics()
    statistics.value = data
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

// 加载复习计划
const loadReviewPlan = async () => {
  try {
    const data = await mistakeApi.getReviewPlan(20)
    reviewPlan.value = data
  } catch (error) {
    console.error('加载复习计划失败:', error)
  }
}

// 加载今日复习清单
const loadTodayReview = async () => {
  try {
    const data = await mistakeApi.getTodayReview(20)
    todayReviewData.value = data
  } catch (error) {
    console.error('加载今日复习清单失败:', error)
  }
}

// 加载推荐复习
const loadRecommendReview = async () => {
  try {
    const data = await mistakeApi.getRecommendReview(10)
    recommendData.value = data
  } catch (error) {
    console.error('加载推荐复习失败:', error)
  }
}

// 加载复习日历
const loadReviewCalendar = async () => {
  try {
    const data = await mistakeApi.getReviewCalendar(30)
    reviewCalendarData.value = data
  } catch (error) {
    console.error('加载复习日历失败:', error)
  }
}

// 开始复习
const handleStartReview = (item: ReviewItem) => {
  // 查找对应的错题并打开重做对话框
  const foundMistake = mistakes.value.find(m => m.id === item.id)
  currentMistake.value = (foundMistake as Mistake & { ai_analysis?: AIAnalysis } | null)
  if (currentMistake.value) {
    showSmartReview.value = false
    retryForm.user_answer = ''
    showRetryDialog.value = true
  } else {
    ElMessage.warning('未找到对应的错题')
  }
}

// 日历相关
const calendarDays = ref<Array<{
  date: number
  currentMonth: boolean
  isToday: boolean
  tasks: any[]
}>>([])

const changeCalendarMonth = async (_delta: number) => {
  // 简化的月份切换，实际可能需要更复杂的逻辑
  await loadReviewCalendar()
}

// initCalendarDays reserved for future calendar initialization
// const _initCalendarDays = () => {
  const now = new Date()
  const year = now.getFullYear()
  const month = now.getMonth()
  calendarMonth.value = `${year}年${month + 1}月`

  // 简化的日历初始化
  // calendarDays.value = []
// }

// 查看详情
const handleViewDetail = (mistake: Mistake) => {
  currentMistake.value = mistake as Mistake & { ai_analysis?: AIAnalysis }
  showDetailDialog.value = true
}

// 重做错题
const handleRetry = (mistake: Mistake) => {
  currentMistake.value = mistake as Mistake & { ai_analysis?: AIAnalysis }
  retryForm.user_answer = ''
  showRetryDialog.value = true
}

// 提交重做
const handleSubmitRetry = async () => {
  if (!currentMistake.value || !retryForm.user_answer.trim()) {
    ElMessage.warning('请输入答案')
    return
  }

  retryLoading.value = true
  try {
    const data: RetryMistakeRequest = {
      user_answer: retryForm.user_answer,
      is_correct: false // 需要前端判断或后端判断
    }

    // TODO: 添加答案判断逻辑
    // 简单的字符串比较，实际可能需要更复杂的判断
    data.is_correct = retryForm.user_answer.trim().toLowerCase() ===
      currentMistake.value.correct_answer.toLowerCase()

    const result = await mistakeApi.retryMistake(currentMistake.value.id, data)

    showRetryDialog.value = false

    if (result.mastered) {
      ElMessage.success('恭喜！已掌握此题')
    } else if (data.is_correct) {
      ElMessage.success('回答正确！继续加油')
    } else {
      ElMessage.warning('回答错误，请继续复习')
    }

    // 刷新列表
    await loadMistakes()
    await loadStatistics()
  } catch (error) {
    console.error('提交重做失败:', error)
    ElMessage.error('提交失败')
  } finally {
    retryLoading.value = false
  }
}

// 收集错题
const handleCollectFromPractice = () => {
  collectForm.practice_id = ''
  showCollectDialog.value = true
}

// 提交收集
const handleSubmitCollect = async () => {
  if (!collectForm.practice_id.trim()) {
    ElMessage.warning('请输入练习ID')
    return
  }

  collectLoading.value = true
  try {
    const result = await mistakeApi.collectFromPractice(collectForm.practice_id.trim())
    showCollectDialog.value = false
    ElMessage.success(result.message)

    // 刷新列表
    await loadMistakes()
    await loadStatistics()
  } catch (error: any) {
    console.error('收集错题失败:', error)
    const message = error.response?.data?.detail || '收集失败'
    ElMessage.error(message)
  } finally {
    collectLoading.value = false
  }
}

// 单个错题AI分析
const handleAnalyze = async (mistake: Mistake) => {
  analyzingMistakeId.value = mistake.id
  try {
    const result = await mistakeApi.analyzeMistake(mistake.id)

    // 更新本地错题数据
    const index = mistakes.value.findIndex(m => m.id === mistake.id)
    if (index !== -1) {
      mistakes.value[index] = {
        ...mistakes.value[index],
        ai_suggestion: result.analysis.encouragement + '\n\n' + result.analysis.explanation,
        ai_analysis: result.analysis
      } as unknown as Mistake & { ai_analysis?: AIAnalysis; needs_ai_analysis?: boolean }
    }

    ElMessage.success('AI分析完成！')
    await loadStatistics()
  } catch (error: any) {
    console.error('AI分析失败:', error)
    const message = error.response?.data?.detail || 'AI分析失败'
    ElMessage.error(message)
  } finally {
    analyzingMistakeId.value = null
  }
}

// 批量AI分析
const handleBatchAnalyze = async () => {
  await ElMessageBox.confirm(
    `将对${statistics.value.need_review_count}道待AI分析的错题进行批量分析，这可能需要一些时间。是否继续？`,
    '批量AI分析确认',
    {
      confirmButtonText: '开始分析',
      cancelButtonText: '取消',
      type: 'warning',
    }
  )

  batchAnalyzing.value = true
  try {
    const result = await mistakeApi.batchAnalyzeMistakes(10)

    ElMessageBox.alert(
      `
分析总结：${result.summary}

常见错误模式：${result.common_patterns.length > 0 ? result.common_patterns.join('、') : '无'}

重点关注：${result.priority_topics.length > 0 ? result.priority_topics.join('、') : '无'}
      `,
      '批量分析完成',
      {
        confirmButtonText: '查看详情',
        type: 'success',
      }
    )

    // 刷新列表
    await loadMistakes()
    await loadStatistics()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('批量AI分析失败:', error)
      const message = error.response?.data?.detail || '批量分析失败'
      ElMessage.error(message)
    }
  } finally {
    batchAnalyzing.value = false
  }
}

// 批量操作（AI分析和导出）
const handleBatchAction = async (command: string) => {
  switch (command) {
    case 'analyze':
      await handleBatchAnalyze()
      break
    case 'export_markdown':
      await handleExport('markdown')
      break
    case 'export_pdf':
      await handleExport('pdf')
      break
    case 'export_word':
      await handleExport('word')
      break
  }
}

// 导出错题本
const exporting = ref(false)
const handleExport = async (format: 'markdown' | 'pdf' | 'word') => {
  const formatNames = {
    markdown: 'Markdown',
    pdf: 'PDF',
    word: 'Word'
  }

  try {
    await ElMessageBox.confirm(
      `将导出当前筛选条件下的${statistics.value.total_mistakes}道错题为${formatNames[format]}格式。是否继续？`,
      '导出确认',
      {
        confirmButtonText: '确认导出',
        cancelButtonText: '取消',
        type: 'info',
      }
    )

    exporting.value = true
    const loading = ElLoading.service({
      lock: true,
      text: `正在生成${formatNames[format]}文件...`,
      background: 'rgba(0, 0, 0, 0.7)',
    })

    try {
      await mistakeApi.exportMistakes({
        format_type: format,
        status_filter: filters.status || undefined,
        type_filter: filters.mistake_type || undefined,
        topic_filter: filters.topic || undefined,
      })

      ElMessage.success(`${formatNames[format]}文件导出成功！`)
    } finally {
      loading.close()
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('导出失败:', error)
      const message = error?.response?.data?.detail || error?.message || '导出失败'
      ElMessage.error(message)
    }
  } finally {
    exporting.value = false
  }
}

// 导出单个错题
const handleExportSingle = async (format: 'markdown' | 'pdf' | 'word') => {
  if (!currentMistake.value) return

  const formatNames = {
    markdown: 'Markdown',
    pdf: 'PDF',
    word: 'Word'
  }

  try {
    exporting.value = true
    const loading = ElLoading.service({
      lock: true,
      text: `正在生成${formatNames[format]}文件...`,
      background: 'rgba(0, 0, 0, 0.7)',
    })

    try {
      await mistakeApi.exportSingleMistake(
        currentMistake.value.id,
        format
      )

      ElMessage.success(`${formatNames[format]}文件导出成功！`)
    } finally {
      loading.close()
    }
  } catch (error: any) {
    console.error('导出失败:', error)
    const message = error?.response?.data?.detail || error?.message || '导出失败'
    ElMessage.error(message)
  } finally {
    exporting.value = false
  }
}

// 工具函数
const getStatusType = (status: string) => {
  const types: Record<string, any> = {
    pending: 'warning',
    reviewing: 'primary',
    mastered: 'success',
    ignored: 'info'
  }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    pending: '待复习',
    reviewing: '复习中',
    mastered: '已掌握',
    ignored: '已忽略'
  }
  return texts[status] || status
}

const getTypeTagType = (type: string) => {
  const types: Record<string, any> = {
    grammar: 'danger',
    vocabulary: 'warning',
    reading: 'primary',
    listening: 'success',
    writing: 'info',
    speaking: 'purple'
  }
  return types[type] || ''
}

const getTypeText = (type: string) => {
  const texts: Record<string, string> = {
    grammar: '语法',
    vocabulary: '词汇',
    reading: '阅读',
    listening: '听力',
    writing: '写作',
    speaking: '口语',
    pronunciation: '发音',
    comprehension: '理解'
  }
  return texts[type] || type
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN')
}

// AI分析相关工具函数
const getSeverityTagType = (severity: string) => {
  const types: Record<string, any> = {
    '轻微': 'success',
    '中等': 'warning',
    '严重': 'danger'
  }
  return types[severity] || 'info'
}

const getSeverityText = (severity: string) => {
  return severity
}

const getPriorityTagType = (priority: string | number) => {
  if (priority === 'high' || priority === 1) return 'danger'
  if (priority === 'medium' || priority === 2) return 'warning'
  if (priority === 'low' || priority === 3) return 'primary'
  return ''
}

// 初始化
onMounted(async () => {
  await Promise.all([
    loadMistakes(),
    loadStatistics(),
    loadReviewPlan(),
    loadTodayReview(),
    loadRecommendReview(),
    loadReviewCalendar()
  ])
})
</script>

<style scoped>
.mistake-book-page {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

/* 统计卡片 */
.stat-card {
  border-radius: 12px;
  overflow: hidden;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: white;
}

.stat-icon.total { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.stat-icon.pending { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
.stat-icon.mastered { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
.stat-icon.frequent { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

/* 错题卡片 */
.mistake-item {
  margin-bottom: 16px;
}

.mistake-card {
  border-radius: 12px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.mistake-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.mistake-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.mistake-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.mistake-actions {
  display: flex;
  gap: 8px;
}

.mistake-question .question-label {
  font-weight: 600;
  color: #606266;
  margin-bottom: 8px;
}

.mistake-question .question-content {
  color: #303133;
  line-height: 1.6;
}

.answer-item {
  padding: 12px;
  border-radius: 8px;
}

.answer-item.wrong {
  background: #fef0f0;
  border-left: 4px solid #f56c6c;
}

.answer-item.correct {
  background: #f0f9ff;
  border-left: 4px solid #67c23a;
}

.answer-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 4px;
}

.answer-content {
  color: #303133;
  line-height: 1.5;
}

.explanation-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.explanation-content {
  line-height: 1.6;
  color: #606266;
}

.mistake-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
  color: #909399;
  font-size: 13px;
}

.mistake-stats {
  display: flex;
  gap: 16px;
}

.mistake-stats span {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 详情对话框 */
.detail-section {
  margin-bottom: 20px;
}

.detail-section h4 {
  margin-bottom: 12px;
  color: #303133;
}

.detail-content {
  color: #606266;
  line-height: 1.6;
}

.answer-comparison {
  padding: 16px;
  border-radius: 8px;
}

.answer-comparison.wrong {
  background: #fef0f0;
  border: 1px solid #fbc4c4;
}

.answer-comparison.correct {
  background: #f0f9ff;
  border: 1px solid #c6e2ff;
}

.answer-comparison .label {
  font-weight: 600;
  margin-bottom: 8px;
}

.answer-comparison.wrong .label { color: #f56c6c; }
.answer-comparison.correct .label { color: #67c23a; }

.answer-comparison .content {
  color: #303133;
  line-height: 1.5;
}

.knowledge-points {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* 复习计划 */
.review-item {
  margin-bottom: 12px;
}

.review-question {
  color: #303133;
  line-height: 1.5;
  margin-bottom: 8px;
}

.review-meta {
  display: flex;
  justify-content: flex-end;
}

.knowledge-point-item {
  margin-bottom: 16px;
}

.point-name {
  margin-bottom: 8px;
  color: #303133;
  font-weight: 500;
}

/* 分页 */
.pagination-wrapper {
  display: flex;
  justify-content: center;
}

/* AI分析相关样式 */
.ai-encouragement {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-radius: 8px;
  padding: 16px;
}

.encouragement-text {
  font-size: 16px;
  font-weight: 500;
  color: #0277d8;
}

.ai-analysis-details {
  background: #fafafa;
  border-radius: 8px;
  padding: 16px;
}

.analysis-item {
  margin-bottom: 16px;
}

.analysis-label {
  font-weight: 600;
  color: #606266;
  margin-bottom: 8px;
}

.analysis-content {
  color: #303133;
  line-height: 1.6;
  white-space: pre-wrap;
}

/* 学习建议卡片 */
.recommendations-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.recommendation-item {
  background: white;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  padding: 12px;
  transition: all 0.2s;
}

.recommendation-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.rec-priority {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.rec-category {
  color: #606266;
  font-size: 14px;
}

.rec-title {
  font-weight: 600;
  color: #303133;
  margin-bottom: 6px;
}

.rec-description {
  color: #606266;
  line-height: 1.5;
  margin-bottom: 8px;
}

.resources-label,
.exercises-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 4px;
}

.resources-list,
.exercises-list {
  color: #606266;
  line-height: 1.5;
}

.resource-item,
.exercise-item {
  color: #409eff;
}

/* 复习计划 */
.review-plan-details {
  display: grid;
  gap: 8px;
}

.plan-item {
  display: flex;
  align-items: center;
}

.plan-label {
  font-weight: 500;
  color: #606266;
  margin-right: 8px;
}

.plan-value {
  color: #303133;
}

/* 智能复习提醒卡片 */
.review-reminder-card {
  border-radius: 12px;
  overflow: hidden;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.review-reminder-card :deep(.el-card__header) {
  background: rgba(255, 255, 255, 0.1);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
}

.review-reminder-card :deep(.el-card__body) {
  color: white;
}

.review-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.review-title {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
}

.review-count {
  padding: 16px 8px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.15);
  margin-bottom: 8px;
}

.review-count.overdue {
  background: rgba(245, 108, 108, 0.3);
}

.review-count.urgent {
  background: rgba(230, 162, 60, 0.3);
}

.review-count.today {
  background: rgba(103, 194, 58, 0.3);
}

.count-value {
  font-size: 32px;
  font-weight: bold;
  text-align: center;
}

.count-label {
  font-size: 12px;
  text-align: center;
  opacity: 0.9;
}

.progress-text {
  text-align: center;
}

.progress-value {
  font-size: 24px;
  font-weight: bold;
}

.progress-label {
  font-size: 12px;
}

.review-actions {
  display: flex;
  gap: 12px;
}

.review-actions .el-button {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.3);
  color: white;
}

.review-actions .el-button:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* 智能复习项目 */
.smart-review-item {
  margin-bottom: 12px;
}

.smart-review-item .el-card {
  border-radius: 8px;
}

.smart-review-item .overdue-item {
  border-left: 4px solid #f56c6c;
}

.review-item-header {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.review-item-content {
  color: #303133;
  line-height: 1.5;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.review-item-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.review-item-footer .priority {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #909399;
  font-size: 13px;
}

/* 复习日历 */
.calendar-grid {
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.calendar-weekday {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  background: #f5f7fa;
  padding: 8px 0;
}

.calendar-weekday div {
  text-align: center;
  font-weight: 600;
  color: #606266;
}

.calendar-days {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
}

.calendar-day {
  min-height: 80px;
  border: 1px solid #ebeef5;
  padding: 4px;
  background: white;
}

.calendar-day.other-month {
  background: #fafafa;
  color: #c0c4cc;
}

.calendar-day.today {
  background: #ecf5ff;
}

.calendar-day.has-tasks {
  background: #fff7e6;
}

.day-number {
  font-weight: 500;
  margin-bottom: 4px;
}

.today .day-number {
  background: #409eff;
  color: white;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.day-tasks {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
}

/* 响应式 */
@media (max-width: 768px) {
  .mistake-book-page {
    padding: 12px;
  }

  .mistake-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .mistake-footer {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .mistake-actions {
    width: 100%;
  }

  .mistake-actions .el-button {
    margin-left: 0;
  }
}
</style>
