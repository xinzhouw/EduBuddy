<template>
  <div class="space-y-6">
    <!-- 欢迎横幅 -->
    <div class="card bg-gradient-to-r from-blue-500 to-blue-600 text-white">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold">👋 {{ greeting }}，{{ authStore.user?.nickname }}！</h1>
          <p class="text-blue-100 mt-1">今天继续加油！</p>
        </div>
        <div v-if="stats.streak_days > 0" class="text-right">
          <p class="text-3xl font-bold">{{ stats.streak_days }} 🔥</p>
          <p class="text-blue-100 text-sm">连续学习天数</p>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="card text-center">
        <p class="text-3xl font-bold text-blue-600">{{ stats.today_study_minutes }}</p>
        <p class="text-gray-500 text-sm mt-1">今日学习（分钟）</p>
      </div>
      <RouterLink to="/wrong-book?due=true" class="card text-center hover:shadow-md transition-shadow cursor-pointer">
        <p class="text-3xl font-bold text-amber-500">{{ stats.wrong_book_count }}</p>
        <p class="text-gray-500 text-sm mt-1">错题待复习</p>
      </RouterLink>
      <RouterLink to="/plan" class="card text-center hover:shadow-md transition-shadow cursor-pointer">
        <p class="text-3xl font-bold text-green-500">{{ todayDone }}/{{ todayTotal }}</p>
        <p class="text-gray-500 text-sm mt-1">今日任务完成</p>
      </RouterLink>
    </div>

    <!-- 今日任务 + 快捷入口 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 今日任务 -->
      <div class="card">
        <h3 class="font-semibold text-gray-800 mb-4">📅 今日学习任务</h3>
        <div v-if="todayTasks.length === 0" class="text-center py-8 text-gray-400">
          <p>暂无学习计划</p>
          <RouterLink to="/plan" class="text-blue-500 text-sm hover:underline">去制定计划 →</RouterLink>
        </div>
        <div v-else class="space-y-3">
          <div v-for="task in todayTasks" :key="task.id" class="flex items-center gap-3 p-3 rounded-lg"
            :class="task.is_done ? 'bg-green-50' : 'bg-gray-50'">
            <span class="text-lg">{{ task.is_done ? '✅' : '⬜' }}</span>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-gray-700 truncate">{{ task.subject }} · {{ task.topic }}</p>
              <p class="text-xs text-gray-500">{{ task.duration_minutes }} 分钟 · {{ taskTypeLabel(task.task_type) }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 快捷入口 -->
      <div class="card">
        <h3 class="font-semibold text-gray-800 mb-4">⚡ 快速开始</h3>
        <div class="grid grid-cols-2 gap-3">
          <RouterLink v-for="item in quickLinks" :key="item.path" :to="item.path"
            class="flex flex-col items-center gap-2 p-4 rounded-xl border-2 border-gray-100 hover:border-blue-200 hover:bg-blue-50 transition-all cursor-pointer">
            <span class="text-3xl">{{ item.icon }}</span>
            <span class="text-sm font-medium text-gray-700">{{ item.label }}</span>
          </RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { statsApi } from '@/api/docs'
import { planApi } from '@/api/plan'

const authStore = useAuthStore()
const stats = ref<any>({ today_study_minutes: 0, wrong_book_count: 0, streak_days: 0 })
const todayTasks = ref<any[]>([])

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 12) return '早上好'
  if (h < 18) return '下午好'
  return '晚上好'
})

const todayDone = computed(() => todayTasks.value.filter((t: any) => t.is_done).length)
const todayTotal = computed(() => todayTasks.value.length)

const quickLinks = [
  { path: '/ai', icon: '🤖', label: 'AI 问答' },
  { path: '/quiz', icon: '📚', label: '开始练习' },
  { path: '/wrong-book', icon: '❌', label: '错题复习' },
  { path: '/notes', icon: '📝', label: '新建笔记' },
]

function taskTypeLabel(type: string) {
  return { study: '学习', practice: '练习', review: '复习' }[type] || type
}

onMounted(async () => {
  try {
    const res: any = await statsApi.getOverview()
    stats.value = res.data
  } catch {}
  try {
    const res: any = await planApi.getToday()
    todayTasks.value = res.data || []
  } catch {}
})
</script>
