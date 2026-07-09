<template>
  <aside class="w-64 bg-gradient-to-b from-slate-900 to-slate-800 flex flex-col h-full shrink-0 shadow-xl hidden md:flex">
    <!-- Logo -->
    <div class="h-16 flex items-center px-6 border-b border-slate-700/50">
      <div class="flex items-center gap-2.5">
        <svg class="w-8 h-8" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
          <defs>
            <linearGradient id="logoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style="stop-color:#60a5fa;stop-opacity:1" />
              <stop offset="100%" style="stop-color:#4f46e5;stop-opacity:1" />
            </linearGradient>
          </defs>
          <circle cx="100" cy="100" r="95" fill="url(#logoGrad)"/>
          <g transform="translate(100, 100)">
            <path d="M -12 -10 Q -22 -3 -22 10 Q -22 23 -12 27 L 12 27 Q 22 23 22 10 Q 22 -3 12 -10 Q 0 -17 -12 -10" fill="white" opacity="0.95"/>
            <circle cx="0" cy="0" r="8" fill="none" stroke="#fbbf24" stroke-width="1.5" opacity="0.8"/>
            <rect x="-10" y="27" width="20" height="5" rx="1.5" fill="white" opacity="0.9"/>
            <rect x="-8" y="32" width="16" height="3" rx="0.5" fill="white" opacity="0.8"/>
            <circle cx="-4" cy="37" r="1.5" fill="white" opacity="0.9"/>
            <circle cx="4" cy="37" r="1.5" fill="white" opacity="0.9"/>
            <g stroke="#fbbf24" stroke-width="1.2" stroke-linecap="round" opacity="0.6">
              <line x1="0" y1="-28" x2="0" y2="-33"/>
              <line x1="20" y1="-20" x2="24" y2="-24"/>
              <line x1="28" y1="0" x2="33" y2="0"/>
              <line x1="20" y1="20" x2="24" y2="24"/>
              <line x1="-20" y1="20" x2="-24" y2="24"/>
              <line x1="-28" y1="0" x2="-33" y2="0"/>
              <line x1="-20" y1="-20" x2="-24" y2="-24"/>
            </g>
          </g>
          <circle cx="100" cy="100" r="92" fill="none" stroke="white" stroke-width="1" opacity="0.2"/>
        </svg>
        <span class="text-lg font-bold text-white tracking-wide">EduBuddy</span>
      </div>
    </div>

    <!-- Navigation menu -->
    <nav class="flex-1 px-3 py-5 space-y-0.5 overflow-y-auto">
      <RouterLink
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ 'nav-item-active': isActive(item.path) }"
      >
        <span class="text-base w-5 text-center">{{ item.icon }}</span>
        <span class="text-sm font-medium">{{ item.label }}</span>
        <span v-if="item.badge" class="ml-auto bg-red-500 text-white text-xs rounded-full px-1.5 py-0.5 min-w-[18px] text-center leading-tight">
          {{ item.badge }}
        </span>
      </RouterLink>
    </nav>

    <!-- Bottom user info (click to enter profile) -->
    <div class="border-t border-slate-700/50 p-3">
      <RouterLink
        to="/profile"
        class="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-slate-700/40 transition-colors group no-underline"
        :class="{ 'bg-slate-700/40': isActive('/profile') }"
      >
        <div class="w-9 h-9 bg-gradient-to-br from-blue-400 to-indigo-500 rounded-full flex items-center justify-center text-white font-bold text-sm shadow-md shrink-0">
          {{ authStore.user?.nickname?.[0]?.toUpperCase() || 'U' }}
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-semibold text-slate-200 truncate">{{ authStore.user?.nickname || $t('auth.student') }}</p>
          <p class="text-xs text-slate-400">{{ authStore.user?.grade || $t('auth.student') }} · {{ $t('navigation.profile') }}</p>
        </div>
        <button @click.prevent.stop="logout"
          class="text-slate-500 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
          :title="$t('auth.logout')">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
        </button>
      </RouterLink>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// Generate navigation menu dynamically based on user role
const navItems = computed<{ path: string; icon: string; label: string; badge?: string | number }[]>(() => {
  const role = authStore.user?.role || 'student'
  const studentItems = [
    { path: '/', icon: '🏠', label: t('navigation.home') },
    { path: '/ai', icon: '🤖', label: t('navigation.ai_chat') },
    { path: '/homework', icon: '✍️', label: t('navigation.homework_grading') },
    { path: '/notes', icon: '📝', label: t('navigation.notes') },
    { path: '/quiz', icon: '📚', label: t('navigation.quiz') },
    { path: '/wrong-book', icon: '❌', label: t('navigation.wrong_book') },
    { path: '/plan', icon: '📅', label: t('navigation.study_plan') },
    { path: '/docs', icon: '📄', label: t('navigation.docs') },
    { path: '/reading-buddy', icon: '📖', label: t('navigation.reading_buddy') },
    { path: '/stats', icon: '📊', label: t('navigation.learning_stats') },
  ]
  const observerItems = [
    { path: '/monitor', icon: '👁️', label: t('navigation.monitor') },
    { path: '/stats', icon: '📊', label: t('navigation.my_stats') },
  ]
  const adminItems = [
    { path: '/admin/dashboard', icon: '📊', label: t('navigation.admin') },
    { path: '/admin/users', icon: '👥', label: t('navigation.user_management') },
    { path: '/admin/audit-logs', icon: '📋', label: t('navigation.audit_logs') },
  ]
  if (role === 'admin') {
    return adminItems
  }
  return (role === 'teacher' || role === 'parent') ? observerItems : studentItems
})

function isActive(path: string) {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

function logout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
@reference "../../style.css";
.nav-item {
  @apply flex items-center gap-3 px-3 py-2.5 rounded-xl text-slate-400 hover:bg-slate-700/50 hover:text-white transition-all duration-150 cursor-pointer no-underline;
}
.nav-item-active {
  @apply bg-gradient-to-r from-blue-600/80 to-indigo-600/80 text-white shadow-sm;
}
</style>
