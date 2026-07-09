<template>
  <div class="space-y-6">

    <!-- Welcome banner -->
    <div class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white shadow-lg">
      <div class="absolute -top-10 -right-10 w-48 h-48 bg-white/10 rounded-full"></div>
      <div class="absolute -bottom-8 -right-24 w-64 h-64 bg-white/5 rounded-full"></div>
      <div class="absolute top-4 right-32 w-16 h-16 bg-white/10 rounded-full"></div>
      <div class="relative p-4 sm:p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div class="flex-1 min-w-0">
          <p class="text-blue-200 text-xs sm:text-sm font-medium mb-1">{{ dateStr }}</p>
          <h1 class="text-lg sm:text-2xl font-bold truncate">{{ greeting }}，{{ authStore.user?.nickname || $t('dashboard.student_suffix') }} 👋</h1>
          <p class="text-blue-100 mt-1 sm:mt-1.5 text-xs sm:text-sm line-clamp-2">{{ motivationText }}</p>
        </div>
        <div v-if="stats.streak_days > 0" class="text-center bg-white/15 backdrop-blur-sm rounded-2xl px-4 sm:px-5 py-3 sm:py-4 border border-white/20 shrink-0">
          <p class="text-3xl sm:text-4xl font-black leading-none">{{ stats.streak_days }}</p>
          <p class="text-blue-200 text-xs mt-1 font-medium">🔥 {{ $t('dashboard.streak_label') }}</p>
        </div>
        <div v-else class="text-center bg-white/15 backdrop-blur-sm rounded-2xl px-4 sm:px-5 py-3 sm:py-4 border border-white/20 shrink-0">
          <p class="text-3xl sm:text-4xl">📚</p>
          <p class="text-blue-200 text-xs mt-1 font-medium">{{ $t('dashboard.start_study') }}</p>
        </div>
      </div>
    </div>

    <!-- System info card - shows current AI model -->
    <div v-if="systemInfo.llm_model" class="card p-4 sm:p-5 bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-50 border border-purple-100">
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div class="flex items-start gap-4 flex-1">
          <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-blue-600 flex items-center justify-center text-white text-xl shrink-0">
            🤖
          </div>
          <div class="min-w-0 flex-1">
            <p class="text-xs text-gray-500 font-semibold uppercase tracking-wide">{{ $t('dashboard.ai_engine') }}</p>
            <p class="text-base sm:text-lg font-bold text-gray-800 mt-1">{{ systemInfo.llm_model_short }}</p>
            <p class="text-xs text-gray-600 mt-1.5 font-mono bg-white/60 px-2 py-1 rounded w-fit">
              {{ systemInfo.llm_model }}
            </p>
          </div>
        </div>
        <div class="text-right text-xs text-gray-600 sm:border-l sm:border-gray-200 sm:pl-4">
          <p class="font-medium">{{ systemInfo.llm_provider }}</p>
          <p class="mt-1.5 text-gray-400">EduBuddy v{{ systemInfo.app_version }}</p>
        </div>
      </div>
    </div>

    <!-- Daily study advice card (student role only) -->
    <div
      v-if="authStore.user?.role !== 'teacher' && authStore.user?.role !== 'parent' && !adviceDismissed && adviceList.length > 0"
      class="relative overflow-hidden rounded-2xl border shadow-sm"
      :class="adviceTypeStyle(adviceList[adviceIndex]).card"
    >
      <!-- Close button -->
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

        <!-- Theory basis (collapsible) -->
        <div v-if="adviceList[adviceIndex].theory_basis" class="mb-3">
          <button
            @click="theoryExpanded = !theoryExpanded"
            class="text-xs flex items-center gap-1 opacity-70 hover:opacity-100 transition-opacity"
            :class="adviceTypeStyle(adviceList[adviceIndex]).title"
          >
            📖 {{ $t('dashboard.theory_basis') }} {{ theoryExpanded ? '▲' : '▼' }}
          </button>
          <p v-if="theoryExpanded" class="text-xs mt-1.5 opacity-70 leading-relaxed" :class="adviceTypeStyle(adviceList[adviceIndex]).body">
            {{ adviceList[adviceIndex].theory_basis }}
          </p>
        </div>

        <div class="flex items-center justify-between">
          <!-- Action button -->
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

          <!-- Page indicator -->
          <div class="flex items-center gap-2">
            <button @click="prevAdvice" :disabled="adviceIndex === 0" class="text-sm disabled:opacity-30 hover:opacity-70 transition-opacity">‹</button>
            <span class="text-xs opacity-60">{{ adviceIndex + 1 }} / {{ adviceList.length }}</span>
            <button @click="nextAdvice" :disabled="adviceIndex >= adviceList.length - 1" class="text-sm disabled:opacity-30 hover:opacity-70 transition-opacity">›</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Stats cards -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
      <div class="stat-card group">
        <div class="flex items-center justify-between mb-3">
          <div class="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center group-hover:bg-blue-100 transition-colors">
            <span class="text-xl">⏱️</span>
          </div>
          <span class="text-xs text-gray-400 font-medium">{{ $t('dashboard.today_label') }}</span>
        </div>
        <p class="text-3xl font-black text-blue-600">{{ stats.today_study_minutes }}<span class="text-base font-medium text-gray-400 ml-1">{{ $t('dashboard.study_minutes') }}</span></p>
        <p class="text-gray-500 text-sm mt-1">{{ $t('dashboard.study_duration') }}</p>
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
          <span class="text-xs text-amber-500 font-medium bg-amber-50 px-2 py-0.5 rounded-full">{{ $t('dashboard.pending_review') }}</span>
        </div>
        <p class="text-3xl font-black text-amber-500">{{ stats.wrong_book_count }}<span class="text-base font-medium text-gray-400 ml-1">{{ $t('dashboard.wrong_count_unit') }}</span></p>
        <p class="text-gray-500 text-sm mt-1">{{ $t('dashboard.wrong_pending') }}</p>
        <p class="mt-3 text-xs text-amber-400 font-medium">{{ $t('dashboard.start_review') }}</p>
      </RouterLink>

      <RouterLink to="/plan" class="stat-card group cursor-pointer hover:-translate-y-0.5 transition-transform">
        <div class="flex items-center justify-between mb-3">
          <div class="w-10 h-10 bg-green-50 rounded-xl flex items-center justify-center group-hover:bg-green-100 transition-colors">
            <span class="text-xl">✅</span>
          </div>
          <span class="text-xs text-green-500 font-medium bg-green-50 px-2 py-0.5 rounded-full">{{ $t('dashboard.today_label') }}</span>
        </div>
        <p class="text-3xl font-black text-green-500">{{ todayDone }}<span class="text-base font-medium text-gray-400 ml-1">/ {{ todayTotal }}</span></p>
        <p class="text-gray-500 text-sm mt-1">{{ $t('dashboard.task_completed') }}</p>
        <div class="mt-3 h-1 bg-green-50 rounded-full overflow-hidden">
          <div class="h-full bg-gradient-to-r from-green-400 to-emerald-500 rounded-full transition-all duration-700"
            :style="{ width: todayTotal > 0 ? (todayDone / todayTotal) * 100 + '%' : '0%' }"></div>
        </div>
      </RouterLink>
    </div>

    <!-- Main content area -->
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-4 sm:gap-6">
      <!-- Today's tasks (3 columns) -->
      <div class="lg:col-span-3 card p-4 sm:p-5">
        <div class="flex items-center justify-between mb-5">
          <h3 class="font-bold text-gray-800 flex items-center gap-2">
            <span class="w-1 h-5 bg-gradient-to-b from-blue-500 to-indigo-500 rounded-full inline-block"></span>
            {{ $t('dashboard.today_tasks') }}
          </h3>
          <RouterLink to="/plan" class="text-xs text-blue-500 hover:text-blue-700 font-medium transition-colors">{{ $t('dashboard.view_all') }}</RouterLink>
        </div>

        <div v-if="todayTasks.length === 0" class="flex flex-col items-center justify-center py-10">
          <div class="w-16 h-16 bg-gray-50 rounded-2xl flex items-center justify-center mb-3">
            <span class="text-3xl">📅</span>
          </div>
          <p class="text-gray-400 text-sm">{{ $t('dashboard.no_plan') }}</p>
          <RouterLink to="/plan" class="mt-2 text-blue-500 text-sm hover:underline font-medium">{{ $t('dashboard.make_plan') }}</RouterLink>
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
              <p class="text-xs text-gray-400 mt-0.5">{{ task.duration_minutes }} {{ $t('dashboard.study_minutes') }} · {{ taskTypeLabel(task.task_type) }}</p>
            </div>
            <span class="text-xs px-2 py-1 rounded-lg font-medium"
              :class="task.is_done ? 'bg-green-100 text-green-600' : 'bg-blue-50 text-blue-500'">
              {{ task.is_done ? $t('dashboard.task_done') : $t('dashboard.task_in_progress') }}
            </span>
          </div>
        </div>
      </div>

      <!-- Quick links (2 columns) -->
      <div class="lg:col-span-2 card p-4 sm:p-5">
        <div class="flex items-center gap-2 mb-4 sm:mb-5">
          <span class="w-1 h-5 bg-gradient-to-b from-purple-500 to-pink-500 rounded-full inline-block"></span>
          <h3 class="font-bold text-gray-800 text-sm sm:text-base">{{ $t('dashboard.quick_start') }}</h3>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-2 gap-2 sm:gap-3">
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

    <!-- Subject distribution -->
    <div class="card">
      <div class="flex items-center gap-2 mb-5">
        <span class="w-1 h-5 bg-gradient-to-b from-green-500 to-teal-500 rounded-full inline-block"></span>
        <h3 class="font-bold text-gray-800">{{ $t('dashboard.subject_distribution') }}</h3>
        <span class="text-xs text-gray-400 ml-1">{{ $t('dashboard.subject_distribution_hint') }}</span>
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
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { statsApi } from '@/api/docs'
import { planApi } from '@/api/plan'
import { adviceApi } from '@/api/advice'
import { systemApi } from '@/api/system'

const { t } = useI18n()
const authStore = useAuthStore()
const router = useRouter()

const stats = ref<any>({ today_study_minutes: 0, wrong_book_count: 0, streak_days: 0 })
const todayTasks = ref<any[]>([])
const systemInfo = ref<any>({ llm_model: '', llm_model_short: '', llm_provider: '', app_version: '1.0.0' })

// ── Daily advice ───────────────────────────────────────────────────────────────
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
  // Record that the user clicked the action button
  if (adviceId.value && item.id) {
    try {
      await adviceApi.recordAction(adviceId.value, item.id)
    } catch {}
  }
}

// ── Server time ────────────────────────────────────────────────────────────────
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
  if (h < 6) return t('dashboard.greeting_night')
  if (h < 12) return t('dashboard.greeting_morning')
  if (h < 14) return t('dashboard.greeting_noon')
  if (h < 18) return t('dashboard.greeting_afternoon')
  return t('dashboard.greeting_evening')
})

const dateStr = computed(() => {
  const { month, day, weekday } = timeParts.value
  const weekdayChar = t(`study_plan.weekday_${weekday}`)
  return t('study_plan.date_label_fmt', { month, day, weekday: weekdayChar })
})

const motivationText = computed(() => {
  const texts = t('dashboard.mottos').split('|')
  return texts[timeParts.value.day % texts.length]
})

const todayDone = computed(() => todayTasks.value.filter((task: any) => task.is_done).length)
const todayTotal = computed(() => todayTasks.value.length)

const quickLinks = computed(() => [
  { path: '/ai', icon: '🤖', label: t('dashboard.quick_start_ai'), desc: t('dashboard.quick_start_ai_desc'), bgColor: 'bg-blue-50' },
  { path: '/quiz', icon: '📚', label: t('dashboard.quick_start_quiz'), desc: t('dashboard.quick_start_quiz_desc'), bgColor: 'bg-purple-50' },
  { path: '/wrong-book', icon: '🔁', label: t('dashboard.quick_start_review'), desc: t('dashboard.quick_start_review_desc'), bgColor: 'bg-amber-50' },
  { path: '/notes', icon: '📝', label: t('dashboard.quick_start_notes'), desc: t('dashboard.quick_start_notes_desc'), bgColor: 'bg-green-50' },
])

const subjects = computed(() => [
  { name: t('subjects.math'), icon: '🔢', color: 'bg-blue-50' },
  { name: t('subjects.physics'), icon: '⚡', color: 'bg-purple-50' },
  { name: t('subjects.chemistry'), icon: '🧪', color: 'bg-orange-50' },
  { name: t('subjects.biology'), icon: '🧬', color: 'bg-green-50' },
  { name: t('subjects.chinese'), icon: '📖', color: 'bg-red-50' },
  { name: t('subjects.english'), icon: '🌍', color: 'bg-cyan-50' },
  { name: t('subjects.history'), icon: '🏛️', color: 'bg-amber-50' },
  { name: t('subjects.geography'), icon: '🗺️', color: 'bg-teal-50' },
  { name: t('subjects.politics'), icon: '⚖️', color: 'bg-rose-50' },
])

function taskTypeLabel(type: string) {
  const map: Record<string, string> = {
    study: t('dashboard.study_type_study'),
    practice: t('dashboard.study_type_practice'),
    review: t('dashboard.study_type_review'),
  }
  return map[type] || type
}

onMounted(async () => {
  // Fetch system info (LLM model)
  try {
    const res: any = await systemApi.getSystemInfo()
    systemInfo.value = res.data
  } catch {}

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

  // Load daily advice for student role only
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
