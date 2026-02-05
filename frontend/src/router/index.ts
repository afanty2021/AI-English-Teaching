/**
 * 路由配置
 * 定义应用的路由和导航守卫
 */
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { requiresAuth: false, title: '登录' }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/RegisterView.vue'),
    meta: { requiresAuth: false, title: '注册' }
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomeView.vue'),
    meta: { requiresAuth: true, title: '首页' }
  },
  {
    path: '/student',
    name: 'StudentDashboard',
    component: () => import('@/views/student/DashboardView.vue'),
    meta: { requiresAuth: true, requiresStudent: true, title: '学生中心' }
  },
  {
    path: '/student/learning',
    name: 'StudentLearning',
    component: () => import('@/views/student/LearningView.vue'),
    meta: { requiresAuth: true, requiresStudent: true, title: '学习内容' }
  },
  {
    path: '/student/speaking',
    name: 'StudentSpeaking',
    component: () => import('@/views/student/SpeakingView.vue'),
    meta: { requiresAuth: true, requiresStudent: true, title: '口语练习' }
  },
  {
    path: '/student/conversation',
    name: 'StudentConversation',
    component: () => import('@/views/student/ConversationView.vue'),
    meta: { requiresAuth: true, requiresStudent: true, title: 'AI对话练习' }
  },
  {
    path: '/student/conversations',
    name: 'StudentConversationHistory',
    component: () => import('@/views/student/ConversationHistoryView.vue'),
    meta: { requiresAuth: true, requiresStudent: true, title: '对话历史' }
  },
  {
    path: '/student/progress',
    name: 'StudentProgress',
    component: () => import('@/views/student/ProgressView.vue'),
    meta: { requiresAuth: true, requiresStudent: true, title: '学习进度' }
  },
  {
    path: '/student/mistakes',
    name: 'StudentMistakes',
    component: () => import('@/views/student/MistakeBookView.vue'),
    meta: { requiresAuth: true, requiresStudent: true, title: '错题本' }
  },
  {
    path: '/student/reports',
    name: 'StudentReports',
    component: () => import('@/views/student/ReportsView.vue'),
    meta: { requiresAuth: true, requiresStudent: true, title: '学习报告' }
  },
  {
    path: '/student/reports/:id',
    name: 'ReportDetail',
    component: () => import('@/views/student/ReportDetailView.vue'),
    meta: { requiresAuth: true, requiresStudent: true, title: '报告详情' }
  },
  {
    path: '/student/practice-list',
    name: 'practice-list',
    component: () => import('@/views/student/PracticeListView.vue'),
    meta: { requiresAuth: true, requiresStudent: true, title: '练习中心' }
  },
  {
    path: '/student/practice/:sessionId',
    name: 'practice',
    component: () => import('@/views/student/PracticeView.vue'),
    meta: { requiresAuth: true, requiresStudent: true, title: '练习答题' }
  },
  {
    path: '/student/practice-result/:sessionId',
    name: 'practice-result',
    component: () => import('@/views/student/PracticeResultView.vue'),
    meta: { requiresAuth: true, requiresStudent: true, title: '练习结果' }
  },
  {
    path: '/teacher',
    name: 'TeacherDashboard',
    component: () => import('@/views/teacher/DashboardView.vue'),
    meta: { requiresAuth: true, requiresTeacher: true, title: '教师中心' }
  },
  {
    path: '/teacher/lessons',
    name: 'TeacherLessons',
    component: () => import('@/views/teacher/LessonsView.vue'),
    meta: { requiresAuth: true, requiresTeacher: true, title: '教案管理' }
  },
  {
    path: '/teacher/students',
    name: 'TeacherStudents',
    component: () => import('@/views/teacher/StudentsView.vue'),
    meta: { requiresAuth: true, requiresTeacher: true, title: '学生管理' }
  },
  {
    path: '/teacher/ai-planning',
    name: 'TeacherAIPlanning',
    component: () => import('@/views/teacher/AIPlanningView.vue'),
    meta: { requiresAuth: true, requiresTeacher: true, title: 'AI 备课' }
  },
  {
    path: '/teacher/reports',
    name: 'TeacherReports',
    component: () => import('@/views/teacher/StudentReportsView.vue'),
    meta: { requiresAuth: true, requiresTeacher: true, title: '学生报告' }
  },
  {
    path: '/teacher/reports/students/:studentId',
    name: 'TeacherStudentReports',
    component: () => import('@/views/teacher/StudentReportDetailView.vue'),
    meta: { requiresAuth: true, requiresTeacher: true, title: '学生报告详情' }
  },
  {
    path: '/teacher/reports/students/:studentId/reports/:reportId',
    name: 'TeacherStudentReport',
    component: () => import('@/views/teacher/StudentReportDetailView.vue'),
    meta: { requiresAuth: true, requiresTeacher: true, title: '学生报告详情' }
  },
  {
    path: '/teacher/reports/class-overview',
    name: 'ClassOverview',
    component: () => import('@/views/teacher/ClassOverviewView.vue'),
    meta: { requiresAuth: true, requiresTeacher: true, title: '班级学习状况' }
  },
  {
    path: '/teacher/question-banks',
    name: 'question-bank-list',
    component: () => import('@/views/teacher/QuestionBankListView.vue'),
    meta: { requiresAuth: true, requiresTeacher: true, title: '题库管理' }
  },
  {
    path: '/teacher/question-banks/:bankId',
    name: 'question-bank-detail',
    component: () => import('@/views/teacher/QuestionBankDetailView.vue'),
    meta: { requiresAuth: true, requiresTeacher: true, title: '题库详情' }
  },
  {
    path: '/teacher/question-banks/:bankId/questions/new',
    name: 'question-create',
    component: () => import('@/views/teacher/QuestionEditorView.vue'),
    meta: { requiresAuth: true, requiresTeacher: true, title: '新建题目' }
  },
  {
    path: '/teacher/questions/:questionId',
    name: 'question-edit',
    component: () => import('@/views/teacher/QuestionEditorView.vue'),
    meta: { requiresAuth: true, requiresTeacher: true, title: '编辑题目' }
  },
  {
    path: '/teacher/lesson-export',
    name: 'LessonExport',
    component: () => import('@/views/teacher/LessonExportView.vue'),
    meta: { requiresAuth: true, requiresTeacher: true, title: '教案导出' }
  },
  {
    path: '/teacher/template-library',
    name: 'TemplateLibrary',
    component: () => import('@/views/teacher/TemplateLibraryView.vue'),
    meta: { requiresAuth: true, requiresTeacher: true, title: '模板库' }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFoundView.vue'),
    meta: { title: '页面不存在' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

/**
 * 全局前置守卫
 * 检查认证状态和角色权限
 */
router.beforeEach(async (to, from, next) => {
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - AI英语教学系统`
  }

  const authStore = useAuthStore()
  const requiresAuth = to.meta.requiresAuth !== false
  const requiresTeacher = to.meta.requiresTeacher === true
  const requiresStudent = to.meta.requiresStudent === true

  // 不需要认证的页面直接放行
  if (!requiresAuth) {
    // 如果已登录，访问登录页时跳转到首页
    if (to.path === '/login' || to.path === '/register') {
      if (authStore.isAuthenticated) {
        // 根据角色跳转
        if (authStore.isStudent) {
          next('/student')
        } else if (authStore.isTeacher) {
          next('/teacher')
        } else {
          next('/')
        }
        return
      }
    }
    next()
    return
  }

  // 需要认证的页面
  // 首先检查 Pinia store 的认证状态
  let isAuthenticated = authStore.isAuthenticated
  let isTeacher = authStore.isTeacher
  let isStudent = authStore.isStudent
  let isAdmin = authStore.isAdmin

  // 调试：初始状态
  console.log('[Router] Initial auth state:', {
    path: to.path,
    isAuthenticated,
    isTeacher,
    isStudent,
    isAdmin,
    user: authStore.user,
    accessToken: authStore.accessToken
  })

  // 如果 store 未完全初始化，检查 localStorage 作为回退（支持 E2E 测试和应用刷新）
  if (!isAuthenticated || (!isTeacher && !isStudent && !isAdmin)) {
    // 添加重试机制，延迟检查 localStorage（解决 E2E 测试时序问题）
    let retryCount = 0
    const maxRetries = 10

    const checkLocalStorage = () => {
      try {
        const token = localStorage.getItem('access_token')
        const userStr = localStorage.getItem('user')
        console.log('[Router] Fallback check:', { token: !!token, userStr: !!userStr, retryCount })

        if (token && userStr) {
          const user = JSON.parse(userStr)
          // 有 token 和用户数据，视为已认证
          isAuthenticated = true
          // 从用户数据确定角色
          isTeacher = user.role === 'teacher'
          isStudent = user.role === 'student'
          isAdmin = user.role === 'admin'
          console.log('[Router] Parsed from localStorage:', { isAuthenticated, isTeacher, isStudent, isAdmin, user })
          return true
        }

        // 如果没有数据且还有重试次数，等待后重试
        if (retryCount < maxRetries) {
          retryCount++
          setTimeout(checkLocalStorage, 200)
          return false
        }

        return false
      } catch (e) {
        // localStorage 可能不可用或数据无效
        console.error('[Router] Failed to read from localStorage:', e)
        return false
      }
    }

    // 立即检查一次
    checkLocalStorage()
  }

  // 调试日志（仅开发环境）
  if (import.meta.env.DEV) {
    console.log('[Router] Final auth check:', {
      path: to.path,
      isAuthenticated,
      isTeacher,
      isStudent,
      isAdmin,
      requiresAuth,
      requiresTeacher,
      requiresStudent
    })
  }

  if (!isAuthenticated) {
    console.log('[Router] Not authenticated, redirecting to login')
    next('/login')
    return
  }

  // 角色权限检查
  if (requiresTeacher && !isTeacher && !isAdmin) {
    console.log('[Router] Not teacher, redirecting to home')
    next('/')
    return
  }

  if (requiresStudent && !isStudent && !isAdmin) {
    console.log('[Router] Not student, redirecting to home')
    next('/')
    return
  }

  console.log('[Router] Auth check passed, proceeding to:', to.path)

  next()
})

export default router
