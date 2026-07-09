<template>
  <div class="max-w-3xl mx-auto space-y-4">
    <!-- Answering questions -->
    <template v-if="!submitted">
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <span class="text-sm text-gray-500">{{ $t('quiz.question_counter', {n: currentIndex + 1, total: questions.length}) }}</span>
          <span class="text-sm text-gray-500">⏱ {{ formatTime(elapsed) }}</span>
        </div>
        <div class="w-full bg-gray-200 rounded-full h-1.5 mb-6">
          <div class="bg-blue-500 h-1.5 rounded-full transition-all" :style="`width: ${((currentIndex + 1) / questions.length) * 100}%`"></div>
        </div>

        <div v-if="currentQ">
          <!-- Question content: supports LaTeX rendering -->
          <div class="text-gray-800 font-medium text-base mb-6 leading-relaxed latex-content"
            v-html="renderLatexOnly(currentQ.content)"></div>

          <!-- Single choice / true-false -->
          <div v-if="currentQ.type === 'single_choice' || currentQ.type === 'true_false'" class="space-y-3">
            <button v-for="(opt, i) in parseOptions(currentQ.options)" :key="i"
              @click="selectAnswer(opt)"
              class="w-full text-left p-3.5 rounded-lg border-2 transition-all text-sm latex-content"
              :class="answers[currentQ.id] === extractOptionKey(opt)
                ? 'border-blue-500 bg-blue-50 text-blue-700'
                : 'border-gray-200 hover:border-gray-300'"
              v-html="renderLatexOnly(opt)">
            </button>
          </div>

          <!-- Multiple choice -->
          <div v-else-if="currentQ.type === 'multiple_choice'" class="space-y-3">
            <button v-for="(opt, i) in parseOptions(currentQ.options)" :key="i"
              @click="toggleMultiAnswer(opt)"
              class="w-full text-left p-3.5 rounded-lg border-2 transition-all text-sm latex-content"
              :class="isMultiSelected(opt)
                ? 'border-blue-500 bg-blue-50 text-blue-700'
                : 'border-gray-200 hover:border-gray-300'"
              v-html="renderLatexOnly(opt)">
            </button>
          </div>

          <!-- Fill-in / short answer -->
          <div v-else>
            <!-- Toolbar: math symbols + image recognition -->
            <div class="math-toolbar">
              <span class="math-toolbar-label">{{ $t('quiz.insert_symbol') }}</span>
              <button
                v-for="sym in mathSymbols" :key="sym.label"
                class="math-sym-btn"
                :title="sym.label"
                @click="insertSymbol(sym.value)"
              >{{ sym.display }}</button>
              <!-- Divider -->
              <span class="toolbar-sep"></span>
              <!-- Image recognition button -->
              <label class="scan-answer-btn" :class="{ 'scanning': scanningAnswer }" :title="scanningAnswer ? $t('quiz.recognizing') : $t('quiz.scan_answer')">
                <input
                  type="file"
                  class="hidden"
                  accept="image/jpeg,image/png,image/gif,image/webp"
                  :disabled="scanningAnswer"
                  @change="onAnswerImageChange"
                />
                <span v-if="!scanningAnswer">{{ $t('quiz.scan_answer') }}</span>
                <span v-else class="flex items-center gap-1">
                  <span class="inline-block w-3 h-3 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></span>
                  {{ $t('quiz.recognizing_short') }}
                </span>
              </label>
            </div>
            <el-input
              :ref="(el: any) => inputRef = el"
              v-model="answers[currentQ.id]"
              type="textarea"
              :rows="4"
              :placeholder="$t('quiz.answer_placeholder')"
            />
          </div>
        </div>
      </div>

      <div class="flex justify-between">
        <el-button @click="prevQuestion" :disabled="currentIndex === 0">{{ $t('quiz.prev_question') }}</el-button>
        <el-button v-if="currentIndex < questions.length - 1" type="primary" @click="nextQuestion">{{ $t('quiz.next_question') }}</el-button>
        <el-button v-else type="success" @click="submitQuiz" :loading="submitting">{{ $t('quiz.submit_answers') }}</el-button>
      </div>
    </template>

    <!-- Results -->
    <template v-else>
      <div class="card text-center">
        <p class="text-3xl mb-2">🎉</p>
        <h2 class="text-2xl font-bold text-gray-800">{{ $t('quiz.complete_title') }}</h2>
        <div class="flex justify-center gap-8 mt-4">
          <div><p class="text-2xl font-bold text-blue-600">{{ result.correct }}/{{ result.total }}</p><p class="text-sm text-gray-500">{{ $t('quiz.accuracy_label') }}</p></div>
          <div><p class="text-2xl font-bold text-green-600">{{ Math.round(result.accuracy * 100) }}%</p><p class="text-sm text-gray-500">{{ $t('quiz.precision_label') }}</p></div>
          <div><p class="text-2xl font-bold text-gray-600">{{ formatTime(result.time_spent) }}</p><p class="text-sm text-gray-500">{{ $t('quiz.time_spent_label') }}</p></div>
        </div>
        <p v-if="result.wrong_items_added?.length > 0" class="text-sm text-amber-600 mt-3">
          {{ $t('quiz.wrong_added', {n: result.wrong_items_added.length}) }}
        </p>
      </div>

      <div class="space-y-3">
        <div v-for="r in result.results" :key="r.question_id" class="card">
          <div class="flex items-center gap-2 mb-2">
            <span>{{ r.is_correct ? '✅' : '❌' }}</span>
            <span class="text-sm font-medium text-gray-700">{{ $t('quiz.question_n', {n: resultIndex(r.question_id) + 1}) }}</span>
          </div>
          <p v-if="!r.is_correct" class="text-sm text-gray-500 mb-2">
            {{ $t('quiz.your_answer') }}<span class="text-red-500 latex-content" v-html="renderLatexOnly(r.user_answer)"></span> ·
            {{ $t('quiz.correct_answer') }}<span class="text-green-600 latex-content" v-html="renderLatexOnly(r.correct_answer)"></span>
          </p>
          <div v-if="!r.is_correct && r.explanation" class="bg-blue-50 rounded-lg p-3 text-sm text-gray-600">
            <p class="font-medium text-blue-700 mb-1">{{ $t('quiz.ai_explain') }}</p>
            <span class="latex-content" v-html="renderLatexOnly(r.explanation)"></span>
          </div>
        </div>
      </div>

      <div class="flex justify-center gap-4">
        <el-button @click="router.push('/quiz')">{{ $t('quiz.try_again') }}</el-button>
        <el-button type="primary" @click="router.push('/wrong-book')">{{ $t('quiz.view_wrong_book') }}</el-button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { quizApi } from '@/api/quiz'
import { ElMessage } from 'element-plus'
import { renderLatexOnly } from '@/utils/markdown'

const router = useRouter()
const { t } = useI18n()
const quizData = JSON.parse(sessionStorage.getItem('quizSession') || 'null')
if (!quizData) router.push('/quiz')

const questions = ref<any[]>(quizData?.questions || [])
const sessionId = ref(quizData?.session_id || '')
const currentIndex = ref(0)
const answers = ref<Record<number, string>>({})
const elapsed = ref(0)
const submitting = ref(false)
const submitted = ref(false)
const result = ref<any>({})
let timer: any

// textarea el-input ref for inserting math symbols
const inputRef = ref<any>(null)

// ── Image recognition answer ──────────────────────────────────────────────────
const scanningAnswer = ref(false)

async function onAnswerImageChange(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  // Reset input to allow selecting the same file again
  input.value = ''

  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    ElMessage.warning(t('quiz.image_type_warning'))
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.warning(t('quiz.image_too_large_answer'))
    return
  }

  scanningAnswer.value = true
  try {
    // Pass current question text to improve recognition accuracy
    const questionText = currentQ.value?.content || ''
    const res: any = await quizApi.extractAnswerFromFile(file, questionText)
    if (res?.data?.code === 200 && res.data.data?.answer) {
      const { answer, confidence } = res.data.data
      const qid = currentQ.value?.id
      if (qid != null) {
        answers.value[qid] = answer
      }
      if (confidence === 'low') {
        ElMessage.warning(t('quiz.answer_low_confidence'))
      } else {
        ElMessage.success(t('quiz.answer_recognized'))
      }
    } else {
      ElMessage.error(t('quiz.image_recognize_failed'))
    }
  } catch (err: any) {
    const msg = err?.response?.data?.detail || t('quiz.image_recognize_failed')
    ElMessage.error(msg)
  } finally {
    scanningAnswer.value = false
  }
}

const currentQ = computed(() => questions.value[currentIndex.value])

// ── Math symbol list ──────────────────────────────────────────────────────────
const mathSymbols = [
  { label: 'π (pi)',                  display: 'π',   value: 'π' },
  { label: '√ (square root)',         display: '√',   value: '√' },
  { label: '² (squared)',             display: 'x²',  value: '²' },
  { label: '³ (cubed)',               display: 'x³',  value: '³' },
  { label: '≥ (greater or equal)',    display: '≥',   value: '≥' },
  { label: '≤ (less or equal)',       display: '≤',   value: '≤' },
  { label: '≠ (not equal)',           display: '≠',   value: '≠' },
  { label: '× (multiply)',            display: '×',   value: '×' },
  { label: '÷ (divide)',              display: '÷',   value: '÷' },
  { label: '± (plus or minus)',       display: '±',   value: '±' },
  { label: '∞ (infinity)',            display: '∞',   value: '∞' },
  { label: 'α (alpha)',               display: 'α',   value: 'α' },
  { label: 'β (beta)',                display: 'β',   value: 'β' },
  { label: 'θ (theta)',               display: 'θ',   value: 'θ' },
  { label: '∠ (angle)',               display: '∠',   value: '∠' },
  { label: '° (degree)',              display: '°',   value: '°' },
  { label: '∑ (summation)',           display: '∑',   value: '∑' },
  { label: '∈ (element of)',          display: '∈',   value: '∈' },
  { label: '∩ (intersection)',        display: '∩',   value: '∩' },
  { label: '∪ (union)',               display: '∪',   value: '∪' },
]

/**
 * Insert symbol at textarea cursor position using native DOM selectionStart/End
 */
function insertSymbol(sym: string) {
  const qid = currentQ.value?.id
  if (qid == null) return

  // Try to get the underlying textarea DOM element
  const textarea: HTMLTextAreaElement | null =
    inputRef.value?.$el?.querySelector('textarea') ?? null

  if (textarea) {
    const start = textarea.selectionStart ?? (answers.value[qid] ?? '').length
    const end   = textarea.selectionEnd   ?? start
    const before = (answers.value[qid] ?? '').slice(0, start)
    const after  = (answers.value[qid] ?? '').slice(end)
    answers.value[qid] = before + sym + after
    // Restore cursor position after inserted symbol
    nextTick(() => {
      textarea.focus()
      const pos = start + sym.length
      textarea.setSelectionRange(pos, pos)
    })
  } else {
    // Fallback: append to end
    answers.value[qid] = (answers.value[qid] ?? '') + sym
  }
}

// ── Option helpers ────────────────────────────────────────────────────────────

function formatTime(s: number) {
  const m = Math.floor(s / 60)
  const sec = s % 60
  return `${m}:${sec.toString().padStart(2, '0')}`
}

function parseOptions(opts: any): string[] {
  if (!opts) return []
  try { return typeof opts === 'string' ? JSON.parse(opts) : opts } catch { return [] }
}

/**
 * Extract letter key from option text, e.g.:
 *   "A. option1" → "A"
 *   "A、option1" → "A"
 *   "true"       → "true" (true/false questions kept as-is)
 */
function extractOptionKey(opt: string): string {
  const match = opt.match(/^([A-Za-z])[.、．\s]/)
  return match ? match[1].toUpperCase() : opt
}

function selectAnswer(opt: string) {
  answers.value[currentQ.value.id] = extractOptionKey(opt)
}

function toggleMultiAnswer(opt: string) {
  const id = currentQ.value.id
  const key = extractOptionKey(opt)
  const current = answers.value[id] || ''
  const selected = current ? current.split(',') : []
  const idx = selected.indexOf(key)
  if (idx >= 0) {
    selected.splice(idx, 1)
  } else {
    selected.push(key)
  }
  answers.value[id] = selected.join(',')
}

function isMultiSelected(opt: string): boolean {
  const key = extractOptionKey(opt)
  const current = answers.value[currentQ.value.id] || ''
  return current.split(',').includes(key)
}

function nextQuestion() {
  if (currentIndex.value < questions.value.length - 1) currentIndex.value++
}

function prevQuestion() {
  if (currentIndex.value > 0) currentIndex.value--
}

function resultIndex(qid: number) {
  return questions.value.findIndex(q => q.id === qid)
}

async function submitQuiz() {
  const answerList = questions.value.map(q => ({
    question_id: q.id,
    answer: answers.value[q.id] || '',
    time_spent: Math.round(elapsed.value / questions.value.length),
  }))
  submitting.value = true
  try {
    const res: any = await quizApi.submit(sessionId.value, { answers: answerList })
    result.value = res.data
    submitted.value = true
    clearInterval(timer)
    sessionStorage.removeItem('quizSession')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  timer = setInterval(() => elapsed.value++, 1000)
})
onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
/* LaTeX content common styles */
.latex-content :deep(.katex-display) {
  margin: 0.4em 0;
  overflow-x: auto;
}

.latex-content :deep(.katex) {
  font-size: 1em;
}

/* Math symbol toolbar */
.math-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  padding: 6px 8px;
  margin-bottom: 8px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}

.math-toolbar-label {
  font-size: 12px;
  color: #64748b;
  margin-right: 4px;
  white-space: nowrap;
}

.math-sym-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 32px;
  height: 28px;
  padding: 0 6px;
  border: 1px solid #cbd5e1;
  border-radius: 5px;
  background: #fff;
  color: #334155;
  font-size: 14px;
  font-family: 'Times New Roman', serif;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
  line-height: 1;
}

.math-sym-btn:hover {
  background: #eff6ff;
  border-color: #3b82f6;
  color: #1d4ed8;
}

/* Toolbar divider */
.toolbar-sep {
  display: inline-block;
  width: 1px;
  height: 20px;
  background: #cbd5e1;
  margin: 0 4px;
  flex-shrink: 0;
}

/* Scan answer button */
.scan-answer-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 28px;
  padding: 0 10px;
  border: 1px solid #93c5fd;
  border-radius: 5px;
  background: #eff6ff;
  color: #2563eb;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
  white-space: nowrap;
  user-select: none;
}

.scan-answer-btn:hover {
  background: #dbeafe;
  border-color: #3b82f6;
}

.scan-answer-btn.scanning {
  opacity: 0.7;
  cursor: not-allowed;
}
</style>
