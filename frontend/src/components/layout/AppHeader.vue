<template>
  <header class="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shrink-0">
    <div class="flex items-center gap-2 text-gray-600">
      <span class="text-lg font-semibold text-gray-800">{{ pageTitle }}</span>
    </div>
    <div class="flex items-center gap-3">
      <!-- 今日待复习提示 -->
      <RouterLink v-if="todayDue > 0" to="/wrong-book?due=true"
        class="flex items-center gap-1.5 px-3 py-1.5 bg-amber-50 text-amber-700 rounded-full text-sm hover:bg-amber-100 transition-colors">
        <span>⏰</span>
        <span>今日待复习 {{ todayDue }} 道</span>
      </RouterLink>
      <!-- 连续打卡 -->
      <span v-if="streakDays > 0" class="text-sm text-gray-500">🔥 连续 {{ streakDays }} 天</span>
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
