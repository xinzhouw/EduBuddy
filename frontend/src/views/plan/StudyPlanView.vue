<template>
  <div class="space-y-6">
    <!-- Show create when no plan -->
    <div v-if="!plan && !showCreate" class="text-center py-16">
      <span class="text-5xl">📅</span>
      <p class="mt-4 text-lg text-gray-600">{{ $t('study_plan.no_plan') }}</p>
      <el-button type="primary" class="mt-4" @click="showCreate = true">{{ $t('study_plan.create_btn') }}</el-button>
    </div>

    <!-- Create plan form -->
    <div v-if="showCreate" class="card max-w-2xl mx-auto space-y-4">
      <h3 class="font-bold text-gray-800">📅 {{ $t('study_plan.create_title') }}</h3>
      <p class="text-sm text-gray-500">{{ $t('study_plan.create_hint') }}</p>
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-600 mb-1">{{ $t('study_plan.subjects_label') }}</label>
          <el-checkbox-group v-model="createForm.subjects">
            <el-checkbox v-for="s in subjects" :key="s" :value="s">{{ s }}</el-checkbox>
          </el-checkbox-group>
        </div>
        <div class="space-y-3">
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">{{ $t('study_plan.exam_date_label') }}</label>
            <el-date-picker v-model="createForm.exam_date" type="date" value-format="YYYY-MM-DD" class="w-full" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">{{ $t('study_plan.daily_hours_label') }}</label>
            <el-input-number v-model="createForm.daily_hours" :min="0.5" :max="12" :step="0.5" />
          </div>
        </div>
      </div>
      <div class="flex gap-3">
        <el-button type="primary" @click="generatePlan" :loading="generating">{{ $t('study_plan.generate_btn') }}</el-button>
        <el-button @click="showCreate = false">{{ $t('common.cancel') }}</el-button>
      </div>
    </div>

    <!-- Plan exists -->
    <template v-if="plan && !showCreate">
      <!-- Overview -->
      <div class="card">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-500">{{ $t('study_plan.countdown_label') }}</p>
            <p class="text-2xl font-bold text-gray-800">{{ $t('study_plan.days_left', { days: daysLeft }) }}</p>
          </div>
          <div class="text-right">
            <p class="text-sm text-gray-500">{{ $t('study_plan.today_completed') }}</p>
            <p class="text-2xl font-bold text-green-600">{{ todayDone }}/{{ todayTotal }}</p>
          </div>
          <el-button size="small" @click="showCreate = true">⚙ {{ $t('study_plan.regenerate_btn') }}</el-button>
        </div>
        <div class="mt-3 w-full bg-gray-200 rounded-full h-2">
          <div class="bg-green-500 h-2 rounded-full transition-all"
            :style="`width: ${todayTotal > 0 ? (todayDone / todayTotal) * 100 : 0}%`"></div>
        </div>
      </div>

      <!-- Daily content generation progress (shown on first login of the day) -->
      <div v-if="generatingTodayContent" class="card border-indigo-200 bg-indigo-50">
        <div class="flex items-center gap-3">
          <div class="animate-spin text-2xl">⏳</div>
          <div class="flex-1">
            <p class="font-medium text-indigo-700">{{ $t('study_plan.generating_content') }}</p>
            <p v-if="todayGenerateProgress" class="text-sm text-indigo-600 mt-1">
              （{{ todayGenerateProgress.current }}/{{ todayGenerateProgress.total }}）
              {{ $t('study_plan.generating_subject') }}{{ todayGenerateProgress.subject }} · {{ todayGenerateProgress.topic }}
            </p>
            <div class="mt-2 w-full bg-indigo-200 rounded-full h-1.5">
              <div class="bg-indigo-500 h-1.5 rounded-full transition-all"
                :style="`width: ${todayGenerateProgress ? (todayGenerateProgress.current / todayGenerateProgress.total) * 100 : 0}%`"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Tabs: Today's plan / Plan archive -->
      <div class="card">
        <div class="flex border-b border-gray-200 mb-4 gap-1">
          <button
            @click="activeTab = 'today'"
            class="px-4 py-2 text-sm font-medium rounded-t-lg border-b-2 transition-colors"
            :class="activeTab === 'today'
              ? 'border-indigo-500 text-indigo-600 bg-indigo-50'
              : 'border-transparent text-gray-500 hover:text-gray-700'">
            📋 {{ $t('study_plan.today_tab') }}
          </button>
          <button
            @click="activeTab = 'all'"
            class="px-4 py-2 text-sm font-medium rounded-t-lg border-b-2 transition-colors"
            :class="activeTab === 'all'
              ? 'border-indigo-500 text-indigo-600 bg-indigo-50'
              : 'border-transparent text-gray-500 hover:text-gray-700'">
            🗓 {{ $t('study_plan.archive_tab') }}
            <span class="ml-1 text-xs text-gray-400">{{ $t('study_plan.archive_readonly') }}</span>
          </button>
        </div>

        <!-- Today's study panel (interactive) -->
        <div v-if="activeTab === 'today'">
          <div v-if="todayTasks.length === 0 && !generatingTodayContent" class="text-center py-4 text-gray-400 text-sm">
            {{ $t('study_plan.no_today_tasks') }}
          </div>
          <div v-else-if="generatingTodayContent && todayTasks.length === 0" class="text-center py-4 text-gray-400 text-sm">
            {{ $t('study_plan.preparing_content') }}
          </div>
          <div class="space-y-3">
            <div v-for="task in todayTasks" :key="task.id"
              class="rounded-lg border transition-colors overflow-hidden"
              :class="task.is_done ? 'border-green-200' : 'border-gray-200'">
              <!-- Task header -->
              <div class="flex items-center gap-3 p-3"
                :class="task.is_done ? 'bg-green-50' : 'bg-gray-50'">
                <input type="checkbox" :checked="task.is_done" @change="toggleTask(task)"
                  class="w-4 h-4 rounded border-gray-300 text-green-500 cursor-pointer" />
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-gray-700">{{ task.subject }} · {{ task.topic }}</p>
                  <p class="text-xs text-gray-500">{{ task.duration_minutes }}{{ $t('study_plan.task_minutes') }} · {{ taskTypeLabel(task.task_type) }}
                    <span v-if="task.eval_score != null"
                      class="ml-2 text-indigo-600 font-medium">{{ $t('study_plan.eval_score') }}{{ $t('study_plan.score_pts_short', { n: task.eval_score }) }}</span>
                    <span v-if="task.quiz_score != null"
                      class="ml-2 text-purple-600 font-medium">{{ $t('study_plan.quiz_score') }}{{ $t('study_plan.score_pts_short', { n: task.quiz_score }) }}</span>
                  </p>
                </div>
                <button @click="toggleExpand(task.id)"
                  class="text-xs text-gray-500 hover:text-indigo-600 px-2 py-1 rounded border border-gray-200 hover:border-indigo-300 transition-colors">
                  {{ expandedTaskId === task.id ? $t('study_plan.collapse') + ' ▲' : $t('study_plan.expand') + ' ▼' }}
                </button>
              </div>

              <!-- Expanded content area (interactive today) -->
              <div v-if="expandedTaskId === task.id" class="border-t border-gray-100 bg-white">
                <!-- Panel tabs -->
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

                <!-- AI study content panel -->
                <div v-if="activePanel[task.id] === 'ai_content'" class="p-4 space-y-3">
                  <!-- Batch generating in progress -->
                  <div v-if="generatingTodayContent && !task.ai_content && !streamingContent[task.id]"
                    class="bg-indigo-50 rounded p-3 text-xs text-indigo-600">
                    ⏳ {{ $t('study_plan.generating_wait') }}
                  </div>
                  <!-- Streaming generation preview -->
                  <div v-else-if="streamingContent[task.id]"
                    class="bg-gray-50 rounded p-3 text-xs text-gray-700">
                    <div class="prose prose-sm" v-html="renderMd(streamingContent[task.id])"></div>
                  </div>
                  <!-- Display generated content -->
                  <div v-else-if="task.ai_content"
                    class="bg-blue-50 rounded p-3 text-sm text-gray-700">
                    <div class="prose prose-sm" v-html="renderMd(task.ai_content)"></div>
                  </div>
                  <!-- Not yet generated -->
                  <div v-else class="text-xs text-gray-400">{{ $t('study_plan.task_not_generated') }}</div>

                  <div class="flex gap-2 flex-wrap">
                    <button @click="startGenerateContent(task)"
                      class="text-xs px-3 py-1.5 rounded border border-indigo-300 text-indigo-600 hover:bg-indigo-50 transition-colors"
                      :disabled="generatingContent[task.id] || generatingTodayContent">
                      {{ generatingContent[task.id] ? ('⏳ ' + $t('study_plan.generating_short')) : ('🤖 ' + $t('study_plan.regenerate_content')) }}
                    </button>
                    <button v-if="!task.is_done && task.ai_content" @click="markDoneByAI(task)"
                      class="text-xs px-3 py-1.5 rounded border border-green-300 text-green-600 hover:bg-green-50 transition-colors">
                      ✅ {{ $t('study_plan.mark_done') }}
                    </button>
                  </div>
                </div>

                <!-- Submit results panel -->
                <div v-if="activePanel[task.id] === 'submit'" class="p-4 space-y-3">
                  <!-- Evaluation result exists -->
                  <div v-if="task.evaluation && !streamingEval[task.id]">
                    <div class="bg-green-50 rounded p-3 text-sm text-gray-700">
                      <div class="prose prose-sm" v-html="renderMd(task.evaluation)"></div>
                    </div>
                    <button @click="resetSubmission(task)"
                      class="mt-2 text-xs px-3 py-1.5 rounded border border-gray-300 text-gray-600 hover:bg-gray-50">
                      🔄 {{ $t('study_plan.resubmit_result') }}
                    </button>
                  </div>
                  <!-- Evaluation streaming -->
                  <div v-else-if="streamingEval[task.id]"
                    class="bg-gray-50 rounded p-3 text-xs text-gray-700">
                    <div class="prose prose-sm" v-html="renderMd(streamingEval[task.id])"></div>
                  </div>
                  <!-- Submit form -->
                  <div v-else>
                    <p class="text-xs text-gray-500 mb-2">{{ $t('study_plan.submit_result_hint') }}</p>
                    <textarea
                      :value="submissionText[task.id] || ''"
                      @input="(e: Event) => submissionText[task.id] = (e.target as HTMLTextAreaElement).value"
                      :placeholder="$t('study_plan.result_placeholder')"
                      class="w-full border border-gray-300 rounded p-2 text-sm resize-none h-20 focus:outline-none focus:border-indigo-400"></textarea>
                    <div class="flex gap-2 mt-2 items-center">
                      <input type="file" accept="image/*"
                        @change="(e: Event) => { const f = (e.target as HTMLInputElement).files?.[0]; if(f) submissionFile[task.id] = f }"
                        class="text-xs text-gray-500 flex-1" />
                      <button @click="startSubmit(task)"
                        :disabled="submitting[task.id] || (!submissionText[task.id] && !submissionFile[task.id])"
                        class="text-xs px-3 py-1.5 rounded border border-purple-300 text-purple-600 hover:bg-purple-50 transition-colors disabled:opacity-50">
                        {{ submitting[task.id] ? ('⏳ ' + $t('study_plan.submitting_short')) : ('📤 ' + $t('study_plan.submit_result_btn')) }}
                      </button>
                    </div>
                  </div>
                </div>

                <!-- Quiz panel -->
                <div v-if="activePanel[task.id] === 'quiz'" class="p-4 space-y-3">
                  <!-- Quiz evaluation result exists -->
                  <div v-if="task.quiz_evaluation && !streamingQuizEval[task.id]">
                    <div class="bg-purple-50 rounded p-3 text-sm text-gray-700">
                      <div class="prose prose-sm" v-html="renderMd(task.quiz_evaluation)"></div>
                    </div>
                    <button @click="resetQuiz(task)"
                      class="mt-2 text-xs px-3 py-1.5 rounded border border-gray-300 text-gray-600 hover:bg-gray-50">
                      🔄 {{ $t('study_plan.practice_again') }}
                    </button>
                  </div>
                  <!-- Quiz evaluation streaming -->
                  <div v-else-if="streamingQuizEval[task.id]"
                    class="bg-gray-50 rounded p-3 text-xs text-gray-700">
                    <div class="prose prose-sm" v-html="renderMd(streamingQuizEval[task.id])"></div>
                  </div>
                  <!-- Generating quiz -->
                  <div v-else-if="generatingQuiz[task.id]"
                    class="text-xs text-gray-500">⏳ {{ $t('study_plan.gen_quiz_loading') }}</div>
                  <!-- Quiz question list -->
                  <div v-else-if="parsedQuiz[task.id] && parsedQuiz[task.id].length > 0" class="space-y-3">
                    <div v-for="q in parsedQuiz[task.id]" :key="q.id" class="border border-gray-100 rounded p-3">
                      <p class="text-sm font-medium text-gray-700 mb-2 latex-content"
                        v-html="`${q.id}. ` + renderLatexOnly(q.question)"></p>
                      <!-- Multiple choice -->
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
                      <!-- Fill-in-the-blank / short-answer -->
                      <div v-else>
                        <input type="text"
                          :value="(quizAnswers[task.id] || {})[String(q.id)] || ''"
                          @input="(e: Event) => setQuizAnswer(task.id, String(q.id), (e.target as HTMLInputElement).value)"
                          :placeholder="$t('study_plan.answer_placeholder')"
                          class="w-full border border-gray-200 rounded px-2 py-1 text-xs focus:outline-none focus:border-indigo-300" />
                      </div>
                    </div>
                    <div class="flex gap-2">
                      <button @click="startSubmitQuiz(task)"
                        :disabled="submittingQuiz[task.id] || !hasAllAnswers(task.id)"
                        class="text-xs px-3 py-1.5 rounded border border-purple-300 text-purple-600 hover:bg-purple-50 disabled:opacity-50">
                        {{ submittingQuiz[task.id] ? ('⏳ ' + $t('study_plan.submitting_short')) : ('📝 ' + $t('study_plan.submit_quiz_btn')) }}
                      </button>
                    </div>
                  </div>
                  <!-- Not yet generated -->
                  <div v-else>
                    <p class="text-xs text-gray-400 mb-2">{{ $t('study_plan.no_quiz') }}</p>
                    <button @click="startGenerateQuiz(task)"
                      class="text-xs px-3 py-1.5 rounded border border-purple-300 text-purple-600 hover:bg-purple-50">
                      🎯 {{ $t('study_plan.gen_quiz_btn') }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Plan archive panel (read-only) -->
        <div v-if="activeTab === 'all'">
          <div class="mb-3 p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-700">
            📚 {{ $t('study_plan.archive_readonly_hint') }}
          </div>

          <!-- Subject filter -->
          <div v-if="allSubjectsInPlan.length > 0" class="mb-4 flex flex-wrap gap-2 items-center">
            <span class="text-xs text-gray-500 mr-1">{{ $t('study_plan.filter_by_subject') }}</span>
            <button
              @click="filterSubject = ''"
              class="px-2 py-1 rounded-full text-xs border transition-colors"
              :class="filterSubject === '' ? 'bg-indigo-500 text-white border-indigo-500' : 'border-gray-300 text-gray-600 hover:border-indigo-300'">
              {{ $t('study_plan.all_subjects') }}
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
            {{ $t('study_plan.no_tasks') }}
          </div>

          <div class="space-y-4">
            <div v-for="dateKey in filteredDateKeys" :key="dateKey">
              <!-- Date header -->
              <div class="flex items-center gap-2 mb-2 sticky top-0 bg-white py-1 z-10">
                <span class="text-sm font-semibold text-gray-700">{{ formatDateLabel(dateKey) }}</span>
                <span v-if="dateKey === todayStr"
                  class="text-xs bg-indigo-500 text-white px-2 py-0.5 rounded-full">{{ $t('study_plan.today_badge') }}</span>
                <span v-else-if="dateKey < todayStr"
                  class="text-xs bg-gray-300 text-gray-600 px-2 py-0.5 rounded-full">{{ $t('study_plan.expired_badge') }}</span>
                <span v-else
                  class="text-xs bg-blue-100 text-blue-600 px-2 py-0.5 rounded-full">{{ $t('study_plan.pending_badge') }}</span>
                <div class="flex-1 h-px bg-gray-200"></div>
              </div>
              <!-- Daily task list (read-only) -->
              <div class="space-y-2 pl-2">
                <div v-for="task in getFilteredTasksForDate(dateKey)" :key="task.id"
                  class="rounded-lg border overflow-hidden"
                  :class="task.is_done ? 'border-green-200' : (dateKey < todayStr ? 'border-orange-100' : 'border-gray-200')">
                  <!-- Read-only task header -->
                  <div class="flex items-center gap-3 p-3"
                    :class="task.is_done ? 'bg-green-50' : (dateKey < todayStr ? 'bg-orange-50' : 'bg-gray-50')">
                    <span class="text-base">{{ task.is_done ? '✅' : (dateKey < todayStr ? '⚠️' : '📝') }}</span>
                    <div class="flex-1 min-w-0">
                      <p class="text-sm font-medium text-gray-700">{{ task.subject }} · {{ task.topic }}</p>
                      <p class="text-xs text-gray-500">{{ task.duration_minutes }}{{ $t('study_plan.task_minutes') }} · {{ taskTypeLabel(task.task_type) }}
                        <span v-if="task.eval_score != null" class="ml-2 text-indigo-600">{{ $t('study_plan.eval_score') }}{{ $t('study_plan.score_pts_short', { n: task.eval_score }) }}</span>
                        <span v-if="task.quiz_score != null" class="ml-2 text-purple-600">{{ $t('study_plan.quiz_score') }}{{ $t('study_plan.score_pts_short', { n: task.quiz_score }) }}</span>
                      </p>
                    </div>
                    <!-- Only today's tasks can be expanded; historical/future tasks show archived content -->
                    <button v-if="task.ai_content || task.evaluation || task.quiz_evaluation"
                      @click="toggleArchiveExpand(task.id)"
                      class="text-xs text-gray-500 hover:text-indigo-600 px-2 py-1 rounded border border-gray-200 hover:border-indigo-300">
                      {{ archiveExpandedId === task.id ? ($t('study_plan.collapse_archive') + ' ▲') : ($t('study_plan.view_archive') + ' ▼') }}
                    </button>
                    <span v-else-if="dateKey > todayStr" class="text-xs text-gray-400 px-2">{{ $t('study_plan.pending_gen') }}</span>
                  </div>
                  <!-- Read-only archived content -->
                  <div v-if="archiveExpandedId === task.id" class="border-t border-gray-100 bg-gray-50 p-4 space-y-3">
                    <div v-if="task.ai_content">
                      <p class="text-xs font-medium text-gray-500 mb-1">📖 {{ $t('study_plan.archive_content_label') }}</p>
                      <div class="bg-white rounded p-3 text-sm text-gray-700 border border-gray-100">
                        <div class="prose prose-sm" v-html="renderMd(task.ai_content)"></div>
                      </div>
                    </div>
                    <div v-if="task.evaluation">
                      <p class="text-xs font-medium text-gray-500 mb-1">📊 {{ $t('study_plan.archive_eval_label') }}
                        <span v-if="task.eval_score != null" class="text-indigo-600">{{ $t('study_plan.score_pts_short', { n: task.eval_score }) }}</span>
                      </p>
                      <div class="bg-white rounded p-3 text-sm text-gray-700 border border-gray-100">
                        <div class="prose prose-sm" v-html="renderMd(task.evaluation)"></div>
                      </div>
                    </div>
                    <div v-if="task.quiz_evaluation">
                      <p class="text-xs font-medium text-gray-500 mb-1">🎯 {{ $t('study_plan.archive_quiz_label') }}
                        <span v-if="task.quiz_score != null" class="text-purple-600">{{ $t('study_plan.score_pts_short', { n: task.quiz_score }) }}</span>
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

      <!-- Pomodoro timer -->
      <div class="card max-w-sm">
        <h3 class="font-semibold text-gray-700 mb-4">🍅 {{ $t('study_plan.pomodoro_title') }}</h3>
        <div class="text-center">
          <p class="text-5xl font-mono font-bold text-gray-800 mb-4">{{ formatTime(pomodoroTime) }}</p>
          <p class="text-sm text-gray-500 mb-4">{{ isBreak ? $t('study_plan.break_time') : $t('study_plan.focus_time') }}</p>
          <div class="flex justify-center gap-3">
            <el-button @click="togglePomodoro" :type="running ? 'warning' : 'primary'">
              {{ running ? $t('study_plan.timer_pause') : $t('study_plan.timer_start') }}
            </el-button>
            <el-button @click="resetPomodoro">{{ $t('study_plan.timer_reset') }}</el-button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
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

const subjectKeys = ['math', 'physics', 'chemistry', 'biology', 'chinese', 'english', 'history', 'geography', 'politics']
const subjects = computed(() => subjectKeys.map(k => t(`subjects.${k}`)))
const plan = ref<any>(null)
const todayTasks = ref<any[]>([])
const showCreate = ref(false)
const generating = ref(false)
const createForm = ref({ subjects: [] as string[], exam_date: '', daily_hours: 3, weak_subjects: [] as string[] })

// Tabs
const activeTab = ref<'today' | 'all'>('today')
// Subject filter
const filterSubject = ref('')

// Task expand state (today panel)
const expandedTaskId = ref<number | null>(null)
// Archive view expand state (plan archive panel)
const archiveExpandedId = ref<number | null>(null)
// Active panel: task.id -> 'ai_content' | 'quiz' | 'submit'
const activePanel = reactive<Record<number, string>>({})

// Panel configuration
const taskPanels = computed(() => [
  { key: 'ai_content', label: `📖 ${t('study_plan.task_ai_content')}` },
  { key: 'submit', label: `📤 ${t('study_plan.task_submit_label')}` },
  { key: 'quiz', label: `🎯 ${t('study_plan.task_quiz_label')}` },
])

// Daily content batch generation state
const generatingTodayContent = ref(false)
const todayGenerateProgress = ref<{ current: number; total: number; task_id: number; subject: string; topic: string } | null>(null)

// AI content generation state (single task regeneration)
const generatingContent = reactive<Record<number, boolean>>({})
const streamingContent = reactive<Record<number, string>>({})

// Submission evaluation state
const submitting = reactive<Record<number, boolean>>({})
const streamingEval = reactive<Record<number, string>>({})
const submissionText = reactive<Record<number, string>>({})
const submissionFile = reactive<Record<number, File | null>>({})

// Quiz state
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

// Today's date string
const todayStr = computed(() => new Date().toISOString().slice(0, 10))

// All dates (sorted)
const allDateKeys = computed(() => {
  if (!plan.value?.tasks_by_date) return []
  return Object.keys(plan.value.tasks_by_date).sort()
})

// All subjects in the plan
const allSubjectsInPlan = computed(() => {
  const set = new Set<string>()
  allDateKeys.value.forEach(dk => {
    const tasks = plan.value.tasks_by_date[dk] || []
    tasks.forEach((t: any) => set.add(t.subject))
  })
  return Array.from(set).sort()
})

// Filtered date list
const filteredDateKeys = computed(() => {
  if (!filterSubject.value) return allDateKeys.value
  return allDateKeys.value.filter(dk =>
    (plan.value.tasks_by_date[dk] || []).some((t: any) => t.subject === filterSubject.value)
  )
})

// Get filtered tasks for a date
function getFilteredTasksForDate(dateKey: string): any[] {
  const tasks = plan.value?.tasks_by_date?.[dateKey] || []
  if (!filterSubject.value) return tasks
  return tasks.filter((t: any) => t.subject === filterSubject.value)
}

function taskTypeLabel(type: string) {
  const map: Record<string, string> = {
    study: t('dashboard.study_type_study'),
    practice: t('dashboard.study_type_practice'),
    review: t('dashboard.study_type_review'),
  }
  return map[type] || type
}
function formatTime(s: number) {
  return `${Math.floor(s / 60).toString().padStart(2, '0')}:${(s % 60).toString().padStart(2, '0')}`
}
function formatDateLabel(dateKey: string) {
  const d = new Date(dateKey + 'T00:00:00')
  const month = d.getMonth() + 1
  const day = d.getDate()
  const weekday = t(`study_plan.weekday_${d.getDay()}`)
  return t('study_plan.date_label_fmt', { month, day, weekday })
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

// Pomodoro timer
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
        ElMessage.success(isBreak.value ? t('study_plan.pomodoro_focus_done') : t('study_plan.pomodoro_break_done'))
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

// Load plan data
async function loadPlan() {
  try {
    const res: any = await planApi.getCurrent()
    plan.value = res.data
    if (plan.value) {
      const todayRes: any = await planApi.getToday()
      todayTasks.value = todayRes.data || []
      const needsGenerate: boolean = todayRes.needs_generate ?? false

      // Restore parsed state for existing quizzes
      for (const task of todayTasks.value) {
        if (task.quiz_data && !task.quiz_evaluation) {
          tryParseQuiz(task.id, task.quiz_data)
        }
      }

      // If today's tasks have no content, trigger batch generation (first login of the day)
      if (needsGenerate) {
        triggerTodayGenerate()
      }
    }
  } catch {}
}

// Trigger today's content batch generation (called on first login of the day)
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
      // Single task generation done, refresh task data
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
      // All generation done
      generatingTodayContent.value = false
      todayGenerateProgress.value = null
      ElMessage.success(t('study_plan.today_content_ready'))
      // Reload today's tasks
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
        // Silently handle normal cases like "not in plan range" or "no tasks today"
        if (!msg.includes('不在学习计划') && !msg.includes('无学习任务')) { // server-side error filter
          ElMessage.error(t('study_plan.today_content_gen_failed', { detail: msg }))
        }
      }
    },
  )
  void stop
}

async function generatePlan() {
  if (createForm.value.subjects.length === 0) return ElMessage.warning(t('study_plan.select_subjects_required'))
  if (!createForm.value.exam_date) return ElMessage.warning(t('study_plan.select_exam_date_required'))
  // Check that exam date is at least 7 days away
  const examDate = new Date(createForm.value.exam_date)
  const minDate = new Date()
  minDate.setDate(minDate.getDate() + 7)
  if (examDate < minDate) {
    return ElMessage.warning(t('study_plan.exam_date_min_7_days'))
  }
  generating.value = true
  try {
    const res: any = await planApi.generate(createForm.value)
    plan.value = res.data
    showCreate.value = false
    // Reload after plan generated and trigger today's content generation
    await loadPlan()
    activeTab.value = 'today'
    ElMessage.success(t('study_plan.plan_generated'))
  } catch (err: any) {
    const detail = err?.response?.data?.detail || err?.message || t('study_plan.gen_failed')
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
    const detail = err?.response?.data?.detail || t('study_plan.operation_failed')
    ElMessage.error(detail)
  }
}

// AI regenerate single task content
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
      ElMessage.error(t('study_plan.content_gen_failed_detail', { detail: err }))
    },
  )
  void stop
}

// Mark "read AI content as done"
async function markDoneByAI(task: any) {
  try {
    await planApi.markTaskDone(task.id, true)
    task.is_done = true
    task.completion_mode = 'ai_content'
    ElMessage.success(t('study_plan.marked_done'))
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || t('study_plan.operation_failed'))
  }
}

// Submit study results for AI evaluation
function startSubmit(task: any) {
  const token = localStorage.getItem('token') || ''
  const text = submissionText[task.id] || ''
  const file = submissionFile[task.id] || null

  if (!text && !file) {
    ElMessage.warning(t('study_plan.submit_empty_warning'))
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
        ElMessage.success(t('study_plan.ai_pass_msg', { score }))
      } else {
        ElMessage.warning(t('study_plan.ai_fail_msg', { score }))
      }
      try {
        const res: any = await planApi.getTaskDetail(task.id)
        Object.assign(task, res.data)
        streamingEval[task.id] = ''
      } catch {}
    },
    (err) => {
      submitting[task.id] = false
      ElMessage.error(t('study_plan.eval_failed_detail', { detail: err }))
    },
  )
  void stop
}

// Reset submission
function resetSubmission(task: any) {
  task.evaluation = null
  task.eval_score = null
  submissionText[task.id] = ''
  submissionFile[task.id] = null
  streamingEval[task.id] = ''
}

// ===== Quiz-related =====

// Try to parse quiz JSON
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

// Generate quiz
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
      ElMessage.error(t('study_plan.quiz_gen_failed_detail', { detail: err }))
    },
  )
  void stop
}

// Set quiz answer
function setQuizAnswer(taskId: number, qid: string, value: string) {
  if (!quizAnswers[taskId]) quizAnswers[taskId] = {}
  quizAnswers[taskId][qid] = value
}

// Check if all questions have been answered
function hasAllAnswers(taskId: number): boolean {
  const qs = parsedQuiz[taskId]
  if (!qs || qs.length === 0) return false
  const ans = quizAnswers[taskId] || {}
  return qs.every((q: any) => {
    const val = ans[String(q.id)]
    return val !== undefined && val !== ''
  })
}

// Submit quiz answers for AI evaluation
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
        ElMessage.success(t('study_plan.quiz_pass_msg', { score }))
      } else {
        ElMessage.warning(t('study_plan.quiz_fail_msg', { score }))
      }
      try {
        const res: any = await planApi.getTaskDetail(task.id)
        Object.assign(task, res.data)
        streamingQuizEval[task.id] = ''
      } catch {}
    },
    (err) => {
      submittingQuiz[task.id] = false
      ElMessage.error(t('study_plan.eval_failed_detail', { detail: err }))
    },
  )
  void stop
}

// Reset quiz, allow re-practice
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
