<template>
  <div class="max-w-3xl mx-auto space-y-6">

    <!-- Header card -->
    <div class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white shadow-lg">
      <div class="absolute -top-10 -right-10 w-48 h-48 bg-white/10 rounded-full"></div>
      <div class="absolute -bottom-8 -right-24 w-64 h-64 bg-white/5 rounded-full"></div>
      <div class="relative p-6 flex items-center gap-5">
        <div class="w-20 h-20 rounded-2xl bg-white/20 backdrop-blur-sm flex items-center justify-center text-4xl font-black shrink-0 border border-white/20">
          {{ form.nickname?.[0]?.toUpperCase() || 'U' }}
        </div>
        <div class="min-w-0">
          <h1 class="text-2xl font-bold truncate">{{ form.nickname || $t('dashboard.student_suffix') }}</h1>
          <p class="text-blue-100 text-sm mt-1">{{ authStore.user?.email }}</p>
          <div class="flex items-center gap-2 mt-1">
            <p class="text-blue-200 text-xs">{{ form.grade || $t('profile.grade_unset') }}</p>
            <span
              class="text-xs px-2 py-0.5 rounded-full font-medium"
              :class="roleStyle(authStore.user?.role)"
            >{{ roleLabel(authStore.user?.role) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Basic info -->
    <div class="card">
      <div class="flex items-center gap-2 mb-5">
        <span class="w-1 h-5 bg-gradient-to-b from-blue-500 to-indigo-500 rounded-full inline-block"></span>
        <h3 class="font-bold text-gray-800">{{ $t('profile.basic_info') }}</h3>
      </div>

      <el-form :model="form" label-position="top" class="grid grid-cols-1 sm:grid-cols-2 gap-x-6">
        <el-form-item :label="$t('profile.nickname_label')">
          <el-input v-model="form.nickname" :placeholder="$t('profile.nickname_placeholder')" maxlength="50" />
        </el-form-item>

        <el-form-item :label="$t('profile.grade_label')">
          <el-select v-model="form.grade" :placeholder="$t('profile.grade_placeholder')" class="w-full">
            <el-option v-for="g in grades" :key="g" :label="g" :value="g" />
          </el-select>
        </el-form-item>

        <el-form-item :label="$t('profile.phone_label')">
          <el-input v-model="form.phone" :placeholder="$t('profile.phone_placeholder')" maxlength="20" />
        </el-form-item>

        <el-form-item :label="$t('profile.gender_label')">
          <el-select v-model="form.gender" :placeholder="$t('profile.gender_placeholder')" clearable class="w-full">
            <el-option :label="$t('profile.gender_male')" value="male" />
            <el-option :label="$t('profile.gender_female')" value="female" />
            <el-option :label="$t('profile.gender_other')" value="other" />
          </el-select>
        </el-form-item>

        <el-form-item :label="$t('profile.age_label')">
          <el-input-number v-model="form.age" :min="1" :max="120" controls-position="right" class="w-full" />
        </el-form-item>

        <el-form-item :label="$t('profile.email_label')">
          <el-input :model-value="authStore.user?.email" disabled />
        </el-form-item>
      </el-form>

      <div class="flex justify-end mt-2">
        <el-button type="primary" :loading="saving" @click="saveProfile">{{ $t('profile.save_btn') }}</el-button>
      </div>
    </div>

    <!-- Change password -->
    <div class="card">
      <div class="flex items-center gap-2 mb-5">
        <span class="w-1 h-5 bg-gradient-to-b from-purple-500 to-pink-500 rounded-full inline-block"></span>
        <h3 class="font-bold text-gray-800">{{ $t('profile.change_password') }}</h3>
      </div>

      <p class="text-sm text-gray-500 mb-4">{{ $t('profile.change_password_hint') }}</p>

      <div class="flex justify-end">
        <el-button @click="openChangePasswordDialog">{{ $t('profile.change_password_btn') }}</el-button>
      </div>
    </div>

    <!-- Delete account -->
    <div class="card border border-red-100">
      <div class="flex items-center gap-2 mb-4">
        <span class="w-1 h-5 bg-gradient-to-b from-red-500 to-rose-500 rounded-full inline-block"></span>
        <h3 class="font-bold text-gray-800">{{ $t('profile.danger_zone') }}</h3>
      </div>
      <div class="bg-red-50 rounded-xl p-4 border border-red-100">
        <p class="text-sm font-semibold text-red-700 mb-1">⚠️ {{ $t('profile.delete_account') }}</p>
        <p class="text-xs text-red-500 mb-4">{{ $t('profile.delete_account_warning') }}</p>
        <el-button type="danger" plain @click="showDeleteDialog = true">{{ $t('profile.delete_account_btn') }}</el-button>
      </div>
    </div>

    <!-- Confirm delete dialog -->
    <el-dialog
      v-model="showDeleteDialog"
      :title="'⚠️ ' + $t('profile.delete_confirm_title')"
      width="420px"
      :close-on-click-modal="false"
    >
      <div class="space-y-3">
        <p class="text-sm text-gray-600">{{ $t('profile.delete_confirm_data') }}</p>
        <ul class="text-xs text-gray-500 list-disc list-inside space-y-1 bg-gray-50 rounded-lg p-3">
          <li>{{ $t('profile.delete_data_account') }}</li>
          <li>{{ $t('profile.delete_data_notes') }}</li>
          <li>{{ $t('profile.delete_data_wrong_book') }}</li>
          <li>{{ $t('profile.delete_data_quiz') }}</li>
          <li>{{ $t('profile.delete_data_plan') }}</li>
          <li>{{ $t('profile.delete_data_docs') }}</li>
          <li>{{ $t('profile.delete_data_chat') }}</li>
          <li>{{ $t('profile.delete_data_homework') }}</li>
          <li>{{ $t('profile.delete_data_relations') }}</li>
        </ul>
        <i18n-t keypath="profile.delete_email_confirm" tag="p" class="text-sm text-gray-700">
          <template #email>
            <strong class="text-red-600">{{ authStore.user?.email }}</strong>
          </template>
        </i18n-t>
        <el-input
          v-model="deleteConfirmEmail"
          :placeholder="$t('profile.delete_email_input_placeholder')"
          clearable
        />
      </div>
      <template #footer>
        <div class="flex gap-3 justify-end">
          <el-button @click="showDeleteDialog = false">{{ $t('profile.cancel_btn') }}</el-button>
          <el-button
            type="danger"
            :loading="deleting"
            :disabled="deleteConfirmEmail !== authStore.user?.email"
            @click="deleteAccount"
          >{{ $t('profile.confirm_delete_btn') }}</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- Relations management (student: bind code + observers; teacher/parent: bind student + create class) -->
    <div class="card">
      <div class="flex items-center gap-2 mb-5">
        <span class="w-1 h-5 bg-gradient-to-b from-green-500 to-teal-500 rounded-full inline-block"></span>
        <h3 class="font-bold text-gray-800">{{ $t('profile.relations_management') }}</h3>
        <span class="text-xs text-gray-400 ml-1">
          {{ authStore.user?.role === 'student' ? $t('profile.relations_student_hint') : $t('profile.relations_teacher_hint') }}
        </span>
      </div>

      <!-- Student side: bind code area -->
      <div v-if="!authStore.user?.role || authStore.user?.role === 'student'" class="space-y-5">
        <!-- Generate bind code -->
        <div class="bg-blue-50 rounded-xl p-4 border border-blue-100">
          <p class="text-sm font-semibold text-blue-800 mb-3">📤 {{ $t('profile.gen_bind_code_title') }}</p>
          <p class="text-xs text-blue-600 mb-3">{{ $t('profile.gen_bind_code_hint') }}</p>
          <div class="flex gap-2 flex-wrap">
            <button
              @click="createBindCode('parent')"
              :disabled="bindCodeLoading"
              class="px-4 py-2 rounded-lg bg-blue-500 hover:bg-blue-600 text-white text-sm font-medium transition-colors disabled:opacity-50"
            >
              🏠 {{ $t('profile.gen_parent_code_btn') }}
            </button>
            <button
              @click="createBindCode('teacher')"
              :disabled="bindCodeLoading"
              class="px-4 py-2 rounded-lg bg-indigo-500 hover:bg-indigo-600 text-white text-sm font-medium transition-colors disabled:opacity-50"
            >
              🏫 {{ $t('profile.gen_teacher_code_btn') }}
            </button>
          </div>

          <!-- Display generated bind code -->
          <div v-if="generatedCode" class="mt-4 bg-white rounded-lg p-4 border border-blue-200 flex items-center justify-between">
            <div>
              <p class="text-xs text-blue-500 font-medium mb-1">{{ generatedCode.type === 'parent' ? $t('profile.parent_code_label') : $t('profile.teacher_code_label') }}</p>
              <p class="text-3xl font-black text-blue-700 tracking-widest">{{ generatedCode.code }}</p>
              <p class="text-xs text-gray-400 mt-1">{{ $t('profile.code_valid_hint') }}</p>
            </div>
            <button
              @click="copyCode(generatedCode.code)"
              class="px-3 py-2 rounded-lg bg-blue-100 hover:bg-blue-200 text-blue-600 text-sm font-medium transition-colors"
            >
              📋 {{ $t('profile.copy_code_btn') }}
            </button>
          </div>
        </div>

        <!-- Join class -->
        <div class="bg-green-50 rounded-xl p-4 border border-green-100">
          <p class="text-sm font-semibold text-green-800 mb-3">🏫 {{ $t('profile.join_class_title') }}</p>
          <div class="flex gap-2">
            <el-input
              v-model="inviteCodeInput"
              :placeholder="$t('profile.class_code_placeholder')"
              class="flex-1"
              maxlength="8"
              @keyup.enter="joinClass"
            />
            <button
              @click="joinClass"
              :disabled="!inviteCodeInput.trim() || joinClassLoading"
              class="px-4 py-2 rounded-lg bg-green-500 hover:bg-green-600 text-white text-sm font-medium transition-colors disabled:opacity-50 shrink-0"
            >
              {{ $t('profile.join_class_btn') }}
            </button>
          </div>
        </div>

        <!-- Linked observers list -->
        <div>
          <p class="text-sm font-semibold text-gray-700 mb-3">👥 {{ $t('profile.observers_list_title') }}</p>
          <div v-if="observers.length === 0" class="text-center py-4 text-gray-400 text-sm bg-gray-50 rounded-xl">
            {{ $t('profile.no_observers') }}
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
                  <p class="text-xs text-gray-400">{{ obs.relation_type === 'teacher' ? $t('profile.relation_teacher_label') : $t('profile.relation_parent_label') }}</p>
                </div>
              </div>
              <button
                @click="removeRelation(obs.relation_id)"
                class="text-xs text-red-400 hover:text-red-600 transition-colors"
              >{{ $t('profile.unbind_btn') }}</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Teacher/parent side: bind student + class management -->
      <div v-else class="space-y-5">
        <!-- Bind student with bind code -->
        <div class="bg-indigo-50 rounded-xl p-4 border border-indigo-100">
          <p class="text-sm font-semibold text-indigo-800 mb-3">🔗 {{ $t('profile.bind_student_title') }}</p>
          <p class="text-xs text-indigo-600 mb-3">{{ $t('profile.bind_student_hint') }}</p>
          <div class="flex gap-2">
            <el-input
              v-model="bindCodeInput"
              :placeholder="$t('profile.student_code_placeholder')"
              class="flex-1"
              maxlength="6"
              @keyup.enter="bindStudent"
            />
            <button
              @click="bindStudent"
              :disabled="!bindCodeInput.trim() || bindStudentLoading"
              class="px-4 py-2 rounded-lg bg-indigo-500 hover:bg-indigo-600 text-white text-sm font-medium transition-colors disabled:opacity-50 shrink-0"
            >
              {{ $t('profile.bind_btn') }}
            </button>
          </div>
        </div>

        <!-- Teacher side: class management -->
        <div v-if="authStore.user?.role === 'teacher'" class="bg-green-50 rounded-xl p-4 border border-green-100">
          <p class="text-sm font-semibold text-green-800 mb-3">🏫 {{ $t('profile.create_class_title') }}</p>
          <p class="text-xs text-green-600 mb-3">{{ $t('profile.create_class_hint') }}</p>
          <div class="flex gap-2">
            <el-input
              v-model="classNameInput"
              :placeholder="$t('profile.class_name_placeholder')"
              class="flex-1"
              maxlength="50"
              @keyup.enter="createClass"
            />
            <button
              @click="createClass"
              :disabled="!classNameInput.trim() || createClassLoading"
              class="px-4 py-2 rounded-lg bg-green-500 hover:bg-green-600 text-white text-sm font-medium transition-colors disabled:opacity-50 shrink-0"
            >
              {{ $t('profile.create_class_btn') }}
            </button>
          </div>

          <!-- Class list -->
          <div v-if="classes.length > 0" class="mt-3 space-y-2">
            <div
              v-for="cls in classes"
              :key="cls.id"
              class="flex items-center justify-between p-3 bg-white rounded-lg border border-green-100"
            >
              <div>
                <p class="text-sm font-semibold text-gray-700">{{ cls.name }}</p>
                <p class="text-xs text-gray-400">{{ $t('profile.class_invite_code') }}<span class="font-mono font-bold text-green-600">{{ cls.invite_code }}</span></p>
              </div>
              <button
                @click="copyCode(cls.invite_code)"
                class="text-xs text-green-600 hover:text-green-800 transition-colors"
              >{{ $t('profile.copy_invite_code_btn') }}</button>
            </div>
          </div>
        </div>

        <!-- Linked students list -->
        <div>
          <div class="flex items-center justify-between mb-3">
            <p class="text-sm font-semibold text-gray-700">👥 {{ $t('profile.students_list_title') }}</p>
            <RouterLink to="/monitor" class="text-xs text-blue-500 hover:text-blue-700 font-medium">{{ $t('profile.view_monitor') }}</RouterLink>
          </div>
          <div v-if="students.length === 0" class="text-center py-4 text-gray-400 text-sm bg-gray-50 rounded-xl">
            {{ $t('profile.no_students') }}
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
              >{{ $t('profile.unbind_btn') }}</button>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>

  <!-- Change password dialog -->
  <ChangePasswordDialog ref="changePasswordDialog" />
</template>

<script setup lang="ts">
import { reactive, ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'
import { relationsApi } from '@/api/relations'
import { ElMessage } from 'element-plus'
import ChangePasswordDialog from '@/components/ChangePasswordDialog.vue'

const router = useRouter()
const authStore = useAuthStore()
const { t } = useI18n()

// Grade list (localized)
const grades = computed(() => [
  t('grades.grade7'),
  t('grades.grade8'),
  t('grades.grade9'),
  t('grades.grade10'),
  t('grades.grade11'),
  t('grades.grade12'),
])

// ── Delete account ────────────────────────────────────────────────────────────
const showDeleteDialog = ref(false)
const deleteConfirmEmail = ref('')
const deleting = ref(false)

async function deleteAccount() {
  if (deleteConfirmEmail.value !== authStore.user?.email) {
    ElMessage.warning(t('profile.email_mismatch'))
    return
  }
  deleting.value = true
  try {
    await authApi.deleteMe()
    ElMessage.success(t('profile.account_deleted'))
    showDeleteDialog.value = false
    authStore.logout()
    router.push('/login?clearCredentials=true')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || t('profile.delete_failed'))
  } finally {
    deleting.value = false
  }
}


// ── Basic profile ─────────────────────────────────────────────────────────────
const form = reactive({
  nickname: '',
  grade: '',
  phone: '',
  gender: '' as string,
  age: undefined as number | undefined,
})
const saving = ref(false)

// ── Change password dialog ────────────────────────────────────────────────────
const changePasswordDialog = ref()

function openChangePasswordDialog() {
  changePasswordDialog.value?.open()
}

// ── Relations ─────────────────────────────────────────────────────────────────
const observers = ref<any[]>([])   // Student side: linked teachers/parents
const students = ref<any[]>([])    // Teacher/parent side: linked students
const classes = ref<any[]>([])     // Teacher side: created classes

// Student side operations
const generatedCode = ref<{ code: string; type: 'teacher' | 'parent' } | null>(null)
const bindCodeLoading = ref(false)
const inviteCodeInput = ref('')
const joinClassLoading = ref(false)

// Teacher/parent side operations
const bindCodeInput = ref('')
const bindStudentLoading = ref(false)
const classNameInput = ref('')
const createClassLoading = ref(false)

// ── Role styles ───────────────────────────────────────────────────────────────
function roleLabel(role?: string | null) {
  const labels: Record<string, string> = {
    student: t('auth.student'),
    teacher: t('auth.teacher'),
    parent: t('auth.parent'),
  }
  return labels[role || 'student'] || t('auth.student')
}

function roleStyle(role?: string | null) {
  const map: Record<string, string> = {
    student: 'bg-blue-400/20 text-blue-200',
    teacher: 'bg-green-400/20 text-green-200',
    parent: 'bg-purple-400/20 text-purple-200',
  }
  return map[role || 'student'] || map.student
}

// ── Basic profile operations ──────────────────────────────────────────────────
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
    ElMessage.success(t('profile.save_success'))
  } catch {
  } finally {
    saving.value = false
  }
}

// ── Student side: generate bind code ─────────────────────────────────────────
async function createBindCode(type: 'teacher' | 'parent') {
  bindCodeLoading.value = true
  try {
    const res: any = await relationsApi.createBindCode(type)
    generatedCode.value = { code: res.data.code, type }
    ElMessage.success(t('profile.bind_code_generated', { hours: res.data.expires_in_hours }))
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || t('profile.gen_code_failed'))
  } finally {
    bindCodeLoading.value = false
  }
}

// ── Student side: join class ──────────────────────────────────────────────────
async function joinClass() {
  if (!inviteCodeInput.value.trim()) return
  joinClassLoading.value = true
  try {
    const res: any = await relationsApi.joinClass(inviteCodeInput.value.trim())
    ElMessage.success(res.message || t('profile.join_class_success'))
    inviteCodeInput.value = ''
    await loadObservers()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || t('profile.join_class_failed'))
  } finally {
    joinClassLoading.value = false
  }
}

// ── Teacher/parent side: bind student ────────────────────────────────────────
async function bindStudent() {
  if (!bindCodeInput.value.trim()) return
  bindStudentLoading.value = true
  const role = authStore.user?.role as 'teacher' | 'parent'
  try {
    await relationsApi.bind(bindCodeInput.value.trim(), role)
    ElMessage.success(t('profile.bind_success'))
    bindCodeInput.value = ''
    await loadStudents()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || t('profile.bind_failed'))
  } finally {
    bindStudentLoading.value = false
  }
}

// ── Teacher side: create class ────────────────────────────────────────────────
async function createClass() {
  if (!classNameInput.value.trim()) return
  createClassLoading.value = true
  try {
    const res: any = await relationsApi.createClass(classNameInput.value.trim())
    ElMessage.success(t('profile.create_class_success'))
    classNameInput.value = ''
    classes.value.push(res.data)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || t('profile.create_failed'))
  } finally {
    createClassLoading.value = false
  }
}

// ── Remove relation ───────────────────────────────────────────────────────────
async function removeRelation(relation_id: number) {
  try {
    await relationsApi.removeRelation(relation_id)
    ElMessage.success(t('profile.unbind_success'))
    const role = authStore.user?.role
    if (!role || role === 'student') {
      observers.value = observers.value.filter(o => o.relation_id !== relation_id)
    } else {
      students.value = students.value.filter(s => s.relation_id !== relation_id)
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || t('profile.unbind_failed'))
  }
}

// ── Copy to clipboard ─────────────────────────────────────────────────────────
async function copyCode(code: string) {
  try {
    await navigator.clipboard.writeText(code)
    ElMessage.success(t('profile.copy_success'))
  } catch {
    ElMessage.info(t('profile.code_fallback', { code }))
  }
}

// ── Data loading ──────────────────────────────────────────────────────────────
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
