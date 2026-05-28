<template>
  <aside class="w-60 bg-white border-r border-gray-200 flex flex-col h-full shrink-0">
    <!-- Logo -->
    <div class="h-16 flex items-center px-6 border-b border-gray-100">
      <span class="text-xl font-bold text-blue-600">📚 EduBuddy</span>
    </div>

    <!-- 导航菜单 -->
    <nav class="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
      <RouterLink
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ 'nav-item-active': isActive(item.path) }"
      >
        <span class="text-lg">{{ item.icon }}</span>
        <span class="text-sm font-medium">{{ item.label }}</span>
      </RouterLink>
    </nav>

    <!-- 底部设置 -->
    <div class="border-t border-gray-100 p-3">
      <div class="flex items-center gap-3 px-3 py-2 rounded-lg">
        <div class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-bold text-sm">
          {{ authStore.user?.nickname?.[0] || 'U' }}
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-gray-700 truncate">{{ authStore.user?.nickname }}</p>
          <p class="text-xs text-gray-500">{{ authStore.user?.grade }}</p>
        </div>
        <button @click="logout" class="text-gray-400 hover:text-red-500 transition-colors" title="退出登录">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const navItems = [
  { path: '/', icon: '🏠', label: '首页' },
  { path: '/ai', icon: '🤖', label: 'AI 问答' },
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
.nav-item {
  @apply flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-colors cursor-pointer no-underline;
}
.nav-item-active {
  @apply bg-blue-50 text-blue-700 font-semibold;
}
</style>
