<template>
  <!-- Mobile session list drawer (slides up from bottom) -->
  <el-drawer
    :model-value="modelValue"
    :title="$t('ai_chat.history_title')"
    direction="btt"
    :size="350"
    :destroy-on-close="true"
    class="session-drawer md:hidden"
    @update:model-value="$emit('update:modelValue', $event)"
    @open="$emit('open')"
    @close="$emit('close')"
  >
    <div class="space-y-3 h-full flex flex-col">
      <!-- New chat button -->
      <el-button type="primary" size="small" class="w-full" @click="handleNewChat">
        {{ $t('ai_chat.new_chat') }}
      </el-button>

      <!-- Subject filter -->
      <div class="flex flex-wrap gap-1">
        <button
          v-for="s in ['', ...subjects]"
          :key="s"
          @click="handleFilterSubject(s)"
          class="text-xs px-2 py-0.5 rounded-full border transition-colors"
          :class="filterSubject === s
            ? 'bg-blue-500 text-white border-blue-500'
            : 'bg-white text-gray-500 border-gray-200'"
        >
          {{ s || $t('ai_chat.filter_all') }}
        </button>
      </div>

      <!-- Session list -->
      <div class="flex-1 overflow-y-auto space-y-1">
        <div v-if="filteredSessions.length === 0" class="text-center py-8 text-gray-400 text-sm">
          {{ $t('ai_chat.no_history') }}
        </div>

        <!-- Grouped by subject -->
        <template v-if="filterSubject === ''">
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
              <p class="text-xs text-gray-400">{{ s.message_count }} {{ $t('ai_chat.message_count_unit') }}</p>
              <button
                @click.stop="handleDeleteSession(s)"
                class="hidden group-hover:block text-red-500 text-xs mt-1"
              >
                {{ $t('common.delete') }}
              </button>
            </button>
          </template>
        </template>

        <!-- Single subject display -->
        <template v-else>
          <button
            v-for="s in filteredSessions"
            :key="s.id"
            @click="handleSelectSession(s.id)"
            class="w-full text-left p-2 rounded-lg text-sm transition-colors group"
            :class="currentSessionId === s.id ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50 text-gray-600'"
          >
            <p class="font-medium truncate">{{ s.title }}</p>
            <p class="text-xs text-gray-400">{{ s.subject }} · {{ s.message_count }} {{ $t('ai_chat.message_count_unit') }}</p>
            <button
              @click.stop="handleDeleteSession(s)"
              class="hidden group-hover:block text-red-500 text-xs mt-1"
            >
              {{ $t('common.delete') }}
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

const filterSubject = ref('')

const groupedSessions = computed(() => {
  const groups: Record<string, Session[]> = {}
  props.sessions.forEach(s => {
    if (!groups[s.subject]) groups[s.subject] = []
    groups[s.subject].push(s)
  })
  return groups
})

const filteredSessions = computed(() => {
  if (!filterSubject.value) {
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
