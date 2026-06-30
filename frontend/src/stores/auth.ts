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
    console.log('[Auth Store] login() 开始', { email })
    try {
      const res: any = await authApi.login({ email, password })
      console.log('[Auth Store] 登录 API 响应', {
        statusOk: res.code === 200 || res.data?.code === 200,
        hasData: !!res.data,
        hasAccessToken: !!res.data?.access_token,
        hasUser: !!res.data?.user
      })

      const authData = res.data

      if (!authData) {
        console.error('[Auth Store] 响应中缺少 data 字段', res)
        throw new Error('响应中缺少 data 字段')
      }

      if (!authData.access_token) {
        console.error('[Auth Store] 响应中缺少 access_token', authData)
        throw new Error('响应中缺少 access_token')
      }

      if (!authData.user) {
        console.error('[Auth Store] 响应中缺少 user', authData)
        throw new Error('响应中缺少 user')
      }

      token.value = authData.access_token
      user.value = authData.user

      console.log('[Auth Store] 保存到 localStorage')
      localStorage.setItem('token', authData.access_token)
      localStorage.setItem('user', JSON.stringify(authData.user))

      console.log('[Auth Store] 登录成功完成', {
        tokenLength: authData.access_token.length,
        userId: authData.user.id,
        userRole: authData.user.role
      })
    } catch (error) {
      console.error('[Auth Store] login() 异常', error)
      throw error
    }
  }

  async function register(data: { email: string; password: string; nickname: string; grade: string; role?: string }) {
    const res: any = await authApi.register(data)
    const authData = res.data
    token.value = authData.access_token
    user.value = authData.user
    localStorage.setItem('token', authData.access_token)
    localStorage.setItem('user', JSON.stringify(authData.user))
    ElMessage.success('注册成功')
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
