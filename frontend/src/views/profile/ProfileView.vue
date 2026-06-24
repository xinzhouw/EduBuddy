<template>
  <div class="max-w-3xl mx-auto space-y-6">

    <!-- 头部卡片 -->
    <div class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white shadow-lg">
      <div class="absolute -top-10 -right-10 w-48 h-48 bg-white/10 rounded-full"></div>
      <div class="absolute -bottom-8 -right-24 w-64 h-64 bg-white/5 rounded-full"></div>
      <div class="relative p-6 flex items-center gap-5">
        <div class="w-20 h-20 rounded-2xl bg-white/20 backdrop-blur-sm flex items-center justify-center text-4xl font-black shrink-0 border border-white/20">
          {{ form.nickname?.[0]?.toUpperCase() || 'U' }}
        </div>
        <div class="min-w-0">
          <h1 class="text-2xl font-bold truncate">{{ form.nickname || '同学' }}</h1>
          <p class="text-blue-100 text-sm mt-1">{{ authStore.user?.email }}</p>
          <div class="flex items-center gap-2 mt-1">
            <p class="text-blue-200 text-xs">{{ form.grade || '未设置年级' }}</p>
            <span
              class="text-xs px-2 py-0.5 rounded-full font-medium"
              :class="roleStyle(authStore.user?.role)"
            >{{ roleLabel(authStore.user?.role) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 基本信息 -->
    <div class="card">
      <div class="flex items-center gap-2 mb-5">
        <span class="w-1 h-5 bg-gradient-to-b from-blue-500 to-indigo-500 rounded-full inline-block"></span>
        <h3 class="font-bold text-gray-800">基本信息</h3>
      </div>

      <el-form :model="form" label-position="top" class="grid grid-cols-1 sm:grid-cols-2 gap-x-6">
        <el-form-item label="昵称">
          <el-input v-model="form.nickname" placeholder="请输入昵称" maxlength="50" />
        </el-form-item>

        <el-form-item label="年级">
          <el-select v-model="form.grade" placeholder="选择年级" class="w-full">
            <el-option v-for="g in grades" :key="g" :label="g" :value="g" />
          </el-select>
        </el-form-item>

        <el-form-item label="手机号码">
          <el-input v-model="form.phone" placeholder="请输入手机号码" maxlength="20" />
        </el-form-item>

        <el-form-item label="性别">
          <el-select v-model="form.gender" placeholder="选择性别" clearable class="w-full">
            <el-option label="男" value="male" />
            <el-option label="女" value="female" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>

        <el-form-item label="年龄">
          <el-input-number v-model="form.age" :min="1" :max="120" controls-position="right" class="w-full" />
        </el-form-item>

        <el-form-item label="邮箱（不可修改）">
          <el-input :model-value="authStore.user?.email" disabled />
        </el-form-item>
      </el-form>

      <div class="flex justify-end mt-2">
        <el-button type="primary" :loading="saving" @click="saveProfile">保存修改</el-button>
      </div>
    </div>

    <!-- 修改密码 -->
    <div class="card">
      <div class="flex items-center gap-2 mb-5">
        <span class="w-1 h-5 bg-gradient-to-b from-purple-500 to-pink-500 rounded-full inline-block"></span>
        <h3 class="font-bold text-gray-800">修改密码</h3>
      </div>

      <p class="text-sm text-gray-500 mb-4">点击按钮修改你的登录密码，新密码需满足强度要求。</p>

      <div class="flex justify-end">
        <el-button @click="openChangePasswordDialog">修改密码</el-button>
      </div>
    </div>

    <!-- 删除账号 -->
    <div class="card border border-red-100">
      <div class="flex items-center gap-2 mb-4">
        <span class="w-1 h-5 bg-gradient-to-b from-red-500 to-rose-500 rounded-full inline-block"></span>
        <h3 class="font-bold text-gray-800">危险操作</h3>
      </div>
      <div class="bg-red-50 rounded-xl p-4 border border-red-100">
        <p class="text-sm font-semibold text-red-700 mb-1">⚠️ 删除账号</p>
        <p class="text-xs text-red-500 mb-4">
          此操作将永久删除你的账号及所有关联数据（笔记、错题、练习记录、学习计划、文档、对话记录等），且<strong>无法恢复</strong>。
        </p>
        <el-button type="danger" plain @click="showDeleteDialog = true">删除我的账号</el-button>
      </div>
    </div>

    <!-- 确认删除对话框 -->
    <el-dialog
      v-model="showDeleteDialog"
      title="⚠️ 确认删除账号"
      width="420px"
      :close-on-click-modal="false"
    >
      <div class="space-y-3">
        <p class="text-sm text-gray-600">删除后，以下数据将被<strong class="text-red-600">永久清除</strong>，无法找回：</p>
        <ul class="text-xs text-gray-500 list-disc list-inside space-y-1 bg-gray-50 rounded-lg p-3">
          <li>账号信息（邮箱、昵称、年级等）</li>
          <li>所有笔记与闪卡</li>
          <li>错题本记录</li>
          <li>练习题与答题历史</li>
          <li>学习计划</li>
          <li>上传的文档</li>
          <li>AI 对话记录</li>
          <li>作业批改历史</li>
          <li>所有关联关系（教师/家长绑定）</li>
        </ul>
        <p class="text-sm text-gray-700">请在下方输入你的邮箱 <strong class="text-red-600">{{ authStore.user?.email }}</strong> 以确认删除：</p>
        <el-input
          v-model="deleteConfirmEmail"
          placeholder="输入你的邮箱地址"
          clearable
        />
      </div>
      <template #footer>
        <div class="flex gap-3 justify-end">
          <el-button @click="showDeleteDialog = false">取消</el-button>
          <el-button
            type="danger"
            :loading="deleting"
            :disabled="deleteConfirmEmail !== authStore.user?.email"
            @click="deleteAccount"
          >确认删除</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 关联关系管理（学生：绑定码 + 查看关联者；教师/家长：绑定学生 + 创建班级） -->
    <div class="card">
      <div class="flex items-center gap-2 mb-5">
        <span class="w-1 h-5 bg-gradient-to-b from-green-500 to-teal-500 rounded-full inline-block"></span>
        <h3 class="font-bold text-gray-800">关联管理</h3>
        <span class="text-xs text-gray-400 ml-1">
          {{ authStore.user?.role === 'student' ? '— 生成绑定码让家长/教师关联你' : '— 绑定学生以查看学习数据' }}
        </span>
      </div>

      <!-- ── 学生端：绑定码区域 ── -->
      <div v-if="!authStore.user?.role || authStore.user?.role === 'student'" class="space-y-5">
        <!-- 生成绑定码 -->
        <div class="bg-blue-50 rounded-xl p-4 border border-blue-100">
          <p class="text-sm font-semibold text-blue-800 mb-3">📤 生成绑定码</p>
          <p class="text-xs text-blue-600 mb-3">生成6位数字绑定码（有效期24小时），分享给家长或老师，他们使用绑定码后即可查看你的学习数据。</p>
          <div class="flex gap-2 flex-wrap">
            <button
              @click="createBindCode('parent')"
              :disabled="bindCodeLoading"
              class="px-4 py-2 rounded-lg bg-blue-500 hover:bg-blue-600 text-white text-sm font-medium transition-colors disabled:opacity-50"
            >
              🏠 生成家长绑定码
            </button>
            <button
              @click="createBindCode('teacher')"
              :disabled="bindCodeLoading"
              class="px-4 py-2 rounded-lg bg-indigo-500 hover:bg-indigo-600 text-white text-sm font-medium transition-colors disabled:opacity-50"
            >
              🏫 生成教师绑定码
            </button>
          </div>

          <!-- 显示生成的绑定码 -->
          <div v-if="generatedCode" class="mt-4 bg-white rounded-lg p-4 border border-blue-200 flex items-center justify-between">
            <div>
              <p class="text-xs text-blue-500 font-medium mb-1">{{ generatedCode.type === 'parent' ? '家长' : '教师' }}绑定码</p>
              <p class="text-3xl font-black text-blue-700 tracking-widest">{{ generatedCode.code }}</p>
              <p class="text-xs text-gray-400 mt-1">24小时内有效，使用后自动失效</p>
            </div>
            <button
              @click="copyCode(generatedCode.code)"
              class="px-3 py-2 rounded-lg bg-blue-100 hover:bg-blue-200 text-blue-600 text-sm font-medium transition-colors"
            >
              📋 复制
            </button>
          </div>
        </div>

        <!-- 加入班级 -->
        <div class="bg-green-50 rounded-xl p-4 border border-green-100">
          <p class="text-sm font-semibold text-green-800 mb-3">🏫 加入班级</p>
          <div class="flex gap-2">
            <el-input
              v-model="inviteCodeInput"
              placeholder="输入教师班级邀请码（8位）"
              class="flex-1"
              maxlength="8"
              @keyup.enter="joinClass"
            />
            <button
              @click="joinClass"
              :disabled="!inviteCodeInput.trim() || joinClassLoading"
              class="px-4 py-2 rounded-lg bg-green-500 hover:bg-green-600 text-white text-sm font-medium transition-colors disabled:opacity-50 shrink-0"
            >
              加入
            </button>
          </div>
        </div>

        <!-- 已关联的观察者列表 -->
        <div>
          <p class="text-sm font-semibold text-gray-700 mb-3">👥 已关联的教师/家长</p>
          <div v-if="observers.length === 0" class="text-center py-4 text-gray-400 text-sm bg-gray-50 rounded-xl">
            暂无关联的教师或家长
          </div>
          <div v-else class="space-y-2">
            <div
              v-for="obs in observers"
              :key="obs.relation_id"
              class="flex items-center justify-between p-3 bg-gray-50 rounded-xl border border-gray-100"
            >
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white font-bold text-sm">
                  {{ obs.nickname?.[0]?.toUpperCase() || '?' }}
                </div>
                <div>
                  <p class="text-sm font-semibold text-gray-700">{{ obs.nickname }}</p>
                  <p class="text-xs text-gray-400">{{ obs.relation_type === 'teacher' ? '教师' : '家长' }}</p>
                </div>
              </div>
              <button
                @click="removeRelation(obs.relation_id)"
                class="text-xs text-red-400 hover:text-red-600 transition-colors"
              >解除</button>
            </div>
          </div>
        </div>
      </div>

      <!-- ── 教师/家长端：绑定学生 + 班级管理 ── -->
      <div v-else class="space-y-5">
        <!-- 使用绑定码绑定学生 -->
        <div class="bg-indigo-50 rounded-xl p-4 border border-indigo-100">
          <p class="text-sm font-semibold text-indigo-800 mb-3">🔗 使用绑定码关联学生</p>
          <p class="text-xs text-indigo-600 mb-3">让学生在个人中心生成绑定码后，在此输入即可关联。</p>
          <div class="flex gap-2">
            <el-input
              v-model="bindCodeInput"
              placeholder="输入学生6位绑定码"
              class="flex-1"
              maxlength="6"
              @keyup.enter="bindStudent"
            />
            <button
              @click="bindStudent"
              :disabled="!bindCodeInput.trim() || bindStudentLoading"
              class="px-4 py-2 rounded-lg bg-indigo-500 hover:bg-indigo-600 text-white text-sm font-medium transition-colors disabled:opacity-50 shrink-0"
            >
              绑定
            </button>
          </div>
        </div>

        <!-- 教师端：班级管理 -->
        <div v-if="authStore.user?.role === 'teacher'" class="bg-green-50 rounded-xl p-4 border border-green-100">
          <p class="text-sm font-semibold text-green-800 mb-3">🏫 创建班级</p>
          <p class="text-xs text-green-600 mb-3">创建班级后会生成邀请码，学生输入邀请码可自动加入班级并与你关联。</p>
          <div class="flex gap-2">
            <el-input
              v-model="classNameInput"
              placeholder="班级名称（如：高一3班）"
              class="flex-1"
              maxlength="50"
              @keyup.enter="createClass"
            />
            <button
              @click="createClass"
              :disabled="!classNameInput.trim() || createClassLoading"
              class="px-4 py-2 rounded-lg bg-green-500 hover:bg-green-600 text-white text-sm font-medium transition-colors disabled:opacity-50 shrink-0"
            >
              创建
            </button>
          </div>

          <!-- 班级列表 -->
          <div v-if="classes.length > 0" class="mt-3 space-y-2">
            <div
              v-for="cls in classes"
              :key="cls.id"
              class="flex items-center justify-between p-3 bg-white rounded-lg border border-green-100"
            >
              <div>
                <p class="text-sm font-semibold text-gray-700">{{ cls.name }}</p>
                <p class="text-xs text-gray-400">邀请码：<span class="font-mono font-bold text-green-600">{{ cls.invite_code }}</span></p>
              </div>
              <button
                @click="copyCode(cls.invite_code)"
                class="text-xs text-green-600 hover:text-green-800 transition-colors"
              >复制码</button>
            </div>
          </div>
        </div>

        <!-- 关联的学生列表 -->
        <div>
          <div class="flex items-center justify-between mb-3">
            <p class="text-sm font-semibold text-gray-700">👥 已关联的学生</p>
            <RouterLink to="/monitor" class="text-xs text-blue-500 hover:text-blue-700 font-medium">查看详情 →</RouterLink>
          </div>
          <div v-if="students.length === 0" class="text-center py-4 text-gray-400 text-sm bg-gray-50 rounded-xl">
            暂无关联的学生
          </div>
          <div v-else class="space-y-2">
            <div
              v-for="stu in students"
              :key="stu.relation_id"
              class="flex items-center justify-between p-3 bg-gray-50 rounded-xl border border-gray-100"
            >
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-full bg-gradient-to-br from-blue-400 to-indigo-500 flex items-center justify-center text-white font-bold text-sm">
                  {{ stu.nickname?.[0]?.toUpperCase() || '?' }}
                </div>
                <div>
                  <p class="text-sm font-semibold text-gray-700">{{ stu.nickname }}</p>
                  <p class="text-xs text-gray-400">{{ stu.grade }}{{ stu.class_name ? ' · ' + stu.class_name : '' }}</p>
                </div>
              </div>
              <button
                @click="removeRelation(stu.relation_id)"
                class="text-xs text-red-400 hover:text-red-600 transition-colors"
              >解除</button>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>

  <!-- 修改密码对话框 -->
  <ChangePasswordDialog ref="changePasswordDialog" />
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'
import { relationsApi } from '@/api/relations'
import { ElMessage } from 'element-plus'
import ChangePasswordDialog from '@/components/ChangePasswordDialog.vue'

const router = useRouter()
const authStore = useAuthStore()
const grades = ['初一', '初二', '初三', '高一', '高二', '高三']

// ── 删除账号 ──────────────────────────────────────────────────────────────────
const showDeleteDialog = ref(false)
const deleteConfirmEmail = ref('')
const deleting = ref(false)

async function deleteAccount() {
  if (deleteConfirmEmail.value !== authStore.user?.email) {
    ElMessage.warning('邮箱输入不匹配')
    return
  }
  deleting.value = true
  try {
    await authApi.deleteMe()
    ElMessage.success('账号已删除')
    showDeleteDialog.value = false
    authStore.logout()
    router.push('/login')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '删除失败，请稍后重试')
  } finally {
    deleting.value = false
  }
}


// ── 基本资料 ──────────────────────────────────────────────────────────────────
const form = reactive({
  nickname: '',
  grade: '',
  phone: '',
  gender: '' as string,
  age: undefined as number | undefined,
})
const saving = ref(false)

// ── 修改密码对话框 ─────────────────────────────────────────────────────────────
const changePasswordDialog = ref<InstanceType<typeof ChangePasswordDialog>>()

function openChangePasswordDialog() {
  changePasswordDialog.value!.visible.value = true
}

// ── 关联关系 ──────────────────────────────────────────────────────────────────
const observers = ref<any[]>([])   // 学生端：关联的教师/家长
const students = ref<any[]>([])    // 教师/家长端：关联的学生
const classes = ref<any[]>([])     // 教师端：创建的班级

// 学生端操作
const generatedCode = ref<{ code: string; type: 'teacher' | 'parent' } | null>(null)
const bindCodeLoading = ref(false)
const inviteCodeInput = ref('')
const joinClassLoading = ref(false)

// 教师/家长端操作
const bindCodeInput = ref('')
const bindStudentLoading = ref(false)
const classNameInput = ref('')
const createClassLoading = ref(false)

// ── 角色样式 ──────────────────────────────────────────────────────────────────
function roleLabel(role?: string | null) {
  return { student: '学生', teacher: '教师', parent: '家长' }[role || 'student'] || '学生'
}

function roleStyle(role?: string | null) {
  const map: Record<string, string> = {
    student: 'bg-blue-400/20 text-blue-200',
    teacher: 'bg-green-400/20 text-green-200',
    parent: 'bg-purple-400/20 text-purple-200',
  }
  return map[role || 'student'] || map.student
}

// ── 基本资料操作 ──────────────────────────────────────────────────────────────
function syncForm() {
  const u = authStore.user
  if (!u) return
  form.nickname = u.nickname || ''
  form.grade = u.grade || ''
  form.phone = u.phone || ''
  form.gender = u.gender || ''
  form.age = u.age ?? undefined
}

async function saveProfile() {
  saving.value = true
  try {
    const res: any = await authApi.updateMe({
      nickname: form.nickname,
      grade: form.grade,
      phone: form.phone,
      gender: form.gender || undefined,
      age: form.age,
    })
    authStore.user = res.data
    localStorage.setItem('user', JSON.stringify(res.data))
    ElMessage.success('资料已更新')
  } catch {
  } finally {
    saving.value = false
  }
}

// ── 学生端：生成绑定码 ────────────────────────────────────────────────────────
async function createBindCode(type: 'teacher' | 'parent') {
  bindCodeLoading.value = true
  try {
    const res: any = await relationsApi.createBindCode(type)
    generatedCode.value = { code: res.data.code, type }
    ElMessage.success(`绑定码已生成，有效期 ${res.data.expires_in_hours} 小时`)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '生成失败')
  } finally {
    bindCodeLoading.value = false
  }
}

// ── 学生端：加入班级 ──────────────────────────────────────────────────────────
async function joinClass() {
  if (!inviteCodeInput.value.trim()) return
  joinClassLoading.value = true
  try {
    const res: any = await relationsApi.joinClass(inviteCodeInput.value.trim())
    ElMessage.success(res.message || '成功加入班级')
    inviteCodeInput.value = ''
    await loadObservers()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加入失败，请检查邀请码')
  } finally {
    joinClassLoading.value = false
  }
}

// ── 教师/家长端：绑定学生 ─────────────────────────────────────────────────────
async function bindStudent() {
  if (!bindCodeInput.value.trim()) return
  bindStudentLoading.value = true
  const role = authStore.user?.role as 'teacher' | 'parent'
  try {
    await relationsApi.bind(bindCodeInput.value.trim(), role)
    ElMessage.success('绑定成功')
    bindCodeInput.value = ''
    await loadStudents()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '绑定失败，请检查绑定码')
  } finally {
    bindStudentLoading.value = false
  }
}

// ── 教师端：创建班级 ──────────────────────────────────────────────────────────
async function createClass() {
  if (!classNameInput.value.trim()) return
  createClassLoading.value = true
  try {
    const res: any = await relationsApi.createClass(classNameInput.value.trim())
    ElMessage.success('班级创建成功')
    classNameInput.value = ''
    classes.value.push(res.data)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '创建失败')
  } finally {
    createClassLoading.value = false
  }
}

// ── 解除关联 ──────────────────────────────────────────────────────────────────
async function removeRelation(relation_id: number) {
  try {
    await relationsApi.removeRelation(relation_id)
    ElMessage.success('已解除关联')
    const role = authStore.user?.role
    if (!role || role === 'student') {
      observers.value = observers.value.filter(o => o.relation_id !== relation_id)
    } else {
      students.value = students.value.filter(s => s.relation_id !== relation_id)
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '解除失败')
  }
}

// ── 复制到剪贴板 ──────────────────────────────────────────────────────────────
async function copyCode(code: string) {
  try {
    await navigator.clipboard.writeText(code)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.info(`绑定码：${code}`)
  }
}

// ── 数据加载 ──────────────────────────────────────────────────────────────────
async function loadObservers() {
  try {
    const res: any = await relationsApi.getObservers()
    observers.value = res.data || []
  } catch {}
}

async function loadStudents() {
  try {
    const res: any = await relationsApi.getStudents()
    students.value = res.data || []
  } catch {}
}

async function loadClasses() {
  try {
    const res: any = await relationsApi.getClasses()
    classes.value = res.data || []
  } catch {}
}

onMounted(async () => {
  try {
    await authStore.fetchMe()
  } catch {}
  syncForm()

  const role = authStore.user?.role
  if (!role || role === 'student') {
    await loadObservers()
  } else {
    await loadStudents()
    if (role === 'teacher') await loadClasses()
  }
})
</script>

<style scoped>
@reference "../../style.css";
.card {
  @apply bg-white rounded-2xl border border-gray-100 shadow-sm p-6;
}
</style>
