<template>
  <div class="space-y-6">
    <!-- 没有计划时显示创建 -->
    <div v-if="!plan && !showCreate" class="text-center py-16">
      <span class="text-5xl">📅</span>
      <p class="mt-4 text-lg text-gray-600">还没有学习计划，制定一个目标吧！</p>
      <el-button type="primary" class="mt-4" @click="showCreate = true">创建学习计划</el-button>
    </div>

    <!-- 创建计划表单 -->
    <div v-if="showCreate" class="card max-w-2xl mx-auto space-y-4">
      <h3 class="font-bold text-gray-800">📅 制定学习计划</h3>
      <p class="text-sm text-gray-500">计划制定后将生成每天的学习任务索引，每天第一次登录时自动生成当日的具体学习内容。</p>
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-600 mb-1">备考学科（多选）</label>
          <el-checkbox-group v-model="createForm.subjects">
            <el-checkbox v-for="s in subjects" :key="s" :value="s">{{ s }}</el-checkbox>
          </el-checkbox-group>
        </div>
        <div class="space-y-3">
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">考试日期</label>
            <el-date-picker v-model="createForm.exam_date" type="date" value-format="YYYY-MM-DD" class="w-full" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">每天学习时长（小时）</label>
            <el-input-number v-model="createForm.daily_hours" :min="0.5" :max="12" :step="0.5" />
          </div>
        </div>
      </div>
      <div class="flex gap-3">
        <el-button type="primary" @click="generatePlan" :loading="generating">生成计划</el-button>
        <el-button @click="showCreate = false">取消</el-button>
      </div>
    </div>

    <!-- 已有计划 -->
    <template v-if="plan && !showCreate">
      <!-- 概览 -->
      <div class="card">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-500">考试倒计时</p>
            <p class="text-2xl font-bold text-gray-800">还有 {{ daysLeft }} 天</p>
          </div>
          <div class="text-right">
            <p class="text-sm text-gray-500">今日完成</p>
            <p class="text-2xl font-bold text-green-600">{{ todayDone }}/{{ todayTotal }}</p>
          </div>
          <el-button size="small" @click="showCreate = true">⚙ 重新生成</el-button>
        </div>
        <div class="mt-3 w-full bg-gray-200 rounded-full h-2">
          <div class="bg-green-500 h-2 rounded-full transition-all"
            :style="`width: ${todayTotal > 0 ? (todayDone / todayTotal) * 100 : 0}%`"></div>
        </div>
      </div>

      <!-- 每日内容生成进度条（当日第一次登录时显示） -->
      <div v-if="generatingTodayContent" class="card border-indigo-200 bg-indigo-50">
        <div class="flex items-center gap-3">
          <div class="animate-spin text-2xl">⏳</div>
          <div class="flex-1">
            <p class="font-medium text-indigo-700">正在为今日学习任务生成 AI 内容...</p>
            <p v-if="todayGenerateProgress" class="text-sm text-indigo-600 mt-1">
              （{{ todayGenerateProgress.current }}/{{ todayGenerateProgress.total }}）
              正在生成：{{ todayGenerateProgress.subject }} · {{ todayGenerateProgress.topic }}
            </p>
            <div class="mt-2 w-full bg-indigo-200 rounded-full h-1.5">
              <div class="bg-indigo-500 h-1.5 rounded-full transition-all"
                :style="`width: ${todayGenerateProgress ? (todayGenerateProgress.current / todayGenerateProgress.total) * 100 : 0}%`"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 标签页：今日计划 / 计划档案 -->
      <div class="card">
        <div class="flex border-b border-gray-200 mb-4 gap-1">
          <button
            @click="activeTab = 'today'"
            class="px-4 py-2 text-sm font-medium rounded-t-lg border-b-2 transition-colors"
            :class="activeTab === 'today'
              ? 'border-indigo-500 text-indigo-600 bg-indigo-50'
              : 'border-transparent text-gray-500 hover:text-gray-700'">
            📋 今日学习
          </button>
          <button
            @click="activeTab = 'all'"
            class="px-4 py-2 text-sm font-medium rounded-t-lg border-b-2 transition-colors"
            :class="activeTab === 'all'
              ? 'border-indigo-500 text-indigo-600 bg-indigo-50'
              : 'border-transparent text-gray-500 hover:text-gray-700'">
            🗓 计划档案
            <span class="ml-1 text-xs text-gray-400">（只读）</span>
          </button>
        </div>

        <!-- 今日学习面板（可交互） -->
        <div v-if="activeTab === 'today'">
          <div v-if="todayTasks.length === 0 && !generatingTodayContent" class="text-center py-4 text-gray-400 text-sm">
            今日无学习任务
          </div>
          <div v-else-if="generatingTodayContent && todayTasks.length === 0" class="text-center py-4 text-gray-400 text-sm">
            正在准备今日学习内容，请稍候...
          </div>
          <div class="space-y-3">
            <div v-for="task in todayTasks" :key="task.id"
              class="rounded-lg border transition-colors overflow-hidden"
              :class="task.is_done ? 'border-green-200' : 'border-gray-200'">
              <!-- 任务头部 -->
              <div class="flex items-center gap-3 p-3"
                :class="task.is_done ? 'bg-green-50' : 'bg-gray-50'">
                <input type="checkbox" :checked="task.is_done" @change="toggleTask(task)"
                  class="w-4 h-4 rounded border-gray-300 text-green-500 cursor-pointer" />
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-gray-700">{{ task.subject }} · {{ task.topic }}</p>
                  <p class="text-xs text-gray-500">{{ task.duration_minutes }}分钟 · {{ taskTypeLabel(task.task_type) }}
                    <span v-if="task.eval_score != null"
                      class="ml-2 text-indigo-600 font-medium">成果评分：{{ task.eval_score }}分</span>
                    <span v-if="task.quiz_score != null"
                      class="ml-2 text-purple-600 font-medium">练习得分：{{ task.quiz_score }}分</span>
                  </p>
                </div>
                <button @click="toggleExpand(task.id)"
                  class="text-xs text-gray-500 hover:text-indigo-600 px-2 py-1 rounded border border-gray-200 hover:border-indigo-300 transition-colors">
                  {{ expandedTaskId === task.id ? '收起 ▲' : '展开 ▼' }}
                </button>
              </div>

              <!-- 展开内容区域（今日可交互） -->
              <div v-if="expandedTaskId === task.id" class="border-t border-gray-100 bg-white">
                <!-- 面板切换 -->
                <div class="flex gap-1 px-4 pt-3">
                  <button v-for="panel in taskPanels" :key="panel.key"
                    @click="activePanel[task.id] = panel.key"
                    class="text-xs px-3 py-1 rounded-full border transition-colors"
                    :class="activePanel[task.id] === panel.key
                      ? 'bg-indigo-500 text-white border-indigo-500'
                      : 'border-gray-300 text-gray-600 hover:border-indigo-300'">
                    {{ panel.label }}
                  </button>
                </div>

                <!-- AI 学习内容面板 -->
                <div v-if="activePanel[task.id] === 'ai_content'" class="p-4 space-y-3">
                  <!-- 正在批量生成中 -->
                  <div v-if="generatingTodayContent && !task.ai_content && !streamingContent[task.id]"
                    class="bg-indigo-50 rounded p-3 text-xs text-indigo-600">
                    ⏳ 正在生成学习内容，请稍候...
                  </div>
                  <!-- 流式生成预览 -->
                  <div v-else-if="streamingContent[task.id]"
                    class="bg-gray-50 rounded p-3 text-xs text-gray-700">
                    <div class="prose prose-sm" v-html="renderMd(streamingContent[task.id])"></div>
                  </div>
                  <!-- 已生成内容展示 -->
                  <div v-else-if="task.ai_content"
                    class="bg-blue-50 rounded p-3 text-sm text-gray-700">
                    <div class="prose prose-sm" v-html="renderMd(task.ai_content)"></div>
                  </div>
                  <!-- 未生成 -->
                  <div v-else class="text-xs text-gray-400">尚未生成学习内容</div>

                  <div class="flex gap-2 flex-wrap">
                    <button @click="startGenerateContent(task)"
                      class="text-xs px-3 py-1.5 rounded border border-indigo-300 text-indigo-600 hover:bg-indigo-50 transition-colors"
                      :disabled="generatingContent[task.id] || generatingTodayContent">
                      {{ generatingContent[task.id] ? '⏳ 生成中...' : '🤖 重新生成内容' }}
                    </button>
                    <button v-if="!task.is_done && task.ai_content" @click="markDoneByAI(task)"
                      class="text-xs px-3 py-1.5 rounded border border-green-300 text-green-600 hover:bg-green-50 transition-colors">
                      ✅ 已阅读，标记完成
                    </button>
                  </div>
                </div>

                <!-- 提交成果面板 -->
                <div v-if="activePanel[task.id] === 'submit'" class="p-4 space-y-3">
                  <!-- 已有评判结果 -->
                  <div v-if="task.evaluation && !streamingEval[task.id]">
                    <div class="bg-green-50 rounded p-3 text-sm text-gray-700">
                      <div class="prose prose-sm" v-html="renderMd(task.evaluation)"></div>
                    </div>
                    <button @click="resetSubmission(task)"
                      class="mt-2 text-xs px-3 py-1.5 rounded border border-gray-300 text-gray-600 hover:bg-gray-50">
                      🔄 重新提交
                    </button>
                  </div>
                  <!-- 评判流式中 -->
                  <div v-else-if="streamingEval[task.id]"
                    class="bg-gray-50 rounded p-3 text-xs text-gray-700">
                    <div class="prose prose-sm" v-html="renderMd(streamingEval[task.id])"></div>
                  </div>
                  <!-- 提交表单 -->
                  <div v-else>
                    <p class="text-xs text-gray-500 mb-2">描述你的学习成果，或上传学习笔记图片，由 AI 评判掌握程度</p>
                    <textarea
                      :value="submissionText[task.id] || ''"
                      @input="(e: Event) => submissionText[task.id] = (e.target as HTMLTextAreaElement).value"
                      placeholder="描述你学到了什么、解题思路、还有哪些疑问..."
                      class="w-full border border-gray-300 rounded p-2 text-sm resize-none h-20 focus:outline-none focus:border-indigo-400"></textarea>
                    <div class="flex gap-2 mt-2 items-center">
                      <input type="file" accept="image/*"
                        @change="(e: Event) => { const f = (e.target as HTMLInputElement).files?.[0]; if(f) submissionFile[task.id] = f }"
                        class="text-xs text-gray-500 flex-1" />
                      <button @click="startSubmit(task)"
                        :disabled="submitting[task.id] || (!submissionText[task.id] && !submissionFile[task.id])"
                        class="text-xs px-3 py-1.5 rounded border border-purple-300 text-purple-600 hover:bg-purple-50 transition-colors disabled:opacity-50">
                        {{ submitting[task.id] ? '⏳ 评判中...' : '📤 提交成果' }}
                      </button>
                    </div>
                  </div>
                </div>

                <!-- 练习题面板 -->
                <div v-if="activePanel[task.id] === 'quiz'" class="p-4 space-y-3">
                  <!-- 已有评判结果 -->
                  <div v-if="task.quiz_evaluation && !streamingQuizEval[task.id]">
                    <div class="bg-purple-50 rounded p-3 text-sm text-gray-700">
                      <div class="prose prose-sm" v-html="renderMd(task.quiz_evaluation)"></div>
                    </div>
                    <button @click="resetQuiz(task)"
                      class="mt-2 text-xs px-3 py-1.5 rounded border border-gray-300 text-gray-600 hover:bg-gray-50">
                      🔄 重新练习
                    </button>
                  </div>
                  <!-- 练习题评判流式中 -->
                  <div v-else-if="streamingQuizEval[task.id]"
                    class="bg-gray-50 rounded p-3 text-xs text-gray-700">
                    <div class="prose prose-sm" v-html="renderMd(streamingQuizEval[task.id])"></div>
                  </div>
                  <!-- 练习题生成中 -->
                  <div v-else-if="generatingQuiz[task.id]"
                    class="text-xs text-gray-500">⏳ 正在生成练习题...</div>
                  <!-- 练习题列表 -->
                  <div v-else-if="parsedQuiz[task.id] && parsedQuiz[task.id].length > 0" class="space-y-3">
                    <div v-for="q in parsedQuiz[task.id]" :key="q.id" class="border border-gray-100 rounded p-3">
                      <p class="text-sm font-medium text-gray-700 mb-2 latex-content"
                        v-html="`${q.id}. ` + renderLatexOnly(q.question)"></p>
                      <!-- 选择题 -->
                      <div v-if="q.type === 'choice'" class="space-y-1">
                        <label v-for="opt in q.options" :key="opt"
                          class="flex items-center gap-2 text-xs text-gray-600 cursor-pointer hover:text-indigo-600">
                          <input type="radio"
                            :name="`quiz-${task.id}-${q.id}`"
                            :value="opt.charAt(0)"
                            :checked="(quizAnswers[task.id] || {})[String(q.id)] === opt.charAt(0)"
                            @change="setQuizAnswer(task.id, String(q.id), opt.charAt(0))" />
                          <span class="latex-content" v-html="renderLatexOnly(opt)"></span>
                        </label>
                      </div>
                      <!-- 填空/简答题 -->
                      <div v-else>
                        <input type="text"
                          :value="(quizAnswers[task.id] || {})[String(q.id)] || ''"
                          @input="(e: Event) => setQuizAnswer(task.id, String(q.id), (e.target as HTMLInputElement).value)"
                          placeholder="输入答案..."
                          class="w-full border border-gray-200 rounded px-2 py-1 text-xs focus:outline-none focus:border-indigo-300" />
                      </div>
                    </div>
                    <div class="flex gap-2">
                      <button @click="startSubmitQuiz(task)"
                        :disabled="submittingQuiz[task.id] || !hasAllAnswers(task.id)"
                        class="text-xs px-3 py-1.5 rounded border border-purple-300 text-purple-600 hover:bg-purple-50 disabled:opacity-50">
                        {{ submittingQuiz[task.id] ? '⏳ 评判中...' : '📝 提交答案' }}
                      </button>
                    </div>
                  </div>
                  <!-- 未生成 -->
                  <div v-else>
                    <p class="text-xs text-gray-400 mb-2">尚未生成练习题</p>
                    <button @click="startGenerateQuiz(task)"
                      class="text-xs px-3 py-1.5 rounded border border-purple-300 text-purple-600 hover:bg-purple-50">
                      🎯 生成练习题
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 计划档案面板（只读查看） -->
        <div v-if="activeTab === 'all'">
          <div class="mb-3 p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-700">
            📚 计划档案为只读模式。历史日期的学习内容已存档保存，仅供查看，无法修改。
          </div>

          <!-- 学科过滤 -->
          <div v-if="allSubjectsInPlan.length > 0" class="mb-4 flex flex-wrap gap-2 items-center">
            <span class="text-xs text-gray-500 mr-1">按学科筛选：</span>
            <button
              @click="filterSubject = ''"
              class="px-2 py-1 rounded-full text-xs border transition-colors"
              :class="filterSubject === '' ? 'bg-indigo-500 text-white border-indigo-500' : 'border-gray-300 text-gray-600 hover:border-indigo-300'">
              全部
            </button>
            <button
              v-for="s in allSubjectsInPlan" :key="s"
              @click="filterSubject = s"
              class="px-2 py-1 rounded-full text-xs border transition-colors"
              :class="filterSubject === s ? 'bg-indigo-500 text-white border-indigo-500' : 'border-gray-300 text-gray-600 hover:border-indigo-300'">
              {{ s }}
            </button>
          </div>

          <div v-if="filteredDateKeys.length === 0" class="text-center py-6 text-gray-400 text-sm">
            暂无计划任务
          </div>

          <div class="space-y-4">
            <div v-for="dateKey in filteredDateKeys" :key="dateKey">
              <!-- 日期标题 -->
              <div class="flex items-center gap-2 mb-2 sticky top-0 bg-white py-1 z-10">
                <span class="text-sm font-semibold text-gray-700">{{ formatDateLabel(dateKey) }}</span>
                <span v-if="dateKey === todayStr"
                  class="text-xs bg-indigo-500 text-white px-2 py-0.5 rounded-full">今天</span>
                <span v-else-if="dateKey < todayStr"
                  class="text-xs bg-gray-300 text-gray-600 px-2 py-0.5 rounded-full">已过期</span>
                <span v-else
                  class="text-xs bg-blue-100 text-blue-600 px-2 py-0.5 rounded-full">待学习</span>
                <div class="flex-1 h-px bg-gray-200"></div>
              </div>
              <!-- 当天任务列表（只读） -->
              <div class="space-y-2 pl-2">
                <div v-for="task in getFilteredTasksForDate(dateKey)" :key="task.id"
                  class="rounded-lg border overflow-hidden"
                  :class="task.is_done ? 'border-green-200' : (dateKey < todayStr ? 'border-orange-100' : 'border-gray-200')">
                  <!-- 只读任务头部 -->
                  <div class="flex items-center gap-3 p-3"
                    :class="task.is_done ? 'bg-green-50' : (dateKey < todayStr ? 'bg-orange-50' : 'bg-gray-50')">
                    <span class="text-base">{{ task.is_done ? '✅' : (dateKey < todayStr ? '⚠️' : '📝') }}</span>
                    <div class="flex-1 min-w-0">
                      <p class="text-sm font-medium text-gray-700">{{ task.subject }} · {{ task.topic }}</p>
                      <p class="text-xs text-gray-500">{{ task.duration_minutes }}分钟 · {{ taskTypeLabel(task.task_type) }}
                        <span v-if="task.eval_score != null" class="ml-2 text-indigo-600">成果评分：{{ task.eval_score }}分</span>
                        <span v-if="task.quiz_score != null" class="ml-2 text-purple-600">练习得分：{{ task.quiz_score }}分</span>
                      </p>
                    </div>
                    <!-- 只有当日任务才能展开；历史/未来任务可查看已存档内容 -->
                    <button v-if="task.ai_content || task.evaluation || task.quiz_evaluation"
                      @click="toggleArchiveExpand(task.id)"
                      class="text-xs text-gray-500 hover:text-indigo-600 px-2 py-1 rounded border border-gray-200 hover:border-indigo-300">
                      {{ archiveExpandedId === task.id ? '收起 ▲' : '查看存档 ▼' }}
                    </button>
                    <span v-else-if="dateKey > todayStr" class="text-xs text-gray-400 px-2">待生成</span>
                  </div>
                  <!-- 只读存档内容 -->
                  <div v-if="archiveExpandedId === task.id" class="border-t border-gray-100 bg-gray-50 p-4 space-y-3">
                    <div v-if="task.ai_content">
                      <p class="text-xs font-medium text-gray-500 mb-1">📖 学习内容（存档）</p>
                      <div class="bg-white rounded p-3 text-sm text-gray-700 border border-gray-100">
                        <div class="prose prose-sm" v-html="renderMd(task.ai_content)"></div>
                      </div>
                    </div>
                    <div v-if="task.evaluation">
                      <p class="text-xs font-medium text-gray-500 mb-1">📊 成果评判（存档）
                        <span v-if="task.eval_score != null" class="text-indigo-600">{{ task.eval_score }}分</span>
                      </p>
                      <div class="bg-white rounded p-3 text-sm text-gray-700 border border-gray-100">
                        <div class="prose prose-sm" v-html="renderMd(task.evaluation)"></div>
                      </div>
                    </div>
                    <div v-if="task.quiz_evaluation">
                      <p class="text-xs font-medium text-gray-500 mb-1">🎯 练习评判（存档）
                        <span v-if="task.quiz_score != null" class="text-purple-600">{{ task.quiz_score }}分</span>
                      </p>
                      <div class="bg-white rounded p-3 text-sm text-gray-700 border border-gray-100">
                        <div class="prose prose-sm" v-html="renderMd(task.quiz_evaluation)"></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 番茄钟 -->
      <div class="card max-w-sm">
        <h3 class="font-semibold text-gray-700 mb-4">🍅 番茄钟</h3>
        <div class="text-center">
          <p class="text-5xl font-mono font-bold text-gray-800 mb-4">{{ formatTime(pomodoroTime) }}</p>
          <p class="text-sm text-gray-500 mb-4">{{ isBreak ? '休息时间 ☕' : '专注学习 📚' }}</p>
          <div class="flex justify-center gap-3">
            <el-button @click="togglePomodoro" :type="running ? 'warning' : 'primary'">
              {{ running ? '暂停' : '开始' }}
            </el-button>
            <el-button @click="resetPomodoro">重置</el-button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, reactive } from 'vue'
import { renderLatexOnly } from '@/utils/markdown'
import {
  planApi,
  createTodayGenerateStream,
  createTaskContentStream,
  createSubmitStream,
  createTaskQuizStream,
  createSubmitQuizStream,
} from '@/api/plan'
import { ElMessage } from 'element-plus'
import { renderMessage } from '@/utils/markdown'

function renderMd(content: string) {
  return content ? renderMessage(content) : ''
}

const subjects = ['数学', '物理', '化学', '生物', '语文', '英语', '历史', '地理', '政治']
const plan = ref<any>(null)
const todayTasks = ref<any[]>([])
const showCreate = ref(false)
const generating = ref(false)
const createForm = ref({ subjects: [] as string[], exam_date: '', daily_hours: 3, weak_subjects: [] as string[] })

// 标签页
const activeTab = ref<'today' | 'all'>('today')
// 学科过滤
const filterSubject = ref('')

// 任务展开状态（今日面板）
const expandedTaskId = ref<number | null>(null)
// 存档查看展开状态（计划档案面板）
const archiveExpandedId = ref<number | null>(null)
// 当前激活面板 task.id -> 'ai_content' | 'quiz' | 'submit'
const activePanel = reactive<Record<number, string>>({})

// 面板配置
const taskPanels = [
  { key: 'ai_content', label: '📖 AI 学习内容' },
  { key: 'submit', label: '📤 提交成果' },
  { key: 'quiz', label: '🎯 练习题' },
]

// 每日内容批量生成状态
const generatingTodayContent = ref(false)
const todayGenerateProgress = ref<{ current: number; total: number; task_id: number; subject: string; topic: string } | null>(null)

// AI 生成内容状态（单任务重新生成）
const generatingContent = reactive<Record<number, boolean>>({})
const streamingContent = reactive<Record<number, string>>({})

// 提交评判状态
const submitting = reactive<Record<number, boolean>>({})
const streamingEval = reactive<Record<number, string>>({})
const submissionText = reactive<Record<number, string>>({})
const submissionFile = reactive<Record<number, File | null>>({})

// 练习题状态
const generatingQuiz = reactive<Record<number, boolean>>({})
const streamingQuiz = reactive<Record<number, string>>({})
const parsedQuiz = reactive<Record<number, any[]>>({})
const quizAnswers = reactive<Record<number, Record<string, string>>>({})
const submittingQuiz = reactive<Record<number, boolean>>({})
const streamingQuizEval = reactive<Record<number, string>>({})

const todayDone = computed(() => todayTasks.value.filter(t => t.is_done).length)
const todayTotal = computed(() => todayTasks.value.length)
const daysLeft = computed(() => {
  if (!plan.value?.end_date) return 0
  const diff = new Date(plan.value.end_date).getTime() - Date.now()
  return Math.max(0, Math.ceil(diff / 86400000))
})

// 今天日期字符串
const todayStr = computed(() => new Date().toISOString().slice(0, 10))

// 所有日期（按序）
const allDateKeys = computed(() => {
  if (!plan.value?.tasks_by_date) return []
  return Object.keys(plan.value.tasks_by_date).sort()
})

// 计划中涉及的所有学科
const allSubjectsInPlan = computed(() => {
  const set = new Set<string>()
  allDateKeys.value.forEach(dk => {
    const tasks = plan.value.tasks_by_date[dk] || []
    tasks.forEach((t: any) => set.add(t.subject))
  })
  return Array.from(set).sort()
})

// 过滤后的日期列表
const filteredDateKeys = computed(() => {
  if (!filterSubject.value) return allDateKeys.value
  return allDateKeys.value.filter(dk =>
    (plan.value.tasks_by_date[dk] || []).some((t: any) => t.subject === filterSubject.value)
  )
})

// 获取某日期过滤后的任务
function getFilteredTasksForDate(dateKey: string): any[] {
  const tasks = plan.value?.tasks_by_date?.[dateKey] || []
  if (!filterSubject.value) return tasks
  return tasks.filter((t: any) => t.subject === filterSubject.value)
}

function taskTypeLabel(type: string) {
  return ({ study: '学习', practice: '练习', review: '复习' } as any)[type] || type
}
function formatTime(s: number) {
  return `${Math.floor(s / 60).toString().padStart(2, '0')}:${(s % 60).toString().padStart(2, '0')}`
}
function formatDateLabel(dateKey: string) {
  const d = new Date(dateKey + 'T00:00:00')
  const month = d.getMonth() + 1
  const day = d.getDate()
  const weekDays = ['日', '一', '二', '三', '四', '五', '六']
  const weekDay = weekDays[d.getDay()]
  return `${month}月${day}日（周${weekDay}）`
}

function toggleExpand(taskId: number) {
  expandedTaskId.value = expandedTaskId.value === taskId ? null : taskId
  if (expandedTaskId.value === taskId && !activePanel[taskId]) {
    activePanel[taskId] = 'ai_content'
  }
}

function toggleArchiveExpand(taskId: number) {
  archiveExpandedId.value = archiveExpandedId.value === taskId ? null : taskId
}

// 番茄钟
const FOCUS = 25 * 60, BREAK = 5 * 60
const pomodoroTime = ref(FOCUS)
const running = ref(false)
const isBreak = ref(false)
let timer: any

function togglePomodoro() {
  running.value = !running.value
  if (running.value) {
    timer = setInterval(() => {
      if (pomodoroTime.value > 0) {
        pomodoroTime.value--
      } else {
        isBreak.value = !isBreak.value
        pomodoroTime.value = isBreak.value ? BREAK : FOCUS
        ElMessage.success(isBreak.value ? '专注时间结束，休息一下！' : '休息结束，继续学习！')
      }
    }, 1000)
  } else {
    clearInterval(timer)
  }
}

function resetPomodoro() {
  running.value = false
  isBreak.value = false
  pomodoroTime.value = FOCUS
  clearInterval(timer)
}

/** 加载计划数据 */
async function loadPlan() {
  try {
    const res: any = await planApi.getCurrent()
    plan.value = res.data
    if (plan.value) {
      const todayRes: any = await planApi.getToday()
      todayTasks.value = todayRes.data || []
      const needsGenerate: boolean = todayRes.needs_generate ?? false

      // 恢复已有练习题的解析状态
      for (const task of todayTasks.value) {
        if (task.quiz_data && !task.quiz_evaluation) {
          tryParseQuiz(task.id, task.quiz_data)
        }
      }

      // 如果今日任务都没有内容，触发批量生成（每日第一次登录时）
      if (needsGenerate) {
        triggerTodayGenerate()
      }
    }
  } catch {}
}

/** 触发今日内容批量生成（每天第一次登录时调用） */
function triggerTodayGenerate() {
  const token = localStorage.getItem('token') || ''
  generatingTodayContent.value = true
  todayGenerateProgress.value = null

  const stop = createTodayGenerateStream(
    token,
    (progress) => {
      todayGenerateProgress.value = progress
    },
    (taskId, delta) => {
      streamingContent[taskId] = (streamingContent[taskId] || '') + delta
    },
    async (taskId) => {
      // 单个任务生成完成，刷新任务数据
      streamingContent[taskId] = ''
      try {
        const res: any = await planApi.getTaskDetail(taskId)
        const updated = res.data
        const idx = todayTasks.value.findIndex(t => t.id === taskId)
        if (idx !== -1) {
          Object.assign(todayTasks.value[idx], updated)
        }
      } catch {}
    },
    async (_total) => {
      // 全部生成完成
      generatingTodayContent.value = false
      todayGenerateProgress.value = null
      ElMessage.success('今日学习内容已全部准备好！')
      // 重新加载今日任务
      try {
        const todayRes: any = await planApi.getToday()
        todayTasks.value = todayRes.data || []
        for (const task of todayTasks.value) {
          if (task.quiz_data && !task.quiz_evaluation) {
            tryParseQuiz(task.id, task.quiz_data)
          }
        }
      } catch {}
    },
    (taskId, msg) => {
      if (taskId !== null) {
        streamingContent[taskId] = ''
      } else {
        generatingTodayContent.value = false
        // 如果是"今日不在计划范围"或"今日无任务"等正常情况，静默处理
        if (!msg.includes('不在学习计划') && !msg.includes('无学习任务')) {
          ElMessage.error('生成今日内容失败：' + msg)
        }
      }
    },
  )
  void stop
}

async function generatePlan() {
  if (createForm.value.subjects.length === 0) return ElMessage.warning('请选择备考学科')
  if (!createForm.value.exam_date) return ElMessage.warning('请选择考试日期')
  // 检查考试日期是否至少在7天后
  const examDate = new Date(createForm.value.exam_date)
  const minDate = new Date()
  minDate.setDate(minDate.getDate() + 7)
  if (examDate < minDate) {
    return ElMessage.warning('考试日期建议至少在7天后，否则可能无法生成足够的学习任务')
  }
  generating.value = true
  try {
    const res: any = await planApi.generate(createForm.value)
    plan.value = res.data
    showCreate.value = false
    // 计划生成后重新加载，并触发今日内容生成
    await loadPlan()
    activeTab.value = 'today'
    ElMessage.success('学习计划已生成！正在为今日准备学习内容...')
  } catch (err: any) {
    const detail = err?.response?.data?.detail || err?.message || '生成失败'
    ElMessage.error(detail)
  } finally {
    generating.value = false
  }
}

async function toggleTask(task: any) {
  try {
    await planApi.markTaskDone(task.id, !task.is_done)
    task.is_done = !task.is_done
    if (!task.is_done) task.completion_mode = null
  } catch (err: any) {
    const detail = err?.response?.data?.detail || '操作失败'
    ElMessage.error(detail)
  }
}

/** AI 重新生成单个任务学习内容 */
function startGenerateContent(task: any) {
  const token = localStorage.getItem('token') || ''
  generatingContent[task.id] = true
  streamingContent[task.id] = ''
  task.ai_content = null

  const stop = createTaskContentStream(
    task.id,
    token,
    (delta) => {
      streamingContent[task.id] = (streamingContent[task.id] || '') + delta
    },
    async () => {
      generatingContent[task.id] = false
      try {
        const res: any = await planApi.getTaskDetail(task.id)
        const updated = res.data
        Object.assign(task, updated)
        streamingContent[task.id] = ''
      } catch {}
    },
    (err) => {
      generatingContent[task.id] = false
      ElMessage.error('生成失败：' + err)
    },
  )
  void stop
}

/** 标记"已阅读AI内容完成" */
async function markDoneByAI(task: any) {
  try {
    await planApi.markTaskDone(task.id, true)
    task.is_done = true
    task.completion_mode = 'ai_content'
    ElMessage.success('已标记为完成！')
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '操作失败')
  }
}

/** 提交学习成果并AI评判 */
function startSubmit(task: any) {
  const token = localStorage.getItem('token') || ''
  const text = submissionText[task.id] || ''
  const file = submissionFile[task.id] || null

  if (!text && !file) {
    ElMessage.warning('请填写学习成果说明或上传图片')
    return
  }

  submitting[task.id] = true
  streamingEval[task.id] = ''

  const stop = createSubmitStream(
    task.id,
    token,
    text,
    file,
    (delta) => {
      streamingEval[task.id] = (streamingEval[task.id] || '') + delta
    },
    async (score, passed) => {
      submitting[task.id] = false
      if (passed) {
        ElMessage.success(`AI 评判通过！得分：${score} 分，任务已自动完成 ✅`)
      } else {
        ElMessage.warning(`AI 评判得分：${score} 分，尚未达到60分标准，请继续努力！`)
      }
      try {
        const res: any = await planApi.getTaskDetail(task.id)
        Object.assign(task, res.data)
        streamingEval[task.id] = ''
      } catch {}
    },
    (err) => {
      submitting[task.id] = false
      ElMessage.error('评判失败：' + err)
    },
  )
  void stop
}

/** 重置提交 */
function resetSubmission(task: any) {
  task.evaluation = null
  task.eval_score = null
  submissionText[task.id] = ''
  submissionFile[task.id] = null
  streamingEval[task.id] = ''
}

// ===== 练习题相关 =====

/** 尝试解析练习题 JSON */
function tryParseQuiz(taskId: number, raw: string) {
  try {
    let cleaned = raw.trim()
    if (cleaned.startsWith('```')) {
      cleaned = cleaned.replace(/^```[a-z]*\n?/i, '').replace(/\n?```$/, '').trim()
    }
    const data = JSON.parse(cleaned)
    parsedQuiz[taskId] = Array.isArray(data) ? data : []
    if (!quizAnswers[taskId]) quizAnswers[taskId] = {}
  } catch {
    parsedQuiz[taskId] = []
  }
}

/** 生成练习题 */
function startGenerateQuiz(task: any) {
  const token = localStorage.getItem('token') || ''
  generatingQuiz[task.id] = true
  streamingQuiz[task.id] = ''
  parsedQuiz[task.id] = []
  quizAnswers[task.id] = {}

  const stop = createTaskQuizStream(
    task.id,
    token,
    (delta) => {
      streamingQuiz[task.id] = (streamingQuiz[task.id] || '') + delta
    },
    async () => {
      generatingQuiz[task.id] = false
      streamingQuiz[task.id] = ''
      try {
        const res: any = await planApi.getTaskDetail(task.id)
        Object.assign(task, res.data)
        if (task.quiz_data) {
          tryParseQuiz(task.id, task.quiz_data)
        }
      } catch {}
    },
    (err) => {
      generatingQuiz[task.id] = false
      ElMessage.error('生成练习题失败：' + err)
    },
  )
  void stop
}

/** 设置练习题答案 */
function setQuizAnswer(taskId: number, qid: string, value: string) {
  if (!quizAnswers[taskId]) quizAnswers[taskId] = {}
  quizAnswers[taskId][qid] = value
}

/** 检查是否所有题目都已作答 */
function hasAllAnswers(taskId: number): boolean {
  const qs = parsedQuiz[taskId]
  if (!qs || qs.length === 0) return false
  const ans = quizAnswers[taskId] || {}
  return qs.every((q: any) => {
    const val = ans[String(q.id)]
    return val !== undefined && val !== ''
  })
}

/** 提交练习题答案并AI评判 */
function startSubmitQuiz(task: any) {
  const token = localStorage.getItem('token') || ''
  const answers = quizAnswers[task.id] || {}

  submittingQuiz[task.id] = true
  streamingQuizEval[task.id] = ''

  const stop = createSubmitQuizStream(
    task.id,
    token,
    answers,
    (delta) => {
      streamingQuizEval[task.id] = (streamingQuizEval[task.id] || '') + delta
    },
    async (score, passed) => {
      submittingQuiz[task.id] = false
      if (passed) {
        ElMessage.success(`练习通过！得分：${score} 分，任务已自动完成 🎯`)
      } else {
        ElMessage.warning(`练习得分：${score} 分，未达到60分，请查看解析后继续加油！`)
      }
      try {
        const res: any = await planApi.getTaskDetail(task.id)
        Object.assign(task, res.data)
        streamingQuizEval[task.id] = ''
      } catch {}
    },
    (err) => {
      submittingQuiz[task.id] = false
      ElMessage.error('评判失败：' + err)
    },
  )
  void stop
}

/** 重置练习题，允许重新练习 */
function resetQuiz(task: any) {
  task.quiz_data = null
  task.quiz_evaluation = null
  task.quiz_score = null
  task.quiz_submission = null
  parsedQuiz[task.id] = []
  quizAnswers[task.id] = {}
  streamingQuizEval[task.id] = ''
  streamingQuiz[task.id] = ''
}

onMounted(loadPlan)
onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.prose :deep(h2) { font-size: 1rem; font-weight: 600; margin: 0.75rem 0 0.4rem; color: #1e293b; }
.prose :deep(h3) { font-size: 0.9rem; font-weight: 600; margin: 0.5rem 0 0.3rem; color: #334155; }
.prose :deep(p) { margin: 0.3rem 0; line-height: 1.6; }
.prose :deep(ul), .prose :deep(ol) { padding-left: 1.2rem; margin: 0.3rem 0; }
.prose :deep(li) { margin: 0.15rem 0; }
.prose :deep(strong) { color: #1e40af; }
.prose :deep(code) { background: #f1f5f9; padding: 0.1em 0.3em; border-radius: 3px; font-size: 0.85em; }
.prose :deep(pre) { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 0.75rem; overflow-x: auto; }
.prose :deep(blockquote) { border-left: 3px solid #6366f1; padding-left: 0.75rem; color: #475569; }
</style>
