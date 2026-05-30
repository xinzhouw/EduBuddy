<template>
  <header class="h-16 bg-white/80 backdrop-blur-md border-b border-gray-100 flex items-center justify-between px-6 shrink-0 sticky top-0 z-10">
    <!-- 页面标题 -->
    <div class="flex items-center gap-3">
      <h1 class="text-lg font-bold text-gray-800">{{ pageTitle }}</h1>
    </div>

    <!-- 右侧工具栏 -->
    <div class="flex items-center gap-3">
      <!-- 今日待复习提示 -->
      <RouterLink
        v-if="todayDue > 0"
        to="/wrong-book?due=true"
        class="flex items-center gap-1.5 px-3 py-1.5 bg-amber-50 text-amber-700 border border-amber-200 rounded-full text-sm hover:bg-amber-100 hover:border-amber-300 transition-all shadow-sm"
      >
        <span>⏰</span>
        <span class="font-medium">{{ todayDue }} 道待复习</span>
      </RouterLink>

      <!-- 连续打卡 -->
      <div
        v-if="streakDays > 0"
        class="flex items-center gap-1.5 px-3 py-1.5 bg-orange-50 text-orange-600 border border-orange-200 rounded-full text-sm shadow-sm"
      >
        <span>🔥</span>
        <span class="font-medium">连续 {{ streakDays }} 天</span>
      </div>

      <!-- 分隔线 -->
      <div class="w-px h-5 bg-gray-200"></div>

      <!-- 搜索按钮（占位） -->
      <button class="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </button>

      <!-- 通知按钮（占位） -->
      <button class="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors relative">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
      </button>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { wrongBookApi } from '@/api/wrongBook'
import { statsApi } from '@/api/docs'

const route = useRoute()
const todayDue = ref(0)
const streakDays = ref(0)

const pageTitles: Record<string, string> = {
  '/': '首页',
  '/ai': 'AI 问答',
  '/notes': '我的笔记',
  '/quiz': '练习题',
  '/wrong-book': '错题本',
  '/plan': '学习计划',
  '/docs': '文档资料',
  '/stats': '学习统计',
}

const pageTitle = computed(() => {
  const path = route.path
  for (const [key, title] of Object.entries(pageTitles)) {
    if (key !== '/' && path.startsWith(key)) return title
  }
  return pageTitles[path] || 'EduBuddy'
})

onMounted(async () => {
  try {
    const res: any = await wrongBookApi.list({ due_review: true, size: 1 })
    todayDue.value = res.data.today_due_count || 0
  } catch {}
  try {
    const res: any = await statsApi.getOverview()
    streakDays.value = res.data.streak_days || 0
  } catch {}
})
</script>
