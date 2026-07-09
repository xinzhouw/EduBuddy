<template>
  <div class="space-y-6">

    <!-- Overview cards -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="stat-card text-center">
        <p class="text-3xl font-bold text-blue-600">{{ formatHours(overview.today_study_minutes) }}</p>
        <p class="text-sm text-gray-500 mt-1">{{ $t('stats.today_study') }}</p>
      </div>
      <div class="stat-card text-center">
        <p class="text-3xl font-bold text-orange-500">{{ overview.streak_days }} 🔥</p>
        <p class="text-sm text-gray-500 mt-1">{{ $t('stats.streak') }}</p>
      </div>
      <div class="stat-card text-center">
        <p class="text-3xl font-bold text-green-600">{{ overview.total_questions_done }}</p>
        <p class="text-sm text-gray-500 mt-1">{{ $t('stats.total_questions') }}</p>
      </div>
      <div class="stat-card text-center">
        <p class="text-3xl font-bold text-purple-600">{{ Math.round((overview.average_accuracy || 0) * 100) }}%</p>
        <p class="text-sm text-gray-500 mt-1">{{ $t('stats.avg_accuracy') }}</p>
      </div>
    </div>

    <!-- Row 1: Study duration trend + Subject radar chart -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Study duration trend -->
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-semibold text-gray-700">📈 {{ $t('stats.duration_trend') }}</h3>
          <div class="flex gap-2">
            <button
              class="text-xs px-3 py-1 rounded-lg border transition-colors"
              :class="period === 'week' ? 'bg-blue-500 text-white border-blue-500' : 'bg-white text-gray-600 border-gray-200 hover:border-blue-300'"
              @click="changePeriod('week')"
            >{{ $t('stats.this_week') }}</button>
            <button
              class="text-xs px-3 py-1 rounded-lg border transition-colors"
              :class="period === 'month' ? 'bg-blue-500 text-white border-blue-500' : 'bg-white text-gray-600 border-gray-200 hover:border-blue-300'"
              @click="changePeriod('month')"
            >{{ $t('stats.this_month') }}</button>
          </div>
        </div>
        <div ref="timeChartEl" style="height: 200px"></div>
      </div>

      <!-- Subject mastery radar chart -->
      <div class="card">
        <h3 class="font-semibold text-gray-700 mb-4">🕸️ {{ $t('stats.subject_radar') }}</h3>
        <div v-if="radarData.length === 0" class="flex items-center justify-center h-[200px] text-gray-400 text-sm">
          {{ $t('stats.no_data') }}
        </div>
        <div v-else ref="radarChartEl" style="height: 200px"></div>
      </div>
    </div>

    <!-- Heatmap -->
    <div class="card">
      <h3 class="font-semibold text-gray-700 mb-4">📅 {{ $t('stats.heatmap_title') }}</h3>
      <div v-if="heatmapData.length === 0" class="text-center py-6 text-gray-400 text-sm">{{ $t('stats.no_data') }}</div>
      <div v-else class="overflow-x-auto">
        <div class="flex gap-1 min-w-max">
          <!-- Group by week -->
          <div v-for="(week, wi) in heatmapWeeks" :key="wi" class="flex flex-col gap-1">
            <div
              v-for="(cell, di) in week"
              :key="di"
              class="w-3 h-3 rounded-sm cursor-default transition-transform hover:scale-125"
              :class="heatmapColor(cell.minutes)"
              :title="cell.date ? $t('stats.heatmap_tooltip', {date: cell.date, minutes: cell.minutes}) : ''"
            ></div>
          </div>
        </div>
        <!-- Legend -->
        <div class="flex items-center gap-2 mt-3 text-xs text-gray-400">
          <span>{{ $t('stats.heatmap_less') }}</span>
          <div class="w-3 h-3 rounded-sm bg-gray-100"></div>
          <div class="w-3 h-3 rounded-sm bg-blue-200"></div>
          <div class="w-3 h-3 rounded-sm bg-blue-400"></div>
          <div class="w-3 h-3 rounded-sm bg-blue-600"></div>
          <span>{{ $t('stats.heatmap_more') }}</span>
        </div>
      </div>
    </div>

    <!-- Row 2: Subject accuracy + Subject time distribution -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Subject accuracy -->
      <div class="card">
        <h3 class="font-semibold text-gray-700 mb-4">📊 {{ $t('stats.subject_accuracy') }}</h3>
        <div v-if="accuracyData.length === 0" class="text-center py-8 text-gray-400 text-sm">{{ $t('stats.no_quiz_data') }}</div>
        <div v-else class="space-y-3">
          <div v-for="item in accuracyData" :key="item.subject" class="flex items-center gap-3">
            <span class="text-sm text-gray-600 w-12 shrink-0">{{ item.subject }}</span>
            <div class="flex-1 bg-gray-100 rounded-full h-2.5">
              <div
                class="h-2.5 rounded-full transition-all duration-700"
                :class="accuracyBarColor(item.accuracy)"
                :style="`width: ${Math.round(item.accuracy * 100)}%`"
              ></div>
            </div>
            <span class="text-sm font-semibold w-10 text-right" :class="accuracyTextColor(item.accuracy)">
              {{ Math.round(item.accuracy * 100) }}%
            </span>
          </div>
        </div>
      </div>

      <!-- Subject time distribution -->
      <div class="card">
        <h3 class="font-semibold text-gray-700 mb-4">🥧 {{ $t('stats.subject_time') }}</h3>
        <div v-if="subjectTimeData.length === 0" class="text-center py-8 text-gray-400 text-sm">{{ $t('stats.no_study_data') }}</div>
        <div v-else ref="pieChartEl" style="height: 200px"></div>
      </div>
    </div>

    <!-- Wrong answer distribution -->
    <div class="card">
      <h3 class="font-semibold text-gray-700 mb-4">❌ {{ $t('stats.wrong_distribution') }}</h3>
      <div v-if="wrongDist.length === 0" class="text-center py-6 text-gray-400 text-sm">{{ $t('stats.no_wrong_data') }}</div>
      <div v-else class="space-y-2">
        <div v-for="item in wrongDist" :key="item.subject" class="flex items-center justify-between">
          <span class="text-sm text-gray-600 w-16 shrink-0">{{ item.subject }}</span>
          <div class="flex-1 bg-gray-100 rounded-full h-2 mx-3">
            <div class="bg-red-400 h-2 rounded-full transition-all duration-700"
              :style="`width: ${(item.count / maxWrongCount) * 100}%`"></div>
          </div>
          <span class="text-sm font-medium text-gray-700 w-8 text-right">{{ item.count }}</span>
        </div>
      </div>
    </div>

    <!-- Study overview + AI report -->
    <div class="card">
      <h3 class="font-semibold text-gray-700 mb-5">📋 {{ $t('stats.overview_title') }}</h3>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-center mb-6">
        <div>
          <p class="text-xl font-bold text-gray-800">{{ overview.total_study_days }}</p>
          <p class="text-sm text-gray-500">{{ $t('stats.total_study_days') }}</p>
        </div>
        <div>
          <p class="text-xl font-bold text-gray-800">{{ overview.wrong_book_count }}</p>
          <p class="text-sm text-gray-500">{{ $t('stats.total_wrong_count') }}</p>
        </div>
        <div>
          <p class="text-xl font-bold text-green-600">{{ overview.mastered_count }}</p>
          <p class="text-sm text-gray-500">{{ $t('stats.mastered_wrong') }}</p>
        </div>
        <div>
          <p class="text-xl font-bold text-blue-600">{{ overview.total_questions_done }}</p>
          <p class="text-sm text-gray-500">{{ $t('stats.total_questions_answered') }}</p>
        </div>
      </div>

      <!-- AI analysis report -->
      <div class="border-t border-gray-100 pt-5">
        <div class="flex items-center justify-between mb-4">
          <h4 class="font-semibold text-gray-700 flex items-center gap-2">
            <span>🤖</span> {{ $t('stats.ai_report_title') }}
          </h4>
          <button
            @click="generateReport"
            :disabled="reportLoading"
            class="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium transition-colors disabled:opacity-50"
          >
            <span v-if="reportLoading" class="animate-spin inline-block">⏳</span>
            <span v-else>✨</span>
            {{ reportLoading ? $t('stats.gen_report_loading') : $t('stats.gen_report_btn') }}
          </button>
        </div>

        <!-- Report content -->
        <div v-if="reportContent" class="bg-slate-50 rounded-xl p-5 border border-slate-100">
          <div class="prose prose-sm max-w-none text-gray-700 leading-relaxed whitespace-pre-wrap">{{ reportContent }}</div>
        </div>
        <div v-else-if="!reportLoading" class="text-center py-8 text-gray-400 text-sm">
          {{ $t('stats.report_prompt') }}
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { statsApi } from '@/api/docs'
// Import ECharts selectively to reduce bundle size
import * as echarts from 'echarts/core'
import { LineChart, PieChart, RadarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, RadarComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([LineChart, PieChart, RadarChart, GridComponent, TooltipComponent, LegendComponent, RadarComponent, CanvasRenderer])

const { t } = useI18n()

// ── Data ──────────────────────────────────────────────────────────────────────
const overview = ref<any>({
  today_study_minutes: 0, streak_days: 0,
  total_questions_done: 0, average_accuracy: 0,
  total_study_days: 0, wrong_book_count: 0, mastered_count: 0,
})
const period = ref('week')
const timeData = ref<any>({ labels: [], values: [] })
const accuracyData = ref<any[]>([])
const wrongDist = ref<any[]>([])
const radarData = ref<any[]>([])
const heatmapData = ref<any[]>([])
const subjectTimeData = ref<any[]>([])

const reportContent = ref('')
const reportLoading = ref(false)

// ── DOM refs ──────────────────────────────────────────────────────────────────
const timeChartEl = ref<HTMLElement>()
const radarChartEl = ref<HTMLElement>()
const pieChartEl = ref<HTMLElement>()
let timeChart: echarts.ECharts | null = null
let radarChart: echarts.ECharts | null = null
let pieChart: echarts.ECharts | null = null

// ── Computed ──────────────────────────────────────────────────────────────────
const maxWrongCount = computed(() => Math.max(...wrongDist.value.map((i: any) => i.count), 1))

/** Group heatmap data into columns of 7 rows (Mon–Sun) */
const heatmapWeeks = computed(() => {
  if (!heatmapData.value.length) return []
  // Build date → minutes map
  const map = new Map<string, number>()
  heatmapData.value.forEach((d: any) => map.set(d.date, d.minutes))

  // Find data date range
  const sorted = [...heatmapData.value].sort((a, b) => a.date.localeCompare(b.date))
  if (!sorted.length) return []
  const start = new Date(sorted[0].date)
  const end = new Date(sorted[sorted.length - 1].date)

  // Rewind to nearest Sunday as start
  const startSunday = new Date(start)
  startSunday.setDate(start.getDate() - start.getDay())

  const weeks: Array<Array<{ date: string; minutes: number }>> = []
  const cur = new Date(startSunday)
  let currentWeek: Array<{ date: string; minutes: number }> = []

  while (cur <= end) {
    const dateStr = cur.toISOString().slice(0, 10)
    currentWeek.push({ date: dateStr, minutes: map.get(dateStr) || 0 })
    if (currentWeek.length === 7) {
      weeks.push(currentWeek)
      currentWeek = []
    }
    cur.setDate(cur.getDate() + 1)
  }
  if (currentWeek.length) weeks.push(currentWeek)
  return weeks
})

// ── Utility functions ──────────────────────────────────────────────────────────
function formatHours(minutes: number) {
  return minutes >= 60 ? `${(minutes / 60).toFixed(1)}h` : `${minutes}min`
}

function heatmapColor(minutes: number) {
  if (minutes === 0) return 'bg-gray-100'
  if (minutes <= 30) return 'bg-blue-200'
  if (minutes <= 60) return 'bg-blue-400'
  return 'bg-blue-600'
}

function accuracyBarColor(acc: number) {
  if (acc >= 0.8) return 'bg-green-500'
  if (acc >= 0.6) return 'bg-amber-500'
  return 'bg-red-400'
}

function accuracyTextColor(acc: number) {
  if (acc >= 0.8) return 'text-green-600'
  if (acc >= 0.6) return 'text-amber-600'
  return 'text-red-500'
}

// ── Chart rendering ────────────────────────────────────────────────────────────
function renderTimeChart() {
  if (!timeChartEl.value) return
  if (!timeChart) timeChart = echarts.init(timeChartEl.value)
  const minutesUnit = t('stats.minutes_unit')
  timeChart.setOption({
    grid: { top: 20, right: 20, bottom: 30, left: 50 },
    xAxis: {
      type: 'category', data: timeData.value.labels,
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisLabel: { color: '#9ca3af', fontSize: 11 },
    },
    yAxis: {
      type: 'value', name: minutesUnit,
      nameTextStyle: { color: '#9ca3af', fontSize: 11 },
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#f3f4f6' } },
    },
    series: [{
      type: 'line', data: timeData.value.values, smooth: true,
      areaStyle: { color: 'rgba(59,130,246,0.08)' },
      lineStyle: { color: '#3b82f6', width: 2 },
      itemStyle: { color: '#3b82f6' },
    }],
    tooltip: {
      trigger: 'axis',
      formatter: (p: any) => `${p[0].name}<br>${p[0].value} ${minutesUnit}`,
    },
  })
}

function renderRadarChart() {
  if (!radarChartEl.value || !radarData.value.length) return
  if (!radarChart) radarChart = echarts.init(radarChartEl.value)
  const indicators = radarData.value.map((d: any) => ({ name: d.subject, max: 100 }))
  const values = radarData.value.map((d: any) => d.score)
  radarChart.setOption({
    radar: {
      indicator: indicators,
      splitNumber: 4,
      axisName: { color: '#6b7280', fontSize: 11 },
      splitLine: { lineStyle: { color: '#f3f4f6' } },
      splitArea: { areaStyle: { color: ['rgba(59,130,246,0.02)', 'rgba(59,130,246,0.05)'] } },
    },
    series: [{
      type: 'radar',
      data: [{ value: values, name: t('stats.subject_radar') }],
      areaStyle: { color: 'rgba(99,102,241,0.15)' },
      lineStyle: { color: '#6366f1', width: 2 },
      itemStyle: { color: '#6366f1' },
    }],
    tooltip: { trigger: 'item' },
  })
}

function renderPieChart() {
  if (!pieChartEl.value || !subjectTimeData.value.length) return
  if (!pieChart) pieChart = echarts.init(pieChartEl.value)
  const pieColors = ['#3b82f6', '#8b5cf6', '#f59e0b', '#10b981', '#ef4444', '#06b6d4', '#f97316', '#14b8a6', '#ec4899']
  const minutesUnit = t('stats.minutes_unit')
  pieChart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: (p: any) => `${p.name}: ${p.value} ${minutesUnit} (${p.percent}%)`,
    },
    legend: { orient: 'vertical', right: '0%', top: 'middle', textStyle: { fontSize: 11, color: '#6b7280' } },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['40%', '50%'],
      data: subjectTimeData.value.map((d: any, i: number) => ({
        name: d.subject,
        value: d.minutes,
        itemStyle: { color: pieColors[i % pieColors.length] },
      })),
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 12 } },
    }],
  })
}

// ── Data loading ──────────────────────────────────────────────────────────────
async function loadData() {
  try {
    const [ovRes, accRes, wrongRes, radarRes, heatRes, subRes]: any[] = await Promise.all([
      statsApi.getOverview(),
      statsApi.getAccuracyBySubject(),
      statsApi.getWrongDistribution(),
      statsApi.getRadar(),
      statsApi.getHeatmap(),
      statsApi.getSubjectTimeDistribution(),
    ])
    overview.value = ovRes.data
    accuracyData.value = accRes.data || []
    wrongDist.value = wrongRes.data || []
    radarData.value = radarRes.data || []
    heatmapData.value = heatRes.data || []
    subjectTimeData.value = subRes.data || []
  } catch {}
  await loadTimeChart()
  await nextTick()
  renderRadarChart()
  renderPieChart()
}

async function changePeriod(p: string) {
  period.value = p
  await loadTimeChart()
}

async function loadTimeChart() {
  try {
    const res: any = await statsApi.getStudyTime(period.value)
    timeData.value = res.data
    await nextTick()
    renderTimeChart()
  } catch {}
}

// ── AI report generation (SSE streaming) ────────────────────────────────────
async function generateReport() {
  reportLoading.value = true
  reportContent.value = ''
  try {
    const token = localStorage.getItem('token')
    const res = await fetch('/api/stats/generate-report', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    })
    if (!res.ok || !res.body) {
      reportLoading.value = false
      return
    }
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const chunk = line.slice(6)
          if (chunk === '[DONE]') {
            reportLoading.value = false
            return
          }
          reportContent.value += chunk
        }
      }
    }
  } catch {
    reportLoading.value = false
  }
  reportLoading.value = false
}

onMounted(loadData)
</script>

<style scoped>
@reference "../../style.css";
.stat-card {
  @apply bg-white rounded-2xl border border-gray-100 shadow-sm p-5;
}
.card {
  @apply bg-white rounded-2xl border border-gray-100 shadow-sm p-6;
}
</style>
