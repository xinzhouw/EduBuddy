<template>
  <div class="space-y-6">
    <!-- 没有计划时显示创建 -->
    <div v-if="!plan && !showCreate" class="text-center py-16">
      <span class="text-5xl">📅</span>
      <p class="mt-4 text-lg text-gray-600">还没有学习计划，制定一个目标吧！</p>
      <el-button type="primary" class="mt-4" @click="showCreate = true">创建学习计划</el-button>
    </div>

    <!-- 创建计划表单 -->
    <div v-if="showCreate" class="card max-w-2xl mx-auto space-y-4">
      <h3 class="font-bold text-gray-800">📅 制定学习计划</h3>
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-600 mb-1">备考学科（多选）</label>
          <el-checkbox-group v-model="createForm.subjects">
            <el-checkbox v-for="s in subjects" :key="s" :value="s">{{ s }}</el-checkbox>
          </el-checkbox-group>
        </div>
        <div class="space-y-3">
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">考试日期</label>
            <el-date-picker v-model="createForm.exam_date" type="date" value-format="YYYY-MM-DD" class="w-full" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">每天学习时长（小时）</label>
            <el-input-number v-model="createForm.daily_hours" :min="0.5" :max="12" :step="0.5" />
          </div>
        </div>
      </div>
      <div class="flex gap-3">
        <el-button type="primary" @click="generatePlan" :loading="generating">生成计划</el-button>
        <el-button @click="showCreate = false">取消</el-button>
      </div>
    </div>

    <!-- 已有计划 -->
    <template v-if="plan && !showCreate">
      <!-- 概览 -->
      <div class="card">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-500">考试倒计时</p>
            <p class="text-2xl font-bold text-gray-800">还有 {{ daysLeft }} 天</p>
          </div>
          <div class="text-right">
            <p class="text-sm text-gray-500">今日完成</p>
            <p class="text-2xl font-bold text-green-600">{{ todayDone }}/{{ todayTotal }}</p>
          </div>
          <el-button size="small" @click="showCreate = true">⚙ 重新生成</el-button>
        </div>
        <div class="mt-3 w-full bg-gray-200 rounded-full h-2">
          <div class="bg-green-500 h-2 rounded-full transition-all"
            :style="`width: ${todayTotal > 0 ? (todayDone / todayTotal) * 100 : 0}%`"></div>
        </div>
      </div>

      <!-- 今日任务 -->
      <div class="card">
        <h3 class="font-semibold text-gray-800 mb-4">📋 今日任务</h3>
        <div v-if="todayTasks.length === 0" class="text-center py-4 text-gray-400 text-sm">今日无任务</div>
        <div class="space-y-3">
          <div v-for="task in todayTasks" :key="task.id"
            class="flex items-center gap-3 p-3 rounded-lg border transition-colors"
            :class="task.is_done ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'">
            <el-checkbox :model-value="task.is_done" @change="toggleTask(task)" />
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-gray-700">{{ task.subject }} · {{ task.topic }}</p>
              <p class="text-xs text-gray-500">{{ task.duration_minutes }}分钟 · {{ taskTypeLabel(task.task_type) }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 番茄钟 -->
      <div class="card max-w-sm">
        <h3 class="font-semibold text-gray-700 mb-4">🍅 番茄钟</h3>
        <div class="text-center">
          <p class="text-5xl font-mono font-bold text-gray-800 mb-4">{{ formatTime(pomodoroTime) }}</p>
          <p class="text-sm text-gray-500 mb-4">{{ isBreak ? '休息时间 ☕' : '专注学习 📚' }}</p>
          <div class="flex justify-center gap-3">
            <el-button @click="togglePomodoro" :type="running ? 'warning' : 'primary'">
              {{ running ? '暂停' : '开始' }}
            </el-button>
            <el-button @click="resetPomodoro">重置</el-button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { planApi } from '@/api/plan'
import { ElMessage } from 'element-plus'

const subjects = ['数学', '物理', '化学', '生物', '语文', '英语', '历史', '地理', '政治']
const plan = ref<any>(null)
const todayTasks = ref<any[]>([])
const showCreate = ref(false)
const generating = ref(false)
const createForm = ref({ subjects: [] as string[], exam_date: '', daily_hours: 3, weak_subjects: [] as string[] })

const todayDone = computed(() => todayTasks.value.filter(t => t.is_done).length)
const todayTotal = computed(() => todayTasks.value.length)
const daysLeft = computed(() => {
  if (!plan.value?.end_date) return 0
  const diff = new Date(plan.value.end_date).getTime() - Date.now()
  return Math.max(0, Math.ceil(diff / 86400000))
})
function taskTypeLabel(type: string) { return { study: '学习', practice: '练习', review: '复习' }[type] || type }
function formatTime(s: number) { return `${Math.floor(s / 60).toString().padStart(2, '0')}:${(s % 60).toString().padStart(2, '0')}` }

// 番茄钟
const FOCUS = 25 * 60, BREAK = 5 * 60
const pomodoroTime = ref(FOCUS)
const running = ref(false)
const isBreak = ref(false)
let timer: any

function togglePomodoro() {
  running.value = !running.value
  if (running.value) {
    timer = setInterval(() => {
      if (pomodoroTime.value > 0) {
        pomodoroTime.value--
      } else {
        isBreak.value = !isBreak.value
        pomodoroTime.value = isBreak.value ? BREAK : FOCUS
        ElMessage.success(isBreak.value ? '专注时间结束，休息一下！' : '休息结束，继续学习！')
      }
    }, 1000)
  } else {
    clearInterval(timer)
  }
}

function resetPomodoro() {
  running.value = false
  isBreak.value = false
  pomodoroTime.value = FOCUS
  clearInterval(timer)
}

async function loadPlan() {
  try {
    const res: any = await planApi.getCurrent()
    plan.value = res.data
    if (plan.value) {
      const todayRes: any = await planApi.getToday()
      todayTasks.value = todayRes.data || []
    }
  } catch {}
}

async function generatePlan() {
  if (createForm.value.subjects.length === 0) return ElMessage.warning('请选择备考学科')
  if (!createForm.value.exam_date) return ElMessage.warning('请选择考试日期')
  generating.value = true
  try {
    const res: any = await planApi.generate(createForm.value)
    plan.value = res.data
    showCreate.value = false
    await loadPlan()
    ElMessage.success('学习计划已生成')
  } finally {
    generating.value = false
  }
}

async function toggleTask(task: any) {
  await planApi.markTaskDone(task.id, !task.is_done)
  task.is_done = !task.is_done
}

onMounted(loadPlan)
onUnmounted(() => clearInterval(timer))
</script>
