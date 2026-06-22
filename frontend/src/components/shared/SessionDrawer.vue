<template>
  <!-- 移动端会话列表抽屉（底部弹出） -->
  <el-drawer
    :model-value="modelValue"
    :title="'历史对话'"
    direction="btt"
    :size="350"
    :destroy-on-close="true"
    class="session-drawer md:hidden"
    @update:model-value="$emit('update:modelValue', $event)"
    @open="$emit('open')"
    @close="$emit('close')"
  >
    <div class="space-y-3 h-full flex flex-col">
      <!-- 新对话按钮 -->
      <el-button type="primary" size="small" class="w-full" @click="handleNewChat">
        + 新对话
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

      <!-- 会话列表 -->
      <div class="flex-1 overflow-y-auto space-y-1">
        <div v-if="filteredSessions.length === 0" class="text-center py-8 text-gray-400 text-sm">
          暂无历史对话
        </div>

        <!-- 按学科分组 -->
        <template v-if="filterSubject === '全部'">
          <template v-for="(group, subject) in groupedSessions" :key="subject">
            <div class="flex items-center gap-1 px-1 pt-2 pb-0.5">
              <span class="text-xs font-semibold text-gray-400 uppercase">{{ subject }}</span>
              <span class="text-xs text-gray-300">({{ group.length }})</span>
            </div>
            <button
              v-for="s in group"
              :key="s.id"
              @click="handleSelectSession(s.id)"
              class="w-full text-left p-2 rounded-lg text-sm transition-colors group"
              :class="currentSessionId === s.id ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50 text-gray-600'"
            >
              <p class="font-medium truncate">{{ s.title }}</p>
              <p class="text-xs text-gray-400">{{ s.message_count }} 条</p>
              <button
                @click.stop="handleDeleteSession(s)"
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
            v-for="s in filteredSessions"
            :key="s.id"
            @click="handleSelectSession(s.id)"
            class="w-full text-left p-2 rounded-lg text-sm transition-colors group"
            :class="currentSessionId === s.id ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50 text-gray-600'"
          >
            <p class="font-medium truncate">{{ s.title }}</p>
            <p class="text-xs text-gray-400">{{ s.subject }} · {{ s.message_count }} 条</p>
            <button
              @click.stop="handleDeleteSession(s)"
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

interface Session {
  id: string
  title: string
  subject: string
  message_count: number
}

const props = defineProps<{
  modelValue: boolean
  sessions: Session[]
  currentSessionId: string | null
  subjects: string[]
}>()

const emit = defineEmits<{
  'update:modelValue': [boolean]
  'new-chat': []
  'select-session': [id: string]
  'delete-session': [session: Session]
  'filter-subject': [subject: string]
}>()

const filterSubject = ref('全部')

const groupedSessions = computed(() => {
  const groups: Record<string, Session[]> = {}
  props.sessions.forEach(s => {
    if (!groups[s.subject]) groups[s.subject] = []
    groups[s.subject].push(s)
  })
  return groups
})

const filteredSessions = computed(() => {
  if (!filterSubject.value || filterSubject.value === '全部') {
    return props.sessions
  }
  return props.sessions.filter(s => s.subject === filterSubject.value)
})

const handleNewChat = () => {
  emit('new-chat')
}

const handleSelectSession = (id: string) => {
  emit('select-session', id)
}

const handleDeleteSession = (session: Session) => {
  emit('delete-session', session)
}

const handleFilterSubject = (subject: string) => {
  filterSubject.value = subject
}
</script>

<style scoped>
:deep(.el-drawer) {
  border-radius: 12px 12px 0 0;
}
</style>
