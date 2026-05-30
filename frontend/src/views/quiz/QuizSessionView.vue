<template>
  <div class="max-w-3xl mx-auto space-y-4">
    <!-- 答题中 -->
    <template v-if="!submitted">
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <span class="text-sm text-gray-500">第 {{ currentIndex + 1 }}/{{ questions.length }} 题</span>
          <span class="text-sm text-gray-500">⏱ {{ formatTime(elapsed) }}</span>
        </div>
        <div class="w-full bg-gray-200 rounded-full h-1.5 mb-6">
          <div class="bg-blue-500 h-1.5 rounded-full transition-all" :style="`width: ${((currentIndex + 1) / questions.length) * 100}%`"></div>
        </div>

        <div v-if="currentQ">
          <!-- 题目内容：支持 LaTeX 渲染 -->
          <div class="text-gray-800 font-medium text-base mb-6 leading-relaxed latex-content"
            v-html="renderLatexOnly(currentQ.content)"></div>

          <!-- 选择题（单选 / 判断） -->
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

          <!-- 多选题 -->
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

          <!-- 填空/简答题 -->
          <div v-else>
            <!-- 操作栏：数学符号 + 图片识别 -->
            <div class="math-toolbar">
              <span class="math-toolbar-label">插入符号：</span>
              <button
                v-for="sym in mathSymbols" :key="sym.label"
                class="math-sym-btn"
                :title="sym.label"
                @click="insertSymbol(sym.value)"
              >{{ sym.display }}</button>
              <!-- 分隔线 -->
              <span class="toolbar-sep"></span>
              <!-- 图片识别按钮 -->
              <label class="scan-answer-btn" :class="{ 'scanning': scanningAnswer }" :title="scanningAnswer ? 'AI 识别中...' : '拍照/上传图片识别答案'">
                <input
                  type="file"
                  class="hidden"
                  accept="image/jpeg,image/png,image/gif,image/webp"
                  :disabled="scanningAnswer"
                  @change="onAnswerImageChange"
                />
                <span v-if="!scanningAnswer">📷 扫描答案</span>
                <span v-else class="flex items-center gap-1">
                  <span class="inline-block w-3 h-3 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></span>
                  识别中…
                </span>
              </label>
            </div>
            <el-input
              :ref="(el: any) => inputRef = el"
              v-model="answers[currentQ.id]"
              type="textarea"
              :rows="4"
              placeholder="请输入你的答案，或点击「📷 扫描答案」上传图片自动识别..."
            />
          </div>
        </div>
      </div>

      <div class="flex justify-between">
        <el-button @click="prevQuestion" :disabled="currentIndex === 0">← 上一题</el-button>
        <el-button v-if="currentIndex < questions.length - 1" type="primary" @click="nextQuestion">下一题 →</el-button>
        <el-button v-else type="success" @click="submitQuiz" :loading="submitting">提交答案</el-button>
      </div>
    </template>

    <!-- 结果 -->
    <template v-else>
      <div class="card text-center">
        <p class="text-3xl mb-2">🎉</p>
        <h2 class="text-2xl font-bold text-gray-800">练习完成！</h2>
        <div class="flex justify-center gap-8 mt-4">
          <div><p class="text-2xl font-bold text-blue-600">{{ result.correct }}/{{ result.total }}</p><p class="text-sm text-gray-500">正确率</p></div>
          <div><p class="text-2xl font-bold text-green-600">{{ Math.round(result.accuracy * 100) }}%</p><p class="text-sm text-gray-500">准确度</p></div>
          <div><p class="text-2xl font-bold text-gray-600">{{ formatTime(result.time_spent) }}</p><p class="text-sm text-gray-500">用时</p></div>
        </div>
        <p v-if="result.wrong_items_added?.length > 0" class="text-sm text-amber-600 mt-3">
          已自动将 {{ result.wrong_items_added.length }} 道错题加入错题本
        </p>
      </div>

      <div class="space-y-3">
        <div v-for="r in result.results" :key="r.question_id" class="card">
          <div class="flex items-center gap-2 mb-2">
            <span>{{ r.is_correct ? '✅' : '❌' }}</span>
            <span class="text-sm font-medium text-gray-700">第 {{ resultIndex(r.question_id) + 1 }} 题</span>
          </div>
          <p v-if="!r.is_correct" class="text-sm text-gray-500 mb-2">
            你的答案：<span class="text-red-500 latex-content" v-html="renderLatexOnly(r.user_answer)"></span> ·
            正确答案：<span class="text-green-600 latex-content" v-html="renderLatexOnly(r.correct_answer)"></span>
          </p>
          <div v-if="!r.is_correct && r.explanation" class="bg-blue-50 rounded-lg p-3 text-sm text-gray-600">
            <p class="font-medium text-blue-700 mb-1">AI 解析：</p>
            <span class="latex-content" v-html="renderLatexOnly(r.explanation)"></span>
          </div>
        </div>
      </div>

      <div class="flex justify-center gap-4">
        <el-button @click="router.push('/quiz')">再来一组</el-button>
        <el-button type="primary" @click="router.push('/wrong-book')">查看错题本</el-button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { quizApi } from '@/api/quiz'
import { ElMessage } from 'element-plus'
import { renderLatexOnly } from '@/utils/markdown'

const router = useRouter()
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

// textarea 的 el-input 引用，用于插入数学符号
const inputRef = ref<any>(null)

// ── 图片识别答案 ──────────────────────────────────────────────────
const scanningAnswer = ref(false)

async function onAnswerImageChange(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  // 重置 input，允许再次选同一文件
  input.value = ''

  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    ElMessage.warning('请上传 JPG 或 PNG 图片')
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.warning('图片大小超过限制（最大 10MB）')
    return
  }

  scanningAnswer.value = true
  try {
    // 将当前题目内容传给后端，提升识别精度
    const questionText = currentQ.value?.content || ''
    const res: any = await quizApi.extractAnswerFromFile(file, questionText)
    if (res?.data?.code === 200 && res.data.data?.answer) {
      const { answer, confidence } = res.data.data
      const qid = currentQ.value?.id
      if (qid != null) {
        answers.value[qid] = answer
      }
      if (confidence === 'low') {
        ElMessage.warning('图片识别置信度较低，请检查并手动修正答案')
      } else {
        ElMessage.success('已识别答案，请确认内容后提交')
      }
    } else {
      ElMessage.error('图片识别失败，请重试')
    }
  } catch (err: any) {
    const msg = err?.response?.data?.detail || '识别失败，请检查图片后重试'
    ElMessage.error(msg)
  } finally {
    scanningAnswer.value = false
  }
}

const currentQ = computed(() => questions.value[currentIndex.value])

// ── 常用数学符号列表 ──────────────────────────────────────────────
const mathSymbols = [
  { label: 'π（圆周率）',    display: 'π',   value: 'π' },
  { label: '√（根号）',      display: '√',   value: '√' },
  { label: '²（平方）',      display: 'x²',  value: '²' },
  { label: '³（立方）',      display: 'x³',  value: '³' },
  { label: '≥（大于等于）',  display: '≥',   value: '≥' },
  { label: '≤（小于等于）',  display: '≤',   value: '≤' },
  { label: '≠（不等于）',    display: '≠',   value: '≠' },
  { label: '×（乘号）',      display: '×',   value: '×' },
  { label: '÷（除号）',      display: '÷',   value: '÷' },
  { label: '±（正负号）',    display: '±',   value: '±' },
  { label: '∞（无穷大）',    display: '∞',   value: '∞' },
  { label: 'α（alpha）',     display: 'α',   value: 'α' },
  { label: 'β（beta）',      display: 'β',   value: 'β' },
  { label: 'θ（theta）',     display: 'θ',   value: 'θ' },
  { label: '∠（角）',        display: '∠',   value: '∠' },
  { label: '°（度）',        display: '°',   value: '°' },
  { label: '∑（求和）',      display: '∑',   value: '∑' },
  { label: '∈（属于）',      display: '∈',   value: '∈' },
  { label: '∩（交集）',      display: '∩',   value: '∩' },
  { label: '∪（并集）',      display: '∪',   value: '∪' },
]

/**
 * 在 textarea 光标处插入符号，优先使用原生 DOM 的 selectionStart/End
 */
function insertSymbol(sym: string) {
  const qid = currentQ.value?.id
  if (qid == null) return

  // 尝试获取底层 textarea DOM
  const textarea: HTMLTextAreaElement | null =
    inputRef.value?.$el?.querySelector('textarea') ?? null

  if (textarea) {
    const start = textarea.selectionStart ?? (answers.value[qid] ?? '').length
    const end   = textarea.selectionEnd   ?? start
    const before = (answers.value[qid] ?? '').slice(0, start)
    const after  = (answers.value[qid] ?? '').slice(end)
    answers.value[qid] = before + sym + after
    // 恢复光标到插入符号之后
    nextTick(() => {
      textarea.focus()
      const pos = start + sym.length
      textarea.setSelectionRange(pos, pos)
    })
  } else {
    // 降级：直接追加到末尾
    answers.value[qid] = (answers.value[qid] ?? '') + sym
  }
}

// ── 选项相关 ──────────────────────────────────────────────────────

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
 * 从选项文本中提取字母标识，例如：
 *   "A. 选项1"  → "A"
 *   "A、选项1"  → "A"
 *   "正确"      → "正确"（判断题保持原值）
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
/* LaTeX 内容通用样式 */
.latex-content :deep(.katex-display) {
  margin: 0.4em 0;
  overflow-x: auto;
}

.latex-content :deep(.katex) {
  font-size: 1em;
}

/* 数学符号工具栏 */
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

/* 工具栏分隔线 */
.toolbar-sep {
  display: inline-block;
  width: 1px;
  height: 20px;
  background: #cbd5e1;
  margin: 0 4px;
  flex-shrink: 0;
}

/* 扫描答案按钮 */
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
