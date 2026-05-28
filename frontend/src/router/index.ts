import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: () => import('@/views/auth/LoginView.vue'), meta: { public: true } },
    { path: '/register', component: () => import('@/views/auth/RegisterView.vue'), meta: { public: true } },
    { path: '/', component: () => import('@/views/DashboardView.vue') },
    { path: '/ai', component: () => import('@/views/ai/AIChatView.vue') },
    { path: '/notes', component: () => import('@/views/notes/NotesListView.vue') },
    { path: '/notes/:id/edit', component: () => import('@/views/notes/NoteEditView.vue') },
    { path: '/quiz', component: () => import('@/views/quiz/QuizSetupView.vue') },
    { path: '/quiz/session', component: () => import('@/views/quiz/QuizSessionView.vue') },
    { path: '/wrong-book', component: () => import('@/views/wrongBook/WrongBookView.vue') },
    { path: '/wrong-book/:id', component: () => import('@/views/wrongBook/WrongDetailView.vue') },
    { path: '/plan', component: () => import('@/views/plan/StudyPlanView.vue') },
    { path: '/docs', component: () => import('@/views/docs/DocsView.vue') },
    { path: '/stats', component: () => import('@/views/stats/StatsView.vue') },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

// 路由守卫
router.beforeEach((to) => {
  const authStore = useAuthStore()
  if (!to.meta.public && !authStore.isAuthenticated) {
    return '/login'
  }
  if (to.meta.public && authStore.isAuthenticated) {
    return '/'
  }
})

export default router
