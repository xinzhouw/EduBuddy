<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 p-4">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <div class="text-5xl mb-2">📚</div>
        <h1 class="text-3xl font-bold text-gray-900">EduBuddy</h1>
        <p class="text-gray-500 mt-2">重置密码</p>
      </div>

      <div class="bg-white rounded-lg shadow-md p-8">
        <!-- 步骤 1: 输入邮箱 -->
        <div v-if="step === 1">
          <h2 class="text-xl font-bold text-gray-900 mb-4">输入你的邮箱地址</h2>
          <p class="text-gray-600 text-sm mb-6">我们会向你的邮箱发送验证码</p>

          <el-form :model="form" :rules="rules" ref="formRef">
            <el-form-item prop="email">
              <el-input
                v-model="form.email"
                placeholder="邮箱地址"
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
              {{ loading ? '正在发送...' : '发送验证码' }}
            </el-button>
          </el-form>

          <p class="text-center text-gray-500 mt-6 text-xs sm:text-sm">
            已有账号？
            <RouterLink to="/login" class="text-blue-500 hover:text-blue-600 font-medium">返回登录</RouterLink>
          </p>
        </div>

        <!-- 步骤 2: 输入验证码和新密码 -->
        <div v-if="step === 2">
          <h2 class="text-xl font-bold text-gray-900 mb-4">重置密码</h2>
          <p class="text-gray-600 text-sm mb-6">
            验证码已发送至 <span class="font-semibold">{{ form.email }}</span>
          </p>

          <el-form :model="form" :rules="resetRules" ref="resetFormRef">
            <el-form-item prop="code">
              <el-input
                v-model="form.code"
                placeholder="6位验证码"
                size="large"
                maxlength="6"
                prefix-icon="Key"
                clearable
              />
            </el-form-item>

            <el-form-item prop="newPassword">
              <el-input
                v-model="form.newPassword"
                placeholder="新密码"
                size="large"
                type="password"
                show-password
                prefix-icon="Lock"
              />
            </el-form-item>

            <el-form-item prop="confirmPassword">
              <el-input
                v-model="form.confirmPassword"
                placeholder="确认密码"
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
              {{ loading ? '正在重置...' : '重置密码' }}
            </el-button>
          </el-form>

          <el-button
            type="text"
            class="w-full mt-4"
            @click="step = 1"
          >
            返回
          </el-button>
        </div>

        <!-- 步骤 3: 成功 -->
        <div v-if="step === 3" class="text-center">
          <div class="text-6xl mb-4">✅</div>
          <h2 class="text-xl font-bold text-gray-900 mb-2">密码重置成功</h2>
          <p class="text-gray-600 mb-6">你可以用新密码登录了</p>

          <RouterLink to="/login">
            <el-button type="primary" size="large" class="w-full h-11">
              返回登录
            </el-button>
          </RouterLink>
        </div>
      </div>

      <!-- 错误提示 -->
      <el-dialog
        v-model="errorDialogVisible"
        title="错误"
        width="90%"
      >
        <p class="text-gray-700">{{ errorMessage }}</p>
        <template #footer>
          <el-button type="primary" @click="errorDialogVisible = false">
            确定
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

const router = useRouter()
const formRef = ref<FormInstance>()
const resetFormRef = ref<FormInstance>()
const loading = ref(false)
const step = ref(1) // 1: 输入邮箱, 2: 输入验证码和密码, 3: 成功
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
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ]
}

const resetRules = {
  code: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { min: 6, max: 6, message: '验证码为6位', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码至少8个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== form.newPassword) {
          callback(new Error('两次输入密码不一致'))
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
      ElMessage.success('验证码已发送到邮箱')
      step.value = 2
    } catch (error: any) {
      errorMessage.value = error.response?.data?.detail?.message || '发送验证码失败'
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
      ElMessage.success('密码重置成功，请登录')
      setTimeout(() => {
        router.push('/login')
      }, 2000)
    } catch (error: any) {
      errorMessage.value = error.response?.data?.detail?.message || '重置密码失败'
      errorDialogVisible.value = true
    } finally {
      loading.value = false
    }
  })
}
</script>
