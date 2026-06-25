<template>
  <div class="min-h-screen flex">
    <div class="hidden lg:flex w-1/2 bg-gradient-to-br from-blue-500 to-blue-700 flex-col items-center justify-center p-12 text-white">
      <div class="text-center">
        <div class="text-7xl mb-6">📚</div>
        <h1 class="text-4xl font-bold mb-4">EduBuddy</h1>
        <p class="text-xl text-blue-100">开始你的 AI 学习之旅</p>
      </div>
    </div>
    <div class="flex-1 flex items-center justify-center p-4 sm:p-8">
      <div class="w-full max-w-md">
        <!-- 移动端 Logo -->
        <div class="lg:hidden text-center mb-6">
          <div class="text-5xl mb-2">📚</div>
          <h1 class="text-2xl font-bold text-gray-900">EduBuddy</h1>
        </div>

        <div class="text-center mb-6 sm:mb-8">
          <h2 class="text-xl sm:text-2xl font-bold text-gray-900">创建账号</h2>
          <p class="text-gray-500 mt-2 text-sm sm:text-base">加入 EduBuddy，开启智能学习</p>
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
            <el-input v-model="form.nickname" placeholder="昵称" size="large" prefix-icon="User" clearable />
          </el-form-item>
          <el-form-item prop="email">
            <el-input v-model="form.email" placeholder="邮箱地址" size="large" type="email" prefix-icon="Message" clearable />
          </el-form-item>
          <el-form-item v-if="form.role === 'student'" prop="grade">
            <el-select v-model="form.grade" placeholder="选择年级" size="large" class="w-full">
              <el-option v-for="g in grades" :key="g" :label="g" :value="g" />
            </el-select>
          </el-form-item>
          <el-form-item prop="password">
            <PasswordInput ref="passwordInput" />
          </el-form-item>
          <el-form-item prop="confirmPassword">
            <el-input v-model="form.confirmPassword" placeholder="再次输入密码" size="large" type="password" show-password prefix-icon="Lock" clearable autocomplete="new-password" />
          </el-form-item>
          <el-button type="primary" size="large" class="w-full mt-2 h-11 sm:h-12" :loading="loading" @click="handleRegister">
            注 册
          </el-button>
        </el-form>
        <p class="text-center text-gray-500 mt-6 text-xs sm:text-sm">
          已有账号？
          <RouterLink to="/login" class="text-blue-500 hover:text-blue-600 font-medium">立即登录</RouterLink>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import type { FormInstance, FormItemRule } from 'element-plus'
import PasswordInput from '@/components/PasswordInput.vue'

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

  // 清空 DOM 中的所有密码字段，防止浏览器 autocomplete 残留
  await nextTick()
  const passwordInputs = document.querySelectorAll('input[type="password"]')
  passwordInputs.forEach(input => {
    const el = input as HTMLInputElement
    el.value = ''
    el.setAttribute('autocomplete', 'new-password')
  })

  // 多次清空确保浏览器 autocomplete 不会覆盖
  for (let i = 0; i < 3; i++) {
    await new Promise(resolve => setTimeout(resolve, 50))
    passwordInputs.forEach(input => {
      const el = input as HTMLInputElement
      el.value = ''
    })
  }
}

async function clearSensitiveData() {
  // 注册成功后立即清空所有敏感数据
  form.confirmPassword = ''
  passwordInput.value?.reset()

  await nextTick()
  const passwordInputs = document.querySelectorAll('input[type="password"]')
  passwordInputs.forEach(input => {
    const el = input as HTMLInputElement
    el.value = ''
  })
}
const grades = ['初一', '初二', '初三', '高一', '高二', '高三']
const roles = [
  { value: 'student', label: '学生', icon: '🎓' },
  { value: 'parent', label: '家长', icon: '👨‍👩‍👧' },
  { value: 'teacher', label: '教师', icon: '🧑‍🏫' },
]
const form = reactive({ role: 'student', nickname: '', email: '', grade: '', confirmPassword: '' })

const validateConfirmPassword = (_rule: FormItemRule, value: string, callback: (err?: Error) => void) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== passwordInput.value?.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const validateGrade = (_rule: FormItemRule, value: string, callback: (err?: Error) => void) => {
  // 仅学生需要选择年级，家长/教师无需填写
  if (form.role === 'student' && !value) {
    callback(new Error('请选择年级'))
  } else {
    callback()
  }
}

const validatePassword = (_rule: FormItemRule, _value: unknown, callback: (err?: Error) => void) => {
  const issues = passwordInput.value?.validation.issues ?? []
  if (!passwordInput.value?.password) {
    callback(new Error('请输入密码'))
  } else if (issues.length > 0) {
    callback(new Error(issues[0]))
  } else {
    callback()
  }
}

const rules = {
  nickname: [{ required: true, message: '请输入昵称', trigger: 'blur' }],
  email: [{ required: true, type: 'email', message: '请输入有效邮箱', trigger: 'blur' }],
  grade: [{ validator: validateGrade, trigger: 'change' }],
  password: [{ validator: validatePassword, trigger: 'blur' }],
  confirmPassword: [{ required: true, validator: validateConfirmPassword, trigger: 'blur' }],
}

async function handleRegister() {
  // 密码强度检查（在表单校验之前快速失败）
  const issues = passwordInput.value?.validation.issues ?? []
  if (issues.length > 0) {
    ElMessage.error('密码不符合要求')
    return
  }

  await formRef.value?.validate(async (valid) => {
    if (!valid) return

    const password = passwordInput.value!.password

    // 再次确认两次密码一致
    if (password !== form.confirmPassword) {
      ElMessage.error('两次输入的密码不一致')
      return
    }

    loading.value = true
    try {
      // 家长/教师没有年级概念，提交一个占位值，避免后端必填校验失败
      const payload = {
        email: form.email,
        password,
        nickname: form.nickname,
        grade: form.role === 'student' ? form.grade : (form.grade || '—'),
        role: form.role,
      }
      await authStore.register(payload)
      // 在跳转前清空所有敏感数据
      await clearSensitiveData()
      router.push('/login')
    } catch {
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

