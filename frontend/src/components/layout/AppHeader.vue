<template>
  <header class="h-16 bg-white/80 backdrop-blur-md border-b border-gray-100 flex items-center justify-between px-3 sm:px-6 shrink-0 sticky top-0 z-10">
    <!-- Page title -->
    <div class="flex items-center gap-3 min-w-0">
      <h1 class="text-base sm:text-lg font-bold text-gray-800 truncate">{{ pageTitle }}</h1>
    </div>

    <!-- Right toolbar -->
    <div class="flex items-center gap-2 sm:gap-3 shrink-0">
      <!-- PC: Today due review reminder (text hidden on mobile) -->
      <RouterLink
        v-if="todayDue > 0"
        to="/wrong-book?due=true"
        class="hidden sm:flex items-center gap-1.5 px-3 py-1.5 bg-amber-50 text-amber-700 border border-amber-200 rounded-full text-sm hover:bg-amber-100 hover:border-amber-300 transition-all shadow-sm"
      >
        <span>⏰</span>
        <span class="font-medium">{{ $t('common.today_due_fmt', { n: todayDue }) }}</span>
      </RouterLink>

      <!-- Mobile: Due review icon -->
      <RouterLink
        v-if="todayDue > 0"
        to="/wrong-book?due=true"
        class="sm:hidden w-8 h-8 flex items-center justify-center text-amber-600 hover:bg-amber-50 rounded-lg transition-colors relative"
        :title="$t('common.pending_review_label')"
      >
        <span class="text-lg">⏰</span>
        <span v-if="todayDue > 0" class="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center font-bold">
          {{ todayDue > 9 ? '9+' : todayDue }}
        </span>
      </RouterLink>

      <!-- PC: Streak days (hidden on mobile) -->
      <div
        v-if="streakDays > 0"
        class="hidden sm:flex items-center gap-1.5 px-3 py-1.5 bg-orange-50 text-orange-600 border border-orange-200 rounded-full text-sm shadow-sm"
      >
        <span>🔥</span>
        <span class="font-medium">{{ $t('common.streak_days_fmt', { n: streakDays }) }}</span>
      </div>

      <!-- Divider (PC only) -->
      <div class="hidden sm:block w-px h-5 bg-gray-200"></div>

      <!-- Search button (placeholder, PC only) -->
      <button class="hidden sm:flex w-8 h-8 items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </button>

      <!-- Language switcher -->
      <LanguageSwitcher />

      <!-- Notification button (placeholder) -->
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
import { useI18n } from 'vue-i18n'
import { wrongBookApi } from '@/api/wrongBook'
import { statsApi } from '@/api/docs'
import LanguageSwitcher from '@/components/layout/LanguageSwitcher.vue'

const { t } = useI18n()
const route = useRoute()
const todayDue = ref(0)
const streakDays = ref(0)

const pageTitle = computed(() => {
  const path = route.path
  const titles: Record<string, string> = {
    '/': t('navigation.home'),
    '/ai': t('navigation.ai_chat'),
    '/notes': t('navigation.my_notes'),
    '/quiz': t('navigation.quiz'),
    '/wrong-book': t('navigation.wrong_book'),
    '/plan': t('navigation.study_plan'),
    '/docs': t('navigation.docs_material'),
    '/stats': t('navigation.learning_stats'),
    '/profile': t('navigation.profile'),
  }
  for (const [key, title] of Object.entries(titles)) {
    if (key !== '/' && path.startsWith(key)) return title
  }
  return titles[path] || 'EduBuddy'
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
