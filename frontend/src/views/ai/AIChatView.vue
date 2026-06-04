<template>
  <div class="flex h-full gap-4" style="height: calc(100vh - 160px)">
    <!-- 历史会话列表 -->
    <div class="w-64 shrink-0 card flex flex-col gap-2 overflow-hidden">
      <div class="flex items-center justify-between">
        <h3 class="font-semibold text-gray-700 text-sm">历史对话</h3>
        <button @click="newChat" class="text-blue-500 text-sm hover:text-blue-600">+ 新对话</button>
      </div>
      <div class="flex-1 overflow-y-auto space-y-1">
        <div v-if="sessions.length === 0" class="text-center py-8 text-gray-400 text-sm">暂无历史对话</div>
        <div v-for="s in sessions" :key="s.id"
          @click="loadSession(s.id)"
          class="session-item group p-2.5 rounded-lg cursor-pointer text-sm transition-colors relative"
          :class="currentSessionId === s.id ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50 text-gray-600'">
          <p class="font-medium truncate pr-6">{{ s.title }}</p>
          <p class="text-xs text-gray-400">{{ s.subject }} · {{ s.message_count }} 条</p>
          <!-- 删除按钮：悬停时显示 -->
          <button
            @click.stop="confirmDeleteSession(s)"
            class="delete-btn absolute right-2 top-1/2 -translate-y-1/2 w-5 h-5 flex items-center justify-center rounded text-gray-400 hover:text-red-500 hover:bg-red-50 opacity-0 group-hover:opacity-100 transition-opacity"
            title="删除会话">
            ✕
          </button>
        </div>
      </div>
    </div>

    <!-- 聊天区域 -->
    <div class="flex-1 card flex flex-col overflow-hidden">
      <!-- 学科选择 -->
      <div class="flex items-center gap-3 pb-3 border-b border-gray-100 shrink-0">
        <span class="text-sm text-gray-500">学科：</span>
        <el-select v-model="selectedSubject" size="small" style="width: 120px">
          <el-option v-for="s in subjects" :key="s" :label="s" :value="s" />
        </el-select>
      </div>

      <!-- 消息区域 -->
      <div ref="messagesEl" class="flex-1 overflow-y-auto py-4 space-y-4">
        <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full text-gray-400">
          <span class="text-5xl mb-4">🤖</span>
          <p class="text-lg font-medium">向 EduBuddy 提问吧！</p>
          <p class="text-sm mt-2">支持数学、物理、化学等全部中学学科，可粘贴含公式的题目</p>
        </div>

        <div v-for="msg in messages" :key="msg.id || msg.tempId" class="flex gap-3"
          :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
          <!-- AI 头像 -->
          <div v-if="msg.role === 'assistant'" class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm shrink-0 mt-1">
            🤖
          </div>
          <!-- 消息内容 -->
          <div class="max-w-2xl">
            <!-- 用户消息：支持 LaTeX 渲染（保留换行） -->
            <div v-if="msg.role === 'user'"
              class="px-4 py-3 rounded-2xl text-sm leading-relaxed bg-blue-500 text-white rounded-tr-sm user-message-content"
              v-html="renderUserMessage(msg.content)">
            </div>
            <!-- AI 消息：Markdown + LaTeX 富文本渲染 + 图片 -->
            <div v-else class="ai-message-content px-4 py-3 rounded-2xl rounded-tl-sm bg-gray-100 text-gray-800">
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
              <button @click="handleFeedback(msg, 'thumbs_up')" class="text-xs text-gray-400 hover:text-green-500 transition-colors">👍</button>
              <button @click="handleFeedback(msg, 'thumbs_down')" class="text-xs text-gray-400 hover:text-red-500 transition-colors">👎</button>
              <button @click="addToWrongBook(msg)" class="text-xs text-gray-400 hover:text-blue-500 transition-colors">➕ 错题本</button>
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
      <div class="border-t border-gray-100 pt-3 shrink-0">
        <!-- 实时 LaTeX 预览区（有内容时显示） -->
        <div v-if="inputText.trim()" class="mb-2 px-3 py-2 bg-blue-50 border border-blue-100 rounded-xl text-sm text-gray-700 leading-relaxed input-preview-content"
          v-html="renderUserMessage(inputText)">
        </div>
        <div class="flex gap-2 items-end">
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="2"
            placeholder="输入你的问题... (Shift+Enter 换行，Enter 发送，公式预览在上方)"
            class="flex-1"
            @keydown.enter.exact.prevent="sendMessage"
            resize="none"
          />
          <el-button type="primary" @click="sendMessage" :disabled="!inputText.trim() || isLoading">
            发送
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { aiApi } from '@/api/ai'
import { ElMessage, ElMessageBox } from 'element-plus'
import { renderMessage, renderLatexOnly } from '@/utils/markdown'
import { searchEducationalImages } from '@/utils/imageSearch'

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

interface ChatMessage {
  id?: number
  tempId?: number
  role: 'user' | 'assistant'
  content: string
  streaming?: boolean
  feedback?: string
  imageBlocks?: ImageBlock[]
  pendingImageKeywords?: string[]
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
  try {
    const res: any = await aiApi.getMessages(sessionId)
    const rawMsgs: ChatMessage[] = res.data || []
    // 历史消息加载后也需要搜索图片
    messages.value = rawMsgs.map(m => ({
      ...m,
      imageBlocks: [],
      pendingImageKeywords: [],
    }))
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
}

// ===================== 发送消息 =====================
async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || isLoading.value) return

  // 添加用户消息
  const userMsg: ChatMessage = { tempId: Date.now(), role: 'user', content: text }
  messages.value.push(userMsg)
  inputText.value = ''
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
    const response = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        session_id: currentSessionId.value,
        question: text,
        subject: selectedSubject.value,
      }),
    })

    if (!response.ok) {
      throw new Error('请求失败')
    }

    const reader = response.body!.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const data = JSON.parse(line.slice(6))
          if (data.type === 'content') {
            aiMsg.value.content += data.delta
            // 实时更新正在出现的图片关键词（流式输出时显示搜索占位）
            aiMsg.value.pendingImageKeywords = extractImageKeywords(aiMsg.value.content)
            await scrollToBottom()
          } else if (data.type === 'done') {
            aiMsg.value.streaming = false
            aiMsg.value.pendingImageKeywords = []
            if (data.message_id) aiMsg.value.id = data.message_id
            if (data.session_id && !currentSessionId.value) {
              currentSessionId.value = data.session_id
              await loadSessions()
            }
            // AI 回复完成后，搜索图片（非阻塞）
            fetchImagesForMessage(aiMsg.value)
          }
        } catch {}
      }
    }
  } catch (e) {
    aiMsg.value.content = '抱歉，请求失败，请检查网络或 API 配置。'
    aiMsg.value.streaming = false
    aiMsg.value.pendingImageKeywords = []
  } finally {
    isLoading.value = false
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
    }
    await loadSessions()
    ElMessage.success('会话已删除')
  } catch (e: any) {
    if (e !== 'cancel' && e?.message !== 'cancel') {
      ElMessage.error('删除失败，请重试')
    }
  }
}

// ===================== 生命周期 =====================
onMounted(async () => {
  await loadSessions()
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
</style>
