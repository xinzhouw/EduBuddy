<template>
  <el-dialog
    v-model="visible"
    :title="$t('change_password.title')"
    width="400px"
    @close="handleDialogClose"
  >
    <el-form :model="form" ref="formRef">
      <!-- Old password -->
      <el-form-item :label="$t('change_password.old_password')" prop="oldPassword">
        <el-input
          v-model="form.oldPassword"
          type="password"
          :show-password="true"
          :placeholder="$t('change_password.old_password_placeholder')"
          autocomplete="off"
        />
      </el-form-item>

      <!-- New password (live validation) -->
      <el-form-item :label="$t('change_password.new_password')" prop="newPassword">
        <PasswordInput ref="passwordInput" />
      </el-form-item>

      <!-- Confirm new password -->
      <el-form-item :label="$t('change_password.confirm_password')" prop="confirmPassword">
        <el-input
          v-model="form.confirmPassword"
          type="password"
          :show-password="true"
          :placeholder="$t('change_password.confirm_password_placeholder')"
          autocomplete="new-password"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">{{ $t('change_password.cancel_btn') }}</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        {{ $t('change_password.submit_btn') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import PasswordInput from '@/components/PasswordInput.vue'
import api from '@/api'

const { t } = useI18n()

const visible = ref(false)
const loading = ref(false)
const passwordInput = ref()
const formRef = ref()

const form = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

async function resetForm() {
  form.value = {
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  }

  // Clear all password fields in the DOM
  await nextTick()
  const passwordInputs = document.querySelectorAll('input[type="password"]')
  passwordInputs.forEach(input => {
    const el = input as HTMLInputElement
    el.value = ''
    el.dispatchEvent(new Event('input', { bubbles: true }))
  })

  passwordInput.value?.reset()
  formRef.value?.clearValidate()
}

async function handleDialogClose() {
  // Clear all sensitive data when dialog closes
  await resetForm()
}

async function handleSubmit() {
  // Validate old password is not empty
  if (!form.value.oldPassword) {
    ElMessage.error(t('change_password.old_password_required'))
    return
  }

  // Validate new password strength
  if (passwordInput.value!.validation.issues.length > 0) {
    ElMessage.error(t('change_password.new_password_invalid'))
    return
  }

  // Validate new passwords match
  if (passwordInput.value!.password !== form.value.confirmPassword) {
    ElMessage.error(t('change_password.password_mismatch'))
    return
  }

  loading.value = true
  try {
    await api.post('/auth/change-password', {
      old_password: form.value.oldPassword,
      new_password: passwordInput.value!.password
    })
    ElMessage.success(t('change_password.success'))
    visible.value = false
    await resetForm()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || t('change_password.failed'))
  } finally {
    loading.value = false
  }
}

async function clearAutofill() {
  // Wait for browser password manager autofill to complete
  await new Promise(resolve => setTimeout(resolve, 100))

  const oldPasswordInput = document.querySelector(`input[placeholder="${t('change_password.old_password_placeholder')}"]`) as HTMLInputElement
  if (oldPasswordInput && oldPasswordInput.value) {
    oldPasswordInput.value = ''
    oldPasswordInput.dispatchEvent(new Event('input', { bubbles: true }))
    form.value.oldPassword = ''
  }
}

defineExpose({
  async open() {
    visible.value = true
    await clearAutofill()
  },
  close() {
    visible.value = false
  }
})
</script>
