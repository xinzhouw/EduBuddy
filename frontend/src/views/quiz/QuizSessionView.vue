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
          <p class="text-gray-800 font-medium text-base mb-6 leading-relaxed">{{ currentQ.content }}</p>

          <!-- 选择题 -->
          <div v-if="currentQ.type === 'single_choice' || currentQ.type === 'true_false'" class="space-y-3">
            <button v-for="(opt, i) in parseOptions(currentQ.options)" :key="i"
              @click="selectAnswer(opt)"
              class="w-full text-left p-3.5 rounded-lg border-2 transition-all text-sm"
              :class="answers[currentQ.id] === opt
                ? 'border-blue-500 bg-blue-50 text-blue-700'
                : 'border-gray-200 hover:border-gray-300'">
              {{ opt }}
            </button>
          </div>

          <!-- 填空/简答题 -->
          <el-input v-else v-model="answers[currentQ.id]" type="textarea" :rows="4"
            placeholder="请输入你的答案..." />
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
            你的答案：<span class="text-red-500">{{ r.user_answer }}</span> ·
            正确答案：<span class="text-green-600">{{ r.correct_answer }}</span>
          </p>
          <div v-if="!r.is_correct && r.explanation" class="bg-blue-50 rounded-lg p-3 text-sm text-gray-600">
            <p class="font-medium text-blue-700 mb-1">AI 解析：</p>
            {{ r.explanation }}
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { quizApi } from '@/api/quiz'
import { ElMessage } from 'element-plus'

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

const currentQ = computed(() => questions.value[currentIndex.value])

function formatTime(s: number) {
  const m = Math.floor(s / 60)
  const sec = s % 60
  return `${m}:${sec.toString().padStart(2, '0')}`
}

function parseOptions(opts: any): string[] {
  if (!opts) return []
  try { return typeof opts === 'string' ? JSON.parse(opts) : opts } catch { return [] }
}

function selectAnswer(opt: string) {
  answers.value[currentQ.value.id] = opt
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
