# Task 9: 在 Pinia store 初始化时恢复用户语言

## 文件修改

**Files:**
- Modify: `frontend/src/stores/auth.ts`

## Interfaces

**Consumes:** 
- 登录后返回的用户对象中的 language 字段

**Produces:** 
- 用户登录后，Language Store 自动初始化用户的语言偏好

## 任务描述

在 auth store 的登录或设置用户信息的地方，初始化 Language Store 的语言偏好。

### 实现代码

在登录成功、设置用户或恢复会话的地方添加：

```typescript
import { useLanguageStore } from './language'

// 在设置用户信息的地方（通常是 user.value = userData 之后）
const langStore = useLanguageStore()
if (user?.language) {
  langStore.currentLanguage = user.language
  localStorage.setItem('language', user.language)
}
```

## 报告位置

完成后写报告到 `/home/xinzhouw/src/EduBuddy/.superpowers/sdd/task-9-i18n-report.md`
