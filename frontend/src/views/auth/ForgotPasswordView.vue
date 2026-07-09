<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 p-4">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <div class="text-5xl mb-2">📚</div>
        <h1 class="text-3xl font-bold text-gray-900">EduBuddy</h1>
        <p class="text-gray-500 mt-2">{{ $t('auth.reset_password') }}</p>
      </div>

      <div class="bg-white rounded-lg shadow-md p-8">
        <!-- Step 1: Enter email -->
        <div v-if="step === 1">
          <h2 class="text-xl font-bold text-gray-900 mb-4">{{ $t('auth.step1_title') }}</h2>
          <p class="text-gray-600 text-sm mb-6">{{ $t('auth.step1_hint') }}</p>

          <el-form :model="form" :rules="rules" ref="formRef">
            <el-form-item prop="email">
              <el-input
                v-model="form.email"
                :placeholder="$t('auth.email')"
                size="large"
                type="email"
                prefix-icon="Message"
                clearable
              />
            </el-form-item>

            <el-button
              type="primary"
              size="large"
              class="w-full h-11"
              :loading="loading"
              @click="handleSendCode"
            >
              {{ loading ? $t('auth.sending') : $t('auth.send_code') }}
            </el-button>
          </el-form>

          <p class="text-center text-gray-500 mt-6 text-xs sm:text-sm">
            {{ $t('auth.has_account') }}
            <RouterLink to="/login" class="text-blue-500 hover:text-blue-600 font-medium">{{ $t('auth.back_to_login') }}</RouterLink>
          </p>
        </div>

        <!-- Step 2: Enter code and new password -->
        <div v-if="step === 2">
          <h2 class="text-xl font-bold text-gray-900 mb-4">{{ $t('auth.reset_password') }}</h2>
          <p class="text-gray-600 text-sm mb-6">
            {{ $t('auth.code_sent_to') }} <span class="font-semibold">{{ form.email }}</span>
          </p>

          <el-form :model="form" :rules="resetRules" ref="resetFormRef">
            <el-form-item prop="code">
              <el-input
                v-model="form.code"
                :placeholder="$t('auth.code_placeholder')"
                size="large"
                maxlength="6"
                prefix-icon="Key"
                clearable
              />
            </el-form-item>

            <el-form-item prop="newPassword">
              <el-input
                v-model="form.newPassword"
                :placeholder="$t('auth.new_password')"
                size="large"
                type="password"
                show-password
                prefix-icon="Lock"
              />
            </el-form-item>

            <el-form-item prop="confirmPassword">
              <el-input
                v-model="form.confirmPassword"
                :placeholder="$t('auth.confirm_password')"
                size="large"
                type="password"
                show-password
                prefix-icon="Lock"
                @keyup.enter="handleResetPassword"
              />
            </el-form-item>

            <el-button
              type="primary"
              size="large"
              class="w-full h-11"
              :loading="loading"
              @click="handleResetPassword"
            >
              {{ loading ? $t('auth.resetting') : $t('auth.reset_password') }}
            </el-button>
          </el-form>

          <el-button
            type="text"
            class="w-full mt-4"
            @click="handleBack"
          >
            {{ $t('common.back') }}
          </el-button>
        </div>

        <!-- Step 3: Success -->
        <div v-if="step === 3" class="text-center">
          <div class="text-6xl mb-4">✅</div>
          <h2 class="text-xl font-bold text-gray-900 mb-2">{{ $t('auth.step3_title') }}</h2>
          <p class="text-gray-600 mb-6">{{ $t('auth.step3_hint') }}</p>

          <RouterLink to="/login">
            <el-button type="primary" size="large" class="w-full h-11">
              {{ $t('auth.back_to_login') }}
            </el-button>
          </RouterLink>
        </div>
      </div>

      <!-- Error dialog -->
      <el-dialog
        v-model="errorDialogVisible"
        :title="$t('common.error')"
        width="90%"
      >
        <p class="text-gray-700">{{ errorMessage }}</p>
        <template #footer>
          <el-button type="primary" @click="errorDialogVisible = false">
            {{ $t('common.confirm') }}
          </el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { authApi } from '@/api/auth'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const router = useRouter()
const formRef = ref<FormInstance>()
const resetFormRef = ref<FormInstance>()
const loading = ref(false)
const step = ref(1) // 1: enter email, 2: enter code and password, 3: success
const errorDialogVisible = ref(false)
const errorMessage = ref('')

const form = reactive({
  email: '',
  code: '',
  newPassword: '',
  confirmPassword: ''
})

const rules = {
  email: [
    { required: true, message: t('auth.enter_email'), trigger: 'blur' },
    { type: 'email', message: t('auth.invalid_email_format'), trigger: 'blur' }
  ]
}

const resetRules = {
  code: [
    { required: true, message: t('auth.enter_code'), trigger: 'blur' },
    { min: 6, max: 6, message: t('auth.code_6_digits'), trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: t('auth.enter_new_password'), trigger: 'blur' },
    { min: 8, message: t('auth.password_min_8'), trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: t('auth.enter_confirm_password'), trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== form.newPassword) {
          callback(new Error(t('auth.password_mismatch')))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

async function handleSendCode() {
  await formRef.value?.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await authApi.forgotPassword(form.email)
      ElMessage.success(t('auth.code_sent_success'))
      form.code = ''
      form.newPassword = ''
      form.confirmPassword = ''
      step.value = 2
    } catch (error: any) {
      errorMessage.value = error.response?.data?.detail?.message || t('auth.send_code_failed')
      errorDialogVisible.value = true
    } finally {
      loading.value = false
    }
  })
}

async function handleResetPassword() {
  await resetFormRef.value?.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await authApi.resetPassword(form.email, form.code, form.newPassword)
      step.value = 3
      ElMessage.success(t('auth.reset_success'))
      setTimeout(() => {
        router.push('/login')
      }, 2000)
    } catch (error: any) {
      errorMessage.value = error.response?.data?.detail?.message || t('auth.reset_failed')
      errorDialogVisible.value = true
    } finally {
      loading.value = false
    }
  })
}

function handleBack() {
  form.code = ''
  form.newPassword = ''
  form.confirmPassword = ''
  resetFormRef.value?.clearValidate()
  step.value = 1
}
</script>
