import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useAuthStore } from './auth'

export const useLanguageStore = defineStore('language', () => {
  const currentLanguage = ref<'zh' | 'en'>('zh')

  const isSupportedLanguage = (lang: unknown): lang is 'zh' | 'en' => {
    return lang === 'zh' || lang === 'en'
  }

  const persistUserLanguage = (lang: 'zh' | 'en', userData?: unknown) => {
    const authStore = useAuthStore()
    const userFromResponse = (userData && typeof userData === 'object' && 'user' in userData
      ? (userData as { user?: unknown }).user
      : userData) as Record<string, unknown> | undefined

    const nextUser = userFromResponse && typeof userFromResponse === 'object'
      ? userFromResponse
      : authStore.user

    if (!nextUser) return

    const updatedUser = { ...nextUser, language: lang }
    authStore.user = updatedUser as typeof authStore.user
    localStorage.setItem('user', JSON.stringify(updatedUser))
  }

  /**
   * 设置语言：更新状态、本地存储、后端偏好
   */
  const setLanguage = async (lang: 'zh' | 'en') => {
    currentLanguage.value = lang
    localStorage.setItem('language', lang)

    // 如果已登录，同步到后端
    const authStore = useAuthStore()
    if (authStore.isAuthenticated) {
      try {
        // 延迟导入以避免循环依赖
        const { updateUserLanguagePreference } = await import('@/api/user')
        const response = await updateUserLanguagePreference(lang)
        persistUserLanguage(lang, response?.data)
      } catch (error) {
        console.error('Failed to update language preference:', error)
        // 失败时仍保持前端切换，并同步本地用户缓存，避免刷新后回退到旧语言
        persistUserLanguage(lang)
      }
    }
  }

  /**
   * 初始化语言：从后端或本地恢复
   */
  const initLanguage = async () => {
    const authStore = useAuthStore()
    const saved = localStorage.getItem('language') as 'zh' | 'en' | null

    if (authStore.isAuthenticated && authStore.user) {
      // 已登录：优先使用本地最近一次切换的语言，避免 localStorage.user 中的旧偏好导致刷新回退
      const userLang = (authStore.user as any).language
      const nextLanguage = isSupportedLanguage(saved)
        ? saved
        : isSupportedLanguage(userLang)
          ? userLang
          : 'zh'

      currentLanguage.value = nextLanguage
      localStorage.setItem('language', nextLanguage)
    } else {
      // 未登录：从 localStorage 读取
      currentLanguage.value = isSupportedLanguage(saved) ? saved : 'zh'
    }
  }

  return {
    currentLanguage,
    setLanguage,
    initLanguage
  }
})
