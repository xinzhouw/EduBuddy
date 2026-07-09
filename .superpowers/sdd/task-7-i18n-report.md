# Task 7 完成报告：Axios 客户端添加 Accept-Language header

## 状态
已完成 ✅

## 修改文件
- `frontend/src/api/index.ts`

## 变更内容

### 1. 新增 import
在文件顶部添加了 `useLanguageStore` 的导入：
```typescript
import { useLanguageStore } from '@/stores/language'
```

### 2. 新增请求拦截器
在 Token 拦截器之后、响应拦截器之前，新增了一个专门处理语言 header 的请求拦截器：
```typescript
api.interceptors.request.use((config) => {
  const langStore = useLanguageStore()
  config.headers['Accept-Language'] = langStore.currentLanguage
  return config
})
```

## 设计说明

- `useLanguageStore()` 在拦截器函数内部调用（而非模块顶层），确保 Pinia 已初始化后才访问 store，避免 "store not activated" 错误。
- `langStore.currentLanguage` 在 Pinia setup store 中会自动解包 ref，直接返回 `'zh'` 或 `'en'` 字符串。
- 循环依赖安全：`language.ts` store 对 `@/api/user` 的引用使用的是动态 import（`await import('@/api/user')`），不会产生静态循环依赖。
- 每次请求都从 store 实时读取当前语言，确保语言切换后立即生效，无需重新初始化。

## 注意事项
- `frontend/src/api/index.ts` 是实际的 Axios 客户端文件（规范中写的 `client.ts` 不存在，index.ts 是实际入口）。
