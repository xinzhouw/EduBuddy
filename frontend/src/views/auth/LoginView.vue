<template>
  <div class="min-h-screen flex">
    <!-- 左侧品牌区 -->
    <div class="hidden lg:flex w-1/2 bg-gradient-to-br from-blue-500 to-blue-700 flex-col items-center justify-center p-12 text-white">
      <div class="text-center">
        <div class="text-7xl mb-6">📚</div>
        <h1 class="text-4xl font-bold mb-4">EduBuddy</h1>
        <p class="text-xl text-blue-100 mb-8">AI 驱动的个性化学习助手</p>
        <div class="grid grid-cols-2 gap-4 text-sm text-blue-100">
          <div class="flex items-center gap-2"><span>🤖</span><span>AI 即时解题</span></div>
          <div class="flex items-center gap-2"><span>📝</span><span>智能笔记管理</span></div>
          <div class="flex items-center gap-2"><span>📚</span><span>练习题生成</span></div>
          <div class="flex items-center gap-2"><span>❌</span><span>错题间隔复习</span></div>
        </div>
      </div>
    </div>

    <!-- 右侧登录表单 -->
    <div class="flex-1 flex items-center justify-center p-4 sm:p-8">
      <div class="w-full max-w-md">
        <!-- 移动端 Logo -->
        <div class="lg:hidden text-center mb-6">
          <div class="text-5xl mb-2">📚</div>
          <h1 class="text-2xl font-bold text-gray-900">EduBuddy</h1>
        </div>

        <div class="text-center mb-6 sm:mb-8">
          <h2 class="text-xl sm:text-2xl font-bold text-gray-900">欢迎回来！</h2>
          <p class="text-gray-500 mt-2 text-sm sm:text-base">登录你的 EduBuddy 账号</p>
        </div>

        <el-form :model="form" :rules="rules" ref="formRef" @submit.prevent="handleLogin">
          <el-form-item prop="email">
            <el-input v-model="form.email" placeholder="邮箱地址" size="large" type="email" prefix-icon="Message" clearable :autocomplete="shouldDisableAutocomplete ? 'off' : 'email'" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="form.password" placeholder="密码" size="large" type="password" show-password prefix-icon="Lock" @keyup.enter="handleLogin" clearable :autocomplete="shouldDisableAutocomplete ? 'off' : 'current-password'" />
          </el-form-item>
          <el-button
            type="primary"
            size="large"
            class="w-full mt-2 h-11 sm:h-12"
            :loading="loading"
            @click="handleLogin"
            :disabled="retryCountdown > 0"
          >
            {{ retryCountdown > 0 ? `登 录 (${retryCountdown}s)` : '登 录' }}
          </el-button>
        </el-form>

        <!-- 错误对话框 -->
        <el-dialog
          v-model="errorDialogVisible"
          :title="errorTitle"
          width="90%"
          :close-on-click-modal="false"
          :close-on-press-escape="false"
        >
          <div class="space-y-4">
            <p class="text-gray-700">{{ errorMessage }}</p>

            <!-- 倒计时提示 -->
            <p v-if="retryCountdown > 0" class="text-sm text-orange-600">
              请在 <span class="font-bold">{{ retryCountdown }}</span> 秒后重试
            </p>

            <!-- 建议操作 -->
            <p v-if="errorSuggestion" class="text-sm text-gray-600">
              💡 {{ errorSuggestion }}
            </p>
          </div>

          <template #footer>
            <el-button type="primary" @click="closeErrorDialog">
              确定
            </el-button>
          </template>
        </el-dialog>

        <p class="text-center text-gray-500 mt-6 text-xs sm:text-sm">
          还没有账号？
          <RouterLink to="/register" class="text-blue-500 hover:text-blue-600 font-medium">立即注册</RouterLink>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { LOGIN_ERROR_MESSAGES } from '@/utils/errorMessages'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const formRef = ref<FormInstance>()
const loading = ref(false)
const errorDialogVisible = ref(false)
const errorTitle = ref('')
const errorMessage = ref('')
const errorSuggestion = ref<string | null>(null)
const retryCountdown = ref(0)
const countdownInterval = ref<NodeJS.Timeout | null>(null)
const shouldDisableAutocomplete = ref(false)

const form = reactive({ email: '', password: '' })

onMounted(async () => {
  const shouldClearCredentials = route.query.clearCredentials === 'true'

  if (shouldClearCredentials) {
    shouldDisableAutocomplete.value = true
  }

  await nextTick()

  form.email = ''
  form.password = ''
  formRef.value?.clearValidate()

  const emailInput = document.querySelector('input[type="email"]') as HTMLInputElement
  const passwordInput = document.querySelector('input[type="password"]') as HTMLInputElement
  if (emailInput) emailInput.value = ''
  if (passwordInput) passwordInput.value = ''

  if (shouldClearCredentials) {
    setTimeout(() => {
      if (emailInput) emailInput.value = ''
      if (passwordInput) passwordInput.value = ''
      form.email = ''
      form.password = ''
    }, 150)
  }
})
const rules = {
  email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }, { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

function showErrorDialog(errorCode: string, retryAfter?: number) {
  const errorInfo = LOGIN_ERROR_MESSAGES[errorCode] || LOGIN_ERROR_MESSAGES.SERVER_ERROR
  errorTitle.value = errorInfo.title
  errorMessage.value = errorInfo.message
  errorSuggestion.value = errorInfo.suggestion
  errorDialogVisible.value = true

  // 如果是速率限制错误，启动倒计时
  if (errorCode === 'RATE_LIMIT_EXCEEDED' && retryAfter) {
    retryCountdown.value = retryAfter
    disableLoginButtonWithCountdown(retryAfter)
  }
}

function disableLoginButtonWithCountdown(seconds: number) {
  loading.value = true

  if (countdownInterval.value) {
    clearInterval(countdownInterval.value)
  }

  countdownInterval.value = setInterval(() => {
    retryCountdown.value--
    if (retryCountdown.value <= 0) {
      clearInterval(countdownInterval.value!)
      loading.value = false
      retryCountdown.value = 0
    }
  }, 1000)
}

function closeErrorDialog() {
  errorDialogVisible.value = false
}

onBeforeUnmount(() => {
  if (countdownInterval.value) {
    clearInterval(countdownInterval.value)
  }
})

async function handleLogin() {
  await formRef.value?.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await authStore.login(form.email, form.password)
      // 登录成功，显示成功消息并跳转
      ElMessage.success('登录成功')
      const role = authStore.user?.role
      if (role === 'admin') {
        router.push('/admin/dashboard')
      } else {
        router.push('/')
      }
    } catch (error: any) {
      loading.value = false
      const errorCode = error.response?.data?.error_code || 'NETWORK_ERROR'
      const retryAfter = error.response?.data?.retry_after
      showErrorDialog(errorCode, retryAfter)
    }
  })
}
</script>
