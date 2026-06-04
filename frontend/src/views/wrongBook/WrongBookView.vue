<template>
  <div class="space-y-4">
    <!-- 筛选栏 -->
    <div class="flex items-center gap-3 flex-wrap">
      <el-select v-model="filter.subject" placeholder="全部学科" clearable size="small" style="width:110px" @change="loadItems">
        <el-option v-for="s in subjects" :key="s" :label="s" :value="s" />
      </el-select>
      <el-select v-model="filter.mastery" placeholder="全部状态" clearable size="small" style="width:110px" @change="loadItems">
        <el-option label="未掌握" value="unmastered" />
        <el-option label="模糊" value="fuzzy" />
        <el-option label="已掌握" value="mastered" />
      </el-select>
      <button @click="filter.due_review = !filter.due_review; loadItems()"
        class="px-3 py-1.5 rounded-full text-sm transition-colors"
        :class="filter.due_review ? 'bg-amber-100 text-amber-700' : 'bg-gray-100 text-gray-600'">
        ⏰ 今日待复习 {{ todayDue }}
      </button>
      <div class="ml-auto">
        <el-button type="primary" @click="showAddDialog = true">+ 手动添加</el-button>
      </div>
    </div>

    <!-- 列表 -->
    <div v-if="items.length === 0" class="text-center py-16 text-gray-400">
      <span class="text-5xl">✅</span>
      <p class="mt-4 text-lg">暂无错题，继续练习保持！</p>
      <RouterLink to="/quiz" class="text-blue-500 text-sm">去练习 →</RouterLink>
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
              <span class="text-xs text-gray-400">{{ item.review_count }}次复习</span>
            </div>
            <div class="text-sm text-gray-700 line-clamp-2 katex-preview" v-html="renderLatexOnly(item.question)"></div>
            <div class="flex flex-wrap gap-1 mt-2">
              <span v-for="tag in parseTags(item.tags)" :key="tag" class="px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded text-xs">{{ tag }}</span>
            </div>
          </div>
          <div class="flex gap-2 shrink-0">
            <el-button size="small" @click="router.push(`/wrong-book/${item.id}`)">AI讲解</el-button>
            <el-button size="small" type="danger" plain @click="deleteItem(item.id)">删除</el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 手动添加对话框 -->
    <el-dialog v-model="showAddDialog" title="手动添加错题" width="500px">
      <el-form :model="addForm" label-width="80px">
        <el-form-item label="题目"><el-input v-model="addForm.question" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="正确答案"><el-input v-model="addForm.correct_answer" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="学科">
          <el-select v-model="addForm.subject" class="w-full">
            <el-option v-for="s in subjects" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="addItem">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { wrongBookApi } from '@/api/wrongBook'
import { ElMessage, ElMessageBox } from 'element-plus'
import { renderLatexOnly } from '@/utils/markdown'

const router = useRouter()
const items = ref<any[]>([])
const todayDue = ref(0)
const showAddDialog = ref(false)
const subjects = ['数学', '物理', '化学', '生物', '语文', '英语', '历史', '地理', '政治']
const filter = reactive({ subject: '', mastery: '', due_review: false })
const addForm = reactive({ question: '', correct_answer: '', subject: '数学', tags: [] as string[] })

function masteryLabel(m: string) { return { unmastered: '❌ 未掌握', fuzzy: '⚠️ 模糊', mastered: '✅ 已掌握' }[m] || m }
function masteryClass(m: string) { return { unmastered: 'bg-red-100 text-red-700', fuzzy: 'bg-amber-100 text-amber-700', mastered: 'bg-green-100 text-green-700' }[m] || '' }
function parseTags(t: string) { try { return JSON.parse(t || '[]') } catch { return [] } }

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
  await ElMessageBox.confirm('确认删除此错题？', '删除', { type: 'warning' })
  await wrongBookApi.delete(id)
  ElMessage.success('已删除')
  loadItems()
}

async function addItem() {
  if (!addForm.question.trim() || !addForm.correct_answer.trim()) return ElMessage.warning('请填写题目和答案')
  await wrongBookApi.create(addForm)
  ElMessage.success('添加成功')
  showAddDialog.value = false
  loadItems()
}

onMounted(loadItems)
</script>
