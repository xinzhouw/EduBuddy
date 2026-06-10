<template>
  <div class="min-h-screen flex">
    <div class="hidden lg:flex w-1/2 bg-gradient-to-br from-blue-500 to-blue-700 flex-col items-center justify-center p-12 text-white">
      <div class="text-center">
        <div class="text-7xl mb-6">📚</div>
        <h1 class="text-4xl font-bold mb-4">EduBuddy</h1>
        <p class="text-xl text-blue-100">开始你的 AI 学习之旅</p>
      </div>
    </div>
    <div class="flex-1 flex items-center justify-center p-8">
      <div class="w-full max-w-md">
        <div class="text-center mb-8">
          <h2 class="text-2xl font-bold text-gray-900">创建账号</h2>
          <p class="text-gray-500 mt-2">加入 EduBuddy，开启智能学习</p>
        </div>
        <el-form :model="form" :rules="rules" ref="formRef">
          <el-form-item prop="role">
            <el-radio-group v-model="form.role" size="large" class="w-full role-group">
              <el-radio-button v-for="r in roles" :key="r.value" :value="r.value">
                {{ r.icon }} {{ r.label }}
              </el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item prop="nickname">
            <el-input v-model="form.nickname" placeholder="昵称" size="large" prefix-icon="User" />
          </el-form-item>
          <el-form-item prop="email">
            <el-input v-model="form.email" placeholder="邮箱地址" size="large" type="email" prefix-icon="Message" />
          </el-form-item>
          <el-form-item v-if="form.role === 'student'" prop="grade">
            <el-select v-model="form.grade" placeholder="选择年级" size="large" class="w-full">
              <el-option v-for="g in grades" :key="g" :label="g" :value="g" />
            </el-select>
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="form.password" placeholder="密码（至少6位）" size="large" type="password" show-password prefix-icon="Lock" />
          </el-form-item>
          <el-form-item prop="confirmPassword">
            <el-input v-model="form.confirmPassword" placeholder="再次输入密码" size="large" type="password" show-password prefix-icon="Lock" />
          </el-form-item>
          <el-button type="primary" size="large" class="w-full mt-2" :loading="loading" @click="handleRegister">
            注 册
          </el-button>
        </el-form>
        <p class="text-center text-gray-500 mt-6 text-sm">
          已有账号？
          <RouterLink to="/login" class="text-blue-500 hover:text-blue-600 font-medium">立即登录</RouterLink>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import type { FormInstance, FormItemRule } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref<FormInstance>()
const loading = ref(false)
const grades = ['初一', '初二', '初三', '高一', '高二', '高三']
const roles = [
  { value: 'student', label: '学生', icon: '🎓' },
  { value: 'parent', label: '家长', icon: '👨‍👩‍👧' },
  { value: 'teacher', label: '教师', icon: '🧑‍🏫' },
]
const form = reactive({ role: 'student', nickname: '', email: '', grade: '', password: '', confirmPassword: '' })

const validateConfirmPassword = (_rule: FormItemRule, value: string, callback: (err?: Error) => void) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== form.password) {
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

const rules = {
  nickname: [{ required: true, message: '请输入昵称', trigger: 'blur' }],
  email: [{ required: true, type: 'email', message: '请输入有效邮箱', trigger: 'blur' }],
  grade: [{ validator: validateGrade, trigger: 'change' }],
  password: [{ required: true, min: 6, message: '密码至少6位', trigger: 'blur' }],
  confirmPassword: [{ required: true, validator: validateConfirmPassword, trigger: 'blur' }],
}

async function handleRegister() {
  await formRef.value?.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      // 家长/教师没有年级概念，提交一个占位值，避免后端必填校验失败
      const payload = { ...form, grade: form.role === 'student' ? form.grade : (form.grade || '—') }
      await authStore.register(payload)
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

