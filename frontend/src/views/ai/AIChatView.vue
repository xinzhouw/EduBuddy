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
            <!-- AI 消息：Markdown + LaTeX 富文本渲染 -->
            <div v-else
              class="ai-message-content px-4 py-3 rounded-2xl rounded-tl-sm bg-gray-100 text-gray-800">
              <div class="markdown-body" v-html="renderMessage(msg.content)"></div>
              <span v-if="msg.streaming" class="typing-cursor"></span>
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

/**
 * 渲染用户消息：支持 LaTeX 公式，同时保留换行（将 \n 转为 <br>）
 */
function renderUserMessage(content: string): string {
  // 先做 LaTeX 渲染，再把换行符转成 <br>
  const withLatex = renderLatexOnly(content)
  // 将剩余的换行符转为 <br>（renderLatexOnly 输出的是纯文本+KaTeX HTML）
  return withLatex.replace(/\n/g, '<br>')
}

const authStore = useAuthStore()
const subjects = ['数学', '物理', '化学', '生物', '语文', '英语', '历史', '地理', '政治']
const selectedSubject = ref('数学')
const inputText = ref('')
const messages = ref<any[]>([])
const sessions = ref<any[]>([])
const currentSessionId = ref<string | null>(null)
const isLoading = ref(false)
const messagesEl = ref<HTMLElement>()

async function scrollToBottom() {
  await nextTick()
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}

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
    messages.value = res.data || []
    await scrollToBottom()
  } catch {}
}

function newChat() {
  currentSessionId.value = null
  messages.value = []
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || isLoading.value) return

  // 添加用户消息
  const userMsg = { tempId: Date.now(), role: 'user', content: text }
  messages.value.push(userMsg)
  inputText.value = ''
  await scrollToBottom()

  // 创建 AI 回复占位
  const aiMsg = ref<{ tempId: number; role: string; content: string; streaming: boolean; id?: number }>({ tempId: Date.now() + 1, role: 'assistant', content: '', streaming: true })
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
            await scrollToBottom()
          } else if (data.type === 'done') {
            aiMsg.value.streaming = false
            if (data.message_id) aiMsg.value.id = data.message_id
            if (data.session_id && !currentSessionId.value) {
              currentSessionId.value = data.session_id
              await loadSessions()
            }
          }
        } catch {}
      }
    }
  } catch (e) {
    aiMsg.value.content = '抱歉，请求失败，请检查网络或 API 配置。'
    aiMsg.value.streaming = false
  } finally {
    isLoading.value = false
  }
}

async function handleFeedback(msg: any, rating: string) {
  try {
    await aiApi.feedback(msg.id, { rating })
    ElMessage.success(rating === 'thumbs_up' ? '感谢你的反馈！' : '已记录，我们会改进')
  } catch {}
}

async function addToWrongBook(msg: any) {
  try {
    // 找到对应的用户问题
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
    // 如果删除的是当前会话，清空聊天区域
    if (currentSessionId.value === session.id) {
      currentSessionId.value = null
      messages.value = []
    }
    // 刷新会话列表
    await loadSessions()
    ElMessage.success('会话已删除')
  } catch (e: any) {
    // 用户取消不提示
    if (e !== 'cancel' && e?.message !== 'cancel') {
      ElMessage.error('删除失败，请重试')
    }
  }
}

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
</style>
