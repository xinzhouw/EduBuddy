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
          class="p-2.5 rounded-lg cursor-pointer text-sm truncate transition-colors"
          :class="currentSessionId === s.id ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50 text-gray-600'">
          <p class="font-medium truncate">{{ s.title }}</p>
          <p class="text-xs text-gray-400">{{ s.subject }} · {{ s.message_count }} 条</p>
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
          <p class="text-sm mt-2">支持数学、物理、化学等全部中学学科</p>
        </div>

        <div v-for="msg in messages" :key="msg.id || msg.tempId" class="flex gap-3"
          :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
          <!-- AI 头像 -->
          <div v-if="msg.role === 'assistant'" class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm shrink-0">
            🤖
          </div>
          <!-- 消息内容 -->
          <div class="max-w-2xl">
            <div class="px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap"
              :class="msg.role === 'user'
                ? 'bg-blue-500 text-white rounded-tr-sm'
                : 'bg-gray-100 text-gray-800 rounded-tl-sm'">
              {{ msg.content }}<span v-if="msg.streaming" class="typing-cursor"></span>
            </div>
            <!-- AI 回复操作按钮 -->
            <div v-if="msg.role === 'assistant' && !msg.streaming && msg.id" class="flex gap-2 mt-1.5 ml-1">
              <button @click="handleFeedback(msg, 'thumbs_up')" class="text-xs text-gray-400 hover:text-green-500 transition-colors">👍</button>
              <button @click="handleFeedback(msg, 'thumbs_down')" class="text-xs text-gray-400 hover:text-red-500 transition-colors">👎</button>
              <button @click="addToWrongBook(msg)" class="text-xs text-gray-400 hover:text-blue-500 transition-colors">➕ 错题本</button>
            </div>
          </div>
          <!-- 用户头像 -->
          <div v-if="msg.role === 'user'" class="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center text-white text-sm shrink-0">
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
        <div class="flex gap-2 items-end">
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="2"
            placeholder="输入你的问题... (Shift+Enter 换行，Enter 发送)"
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
import { ElMessage } from 'element-plus'

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
  const aiMsg = ref({ tempId: Date.now() + 1, role: 'assistant', content: '', streaming: true })
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

onMounted(async () => {
  await loadSessions()
})
</script>
