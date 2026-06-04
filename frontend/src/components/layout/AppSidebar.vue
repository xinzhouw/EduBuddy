<template>
  <aside class="w-64 bg-gradient-to-b from-slate-900 to-slate-800 flex flex-col h-full shrink-0 shadow-xl">
    <!-- Logo -->
    <div class="h-16 flex items-center px-6 border-b border-slate-700/50">
      <div class="flex items-center gap-2.5">
        <div class="w-8 h-8 bg-gradient-to-br from-blue-400 to-indigo-500 rounded-lg flex items-center justify-center shadow-md">
          <span class="text-white text-sm font-bold">E</span>
        </div>
        <span class="text-lg font-bold text-white tracking-wide">EduBuddy</span>
      </div>
    </div>

    <!-- 导航菜单 -->
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

    <!-- 底部用户信息（点击进入个人资料） -->
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
          <p class="text-sm font-semibold text-slate-200 truncate">{{ authStore.user?.nickname || '同学' }}</p>
          <p class="text-xs text-slate-400">{{ authStore.user?.grade || '学生' }} · 个人资料</p>
        </div>
        <button @click.prevent.stop="logout"
          class="text-slate-500 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
          title="退出登录">
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
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const navItems: { path: string; icon: string; label: string; badge?: string | number }[] = [
  { path: '/', icon: '🏠', label: '首页' },
  { path: '/ai', icon: '🤖', label: 'AI 问答' },
  { path: '/homework', icon: '✍️', label: 'AI 批改作业' },
  { path: '/notes', icon: '📝', label: '笔记' },
  { path: '/quiz', icon: '📚', label: '练习题' },
  { path: '/wrong-book', icon: '❌', label: '错题本' },
  { path: '/plan', icon: '📅', label: '学习计划' },
  { path: '/docs', icon: '📄', label: '文档' },
  { path: '/stats', icon: '📊', label: '学习统计' },
]

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
