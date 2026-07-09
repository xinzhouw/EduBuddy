<template>
  <div class="flex h-full gap-3 sm:gap-4 overflow-hidden" style="height: calc(100vh - 160px)">
    <!-- History sessions (PC: fixed sidebar, mobile: drawer triggered by button) -->
    <div class="hidden md:flex w-64 shrink-0 card flex-col gap-2 overflow-hidden">
      <div class="flex items-center justify-between">
        <h3 class="font-semibold text-gray-700 text-sm">{{ $t('ai_chat.history_title') }}</h3>
        <button @click="newChat" class="text-blue-500 text-sm hover:text-blue-600">{{ $t('ai_chat.new_chat') }}</button>
      </div>

      <!-- Subject filter tabs -->
      <div class="flex flex-wrap gap-1">
        <button
          v-for="(k, idx) in filterKeys"
          :key="k"
          @click="filterSubject = k"
          class="text-xs px-2 py-0.5 rounded-full border transition-colors"
          :class="filterSubject === k
            ? 'bg-blue-500 text-white border-blue-500'
            : 'bg-white text-gray-500 border-gray-200 hover:border-blue-300 hover:text-blue-500'"
        >{{ filterLabels[idx] }}</button>
      </div>

      <div class="flex-1 overflow-y-auto space-y-1">
        <div v-if="filteredSessions.length === 0" class="text-center py-8 text-gray-400 text-sm">{{ $t('ai_chat.no_history') }}</div>

        <!-- Group by subject -->
        <template v-if="filterSubject === 'all'">
          <template v-for="(group, subject) in groupedSessions" :key="subject">
            <!-- Subject group header -->
            <div class="flex items-center gap-1 px-1 pt-2 pb-0.5">
              <span class="text-xs font-semibold text-gray-400 uppercase tracking-wide">{{ subject }}</span>
              <span class="text-xs text-gray-300">({{ group.length }})</span>
            </div>
            <!-- Sessions in this subject group -->
            <div v-for="s in group" :key="s.id"
              @click="loadSession(s.id)"
              class="session-item group p-2.5 rounded-lg cursor-pointer text-sm transition-colors relative"
              :class="currentSessionId === s.id ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50 text-gray-600'">
              <p class="font-medium truncate pr-6">{{ s.title }}</p>
              <p class="text-xs text-gray-400">{{ s.message_count }} {{ $t('ai_chat.message_count_unit') }}</p>
              <button
                @click.stop="confirmDeleteSession(s)"
                class="delete-btn absolute right-2 top-1/2 -translate-y-1/2 w-5 h-5 flex items-center justify-center rounded text-gray-400 hover:text-red-500 hover:bg-red-50 opacity-0 group-hover:opacity-100 transition-opacity"
                :title="$t('ai_chat.delete_session')">
                ✕
              </button>
            </div>
          </template>
        </template>

        <!-- Single subject filter view -->
        <template v-else>
          <div v-for="s in filteredSessions" :key="s.id"
            @click="loadSession(s.id)"
            class="session-item group p-2.5 rounded-lg cursor-pointer text-sm transition-colors relative"
            :class="currentSessionId === s.id ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50 text-gray-600'">
            <p class="font-medium truncate pr-6">{{ s.title }}</p>
            <p class="text-xs text-gray-400">{{ s.subject }} · {{ s.message_count }} {{ $t('ai_chat.message_count_unit') }}</p>
            <button
              @click.stop="confirmDeleteSession(s)"
              class="delete-btn absolute right-2 top-1/2 -translate-y-1/2 w-5 h-5 flex items-center justify-center rounded text-gray-400 hover:text-red-500 hover:bg-red-50 opacity-0 group-hover:opacity-100 transition-opacity"
              :title="$t('ai_chat.delete_session')">
              ✕
            </button>
          </div>
        </template>
      </div>
    </div>

    <!-- Chat area -->
    <div class="flex-1 card flex flex-col overflow-hidden">
      <!-- Subject selector + mobile session button -->
      <div class="flex items-center gap-2 sm:gap-3 pb-3 border-b border-gray-100 shrink-0 flex-wrap">
        <!-- Mobile: session list button -->
        <button
          @click="showSessionDrawer = true"
          class="md:hidden px-3 py-1 text-sm bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors"
        >
          📋 {{ $t('ai_chat.session_list_title') }}
        </button>

        <span class="text-sm text-gray-500 hidden sm:inline">{{ $t('ai_chat.subject_label') }}</span>
        <el-select
          v-model="selectedSubject"
          size="small"
          style="width: 100px"
          :disabled="!isNewChat"
          :title="!isNewChat ? $t('ai_chat.history_locked') : ''"
        >
          <el-option v-for="s in subjects" :key="s" :label="s" :value="s" />
        </el-select>
        <span v-if="!isNewChat" class="text-xs text-gray-400 hidden sm:inline">{{ $t('ai_chat.history_locked_hint') }}</span>
      </div>

      <!-- Message area -->
      <div ref="messagesEl" class="flex-1 overflow-y-auto py-2 sm:py-4 space-y-2 sm:space-y-4 px-2 sm:px-4">
        <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full text-gray-400">
          <span class="text-4xl sm:text-5xl mb-2 sm:mb-4">🤖</span>
          <p class="text-base sm:text-lg font-medium text-center">{{ $t('ai_chat.welcome_prompt') }}</p>
          <p class="text-xs sm:text-sm mt-1 sm:mt-2 text-center text-gray-500">{{ $t('ai_chat.welcome_hint') }}</p>
        </div>

        <div v-for="msg in messages" :key="msg.id || msg.tempId" class="flex gap-2 sm:gap-3"
          :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
          <!-- AI avatar (hidden on mobile) -->
          <div v-if="msg.role === 'assistant'" class="hidden sm:flex w-8 h-8 bg-blue-500 rounded-full items-center justify-center text-white text-sm shrink-0 mt-1">
            🤖
          </div>
          <!-- Message content -->
          <div class="max-w-xs sm:max-w-2xl">
            <!-- User message: supports LaTeX rendering (preserves newlines) -->
            <template v-if="msg.role === 'user'">
              <!-- User uploaded problem images -->
              <div v-if="msg.uploadedImages && msg.uploadedImages.length > 0"
                class="flex flex-wrap gap-2 justify-end mb-1">
                <el-image
                  v-for="(img, ii) in msg.uploadedImages"
                  :key="ii"
                  :src="img.url"
                  :preview-src-list="msg.uploadedImages.map(u => u.url)"
                  :initial-index="ii"
                  fit="cover"
                  class="w-20 h-20 rounded-lg border border-blue-200 cursor-pointer"
                  preview-teleported
                />
              </div>
              <!-- User text (may be empty when image-only, no bubble rendered) -->
              <div v-if="msg.content && msg.content.trim()"
                class="px-3 sm:px-4 py-2 sm:py-3 rounded-2xl text-xs sm:text-sm leading-relaxed bg-blue-500 text-white rounded-tr-sm user-message-content"
                v-html="renderUserMessage(msg.content)">
              </div>
            </template>
            <!-- AI message: Markdown + LaTeX rich text rendering + images -->
            <div v-else :data-msg-key="msg.id || msg.tempId" class="ai-message-content px-3 sm:px-4 py-2 sm:py-3 rounded-2xl rounded-tl-sm bg-gray-100 text-gray-800 text-xs sm:text-sm">

              <div class="markdown-body" v-dyn-figures v-html="renderMessageWithImagePlaceholders(msg.content)"></div>
              <span v-if="msg.streaming" class="typing-cursor"></span>
              <!-- Image display area: fully loaded images -->
              <template v-if="!msg.streaming && msg.imageBlocks && msg.imageBlocks.length > 0">
                <div v-for="(block, bi) in msg.imageBlocks" :key="bi" class="mt-3">
                  <div class="image-block-label text-xs text-gray-500 mb-1.5 flex items-center gap-1">
                    <span>📷</span>
                    <span>{{ $t('ai_chat.ref_image') }}{{ block.keyword }}</span>
                  </div>
                  <div v-if="block.loading" class="image-loading-placeholder">
                    <span class="text-xs text-gray-400">{{ $t('ai_chat.searching_image') }}</span>
                  </div>
                  <div v-else-if="block.images && block.images.length > 0" class="image-grid">
                    <a
                      v-for="(img, ii) in block.images"
                      :key="ii"
                      :href="img.source_url"
                      target="_blank"
                      rel="noopener noreferrer"
                      class="image-card"
                      :title="img.title">
                      <img
                        :src="img.thumbnail || img.url"
                        :alt="img.title"
                        class="image-card-img"
                        loading="lazy"
                        @error="onImgError($event)"
                      />
                      <div class="image-card-caption">{{ img.title }}</div>
                    </a>
                  </div>
                  <div v-else class="text-xs text-gray-400 italic">{{ $t('ai_chat.no_image_found') }}</div>
                </div>
              </template>
              <!-- Streaming: show image search placeholders -->
              <template v-if="msg.streaming && msg.pendingImageKeywords && msg.pendingImageKeywords.length > 0">
                <div v-for="kw in msg.pendingImageKeywords" :key="kw" class="mt-3">
                  <div class="image-loading-placeholder">
                    <span class="text-xs text-gray-400">🔍 {{ $t('ai_chat.searching_image_hint') }}{{ kw }}</span>
                  </div>
                </div>
              </template>
            </div>
            <!-- AI reply action buttons -->
            <div v-if="msg.role === 'assistant' && !msg.streaming && msg.id" class="flex gap-2 mt-1.5 ml-1">
              <button @click="copyMessage(msg)" class="text-xs text-gray-400 hover:text-blue-500 transition-colors">
                {{ copiedMsgId === (msg.id || msg.tempId) ? '✓ ' + $t('ai_chat.copied_btn') : '📋 ' + $t('ai_chat.copy_btn') }}
              </button>
              <button @click="handleFeedback(msg, 'thumbs_up')" class="text-xs text-gray-400 hover:text-green-500 transition-colors">👍</button>
              <button @click="handleFeedback(msg, 'thumbs_down')" class="text-xs text-gray-400 hover:text-red-500 transition-colors">👎</button>
              <button @click="addToWrongBook(msg)" class="text-xs text-gray-400 hover:text-blue-500 transition-colors">➕ {{ $t('ai_chat.add_to_wrong_book') }}</button>
              <button @click="exportPdf(msg)" :disabled="exportingMsgId !== null" class="text-xs text-gray-400 hover:text-blue-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                {{ exportingMsgId === (msg.id || msg.tempId) ? $t('ai_chat.exporting') : '📄 ' + $t('ai_chat.export_pdf') }}
              </button>
              <!-- TTS button: only shown for Chinese/English subjects -->
              <template v-if="isTtsSubject">
                <template v-if="ttsState === 'idle' || ttsActiveMsgId !== (msg.id || msg.tempId)">
                  <button @click="startSpeech(msg)" class="text-xs text-gray-400 hover:text-indigo-500 transition-colors">
                    🔊 {{ $t('ai_chat.tts_read') }}
                  </button>
                </template>
                <template v-else-if="ttsState === 'playing'">
                  <span class="tts-wave-bar" aria-hidden="true">
                    <span></span><span></span><span></span><span></span>
                  </span>
                  <button @click="togglePauseSpeech" class="text-xs text-amber-500 hover:text-amber-600 transition-colors">⏸ {{ $t('ai_chat.tts_pause') }}</button>
                  <button @click="stopSpeech" class="text-xs text-gray-400 hover:text-red-500 transition-colors">⏹ {{ $t('ai_chat.tts_stop') }}</button>
                </template>
                <template v-else-if="ttsState === 'paused'">
                  <button @click="togglePauseSpeech" class="text-xs text-green-500 hover:text-green-600 transition-colors">▶ {{ $t('ai_chat.tts_resume') }}</button>
                  <button @click="stopSpeech" class="text-xs text-gray-400 hover:text-red-500 transition-colors">⏹ {{ $t('ai_chat.tts_stop') }}</button>
                  <span class="text-xs text-gray-400">{{ $t('ai_chat.tts_paused') }}</span>
                </template>
              </template>
            </div>
          </div>
          <!-- User avatar -->
          <div v-if="msg.role === 'user'" class="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center text-white text-sm shrink-0 mt-1">
            👤
          </div>
        </div>

        <!-- AI thinking indicator -->
        <div v-if="isLoading" class="flex gap-3">
          <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm">🤖</div>
          <div class="bg-gray-100 px-4 py-3 rounded-2xl rounded-tl-sm">
            <span class="text-gray-500 text-sm">{{ $t('ai_chat.thinking') }}</span>
            <span class="inline-flex gap-1 ml-2">
              <span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay:0ms"></span>
              <span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay:150ms"></span>
              <span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay:300ms"></span>
            </span>
          </div>
        </div>
      </div>

      <!-- Input area -->
      <div class="border-t border-gray-100 pt-2 sm:pt-3 px-2 sm:px-0 shrink-0">
        <!-- Image upload area (collapsible) -->
        <div v-show="showImageUpload" class="mb-2">
          <ImageUploadArea
            ref="imageUploadRef"
            :max-count="5"
            :max-size-m-b="10"
            @images-selected="handleImagesSelected"
          />
        </div>
        <!-- Selected image count hint -->
        <div v-if="selectedImages.length > 0 && !showImageUpload" class="mb-2 text-xs text-gray-500">
          {{ $t('ai_chat.images_selected', { n: selectedImages.length }) }}
        </div>
        <!-- Real-time LaTeX preview (shown when input has content) -->
        <div v-if="inputText.trim()" class="mb-2 px-3 py-2 bg-blue-50 border border-blue-100 rounded-xl text-xs sm:text-sm text-gray-700 leading-relaxed input-preview-content"
          v-html="renderUserMessage(inputText)">
        </div>
        <div class="flex gap-2 items-end">
          <el-button
            :type="showImageUpload || selectedImages.length ? 'primary' : 'default'"
            @click="showImageUpload = !showImageUpload"
            size="small"
            class="shrink-0"
            :title="$t('ai_chat.upload_image')"
            :icon="UploadFilled"
          />
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="2"
            :placeholder="$t('ai_chat.send_placeholder')"
            class="flex-1 text-xs sm:text-sm"
            @keydown.enter.exact.prevent="sendMessage"
            resize="none"
          />
          <el-button type="primary" @click="sendMessage" :disabled="(!inputText.trim() && selectedImages.length === 0) || isLoading" size="small" class="shrink-0">
            {{ $t('ai_chat.send_btn') }}
          </el-button>
        </div>
      </div>
    </div>

    <!-- Mobile session list drawer (mobile only) -->
    <SessionDrawer
      v-model="showSessionDrawer"
      :sessions="sessions"
      :current-session-id="currentSessionId"
      :subjects="subjects"
      @new-chat="newChat"
      @select-session="loadSession"
      @delete-session="confirmDeleteSession"
      @filter-subject="onFilterSubject"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { aiApi } from '@/api/ai'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { renderMessage, renderLatexOnly } from '@/utils/markdown'
import { searchEducationalImages } from '@/utils/imageSearch'
import SessionDrawer from '@/components/shared/SessionDrawer.vue'
import ImageUploadArea from '@/components/shared/ImageUploadArea.vue'
import { buildChatFormData } from '@/api/image'
import { isPictureFile, getImagePreviewUrl } from '@/utils/imageUpload'
import { setupLongPressCopyGesture } from '@/utils/touchGestures'


// ===================== Type definitions =====================
interface ImageItem {
  url: string
  thumbnail: string
  title: string
  description: string
  source_url: string
}

interface ImageBlock {
  keyword: string
  loading: boolean
  images: ImageItem[]
}

/** Problem images uploaded by user with messages (distinct from AI-fetched ImageBlock) */
interface UploadedImage {
  id?: string
  url: string
}

interface ChatMessage {
  id?: number
  tempId?: number
  role: 'user' | 'assistant'
  content: string
  streaming?: boolean
  feedback?: string
  imageBlocks?: ImageBlock[]
  pendingImageKeywords?: string[]
  uploadedImages?: UploadedImage[]
}

// ===================== Image marker processing =====================

/** 从 AI 回复内容中提取所有 [[IMAGE:关键词]] 标记的关键词列表 */
function extractImageKeywords(content: string): string[] {
  const pattern = /\[\[IMAGE:([^\]]+)\]\]/gi
  const keywords: string[] = []
  let match
  while ((match = pattern.exec(content)) !== null) {
    const kw = match[1].trim()
    if (kw && !keywords.includes(kw)) {
      keywords.push(kw)
    }
  }
  return keywords
}

/**
 * 渲染消息内容：将 [[IMAGE:xxx]] 标记替换为"图片占位锚点"
 * 实际图片由 imageBlocks 数据驱动渲染，此处只去掉标记文字避免显示在正文中
 */
function renderMessageWithImagePlaceholders(content: string): string {
  // Strip [[IMAGE:...]] markers (images rendered by imageBlocks section below)
  const cleaned = content.replace(/\[\[IMAGE:[^\]]*\]\]/gi, '')
  return renderMessage(cleaned)
}

/**
 * Render user message: supports LaTeX formulas while preserving newlines (\n → <br>).
 */
function renderUserMessage(content: string): string {
  const withLatex = renderLatexOnly(content)
  return withLatex.replace(/\n/g, '<br>')
}

// ===================== State =====================
const { t } = useI18n()
const authStore = useAuthStore()
const subjectKeys = ['math', 'physics', 'chemistry', 'biology', 'chinese', 'english', 'history', 'geography', 'politics']
const subjects = computed(() => subjectKeys.map(k => t('subjects.' + k)))
const filterKeys = computed(() => ['all', ...subjectKeys])
const filterLabels = computed(() => [t('ai_chat.filter_all'), ...subjects.value])
const selectedSubject = ref(t('subjects.math'))
const inputText = ref('')
const messages = ref<ChatMessage[]>([])
const sessions = ref<any[]>([])
const currentSessionId = ref<string | null>(null)
const isLoading = ref(false)
const messagesEl = ref<HTMLElement>()
const copiedMsgId = ref<number | null>(null)
const exportingMsgId = ref<number | null>(null)

// ===================== Image upload state =====================
/** Problem images currently selected, to be sent with next message */
const selectedImages = ref<File[]>([])
/** Whether the image upload area is expanded */
const showImageUpload = ref(false)
const imageUploadRef = ref<InstanceType<typeof ImageUploadArea> | null>(null)

function handleImagesSelected(files: File[]) {
  selectedImages.value = files
}

/** Subject filter for left session list ('all' or subjectKey) */
const filterSubject = ref('all')
/** Key corresponding to the currently selected subject */
const selectedSubjectKey = computed(() => {
  const idx = subjects.value.indexOf(selectedSubject.value)
  return idx !== -1 ? subjectKeys[idx] : 'math'
})

/** Whether the mobile session list drawer is visible */
const showSessionDrawer = ref(false)

/** Message cache by session: avoids reloading already-fetched messages */
const messagesCacheMap = ref<Map<string, ChatMessage[]>>(new Map())

/** Whether this is a new chat (not bound to a history session) */
const isNewChat = computed(() => currentSessionId.value === null)

// ===================== Subject grouping & filtering =====================

/** Group sessions by subject (used for the "All" view in the left panel) */
const groupedSessions = computed(() => {
  const groups: Record<string, any[]> = {}
  for (const s of sessions.value) {
    const subj = s.subject || t('ai_chat.session_other_subject')
    if (!groups[subj]) groups[subj] = []
    groups[subj].push(s)
  }
  return groups
})

/** Session list filtered by the current subject filter */
const filteredSessions = computed(() => {
  if (filterSubject.value === 'all') return sessions.value
  // filterSubject stores a subjectKey; translate to display label for backend-stored subject comparison
  const label = t('subjects.' + filterSubject.value)
  return sessions.value.filter(s => s.subject === label || s.subject === filterSubject.value)
})

/** Map a subject value emitted by SessionDrawer or filter buttons to subjectKey or 'all' */
function onFilterSubject(s: string) {
  if (!s || s === t('ai_chat.filter_all')) {
    filterSubject.value = 'all'
  } else {
    const idx = subjects.value.indexOf(s)
    filterSubject.value = idx !== -1 ? subjectKeys[idx] : s
  }
}

// ===================== Utility functions =====================
async function scrollToBottom() {
  await nextTick()
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}

/** Hide broken image element on load error */
function onImgError(event: Event) {
  const img = event.target as HTMLImageElement
  if (img) {
    img.style.display = 'none'
  }
}

// ===================== Image search =====================
/** Fetch images for all [[IMAGE:...]] keywords in an AI message */
async function fetchImagesForMessage(msg: ChatMessage) {
  const keywords = extractImageKeywords(msg.content)
  if (keywords.length === 0) return

  // Initialize imageBlocks (loading state)
  msg.imageBlocks = keywords.map(kw => ({
    keyword: kw,
    loading: true,
    images: [],
  }))
  msg.pendingImageKeywords = []
  await scrollToBottom()

  // Search images per keyword (frontend calls Wikimedia API directly, no backend relay needed)
  for (let i = 0; i < keywords.length; i++) {
    const kw = keywords[i]
    try {
      const imgs = await searchEducationalImages(kw, 3)
      if (msg.imageBlocks && msg.imageBlocks[i]) {
        msg.imageBlocks[i].loading = false
        msg.imageBlocks[i].images = imgs
      }
    } catch {
      if (msg.imageBlocks && msg.imageBlocks[i]) {
        msg.imageBlocks[i].loading = false
        msg.imageBlocks[i].images = []
      }
    }
    await scrollToBottom()
  }
}

// ===================== Session management =====================
async function loadSessions() {
  try {
    const res: any = await aiApi.getSessions()
    sessions.value = res.data.items || []
  } catch {}
}

async function loadSession(sessionId: string) {
  currentSessionId.value = sessionId
  // Find the subject of this session and lock the subject selector
  const session = sessions.value.find(s => s.id === sessionId)
  if (session?.subject) {
    selectedSubject.value = session.subject
  }

  // Check cache: use cached messages if this session was already loaded
  if (messagesCacheMap.value.has(sessionId)) {
    const cachedMsgs = messagesCacheMap.value.get(sessionId)!
    messages.value = cachedMsgs
    await scrollToBottom()
    // Fetch images for cached AI messages that haven't loaded images yet
    for (const msg of messages.value) {
      if (msg.role === 'assistant' && (!msg.imageBlocks || msg.imageBlocks.length === 0)) {
        fetchImagesForMessage(msg)
      }
    }
    return
  }

  try {
    const res: any = await aiApi.getMessages(sessionId)
    const rawMsgs: any[] = res.data || []
    // Also search images for historical messages after loading
    messages.value = rawMsgs.map(m => ({
      ...m,
      imageBlocks: [],
      pendingImageKeywords: [],
      // Map backend images: [{id, url}] to uploaded image previews
      uploadedImages: Array.isArray(m.images) ? m.images : [],
    }))
    // Cache messages for this session
    messagesCacheMap.value.set(sessionId, messages.value)
    await scrollToBottom()
    // Load images for each historical AI message (non-blocking)
    for (const msg of messages.value) {
      if (msg.role === 'assistant') {
        fetchImagesForMessage(msg)
      }
    }
  } catch {}
}

function newChat() {
  currentSessionId.value = null
  messages.value = []
  // Reset to default subject on new chat (user can freely choose)
  selectedSubject.value = t('subjects.math')
}

// ===================== Send message =====================
async function sendMessage() {
  const text = inputText.value.trim()
  const imagesToSend = selectedImages.value.slice()
  // Allow image-only or image+text, but not both empty
  if ((!text && imagesToSend.length === 0) || isLoading.value) return

  // Add user message (with local image previews, shown immediately)
  const userMsg: ChatMessage = {
    tempId: Date.now(),
    role: 'user',
    content: text,
    uploadedImages: imagesToSend
      .filter(isPictureFile)
      .map((f) => ({ url: getImagePreviewUrl(f) })),
  }
  messages.value.push(userMsg)
  inputText.value = ''
  // Clear image selection and upload area
  selectedImages.value = []
  showImageUpload.value = false
  imageUploadRef.value?.clear()
  await scrollToBottom()

  // Create AI reply placeholder
  const aiMsg = ref<ChatMessage>({
    tempId: Date.now() + 1,
    role: 'assistant',
    content: '',
    streaming: true,
    imageBlocks: [],
    pendingImageKeywords: [],
  })
  messages.value.push(aiMsg.value)
  isLoading.value = true

  try {
    const token = authStore.token
    // Backend /api/ai/chat uses multipart form params (Form/File),
    // so we always use FormData (images field is empty when no images).
    // Do NOT set Content-Type manually — let the browser include the multipart boundary.
    const body = buildChatFormData({
      sessionId: currentSessionId.value,
      question: text || t('ai_chat.image_question_default'),
      subject: selectedSubject.value,
      images: imagesToSend,
    })
    const response = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body,
    })

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error(t('ai_chat.auth_expired'))
      }
      throw new Error(t('ai_chat.request_failed_status', { status: response.status }))
    }

    const reader = response.body!.getReader()
    const decoder = new TextDecoder()
    // Buffer: accumulate partial data to avoid SSE events being split by TCP segmentation
    let buffer = ''

    // Process a single SSE data line
    const handleLine = async (line: string) => {
      if (!line.startsWith('data: ')) return
      const payload = line.slice(6).trim()
      if (!payload) return
      let data: any
      try {
        data = JSON.parse(payload)
      } catch {
        // Incomplete or invalid JSON — ignore (full data will be reparsed after accumulation)
        return
      }
      if (data.type === 'content') {
        aiMsg.value.content += data.delta
        // Update pending image keywords in real time (show search placeholders during streaming)
        aiMsg.value.pendingImageKeywords = extractImageKeywords(aiMsg.value.content)
        await scrollToBottom()
      } else if (data.type === 'done') {
        aiMsg.value.streaming = false
        aiMsg.value.pendingImageKeywords = []
        if (data.message_id) aiMsg.value.id = data.message_id
        if (data.session_id) {
          const isFirstMessage = !currentSessionId.value
          currentSessionId.value = data.session_id
          if (isFirstMessage) {
            // Refresh session list after first message in a new session
            await loadSessions()
          }
        }
        // After AI reply is complete, search images (non-blocking)
        fetchImagesForMessage(aiMsg.value)
      }
    }

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      // stream: true ensures multi-byte UTF-8 characters (e.g. Chinese) are not split across chunks
      buffer += decoder.decode(value, { stream: true })

      // Only process fully received lines (ending with newline); incomplete data stays in buffer
      let newlineIndex: number
      while ((newlineIndex = buffer.indexOf('\n')) !== -1) {
        const line = buffer.slice(0, newlineIndex)
        buffer = buffer.slice(newlineIndex + 1)
        await handleLine(line)
      }
    }

    // Process the last line remaining in the buffer after stream ends (may lack trailing newline)
    buffer += decoder.decode()
    if (buffer.trim()) {
      await handleLine(buffer)
    }
  } catch (e) {

    aiMsg.value.content = t('ai_chat.request_failed')
    aiMsg.value.streaming = false
    aiMsg.value.pendingImageKeywords = []
  } finally {
    isLoading.value = false
  }
}

// ===================== Copy =====================
/** Copy AI reply content (raw Markdown text with [[IMAGE:...]] markers stripped) */
async function copyMessage(msg: ChatMessage) {
  const text = msg.content.replace(/\[\[IMAGE:[^\]]*\]\]/gi, '').trim()
  if (!text) return
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
    } else {
      // Fallback for non-secure contexts (e.g. http) where navigator.clipboard is unavailable
      const textarea = document.createElement('textarea')
      textarea.value = text
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      document.body.appendChild(textarea)
      textarea.focus()
      textarea.select()
      // execCommand is deprecated, but it's the only fallback in non-secure (http) contexts
      // where navigator.clipboard is unavailable; use 'as any' to suppress the type-level deprecation warning.
      ;(document as any).execCommand('copy')
      document.body.removeChild(textarea)
    }
    copiedMsgId.value = (msg.id || msg.tempId) ?? null
    ElMessage.success(t('ai_chat.copy_success'))
    setTimeout(() => {
      if (copiedMsgId.value === ((msg.id || msg.tempId) ?? null)) {
        copiedMsgId.value = null
      }
    }, 2000)
  } catch {
    ElMessage.error(t('ai_chat.copy_failed'))
  }
}

// ===================== Export PDF =====================
/** HTML-escape a string to prevent XSS */
function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

/**
 * Export an AI answer (with Markdown and LaTeX) as PDF.
 * Uses the 'new window print' approach: write HTML with print styles to a new window,
 * let the browser's native print dialog handle 'Save as PDF', avoiding html2canvas compatibility issues.
 */
async function exportPdf(msg: ChatMessage) {
  if (exportingMsgId.value !== null) return
  const key = (msg.id || msg.tempId) ?? null
  if (key === null) return

  // Strip [[IMAGE:...]] markers then render Markdown + LaTeX
  const cleaned = msg.content.replace(/\[\[IMAGE:[^\]]*\]\]/gi, '').trim()
  if (!cleaned) {
    ElMessage.error(t('ai_chat.export_no_content'))
    return
  }

  exportingMsgId.value = key
  try {
    const reportHtml = renderMessage(cleaned)
    const dateStr = new Date().toLocaleDateString('zh-CN')

    const fullHtml = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>${escapeHtml(t('ai_chat.pdf_title'))}</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #ffffff;
    color: #1f2937;
    font-family: "PingFang SC", "Microsoft YaHei", "SimSun", sans-serif;
    font-size: 14px;
    line-height: 1.8;
  }
  .page {
    width: 210mm;
    min-height: 297mm;
    padding: 20mm 18mm;
    margin: 0 auto;
    background: white;
  }
  .header { margin-bottom: 20px; padding-bottom: 16px; border-bottom: 2px solid #e5e7eb; }
  .header h1 { font-size: 22px; font-weight: 700; color: #111827; margin-bottom: 10px; }
  .header-meta { display: flex; flex-wrap: wrap; gap: 16px; font-size: 13px; color: #6b7280; }
  p { margin: 0.5em 0; color: #374151; }
  strong, b { font-weight: 700; color: #111827; }
  em, i { font-style: italic; }
  h1 { font-size: 1.3em; font-weight: 700; margin: 1em 0 0.5em; color: #111827; }
  h2 { font-size: 1.15em; font-weight: 700; margin: 0.9em 0 0.4em; color: #1d4ed8; border-bottom: 1px solid #e0e7ff; padding-bottom: 4px; }
  h3 { font-size: 1.05em; font-weight: 700; margin: 0.8em 0 0.3em; color: #1f2937; }
  h4, h5, h6 { font-size: 1em; font-weight: 700; margin: 0.7em 0 0.3em; color: #374151; }
  ul, ol { padding-left: 1.8em; margin: 0.5em 0; }
  li { margin: 0.3em 0; color: #374151; }
  table { width: 100%; border-collapse: collapse; margin: 0.8em 0; font-size: 0.9em; page-break-inside: avoid; }
  th { background: #f1f5f9; padding: 8px 12px; font-weight: 600; border: 1px solid #cbd5e1; text-align: left; color: #1f2937; }
  td { padding: 6px 12px; border: 1px solid #cbd5e1; color: #374151; }
  tr:nth-child(even) td { background: #f8fafc; }
  code { background: #f1f5f9; border-radius: 3px; padding: 0.1em 0.4em; font-family: "Courier New", monospace; font-size: 0.88em; color: #1e293b; }
  pre { background: #1e293b; border-radius: 6px; padding: 1em; overflow: hidden; margin: 0.5em 0; page-break-inside: avoid; }
  pre code { background: transparent; color: #e2e8f0; padding: 0; }
  blockquote { border-left: 4px solid #3b82f6; padding: 0.5em 1em; margin: 0.5em 0; color: #4b5563; background: #eff6ff; border-radius: 0 6px 6px 0; }
  hr { border: none; border-top: 1px solid #e5e7eb; margin: 1em 0; }
  a { color: #2563eb; text-decoration: none; }
  svg { max-width: 100%; height: auto; }
  .footer { margin-top: 24px; padding-top: 10px; border-top: 1px solid #e5e7eb; font-size: 11px; color: #9ca3af; text-align: center; }
  /* KaTeX formula styles */
  .katex { font-size: 1em; }
  .katex-display { margin: 0.6em 0; }
  /* Print styles */
  @media print {
    body { padding: 0; }
    .page { padding: 15mm 15mm; width: 100%; }
    .no-print { display: none !important; }
    pre, blockquote, table { page-break-inside: avoid; }
    h2, h3 { page-break-after: avoid; }
  }
  @page {
    size: A4;
    margin: 0;
  }
</style>
<!-- Load KaTeX styles from CDN for correct formula rendering -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.22/dist/katex.min.css" crossorigin="anonymous">
</head>
<body>
<div class="page">
  <div class="header">
    <h1>${escapeHtml(t('ai_chat.pdf_title'))}</h1>
    <div class="header-meta">
      <span>${escapeHtml(t('ai_chat.pdf_subject_label'))}${escapeHtml(selectedSubject.value)}</span>
      <span>${escapeHtml(t('ai_chat.pdf_export_time'))}${escapeHtml(dateStr)}</span>
    </div>
  </div>
  <div class="report-body">${reportHtml}</div>
  <div class="footer">${escapeHtml(t('ai_chat.pdf_footer', { date: dateStr }))}</div>
  <!-- Auto-print button area -->
  <div class="no-print" style="position:fixed;bottom:20px;right:20px;display:flex;gap:10px;z-index:9999;">
    <button onclick="window.print()" style="padding:10px 24px;background:#2563eb;color:white;border:none;border-radius:8px;font-size:14px;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,0.2);">
      🖨️ ${escapeHtml(t('ai_chat.pdf_print_btn'))}
    </button>
    <button onclick="window.close()" style="padding:10px 16px;background:#6b7280;color:white;border:none;border-radius:8px;font-size:14px;cursor:pointer;">
      ✕ ${escapeHtml(t('ai_chat.pdf_close_btn'))}
    </button>
  </div>
</div>
<script>
  // Wait for KaTeX and fonts to load, then auto-open print dialog
  window.addEventListener('load', function() {
    setTimeout(function() { window.print(); }, 800);
  });
<\/script>
</body>
</html>`

    const printWindow = window.open('', '_blank', 'width=900,height=700')
    if (!printWindow) {
      throw new Error(t('ai_chat.popup_blocked'))
    }
    // Use Blob URL to load export document (replaces deprecated document.write)
    const blobUrl = URL.createObjectURL(new Blob([fullHtml], { type: 'text/html' }))
    printWindow.location.href = blobUrl
    // Delay revoke to ensure the new window has finished loading and printing
    setTimeout(() => URL.revokeObjectURL(blobUrl), 60000)

    ElMessage.success(t('ai_chat.export_print_hint'))
  } catch (err: any) {
    ElMessage.error(t('ai_chat.export_failed', { msg: err?.message || '' }))
  } finally {
    exportingMsgId.value = null
  }
}


// ===================== Feedback & mistake notebook =====================
async function handleFeedback(msg: ChatMessage, rating: string) {


  try {
    await aiApi.feedback(msg.id!, { rating })
    ElMessage.success(rating === 'thumbs_up' ? t('ai_chat.feedback_positive') : t('ai_chat.feedback_negative'))
  } catch {}
}

async function addToWrongBook(msg: ChatMessage) {
  try {
    const idx = messages.value.indexOf(msg)
    const userMsg = messages.value[idx - 1]
    if (!userMsg || !msg.id) return
    await aiApi.addToWrongBook(userMsg.id || msg.id, { subject: selectedSubject.value, tags: [] })
    ElMessage.success(t('ai_chat.add_to_wrong_book_success'))
  } catch {}
}

async function confirmDeleteSession(session: any) {
  try {
    await ElMessageBox.confirm(
      t('ai_chat.delete_session_confirm_msg', { title: session.title }),
      t('ai_chat.delete_session'),
      {
        confirmButtonText: t('common.delete'),
        cancelButtonText: t('common.cancel'),
        type: 'warning',
        confirmButtonClass: 'el-button--danger',
      }
    )
    await aiApi.deleteSession(session.id)
    if (currentSessionId.value === session.id) {
      currentSessionId.value = null
      messages.value = []
      selectedSubject.value = t('subjects.math')
    }
    await loadSessions()
    ElMessage.success(t('ai_chat.delete_session_success'))
  } catch (e: any) {
    if (e !== 'cancel' && e?.message !== 'cancel') {
      ElMessage.error(t('ai_chat.delete_failed'))
    }
  }
}

// ===================== Text-to-Speech (TTS) =====================

/** Subject keys that support TTS */
const TTS_SUBJECT_KEYS = ['chinese', 'english']

/** Whether the current subject supports TTS */
const isTtsSubject = computed(() => TTS_SUBJECT_KEYS.includes(selectedSubjectKey.value))

/** TTS playback state: idle / playing / paused */
const ttsState = ref<'idle' | 'playing' | 'paused'>('idle')

/** ID of the message currently being read aloud (msg.id or msg.tempId) */
const ttsActiveMsgId = ref<number | null>(null)

/** Pick the best available browser voice for the given subject key */
function pickVoice(subjectKey: string): SpeechSynthesisVoice | null {
  const voices = window.speechSynthesis.getVoices()
  if (subjectKey === 'english') {
    // English: prefer en-US, then en-GB, then any en-* voice
    return (
      voices.find(v => v.lang === 'en-US') ||
      voices.find(v => v.lang === 'en-GB') ||
      voices.find(v => v.lang.startsWith('en')) ||
      null
    )
  }
  // Chinese: prefer zh-CN, then zh-TW, then any zh-* voice
  return (
    voices.find(v => v.lang === 'zh-CN') ||
    voices.find(v => v.lang === 'zh-TW') ||
    voices.find(v => v.lang.startsWith('zh')) ||
    null
  )
}

/**
 * Convert AI reply (Markdown + LaTeX) to plain text suitable for TTS:
 * - Remove [[IMAGE:...]] markers
 * - Remove Markdown heading symbols (#)
 * - Remove bold/italic markers (** / *)
 * - Remove inline code backticks
 * - Replace LaTeX formulas ($...$ and $$...$$) with spoken placeholders
 * - Collapse excessive blank lines
 */
function msgToPlainText(content: string): string {
  let text = content
  // Remove image markers
  text = text.replace(/\[\[IMAGE:[^\]]*\]\]/gi, '')
  // 块级公式 $$...$$ → translated placeholder
  text = text.replace(/\$\$[\s\S]*?\$\$/g, t('ai_chat.tts_math_formula'))
  // 行内公式 $...$ → translated placeholder
  text = text.replace(/\$[^$\n]+\$/g, t('ai_chat.tts_math_formula'))
  // Markdown headings
  text = text.replace(/^#{1,6}\s+/gm, '')
  // Bold / italic
  text = text.replace(/\*{1,3}([^*]+)\*{1,3}/g, '$1')
  // Inline code
  text = text.replace(/`([^`]+)`/g, '$1')
  // Code blocks
  text = text.replace(/```[\s\S]*?```/g, t('ai_chat.tts_code_block'))
  // Horizontal rules
  text = text.replace(/^---+$/gm, '')
  // Collapse excessive blank lines
  text = text.replace(/\n{3,}/g, '\n\n')
  return text.trim()
}

/** Start reading an AI message aloud */
function startSpeech(msg: ChatMessage) {
  // Stop any in-progress speech
  window.speechSynthesis.cancel()
  ttsState.value = 'idle'
  ttsActiveMsgId.value = null

  const plainText = msgToPlainText(msg.content)
  if (!plainText) {
    ElMessage.warning(t('ai_chat.tts_no_text'))
    return
  }

  const utter = new SpeechSynthesisUtterance(plainText)

  // Set language based on subject
  if (selectedSubjectKey.value === 'english') {
    utter.lang = 'en-US'
    utter.rate = 0.9
  } else {
    utter.lang = 'zh-CN'
    utter.rate = 1.0
  }
  utter.pitch = 1.0
  utter.volume = 1.0

  // Try to use a specific voice
  const voice = pickVoice(selectedSubjectKey.value)
  if (voice) utter.voice = voice

  const msgKey = (msg.id || msg.tempId) ?? null

  utter.onstart = () => {
    ttsState.value = 'playing'
    ttsActiveMsgId.value = msgKey
  }
  utter.onpause = () => {
    ttsState.value = 'paused'
  }
  utter.onresume = () => {
    ttsState.value = 'playing'
  }
  utter.onend = () => {
    ttsState.value = 'idle'
    ttsActiveMsgId.value = null
  }
  utter.onerror = () => {
    ttsState.value = 'idle'
    ttsActiveMsgId.value = null
  }

  window.speechSynthesis.speak(utter)
  // Some browsers don't fire onstart, so manually set state
  ttsState.value = 'playing'
  ttsActiveMsgId.value = msgKey
}

/** Toggle pause / resume */
function togglePauseSpeech() {
  if (ttsState.value === 'playing') {
    window.speechSynthesis.pause()
    ttsState.value = 'paused'
  } else if (ttsState.value === 'paused') {
    window.speechSynthesis.resume()
    ttsState.value = 'playing'
  }
}

/** Stop speech */
function stopSpeech() {
  window.speechSynthesis.cancel()
  ttsState.value = 'idle'
  ttsActiveMsgId.value = null
}

// ===================== Lifecycle =====================
onMounted(async () => {
  await loadSessions()

  // Set up long-press copy gesture for messages
  setTimeout(() => {
    const messageContents = document.querySelectorAll('.markdown-body, .ai-message-content')
    messageContents.forEach((content) => {
      setupLongPressCopyGesture(content as HTMLElement)
    })
  }, 200)

  // Pre-load voice list (some browsers return empty on first getVoices(), need to trigger async load)
  if (typeof window !== 'undefined' && window.speechSynthesis) {
    window.speechSynthesis.getVoices()
  }
})

onUnmounted(() => {
  // Stop speech and release resources when leaving the page
  if (typeof window !== 'undefined' && window.speechSynthesis) {
    window.speechSynthesis.cancel()
  }
})
</script>

<style scoped>
/* Typing cursor animation */
.typing-cursor {
  display: inline-block;
  width: 2px;
  height: 1em;
  background-color: #6b7280;
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* AI message Markdown styles */
.markdown-body {
  font-size: 0.875rem;
  line-height: 1.75;
  word-break: break-word;
}

.markdown-body :deep(p) {
  margin: 0.4em 0;
}

.markdown-body :deep(p:first-child) {
  margin-top: 0;
}

.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-body :deep(strong) {
  font-weight: 600;
  color: #111827;
}

.markdown-body :deep(em) {
  font-style: italic;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 1.5em;
  margin: 0.4em 0;
}

.markdown-body :deep(li) {
  margin: 0.2em 0;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4) {
  font-weight: 600;
  margin: 0.6em 0 0.3em;
  color: #1f2937;
}

.markdown-body :deep(h1) { font-size: 1.1em; }
.markdown-body :deep(h2) { font-size: 1.05em; }
.markdown-body :deep(h3) { font-size: 1em; }

.markdown-body :deep(code) {
  background: rgba(0, 0, 0, 0.06);
  border-radius: 3px;
  padding: 0.1em 0.4em;
  font-family: 'Fira Code', 'Courier New', monospace;
  font-size: 0.9em;
}

.markdown-body :deep(pre) {
  background: #1e293b;
  border-radius: 8px;
  padding: 1em;
  overflow-x: auto;
  margin: 0.5em 0;
}

.markdown-body :deep(pre code) {
  background: transparent;
  color: #e2e8f0;
  padding: 0;
  font-size: 0.85em;
}

.markdown-body :deep(blockquote) {
  border-left: 3px solid #3b82f6;
  padding-left: 0.8em;
  margin: 0.4em 0;
  color: #4b5563;
}

.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid #e5e7eb;
  margin: 0.6em 0;
}

/* KaTeX formula style adjustments (AI messages) */
.markdown-body :deep(.katex-display) {
  margin: 0.6em 0;
  overflow-x: auto;
  overflow-y: hidden;
}

.markdown-body :deep(.katex) {
  font-size: 1em;
}

/* User message KaTeX styles: white formula text for blue background */
.user-message-content :deep(.katex) {
  font-size: 1em;
  color: white;
}

.user-message-content :deep(.katex-display) {
  margin: 0.4em 0;
  overflow-x: auto;
}

/* KaTeX internal SVG/path color inheritance */
.user-message-content :deep(.katex .mord),
.user-message-content :deep(.katex .mrel),
.user-message-content :deep(.katex .mop),
.user-message-content :deep(.katex .mbin),
.user-message-content :deep(.katex .mpunct),
.user-message-content :deep(.katex .minner),
.user-message-content :deep(.katex .mopen),
.user-message-content :deep(.katex .mclose) {
  color: white;
}

/* Input preview area KaTeX styles */
.input-preview-content :deep(.katex) {
  font-size: 1em;
}

.input-preview-content :deep(.katex-display) {
  margin: 0.3em 0;
  overflow-x: auto;
}

/* ============ Image styles ============ */

/* Image block label */
.image-block-label {
  color: #6b7280;
  font-size: 0.75rem;
  margin-bottom: 6px;
}

/* Image loading placeholder */
.image-loading-placeholder {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: #f9fafb;
  border: 1px dashed #d1d5db;
  border-radius: 8px;
  margin-top: 4px;
}

/* Image grid (up to 3 columns) */
.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 8px;
  margin-top: 4px;
}

/* Single image card */
.image-card {
  display: block;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
  text-decoration: none;
  background: #f9fafb;
  transition: box-shadow 0.2s, transform 0.2s;
}

.image-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

/* Image element */
.image-card-img {
  width: 100%;
  height: 100px;
  object-fit: cover;
  display: block;
  background: #e5e7eb;
}

/* Image caption */
.image-card-caption {
  padding: 4px 6px;
  font-size: 0.7rem;
  color: #6b7280;
  line-height: 1.3;
  max-height: 2.6em;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

/* ============ TTS audio wave animation ============ */

/* Four-bar container, vertically centered for inline alignment */
.tts-wave-bar {
  display: inline-flex;
  align-items: flex-end;
  gap: 2px;
  height: 14px;
  margin-right: 2px;
  vertical-align: middle;
}

/* Each bar */
.tts-wave-bar span {
  display: inline-block;
  width: 3px;
  border-radius: 2px;
  background: #6366f1; /* indigo-500 */
  animation: tts-wave 0.8s ease-in-out infinite;
}

.tts-wave-bar span:nth-child(1) { height: 6px;  animation-delay: 0ms; }
.tts-wave-bar span:nth-child(2) { height: 10px; animation-delay: 120ms; }
.tts-wave-bar span:nth-child(3) { height: 14px; animation-delay: 240ms; }
.tts-wave-bar span:nth-child(4) { height: 8px;  animation-delay: 360ms; }

@keyframes tts-wave {
  0%, 100% { transform: scaleY(0.4); opacity: 0.7; }
  50%       { transform: scaleY(1.0); opacity: 1.0; }
}
</style>
