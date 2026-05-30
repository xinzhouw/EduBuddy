<template>
  <div class="flex h-full gap-4" style="height: calc(100vh - 160px)">
    <!-- 左侧：历史记录 -->
    <div class="w-64 shrink-0 card flex flex-col gap-2 overflow-hidden">
      <div class="flex items-center justify-between shrink-0">
        <h3 class="font-semibold text-gray-700 text-sm">批改历史</h3>
        <button @click="startNew" class="text-blue-500 text-sm hover:text-blue-600">+ 新批改</button>
      </div>

      <!-- 学科筛选 -->
      <el-select v-model="filterSubject" size="small" placeholder="全部学科" clearable class="w-full shrink-0">
        <el-option v-for="s in subjects" :key="s" :label="s" :value="s" />
      </el-select>

      <div class="flex-1 overflow-y-auto space-y-1">
        <div v-if="historyList.length === 0" class="text-center py-8 text-gray-400 text-sm">
          暂无批改记录
        </div>
        <div
          v-for="item in historyList"
          :key="item.id"
          @click="loadDetail(item.id)"
          class="group p-2.5 rounded-lg cursor-pointer text-sm transition-colors relative"
          :class="currentGradingId === item.id ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50 text-gray-600'"
        >
          <div class="flex items-center gap-1.5 pr-6">
            <span class="text-xs px-1.5 py-0.5 rounded-md font-medium"
              :class="subjectColorClass(item.subject)">{{ item.subject }}</span>
            <p class="font-medium truncate flex-1">{{ item.title }}</p>
          </div>
          <div class="flex items-center gap-2 mt-0.5">
            <span v-if="item.score !== null && item.score !== undefined"
              class="text-xs font-bold"
              :class="scoreColorClass(item.score)">
              {{ item.score.toFixed(0) }}分
            </span>
            <span v-else class="text-xs text-gray-400">待批改</span>
            <span class="text-xs text-gray-400">{{ formatDate(item.created_at) }}</span>
          </div>
          <button
            @click.stop="confirmDelete(item)"
            class="absolute right-2 top-1/2 -translate-y-1/2 w-5 h-5 flex items-center justify-center rounded text-gray-400 hover:text-red-500 hover:bg-red-50 opacity-0 group-hover:opacity-100 transition-opacity text-xs"
            title="删除">✕</button>
        </div>
      </div>
    </div>

    <!-- 右侧：提交 & 结果区域 -->
    <div class="flex-1 card flex flex-col overflow-hidden">
      <!-- 顶部工具栏 -->
      <div class="flex items-center gap-3 pb-3 border-b border-gray-100 shrink-0 flex-wrap">
        <!-- 学科 -->
        <div class="flex items-center gap-1.5">
          <span class="text-sm text-gray-500">学科：</span>
          <el-select v-model="form.subject" size="small" style="width: 110px" :disabled="isGrading || isRecognizing">
            <el-option v-for="s in subjects" :key="s" :label="s" :value="s" />
          </el-select>
        </div>
        <!-- 提交方式切换 -->
        <el-radio-group v-model="submitMode" size="small" :disabled="isGrading || isRecognizing">
          <el-radio-button value="text">📝 文本输入</el-radio-button>
          <el-radio-button value="file">📎 上传文件</el-radio-button>
        </el-radio-group>
      </div>

      <!-- 内容区：提交表单 / 批改结果 -->
      <div class="flex-1 overflow-y-auto">
        <!-- 批改结果视图 -->
        <div v-if="viewMode === 'result'" class="h-full flex flex-col">
          <!-- 分数展示 -->
          <div v-if="finalScore !== null" class="flex items-center gap-4 py-4 px-1 shrink-0 border-b border-gray-100">
            <div class="flex flex-col items-center justify-center w-20 h-20 rounded-full border-4 shrink-0"
              :class="scoreBorderClass(finalScore)">
              <span class="text-2xl font-bold" :class="scoreColorClass(finalScore)">{{ finalScore.toFixed(0) }}</span>
              <span class="text-xs text-gray-500">/ 100</span>
            </div>
            <div>
              <p class="text-base font-semibold text-gray-700">{{ currentTitle }}</p>
              <p class="text-sm text-gray-500">{{ form.subject }} · {{ scoreLabel(finalScore) }}</p>
              <p class="text-xs text-gray-400 mt-1">批改时间：{{ currentGradedAt || '刚刚' }}</p>
            </div>
            <div class="ml-auto flex gap-2">
              <!-- PDF 导出按钮 -->
              <el-button
                size="small"
                type="primary"
                plain
                :loading="isExportingPDF"
                :disabled="isGrading || !gradingReport"
                @click="exportToPDF"
                title="导出批改报告为 PDF"
              >
                <span class="flex items-center gap-1">
                  <span>📥</span>
                  <span>{{ isExportingPDF ? '生成中...' : '导出 PDF' }}</span>
                </span>
              </el-button>
              <el-button size="small" @click="startNew">重新提交</el-button>
            </div>
          </div>
          <!-- 批改完成但无分数时也显示导出按钮 -->
          <div v-else-if="gradingReport && !isGrading" class="flex justify-end py-2 px-1 shrink-0 border-b border-gray-100">
            <el-button
              size="small"
              type="primary"
              plain
              :loading="isExportingPDF"
              @click="exportToPDF"
            >
              <span class="flex items-center gap-1">
                <span>📥</span>
                <span>{{ isExportingPDF ? '生成中...' : '导出 PDF' }}</span>
              </span>
            </el-button>
            <el-button size="small" class="ml-2" @click="startNew">重新提交</el-button>
          </div>

          <!-- 批改报告（Markdown 渲染） -->
          <div class="flex-1 overflow-y-auto py-4 px-1">
            <div v-if="isGrading" class="space-y-2">
              <div class="flex items-center gap-2 text-blue-500 text-sm mb-3">
                <span class="animate-spin text-base">⚙️</span>
                <span>AI 正在批改中，请稍候...</span>
              </div>
              <!-- 流式输出预览 -->
              <div v-if="gradingReport" class="markdown-body px-1 py-2 bg-gray-50 rounded-xl"
                v-html="renderMessage(gradingReport)">
              </div>
              <span class="typing-cursor"></span>
            </div>
            <!-- 批改报告内容区域（用于 PDF 导出的 ref） -->
            <div
              v-else-if="gradingReport"
              ref="reportContentEl"
              class="markdown-body px-1"
              v-html="renderMessage(gradingReport)"
            ></div>
            <div v-else class="text-center text-gray-400 py-12">
              <span class="text-4xl block mb-3">📋</span>
              <p>批改报告将在这里显示</p>
            </div>
          </div>
        </div>

        <!-- 提交表单视图 -->
        <div v-else class="py-4 space-y-4">
          <!-- 作业标题 -->
          <div class="flex items-center gap-3">
            <label class="text-sm text-gray-600 w-16 shrink-0">作业标题</label>
            <el-input
              v-model="form.title"
              placeholder="例如：第三章练习题、期中数学作业..."
              size="small"
              class="flex-1"
              :maxlength="100"
              show-word-limit
            />
          </div>

          <!-- 文本输入模式 -->
          <div v-if="submitMode === 'text'" class="space-y-2">
            <div class="flex items-center justify-between">
              <label class="text-sm text-gray-600">作业内容</label>
              <span class="text-xs text-gray-400">{{ form.content.length }} / 10000 字</span>
            </div>
            <el-input
              v-model="form.content"
              type="textarea"
              :rows="12"
              placeholder="请粘贴或输入你的作业内容...

示例：
1. 已知 $x^2 - 5x + 6 = 0$，求 $x$ 的值。
答：分解因式得 $(x-2)(x-3)=0$，所以 $x=2$ 或 $x=3$

2. 计算 $\int_0^1 x^2 dx$
答：..."
              :maxlength="10000"
              resize="none"
              class="font-mono text-sm"
            />
            <p class="text-xs text-gray-400">💡 支持 LaTeX 公式（如 $x^2$），直接粘贴题目和答案即可</p>
          </div>

          <!-- 文件上传模式 -->
          <div v-else class="space-y-3">
            <label class="text-sm text-gray-600">上传作业文件</label>

            <!-- 拖拽上传区域 -->
            <div
              class="border-2 border-dashed rounded-xl p-8 text-center transition-colors cursor-pointer"
              :class="isDragOver ? 'border-blue-400 bg-blue-50' : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'"
              @dragover.prevent="isDragOver = true"
              @dragleave="isDragOver = false"
              @drop.prevent="handleDrop"
              @click="fileInputEl?.click()"
            >
              <input
                ref="fileInputEl"
                type="file"
                accept=".pdf,.docx,.jpg,.jpeg,.png,.gif,.webp"
                class="hidden"
                @change="handleFileChange"
              />
              <div v-if="!selectedFile">
                <div class="text-4xl mb-3">📁</div>
                <p class="text-sm font-medium text-gray-600">点击选择文件 或 拖拽到此处</p>
                <p class="text-xs text-gray-400 mt-2">支持 PDF、Word (.docx)、图片 (JPG/PNG)</p>
                <p class="text-xs text-gray-400">最大 50MB</p>
              </div>
              <div v-else class="flex items-center justify-center gap-3">
                <span class="text-2xl">{{ fileIcon(selectedFile.name) }}</span>
                <div class="text-left">
                  <p class="text-sm font-medium text-gray-700">{{ selectedFile.name }}</p>
                  <p class="text-xs text-gray-400">{{ formatFileSize(selectedFile.size) }}</p>
                </div>
                <el-button size="small" type="danger" text @click.stop="clearFile">更换文件</el-button>
              </div>
            </div>

            <!-- 图片识别预览区域 -->
            <div v-if="isImageFile && selectedFile">
              <!-- 识别中状态 -->
              <div v-if="isRecognizing" class="bg-blue-50 border border-blue-200 rounded-xl p-4">
                <div class="flex items-center gap-2 text-blue-600 text-sm">
                  <span class="animate-spin">🔍</span>
                  <span>AI 正在识别图片内容，请稍候...</span>
                </div>
              </div>

              <!-- 识别结果展示 -->
              <div v-else-if="recognizedText !== null" class="bg-gray-50 border border-gray-200 rounded-xl p-4 space-y-2">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <span class="text-sm font-medium text-gray-700">🔍 图片识别结果</span>
                    <span class="text-xs px-2 py-0.5 rounded-full font-medium"
                      :class="recognizeConfidence === 'high' ? 'bg-green-100 text-green-700'
                            : recognizeConfidence === 'medium' ? 'bg-amber-100 text-amber-700'
                            : 'bg-red-100 text-red-700'">
                      {{ recognizeConfidence === 'high' ? '✓ 高置信度' : recognizeConfidence === 'medium' ? '⚠ 中等置信度' : '⚠ 低置信度' }}
                    </span>
                  </div>
                  <div class="flex items-center gap-2">
                    <el-button size="small" text @click="recognizeEditMode = !recognizeEditMode">
                      {{ recognizeEditMode ? '预览' : '✏️ 编辑' }}
                    </el-button>
                    <el-button size="small" text @click="retryRecognize" :disabled="isRecognizing">重新识别</el-button>
                  </div>
                </div>
                <div class="text-xs text-gray-500">以下是 AI 从图片中识别到的文字内容，请确认是否正确：</div>

                <!-- 预览模式：安全渲染（HTML转义 + LaTeX公式） -->
                <div
                  v-if="!recognizeEditMode"
                  class="recognize-preview bg-white border border-gray-100 rounded-lg p-3 min-h-24 max-h-64 overflow-y-auto cursor-pointer text-sm leading-relaxed"
                  v-html="renderRecognizedText(recognizedText)"
                  @click="recognizeEditMode = true"
                  title="点击编辑"
                ></div>

                <!-- 编辑模式：左右分栏 - 左侧MathLive公式编辑区 + 右侧实时预览 -->
                <div v-else class="space-y-2">
                  <!-- 工具栏：Undo / Redo + 插入公式 -->
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-1.5">
                      <!-- Undo 按钮 -->
                      <button
                        @click="undoRecognizedText"
                        :disabled="undoStack.length === 0"
                        class="flex items-center gap-1 px-2 py-1 text-xs rounded-md border transition-colors"
                        :class="undoStack.length > 0
                          ? 'border-gray-300 text-gray-600 hover:bg-gray-100 hover:border-gray-400'
                          : 'border-gray-200 text-gray-300 cursor-not-allowed'"
                        title="撤销 (Ctrl+Z)"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                          <path d="M3 7v6h6"/><path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13"/>
                        </svg>
                        撤销
                      </button>
                      <!-- Redo 按钮 -->
                      <button
                        @click="redoRecognizedText"
                        :disabled="redoStack.length === 0"
                        class="flex items-center gap-1 px-2 py-1 text-xs rounded-md border transition-colors"
                        :class="redoStack.length > 0
                          ? 'border-gray-300 text-gray-600 hover:bg-gray-100 hover:border-gray-400'
                          : 'border-gray-200 text-gray-300 cursor-not-allowed'"
                        title="重做 (Ctrl+Y)"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                          <path d="M21 7v6h-6"/><path d="M3 17a9 9 0 0 1 9-9 9 9 0 0 1 6 2.3l3 2.7"/>
                        </svg>
                        重做
                      </button>
                      <!-- 历史步数提示 -->
                      <span class="text-xs text-gray-400 ml-1">
                        {{ undoStack.length > 0 ? `可撤销 ${undoStack.length} 步` : '' }}
                      </span>
                    </div>
                    <button
                      @click="showMathEditor = !showMathEditor"
                      class="text-xs px-2 py-1 bg-purple-50 text-purple-700 rounded-md hover:bg-purple-100 transition-colors border border-purple-200"
                    >
                      {{ showMathEditor ? '▲ 关闭公式编辑' : '∑ 插入公式' }}
                    </button>
                  </div>

                  <!-- 提示说明 -->
                  <div class="bg-blue-50 border border-blue-100 rounded-lg px-3 py-2 text-xs text-blue-700 flex items-start gap-2">
                    <span class="shrink-0 mt-0.5">💡</span>
                    <div>
                      <p class="font-medium mb-0.5">如何编辑数学公式</p>
                      <p>• 点击下方「插入公式」按钮，用可视化界面编辑数学公式，自动转为 <code class="bg-blue-100 px-1 rounded">$公式$</code> 格式</p>
                      <p>• 也可以直接在文本框中修改文字内容，公式部分保持 <code class="bg-blue-100 px-1 rounded">$...$</code> 格式不变</p>
                      <p>• 支持 <kbd class="bg-blue-100 px-1 rounded font-mono">Ctrl+Z</kbd> 撤销 / <kbd class="bg-blue-100 px-1 rounded font-mono">Ctrl+Y</kbd> 重做</p>
                    </div>
                  </div>

                  <!-- MathLive 可视化公式编辑器（折叠显示） -->
                  <div v-if="showMathEditor" class="border border-purple-200 rounded-lg bg-purple-50 p-2 space-y-1.5">
                    <p class="text-xs text-purple-600">在下方输入或点击公式键盘，完成后点击「插入到文本」：</p>
                    <math-field
                      ref="mathFieldEl"
                      virtual-keyboard-mode="onfocus"
                      class="w-full border border-purple-300 rounded bg-white p-2 text-base"
                      style="min-height: 48px;"
                      @input="onMathFieldInput"
                    ></math-field>
                    <button
                      @click="insertMathToText"
                      class="w-full text-xs py-1.5 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
                    >
                      ✓ 插入到文本（将以 $公式$ 格式插入光标处）
                    </button>
                  </div>

                  <!-- 左右分栏：左侧文本编辑 | 右侧实时预览 -->
                  <div class="grid grid-cols-2 gap-2">
                    <!-- 左侧：文本编辑区 -->
                    <div class="space-y-1.5">
                      <span class="text-xs text-gray-500 font-medium">✏️ 编辑区</span>
                      <!-- 文本 textarea -->
                      <textarea
                        ref="recognizeTextareaEl"
                        v-model="recognizedText"
                        rows="7"
                        placeholder="识别内容为空，可在此输入..."
                        class="w-full border border-gray-300 rounded-lg p-2 text-xs font-mono leading-relaxed resize-none focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent"
                        @keydown="onRecognizeKeydown"
                        @input="onRecognizeInput"
                      ></textarea>
                    </div>

                    <!-- 右侧：实时渲染预览 -->
                    <div class="space-y-1.5">
                      <span class="text-xs text-gray-500 font-medium">👁 实时预览</span>
                      <div
                        class="recognize-preview bg-white border border-gray-200 rounded-lg p-2 text-sm leading-relaxed overflow-y-auto"
                        style="height: calc(7 * 1.6rem + 16px)"
                        v-html="renderRecognizedText(recognizedText || '')"
                      ></div>
                    </div>
                  </div>
                </div>
                <p class="text-xs text-gray-400">💡 点击预览区域可切换编辑/预览模式</p>
              </div>

              <!-- 识别失败 -->
              <div v-else-if="recognizeError" class="bg-red-50 border border-red-200 rounded-xl p-3">
                <div class="flex items-center justify-between">
                  <span class="text-sm text-red-600">⚠ 识别失败：{{ recognizeError }}</span>
                  <el-button size="small" text type="danger" @click="retryRecognize">重试</el-button>
                </div>
              </div>
            </div>

            <div class="bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-700 space-y-1">
              <p class="font-medium">📌 上传说明</p>
              <p>• <strong>PDF / Word</strong>：自动提取文字内容进行批改</p>
              <p>• <strong>图片 (JPG/PNG)</strong>：AI 先识别图片文字，确认无误后再批改</p>
              <p>• 请确保图片清晰，手写内容可识别</p>
            </div>
          </div>

          <!-- 提交按钮 -->
          <div class="flex justify-end pt-2">
            <el-button
              type="primary"
              size="large"
              @click="submitHomework"
              :loading="isGrading"
              :disabled="!canSubmit"
              icon="Check"
            >
              {{ isGrading ? 'AI 批改中...' : '🚀 提交批改' }}
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- PDF 导出用的隐藏渲染容器（绝对定位在视口外） -->
  <div
    id="pdf-export-container"
    ref="pdfExportContainerEl"
    style="position: absolute; left: -9999px; top: 0; width: 794px; background: white; padding: 48px; font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;"
  >
    <!-- PDF 封面信息 -->
    <div style="margin-bottom: 24px; padding-bottom: 20px; border-bottom: 2px solid #e5e7eb;">
      <h1 style="font-size: 22px; font-weight: 700; color: #111827; margin: 0 0 8px 0;">AI 作业批改报告</h1>
      <div style="display: flex; gap: 24px; font-size: 13px; color: #6b7280; flex-wrap: wrap;">
        <span>作业标题：{{ currentTitle || '我的作业' }}</span>
        <span>学科：{{ form.subject }}</span>
        <span v-if="finalScore !== null">得分：{{ finalScore.toFixed(0) }} / 100</span>
        <span>批改时间：{{ currentGradedAt || '刚刚' }}</span>
      </div>
      <div v-if="finalScore !== null" style="margin-top: 12px;">
        <span
          style="display: inline-block; padding: 4px 14px; border-radius: 20px; font-size: 13px; font-weight: 600;"
          :style="pdfScoreBadgeStyle(finalScore)"
        >
          {{ scoreLabel(finalScore) }}
        </span>
      </div>
    </div>
    <!-- PDF 报告内容 -->
    <div
      class="pdf-markdown-body"
      v-html="renderMessage(gradingReport)"
    ></div>
    <!-- PDF 页脚 -->
    <div style="margin-top: 32px; padding-top: 12px; border-top: 1px solid #e5e7eb; font-size: 11px; color: #9ca3af; text-align: center;">
      由 EduBuddy AI 智能学习助手生成 · {{ new Date().toLocaleDateString('zh-CN') }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { homeworkApi, createTextGradingStream, createFileGradingStream } from '@/api/homework'
import { ElMessage, ElMessageBox } from 'element-plus'
import { renderMessage, renderRecognizedText } from '@/utils/markdown'
// 引入 MathLive Web Component
import 'mathlive'

const authStore = useAuthStore()

// ─── 常量 ───────────────────────────────────────────────────
const subjects = ['数学', '物理', '化学', '生物', '语文', '英语', '历史', '地理', '政治']
const IMAGE_TYPES = ['jpg', 'jpeg', 'png', 'gif', 'webp']

// ─── 状态 ───────────────────────────────────────────────────
const submitMode = ref<'text' | 'file'>('text')
const viewMode = ref<'form' | 'result'>('form')
const isGrading = ref(false)
const isDragOver = ref(false)
const filterSubject = ref('')

// 表单
const form = ref({
  title: '',
  subject: '数学',
  content: '',
})

// 文件
const selectedFile = ref<File | null>(null)
const fileInputEl = ref<HTMLInputElement>()

// 图片识别
const isRecognizing = ref(false)
const recognizedText = ref<string | null>(null)
const recognizeConfidence = ref<string>('')
const recognizeError = ref<string>('')
const recognizeEditMode = ref(false)

// MathLive 公式编辑器
const showMathEditor = ref(false)
const mathFieldEl = ref<any>(null)           // <math-field> 元素引用
const recognizeTextareaEl = ref<HTMLTextAreaElement>()  // textarea 引用
const currentMathLatex = ref('')             // 当前公式编辑器中的 LaTeX

// ─── Undo / Redo 状态 ────────────────────────────────────────
const undoStack = ref<string[]>([])         // 历史快照栈
const redoStack = ref<string[]>([])         // 重做快照栈
const MAX_HISTORY = 100                      // 最大历史记录数
let inputDebounceTimer: ReturnType<typeof setTimeout> | null = null
let isUndoRedoOperation = false              // 标记是否正在执行 undo/redo，防止重复入栈

/** 将当前 recognizedText 快照推入 undo 栈（在变更前调用） */
function pushUndoSnapshot(prevValue: string) {
  if (isUndoRedoOperation) return
  undoStack.value.push(prevValue)
  if (undoStack.value.length > MAX_HISTORY) {
    undoStack.value.shift()
  }
  // 任何新编辑操作都清空 redo 栈
  redoStack.value = []
}

/** 撤销：还原到上一个快照 */
function undoRecognizedText() {
  if (undoStack.value.length === 0) return
  isUndoRedoOperation = true
  const current = recognizedText.value ?? ''
  redoStack.value.push(current)
  recognizedText.value = undoStack.value.pop()!
  isUndoRedoOperation = false
  nextTick(() => {
    recognizeTextareaEl.value?.focus()
  })
}

/** 重做：前进到下一个快照 */
function redoRecognizedText() {
  if (redoStack.value.length === 0) return
  isUndoRedoOperation = true
  const current = recognizedText.value ?? ''
  undoStack.value.push(current)
  recognizedText.value = redoStack.value.pop()!
  isUndoRedoOperation = false
  nextTick(() => {
    recognizeTextareaEl.value?.focus()
  })
}

/** textarea input 事件：防抖推快照 */
function onRecognizeInput(e: Event) {
  if (isUndoRedoOperation) return
  // 取 input 事件触发前的值（通过 beforeinput 或 debounce 方案）
  // 这里使用 debounce：每隔 500ms 才推一次快照
  if (inputDebounceTimer) clearTimeout(inputDebounceTimer)
  inputDebounceTimer = setTimeout(() => {
    // 将当前值记录到快照（在下次输入发生时）
    // 因为 v-model 已经更新了 recognizedText，
    // 我们需要记录的是当前值（供下次撤销时还原）
    // 这里直接在每次 debounce 末尾记录当前值为新基准（不推旧值了）
    // 正确做法：在 beforeinput 记录旧值
  }, 500)
}

/** textarea keydown：监听 Ctrl+Z / Ctrl+Y */
function onRecognizeKeydown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
    e.preventDefault()
    undoRecognizedText()
  } else if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.shiftKey && e.key === 'z'))) {
    e.preventDefault()
    redoRecognizedText()
  }
}

/** 使用 beforeinput 事件在真正输入前记录快照（更准确）*/
function setupTextareaUndoTracking() {
  nextTick(() => {
    const ta = recognizeTextareaEl.value
    if (!ta) return
    // 移除旧监听，避免重复
    ta.removeEventListener('beforeinput', handleBeforeInput)
    ta.addEventListener('beforeinput', handleBeforeInput)
  })
}

function handleBeforeInput(_e: InputEvent) {
  if (isUndoRedoOperation) return
  pushUndoSnapshot(recognizedText.value ?? '')
}

// 监听编辑模式切换，进入编辑模式时绑定 beforeinput
watch(recognizeEditMode, (val) => {
  if (val) {
    setupTextareaUndoTracking()
  }
})

// 监听识别文本变化（重新识别时清空历史）
watch(() => recognizedText.value, (newVal, oldVal) => {
  if (!isUndoRedoOperation && oldVal === null && newVal !== null) {
    // 初次识别完成，清空历史
    undoStack.value = []
    redoStack.value = []
  }
})

function onMathFieldInput(e: Event) {
  const mf = e.target as any
  currentMathLatex.value = mf.value || ''
}

function insertMathToText() {
  const latex = currentMathLatex.value.trim()
  if (!latex) return

  const insertion = `$${latex}$`
  const ta = recognizeTextareaEl.value
  if (ta && recognizedText.value !== null) {
    // 插入前先保存快照
    pushUndoSnapshot(recognizedText.value)
    const start = ta.selectionStart ?? recognizedText.value.length
    const end = ta.selectionEnd ?? start
    const text = recognizedText.value
    recognizedText.value = text.slice(0, start) + insertion + text.slice(end)
    // 恢复光标位置到插入内容之后
    nextTick(() => {
      ta.focus()
      const newPos = start + insertion.length
      ta.setSelectionRange(newPos, newPos)
    })
  } else if (recognizedText.value !== null) {
    pushUndoSnapshot(recognizedText.value)
    recognizedText.value += insertion
  }

  // 清空公式编辑器
  if (mathFieldEl.value) {
    mathFieldEl.value.value = ''
  }
  currentMathLatex.value = ''
  showMathEditor.value = false
}

// 批改结果
const gradingReport = ref('')
const finalScore = ref<number | null>(null)
const currentGradingId = ref<number | null>(null)
const currentTitle = ref('')
const currentGradedAt = ref('')

// 历史记录
const historyList = ref<any[]>([])

// PDF 导出
const isExportingPDF = ref(false)
const reportContentEl = ref<HTMLElement>()
const pdfExportContainerEl = ref<HTMLElement>()

// ─── 计算属性 ───────────────────────────────────────────────
const isImageFile = computed(() => {
  if (!selectedFile.value) return false
  const ext = selectedFile.value.name.split('.').pop()?.toLowerCase() || ''
  return IMAGE_TYPES.includes(ext)
})

const canSubmit = computed(() => {
  if (isGrading.value || isRecognizing.value) return false
  if (submitMode.value === 'text') return form.value.content.trim().length > 0
  if (!selectedFile.value) return false
  // 图片文件：需要识别完成（不论成功还是失败都可以提交）
  if (isImageFile.value && recognizedText.value === null && !recognizeError.value) return false
  return true
})

// ─── PDF 导出（新窗口打印方案，彻底绕过 html2canvas + oklch 兼容问题） ─────
async function exportToPDF() {
  if (!gradingReport.value || isExportingPDF.value) return

  isExportingPDF.value = true

  try {
    const scoreHtml = finalScore.value !== null ? (() => {
      const s = finalScore.value!
      let bg = '#fee2e2'; let fg = '#dc2626'
      if (s >= 90) { bg = '#dcfce7'; fg = '#16a34a' }
      else if (s >= 75) { bg = '#dbeafe'; fg = '#1d4ed8' }
      else if (s >= 60) { bg = '#fef3c7'; fg = '#d97706' }
      return `<span style="display:inline-block;padding:3px 14px;border-radius:20px;font-size:13px;font-weight:600;background:${bg};color:${fg};">${scoreLabel(s)}</span>`
    })() : ''

    const reportHtml = renderMessage(gradingReport.value)
    const safeTitle = (currentTitle.value || '作业批改报告')
      .replace(/[<>:"/\\|?*]/g, '_').slice(0, 50)

    // 构建完整 HTML，包含打印样式
    const fullHtml = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>${escapeHtml(safeTitle)}</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #ffffff;
    color: #1f2937;
    font-family: "PingFang SC", "Microsoft YaHei", "SimSun", sans-serif;
    font-size: 14px;
    line-height: 1.8;
    padding: 0;
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
  .header-meta { display: flex; flex-wrap: wrap; gap: 16px; font-size: 13px; color: #6b7280; margin-bottom: 8px; }
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
    <h1>AI 作业批改报告</h1>
    <div class="header-meta">
      <span>作业标题：${escapeHtml(currentTitle.value || '我的作业')}</span>
      <span>学科：${escapeHtml(form.value.subject)}</span>
      ${finalScore.value !== null ? `<span>得分：${finalScore.value.toFixed(0)} / 100</span>` : ''}
      <span>批改时间：${escapeHtml(currentGradedAt.value || '刚刚')}</span>
    </div>
    ${scoreHtml ? `<div style="margin-top:8px;">${scoreHtml}</div>` : ''}
  </div>
  <div class="report-body">${reportHtml}</div>
  <div class="footer">由 EduBuddy AI 智能学习助手生成 · ${new Date().toLocaleDateString('zh-CN')}</div>
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

    // 在新窗口中打开
    const printWindow = window.open('', '_blank', 'width=900,height=700')
    if (!printWindow) {
      throw new Error('无法打开新窗口，请检查浏览器是否阻止了弹出窗口')
    }

    printWindow.document.open()
    printWindow.document.write(fullHtml)
    printWindow.document.close()

    ElMessage.success('已打开打印预览，请选择"另存为 PDF"保存文件')
  } catch (err: any) {
    console.error('PDF 导出失败:', err)
    ElMessage.error('导出失败：' + (err?.message || '未知错误'))
  } finally {
    isExportingPDF.value = false
  }
}

/** HTML 转义，防止 XSS */
function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function pdfScoreBadgeStyle(score: number) {
  if (score >= 90) return 'background: #dcfce7; color: #16a34a;'
  if (score >= 75) return 'background: #dbeafe; color: #1d4ed8;'
  if (score >= 60) return 'background: #fef3c7; color: #d97706;'
  return 'background: #fee2e2; color: #dc2626;'
}

// ─── 历史记录 ───────────────────────────────────────────────
async function loadHistory() {
  try {
    const res: any = await homeworkApi.getHistory({
      subject: filterSubject.value || undefined,
    })
    historyList.value = res.data?.items || []
  } catch {}
}

watch(filterSubject, loadHistory)

async function loadDetail(id: number) {
  try {
    const res: any = await homeworkApi.getDetail(id)
    const data = res.data
    currentGradingId.value = data.id
    currentTitle.value = data.title
    form.value.subject = data.subject
    gradingReport.value = data.detailed_feedback || ''
    finalScore.value = data.score ?? null
    currentGradedAt.value = data.graded_at ? formatDate(data.graded_at) : ''
    viewMode.value = 'result'
  } catch {
    ElMessage.error('加载批改详情失败')
  }
}

async function confirmDelete(item: any) {
  try {
    await ElMessageBox.confirm(
      `确定要删除「${item.title}」的批改记录吗？`,
      '删除确认',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning', confirmButtonClass: 'el-button--danger' }
    )
    await homeworkApi.deleteGrading(item.id)
    if (currentGradingId.value === item.id) startNew()
    await loadHistory()
    ElMessage.success('已删除')
  } catch (e: any) {
    if (e !== 'cancel' && e?.message !== 'cancel') ElMessage.error('删除失败')
  }
}

// ─── 文件处理 ───────────────────────────────────────────────
function handleFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files?.[0]) {
    setFile(input.files[0])
  }
}

function handleDrop(e: DragEvent) {
  isDragOver.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) setFile(file)
}

function setFile(file: File) {
  selectedFile.value = file
  if (!form.value.title) {
    form.value.title = file.name.replace(/\.[^.]+$/, '')
  }
  // 重置识别状态
  recognizedText.value = null
  recognizeConfidence.value = ''
  recognizeError.value = ''
  undoStack.value = []
  redoStack.value = []
  // 如果是图片，自动触发识别
  const ext = file.name.split('.').pop()?.toLowerCase() || ''
  if (IMAGE_TYPES.includes(ext)) {
    triggerRecognize(file)
  }
}

function clearFile() {
  selectedFile.value = null
  recognizedText.value = null
  recognizeConfidence.value = ''
  recognizeError.value = ''
  undoStack.value = []
  redoStack.value = []
  if (fileInputEl.value) fileInputEl.value.value = ''
}

async function triggerRecognize(file: File) {
  isRecognizing.value = true
  recognizedText.value = null
  recognizeError.value = ''
  undoStack.value = []
  redoStack.value = []
  try {
    const res: any = await homeworkApi.recognizeImage(file)
    recognizedText.value = res.data?.recognized_text ?? ''
    recognizeConfidence.value = res.data?.confidence ?? 'low'
  } catch (e: any) {
    recognizeError.value = e?.response?.data?.detail || e?.message || '识别失败'
  } finally {
    isRecognizing.value = false
  }
}

function retryRecognize() {
  if (selectedFile.value) {
    triggerRecognize(selectedFile.value)
  }
}

// ─── 提交批改 ───────────────────────────────────────────────
function submitHomework() {
  if (!canSubmit.value) return

  // 重置结果
  gradingReport.value = ''
  finalScore.value = null
  currentTitle.value = form.value.title || (submitMode.value === 'file' ? selectedFile.value!.name : '我的作业')
  viewMode.value = 'result'
  isGrading.value = true

  const token = authStore.token || ''

  if (submitMode.value === 'text') {
    createTextGradingStream(
      {
        title: form.value.title || '我的作业',
        subject: form.value.subject,
        content: form.value.content,
      },
      token,
      (delta) => { gradingReport.value += delta },
      (gradingId, score) => {
        isGrading.value = false
        finalScore.value = score
        currentGradingId.value = gradingId
        currentGradedAt.value = '刚刚'
        loadHistory()
      },
      (errMsg) => {
        isGrading.value = false
        ElMessage.error('批改失败：' + errMsg)
        viewMode.value = 'form'
      },
    )
  } else {
    const fd = new FormData()
    fd.append('subject', form.value.subject)
    fd.append('title', form.value.title || selectedFile.value!.name)
    fd.append('file', selectedFile.value!)

    createFileGradingStream(
      fd,
      token,
      (delta) => { gradingReport.value += delta },
      (gradingId, score) => {
        isGrading.value = false
        finalScore.value = score
        currentGradingId.value = gradingId
        currentGradedAt.value = '刚刚'
        loadHistory()
      },
      (errMsg) => {
        isGrading.value = false
        ElMessage.error('批改失败：' + errMsg)
        viewMode.value = 'form'
      },
    )
  }
}

function startNew() {
  viewMode.value = 'form'
  gradingReport.value = ''
  finalScore.value = null
  currentGradingId.value = null
  currentTitle.value = ''
  form.value.title = ''
  form.value.content = ''
  selectedFile.value = null
  recognizedText.value = null
  recognizeConfidence.value = ''
  recognizeError.value = ''
  undoStack.value = []
  redoStack.value = []
  if (fileInputEl.value) fileInputEl.value.value = ''
}

// ─── 工具函数 ───────────────────────────────────────────────
function formatDate(iso: string) {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return d.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
}

function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function fileIcon(name: string) {
  const ext = name.split('.').pop()?.toLowerCase()
  if (ext === 'pdf') return '📄'
  if (ext === 'docx' || ext === 'doc') return '📝'
  if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext || '')) return '🖼️'
  return '📎'
}

function scoreColorClass(score: number) {
  if (score >= 90) return 'text-green-600'
  if (score >= 75) return 'text-blue-600'
  if (score >= 60) return 'text-amber-600'
  return 'text-red-500'
}

function scoreBorderClass(score: number) {
  if (score >= 90) return 'border-green-400'
  if (score >= 75) return 'border-blue-400'
  if (score >= 60) return 'border-amber-400'
  return 'border-red-400'
}

function scoreLabel(score: number) {
  if (score >= 90) return '优秀 🌟'
  if (score >= 80) return '良好 👍'
  if (score >= 70) return '中等 📚'
  if (score >= 60) return '及格 💪'
  return '需要加油 📖'
}

function subjectColorClass(subject: string) {
  const map: Record<string, string> = {
    数学: 'bg-blue-100 text-blue-700',
    物理: 'bg-purple-100 text-purple-700',
    化学: 'bg-green-100 text-green-700',
    生物: 'bg-emerald-100 text-emerald-700',
    语文: 'bg-red-100 text-red-700',
    英语: 'bg-sky-100 text-sky-700',
    历史: 'bg-amber-100 text-amber-700',
    地理: 'bg-teal-100 text-teal-700',
    政治: 'bg-orange-100 text-orange-700',
  }
  return map[subject] || 'bg-gray-100 text-gray-600'
}

// ─── 生命周期 ───────────────────────────────────────────────
onMounted(async () => {
  await loadHistory()
})
</script>

<style scoped>
/* 打字光标 */
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

/* Markdown 批改报告样式 */
.markdown-body {
  font-size: 0.875rem;
  line-height: 1.75;
  word-break: break-word;
}

.markdown-body :deep(p) { margin: 0.4em 0; }
.markdown-body :deep(p:first-child) { margin-top: 0; }
.markdown-body :deep(p:last-child) { margin-bottom: 0; }

.markdown-body :deep(strong) {
  font-weight: 600;
  color: #111827;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 1.5em;
  margin: 0.4em 0;
}

.markdown-body :deep(li) { margin: 0.2em 0; }

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4) {
  font-weight: 600;
  margin: 0.8em 0 0.4em;
  color: #1f2937;
}

.markdown-body :deep(h1) { font-size: 1.15em; }
.markdown-body :deep(h2) { font-size: 1.1em; color: #1d4ed8; }
.markdown-body :deep(h3) { font-size: 1em; }

.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 0.6em 0;
  font-size: 0.875em;
}

.markdown-body :deep(th) {
  background: #f1f5f9;
  padding: 6px 10px;
  text-align: left;
  font-weight: 600;
  border: 1px solid #e2e8f0;
}

.markdown-body :deep(td) {
  padding: 5px 10px;
  border: 1px solid #e2e8f0;
}

.markdown-body :deep(tr:nth-child(even) td) {
  background: #f8fafc;
}

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
  margin: 0.8em 0;
}

.markdown-body :deep(.katex-display) {
  margin: 0.6em 0;
  overflow-x: auto;
}

.markdown-body :deep(.katex) {
  font-size: 1em;
}
</style>

<!-- PDF 导出容器的全局样式（不使用 scoped） -->
<style>
#pdf-export-container .pdf-markdown-body {
  font-size: 14px;
  line-height: 1.8;
  word-break: break-word;
  color: #1f2937;
}
#pdf-export-container .pdf-markdown-body p { margin: 0.5em 0; }
#pdf-export-container .pdf-markdown-body strong { font-weight: 700; color: #111827; }
#pdf-export-container .pdf-markdown-body h1,
#pdf-export-container .pdf-markdown-body h2,
#pdf-export-container .pdf-markdown-body h3 {
  font-weight: 700;
  margin: 1em 0 0.5em;
  color: #1f2937;
}
#pdf-export-container .pdf-markdown-body h1 { font-size: 1.3em; }
#pdf-export-container .pdf-markdown-body h2 { font-size: 1.15em; color: #1d4ed8; }
#pdf-export-container .pdf-markdown-body h3 { font-size: 1.05em; }
#pdf-export-container .pdf-markdown-body ul,
#pdf-export-container .pdf-markdown-body ol {
  padding-left: 1.8em;
  margin: 0.5em 0;
}
#pdf-export-container .pdf-markdown-body li { margin: 0.3em 0; }
#pdf-export-container .pdf-markdown-body table {
  width: 100%;
  border-collapse: collapse;
  margin: 0.8em 0;
  font-size: 0.9em;
}
#pdf-export-container .pdf-markdown-body th {
  background: #f1f5f9;
  padding: 8px 12px;
  font-weight: 600;
  border: 1px solid #cbd5e1;
  text-align: left;
}
#pdf-export-container .pdf-markdown-body td {
  padding: 6px 12px;
  border: 1px solid #cbd5e1;
}
#pdf-export-container .pdf-markdown-body tr:nth-child(even) td {
  background: #f8fafc;
}
#pdf-export-container .pdf-markdown-body code {
  background: #f1f5f9;
  border-radius: 3px;
  padding: 0.1em 0.4em;
  font-family: 'Fira Code', 'Courier New', monospace;
  font-size: 0.88em;
}
#pdf-export-container .pdf-markdown-body blockquote {
  border-left: 4px solid #3b82f6;
  padding-left: 1em;
  margin: 0.5em 0;
  color: #4b5563;
  background: #eff6ff;
  border-radius: 0 6px 6px 0;
}
#pdf-export-container .pdf-markdown-body hr {
  border: none;
  border-top: 1px solid #e5e7eb;
  margin: 1em 0;
}
</style>
