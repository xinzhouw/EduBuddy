import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000, // 增加到 60 秒以支持弱网环境
})

// 不需要登录态的白名单接口（避免退出登录后误判）
const PUBLIC_PATHS = ['/auth/login', '/auth/register', '/auth/password/validate']

function isPublicPath(url?: string) {
  if (!url) return false
  return PUBLIC_PATHS.some((p) => url.includes(p))
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

// 响应拦截器：统一错误处理
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
  (error) => {
    // 请求被主动取消（如未登录时拦截），静默忽略，不弹任何提示
    if (axios.isCancel?.(error) || error.code === 'ERR_CANCELED' || error.name === 'CanceledError') {
      return Promise.reject(error)
    }

    const status = error.response?.status
    const message = error.response?.data?.detail || error.message || '请求失败'

    // 401（Token 无效/过期）均视为登录态失效：
    // 静默清理登录信息并跳转登录页，不弹出错误提示。
    const isAuthError = status === 401

    if (isAuthError) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      // 已在登录页则不重复跳转，避免循环
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
