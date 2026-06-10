<template>
  <div class="max-w-2xl mx-auto">
    <div class="card space-y-6">
      <h2 class="text-xl font-bold text-gray-800">📚 开始练习</h2>

      <!-- 扫描输入区域 -->
      <div class="border-2 border-dashed rounded-xl p-4 transition-colors"
        :class="isDragging ? 'border-blue-400 bg-blue-50' : 'border-gray-200 bg-gray-50 hover:border-blue-300'"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="onDrop">
        <div v-if="!scanning && !scanResult" class="text-center">
          <p class="text-2xl mb-1">📷</p>
          <p class="text-sm font-medium text-gray-700 mb-1">扫描图片 / 文档 自动识别题目</p>
          <p class="text-xs text-gray-400 mb-3">支持 JPG、PNG、PDF、Word，拖拽或点击上传</p>
          <label class="inline-block cursor-pointer">
            <input
              ref="fileInputRef"
              type="file"
              class="hidden"
              accept=".jpg,.jpeg,.png,.gif,.webp,.pdf,.docx"
              @change="onFileChange"
            />
            <span class="px-4 py-2 rounded-lg bg-blue-500 text-white text-sm font-medium hover:bg-blue-600 transition-colors">
              选择文件
            </span>
          </label>
        </div>

        <!-- 识别中 -->
        <div v-else-if="scanning" class="text-center py-2">
          <div class="inline-block w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mb-2"></div>
          <p class="text-sm text-gray-600">AI 正在识别题目内容…</p>
        </div>

        <!-- 识别结果 -->
        <div v-else-if="scanResult" class="space-y-3">
          <div class="flex items-start justify-between gap-2">
            <div class="flex items-center gap-2">
              <span class="text-green-500 text-lg">✅</span>
              <span class="text-sm font-medium text-gray-700">识别成功，信息已自动填入</span>
            </div>
            <button class="text-xs text-gray-400 hover:text-red-500 transition-colors flex-shrink-0" @click="clearScan">
              ✕ 清除
            </button>
          </div>

          <!-- 识别到的文字 -->
          <div v-if="scanResult.recognized_text" class="bg-white border border-gray-200 rounded-lg p-3 max-h-36 overflow-y-auto">
            <p class="text-xs text-gray-400 mb-1">识别到的题目内容：</p>
            <div class="text-sm text-gray-700 leading-relaxed latex-content" v-html="renderRecognizedText(scanResult.recognized_text)"></div>
          </div>

          <div class="grid grid-cols-2 gap-3 text-sm">
            <div class="bg-blue-50 rounded-lg px-3 py-2">
              <span class="text-gray-500 text-xs">学科</span>
              <p class="font-semibold text-blue-700">{{ scanResult.subject }}</p>
            </div>
            <div class="bg-purple-50 rounded-lg px-3 py-2">
              <span class="text-gray-500 text-xs">知识点</span>
              <p class="font-semibold text-purple-700">{{ scanResult.topic }}</p>
            </div>
          </div>

          <div class="flex gap-2">
            <button class="flex-1 text-xs text-center py-2 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 transition-colors" @click="clearScan">
              重新上传
            </button>
            <button class="flex-1 text-xs text-center py-2 rounded-lg bg-blue-50 text-blue-600 font-medium hover:bg-blue-100 transition-colors" @click="applyToForm">
              ✔ 应用到表单
            </button>
          </div>
        </div>
      </div>

      <div class="flex items-center gap-2 text-gray-300">
        <div class="flex-1 h-px bg-gray-200"></div>
        <span class="text-xs">或手动填写</span>
        <div class="flex-1 h-px bg-gray-200"></div>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-600 mb-1">学科</label>
          <el-select v-model="form.subject" class="w-full">
            <el-option v-for="s in subjects" :key="s" :label="s" :value="s" />
          </el-select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-600 mb-1">知识点</label>
          <el-input v-model="form.topic" placeholder="如：二次函数、牛顿定律" />
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-600 mb-2">难度</label>
        <div class="grid grid-cols-4 gap-3">
          <button v-for="d in difficulties" :key="d.value"
            @click="form.difficulty = d.value"
            class="p-3 rounded-lg border-2 text-center transition-all"
            :class="form.difficulty === d.value ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'">
            <p class="text-lg">{{ d.icon }}</p>
            <p class="text-xs font-medium mt-1">{{ d.label }}</p>
          </button>
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-600 mb-2">题型</label>
        <div class="flex flex-wrap gap-2">
          <el-checkbox v-for="t in questionTypes" :key="t.value" v-model="t.checked" :label="t.label" />
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-600 mb-1">题目数量</label>
        <el-select v-model="form.count" style="width:100px">
          <el-option v-for="n in [3, 5, 10, 15]" :key="n" :label="`${n}道`" :value="n" />
        </el-select>
      </div>

      <el-button type="primary" size="large" class="w-full" :loading="loading" @click="startQuiz">
        🚀 开始练习
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { quizApi } from '@/api/quiz'
import { ElMessage } from 'element-plus'
import { renderRecognizedText } from '@/utils/markdown'

const router = useRouter()
const loading = ref(false)
const subjects = ['数学', '物理', '化学', '生物', '语文', '英语', '历史', '地理', '政治']
const difficulties = [
  { value: 1, icon: '🌱', label: '基础' },
  { value: 2, icon: '📘', label: '中等' },
  { value: 3, icon: '🔥', label: '困难' },
  { value: 4, icon: '🏆', label: '挑战' },
]
const questionTypes = reactive([
  { value: 'single_choice', label: '单选题', checked: true },
  { value: 'fill_blank', label: '填空题', checked: true },
  { value: 'true_false', label: '判断题', checked: false },
  { value: 'subjective', label: '简答题', checked: false },
])
const form = reactive({ subject: '数学', topic: '', difficulty: 2, count: 5 })

// ===== 扫描识别相关状态 =====
const fileInputRef = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)
const scanning = ref(false)
const scanResult = ref<{
  subject: string
  topic: string
  recognized_text: string
  question_count: number
} | null>(null)

// 按文件扩展名推断 MIME type（用于拖拽上传时 file.type 为空的情况）
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
    ElMessage.warning('不支持的文件类型，请上传 JPG、PNG、PDF 或 Word 文件')
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.warning('文件大小超过限制（最大 10MB）')
    return
  }

  scanning.value = true
  scanResult.value = null
  try {
    const res: any = await quizApi.extractTopicFromFile(file)
    if (res?.code === 200 && res.data) {
      scanResult.value = res.data
      // 自动填入表单
      applyToFormFromResult(res.data)
      ElMessage.success('题目识别成功，已自动填写学科和知识点')
    } else {
      ElMessage.error('识别失败，请重试')
    }
  } catch (e: any) {
    const msg = e?.response?.data?.detail || '识别失败，请检查文件内容后重试'
    ElMessage.error(msg)
  } finally {
    scanning.value = false
    // 重置 input，允许再次选同一文件
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
  if (subjects.includes(result.subject)) {
    form.subject = result.subject
  }
  if (result.topic) {
    form.topic = result.topic
  }
}

function applyToForm() {
  applyToFormFromResult(scanResult.value)
  ElMessage.success('已应用到表单')
}

function clearScan() {
  scanResult.value = null
  scanning.value = false
}

// ===== 开始练习 =====
async function startQuiz() {
  if (!form.topic.trim()) return ElMessage.warning('请输入知识点')
  const selectedTypes = questionTypes.filter(t => t.checked).map(t => t.value)
  if (selectedTypes.length === 0) return ElMessage.warning('请至少选择一种题型')

  loading.value = true
  try {
    const res: any = await quizApi.generate({
      subject: form.subject,
      topic: form.topic,
      difficulty: form.difficulty,
      question_types: selectedTypes,
      count: form.count,
    })
    // 将数据存入 sessionStorage 再跳转
    sessionStorage.setItem('quizSession', JSON.stringify(res.data))
    router.push('/quiz/session')
  } finally {
    loading.value = false
  }
}
</script>
