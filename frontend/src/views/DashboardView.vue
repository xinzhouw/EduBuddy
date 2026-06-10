<template>
  <div class="space-y-6">

    <!-- 欢迎横幅 -->
    <div class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white shadow-lg">
      <div class="absolute -top-10 -right-10 w-48 h-48 bg-white/10 rounded-full"></div>
      <div class="absolute -bottom-8 -right-24 w-64 h-64 bg-white/5 rounded-full"></div>
      <div class="absolute top-4 right-32 w-16 h-16 bg-white/10 rounded-full"></div>
      <div class="relative p-6 flex items-center justify-between">
        <div>
          <p class="text-blue-200 text-sm font-medium mb-1">{{ dateStr }}</p>
          <h1 class="text-2xl font-bold">{{ greeting }}，{{ authStore.user?.nickname || '同学' }} 👋</h1>
          <p class="text-blue-100 mt-1.5 text-sm">{{ motivationText }}</p>
        </div>
        <div v-if="stats.streak_days > 0" class="text-center bg-white/15 backdrop-blur-sm rounded-2xl px-5 py-4 border border-white/20">
          <p class="text-4xl font-black leading-none">{{ stats.streak_days }}</p>
          <p class="text-blue-200 text-xs mt-1 font-medium">🔥 连续打卡</p>
        </div>
        <div v-else class="text-center bg-white/15 backdrop-blur-sm rounded-2xl px-5 py-4 border border-white/20">
          <p class="text-4xl">📚</p>
          <p class="text-blue-200 text-xs mt-1 font-medium">开始学习</p>
        </div>
      </div>
    </div>

    <!-- 每日学习建议卡片（仅学生角色显示） -->
    <div
      v-if="authStore.user?.role !== 'teacher' && authStore.user?.role !== 'parent' && !adviceDismissed && adviceList.length > 0"
      class="relative overflow-hidden rounded-2xl border shadow-sm"
      :class="adviceTypeStyle(adviceList[adviceIndex]).card"
    >
      <!-- 关闭按钮 -->
      <button
        @click="adviceDismissed = true"
        class="absolute top-3 right-3 w-7 h-7 rounded-full bg-black/10 hover:bg-black/20 flex items-center justify-center text-sm transition-colors z-10"
      >✕</button>

      <div class="p-5">
        <div class="flex items-start gap-3 mb-3">
          <span class="text-2xl shrink-0">{{ adviceList[adviceIndex].icon }}</span>
          <div class="flex-1 min-w-0">
            <p class="font-bold text-base" :class="adviceTypeStyle(adviceList[adviceIndex]).title">
              {{ adviceList[adviceIndex].title }}
            </p>
            <p class="text-sm mt-1" :class="adviceTypeStyle(adviceList[adviceIndex]).body">
              {{ adviceList[adviceIndex].content }}
            </p>
          </div>
        </div>

        <!-- 理论依据（可折叠） -->
        <div v-if="adviceList[adviceIndex].theory_basis" class="mb-3">
          <button
            @click="theoryExpanded = !theoryExpanded"
            class="text-xs flex items-center gap-1 opacity-70 hover:opacity-100 transition-opacity"
            :class="adviceTypeStyle(adviceList[adviceIndex]).title"
          >
            📖 理论依据 {{ theoryExpanded ? '▲' : '▼' }}
          </button>
          <p v-if="theoryExpanded" class="text-xs mt-1.5 opacity-70 leading-relaxed" :class="adviceTypeStyle(adviceList[adviceIndex]).body">
            {{ adviceList[adviceIndex].theory_basis }}
          </p>
        </div>

        <div class="flex items-center justify-between">
          <!-- 行动按钮 -->
          <RouterLink
            v-if="adviceList[adviceIndex].action"
            :to="adviceList[adviceIndex].action.route"
            @click="handleAdviceAction(adviceList[adviceIndex])"
            class="text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors no-underline"
            :class="adviceTypeStyle(adviceList[adviceIndex]).btn"
          >
            {{ adviceList[adviceIndex].action.label }} →
          </RouterLink>
          <span v-else></span>

          <!-- 翻页指示器 -->
          <div class="flex items-center gap-2">
            <button @click="prevAdvice" :disabled="adviceIndex === 0" class="text-sm disabled:opacity-30 hover:opacity-70 transition-opacity">‹</button>
            <span class="text-xs opacity-60">{{ adviceIndex + 1 }} / {{ adviceList.length }}</span>
            <button @click="nextAdvice" :disabled="adviceIndex >= adviceList.length - 1" class="text-sm disabled:opacity-30 hover:opacity-70 transition-opacity">›</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-3 gap-4">
      <div class="stat-card group">
        <div class="flex items-center justify-between mb-3">
          <div class="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center group-hover:bg-blue-100 transition-colors">
            <span class="text-xl">⏱️</span>
          </div>
          <span class="text-xs text-gray-400 font-medium">今日</span>
        </div>
        <p class="text-3xl font-black text-blue-600">{{ stats.today_study_minutes }}<span class="text-base font-medium text-gray-400 ml-1">分钟</span></p>
        <p class="text-gray-500 text-sm mt-1">学习时长</p>
        <div class="mt-3 h-1 bg-blue-50 rounded-full overflow-hidden">
          <div class="h-full bg-gradient-to-r from-blue-400 to-blue-600 rounded-full transition-all duration-700"
            :style="{ width: Math.min((stats.today_study_minutes / 120) * 100, 100) + '%' }"></div>
        </div>
      </div>

      <RouterLink to="/wrong-book?due=true" class="stat-card group cursor-pointer hover:-translate-y-0.5 transition-transform">
        <div class="flex items-center justify-between mb-3">
          <div class="w-10 h-10 bg-amber-50 rounded-xl flex items-center justify-center group-hover:bg-amber-100 transition-colors">
            <span class="text-xl">📋</span>
          </div>
          <span class="text-xs text-amber-500 font-medium bg-amber-50 px-2 py-0.5 rounded-full">待复习</span>
        </div>
        <p class="text-3xl font-black text-amber-500">{{ stats.wrong_book_count }}<span class="text-base font-medium text-gray-400 ml-1">道</span></p>
        <p class="text-gray-500 text-sm mt-1">错题待复习</p>
        <p class="mt-3 text-xs text-amber-400 font-medium">点击开始复习 →</p>
      </RouterLink>

      <RouterLink to="/plan" class="stat-card group cursor-pointer hover:-translate-y-0.5 transition-transform">
        <div class="flex items-center justify-between mb-3">
          <div class="w-10 h-10 bg-green-50 rounded-xl flex items-center justify-center group-hover:bg-green-100 transition-colors">
            <span class="text-xl">✅</span>
          </div>
          <span class="text-xs text-green-500 font-medium bg-green-50 px-2 py-0.5 rounded-full">今日</span>
        </div>
        <p class="text-3xl font-black text-green-500">{{ todayDone }}<span class="text-base font-medium text-gray-400 ml-1">/ {{ todayTotal }}</span></p>
        <p class="text-gray-500 text-sm mt-1">任务完成</p>
        <div class="mt-3 h-1 bg-green-50 rounded-full overflow-hidden">
          <div class="h-full bg-gradient-to-r from-green-400 to-emerald-500 rounded-full transition-all duration-700"
            :style="{ width: todayTotal > 0 ? (todayDone / todayTotal) * 100 + '%' : '0%' }"></div>
        </div>
      </RouterLink>
    </div>

    <!-- 主内容区 -->
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-6">
      <!-- 今日任务（占3列） -->
      <div class="lg:col-span-3 card">
        <div class="flex items-center justify-between mb-5">
          <h3 class="font-bold text-gray-800 flex items-center gap-2">
            <span class="w-1 h-5 bg-gradient-to-b from-blue-500 to-indigo-500 rounded-full inline-block"></span>
            今日学习任务
          </h3>
          <RouterLink to="/plan" class="text-xs text-blue-500 hover:text-blue-700 font-medium transition-colors">查看全部 →</RouterLink>
        </div>

        <div v-if="todayTasks.length === 0" class="flex flex-col items-center justify-center py-10">
          <div class="w-16 h-16 bg-gray-50 rounded-2xl flex items-center justify-center mb-3">
            <span class="text-3xl">📅</span>
          </div>
          <p class="text-gray-400 text-sm">暂无学习计划</p>
          <RouterLink to="/plan" class="mt-2 text-blue-500 text-sm hover:underline font-medium">去制定计划 →</RouterLink>
        </div>

        <div v-else class="space-y-2.5">
          <div
            v-for="task in todayTasks"
            :key="task.id"
            class="flex items-center gap-3 p-3.5 rounded-xl transition-colors"
            :class="task.is_done ? 'bg-green-50 border border-green-100' : 'bg-gray-50 border border-gray-100 hover:bg-blue-50 hover:border-blue-100'"
          >
            <div class="w-6 h-6 rounded-full flex items-center justify-center shrink-0"
              :class="task.is_done ? 'bg-green-500' : 'bg-white border-2 border-gray-300'">
              <svg v-if="task.is_done" class="w-3.5 h-3.5 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-semibold text-gray-700 truncate" :class="{ 'line-through text-gray-400': task.is_done }">
                {{ task.subject }} · {{ task.topic }}
              </p>
              <p class="text-xs text-gray-400 mt-0.5">{{ task.duration_minutes }} 分钟 · {{ taskTypeLabel(task.task_type) }}</p>
            </div>
            <span class="text-xs px-2 py-1 rounded-lg font-medium"
              :class="task.is_done ? 'bg-green-100 text-green-600' : 'bg-blue-50 text-blue-500'">
              {{ task.is_done ? '已完成' : '进行中' }}
            </span>
          </div>
        </div>
      </div>

      <!-- 快捷入口（占2列） -->
      <div class="lg:col-span-2 card">
        <div class="flex items-center gap-2 mb-5">
          <span class="w-1 h-5 bg-gradient-to-b from-purple-500 to-pink-500 rounded-full inline-block"></span>
          <h3 class="font-bold text-gray-800">快速开始</h3>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <RouterLink
            v-for="item in quickLinks"
            :key="item.path"
            :to="item.path"
            class="quick-link-card group"
          >
            <div class="w-12 h-12 rounded-2xl flex items-center justify-center mb-3 transition-transform group-hover:scale-110"
              :class="item.bgColor">
              <span class="text-2xl">{{ item.icon }}</span>
            </div>
            <span class="text-sm font-semibold text-gray-700 group-hover:text-gray-900">{{ item.label }}</span>
            <span class="text-xs text-gray-400 mt-0.5">{{ item.desc }}</span>
          </RouterLink>
        </div>
      </div>
    </div>

    <!-- 学科分布 -->
    <div class="card">
      <div class="flex items-center gap-2 mb-5">
        <span class="w-1 h-5 bg-gradient-to-b from-green-500 to-teal-500 rounded-full inline-block"></span>
        <h3 class="font-bold text-gray-800">学科分布</h3>
        <span class="text-xs text-gray-400 ml-1">（基于错题统计）</span>
      </div>
      <div class="grid grid-cols-3 sm:grid-cols-5 lg:grid-cols-9 gap-3">
        <div v-for="sub in subjects" :key="sub.name" class="flex flex-col items-center gap-1.5 group cursor-pointer">
          <div class="w-10 h-10 rounded-xl flex items-center justify-center text-lg transition-transform group-hover:scale-110"
            :class="sub.color">{{ sub.icon }}</div>
          <span class="text-xs text-gray-500 font-medium">{{ sub.name }}</span>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { statsApi } from '@/api/docs'
import { planApi } from '@/api/plan'
import { adviceApi } from '@/api/advice'

const authStore = useAuthStore()
const router = useRouter()

const stats = ref<any>({ today_study_minutes: 0, wrong_book_count: 0, streak_days: 0 })
const todayTasks = ref<any[]>([])

// ── 每日建议 ──────────────────────────────────────────────────────────────────
const adviceList = ref<any[]>([])
const adviceId = ref<number | null>(null)
const adviceIndex = ref(0)
const adviceDismissed = ref(false)
const theoryExpanded = ref(false)

function adviceTypeStyle(item: any) {
  const type = item?.type || 'general'
  const map: Record<string, { card: string; title: string; body: string; btn: string }> = {
    review_reminder: {
      card: 'bg-amber-50 border-amber-200',
      title: 'text-amber-800',
      body: 'text-amber-700',
      btn: 'bg-amber-500 text-white hover:bg-amber-600',
    },
    practice_suggestion: {
      card: 'bg-blue-50 border-blue-200',
      title: 'text-blue-800',
      body: 'text-blue-700',
      btn: 'bg-blue-500 text-white hover:bg-blue-600',
    },
    plan_adjustment: {
      card: 'bg-orange-50 border-orange-200',
      title: 'text-orange-800',
      body: 'text-orange-700',
      btn: 'bg-orange-500 text-white hover:bg-orange-600',
    },
    achievement: {
      card: 'bg-green-50 border-green-200',
      title: 'text-green-800',
      body: 'text-green-700',
      btn: 'bg-green-500 text-white hover:bg-green-600',
    },
    general: {
      card: 'bg-indigo-50 border-indigo-200',
      title: 'text-indigo-800',
      body: 'text-indigo-700',
      btn: 'bg-indigo-500 text-white hover:bg-indigo-600',
    },
  }
  return map[type] || map.general
}

function prevAdvice() {
  if (adviceIndex.value > 0) {
    adviceIndex.value--
    theoryExpanded.value = false
  }
}

function nextAdvice() {
  if (adviceIndex.value < adviceList.value.length - 1) {
    adviceIndex.value++
    theoryExpanded.value = false
  }
}

async function handleAdviceAction(item: any) {
  // 记录用户点击了行动按钮
  if (adviceId.value && item.id) {
    try {
      await adviceApi.recordAction(adviceId.value, item.id)
    } catch {}
  }
}

// ── 服务器时间 ─────────────────────────────────────────────────────────────────
interface ServerTime {
  hour: number
  month: number
  day: number
  weekday: number
}
const serverTime = ref<ServerTime | null>(null)

const timeParts = computed<ServerTime>(() => {
  if (serverTime.value) return serverTime.value
  const now = new Date()
  return {
    hour: now.getHours(),
    month: now.getMonth() + 1,
    day: now.getDate(),
    weekday: now.getDay(),
  }
})

const greeting = computed(() => {
  const h = timeParts.value.hour
  if (h < 6) return '深夜了'
  if (h < 12) return '早上好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})

const dateStr = computed(() => {
  const { month, day, weekday } = timeParts.value
  const days = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return `${month}月${day}日 ${days[weekday]}`
})

const motivationText = computed(() => {
  const texts = [
    '坚持学习，每天进步一点点！',
    '知识是改变命运的力量，加油！',
    '今日努力，明日更好的自己！',
    '专注当下，学习使人进步！',
    '好好学习，天天向上！',
  ]
  return texts[timeParts.value.day % texts.length]
})

const todayDone = computed(() => todayTasks.value.filter((t: any) => t.is_done).length)
const todayTotal = computed(() => todayTasks.value.length)

const quickLinks = [
  { path: '/ai', icon: '🤖', label: 'AI 问答', desc: '解题助手', bgColor: 'bg-blue-50' },
  { path: '/quiz', icon: '📚', label: '开始练习', desc: '刷题训练', bgColor: 'bg-purple-50' },
  { path: '/wrong-book', icon: '🔁', label: '错题复习', desc: '艾宾浩斯', bgColor: 'bg-amber-50' },
  { path: '/notes', icon: '📝', label: '新建笔记', desc: '知识整理', bgColor: 'bg-green-50' },
]

const subjects = [
  { name: '数学', icon: '🔢', color: 'bg-blue-50' },
  { name: '物理', icon: '⚡', color: 'bg-purple-50' },
  { name: '化学', icon: '🧪', color: 'bg-orange-50' },
  { name: '生物', icon: '🧬', color: 'bg-green-50' },
  { name: '语文', icon: '📖', color: 'bg-red-50' },
  { name: '英语', icon: '🌍', color: 'bg-cyan-50' },
  { name: '历史', icon: '🏛️', color: 'bg-amber-50' },
  { name: '地理', icon: '🗺️', color: 'bg-teal-50' },
  { name: '政治', icon: '⚖️', color: 'bg-rose-50' },
]

function taskTypeLabel(type: string) {
  return ({ study: '学习', practice: '练习', review: '复习' } as any)[type] || type
}

onMounted(async () => {
  try {
    const res: any = await statsApi.getOverview()
    stats.value = res.data
    const st = res.data?.server_time
    if (st && typeof st.hour === 'number') {
      serverTime.value = { hour: st.hour, month: st.month, day: st.day, weekday: st.weekday }
    }
  } catch {}

  try {
    const res: any = await planApi.getToday()
    todayTasks.value = res.data || []
  } catch {}

  // 仅学生角色加载每日建议
  const role = authStore.user?.role
  if (!role || role === 'student') {
    try {
      const res: any = await adviceApi.getToday()
      adviceId.value = res.data?.advice_id ?? null
      adviceList.value = res.data?.advices || []
    } catch {}
  }
})
</script>

<style scoped>
@reference "../style.css";
.stat-card {
  @apply bg-white rounded-2xl border border-gray-100 shadow-sm p-5 hover:shadow-md transition-shadow;
}
.quick-link-card {
  @apply flex flex-col items-center text-center p-4 rounded-2xl border-2 border-gray-100 hover:border-blue-200 hover:bg-blue-50/50 transition-all cursor-pointer no-underline;
}
.card {
  @apply bg-white rounded-2xl border border-gray-100 shadow-sm p-6;
}
</style>
