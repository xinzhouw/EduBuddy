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
    <div class="flex-1 flex items-center justify-center p-8">
      <div class="w-full max-w-md">
        <div class="text-center mb-8">
          <h2 class="text-2xl font-bold text-gray-900">欢迎回来！</h2>
          <p class="text-gray-500 mt-2">登录你的 EduBuddy 账号</p>
        </div>

        <el-form :model="form" :rules="rules" ref="formRef" @submit.prevent="handleLogin">
          <el-form-item prop="email">
            <el-input v-model="form.email" placeholder="邮箱地址" size="large" type="email" prefix-icon="Message" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="form.password" placeholder="密码" size="large" type="password" show-password prefix-icon="Lock" @keyup.enter="handleLogin" />
          </el-form-item>
          <el-button type="primary" size="large" class="w-full mt-2" :loading="loading" @click="handleLogin">
            登 录
          </el-button>
        </el-form>

        <p class="text-center text-gray-500 mt-6 text-sm">
          还没有账号？
          <RouterLink to="/register" class="text-blue-500 hover:text-blue-600 font-medium">立即注册</RouterLink>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import type { FormInstance } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({ email: '', password: '' })
const rules = {
  email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }, { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  await formRef.value?.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await authStore.login(form.email, form.password)
      router.push('/')
    } catch {
    } finally {
      loading.value = false
    }
  })
}
</script>
