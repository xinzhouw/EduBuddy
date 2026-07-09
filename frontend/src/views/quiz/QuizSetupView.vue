<template>
  <div class="max-w-2xl mx-auto">
    <div class="card space-y-6">
      <h2 class="text-xl font-bold text-gray-800">📚 {{ $t('quiz.page_title') }}</h2>

      <!-- Scan input area -->
      <div class="border-2 border-dashed rounded-xl p-4 transition-colors"
        :class="isDragging ? 'border-blue-400 bg-blue-50' : 'border-gray-200 bg-gray-50 hover:border-blue-300'"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="onDrop">
        <div v-if="!scanning && !scanResult" class="text-center">
          <p class="text-2xl mb-1">📷</p>
          <p class="text-sm font-medium text-gray-700 mb-1">{{ $t('quiz.scan_title') }}</p>
          <p class="text-xs text-gray-400 mb-3">{{ $t('quiz.scan_hint') }}</p>
          <label class="inline-block cursor-pointer">
            <input
              ref="fileInputRef"
              type="file"
              class="hidden"
              accept=".jpg,.jpeg,.png,.gif,.webp,.pdf,.docx"
              @change="onFileChange"
            />
            <span class="px-4 py-2 rounded-lg bg-blue-500 text-white text-sm font-medium hover:bg-blue-600 transition-colors">
              {{ $t('quiz.choose_file') }}
            </span>
          </label>
        </div>

        <!-- Recognizing -->
        <div v-else-if="scanning" class="text-center py-2">
          <div class="inline-block w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mb-2"></div>
          <p class="text-sm text-gray-600">{{ $t('quiz.recognizing') }}</p>
        </div>

        <!-- Recognition result -->
        <div v-else-if="scanResult" class="space-y-3">
          <div class="flex items-start justify-between gap-2">
            <div class="flex items-center gap-2">
              <span class="text-green-500 text-lg">✅</span>
              <span class="text-sm font-medium text-gray-700">{{ $t('quiz.recognize_success') }}</span>
            </div>
            <button class="text-xs text-gray-400 hover:text-red-500 transition-colors flex-shrink-0" @click="clearScan">
              ✕ {{ $t('quiz.clear_btn') }}
            </button>
          </div>

          <!-- Recognized text -->
          <div v-if="scanResult.recognized_text" class="bg-white border border-gray-200 rounded-lg p-3 max-h-36 overflow-y-auto">
            <p class="text-xs text-gray-400 mb-1">{{ $t('quiz.recognized_content') }}</p>
            <div class="text-sm text-gray-700 leading-relaxed latex-content" v-html="renderRecognizedText(scanResult.recognized_text)"></div>
          </div>

          <div class="grid grid-cols-2 gap-3 text-sm">
            <div class="bg-blue-50 rounded-lg px-3 py-2">
              <span class="text-gray-500 text-xs">{{ $t('quiz.subject_label') }}</span>
              <p class="font-semibold text-blue-700">{{ scanResult.subject }}</p>
            </div>
            <div class="bg-purple-50 rounded-lg px-3 py-2">
              <span class="text-gray-500 text-xs">{{ $t('quiz.topic_label') }}</span>
              <p class="font-semibold text-purple-700">{{ scanResult.topic }}</p>
            </div>
          </div>

          <div class="flex gap-2">
            <button class="flex-1 text-xs text-center py-2 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 transition-colors" @click="clearScan">
              {{ $t('quiz.reupload_btn') }}
            </button>
            <button class="flex-1 text-xs text-center py-2 rounded-lg bg-blue-50 text-blue-600 font-medium hover:bg-blue-100 transition-colors" @click="applyToForm">
              ✔ {{ $t('quiz.apply_btn') }}
            </button>
          </div>
        </div>
      </div>

      <div class="flex items-center gap-2 text-gray-300">
        <div class="flex-1 h-px bg-gray-200"></div>
        <span class="text-xs">{{ $t('quiz.manual_fill') }}</span>
        <div class="flex-1 h-px bg-gray-200"></div>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-600 mb-1">{{ $t('quiz.subject_label') }}</label>
          <el-select v-model="form.subject" class="w-full">
            <el-option v-for="s in subjects" :key="s.key" :label="$t('subjects.' + s.key)" :value="s.value" />
          </el-select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-600 mb-1">{{ $t('quiz.topic_label') }}</label>
          <el-input v-model="form.topic" :placeholder="$t('quiz.topic_placeholder')" />
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-600 mb-2">{{ $t('quiz.difficulty_label') }}</label>
        <div class="grid grid-cols-4 gap-3">
          <button v-for="d in difficulties" :key="d.value"
            @click="form.difficulty = d.value"
            class="p-3 rounded-lg border-2 text-center transition-all"
            :class="form.difficulty === d.value ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'">
            <p class="text-lg">{{ d.icon }}</p>
            <p class="text-xs font-medium mt-1">{{ $t('quiz.' + d.key) }}</p>
          </button>
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-600 mb-2">{{ $t('quiz.question_type_label') }}</label>
        <div class="flex flex-wrap gap-2">
          <el-checkbox v-for="qt in questionTypes" :key="qt.value" v-model="qt.checked" :label="$t('quiz.type_' + qt.value)" />
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-600 mb-1">{{ $t('quiz.question_count_label') }}</label>
        <el-select v-model="form.count" style="width:100px">
          <el-option v-for="n in [3, 5, 10, 15]" :key="n" :label="n + $t('quiz.question_count_unit')" :value="n" />
        </el-select>
      </div>

      <el-button type="primary" size="large" class="w-full" :loading="loading" @click="startQuiz">
        🚀 {{ $t('quiz.start_btn') }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { quizApi } from '@/api/quiz'
import { ElMessage } from 'element-plus'
import { renderRecognizedText } from '@/utils/markdown'

const router = useRouter()
const { t, getLocaleMessage } = useI18n()
const loading = ref(false)

// Subject keys match zh.json subjects section; API expects Chinese names
const subjectKeys = ['math', 'physics', 'chemistry', 'biology', 'chinese', 'english', 'history', 'geography', 'politics']
const zhMessages = getLocaleMessage('zh') as any
const subjects = subjectKeys.map(key => ({ key, value: zhMessages.subjects[key] as string }))

const difficulties = [
  { value: 1, icon: '🌱', key: 'difficulty_easy' },
  { value: 2, icon: '📘', key: 'difficulty_medium' },
  { value: 3, icon: '🔥', key: 'difficulty_hard' },
  { value: 4, icon: '🏆', key: 'difficulty_challenge' },
]
const questionTypes = reactive([
  { value: 'single_choice', checked: true },
  { value: 'fill_blank', checked: true },
  { value: 'true_false', checked: false },
  { value: 'subjective', checked: false },
])
const form = reactive({ subject: subjects[0].value, topic: '', difficulty: 2, count: 5 })

// ===== Scan recognition state =====
const fileInputRef = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)
const scanning = ref(false)
const scanResult = ref<{
  subject: string
  topic: string
  recognized_text: string
  question_count: number
} | null>(null)

// Infer MIME type from file extension (for drag-drop where file.type may be empty)
function inferMimeType(file: File): string {
  if (file.type) return file.type
  const ext = file.name.split('.').pop()?.toLowerCase() || ''
  const extMap: Record<string, string> = {
    jpg: 'image/jpeg',
    jpeg: 'image/jpeg',
    png: 'image/png',
    gif: 'image/gif',
    webp: 'image/webp',
    pdf: 'application/pdf',
    docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  }
  return extMap[ext] || ''
}

async function handleFile(file: File) {
  const allowed = [
    'image/jpeg', 'image/png', 'image/gif', 'image/webp',
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  ]
  const mimeType = inferMimeType(file)
  if (!allowed.includes(mimeType)) {
    ElMessage.warning(t('quiz.unsupported_file'))
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.warning(t('quiz.file_too_large'))
    return
  }

  scanning.value = true
  scanResult.value = null
  try {
    const res: any = await quizApi.extractTopicFromFile(file)
    if (res?.code === 200 && res.data) {
      scanResult.value = res.data
      // Auto-fill form
      applyToFormFromResult(res.data)
      ElMessage.success(t('quiz.recognize_ok'))
    } else {
      ElMessage.error(t('quiz.recognize_failed'))
    }
  } catch (e: any) {
    const msg = e?.response?.data?.detail || t('quiz.recognize_failed')
    ElMessage.error(msg)
  } finally {
    scanning.value = false
    // Reset input to allow selecting the same file again
    if (fileInputRef.value) fileInputRef.value.value = ''
  }
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files && input.files[0]) {
    handleFile(input.files[0])
  }
}

function onDrop(e: DragEvent) {
  isDragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) handleFile(file)
}

function applyToFormFromResult(result: typeof scanResult.value) {
  if (!result) return
  if (subjects.some(s => s.value === result.subject)) {
    form.subject = result.subject
  }
  if (result.topic) {
    form.topic = result.topic
  }
}

function applyToForm() {
  applyToFormFromResult(scanResult.value)
  ElMessage.success(t('common.success'))
}

function clearScan() {
  scanResult.value = null
  scanning.value = false
}

// ===== Start quiz =====
async function startQuiz() {
  if (!form.topic.trim()) return ElMessage.warning(t('error.required_field'))
  const selectedTypes = questionTypes.filter(qt => qt.checked).map(qt => qt.value)
  if (selectedTypes.length === 0) return ElMessage.warning(t('error.required_field'))

  loading.value = true
  try {
    const res: any = await quizApi.generate({
      subject: form.subject,
      topic: form.topic,
      difficulty: form.difficulty,
      question_types: selectedTypes,
      count: form.count,
    })
    // Store data in sessionStorage then navigate
    sessionStorage.setItem('quizSession', JSON.stringify(res.data))
    router.push('/quiz/session')
  } finally {
    loading.value = false
  }
}
</script>
