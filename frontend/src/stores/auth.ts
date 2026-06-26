import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import { ElMessage } from 'element-plus'

export interface User {
  id: number
  email: string
  nickname: string
  grade: string
  role: string   // student / teacher / parent
  phone?: string | null
  gender?: string | null
  age?: number | null
  avatar_url: string | null
  created_at?: string
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<User | null>(JSON.parse(localStorage.getItem('user') || 'null'))

  const isAuthenticated = computed(() => !!token.value)

  async function login(email: string, password: string) {
    const res: any = await authApi.login({ email, password })
    token.value = res.data.access_token
    user.value = res.data.user
    localStorage.setItem('token', res.data.access_token)
    localStorage.setItem('user', JSON.stringify(res.data.user))
  }

  async function register(data: { email: string; password: string; nickname: string; grade: string; role?: string }) {
    await authApi.register(data)
    ElMessage.success('注册成功，请登录')
  }

  async function fetchMe() {
    const res: any = await authApi.getMe()
    user.value = res.data
    localStorage.setItem('user', JSON.stringify(res.data))
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return { token, user, isAuthenticated, login, register, fetchMe, logout }
})
