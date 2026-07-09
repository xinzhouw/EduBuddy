<template>
  <div class="min-h-screen flex">
    <div class="hidden lg:flex w-1/2 bg-gradient-to-br from-blue-500 to-blue-700 flex-col items-center justify-center p-12 text-white">
      <div class="text-center">
        <div class="text-7xl mb-6">📚</div>
        <h1 class="text-4xl font-bold mb-4">EduBuddy</h1>
        <p class="text-xl text-blue-100">{{ $t('auth.ai_journey') }}</p>
      </div>
    </div>
    <div class="flex-1 flex items-center justify-center p-4 sm:p-8">
      <div class="w-full max-w-md">
        <!-- Mobile logo -->
        <div class="lg:hidden text-center mb-6">
          <div class="text-5xl mb-2">📚</div>
          <h1 class="text-2xl font-bold text-gray-900">EduBuddy</h1>
        </div>

        <div class="text-center mb-6 sm:mb-8">
          <h2 class="text-xl sm:text-2xl font-bold text-gray-900">{{ $t('auth.create_account') }}</h2>
          <p class="text-gray-500 mt-2 text-sm sm:text-base">{{ $t('auth.register_subtitle') }}</p>
        </div>
        <el-form :model="form" :rules="rules" ref="formRef">
          <el-form-item prop="role">
            <el-radio-group v-model="form.role" size="large" class="w-full role-group flex flex-wrap gap-2">
              <el-radio-button v-for="r in roles" :key="r.value" :value="r.value">
                {{ r.icon }} {{ r.label }}
              </el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item prop="nickname">
            <el-input v-model="form.nickname" :placeholder="$t('auth.nickname_placeholder')" size="large" prefix-icon="User" clearable />
          </el-form-item>
          <el-form-item prop="email">
            <el-input v-model="form.email" :placeholder="$t('auth.email')" size="large" type="email" prefix-icon="Message" clearable />
          </el-form-item>
          <el-form-item v-if="form.role === 'student'" prop="grade">
            <el-select v-model="form.grade" :placeholder="$t('profile.grade_placeholder')" size="large" class="w-full">
              <el-option v-for="g in grades" :key="g.value" :label="g.label" :value="g.value" />
            </el-select>
          </el-form-item>
          <el-form-item prop="password">
            <PasswordInput ref="passwordInput" />
          </el-form-item>
          <el-form-item prop="confirmPassword">
            <el-input v-model="form.confirmPassword" :placeholder="$t('auth.confirm_password')" size="large" type="password" show-password prefix-icon="Lock" clearable autocomplete="new-password" />
          </el-form-item>
          <el-button type="primary" size="large" class="w-full mt-2 h-11 sm:h-12" :loading="loading" @click="handleRegister">
            {{ $t('auth.register') }}
          </el-button>
        </el-form>
        <p class="text-center text-gray-500 mt-6 text-xs sm:text-sm">
          {{ $t('auth.has_account') }}
          <RouterLink to="/login" class="text-blue-500 hover:text-blue-600 font-medium">{{ $t('auth.go_login') }}</RouterLink>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import type { FormInstance, FormItemRule } from 'element-plus'
import PasswordInput from '@/components/PasswordInput.vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()
const formRef = ref<FormInstance>()
const passwordInput = ref<InstanceType<typeof PasswordInput>>()
const loading = ref(false)

onMounted(async () => {
  await resetForm()
})

async function resetForm() {
  form.role = 'student'
  form.nickname = ''
  form.email = ''
  form.grade = ''
  form.confirmPassword = ''
  passwordInput.value?.reset()
  formRef.value?.clearValidate()

  // Clear all password fields from DOM to prevent browser autocomplete residue
  await nextTick()
  const passwordInputs = document.querySelectorAll('input[type="password"]')
  passwordInputs.forEach(input => {
    const el = input as HTMLInputElement
    el.value = ''
    el.setAttribute('autocomplete', 'new-password')
  })

  // Clear multiple times to ensure browser autocomplete does not override
  for (let i = 0; i < 3; i++) {
    await new Promise(resolve => setTimeout(resolve, 50))
    passwordInputs.forEach(input => {
      const el = input as HTMLInputElement
      el.value = ''
    })
  }
}

async function clearSensitiveData() {
  // Clear all sensitive data immediately after successful registration
  form.confirmPassword = ''
  passwordInput.value?.reset()

  await nextTick()
  const passwordInputs = document.querySelectorAll('input[type="password"]')
  passwordInputs.forEach(input => {
    const el = input as HTMLInputElement
    el.value = ''
  })
}
const grades = computed(() => [
  { value: '初一', label: t('grades.grade7') },
  { value: '初二', label: t('grades.grade8') },
  { value: '初三', label: t('grades.grade9') },
  { value: '高一', label: t('grades.grade10') },
  { value: '高二', label: t('grades.grade11') },
  { value: '高三', label: t('grades.grade12') },
])
const roles = computed(() => [
  { value: 'student', label: t('auth.student'), icon: '🎓' },
  { value: 'parent', label: t('auth.parent'), icon: '👨‍👩‍👧' },
  { value: 'teacher', label: t('auth.teacher'), icon: '🧑‍🏫' },
])
const form = reactive({ role: 'student', nickname: '', email: '', grade: '', confirmPassword: '' })

const validateConfirmPassword = (_rule: FormItemRule, value: string, callback: (err?: Error) => void) => {
  if (value === '') {
    callback(new Error(t('auth.enter_confirm_password')))
  } else if (value !== passwordInput.value?.password) {
    callback(new Error(t('auth.password_mismatch')))
  } else {
    callback()
  }
}

const validateGrade = (_rule: FormItemRule, value: string, callback: (err?: Error) => void) => {
  // Only students need to select grade; parents/teachers do not
  if (form.role === 'student' && !value) {
    callback(new Error(t('auth.select_grade')))
  } else {
    callback()
  }
}

const validatePassword = (_rule: FormItemRule, _value: unknown, callback: (err?: Error) => void) => {
  const issues = passwordInput.value?.validation.issues ?? []
  if (!passwordInput.value?.password) {
    callback(new Error(t('auth.enter_password')))
  } else if (issues.length > 0) {
    callback(new Error(issues[0]))
  } else {
    callback()
  }
}

const rules = {
  nickname: [{ required: true, message: t('auth.enter_nickname'), trigger: 'blur' }],
  email: [{ required: true, type: 'email', message: t('auth.invalid_email'), trigger: 'blur' }],
  grade: [{ validator: validateGrade, trigger: 'change' }],
  password: [{ validator: validatePassword, trigger: 'blur' }],
  confirmPassword: [{ required: true, validator: validateConfirmPassword, trigger: 'blur' }],
}

async function handleRegister() {
  // Password strength check (fail fast before form validation)
  const issues = passwordInput.value?.validation.issues ?? []
  if (issues.length > 0) {
    ElMessage.error(t('auth.password_requirements'))
    return
  }

  await formRef.value?.validate(async (valid) => {
    if (!valid) return

    const password = passwordInput.value!.password

    // Double-check that both passwords match
    if (password !== form.confirmPassword) {
      ElMessage.error(t('auth.password_mismatch'))
      return
    }

    loading.value = true
    try {
      // Parents/teachers have no grade concept; submit a placeholder to avoid backend required field failure
      const payload = {
        email: form.email,
        password,
        nickname: form.nickname,
        grade: form.role === 'student' ? form.grade : (form.grade || '—'),
        role: form.role,
      }
      await authStore.register(payload)
      // Clear all sensitive data before redirecting
      await clearSensitiveData()

      // Redirect to role-specific home after successful registration
      // User is already auto-logged in
      const role = form.role
      let redirectPath = '/'
      if (role === 'admin') {
        redirectPath = '/admin/dashboard'
      } else if (role === 'teacher' || role === 'parent') {
        redirectPath = '/monitor'
      }

      router.push(redirectPath)
    } catch (error) {
      console.error('[Register] Registration failed:', error)
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.role-group :deep(.el-radio-button) {
  flex: 1;
}
.role-group :deep(.el-radio-button__inner) {
  width: 100%;
}
</style>

