<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-6">
    <div class="max-w-4xl mx-auto">

      <!-- 页面标题 -->
      <div class="mb-6 flex items-center gap-3">
        <div class="w-10 h-10 bg-gradient-to-br from-amber-400 to-orange-500 rounded-xl flex items-center justify-center shadow-md">
          <span class="text-xl">📖</span>
        </div>
        <div>
          <h1 class="text-2xl font-bold text-slate-800">读书郎</h1>
          <p class="text-sm text-slate-500">上传文件或输入文本，一键转换为语音朗读，支持导出音频</p>
        </div>
      </div>

      <!-- 主体卡片 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

        <!-- 左侧：内容输入区 -->
        <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 flex flex-col gap-5">
          <h2 class="text-base font-semibold text-slate-700 flex items-center gap-2">
            <span>📥</span> 内容来源
          </h2>

          <!-- Tab 切换 -->
          <div class="flex gap-1 bg-slate-100 rounded-xl p-1">
            <button
              v-for="tab in tabs"
              :key="tab.key"
              @click="activeTab = tab.key"
              class="flex-1 py-2 rounded-lg text-sm font-medium transition-all duration-150"
              :class="activeTab === tab.key
                ? 'bg-white text-slate-800 shadow-sm'
                : 'text-slate-500 hover:text-slate-700'"
            >
              {{ tab.icon }} {{ tab.label }}
            </button>
          </div>

          <!-- 文本输入 -->
          <div v-if="activeTab === 'text'" class="flex flex-col gap-3">
            <textarea
              v-model="inputText"
              placeholder="在此粘贴或输入要朗读的文章、段落……"
              class="w-full h-52 px-4 py-3 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-amber-400 focus:border-transparent transition"
            />
            <div class="flex items-center justify-between text-xs text-slate-400">
              <span>{{ inputText.length }} / 50000 字</span>
              <button
                v-if="inputText"
                @click="inputText = ''"
                class="text-slate-400 hover:text-red-400 transition-colors"
              >清空</button>
            </div>
            <button
              @click="submitText"
              :disabled="!inputText.trim() || isExtracting"
              class="btn-primary"
            >
              <span v-if="isExtracting" class="animate-spin">⏳</span>
              <span v-else>✅</span>
              {{ isExtracting ? '处理中…' : '确认文本' }}
            </button>
          </div>

          <!-- 文件上传 -->
          <div v-else class="flex flex-col gap-3">
            <!-- 拖拽区域 -->
            <div
              class="relative border-2 border-dashed rounded-xl p-6 text-center transition-all duration-150 cursor-pointer"
              :class="isDragging
                ? 'border-amber-400 bg-amber-50'
                : 'border-slate-200 hover:border-amber-300 hover:bg-amber-50/40'"
              @dragover.prevent="isDragging = true"
              @dragleave.prevent="isDragging = false"
              @drop.prevent="onDrop"
              @click="fileInputRef?.click()"
            >
              <input
                ref="fileInputRef"
                type="file"
                class="hidden"
                accept=".pdf,.docx,.jpg,.jpeg,.png,.gif,.webp"
                @change="onFileChange"
              />
              <div v-if="!uploadedFile">
                <p class="text-3xl mb-2">📂</p>
                <p class="text-sm font-medium text-slate-600">点击或拖拽上传文件</p>
                <p class="text-xs text-slate-400 mt-1">支持 PDF、Word(.docx)、图片(JPG/PNG/WebP)</p>
              </div>
              <div v-else class="flex items-center gap-3 justify-center">
                <span class="text-2xl">{{ fileIcon(uploadedFile.name) }}</span>
                <div class="text-left">
                  <p class="text-sm font-medium text-slate-700 truncate max-w-[180px]">{{ uploadedFile.name }}</p>
                  <p class="text-xs text-slate-400">{{ formatSize(uploadedFile.size) }}</p>
                </div>
                <button
                  @click.stop="clearFile"
                  class="ml-auto text-slate-400 hover:text-red-400 transition-colors text-lg"
                  title="移除文件"
                >✕</button>
              </div>
            </div>

            <button
              @click="submitFile"
              :disabled="!uploadedFile || isExtracting"
              class="btn-primary"
            >
              <span v-if="isExtracting" class="animate-spin inline-block">⏳</span>
              <span v-else>🔍</span>
              {{ isExtracting ? '识别中…' : '提取文字' }}
            </button>

            <!-- 错误提示 -->
            <p v-if="extractError" class="text-sm text-red-500 bg-red-50 rounded-lg px-3 py-2">
              ⚠️ {{ extractError }}
            </p>
          </div>
        </div>

        <!-- 右侧：语音控制区 -->
        <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 flex flex-col gap-5">
          <h2 class="text-base font-semibold text-slate-700 flex items-center gap-2">
            <span>🎙️</span> 语音朗读
          </h2>

          <!-- 语音设置 -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="text-xs text-slate-500 font-medium mb-1 block">朗读语言</label>
              <select
                v-model="ttsLang"
                class="w-full px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-amber-400"
              >
                <option value="zh-CN">中文（普通话）</option>
                <option value="zh-TW">中文（台湾）</option>
                <option value="en-US">English (US)</option>
                <option value="en-GB">English (UK)</option>
                <option value="ja-JP">日本語</option>
              </select>
            </div>
            <div>
              <label class="text-xs text-slate-500 font-medium mb-1 block">朗读速度 ({{ ttsRate.toFixed(1) }}x)</label>
              <input
                type="range"
                v-model.number="ttsRate"
                min="0.5" max="2.0" step="0.1"
                class="w-full mt-1.5 accent-amber-500"
              />
            </div>
            <div>
              <label class="text-xs text-slate-500 font-medium mb-1 block">音调 ({{ ttsPitch.toFixed(1) }})</label>
              <input
                type="range"
                v-model.number="ttsPitch"
                min="0.5" max="2.0" step="0.1"
                class="w-full mt-1.5 accent-amber-500"
              />
            </div>
            <div>
              <label class="text-xs text-slate-500 font-medium mb-1 block">音量 ({{ Math.round(ttsVolume * 100) }}%)</label>
              <input
                type="range"
                v-model.number="ttsVolume"
                min="0" max="1" step="0.05"
                class="w-full mt-1.5 accent-amber-500"
              />
            </div>
          </div>

          <!-- 文本字数信息 -->
          <div v-if="readyText" class="bg-amber-50 rounded-xl px-4 py-3 border border-amber-100">
            <p class="text-xs text-amber-700 font-medium mb-1">✅ 文本已就绪</p>
            <p class="text-xs text-amber-600">共 {{ readyText.length }} 字，预计约 {{ estimatedDuration }} 分钟</p>
          </div>
          <div v-else class="bg-slate-50 rounded-xl px-4 py-3 border border-slate-100 text-center">
            <p class="text-sm text-slate-400">请先在左侧输入文本或上传文件</p>
          </div>

          <!-- 播放控制按钮 -->
          <div class="flex flex-col gap-3">
            <!-- 播放/暂停/停止 -->
            <div class="flex gap-2">
              <button
                v-if="ttsState === 'idle'"
                @click="startSpeech"
                :disabled="!readyText"
                class="flex-1 btn-play"
              >
                ▶ 开始朗读
              </button>
              <template v-else-if="ttsState === 'playing'">
                <button @click="togglePause" class="flex-1 btn-pause">
                  ⏸ 暂停
                </button>
                <button @click="stopSpeech" class="btn-stop">
                  ⏹
                </button>
              </template>
              <template v-else-if="ttsState === 'paused'">
                <button @click="togglePause" class="flex-1 btn-resume">
                  ▶ 继续
                </button>
                <button @click="stopSpeech" class="btn-stop">
                  ⏹
                </button>
              </template>
            </div>

            <!-- 波形动画 -->
            <div v-if="ttsState === 'playing'" class="flex items-end justify-center gap-1 h-8">
              <span
                v-for="i in 5" :key="i"
                class="wave-bar"
                :style="{ animationDelay: `${(i - 1) * 0.12}s` }"
              />
            </div>
            <p v-else-if="ttsState === 'paused'" class="text-center text-xs text-amber-600">⏸ 已暂停</p>

            <!-- 录制导出 -->
            <div class="border-t border-slate-100 pt-3 flex flex-col gap-2">
              <p class="text-xs text-slate-500 font-medium flex items-center gap-1">
                <span>💾</span> 录制并导出音频
              </p>
              <p class="text-xs text-slate-400">
                点击「开始录制」后再点「开始朗读」，完成后点「停止录制」即可下载音频文件（WebM 格式）
              </p>
              <div class="flex gap-2">
                <button
                  v-if="!isRecording"
                  @click="startRecording"
                  :disabled="!readyText || ttsState === 'playing'"
                  class="flex-1 btn-record"
                >
                  🔴 开始录制
                </button>
                <template v-else>
                  <div class="flex items-center gap-2 flex-1 bg-red-50 border border-red-200 rounded-xl px-3 py-2">
                    <span class="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
                    <span class="text-xs text-red-600 font-medium">录制中 {{ recordingDuration }}s</span>
                  </div>
                  <button @click="stopRecording" class="btn-stop-record">
                    ⏹ 停止
                  </button>
                </template>
              </div>
              <button
                v-if="recordedBlob"
                @click="downloadAudio"
                class="btn-download"
              >
                ⬇️ 下载音频文件
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 文本预览区 -->
      <div v-if="readyText" class="mt-6 bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-base font-semibold text-slate-700 flex items-center gap-2">
            <span>📄</span> 待朗读文本
            <span class="text-xs font-normal text-slate-400 ml-1">（{{ readyText.length }} 字）</span>
          </h2>
          <button @click="clearReadyText" class="text-xs text-slate-400 hover:text-red-400 transition-colors">
            🗑️ 清除
          </button>
        </div>
        <div class="max-h-64 overflow-y-auto bg-slate-50 rounded-xl px-4 py-3 text-sm text-slate-700 leading-relaxed whitespace-pre-wrap border border-slate-100">
          {{ readyText }}
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import apiClient from '@/api/index'

// ── Tabs ──────────────────────────────────────────────────────────────────────
const tabs = [
  { key: 'text', icon: '✏️', label: '文本输入' },
  { key: 'file', icon: '📂', label: '文件上传' },
] as const
type TabKey = typeof tabs[number]['key']
const activeTab = ref<TabKey>('text')

// ── 输入状态 ──────────────────────────────────────────────────────────────────
const inputText = ref('')
const uploadedFile = ref<File | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)
const isExtracting = ref(false)
const extractError = ref('')

// 已处理好、可朗读的文本
const readyText = ref('')

// ── TTS 设置 ──────────────────────────────────────────────────────────────────
const ttsLang = ref('zh-CN')
const ttsRate = ref(1.0)
const ttsPitch = ref(1.0)
const ttsVolume = ref(1.0)
const ttsState = ref<'idle' | 'playing' | 'paused'>('idle')

let utterance: SpeechSynthesisUtterance | null = null
const voices = ref<SpeechSynthesisVoice[]>([])

// ── 录制 ──────────────────────────────────────────────────────────────────────
const isRecording = ref(false)
const recordedBlob = ref<Blob | null>(null)
const recordingDuration = ref(0)
let mediaRecorder: MediaRecorder | null = null
let recordingTimer: ReturnType<typeof setInterval> | null = null
let audioChunks: Blob[] = []

// ── Computed ──────────────────────────────────────────────────────────────────
const estimatedDuration = computed(() => {
  if (!readyText.value) return '0'
  // 中文约 200 字/分钟 * ttsRate
  const mins = readyText.value.length / (200 * ttsRate.value)
  if (mins < 1) return `${Math.ceil(mins * 60)} 秒`
  return `${mins.toFixed(1)}`
})

// ── 文件工具 ──────────────────────────────────────────────────────────────────
function fileIcon(name: string) {
  const ext = name.split('.').pop()?.toLowerCase()
  if (ext === 'pdf') return '📕'
  if (ext === 'docx' || ext === 'doc') return '📘'
  if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext || '')) return '🖼️'
  return '📄'
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function onDrop(e: DragEvent) {
  isDragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) setFile(file)
}

function onFileChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) setFile(file)
}

function setFile(file: File) {
  uploadedFile.value = file
  extractError.value = ''
  recordedBlob.value = null
}

function clearFile() {
  uploadedFile.value = null
  if (fileInputRef.value) fileInputRef.value.value = ''
  extractError.value = ''
}

// ── 提交文本 ──────────────────────────────────────────────────────────────────
async function submitText() {
  if (!inputText.value.trim()) return
  isExtracting.value = true
  extractError.value = ''
  try {
    const resp = await apiClient.post('/tts/extract-text/plain', {
      text: inputText.value,
    })
    readyText.value = resp.data.text
  } catch (e: any) {
    extractError.value = e?.response?.data?.detail || '文本处理失败，请重试'
  } finally {
    isExtracting.value = false
  }
}

// ── 提交文件 ──────────────────────────────────────────────────────────────────
async function submitFile() {
  if (!uploadedFile.value) return
  isExtracting.value = true
  extractError.value = ''
  try {
    const form = new FormData()
    form.append('file', uploadedFile.value)
    const resp = await apiClient.post('/tts/extract-text/file', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    readyText.value = resp.data.text
  } catch (e: any) {
    extractError.value = e?.response?.data?.detail || '文件识别失败，请检查文件格式或重试'
  } finally {
    isExtracting.value = false
  }
}

function clearReadyText() {
  readyText.value = ''
  stopSpeech()
  recordedBlob.value = null
}

// ── TTS 朗读 ──────────────────────────────────────────────────────────────────
function pickVoice(lang: string): SpeechSynthesisVoice | null {
  // 完全匹配 → 语言前缀匹配
  return (
    voices.value.find(v => v.lang === lang) ||
    voices.value.find(v => v.lang.startsWith(lang.split('-')[0])) ||
    null
  )
}

function startSpeech() {
  if (!readyText.value) return
  window.speechSynthesis.cancel()

  utterance = new SpeechSynthesisUtterance(readyText.value)
  utterance.lang = ttsLang.value
  utterance.rate = ttsRate.value
  utterance.pitch = ttsPitch.value
  utterance.volume = ttsVolume.value

  const voice = pickVoice(ttsLang.value)
  if (voice) utterance.voice = voice

  utterance.onstart = () => { ttsState.value = 'playing' }
  utterance.onpause = () => { ttsState.value = 'paused' }
  utterance.onresume = () => { ttsState.value = 'playing' }
  utterance.onend = () => { ttsState.value = 'idle' }
  utterance.onerror = () => { ttsState.value = 'idle' }

  window.speechSynthesis.speak(utterance)
  ttsState.value = 'playing'
}

function togglePause() {
  if (ttsState.value === 'playing') {
    window.speechSynthesis.pause()
    ttsState.value = 'paused'
  } else if (ttsState.value === 'paused') {
    window.speechSynthesis.resume()
    ttsState.value = 'playing'
  }
}

function stopSpeech() {
  window.speechSynthesis.cancel()
  ttsState.value = 'idle'
  utterance = null
}

// ── 录制音频（使用系统音频 / AudioContext） ───────────────────────────────────
// 注意：Web Speech API 直接输出到扬声器，浏览器不允许捕获 TTS 音频流
// 因此采用「录制扬声器输出」（getDisplayMedia / getUserMedia loopback）策略
// 如果浏览器不支持，则提示用户使用系统录音工具
async function startRecording() {
  recordedBlob.value = null
  audioChunks = []
  recordingDuration.value = 0

  try {
    // 优先尝试捕获系统/选项卡音频（Chrome 支持 getDisplayMedia + audio）
    let stream: MediaStream | null = null

    try {
      // @ts-ignore — getDisplayMedia 含音频，Chrome 实验性支持
      stream = await (navigator.mediaDevices as any).getDisplayMedia({
        video: false,
        audio: {
          echoCancellation: false,
          noiseSuppression: false,
          sampleRate: 44100,
        },
      })
    } catch {
      // 若用户取消选屏共享，尝试麦克风作为备选（用户可以对着外放录制）
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          audio: { echoCancellation: false, noiseSuppression: false },
        })
      } catch {
        stream = null
      }
    }

    if (!stream) {
      alert('无法获取音频流。\n\n建议：\n① 点击「开始录制」时选择「整个屏幕」并勾选「分享系统音频」\n② 或使用系统录音软件录制外放声音')
      return
    }

    mediaRecorder = new MediaRecorder(stream, { mimeType: getSupportedMime() })
    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunks.push(e.data)
    }
    mediaRecorder.onstop = () => {
      const mime = getSupportedMime()
      recordedBlob.value = new Blob(audioChunks, { type: mime })
      stream?.getTracks().forEach(t => t.stop())
    }
    mediaRecorder.start(200)
    isRecording.value = true

    recordingTimer = setInterval(() => {
      recordingDuration.value++
    }, 1000)
  } catch (err) {
    console.error('录制失败', err)
    alert('录制初始化失败，请检查浏览器权限设置')
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop()
  }
  isRecording.value = false
  if (recordingTimer) {
    clearInterval(recordingTimer)
    recordingTimer = null
  }
}

function getSupportedMime(): string {
  const types = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4']
  for (const t of types) {
    if (MediaRecorder.isTypeSupported(t)) return t
  }
  return ''
}

function downloadAudio() {
  if (!recordedBlob.value) return
  const url = URL.createObjectURL(recordedBlob.value)
  const a = document.createElement('a')
  a.href = url
  const ext = recordedBlob.value.type.includes('ogg') ? 'ogg'
    : recordedBlob.value.type.includes('mp4') ? 'mp4'
    : 'webm'
  a.download = `读书郎_${Date.now()}.${ext}`
  a.click()
  URL.revokeObjectURL(url)
}

// ── 生命周期 ──────────────────────────────────────────────────────────────────
onMounted(() => {
  const load = () => {
    voices.value = window.speechSynthesis.getVoices()
  }
  load()
  window.speechSynthesis.addEventListener('voiceschanged', load)
})

onUnmounted(() => {
  window.speechSynthesis.cancel()
  stopRecording()
})
</script>

<style scoped>
@reference "../../style.css";

.btn-primary {
  @apply flex items-center justify-center gap-2 w-full py-2.5 rounded-xl bg-amber-500 hover:bg-amber-600 active:bg-amber-700 text-white text-sm font-semibold shadow-sm transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed;
}
.btn-play {
  @apply flex items-center justify-center gap-2 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold shadow-sm transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed;
}
.btn-pause {
  @apply flex items-center justify-center gap-2 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-600 text-white text-sm font-semibold shadow-sm transition-all duration-150;
}
.btn-resume {
  @apply flex items-center justify-center gap-2 py-2.5 rounded-xl bg-green-600 hover:bg-green-700 text-white text-sm font-semibold shadow-sm transition-all duration-150;
}
.btn-stop {
  @apply flex items-center justify-center px-4 py-2.5 rounded-xl bg-slate-200 hover:bg-slate-300 text-slate-700 text-sm font-semibold shadow-sm transition-all duration-150;
}
.btn-record {
  @apply flex items-center justify-center gap-2 py-2.5 rounded-xl bg-rose-500 hover:bg-rose-600 text-white text-sm font-semibold shadow-sm transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed;
}
.btn-stop-record {
  @apply flex items-center justify-center gap-1 px-4 py-2.5 rounded-xl bg-slate-700 hover:bg-slate-800 text-white text-sm font-semibold shadow-sm transition-all duration-150;
}
.btn-download {
  @apply flex items-center justify-center gap-2 w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold shadow-sm transition-all duration-150;
}

/* 波形动画 */
.wave-bar {
  display: inline-block;
  width: 4px;
  border-radius: 9999px;
  background: linear-gradient(to top, #f59e0b, #f97316);
  animation: wave-anim 0.8s ease-in-out infinite alternate;
}
.wave-bar:nth-child(1) { height: 16px; }
.wave-bar:nth-child(2) { height: 28px; }
.wave-bar:nth-child(3) { height: 22px; }
.wave-bar:nth-child(4) { height: 32px; }
.wave-bar:nth-child(5) { height: 18px; }

@keyframes wave-anim {
  0%   { transform: scaleY(0.4); opacity: 0.7; }
  100% { transform: scaleY(1.0); opacity: 1; }
}
</style>
