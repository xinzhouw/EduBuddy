<template>
  <div class="max-w-3xl mx-auto space-y-4">
    <div class="flex items-center gap-3">
      <el-button @click="router.push('/wrong-book')">← {{ $t('wrong_book.back') }}</el-button>
      <h2 class="font-semibold text-gray-800">{{ $t('wrong_book.detail_title') }}</h2>
    </div>

    <div v-if="item" class="space-y-4">
      <!-- Question info -->
      <div class="card">
        <div class="flex items-center gap-2 mb-3">
          <span class="px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700">{{ item.subject }}</span>
          <el-select v-model="item.mastery" size="small" style="width:110px" @change="updateMastery">
            <el-option :label="$t('wrong_book.mastery_label_unmastered')" value="unmastered" />
            <el-option :label="$t('wrong_book.mastery_label_fuzzy')" value="fuzzy" />
            <el-option :label="$t('wrong_book.mastery_label_mastered')" value="mastered" />
          </el-select>
        </div>
        <div class="bg-gray-50 rounded-lg p-4 mb-3">
          <p class="text-sm font-medium text-gray-500 mb-1">📝 {{ $t('wrong_book.question_label_detail') }}</p>
          <div class="text-gray-800 markdown-body" v-html="renderQuestionWithOptions(item.question)"></div>
        </div>
        <div v-if="item.user_wrong_answer" class="text-sm text-red-500 mb-2">
          ❌ {{ $t('wrong_book.my_answer') }}<span v-html="renderLatexOnly(item.user_wrong_answer)"></span>
        </div>
        <div class="text-sm text-green-600">
          ✅ {{ $t('wrong_book.correct_answer') }}<span v-html="renderLatexOnly(item.correct_answer)"></span>
        </div>
      </div>

      <!-- AI explanation -->
      <div class="card">
        <div class="flex items-center justify-between mb-3">
          <h3 class="font-semibold text-gray-700">🤖 {{ $t('wrong_book.ai_explain_title') }}</h3>
          <el-button size="small" type="primary" plain @click="getAIExplain" :loading="explaining">{{ $t('wrong_book.get_ai_explain') }}</el-button>
        </div>

        <div v-if="explanation || explaining" class="bg-gray-50 rounded-lg p-4 text-sm text-gray-700 leading-relaxed">
          <div class="markdown-body" v-dyn-figures v-html="renderMessage(explanation)"></div>
          <span v-if="explaining" class="typing-cursor"></span>
        </div>
        <p v-else class="text-gray-400 text-sm">{{ $t('wrong_book.ai_explain_hint') }}</p>

        <!-- Follow-up question -->
        <div v-if="explanation" class="mt-4 border-t pt-4">
          <div class="flex gap-2">
            <el-input v-model="followUpQ" :placeholder="$t('wrong_book.follow_up_placeholder')" size="small" @keyup.enter="sendFollowUp" />
            <el-button size="small" type="primary" @click="sendFollowUp" :loading="followingUp">{{ $t('wrong_book.send_btn') }}</el-button>
          </div>
          <div v-if="followUpAnswer" class="mt-3 bg-blue-50 rounded-lg p-3 text-sm text-gray-700">
            <div class="markdown-body" v-dyn-figures v-html="renderMessage(followUpAnswer)"></div>
          </div>
        </div>
      </div>

      <!-- Action buttons -->
      <div class="flex gap-3">
        <el-button type="success" @click="markUnderstood">✅ {{ $t('wrong_book.mark_understood_btn') }}</el-button>
        <el-button @click="generateSimilar" :loading="generatingSimilar">📚 {{ $t('wrong_book.gen_similar_btn') }}</el-button>
      </div>

      <!-- Similar questions -->
      <div v-if="similarQuestions.length > 0" class="card">
        <h3 class="font-semibold text-gray-700 mb-3">📚 {{ $t('wrong_book.similar_title') }}</h3>
        <div class="space-y-3">
          <div v-for="(q, i) in similarQuestions" :key="i" class="border border-gray-200 rounded-lg p-3">
            <div class="text-sm text-gray-700 mb-2 markdown-body" v-html="renderLatexOnly(q.content)"></div>
            <div class="text-xs text-gray-400">{{ $t('wrong_book.ref_answer') }}<span v-html="renderLatexOnly(q.correct_answer)"></span></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { wrongBookApi } from '@/api/wrongBook'
import { ElMessage } from 'element-plus'
import { renderMessage, renderLatexOnly } from '@/utils/markdown'

/**
 * Render question content: convert \n-separated options to <br> line breaks after LaTeX rendering.
 * Handles both old data (plain question, no newlines) and new data (question + options, \n-separated).
 */
function renderQuestionWithOptions(text: string): string {
  if (!text) return ''
  // Render LaTeX formulas first
  const rendered = renderLatexOnly(text)
  // Convert \n to <br> (renderLatexOnly does not handle newlines)
  return rendered.replace(/\n/g, '<br>')
}

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const authStore = useAuthStore()
const itemId = Number(route.params.id)
const item = ref<any>(null)
const explanation = ref('')
const explaining = ref(false)
const followUpQ = ref('')
const followUpAnswer = ref('')
const followingUp = ref(false)
const generatingSimilar = ref(false)
const similarQuestions = ref<any[]>([])

async function loadItem() {
  const res: any = await wrongBookApi.get(itemId)
  item.value = res.data
  if (item.value.ai_explanation) explanation.value = item.value.ai_explanation
}

async function getAIExplain() {
  explanation.value = ''
  explaining.value = true
  try {
    const token = authStore.token
    const response = await fetch(`/api/wrong-book/${itemId}/ai-explain`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
    })
    const reader = response.body!.getReader()
    const decoder = new TextDecoder()
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const chunk = decoder.decode(value)
      for (const line of chunk.split('\n')) {
        if (!line.startsWith('data: ')) continue
        try {
          const data = JSON.parse(line.slice(6))
          if (data.type === 'content') explanation.value += data.delta
          if (data.type === 'done') explaining.value = false
        } catch {}
      }
    }
  } finally {
    explaining.value = false
  }
}

async function sendFollowUp() {
  if (!followUpQ.value.trim()) return
  followingUp.value = true
  followUpAnswer.value = ''
  try {
    const token = authStore.token
    const response = await fetch(`/api/wrong-book/${itemId}/follow-up`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({ question: followUpQ.value }),
    })
    const reader = response.body!.getReader()
    const decoder = new TextDecoder()
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const chunk = decoder.decode(value)
      for (const line of chunk.split('\n')) {
        if (!line.startsWith('data: ')) continue
        try {
          const data = JSON.parse(line.slice(6))
          if (data.type === 'content') followUpAnswer.value += data.delta
        } catch {}
      }
    }
    followUpQ.value = ''
  } finally {
    followingUp.value = false
  }
}

async function updateMastery() {
  await wrongBookApi.updateMastery(itemId, item.value.mastery)
  ElMessage.success(t('common.success'))
}

async function markUnderstood() {
  item.value.mastery = 'mastered'
  await updateMastery()
}

async function generateSimilar() {
  generatingSimilar.value = true
  try {
    const res: any = await wrongBookApi.similarQuiz(itemId, 3)
    similarQuestions.value = res.data.questions || []
  } finally {
    generatingSimilar.value = false
  }
}

onMounted(loadItem)
</script>

<style scoped>
/* KaTeX formula rendering base styles */
.markdown-body :deep(.katex-display) {
  overflow-x: auto;
  padding: 0.5rem 0;
}

.markdown-body :deep(p) {
  margin: 0.4em 0;
}

.markdown-body :deep(ol),
.markdown-body :deep(ul) {
  padding-left: 1.5em;
  margin: 0.4em 0;
}

.markdown-body :deep(li) {
  margin: 0.2em 0;
}

.markdown-body :deep(strong) {
  font-weight: 600;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  font-weight: 600;
  margin: 0.6em 0 0.3em;
}

.markdown-body :deep(code) {
  background: #f0f0f0;
  padding: 0.1em 0.3em;
  border-radius: 3px;
  font-size: 0.9em;
}

.markdown-body :deep(pre) {
  background: #f6f8fa;
  padding: 0.8em;
  border-radius: 6px;
  overflow-x: auto;
}

/* Typing cursor animation */
.typing-cursor {
  display: inline-block;
  width: 2px;
  height: 1em;
  background: currentColor;
  margin-left: 2px;
  vertical-align: middle;
  animation: blink 0.8s step-end infinite;
}

@keyframes blink {
  50% { opacity: 0; }
}
</style>
