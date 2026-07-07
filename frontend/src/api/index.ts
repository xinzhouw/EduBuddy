import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000, // 增加到 60 秒以支持弱网环境
})

// 不需要登录态的白名单接口（避免退出登录后误判）
const PUBLIC_PATHS = ['/auth/login', '/auth/register', '/auth/password/validate', '/auth/refresh', '/auth/forgot-password', '/auth/reset-password']

function isPublicPath(url?: string) {
  if (!url) return false
  return PUBLIC_PATHS.some((p) => url.includes(p))
}

// Token 刷新锁，防止并发请求时多次刷新
let isRefreshing = false
let refreshSubscribers: Array<(token: string) => void> = []

function subscribeTokenRefresh(callback: (token: string) => void) {
  refreshSubscribers.push(callback)
}

function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach((callback) => callback(token))
  refreshSubscribers = []
}

// 请求拦截器：自动添加 Token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  } else if (!isPublicPath(config.url)) {
    // 未登录（或已退出登录）时，直接取消需要鉴权的请求，
    // 避免发出无 Authorization 头的请求导致后端返回 "Not authenticated"
    const controller = new AbortController()
    config.signal = controller.signal
    controller.abort()
  }
  return config
})

// 响应拦截器：统一错误处理 + Token 自动刷新
api.interceptors.response.use(
  (response) => {
    if (response.config.url?.includes('/auth/login') || response.config.url?.includes('/auth/register')) {
      console.log('[API] Auth endpoint response:', {
        url: response.config.url,
        status: response.status,
        dataKeys: Object.keys(response.data),
        hasNestedData: !!response.data.data
      })
    }
    return response.data
  },
  async (error) => {
    // 请求被主动取消（如未登录时拦截），静默忽略，不弹任何提示
    if (axios.isCancel?.(error) || error.code === 'ERR_CANCELED' || error.name === 'CanceledError') {
      return Promise.reject(error)
    }

    const status = error.response?.status
    const message = error.response?.data?.detail || error.message || '请求失败'
    const originalRequest = error.config

    // 如果是 401 错误且不是刷新 Token 的请求，尝试刷新 Token
    if (status === 401 && !isPublicPath(originalRequest.url)) {
      if (!isRefreshing) {
        isRefreshing = true
        const refreshToken = localStorage.getItem('refresh_token')

        if (refreshToken) {
          try {
            // 调用刷新 Token 接口
            const response = await axios.post('/api/auth/refresh', { refresh_token: refreshToken })
            const newAccessToken = response.data.data.access_token
            const newRefreshToken = response.data.data.refresh_token

            // 保存新 Token
            localStorage.setItem('token', newAccessToken)
            localStorage.setItem('refresh_token', newRefreshToken)

            // 更新当前请求的 Authorization header
            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`

            isRefreshing = false
            // 通知所有等待的请求
            onTokenRefreshed(newAccessToken)

            // 重新发送原始请求
            return api(originalRequest)
          } catch (refreshError) {
            isRefreshing = false
            // 刷新失败，清空登录信息并跳转
            localStorage.removeItem('token')
            localStorage.removeItem('refresh_token')
            localStorage.removeItem('user')
            if (window.location.pathname !== '/login') {
              window.location.href = '/login'
            }
            return Promise.reject(refreshError)
          }
        } else {
          isRefreshing = false
          // 没有刷新令牌，清空登录信息
          localStorage.removeItem('token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('user')
          if (window.location.pathname !== '/login') {
            window.location.href = '/login'
          }
          return Promise.reject(error)
        }
      } else {
        // 如果正在刷新，等待刷新完成后重试
        return new Promise((resolve) => {
          subscribeTokenRefresh((token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            resolve(api(originalRequest))
          })
        })
      }
    }

    // 其他 401 错误（如刷新令牌无效）
    if (status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    } else if (isPublicPath(error.config?.url)) {
      // 对于登录/注册等公开路由，跳过自动错误提示，由调用方负责 UI
    } else if (status !== 422) {
      ElMessage.error(message)
    }
    return Promise.reject(error)
  }
)

export default api
