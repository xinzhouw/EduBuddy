<template>
  <div class="space-y-4">
    <!-- Filter bar -->
    <div class="flex items-center gap-3 flex-wrap">
      <el-select v-model="filter.subject" :placeholder="$t('wrong_book.filter_subject')" clearable size="small" style="width:110px" @change="loadItems">
        <el-option v-for="s in subjects" :key="s" :label="s" :value="s" />
      </el-select>
      <el-select v-model="filter.mastery" :placeholder="$t('wrong_book.filter_mastery')" clearable size="small" style="width:110px" @change="loadItems">
        <el-option :label="$t('wrong_book.mastery_unmastered')" value="unmastered" />
        <el-option :label="$t('wrong_book.mastery_fuzzy')" value="fuzzy" />
        <el-option :label="$t('wrong_book.mastery_mastered')" value="mastered" />
      </el-select>
      <button @click="filter.due_review = !filter.due_review; loadItems()"
        class="px-3 py-1.5 rounded-full text-sm transition-colors"
        :class="filter.due_review ? 'bg-amber-100 text-amber-700' : 'bg-gray-100 text-gray-600'">
        ⏰ {{ $t('wrong_book.today_due') }} {{ todayDue }}
      </button>
      <div class="ml-auto">
        <el-button type="primary" @click="showAddDialog = true">{{ $t('wrong_book.add_manually') }}</el-button>
      </div>
    </div>

    <!-- List -->
    <div v-if="items.length === 0" class="text-center py-16 text-gray-400">
      <span class="text-5xl">✅</span>
      <p class="mt-4 text-lg">{{ $t('wrong_book.empty_hint') }}</p>
      <RouterLink to="/quiz" class="text-blue-500 text-sm">{{ $t('wrong_book.go_practice') }}</RouterLink>
    </div>

    <div v-else class="space-y-3">
      <div v-for="item in items" :key="item.id" class="card">
        <div class="flex items-start justify-between gap-3">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-2">
              <span class="px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700">{{ item.subject }}</span>
              <span :class="masteryClass(item.mastery)" class="text-xs px-2 py-0.5 rounded-full font-medium">
                {{ masteryLabel(item.mastery) }}
              </span>
              <span class="text-xs text-gray-400">{{ item.review_count }}{{ $t('wrong_book.review_count_unit') }}</span>
            </div>
            <div class="text-sm text-gray-700 line-clamp-2 katex-preview" v-html="renderLatexOnly(item.question)"></div>
            <div class="flex flex-wrap gap-1 mt-2">
              <span v-for="tag in parseTags(item.tags)" :key="tag" class="px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded text-xs">{{ tag }}</span>
            </div>
          </div>
          <div class="flex gap-2 shrink-0">
            <el-button size="small" @click="router.push(`/wrong-book/${item.id}`)">{{ $t('wrong_book.ai_explain_btn') }}</el-button>
            <el-button size="small" type="danger" plain @click="deleteItem(item.id)">{{ $t('wrong_book.delete_btn') }}</el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- Add manually dialog -->
    <el-dialog v-model="showAddDialog" :title="$t('wrong_book.add_dialog_title')" width="500px">
      <el-form :model="addForm" label-width="80px">
        <el-form-item :label="$t('wrong_book.question_label')"><el-input v-model="addForm.question" type="textarea" :rows="3" /></el-form-item>
        <el-form-item :label="$t('wrong_book.correct_answer_label')"><el-input v-model="addForm.correct_answer" type="textarea" :rows="2" /></el-form-item>
        <el-form-item :label="$t('wrong_book.subject_label')">
          <el-select v-model="addForm.subject" class="w-full">
            <el-option v-for="s in subjects" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="addItem">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { wrongBookApi } from '@/api/wrongBook'
import { ElMessage, ElMessageBox } from 'element-plus'
import { renderLatexOnly } from '@/utils/markdown'

const router = useRouter()
const { t } = useI18n()
const items = ref<any[]>([])
const todayDue = ref(0)
const showAddDialog = ref(false)

// Subject values are kept in sync with i18n keys; in zh locale they equal the Chinese API values
const subjects = computed(() => [
  t('subjects.math'), t('subjects.physics'), t('subjects.chemistry'),
  t('subjects.biology'), t('subjects.chinese'), t('subjects.english'),
  t('subjects.history'), t('subjects.geography'), t('subjects.politics'),
])

const filter = reactive({ subject: '', mastery: '', due_review: false })
const addForm = reactive({ question: '', correct_answer: '', subject: t('subjects.math'), tags: [] as string[] })

function masteryLabel(m: string) {
  return ({
    unmastered: t('wrong_book.mastery_label_unmastered'),
    fuzzy: t('wrong_book.mastery_label_fuzzy'),
    mastered: t('wrong_book.mastery_label_mastered'),
  } as Record<string, string>)[m] || m
}
function masteryClass(m: string) { return { unmastered: 'bg-red-100 text-red-700', fuzzy: 'bg-amber-100 text-amber-700', mastered: 'bg-green-100 text-green-700' }[m] || '' }
function parseTags(tagsStr: string) { try { return JSON.parse(tagsStr || '[]') } catch { return [] } }

async function loadItems() {
  const res: any = await wrongBookApi.list({
    subject: filter.subject || undefined,
    mastery: filter.mastery || undefined,
    due_review: filter.due_review || undefined,
  })
  items.value = res.data.items || []
  todayDue.value = res.data.today_due_count || 0
}

async function deleteItem(id: number) {
  await ElMessageBox.confirm(t('wrong_book.delete_confirm'), t('common.delete'), { type: 'warning' })
  await wrongBookApi.delete(id)
  ElMessage.success(t('wrong_book.delete_success'))
  loadItems()
}

async function addItem() {
  if (!addForm.question.trim() || !addForm.correct_answer.trim()) return ElMessage.warning(t('wrong_book.fill_required'))
  await wrongBookApi.create(addForm)
  ElMessage.success(t('wrong_book.add_success'))
  showAddDialog.value = false
  loadItems()
}

onMounted(loadItems)
</script>
