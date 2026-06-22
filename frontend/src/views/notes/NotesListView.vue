<template>
  <div class="space-y-3 sm:space-y-4">
    <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
      <div class="flex items-center gap-2">
        <el-select v-model="filterSubject" placeholder="全部学科" clearable size="small" style="width:100px" @change="loadNotes">
          <el-option v-for="s in subjects" :key="s" :label="s" :value="s" />
        </el-select>
      </div>
      <el-button type="primary" @click="createNote" size="small" class="w-full sm:w-auto">+ 新建笔记</el-button>
    </div>

    <div v-if="loading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
      <el-skeleton v-for="i in 6" :key="i" :rows="3" animated class="card" />
    </div>

    <div v-else-if="notes.length === 0" class="text-center py-12 sm:py-16 text-gray-400">
      <span class="text-4xl sm:text-5xl">📝</span>
      <p class="mt-3 sm:mt-4 text-base sm:text-lg">还没有笔记，记录你的第一篇笔记吧</p>
      <el-button type="primary" class="mt-3 sm:mt-4" @click="createNote" size="small">新建笔记</el-button>
    </div>

    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
      <div v-for="note in notes" :key="note.id" class="card-hover"
        @click="router.push(`/notes/${note.id}/edit`)">
        <div class="flex items-start justify-between mb-3">
          <h3 class="font-semibold text-gray-800 truncate flex-1">{{ note.title }}</h3>
          <span class="ml-2 px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700 shrink-0">{{ note.subject }}</span>
        </div>
        <p v-if="note.ai_summary" class="text-sm text-gray-500 line-clamp-2 mb-3">{{ note.ai_summary }}</p>
        <p v-else class="text-sm text-gray-400 line-clamp-2 mb-3">{{ stripMarkdown(note.content) }}</p>
        <p class="text-xs text-gray-400">{{ formatDate(note.updated_at) }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { notesApi } from '@/api/notes'

const router = useRouter()
const notes = ref<any[]>([])
const loading = ref(false)
const filterSubject = ref('')
const subjects = ['数学', '物理', '化学', '生物', '语文', '英语', '历史', '地理', '政治']

function stripMarkdown(text: string) {
  return text.replace(/[#*`\[\]()>]/g, '').trim().slice(0, 100)
}

function formatDate(dt: string) {
  return new Date(dt).toLocaleDateString('zh-CN')
}

async function loadNotes() {
  loading.value = true
  try {
    const res: any = await notesApi.list({ subject: filterSubject.value || undefined })
    notes.value = res.data.items || []
  } finally {
    loading.value = false
  }
}

async function createNote() {
  const res: any = await notesApi.create({ title: '新笔记', subject: '数学', content: '' })
  router.push(`/notes/${res.data.id}/edit`)
}

onMounted(loadNotes)
</script>
