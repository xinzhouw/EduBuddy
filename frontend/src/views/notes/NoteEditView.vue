<template>
  <div class="space-y-4">
    <div class="card">
      <div class="flex items-center gap-4 mb-4">
        <el-input v-model="note.title" placeholder="笔记标题" size="large" class="flex-1" @blur="autoSave" />
        <el-select v-model="note.subject" size="large" style="width:120px" @change="autoSave">
          <el-option v-for="s in subjects" :key="s" :label="s" :value="s" />
        </el-select>
        <el-button @click="router.push('/notes')">← 返回</el-button>
      </div>

      <el-input
        v-model="note.content"
        type="textarea"
        :rows="20"
        placeholder="开始写笔记... (支持 Markdown 格式)"
        @blur="autoSave"
        style="font-family: 'JetBrains Mono', monospace; font-size: 14px"
      />

      <div class="flex gap-2 mt-4">
        <el-button @click="aiSummarize" :loading="summarizing" type="primary" plain>🤖 AI总结</el-button>
        <el-button @click="generateFlashcards" :loading="generatingCards" type="success" plain>🃏 生成知识卡片</el-button>
        <el-button @click="saveNote" :loading="saving" type="primary">💾 保存</el-button>
        <el-button @click="deleteNote" type="danger" plain>🗑 删除</el-button>
      </div>
    </div>

    <!-- AI 总结结果 -->
    <div v-if="note.ai_summary" class="card">
      <h3 class="font-semibold text-gray-700 mb-3">🤖 AI 总结</h3>
      <p class="text-sm text-gray-600 whitespace-pre-wrap">{{ note.ai_summary }}</p>
      <div v-if="keyPoints.length > 0" class="mt-3 flex flex-wrap gap-2">
        <span v-for="kp in keyPoints" :key="kp" class="px-2 py-1 bg-blue-50 text-blue-600 rounded text-xs">{{ kp }}</span>
      </div>
    </div>

    <!-- 生成的知识卡片 -->
    <div v-if="flashcards.length > 0" class="card">
      <h3 class="font-semibold text-gray-700 mb-3">🃏 生成的知识卡片（{{ flashcards.length }} 张）</h3>
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
import { notesApi } from '@/api/notes'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const noteId = Number(route.params.id)
const subjects = ['数学', '物理', '化学', '生物', '语文', '英语', '历史', '地理', '政治']
const note = ref<any>({ title: '', subject: '数学', content: '', ai_summary: '', key_points: null })
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
    ElMessage.success('保存成功')
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
  if (!note.value.content.trim()) return ElMessage.warning('笔记内容为空')
  summarizing.value = true
  try {
    const res: any = await notesApi.aiSummarize(noteId)
    note.value.ai_summary = res.data.summary
    note.value.key_points = JSON.stringify(res.data.key_points || [])
    ElMessage.success('AI 总结完成')
  } finally {
    summarizing.value = false
  }
}

async function generateFlashcards() {
  generatingCards.value = true
  try {
    const res: any = await notesApi.generateFlashcards(noteId)
    flashcards.value = res.data.flashcards || []
    ElMessage.success(`生成了 ${flashcards.value.length} 张知识卡片`)
  } finally {
    generatingCards.value = false
  }
}

async function deleteNote() {
  await ElMessageBox.confirm('确认删除这篇笔记？', '删除确认', { type: 'warning' })
  await notesApi.delete(noteId)
  ElMessage.success('已删除')
  router.push('/notes')
}

onMounted(loadNote)
</script>
