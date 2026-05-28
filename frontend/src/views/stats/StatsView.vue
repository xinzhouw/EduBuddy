<template>
  <div class="space-y-6">
    <!-- 统计卡片 -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="card text-center">
        <p class="text-3xl font-bold text-blue-600">{{ formatHours(overview.today_study_minutes) }}</p>
        <p class="text-sm text-gray-500 mt-1">今日学习</p>
      </div>
      <div class="card text-center">
        <p class="text-3xl font-bold text-orange-500">{{ overview.streak_days }} 🔥</p>
        <p class="text-sm text-gray-500 mt-1">连续打卡</p>
      </div>
      <div class="card text-center">
        <p class="text-3xl font-bold text-green-600">{{ overview.total_questions_done }}</p>
        <p class="text-sm text-gray-500 mt-1">累计完成题数</p>
      </div>
      <div class="card text-center">
        <p class="text-3xl font-bold text-purple-600">{{ Math.round((overview.average_accuracy || 0) * 100) }}%</p>
        <p class="text-sm text-gray-500 mt-1">平均正确率</p>
      </div>
    </div>

    <!-- 学习时长趋势 -->
    <div class="card">
      <div class="flex items-center justify-between mb-4">
        <h3 class="font-semibold text-gray-700">📈 学习时长趋势</h3>
        <div class="flex gap-2">
          <el-button size="small" :type="period === 'week' ? 'primary' : ''" @click="changePeriod('week')">本周</el-button>
          <el-button size="small" :type="period === 'month' ? 'primary' : ''" @click="changePeriod('month')">本月</el-button>
        </div>
      </div>
      <div ref="chartEl" style="height: 200px"></div>
    </div>

    <!-- 错题分布 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="card">
        <h3 class="font-semibold text-gray-700 mb-4">📊 各学科正确率</h3>
        <div v-if="accuracyData.length === 0" class="text-center py-8 text-gray-400 text-sm">暂无答题数据</div>
        <div v-else class="space-y-3">
          <div v-for="item in accuracyData" :key="item.subject" class="flex items-center gap-3">
            <span class="text-sm text-gray-600 w-12 shrink-0">{{ item.subject }}</span>
            <div class="flex-1 bg-gray-200 rounded-full h-2">
              <div class="bg-blue-500 h-2 rounded-full transition-all"
                :style="`width: ${Math.round(item.accuracy * 100)}%`"></div>
            </div>
            <span class="text-sm font-medium text-gray-700 w-10 text-right">{{ Math.round(item.accuracy * 100) }}%</span>
          </div>
        </div>
      </div>

      <div class="card">
        <h3 class="font-semibold text-gray-700 mb-4">❌ 错题知识点分布</h3>
        <div v-if="wrongDist.length === 0" class="text-center py-8 text-gray-400 text-sm">暂无错题数据</div>
        <div v-else class="space-y-2">
          <div v-for="item in wrongDist" :key="item.subject" class="flex items-center justify-between">
            <span class="text-sm text-gray-600">{{ item.subject }}</span>
            <div class="flex items-center gap-2">
              <div class="w-24 bg-gray-200 rounded-full h-1.5">
                <div class="bg-red-400 h-1.5 rounded-full"
                  :style="`width: ${(item.count / maxWrongCount) * 100}%`"></div>
              </div>
              <span class="text-sm font-medium text-gray-700">{{ item.count }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 总体数据 -->
    <div class="card">
      <h3 class="font-semibold text-gray-700 mb-4">📋 学习总览</h3>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
        <div><p class="text-xl font-bold text-gray-800">{{ overview.total_study_days }}</p><p class="text-sm text-gray-500">总学习天数</p></div>
        <div><p class="text-xl font-bold text-gray-800">{{ overview.wrong_book_count }}</p><p class="text-sm text-gray-500">错题总数</p></div>
        <div><p class="text-xl font-bold text-green-600">{{ overview.mastered_count }}</p><p class="text-sm text-gray-500">已掌握错题</p></div>
        <div><p class="text-xl font-bold text-blue-600">{{ overview.total_questions_done }}</p><p class="text-sm text-gray-500">总答题数</p></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { statsApi } from '@/api/docs'
import * as echarts from 'echarts'

const overview = ref<any>({ today_study_minutes: 0, streak_days: 0, total_questions_done: 0, average_accuracy: 0, total_study_days: 0, wrong_book_count: 0, mastered_count: 0 })
const chartEl = ref<HTMLElement>()
const period = ref('week')
const timeData = ref<any>({ labels: [], values: [] })
const accuracyData = ref<any[]>([])
const wrongDist = ref<any[]>([])
let chart: echarts.ECharts | null = null

const maxWrongCount = computed(() => Math.max(...wrongDist.value.map(i => i.count), 1))
function formatHours(minutes: number) { return minutes >= 60 ? `${(minutes / 60).toFixed(1)}h` : `${minutes}min` }

async function loadData() {
  try {
    const [ovRes, accRes, wrongRes]: any[] = await Promise.all([
      statsApi.getOverview(),
      statsApi.getAccuracyBySubject(),
      statsApi.getWrongDistribution(),
    ])
    overview.value = ovRes.data
    accuracyData.value = accRes.data || []
    wrongDist.value = wrongRes.data || []
  } catch {}
  await loadTimeChart()
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
    renderChart()
  } catch {}
}

function renderChart() {
  if (!chartEl.value) return
  if (!chart) chart = echarts.init(chartEl.value)
  chart.setOption({
    grid: { top: 20, right: 20, bottom: 30, left: 50 },
    xAxis: { type: 'category', data: timeData.value.labels, axisLine: { lineStyle: { color: '#e5e7eb' } } },
    yAxis: { type: 'value', name: '分钟', nameTextStyle: { color: '#9ca3af' }, axisLine: { show: false }, splitLine: { lineStyle: { color: '#f3f4f6' } } },
    series: [{ type: 'line', data: timeData.value.values, smooth: true, areaStyle: { color: 'rgba(59, 130, 246, 0.1)' }, lineStyle: { color: '#3b82f6' }, itemStyle: { color: '#3b82f6' } }],
    tooltip: { trigger: 'axis', formatter: (p: any) => `${p[0].name}<br>${p[0].value} 分钟` },
  })
}

onMounted(loadData)
</script>
