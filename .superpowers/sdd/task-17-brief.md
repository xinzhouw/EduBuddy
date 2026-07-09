# Task 17: 在前端 api/user.ts 中创建 updateUserLanguagePreference API 调用

## 文件修改

**Files:**
- Create or Modify: `frontend/src/api/user.ts`

## Interfaces

**Produces:**
- `updateUserLanguagePreference(language: 'zh' | 'en'): Promise<void>` - 调用后端 API

## 任务描述

在前端创建 API 函数来调用后端的语言偏好更新端点。

### 实现代码

```typescript
import api from './client'

export const updateUserLanguagePreference = async (language: 'zh' | 'en') => {
  const response = await api.patch('/api/users/preferences', { language })
  return response.data
}
```

## 报告位置

完成后报告到 `/home/xinzhouw/src/EduBuddy/.superpowers/sdd/task-17-i18n-report.md`
