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
  if (!authStore.isAuthenticated) {
    next('/login')
    return
  }

  // 角色权限检查
  if (requiresTeacher && !authStore.isTeacher && !authStore.isAdmin) {
    next('/')
    return
  }

  if (requiresStudent && !authStore.isStudent && !authStore.isAdmin) {
    next('/')
    return
  }

  next()
})

export default router
