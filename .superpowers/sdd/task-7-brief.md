# Task 7: 修改 Axios 客户端添加 Accept-Language header

## 文件修改

**Files:**
- Modify: `frontend/src/api/client.ts`

## Interfaces

**Consumes:** 
- `useLanguageStore()` - 获取当前语言

**Produces:** 
- Axios 实例在所有请求中自动加 `Accept-Language` header

## 任务描述

添加 Axios 请求拦截器，在每个请求中自动加 Accept-Language header。

### 实现代码

在 axios 实例创建后添加请求拦截器：

```typescript
import { useLanguageStore } from '@/stores/language'

api.interceptors.request.use((config) => {
  const langStore = useLanguageStore()
  config.headers['Accept-Language'] = langStore.currentLanguage
  return config
})
```

## 报告位置

完成后写报告到 `/home/xinzhouw/src/EduBuddy/.superpowers/sdd/task-7-i18n-report.md`
