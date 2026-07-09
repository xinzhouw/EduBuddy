import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useAuthStore } from './auth'

export const useLanguageStore = defineStore('language', () => {
  const currentLanguage = ref<'zh' | 'en'>('zh')

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
        await updateUserLanguagePreference(lang)
      } catch (error) {
        console.error('Failed to update language preference:', error)
        // 失败时仍保持前端切换，下次登录会同步
      }
    }
  }

  /**
   * 初始化语言：从后端或本地恢复
   */
  const initLanguage = async () => {
    const authStore = useAuthStore()

    if (authStore.isAuthenticated && authStore.user) {
      // 已登录：使用后端用户偏好
      const userLang = (authStore.user as any).language || 'zh'
      currentLanguage.value = userLang as 'zh' | 'en'
    } else {
      // 未登录：从 localStorage 读取
      const saved = localStorage.getItem('language') as 'zh' | 'en' | null
      currentLanguage.value = saved || 'zh'
    }
  }

  return {
    currentLanguage,
    setLanguage,
    initLanguage
  }
})
