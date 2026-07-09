<template>
  <div class="space-y-4">
    <div class="card">
      <div class="flex items-center gap-4 mb-4">
        <el-input v-model="note.title" :placeholder="$t('notes.title_placeholder')" size="large" class="flex-1" @blur="autoSave" />
        <el-select v-model="note.subject" size="large" style="width:120px" @change="autoSave">
          <el-option v-for="s in subjects" :key="s" :label="s" :value="s" />
        </el-select>
        <el-button @click="router.push('/notes')">← {{ $t('notes.back') }}</el-button>
      </div>

      <el-input
        v-model="note.content"
        type="textarea"
        :rows="20"
        :placeholder="$t('notes.content_placeholder')"
        @blur="autoSave"
        style="font-family: 'JetBrains Mono', monospace; font-size: 14px"
      />

      <div class="flex gap-2 mt-4">
        <el-button @click="aiSummarize" :loading="summarizing" type="primary" plain>🤖 {{ $t('notes.ai_summary') }}</el-button>
        <el-button @click="generateFlashcards" :loading="generatingCards" type="success" plain>🃏 {{ $t('notes.generate_flashcards') }}</el-button>
        <el-button @click="saveNote" :loading="saving" type="primary">💾 {{ $t('notes.save') }}</el-button>
        <el-button @click="deleteNote" type="danger" plain>🗑 {{ $t('notes.delete') }}</el-button>
      </div>
    </div>

    <!-- AI summary result -->
    <div v-if="note.ai_summary" class="card">
      <h3 class="font-semibold text-gray-700 mb-3">🤖 {{ $t('notes.ai_summary_title') }}</h3>
      <p class="text-sm text-gray-600 whitespace-pre-wrap">{{ note.ai_summary }}</p>
      <div v-if="keyPoints.length > 0" class="mt-3 flex flex-wrap gap-2">
        <span v-for="kp in keyPoints" :key="kp" class="px-2 py-1 bg-blue-50 text-blue-600 rounded text-xs">{{ kp }}</span>
      </div>
    </div>

    <!-- Generated flashcards -->
    <div v-if="flashcards.length > 0" class="card">
      <h3 class="font-semibold text-gray-700 mb-3">🃏 {{ $t('notes.flashcards_title') }}（{{ flashcards.length }} {{ $t('notes.flashcards_unit') }}）</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div v-for="(fc, i) in flashcards" :key="i" class="border border-gray-200 rounded-lg p-3">
          <p class="text-sm font-medium text-gray-700">Q: {{ fc.front }}</p>
          <p class="text-sm text-gray-500 mt-2">A: {{ fc.back }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { notesApi } from '@/api/notes'
import { ElMessage, ElMessageBox } from 'element-plus'

const { t } = useI18n()

const route = useRoute()
const router = useRouter()
const noteId = Number(route.params.id)

const subjects = computed(() => [
  t('subjects.math'),
  t('subjects.physics'),
  t('subjects.chemistry'),
  t('subjects.biology'),
  t('subjects.chinese'),
  t('subjects.english'),
  t('subjects.history'),
  t('subjects.geography'),
  t('subjects.politics'),
])

const note = ref<any>({ title: '', subject: t('subjects.math'), content: '', ai_summary: '', key_points: null })
const saving = ref(false)
const summarizing = ref(false)
const generatingCards = ref(false)
const flashcards = ref<any[]>([])

const keyPoints = computed(() => {
  try { return JSON.parse(note.value.key_points || '[]') } catch { return [] }
})

async function loadNote() {
  const res: any = await notesApi.get(noteId)
  note.value = res.data
}

async function saveNote() {
  saving.value = true
  try {
    await notesApi.update(noteId, { title: note.value.title, content: note.value.content, subject: note.value.subject })
    ElMessage.success(t('notes.save_success'))
  } finally {
    saving.value = false
  }
}

let saveTimer: any = null
function autoSave() {
  clearTimeout(saveTimer)
  saveTimer = setTimeout(saveNote, 2000)
}

async function aiSummarize() {
  if (!note.value.content.trim()) return ElMessage.warning(t('notes.content_empty'))
  summarizing.value = true
  try {
    const res: any = await notesApi.aiSummarize(noteId)
    note.value.ai_summary = res.data.summary
    note.value.key_points = JSON.stringify(res.data.key_points || [])
    ElMessage.success(t('notes.summary_success'))
  } finally {
    summarizing.value = false
  }
}

async function generateFlashcards() {
  generatingCards.value = true
  try {
    const res: any = await notesApi.generateFlashcards(noteId)
    flashcards.value = res.data.flashcards || []
    ElMessage.success(t('notes.flashcards_success', { count: flashcards.value.length }))
  } finally {
    generatingCards.value = false
  }
}

async function deleteNote() {
  await ElMessageBox.confirm(t('notes.delete_confirm'), t('notes.delete_confirm_title'), { type: 'warning' })
  await notesApi.delete(noteId)
  ElMessage.success(t('notes.delete_success'))
  router.push('/notes')
}

onMounted(loadNote)
</script>
