<template>
  <!-- 移动端批改历史抽屉（底部弹出） -->
  <el-drawer
    :model-value="modelValue"
    :title="'批改历史'"
    direction="btt"
    :size="350"
    :destroy-on-close="true"
    class="grading-drawer md:hidden"
    @update:model-value="$emit('update:modelValue', $event)"
    @open="$emit('open')"
    @close="$emit('close')"
  >
    <div class="space-y-3 h-full flex flex-col">
      <!-- 新批改按钮 -->
      <el-button type="primary" size="small" class="w-full" @click="handleStartNew">
        + 新批改
      </el-button>

      <!-- 学科过滤 -->
      <div class="flex flex-wrap gap-1">
        <button
          v-for="s in ['全部', ...subjects]"
          :key="s"
          @click="handleFilterSubject(s)"
          class="text-xs px-2 py-0.5 rounded-full border transition-colors"
          :class="filterSubject === s
            ? 'bg-blue-500 text-white border-blue-500'
            : 'bg-white text-gray-500 border-gray-200'"
        >
          {{ s }}
        </button>
      </div>

      <!-- 批改列表 -->
      <div class="flex-1 overflow-y-auto space-y-1">
        <div v-if="filteredItems.length === 0" class="text-center py-8 text-gray-400 text-sm">
          暂无批改记录
        </div>

        <!-- 按学科分组 -->
        <template v-if="filterSubject === '全部'">
          <template v-for="(group, subject) in groupedItems" :key="subject">
            <div class="flex items-center gap-1 px-1 pt-2 pb-0.5">
              <span class="text-xs font-semibold text-gray-400 uppercase">{{ subject }}</span>
              <span class="text-xs text-gray-300">({{ group.length }})</span>
            </div>
            <button
              v-for="item in group"
              :key="item.id"
              @click="handleSelectGrading(item.id)"
              class="w-full text-left p-2 rounded-lg text-sm transition-colors group"
              :class="currentGradingId === item.id ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50 text-gray-600'"
            >
              <div class="flex items-center gap-1.5 pr-6">
                <span class="text-xs px-1.5 py-0.5 rounded-md font-medium"
                  :class="subjectColorClass(item.subject)">{{ item.subject }}</span>
                <p class="font-medium truncate flex-1">{{ item.title }}</p>
              </div>
              <div class="flex items-center gap-2 mt-0.5">
                <span v-if="item.score !== null && item.score !== undefined"
                  class="text-xs font-bold"
                  :class="scoreColorClass(item.score)">
                  {{ item.score.toFixed(0) }}分
                </span>
                <span v-else class="text-xs text-gray-400">待批改</span>
                <span class="text-xs text-gray-400">{{ formatDate(item.created_at) }}</span>
              </div>
              <button
                @click.stop="handleDeleteGrading(item)"
                class="hidden group-hover:block text-red-500 text-xs mt-1"
              >
                删除
              </button>
            </button>
          </template>
        </template>

        <!-- 单一学科显示 -->
        <template v-else>
          <button
            v-for="item in filteredItems"
            :key="item.id"
            @click="handleSelectGrading(item.id)"
            class="w-full text-left p-2 rounded-lg text-sm transition-colors group"
            :class="currentGradingId === item.id ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50 text-gray-600'"
          >
            <div class="flex items-center gap-1.5 pr-6">
              <span class="text-xs px-1.5 py-0.5 rounded-md font-medium"
                :class="subjectColorClass(item.subject)">{{ item.subject }}</span>
              <p class="font-medium truncate flex-1">{{ item.title }}</p>
            </div>
            <div class="flex items-center gap-2 mt-0.5">
              <span v-if="item.score !== null && item.score !== undefined"
                class="text-xs font-bold"
                :class="scoreColorClass(item.score)">
                {{ item.score.toFixed(0) }}分
              </span>
              <span v-else class="text-xs text-gray-400">待批改</span>
              <span class="text-xs text-gray-400">{{ formatDate(item.created_at) }}</span>
            </div>
            <button
              @click.stop="handleDeleteGrading(item)"
              class="hidden group-hover:block text-red-500 text-xs mt-1"
            >
              删除
            </button>
          </button>
        </template>
      </div>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface GradingItem {
  id: number
  title: string
  subject: string
  score: number | null
  created_at: string
}

const props = defineProps<{
  modelValue: boolean
  historyList: GradingItem[]
  currentGradingId: number | null
  subjects: string[]
}>()

const emit = defineEmits<{
  'update:modelValue': [boolean]
  'start-new': []
  'select-grading': [id: number]
  'delete-grading': [item: GradingItem]
  'filter-subject': [subject: string]
}>()

const filterSubject = ref('全部')

const groupedItems = computed(() => {
  const groups: Record<string, GradingItem[]> = {}
  props.historyList.forEach(item => {
    if (!groups[item.subject]) groups[item.subject] = []
    groups[item.subject].push(item)
  })
  return groups
})

const filteredItems = computed(() => {
  if (!filterSubject.value || filterSubject.value === '全部') {
    return props.historyList
  }
  return props.historyList.filter(item => item.subject === filterSubject.value)
})

const handleStartNew = () => {
  emit('start-new')
}

const handleSelectGrading = (id: number) => {
  emit('select-grading', id)
}

const handleDeleteGrading = (item: GradingItem) => {
  emit('delete-grading', item)
}

const handleFilterSubject = (subject: string) => {
  filterSubject.value = subject
}

function formatDate(iso: string) {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return d.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
}

function scoreColorClass(score: number) {
  if (score >= 90) return 'text-green-600'
  if (score >= 75) return 'text-blue-600'
  if (score >= 60) return 'text-amber-600'
  return 'text-red-500'
}

function subjectColorClass(subject: string) {
  const map: Record<string, string> = {
    数学: 'bg-blue-100 text-blue-700',
    物理: 'bg-purple-100 text-purple-700',
    化学: 'bg-green-100 text-green-700',
    生物: 'bg-emerald-100 text-emerald-700',
    语文: 'bg-red-100 text-red-700',
    英语: 'bg-sky-100 text-sky-700',
    历史: 'bg-amber-100 text-amber-700',
    地理: 'bg-teal-100 text-teal-700',
    政治: 'bg-orange-100 text-orange-700',
  }
  return map[subject] || 'bg-gray-100 text-gray-600'
}
</script>

<style scoped>
:deep(.el-drawer) {
  border-radius: 12px 12px 0 0;
}
</style>
