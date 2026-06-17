<template>
  <div class="space-y-6">

    <!-- 返回 + 标题 -->
    <div class="flex items-center gap-3">
      <button @click="router.back()" class="w-9 h-9 rounded-xl bg-white border border-gray-100 shadow-sm flex items-center justify-center text-gray-500 hover:text-gray-700 hover:shadow-md transition-all">
        ‹
      </button>
      <div v-if="student">
        <h1 class="text-xl font-bold text-gray-800">{{ student.nickname }} 的学习概览</h1>
        <p class="text-sm text-gray-400">{{ student.grade }} · 最后活跃：{{ student.last_login_date || '未知' }}</p>
      </div>
      <div v-else class="text-gray-500 text-sm">加载中…</div>
    </div>

    <div v-if="loading" class="flex items-center justify-center py-20 text-gray-400">
      <span class="animate-spin mr-2">⏳</span> 加载中…
    </div>

    <template v-else-if="overview">
      <!-- 概览卡片 -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="stat-card text-center">
          <p class="text-2xl font-bold text-blue-600">{{ overview.today_study_minutes }}<span class="text-sm font-normal text-gray-400 ml-1">min</span></p>
          <p class="text-sm text-gray-500 mt-1">今日学习</p>
        </div>
        <div class="stat-card text-center">
          <p class="text-2xl font-bold text-orange-500">{{ overview.streak_days }} 🔥</p>
          <p class="text-sm text-gray-500 mt-1">连续打卡</p>
        </div>
        <div class="stat-card text-center">
          <p class="text-2xl font-bold text-green-600">{{ overview.total_questions_done }}</p>
          <p class="text-sm text-gray-500 mt-1">累计答题</p>
        </div>
        <div class="stat-card text-center">
          <p class="text-2xl font-bold text-purple-600">{{ Math.round((overview.average_accuracy || 0) * 100) }}%</p>
          <p class="text-sm text-gray-500 mt-1">平均正确率</p>
        </div>
      </div>

      <!-- 详细统计图表 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- 学习时长趋势 -->
        <div class="card">
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-semibold text-gray-700">📈 学习时长趋势</h3>
            <div class="flex gap-2">
              <button
                class="text-xs px-3 py-1 rounded-lg border transition-colors"
                :class="period === 'week' ? 'bg-blue-500 text-white border-blue-500' : 'bg-white text-gray-600 border-gray-200 hover:border-blue-300'"
                @click="changePeriod('week')"
              >本周</button>
              <button
                class="text-xs px-3 py-1 rounded-lg border transition-colors"
                :class="period === 'month' ? 'bg-blue-500 text-white border-blue-500' : 'bg-white text-gray-600 border-gray-200 hover:border-blue-300'"
                @click="changePeriod('month')"
              >本月</button>
            </div>
          </div>
          <div ref="timeChartEl" style="height: 180px"></div>
        </div>

        <!-- 各学科正确率 -->
        <div class="card">
          <h3 class="font-semibold text-gray-700 mb-4">📊 各学科正确率</h3>
          <div v-if="!accuracyData.length" class="text-center py-8 text-gray-400 text-sm">暂无数据</div>
          <div v-else class="space-y-3">
            <div v-for="item in accuracyData" :key="item.subject" class="flex items-center gap-3">
              <span class="text-sm text-gray-600 w-12 shrink-0">{{ item.subject }}</span>
              <div class="flex-1 bg-gray-100 rounded-full h-2.5">
                <div
                  class="h-2.5 rounded-full transition-all duration-700"
                  :class="item.accuracy >= 0.8 ? 'bg-green-500' : item.accuracy >= 0.6 ? 'bg-amber-500' : 'bg-red-400'"
                  :style="`width: ${Math.round(item.accuracy * 100)}%`"
                ></div>
              </div>
              <span class="text-sm font-semibold w-10 text-right"
                :class="item.accuracy >= 0.8 ? 'text-green-600' : item.accuracy >= 0.6 ? 'text-amber-600' : 'text-red-500'">
                {{ Math.round(item.accuracy * 100) }}%
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 雷达图 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="card">
          <h3 class="font-semibold text-gray-700 mb-4">🕸️ 学科掌握雷达</h3>
          <div v-if="!radarData.length" class="text-center py-8 text-gray-400 text-sm">暂无数据</div>
          <div v-else ref="radarChartEl" style="height: 200px"></div>
        </div>

        <!-- 错题分布 -->
        <div class="card">
          <h3 class="font-semibold text-gray-700 mb-4">❌ 错题分布</h3>
          <div v-if="!wrongDist.length" class="text-center py-8 text-gray-400 text-sm">暂无错题</div>
          <div v-else class="space-y-2">
            <div v-for="item in wrongDist" :key="item.subject" class="flex items-center justify-between">
              <span class="text-sm text-gray-600 w-16 shrink-0">{{ item.subject }}</span>
              <div class="flex-1 bg-gray-100 rounded-full h-2 mx-3">
                <div class="bg-red-400 h-2 rounded-full"
                  :style="`width: ${(item.count / maxWrongCount) * 100}%`"></div>
              </div>
              <span class="text-sm font-medium text-gray-700 w-8 text-right">{{ item.count }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 今日学习计划 -->
      <div class="card">
        <h3 class="font-semibold text-gray-700 mb-4">📅 近期学习计划（只读）</h3>
        <div v-if="!planData" class="text-center py-6 text-gray-400 text-sm">暂无学习计划</div>
        <div v-else>
          <div
            v-for="(tasks, dateKey) in planData.tasks_by_date"
            :key="dateKey"
            class="mb-4"
          >
            <p class="text-xs font-semibold text-gray-500 mb-2">{{ dateKey }}</p>
            <div class="space-y-1.5">
              <div
                v-for="task in tasks"
                :key="task.id"
                class="flex items-center gap-2 p-2.5 rounded-xl text-sm"
                :class="task.is_done ? 'bg-green-50 border border-green-100' : 'bg-gray-50 border border-gray-100'"
              >
                <span class="text-base">{{ task.is_done ? '✅' : '⬜' }}</span>
                <span class="flex-1 text-gray-700" :class="{ 'line-through text-gray-400': task.is_done }">
                  {{ task.subject }} · {{ task.topic }}
                </span>
                <span class="text-xs text-gray-400">{{ task.duration_minutes }}min</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- AI 学习报告 -->
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-semibold text-gray-700">🤖 AI 学习报告</h3>
          <button
            @click="generateReport"
            :disabled="reportLoading"
            class="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium transition-colors disabled:opacity-50"
          >
            <span v-if="reportLoading" class="animate-spin inline-block">⏳</span>
            <span v-else>✨</span>
            {{ reportLoading ? '生成中…' : '生成报告' }}
          </button>
        </div>
        <div v-if="reportContent" class="bg-slate-50 rounded-xl p-5 border border-slate-100">
          <div class="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{{ reportContent }}</div>
        </div>
        <div v-else-if="!reportLoading" class="text-center py-6 text-gray-400 text-sm">
          点击「生成报告」，AI 将为该学生生成近30天学习分析
        </div>
      </div>
    </template>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { monitorApi } from '@/api/relations'
// 按需导入 ECharts，减少包体积
import * as echarts from 'echarts/core'
import { LineChart, RadarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, RadarComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([LineChart, RadarChart, GridComponent, TooltipComponent, LegendComponent, RadarComponent, CanvasRenderer])

const route = useRoute()
const router = useRouter()

const studentId = Number(route.params.id)

const loading = ref(true)
const student = ref<any>(null)
const overview = ref<any>(null)
const accuracyData = ref<any[]>([])
const radarData = ref<any[]>([])
const wrongDist = ref<any[]>([])
const planData = ref<any>(null)
const period = ref('week')
const timeData = ref<any>({ labels: [], values: [] })

const reportLoading = ref(false)
const reportContent = ref('')

const timeChartEl = ref<HTMLElement>()
const radarChartEl = ref<HTMLElement>()
let timeChart: echarts.ECharts | null = null
let radarChart: echarts.ECharts | null = null

const maxWrongCount = computed(() => Math.max(...wrongDist.value.map((i: any) => i.count), 1))

function renderTimeChart() {
  if (!timeChartEl.value) return
  if (!timeChart) timeChart = echarts.init(timeChartEl.value)
  timeChart.setOption({
    grid: { top: 20, right: 20, bottom: 30, left: 50 },
    xAxis: {
      type: 'category', data: timeData.value.labels,
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisLabel: { color: '#9ca3af', fontSize: 11 },
    },
    yAxis: {
      type: 'value', name: '分钟',
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
    tooltip: { trigger: 'axis', formatter: (p: any) => `${p[0].name}<br>${p[0].value} 分钟` },
  })
}

function renderRadarChart() {
  if (!radarChartEl.value || !radarData.value.length) return
  if (!radarChart) radarChart = echarts.init(radarChartEl.value)
  radarChart.setOption({
    radar: {
      indicator: radarData.value.map((d: any) => ({ name: d.subject, max: 100 })),
      splitNumber: 4,
      axisName: { color: '#6b7280', fontSize: 11 },
      splitLine: { lineStyle: { color: '#f3f4f6' } },
    },
    series: [{
      type: 'radar',
      data: [{ value: radarData.value.map((d: any) => d.score), name: '掌握深度' }],
      areaStyle: { color: 'rgba(99,102,241,0.15)' },
      lineStyle: { color: '#6366f1', width: 2 },
      itemStyle: { color: '#6366f1' },
    }],
    tooltip: { trigger: 'item' },
  })
}

async function changePeriod(p: string) {
  period.value = p
  try {
    const res: any = await monitorApi.getStudentStats(studentId, p)
    timeData.value = res.data?.time_trend || { labels: [], values: [] }
    await nextTick()
    renderTimeChart()
  } catch {}
}

async function generateReport() {
  reportLoading.value = true
  reportContent.value = ''
  try {
    const token = localStorage.getItem('token')
    const res = await fetch(`/api/monitor/students/${studentId}/report`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!res.ok || !res.body) { reportLoading.value = false; return }
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
          if (chunk === '[DONE]') { reportLoading.value = false; return }
          reportContent.value += chunk
        }
      }
    }
  } catch {}
  reportLoading.value = false
}

onMounted(async () => {
  try {
    // 并行请求概览 + 统计 + 计划
    const [ovRes, statsRes, planRes]: any[] = await Promise.all([
      monitorApi.getStudentOverview(studentId),
      monitorApi.getStudentStats(studentId, period.value),
      monitorApi.getStudentPlan(studentId),
    ])
    overview.value = ovRes.data
    student.value = ovRes.data?.student

    const statsData = statsRes.data
    timeData.value = statsData?.time_trend || { labels: [], values: [] }
    accuracyData.value = statsData?.accuracy_by_subject || []
    radarData.value = statsData?.radar || []
    wrongDist.value = statsData?.wrong_distribution || []

    planData.value = planRes.data
  } catch {}
  loading.value = false
  await nextTick()
  renderTimeChart()
  renderRadarChart()
})
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
