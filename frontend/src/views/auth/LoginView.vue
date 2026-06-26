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

        <el-form :model="form" :rules="rules" ref="formRef" @submit.prevent="handleLogin" class="space-y-4">
          <el-form-item prop="email">
            <el-input
              v-model="form.email"
              placeholder="邮箱地址"
              size="large"
              type="email"
              prefix-icon="Message"
              clearable
              :autocomplete="shouldDisableAutocomplete ? 'off' : 'email'"
              class="h-12"
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              placeholder="密码"
              size="large"
              type="password"
              show-password
              prefix-icon="Lock"
              @keyup.enter="handleLogin"
              clearable
              :autocomplete="shouldDisableAutocomplete ? 'off' : 'current-password'"
              class="h-12"
            />
          </el-form-item>

          <el-button
            type="primary"
            size="large"
            class="w-full h-12 text-base font-semibold rounded-lg"
            :loading="loading"
            @click="handleLogin"
            :disabled="retryCountdown > 0"
          >
            {{ retryCountdown > 0 ? `登 录 (${retryCountdown}s)` : '登 录' }}
          </el-button>

          <div class="text-center pt-2">
            <RouterLink
              to="/forgot-password"
              class="text-blue-500 hover:text-blue-600 text-sm font-medium inline-flex items-center gap-1 transition-colors"
            >
              <span>🔑</span>
              <span>忘记密码？</span>
            </RouterLink>
          </div>
        </el-form>

        <!-- 错误对话框 -->
        <el-dialog
          v-model="errorDialogVisible"
          :title="errorTitle"
          width="90%"
          max-width="450px"
          :close-on-click-modal="false"
          :close-on-press-escape="false"
          class="error-dialog-wrapper"
          align-center
        >
          <template #header>
            <div class="w-full">
              <div class="flex items-center gap-3 mb-2">
                <div class="text-3xl" :class="getIconByErrorCode">
                  {{ getEmojiByErrorCode }}
                </div>
                <div class="flex-1">
                  <h3 class="text-lg font-bold text-gray-900">{{ errorTitle }}</h3>
                </div>
              </div>
            </div>
          </template>

          <div class="space-y-4">
            <!-- 主要错误消息 -->
            <p class="text-gray-700 text-base leading-relaxed">{{ errorMessage }}</p>

            <!-- 倒计时提示 -->
            <div v-if="retryCountdown > 0" class="bg-amber-50 border border-amber-200 rounded-lg p-4">
              <div class="flex items-center gap-3">
                <div class="text-2xl">⏳</div>
                <div class="flex-1">
                  <p class="text-sm font-semibold text-amber-900">请稍候</p>
                  <p class="text-sm text-amber-700">
                    <span class="font-bold text-lg text-amber-600">{{ retryCountdown }}</span> 秒后重试
                  </p>
                </div>
              </div>
            </div>

            <!-- 建议操作 -->
            <div v-if="errorSuggestion" class="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div class="flex gap-3">
                <span class="text-xl">💡</span>
                <p class="text-sm text-blue-900">{{ errorSuggestion }}</p>
              </div>
            </div>

            <!-- 忘记密码链接 -->
            <div v-if="showForgotPasswordLink" class="pt-2">
              <RouterLink
                to="/forgot-password"
                @click="closeErrorDialog"
                class="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-lg text-blue-600 hover:text-blue-700 text-sm font-medium transition-all w-full justify-center"
              >
                <span>🔑</span>
                <span>前往重置密码</span>
              </RouterLink>
            </div>
          </div>

          <template #footer>
            <div class="flex gap-2 w-full">
              <el-button
                v-if="showForgotPasswordLink"
                plain
                @click="closeErrorDialog"
                class="flex-1"
              >
                关闭
              </el-button>
              <el-button
                type="primary"
                @click="closeErrorDialog"
                :class="{ 'flex-1': showForgotPasswordLink, 'w-full': !showForgotPasswordLink }"
              >
                确定
              </el-button>
            </div>
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
import { ref, reactive, onMounted, nextTick, onBeforeUnmount, computed } from 'vue'
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
const showForgotPasswordLink = ref(false)
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
  showForgotPasswordLink.value = errorInfo.showForgotPasswordLink || false
  errorDialogVisible.value = true

  // 如果是速率限制错误，启动倒计时
  if (errorCode === 'RATE_LIMIT_EXCEEDED' && retryAfter) {
    retryCountdown.value = retryAfter
    disableLoginButtonWithCountdown(retryAfter)
  }
}

function disableLoginButtonWithCountdown(seconds: number) {
  if (countdownInterval.value) {
    clearInterval(countdownInterval.value)
  }

  countdownInterval.value = setInterval(() => {
    retryCountdown.value--
    if (retryCountdown.value <= 0) {
      clearInterval(countdownInterval.value!)
      countdownInterval.value = null
      loading.value = false
      retryCountdown.value = 0
    }
  }, 1000)
}

function closeErrorDialog() {
  errorDialogVisible.value = false
}

const getEmojiByErrorCode = computed(() => {
  if (retryCountdown.value > 0) return '⏱️'
  if (showForgotPasswordLink.value) return '🔑'
  if (errorTitle.value.includes('禁用')) return '🔒'
  if (errorTitle.value.includes('锁定')) return '🔐'
  return '⚠️'
})

const getIconByErrorCode = computed(() => {
  if (retryCountdown.value > 0) return 'text-amber-500'
  if (showForgotPasswordLink.value) return 'text-blue-500'
  if (errorTitle.value.includes('禁用')) return 'text-red-500'
  if (errorTitle.value.includes('锁定')) return 'text-red-500'
  return 'text-gray-500'
})

onBeforeUnmount(() => {
  if (countdownInterval.value) {
    clearInterval(countdownInterval.value)
    countdownInterval.value = null
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
      const errorCode = error.response?.data?.detail?.error_code || 'NETWORK_ERROR'
      const retryAfter = error.response?.data?.detail?.retry_after
      showErrorDialog(errorCode, retryAfter)
    }
  })
}
</script>
