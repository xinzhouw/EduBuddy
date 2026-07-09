# Task 9 完成报告：Auth Store 恢复用户语言

## 状态：完成

## 修改文件

- `frontend/src/stores/auth.ts`

## 变更内容

### 1. 新增 import
```typescript
import { useLanguageStore } from './language'
```

### 2. User 接口增加 language 字段
```typescript
language?: string | null
```

### 3. 新增 syncUserLanguage 辅助函数
在 store 内部定义，避免三处重复代码：
```typescript
function syncUserLanguage(userData: User | null) {
  if (userData?.language) {
    const langStore = useLanguageStore()
    langStore.currentLanguage = userData.language as 'zh' | 'en'
    localStorage.setItem('language', userData.language)
  }
}
```

### 4. 调用位置（三处）
- `login()` — `user.value = authData.user` 之后
- `register()` — `user.value = authData.user` 之后
- `fetchMe()` — `user.value = res.data` 之后

## 循环依赖说明

`auth.ts` 导入 `language.ts`，`language.ts` 也导入 `auth.ts`。  
这在 Pinia 中是安全的：`useLanguageStore()` 和 `useAuthStore()` 均在函数体内懒调用，
模块加载时不执行 store 实例化，不会产生死循环。

## 行为说明

- 用户登录/注册/刷新 Me 时，若后端返回 `language` 字段，自动同步到 Language Store 和 localStorage。
- 若用户无 `language` 字段（值为 null/undefined），不覆盖当前语言设置，保持原有行为。
