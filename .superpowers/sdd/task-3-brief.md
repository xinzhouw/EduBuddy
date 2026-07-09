# Task 3: 创建 Language Store

## 文件修改

**Files:**
- Create: `frontend/src/stores/language.ts`

## Interfaces

**Consumes:** 
- `@/api/user` 中的 `updateUserLanguagePreference(lang)` 函数（在 Task 11 创建，但现在先用 mock）

**Produces:**
- `useLanguageStore()` - Pinia store，提供：
  - `currentLanguage: Ref<'zh' | 'en'>` - 当前语言
  - `setLanguage(lang: 'zh' | 'en'): Promise<void>` - 切换语言
  - `initLanguage(): Promise<void>` - 初始化语言

## 任务描述

创建 Pinia store 来管理语言状态。这是前端多语言系统的核心状态容器。

### 全局约束
- 语言参数统一使用 `'zh'` 和 `'en'`
- 前端未登录时使用 localStorage 存储语言偏好

### 创建的文件详情

`frontend/src/stores/language.ts` - 完整实现如下：

```typescript
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
      const userLang = authStore.user.language || 'zh'
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
```

## 实现步骤

1. 创建 `frontend/src/stores/language.ts` 文件
2. 定义 Pinia store，使用 Composition API 风格
3. 实现 setLanguage() - 更新状态、localStorage、后端同步
4. 实现 initLanguage() - 从后端或 localStorage 恢复
5. 导出 useLanguageStore() 函数
6. 提交到 git

## 验证方式

编译验证（无类型错误）：
```bash
cd frontend && npm run build 2>&1 | grep -i error | head -10
```

## 报告位置

完成后写报告到 `/home/xinzhouw/src/EduBuddy/.superpowers/sdd/task-3-i18n-report.md`

包含：
- 创建的文件
- TypeScript 编译结果
- commit ID
- 任何观察
