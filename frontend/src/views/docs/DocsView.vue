<template>
  <div class="space-y-4">
    <!-- 上传区 -->
    <div class="card">
      <h3 class="font-semibold text-gray-700 mb-4">📄 上传文档</h3>
      <el-upload
        drag
        :show-file-list="false"
        :before-upload="beforeUpload"
        :http-request="handleUpload"
        accept=".pdf,.docx,.jpg,.jpeg,.png"
      >
        <div class="py-8 text-center">
          <p class="text-4xl mb-3">📤</p>
          <p class="text-gray-600">拖拽文件到此处或<span class="text-blue-500">点击上传</span></p>
          <p class="text-xs text-gray-400 mt-2">支持 PDF、DOCX、JPG、PNG，最大 20MB</p>
        </div>
      </el-upload>
    </div>

    <!-- 文档列表 -->
    <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <el-skeleton v-for="i in 4" :key="i" :rows="3" animated class="card" />
    </div>

    <div v-else-if="docs.length === 0" class="text-center py-12 text-gray-400">
      <span class="text-5xl">📂</span>
      <p class="mt-4">上传第一份资料，让AI帮你提炼重点</p>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div v-for="doc in docs" :key="doc.id" class="card">
        <div class="flex items-start justify-between">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-2">
              <span class="text-xl">{{ fileIcon(doc.file_type) }}</span>
              <p class="font-medium text-gray-800 truncate">{{ doc.title }}</p>
            </div>
            <div class="flex items-center gap-2 text-xs text-gray-400">
              <span v-if="doc.subject" class="px-1.5 py-0.5 bg-blue-50 text-blue-600 rounded">{{ doc.subject }}</span>
              <span>{{ formatSize(doc.file_size) }}</span>
              <span :class="statusClass(doc.status)">{{ statusLabel(doc.status) }}</span>
            </div>
          </div>
          <div class="flex gap-1 ml-2">
            <el-button size="small" @click="analyzeDoc(doc, 'extract_key_points')" :disabled="doc.status !== 'done'" plain>提取知识点</el-button>
            <el-button size="small" type="danger" plain @click="deleteDoc(doc.id)">删除</el-button>
          </div>
        </div>

        <!-- AI分析结果 -->
        <div v-if="analyzing[doc.id]" class="mt-3 bg-blue-50 rounded-lg p-3">
          <p class="text-sm text-gray-600 whitespace-pre-wrap">
            {{ analysisResults[doc.id] }}<span class="typing-cursor"></span>
          </p>
        </div>
        <div v-else-if="analysisResults[doc.id]" class="mt-3 bg-blue-50 rounded-lg p-3 text-sm text-gray-600 whitespace-pre-wrap">
          {{ analysisResults[doc.id] }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { docsApi } from '@/api/docs'
import { ElMessage } from 'element-plus'

const authStore = useAuthStore()
const docs = ref<any[]>([])
const loading = ref(false)
const analyzing = ref<Record<number, boolean>>({})
const analysisResults = ref<Record<number, string>>({})

function fileIcon(type: string) { return { pdf: '📕', docx: '📘', jpg: '🖼️', png: '🖼️' }[type] || '📄' }
function formatSize(b: number) { return b > 1048576 ? `${(b / 1048576).toFixed(1)}MB` : `${(b / 1024).toFixed(0)}KB` }
function statusLabel(s: string) { return { pending: '待处理', processing: '解析中', done: '已完成', error: '解析失败' }[s] || s }
function statusClass(s: string) { return { done: 'text-green-500', error: 'text-red-500', processing: 'text-amber-500' }[s] || 'text-gray-400' }

function beforeUpload(file: File) {
  const allowed = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'image/jpeg', 'image/png']
  if (!allowed.includes(file.type)) { ElMessage.error('不支持的文件类型'); return false }
  if (file.size > 20 * 1024 * 1024) { ElMessage.error('文件超过20MB'); return false }
  return true
}

async function handleUpload({ file }: any) {
  const fd = new FormData()
  fd.append('file', file)
  const res: any = await docsApi.upload(fd)
  ElMessage.success('上传成功')
  docs.value.unshift(res.data)
}

async function analyzeDoc(doc: any, task: string) {
  analyzing.value[doc.id] = true
  analysisResults.value[doc.id] = ''
  try {
    const token = authStore.token
    const response = await fetch(`/api/documents/${doc.id}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({ task }),
    })
    const reader = response.body!.getReader()
    const decoder = new TextDecoder()
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      for (const line of decoder.decode(value).split('\n')) {
        if (!line.startsWith('data: ')) continue
        try {
          const data = JSON.parse(line.slice(6))
          if (data.type === 'content') analysisResults.value[doc.id] += data.delta
          if (data.type === 'done') analyzing.value[doc.id] = false
        } catch {}
      }
    }
  } finally {
    analyzing.value[doc.id] = false
  }
}

async function deleteDoc(id: number) {
  await docsApi.delete(id)
  docs.value = docs.value.filter(d => d.id !== id)
  ElMessage.success('已删除')
}

async function loadDocs() {
  loading.value = true
  try {
    const res: any = await docsApi.list()
    docs.value = res.data.items || []
  } finally {
    loading.value = false
  }
}

onMounted(loadDocs)
</script>
