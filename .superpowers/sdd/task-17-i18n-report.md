# Task 17 完成报告：前端 API 函数 updateUserLanguagePreference

## 状态
已完成 ✅

## 实现内容

创建了新文件 `frontend/src/api/user.ts`，包含：

```typescript
import api from './index'

export const updateUserLanguagePreference = async (language: 'zh' | 'en') => {
  const response = await api.patch('/users/preferences', { language })
  return response.data
}
```

## 关键决策

- **导入路径**：规范示例使用 `./client`，但项目中不存在该文件。所有其他 API 文件均从 `./index` 导入，故采用 `./index`。
- **URL 路径**：`index.ts` 中 `baseURL` 已设为 `/api`，因此端点使用 `/users/preferences`（不含 `/api` 前缀），避免重复。

## 文件位置

`/home/xinzhouw/src/EduBuddy/frontend/src/api/user.ts`
