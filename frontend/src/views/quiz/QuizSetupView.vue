<template>
  <div class="max-w-2xl mx-auto">
    <div class="card space-y-6">
      <h2 class="text-xl font-bold text-gray-800">📚 开始练习</h2>

      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-600 mb-1">学科</label>
          <el-select v-model="form.subject" class="w-full">
            <el-option v-for="s in subjects" :key="s" :label="s" :value="s" />
          </el-select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-600 mb-1">知识点</label>
          <el-input v-model="form.topic" placeholder="如：二次函数、牛顿定律" />
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-600 mb-2">难度</label>
        <div class="grid grid-cols-4 gap-3">
          <button v-for="d in difficulties" :key="d.value"
            @click="form.difficulty = d.value"
            class="p-3 rounded-lg border-2 text-center transition-all"
            :class="form.difficulty === d.value ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'">
            <p class="text-lg">{{ d.icon }}</p>
            <p class="text-xs font-medium mt-1">{{ d.label }}</p>
          </button>
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-600 mb-2">题型</label>
        <div class="flex flex-wrap gap-2">
          <el-checkbox v-for="t in questionTypes" :key="t.value" v-model="t.checked" :label="t.label" />
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-600 mb-1">题目数量</label>
        <el-select v-model="form.count" style="width:100px">
          <el-option v-for="n in [3, 5, 10, 15]" :key="n" :label="`${n}道`" :value="n" />
        </el-select>
      </div>

      <el-button type="primary" size="large" class="w-full" :loading="loading" @click="startQuiz">
        🚀 开始练习
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { quizApi } from '@/api/quiz'
import { ElMessage } from 'element-plus'

const router = useRouter()
const loading = ref(false)
const subjects = ['数学', '物理', '化学', '生物', '语文', '英语', '历史', '地理', '政治']
const difficulties = [
  { value: 1, icon: '🌱', label: '基础' },
  { value: 2, icon: '📘', label: '中等' },
  { value: 3, icon: '🔥', label: '困难' },
  { value: 4, icon: '🏆', label: '挑战' },
]
const questionTypes = reactive([
  { value: 'single_choice', label: '单选题', checked: true },
  { value: 'fill_blank', label: '填空题', checked: true },
  { value: 'true_false', label: '判断题', checked: false },
  { value: 'subjective', label: '简答题', checked: false },
])
const form = reactive({ subject: '数学', topic: '', difficulty: 2, count: 5 })

async function startQuiz() {
  if (!form.topic.trim()) return ElMessage.warning('请输入知识点')
  const selectedTypes = questionTypes.filter(t => t.checked).map(t => t.value)
  if (selectedTypes.length === 0) return ElMessage.warning('请至少选择一种题型')

  loading.value = true
  try {
    const res: any = await quizApi.generate({
      subject: form.subject,
      topic: form.topic,
      difficulty: form.difficulty,
      question_types: selectedTypes,
      count: form.count,
    })
    // 将数据存入 sessionStorage 再跳转
    sessionStorage.setItem('quizSession', JSON.stringify(res.data))
    router.push('/quiz/session')
  } finally {
    loading.value = false
  }
}
</script>
