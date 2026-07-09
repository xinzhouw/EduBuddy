<template>
  <div class="flex h-full gap-3 sm:gap-4 overflow-hidden" style="height: calc(100vh - 160px)">
    <!-- 历史会话列表（PC 端固定，移动端改为按钮触发抽屉） -->
    <div class="hidden md:flex w-64 shrink-0 card flex-col gap-2 overflow-hidden">
      <div class="flex items-center justify-between">
        <h3 class="font-semibold text-gray-700 text-sm">历史对话</h3>
        <button @click="newChat" class="text-blue-500 text-sm hover:text-blue-600">+ 新对话</button>
      </div>

      <!-- 学科过滤标签 -->
      <div class="flex flex-wrap gap-1">
        <button
          v-for="s in ['全部', ...subjects]"
          :key="s"
          @click="filterSubject = s"
          class="text-xs px-2 py-0.5 rounded-full border transition-colors"
          :class="filterSubject === s
            ? 'bg-blue-500 text-white border-blue-500'
            : 'bg-white text-gray-500 border-gray-200 hover:border-blue-300 hover:text-blue-500'"
        >{{ s }}</button>
      </div>

      <div class="flex-1 overflow-y-auto space-y-1">
        <div v-if="filteredSessions.length === 0" class="text-center py-8 text-gray-400 text-sm">暂无历史对话</div>

        <!-- 按学科分组显示 -->
        <template v-if="filterSubject === '全部'">
          <template v-for="(group, subject) in groupedSessions" :key="subject">
            <!-- 学科分组标题 -->
            <div class="flex items-center gap-1 px-1 pt-2 pb-0.5">
              <span class="text-xs font-semibold text-gray-400 uppercase tracking-wide">{{ subject }}</span>
              <span class="text-xs text-gray-300">({{ group.length }})</span>
            </div>
            <!-- 该学科下的会话 -->
            <div v-for="s in group" :key="s.id"
              @click="loadSession(s.id)"
              class="session-item group p-2.5 rounded-lg cursor-pointer text-sm transition-colors relative"
              :class="currentSessionId === s.id ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50 text-gray-600'">
              <p class="font-medium truncate pr-6">{{ s.title }}</p>
              <p class="text-xs text-gray-400">{{ s.message_count }} 条</p>
              <button
                @click.stop="confirmDeleteSession(s)"
                class="delete-btn absolute right-2 top-1/2 -translate-y-1/2 w-5 h-5 flex items-center justify-center rounded text-gray-400 hover:text-red-500 hover:bg-red-50 opacity-0 group-hover:opacity-100 transition-opacity"
                title="删除会话">
                ✕
              </button>
            </div>
          </template>
        </template>

        <!-- 单一学科过滤后显示 -->
        <template v-else>
          <div v-for="s in filteredSessions" :key="s.id"
            @click="loadSession(s.id)"
            class="session-item group p-2.5 rounded-lg cursor-pointer text-sm transition-colors relative"
            :class="currentSessionId === s.id ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50 text-gray-600'">
            <p class="font-medium truncate pr-6">{{ s.title }}</p>
            <p class="text-xs text-gray-400">{{ s.subject }} · {{ s.message_count }} 条</p>
            <button
              @click.stop="confirmDeleteSession(s)"
              class="delete-btn absolute right-2 top-1/2 -translate-y-1/2 w-5 h-5 flex items-center justify-center rounded text-gray-400 hover:text-red-500 hover:bg-red-50 opacity-0 group-hover:opacity-100 transition-opacity"
              title="删除会话">
              ✕
            </button>
          </div>
        </template>
      </div>
    </div>

    <!-- 聊天区域 -->
    <div class="flex-1 card flex flex-col overflow-hidden">
      <!-- 学科选择 + 移动端会话按钮 -->
      <div class="flex items-center gap-2 sm:gap-3 pb-3 border-b border-gray-100 shrink-0 flex-wrap">
        <!-- 移动端：会话列表按钮 -->
        <button
          @click="showSessionDrawer = true"
          class="md:hidden px-3 py-1 text-sm bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors"
        >
          📋 对话列表
        </button>

        <span class="text-sm text-gray-500 hidden sm:inline">学科：</span>
        <el-select
          v-model="selectedSubject"
          size="small"
          style="width: 100px"
          :disabled="!isNewChat"
          :title="!isNewChat ? '查看历史对话时学科不可更改' : ''"
        >
          <el-option v-for="s in subjects" :key="s" :label="s" :value="s" />
        </el-select>
        <span v-if="!isNewChat" class="text-xs text-gray-400 hidden sm:inline">（历史对话学科不可更改）</span>
      </div>

      <!-- 消息区域 -->
      <div ref="messagesEl" class="flex-1 overflow-y-auto py-2 sm:py-4 space-y-2 sm:space-y-4 px-2 sm:px-4">
        <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full text-gray-400">
          <span class="text-4xl sm:text-5xl mb-2 sm:mb-4">🤖</span>
          <p class="text-base sm:text-lg font-medium text-center">向 EduBuddy 提问吧！</p>
          <p class="text-xs sm:text-sm mt-1 sm:mt-2 text-center text-gray-500">支持数学、物理、化学等学科</p>
        </div>

        <div v-for="msg in messages" :key="msg.id || msg.tempId" class="flex gap-2 sm:gap-3"
          :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
          <!-- AI 头像（移动端隐藏） -->
          <div v-if="msg.role === 'assistant'" class="hidden sm:flex w-8 h-8 bg-blue-500 rounded-full items-center justify-center text-white text-sm shrink-0 mt-1">
            🤖
          </div>
          <!-- 消息内容 -->
          <div class="max-w-xs sm:max-w-2xl">
            <!-- 用户消息：支持 LaTeX 渲染（保留换行） -->
            <template v-if="msg.role === 'user'">
              <!-- 用户上传的试题图片 -->
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
              <!-- 用户文字（可能为空，仅图片时不渲染气泡） -->
              <div v-if="msg.content && msg.content.trim()"
                class="px-3 sm:px-4 py-2 sm:py-3 rounded-2xl text-xs sm:text-sm leading-relaxed bg-blue-500 text-white rounded-tr-sm user-message-content"
                v-html="renderUserMessage(msg.content)">
              </div>
            </template>
            <!-- AI 消息：Markdown + LaTeX 富文本渲染 + 图片 -->
            <div v-else :data-msg-key="msg.id || msg.tempId" class="ai-message-content px-3 sm:px-4 py-2 sm:py-3 rounded-2xl rounded-tl-sm bg-gray-100 text-gray-800 text-xs sm:text-sm">

              <div class="markdown-body" v-dyn-figures v-html="renderMessageWithImagePlaceholders(msg.content)"></div>
              <span v-if="msg.streaming" class="typing-cursor"></span>
              <!-- 图片展示区：已搜索完的图片 -->
              <template v-if="!msg.streaming && msg.imageBlocks && msg.imageBlocks.length > 0">
                <div v-for="(block, bi) in msg.imageBlocks" :key="bi" class="mt-3">
                  <div class="image-block-label text-xs text-gray-500 mb-1.5 flex items-center gap-1">
                    <span>📷</span>
                    <span>参考图片：{{ block.keyword }}</span>
                  </div>
                  <div v-if="block.loading" class="image-loading-placeholder">
                    <span class="text-xs text-gray-400">搜索图片中...</span>
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
                  <div v-else class="text-xs text-gray-400 italic">未找到相关图片</div>
                </div>
              </template>
              <!-- 流式输出中：显示正在搜索的图片占位 -->
              <template v-if="msg.streaming && msg.pendingImageKeywords && msg.pendingImageKeywords.length > 0">
                <div v-for="kw in msg.pendingImageKeywords" :key="kw" class="mt-3">
                  <div class="image-loading-placeholder">
                    <span class="text-xs text-gray-400">🔍 正在搜索图片：{{ kw }}</span>
                  </div>
                </div>
              </template>
            </div>
            <!-- AI 回复操作按钮 -->
            <div v-if="msg.role === 'assistant' && !msg.streaming && msg.id" class="flex gap-2 mt-1.5 ml-1">
              <button @click="copyMessage(msg)" class="text-xs text-gray-400 hover:text-blue-500 transition-colors">
                {{ copiedMsgId === (msg.id || msg.tempId) ? '✓ 已复制' : '📋 复制' }}
              </button>
              <button @click="handleFeedback(msg, 'thumbs_up')" class="text-xs text-gray-400 hover:text-green-500 transition-colors">👍</button>
              <button @click="handleFeedback(msg, 'thumbs_down')" class="text-xs text-gray-400 hover:text-red-500 transition-colors">👎</button>
              <button @click="addToWrongBook(msg)" class="text-xs text-gray-400 hover:text-blue-500 transition-colors">➕ 错题本</button>
              <button @click="exportPdf(msg)" :disabled="exportingMsgId !== null" class="text-xs text-gray-400 hover:text-blue-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                {{ exportingMsgId === (msg.id || msg.tempId) ? '导出中...' : '📄 导出PDF' }}
              </button>
              <!-- 语音朗读按钮：仅语文、英语学科显示 -->
              <template v-if="isTtsSubject">
                <template v-if="ttsState === 'idle' || ttsActiveMsgId !== (msg.id || msg.tempId)">
                  <button @click="startSpeech(msg)" class="text-xs text-gray-400 hover:text-indigo-500 transition-colors">
                    🔊 朗读
                  </button>
                </template>
                <template v-else-if="ttsState === 'playing'">
                  <span class="tts-wave-bar" aria-hidden="true">
                    <span></span><span></span><span></span><span></span>
                  </span>
                  <button @click="togglePauseSpeech" class="text-xs text-amber-500 hover:text-amber-600 transition-colors">⏸ 暂停</button>
                  <button @click="stopSpeech" class="text-xs text-gray-400 hover:text-red-500 transition-colors">⏹ 停止</button>
                </template>
                <template v-else-if="ttsState === 'paused'">
                  <button @click="togglePauseSpeech" class="text-xs text-green-500 hover:text-green-600 transition-colors">▶ 继续</button>
                  <button @click="stopSpeech" class="text-xs text-gray-400 hover:text-red-500 transition-colors">⏹ 停止</button>
                  <span class="text-xs text-gray-400">⏸ 已暂停</span>
                </template>
              </template>
            </div>
          </div>
          <!-- 用户头像 -->
          <div v-if="msg.role === 'user'" class="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center text-white text-sm shrink-0 mt-1">
            👤
          </div>
        </div>

        <!-- AI 思考中 -->
        <div v-if="isLoading" class="flex gap-3">
          <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm">🤖</div>
          <div class="bg-gray-100 px-4 py-3 rounded-2xl rounded-tl-sm">
            <span class="text-gray-500 text-sm">思考中</span>
            <span class="inline-flex gap-1 ml-2">
              <span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay:0ms"></span>
              <span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay:150ms"></span>
              <span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay:300ms"></span>
            </span>
          </div>
        </div>
      </div>

      <!-- 输入区 -->
      <div class="border-t border-gray-100 pt-2 sm:pt-3 px-2 sm:px-0 shrink-0">
        <!-- 图片上传区（可折叠） -->
        <div v-show="showImageUpload" class="mb-2">
          <ImageUploadArea
            ref="imageUploadRef"
            :max-count="5"
            :max-size-m-b="10"
            @images-selected="handleImagesSelected"
          />
        </div>
        <!-- 已选图片数量提示 -->
        <div v-if="selectedImages.length > 0 && !showImageUpload" class="mb-2 text-xs text-gray-500">
          已选择 {{ selectedImages.length }} 张图片，将随下一条消息发送
        </div>
        <!-- 实时 LaTeX 预览区（有内容时显示） -->
        <div v-if="inputText.trim()" class="mb-2 px-3 py-2 bg-blue-50 border border-blue-100 rounded-xl text-xs sm:text-sm text-gray-700 leading-relaxed input-preview-content"
          v-html="renderUserMessage(inputText)">
        </div>
        <div class="flex gap-2 items-end">
          <el-button
            :type="showImageUpload || selectedImages.length ? 'primary' : 'default'"
            @click="showImageUpload = !showImageUpload"
            size="small"
            class="shrink-0"
            title="上传试题图片"
            :icon="UploadFilled"
          />
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="2"
            placeholder="输入问题，或上传试题图片..."
            class="flex-1 text-xs sm:text-sm"
            @keydown.enter.exact.prevent="sendMessage"
            resize="none"
          />
          <el-button type="primary" @click="sendMessage" :disabled="(!inputText.trim() && selectedImages.length === 0) || isLoading" size="small" class="shrink-0">
            发送
          </el-button>
        </div>
      </div>
    </div>

    <!-- 移动端会话列表抽屉（移动端专用） -->
    <SessionDrawer
      v-model="showSessionDrawer"
      :sessions="sessions"
      :current-session-id="currentSessionId"
      :subjects="subjects"
      @new-chat="newChat"
      @select-session="loadSession"
      @delete-session="confirmDeleteSession"
      @filter-subject="(s: string) => filterSubject = s"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
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


// ===================== 类型定义 =====================
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

/** 用户随消息上传的试题图片（区别于 AI 配图 ImageBlock） */
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

// ===================== 图片标记处理 =====================

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
  // 先去掉 [[IMAGE:...]] 标记（图片由下方的 imageBlocks 区域展示）
  const cleaned = content.replace(/\[\[IMAGE:[^\]]*\]\]/gi, '')
  return renderMessage(cleaned)
}

/**
 * 渲染用户消息：支持 LaTeX 公式，同时保留换行（将 \n 转为 <br>）
 */
function renderUserMessage(content: string): string {
  const withLatex = renderLatexOnly(content)
  return withLatex.replace(/\n/g, '<br>')
}

// ===================== 状态 =====================
const authStore = useAuthStore()
const subjects = ['数学', '物理', '化学', '生物', '语文', '英语', '历史', '地理', '政治']
const selectedSubject = ref('数学')
const inputText = ref('')
const messages = ref<ChatMessage[]>([])
const sessions = ref<any[]>([])
const currentSessionId = ref<string | null>(null)
const isLoading = ref(false)
const messagesEl = ref<HTMLElement>()
const copiedMsgId = ref<number | null>(null)
const exportingMsgId = ref<number | null>(null)

// ===================== 图片上传状态 =====================
/** 当前已选择、待随下一条消息发送的试题图片 */
const selectedImages = ref<File[]>([])
/** 是否展开图片上传区 */
const showImageUpload = ref(false)
const imageUploadRef = ref<InstanceType<typeof ImageUploadArea> | null>(null)

function handleImagesSelected(files: File[]) {
  selectedImages.value = files
}

/** 历史会话左侧列表的学科过滤（'全部' 或具体学科名） */
const filterSubject = ref('全部')

/** 移动端会话列表抽屉是否显示 */
const showSessionDrawer = ref(false)

/** 会话消息缓存：避免重复加载已读取的消息 */
const messagesCacheMap = ref<Map<string, ChatMessage[]>>(new Map())

/** 是否为新会话（未绑定历史会话） */
const isNewChat = computed(() => currentSessionId.value === null)

// ===================== 学科分组 & 过滤 =====================

/** 按学科对会话分组（用于左侧列表"全部"视图） */
const groupedSessions = computed(() => {
  const groups: Record<string, any[]> = {}
  for (const s of sessions.value) {
    const subj = s.subject || '其他'
    if (!groups[subj]) groups[subj] = []
    groups[subj].push(s)
  }
  return groups
})

/** 当前学科过滤后的会话列表 */
const filteredSessions = computed(() => {
  if (filterSubject.value === '全部') return sessions.value
  return sessions.value.filter(s => s.subject === filterSubject.value)
})

// ===================== 工具函数 =====================
async function scrollToBottom() {
  await nextTick()
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}

/** 图片加载失败时隐藏破图 */
function onImgError(event: Event) {
  const img = event.target as HTMLImageElement
  if (img) {
    img.style.display = 'none'
  }
}

// ===================== 图片搜索 =====================
/** 为一条 AI 消息搜索所有 [[IMAGE:...]] 关键词对应的图片 */
async function fetchImagesForMessage(msg: ChatMessage) {
  const keywords = extractImageKeywords(msg.content)
  if (keywords.length === 0) return

  // 初始化 imageBlocks（loading 状态）
  msg.imageBlocks = keywords.map(kw => ({
    keyword: kw,
    loading: true,
    images: [],
  }))
  msg.pendingImageKeywords = []
  await scrollToBottom()

  // 逐个关键词搜索（前端直接调用 Wikimedia API，无需后端中转）
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

// ===================== 会话管理 =====================
async function loadSessions() {
  try {
    const res: any = await aiApi.getSessions()
    sessions.value = res.data.items || []
  } catch {}
}

async function loadSession(sessionId: string) {
  currentSessionId.value = sessionId
  // 找到该会话对应的学科，并锁定学科选择器
  const session = sessions.value.find(s => s.id === sessionId)
  if (session?.subject) {
    selectedSubject.value = session.subject
  }

  // 检查缓存：如果该会话的消息已加载过，直接使用缓存
  if (messagesCacheMap.value.has(sessionId)) {
    const cachedMsgs = messagesCacheMap.value.get(sessionId)!
    messages.value = cachedMsgs
    await scrollToBottom()
    // 为缓存中尚未加载图片的 AI 消息补充图片搜索
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
    // 历史消息加载后也需要搜索图片
    messages.value = rawMsgs.map(m => ({
      ...m,
      imageBlocks: [],
      pendingImageKeywords: [],
      // 后端返回的 images: [{id, url}] 映射为用户上传图回显
      uploadedImages: Array.isArray(m.images) ? m.images : [],
    }))
    // 缓存该会话的消息
    messagesCacheMap.value.set(sessionId, messages.value)
    await scrollToBottom()
    // 为每条历史 AI 消息加载图片（非阻塞）
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
  // 新建会话时恢复默认学科（可自由选择）
  selectedSubject.value = '数学'
}

// ===================== 发送消息 =====================
async function sendMessage() {
  const text = inputText.value.trim()
  const imagesToSend = selectedImages.value.slice()
  // 允许"仅图片"或"图片+文字"，但不允许两者皆空
  if ((!text && imagesToSend.length === 0) || isLoading.value) return

  // 添加用户消息（含本地图片预览，立即回显）
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
  // 清空图片选择与上传区
  selectedImages.value = []
  showImageUpload.value = false
  imageUploadRef.value?.clear()
  await scrollToBottom()

  // 创建 AI 回复占位
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
    // 后端 /api/ai/chat 使用 multipart 表单参数（Form/File），
    // 因此统一用 FormData 发送（无图片时 images 字段为空）。
    // 注意：不要手动设置 Content-Type，需由浏览器自动带上 multipart boundary。
    const body = buildChatFormData({
      sessionId: currentSessionId.value,
      question: text || '请解读并解答图片中的题目',
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
        throw new Error('认证已过期，请重新登录')
      }
      throw new Error(`请求失败 (${response.status})`)
    }

    const reader = response.body!.getReader()
    const decoder = new TextDecoder()
    // 缓冲区：累积尚未构成完整一行的数据，避免 SSE 事件被 TCP 分包截断
    let buffer = ''

    // 处理单条 SSE data 行
    const handleLine = async (line: string) => {
      if (!line.startsWith('data: ')) return
      const payload = line.slice(6).trim()
      if (!payload) return
      let data: any
      try {
        data = JSON.parse(payload)
      } catch {
        // 不完整或非法 JSON，忽略（完整数据会在后续累积后重新解析）
        return
      }
      if (data.type === 'content') {
        aiMsg.value.content += data.delta
        // 实时更新正在出现的图片关键词（流式输出时显示搜索占位）
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
            // 新会话第一条消息发送完成后刷新会话列表
            await loadSessions()
          }
        }
        // AI 回复完成后，搜索图片（非阻塞）
        fetchImagesForMessage(aiMsg.value)
      }
    }

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      // stream: true 保证多字节 UTF-8 字符（如中文）跨 chunk 时不会被截断
      buffer += decoder.decode(value, { stream: true })

      // 仅处理已完整接收（以换行结尾）的行，剩余不完整部分保留在 buffer
      let newlineIndex: number
      while ((newlineIndex = buffer.indexOf('\n')) !== -1) {
        const line = buffer.slice(0, newlineIndex)
        buffer = buffer.slice(newlineIndex + 1)
        await handleLine(line)
      }
    }

    // 处理流结束后缓冲区中残留的最后一行（可能没有结尾换行符）
    buffer += decoder.decode()
    if (buffer.trim()) {
      await handleLine(buffer)
    }
  } catch (e) {

    aiMsg.value.content = '抱歉，请求失败，请检查网络或 API 配置。'
    aiMsg.value.streaming = false
    aiMsg.value.pendingImageKeywords = []
  } finally {
    isLoading.value = false
  }
}

// ===================== 复制 =====================
/** 复制 AI 回复内容（去除 [[IMAGE:...]] 标记后的原始 Markdown 文本） */
async function copyMessage(msg: ChatMessage) {
  const text = msg.content.replace(/\[\[IMAGE:[^\]]*\]\]/gi, '').trim()
  if (!text) return
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
    } else {
      // 降级方案：非安全上下文（如 http）下使用 execCommand
      const textarea = document.createElement('textarea')
      textarea.value = text
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      document.body.appendChild(textarea)
      textarea.focus()
      textarea.select()
      // execCommand 已弃用，但在非安全上下文（http）下 navigator.clipboard 不可用，
      // 这是唯一可用的复制降级方案；用 as any 规避类型层的弃用告警。
      ;(document as any).execCommand('copy')
      document.body.removeChild(textarea)
    }
    copiedMsgId.value = (msg.id || msg.tempId) ?? null
    ElMessage.success('已复制到剪贴板')
    setTimeout(() => {
      if (copiedMsgId.value === ((msg.id || msg.tempId) ?? null)) {
        copiedMsgId.value = null
      }
    }, 2000)
  } catch {
    ElMessage.error('复制失败，请手动选择文本复制')
  }
}

// ===================== 导出 PDF =====================
/** HTML 转义，防止 XSS */
function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

/**
 * 将一条 AI 回答（含 Markdown、LaTeX 公式）导出为 PDF。
 * 参照作业批改的「新窗口打印」方案：在新窗口中写入带打印样式的 HTML，
 * 由浏览器原生打印对话框完成「另存为 PDF」，避免 html2canvas 的兼容性问题。
 */
async function exportPdf(msg: ChatMessage) {
  if (exportingMsgId.value !== null) return
  const key = (msg.id || msg.tempId) ?? null
  if (key === null) return

  // 去掉 [[IMAGE:...]] 标记后渲染 Markdown + LaTeX
  const cleaned = msg.content.replace(/\[\[IMAGE:[^\]]*\]\]/gi, '').trim()
  if (!cleaned) {
    ElMessage.error('暂无可导出的内容')
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
<title>EduBuddy AI 回答</title>
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
  /* KaTeX 公式样式 */
  .katex { font-size: 1em; }
  .katex-display { margin: 0.6em 0; }
  /* 打印样式 */
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
<!-- 引入 KaTeX 样式（从 CDN 加载，保证公式正确渲染） -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.22/dist/katex.min.css" crossorigin="anonymous">
</head>
<body>
<div class="page">
  <div class="header">
    <h1>EduBuddy AI 回答</h1>
    <div class="header-meta">
      <span>学科：${escapeHtml(selectedSubject.value)}</span>
      <span>导出时间：${escapeHtml(dateStr)}</span>
    </div>
  </div>
  <div class="report-body">${reportHtml}</div>
  <div class="footer">由 EduBuddy AI 智能学习助手生成 · ${dateStr}</div>
  <!-- 自动打印按钮区域 -->
  <div class="no-print" style="position:fixed;bottom:20px;right:20px;display:flex;gap:10px;z-index:9999;">
    <button onclick="window.print()" style="padding:10px 24px;background:#2563eb;color:white;border:none;border-radius:8px;font-size:14px;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,0.2);">
      🖨️ 打印 / 另存为 PDF
    </button>
    <button onclick="window.close()" style="padding:10px 16px;background:#6b7280;color:white;border:none;border-radius:8px;font-size:14px;cursor:pointer;">
      ✕ 关闭
    </button>
  </div>
</div>
<script>
  // 等待 KaTeX 和字体加载完成后自动弹出打印对话框
  window.addEventListener('load', function() {
    setTimeout(function() { window.print(); }, 800);
  });
<\/script>
</body>
</html>`

    const printWindow = window.open('', '_blank', 'width=900,height=700')
    if (!printWindow) {
      throw new Error('无法打开新窗口，请检查浏览器是否阻止了弹出窗口')
    }
    // 用 Blob URL 加载导出文档（替代已弃用的 document.write）
    const blobUrl = URL.createObjectURL(new Blob([fullHtml], { type: 'text/html' }))
    printWindow.location.href = blobUrl
    // 延时释放，确保新窗口已完成加载与打印
    setTimeout(() => URL.revokeObjectURL(blobUrl), 60000)

    ElMessage.success('已打开打印预览，请选择"另存为 PDF"保存文件')
  } catch (err: any) {
    ElMessage.error('导出失败：' + (err?.message || '未知错误'))
  } finally {
    exportingMsgId.value = null
  }
}


// ===================== 反馈 & 错题本 =====================
async function handleFeedback(msg: ChatMessage, rating: string) {


  try {
    await aiApi.feedback(msg.id!, { rating })
    ElMessage.success(rating === 'thumbs_up' ? '感谢你的反馈！' : '已记录，我们会改进')
  } catch {}
}

async function addToWrongBook(msg: ChatMessage) {
  try {
    const idx = messages.value.indexOf(msg)
    const userMsg = messages.value[idx - 1]
    if (!userMsg || !msg.id) return
    await aiApi.addToWrongBook(userMsg.id || msg.id, { subject: selectedSubject.value, tags: [] })
    ElMessage.success('已加入错题本')
  } catch {}
}

async function confirmDeleteSession(session: any) {
  try {
    await ElMessageBox.confirm(
      `确定要删除对话「${session.title}」吗？此操作不可恢复。`,
      '删除会话',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger',
      }
    )
    await aiApi.deleteSession(session.id)
    if (currentSessionId.value === session.id) {
      currentSessionId.value = null
      messages.value = []
      selectedSubject.value = '数学'
    }
    await loadSessions()
    ElMessage.success('会话已删除')
  } catch (e: any) {
    if (e !== 'cancel' && e?.message !== 'cancel') {
      ElMessage.error('删除失败，请重试')
    }
  }
}

// ===================== 语音朗读（TTS）=====================

/** 支持语音朗读的学科 */
const TTS_SUBJECTS = ['语文', '英语']

/** 当前学科是否支持 TTS */
const isTtsSubject = computed(() => TTS_SUBJECTS.includes(selectedSubject.value))

/** TTS 播放状态：idle / playing / paused */
const ttsState = ref<'idle' | 'playing' | 'paused'>('idle')

/** 当前正在朗读的消息 id（msg.id 或 msg.tempId） */
const ttsActiveMsgId = ref<number | null>(null)

/** 从浏览器语音列表中挑选最优中文语音 */
function pickVoice(lang: string): SpeechSynthesisVoice | null {
  const voices = window.speechSynthesis.getVoices()
  if (lang === '英语') {
    // 英语：优先 en-US，其次 en-GB，再次任意 en
    return (
      voices.find(v => v.lang === 'en-US') ||
      voices.find(v => v.lang === 'en-GB') ||
      voices.find(v => v.lang.startsWith('en')) ||
      null
    )
  }
  // 语文（中文）：优先 zh-CN，其次 zh-TW，再次任意 zh
  return (
    voices.find(v => v.lang === 'zh-CN') ||
    voices.find(v => v.lang === 'zh-TW') ||
    voices.find(v => v.lang.startsWith('zh')) ||
    null
  )
}

/**
 * 将 AI 回复（Markdown + LaTeX）转为适合朗读的纯文本：
 * - 去除 [[IMAGE:...]] 标记
 * - 去除 Markdown 标题符号 #
 * - 去除加粗/斜体 ** / *
 * - 去除行内代码反引号
 * - 将 LaTeX 公式（$...$、$$...$$）替换为口播词
 * - 去除多余空行
 */
function msgToPlainText(content: string): string {
  let text = content
  // 去除图片标记
  text = text.replace(/\[\[IMAGE:[^\]]*\]\]/gi, '')
  // 块级公式 $$...$$ → "数学公式"
  text = text.replace(/\$\$[\s\S]*?\$\$/g, '数学公式')
  // 行内公式 $...$ → "数学公式"
  text = text.replace(/\$[^$\n]+\$/g, '数学公式')
  // Markdown 标题
  text = text.replace(/^#{1,6}\s+/gm, '')
  // 加粗 / 斜体
  text = text.replace(/\*{1,3}([^*]+)\*{1,3}/g, '$1')
  // 行内代码
  text = text.replace(/`([^`]+)`/g, '$1')
  // 代码块
  text = text.replace(/```[\s\S]*?```/g, '代码块')
  // 分隔线
  text = text.replace(/^---+$/gm, '')
  // 多余空行合并
  text = text.replace(/\n{3,}/g, '\n\n')
  return text.trim()
}

/** 开始朗读某条 AI 消息 */
function startSpeech(msg: ChatMessage) {
  // 停止之前的朗读
  window.speechSynthesis.cancel()
  ttsState.value = 'idle'
  ttsActiveMsgId.value = null

  const plainText = msgToPlainText(msg.content)
  if (!plainText) {
    ElMessage.warning('没有可朗读的文本内容')
    return
  }

  const utter = new SpeechSynthesisUtterance(plainText)

  // 根据学科设置语言
  if (selectedSubject.value === '英语') {
    utter.lang = 'en-US'
    utter.rate = 0.9
  } else {
    utter.lang = 'zh-CN'
    utter.rate = 1.0
  }
  utter.pitch = 1.0
  utter.volume = 1.0

  // 尝试指定具体语音
  const voice = pickVoice(selectedSubject.value)
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
  // 部分浏览器不触发 onstart，手动设置状态
  ttsState.value = 'playing'
  ttsActiveMsgId.value = msgKey
}

/** 切换暂停 / 继续 */
function togglePauseSpeech() {
  if (ttsState.value === 'playing') {
    window.speechSynthesis.pause()
    ttsState.value = 'paused'
  } else if (ttsState.value === 'paused') {
    window.speechSynthesis.resume()
    ttsState.value = 'playing'
  }
}

/** 停止朗读 */
function stopSpeech() {
  window.speechSynthesis.cancel()
  ttsState.value = 'idle'
  ttsActiveMsgId.value = null
}

// ===================== 生命周期 =====================
onMounted(async () => {
  await loadSessions()

  // 为消息添加长按复制功能
  setTimeout(() => {
    const messageContents = document.querySelectorAll('.markdown-body, .ai-message-content')
    messageContents.forEach((content) => {
      setupLongPressCopyGesture(content as HTMLElement)
    })
  }, 200)

  // 预加载语音列表（部分浏览器首次 getVoices() 返回空，需触发异步加载）
  if (typeof window !== 'undefined' && window.speechSynthesis) {
    window.speechSynthesis.getVoices()
  }
})

onUnmounted(() => {
  // 离开页面时停止朗读，释放资源
  if (typeof window !== 'undefined' && window.speechSynthesis) {
    window.speechSynthesis.cancel()
  }
})
</script>

<style scoped>
/* 打字光标动画 */
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

/* AI 消息 Markdown 样式 */
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

/* KaTeX 公式样式调整（AI 消息） */
.markdown-body :deep(.katex-display) {
  margin: 0.6em 0;
  overflow-x: auto;
  overflow-y: hidden;
}

.markdown-body :deep(.katex) {
  font-size: 1em;
}

/* 用户消息 KaTeX 样式：白色公式以适配蓝色背景 */
.user-message-content :deep(.katex) {
  font-size: 1em;
  color: white;
}

.user-message-content :deep(.katex-display) {
  margin: 0.4em 0;
  overflow-x: auto;
}

/* KaTeX 内部 SVG/路径颜色继承 */
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

/* 输入框预览区 KaTeX 样式 */
.input-preview-content :deep(.katex) {
  font-size: 1em;
}

.input-preview-content :deep(.katex-display) {
  margin: 0.3em 0;
  overflow-x: auto;
}

/* ============ 图片相关样式 ============ */

/* 图片块标签 */
.image-block-label {
  color: #6b7280;
  font-size: 0.75rem;
  margin-bottom: 6px;
}

/* 图片加载占位 */
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

/* 图片网格（最多3列） */
.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 8px;
  margin-top: 4px;
}

/* 单张图片卡片 */
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

/* 图片本体 */
.image-card-img {
  width: 100%;
  height: 100px;
  object-fit: cover;
  display: block;
  background: #e5e7eb;
}

/* 图片标题 */
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

/* ============ TTS 音频波形动画 ============ */

/* 四根竖条容器，垂直居中对齐行内元素 */
.tts-wave-bar {
  display: inline-flex;
  align-items: flex-end;
  gap: 2px;
  height: 14px;
  margin-right: 2px;
  vertical-align: middle;
}

/* 每根竖条 */
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
