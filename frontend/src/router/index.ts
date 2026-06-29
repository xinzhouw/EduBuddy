import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// 角色权限说明：
// - student（学生）：可访问学习类功能（AI 问答、作业批改、笔记、练习题、错题本、学习计划、文档、读书郎、统计）
// - teacher（教师）/ parent（家长）：可访问监督类功能（学生监督、统计）
// - admin（管理员）：可访问管理后台
// 未在 meta.roles 中限制的页面（如个人资料、统计）对所有已登录角色开放。
const STUDENT_ONLY = ['student']
const OBSERVER_ONLY = ['teacher', 'parent']
const ADMIN_ONLY = ['admin']

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: () => import('@/views/auth/LoginView.vue'), meta: { public: true } },
    { path: '/register', component: () => import('@/views/auth/RegisterView.vue'), meta: { public: true } },
    { path: '/forgot-password', component: () => import('@/views/auth/ForgotPasswordView.vue'), meta: { public: true } },
    { path: '/', component: () => import('@/views/DashboardView.vue'), meta: { roles: STUDENT_ONLY } },
    { path: '/ai', component: () => import('@/views/ai/AIChatView.vue'), meta: { roles: STUDENT_ONLY } },
    { path: '/notes', component: () => import('@/views/notes/NotesListView.vue'), meta: { roles: STUDENT_ONLY } },
    { path: '/notes/:id/edit', component: () => import('@/views/notes/NoteEditView.vue'), meta: { roles: STUDENT_ONLY } },
    { path: '/quiz', component: () => import('@/views/quiz/QuizSetupView.vue'), meta: { roles: STUDENT_ONLY } },
    { path: '/quiz/session', component: () => import('@/views/quiz/QuizSessionView.vue'), meta: { roles: STUDENT_ONLY } },
    { path: '/wrong-book', component: () => import('@/views/wrongBook/WrongBookView.vue'), meta: { roles: STUDENT_ONLY } },
    { path: '/wrong-book/:id', component: () => import('@/views/wrongBook/WrongDetailView.vue'), meta: { roles: STUDENT_ONLY } },
    { path: '/plan', component: () => import('@/views/plan/StudyPlanView.vue'), meta: { roles: STUDENT_ONLY } },
    { path: '/docs', component: () => import('@/views/docs/DocsView.vue'), meta: { roles: STUDENT_ONLY } },
    { path: '/stats', component: () => import('@/views/stats/StatsView.vue') },
    { path: '/homework', component: () => import('@/views/homework/HomeworkGradingView.vue'), meta: { roles: STUDENT_ONLY } },
    { path: '/reading-buddy', component: () => import('@/views/readingBuddy/ReadingBuddyView.vue'), meta: { roles: STUDENT_ONLY } },
    { path: '/monitor', component: () => import('@/views/monitor/MonitorView.vue'), meta: { roles: OBSERVER_ONLY } },
    { path: '/monitor/students/:id', component: () => import('@/views/monitor/MonitorStudentView.vue'), meta: { roles: OBSERVER_ONLY } },
    {
      path: '/admin',
      component: () => import('@/views/admin/AdminLayout.vue'),
      meta: { roles: ADMIN_ONLY },
      children: [
        { path: 'dashboard', component: () => import('@/views/admin/AdminDashboard.vue'), meta: { title: '仪表板' } },
        { path: 'users', component: () => import('@/views/admin/UserManagement.vue'), meta: { title: '用户管理' } },
        { path: 'users/:id', component: () => import('@/views/admin/UserDetail.vue'), meta: { title: '用户详情' } },
        { path: 'audit-logs', component: () => import('@/views/admin/AuditLogs.vue'), meta: { title: '审计日志' } },
        { path: '', redirect: 'dashboard' }
      ]
    },
    { path: '/profile', component: () => import('@/views/profile/ProfileView.vue') },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

// 路由守卫：登录态校验 + 基于角色的权限控制
router.beforeEach((to) => {
  const authStore = useAuthStore()

  // 1. 未登录访问受保护页面 → 跳转登录
  if (!to.meta.public && !authStore.isAuthenticated) {
    return '/login'
  }

  // 2. 已登录访问登录/注册页 → 根据角色跳转到对应的默认页面
  if (to.meta.public && authStore.isAuthenticated) {
    const role = authStore.user?.role || 'student'
    return role === 'admin' ? '/admin/dashboard' : '/'
  }

  // 3. 基于角色的权限控制：当前角色无权访问该页面 → 根据角色跳转到对应的默认页面
  const allowedRoles = to.meta.roles as string[] | undefined
  if (allowedRoles && authStore.isAuthenticated) {
    const role = authStore.user?.role || 'student'
    if (!allowedRoles.includes(role)) {
      return role === 'admin' ? '/admin/dashboard' : '/'
    }
  }
})

export default router
