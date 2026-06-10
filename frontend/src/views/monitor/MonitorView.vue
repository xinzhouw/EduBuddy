<template>
  <div class="space-y-6">

    <!-- 页面标题 -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">
          {{ authStore.user?.role === 'teacher' ? '🏫 班级学生监督' : '👪 子女学习监督' }}
        </h1>
        <p class="text-sm text-gray-500 mt-1">查看关联学生的学习状况</p>
      </div>
      <RouterLink
        to="/profile"
        class="text-sm text-blue-500 hover:text-blue-700 font-medium transition-colors"
      >
        + 添加学生
      </RouterLink>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="flex items-center justify-center py-20 text-gray-400">
      <span class="animate-spin mr-2">⏳</span> 加载中…
    </div>

    <!-- 无数据 -->
    <div v-else-if="students.length === 0" class="flex flex-col items-center justify-center py-20 text-gray-400">
      <div class="w-20 h-20 bg-gray-50 rounded-2xl flex items-center justify-center text-4xl mb-4">👤</div>
      <p class="text-gray-500 font-medium">暂无关联学生</p>
      <p class="text-sm mt-1">前往「个人中心」添加学生</p>
      <RouterLink to="/profile" class="mt-3 px-4 py-2 rounded-xl bg-blue-500 text-white text-sm font-medium hover:bg-blue-600 transition-colors">
        去关联学生
      </RouterLink>
    </div>

    <!-- 学生卡片列表 -->
    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
      <div
        v-for="stu in students"
        :key="stu.student_id"
        class="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 hover:shadow-md transition-shadow cursor-pointer group"
        @click="goToDetail(stu.student_id)"
      >
        <!-- 头部：头像 + 基本信息 -->
        <div class="flex items-center gap-3 mb-4">
          <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-400 to-indigo-500 flex items-center justify-center text-white font-black text-lg shrink-0">
            {{ stu.nickname?.[0]?.toUpperCase() || '?' }}
          </div>
          <div class="flex-1 min-w-0">
            <p class="font-bold text-gray-800 truncate">{{ stu.nickname }}</p>
            <p class="text-xs text-gray-400">
              {{ stu.grade }}
              <span v-if="stu.class_name"> · {{ stu.class_name }}</span>
            </p>
          </div>
          <!-- 最后活跃时间 -->
          <div class="text-right shrink-0">
            <p class="text-xs text-gray-400">
              {{ stu.last_login_date ? `${stu.last_login_date} 活跃` : '未登录' }}
            </p>
          </div>
        </div>

        <!-- 统计数据 -->
        <div class="grid grid-cols-3 gap-3 mb-4">
          <div class="text-center">
            <p class="text-lg font-bold text-blue-600">{{ stu.today_study_minutes }}<span class="text-xs font-normal text-gray-400">min</span></p>
            <p class="text-xs text-gray-500 mt-0.5">今日学习</p>
          </div>
          <div class="text-center">
            <p class="text-lg font-bold text-orange-500">{{ stu.streak_days }}<span class="text-xs font-normal text-gray-400">天</span></p>
            <p class="text-xs text-gray-500 mt-0.5">连续打卡</p>
          </div>
          <div class="text-center">
            <p class="text-lg font-bold text-green-600">{{ Math.round((stu.completion_rate_7d || 0) * 100) }}<span class="text-xs font-normal text-gray-400">%</span></p>
            <p class="text-xs text-gray-500 mt-0.5">7天完成率</p>
          </div>
        </div>

        <!-- 完成率进度条 -->
        <div class="h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <div
            class="h-full rounded-full transition-all duration-700"
            :class="completionBarColor(stu.completion_rate_7d)"
            :style="`width: ${Math.round((stu.completion_rate_7d || 0) * 100)}%`"
          ></div>
        </div>

        <!-- 查看详情 -->
        <div class="mt-4 flex items-center justify-end text-xs text-blue-400 group-hover:text-blue-600 transition-colors font-medium">
          查看详情 →
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { monitorApi } from '@/api/relations'

const authStore = useAuthStore()
const router = useRouter()

const students = ref<any[]>([])
const loading = ref(true)

function completionBarColor(rate: number) {
  if (rate >= 0.8) return 'bg-green-500'
  if (rate >= 0.5) return 'bg-amber-500'
  return 'bg-red-400'
}

function goToDetail(studentId: number) {
  router.push(`/monitor/students/${studentId}`)
}

onMounted(async () => {
  try {
    const res: any = await monitorApi.getStudentsSummary()
    students.value = res.data || []
  } catch {}
  loading.value = false
})
</script>
