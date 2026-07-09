# Task 3 Report: Language Store

## 创建的文件

- `frontend/src/stores/language.ts` — Pinia store，Composition API 风格

## 实现说明

- `currentLanguage` ref 默认值为 `'zh'`
- `setLanguage(lang)` 更新 state + localStorage；若已登录则动态 import `@/api/user` 同步后端，失败时 catch 并 console.error（前端切换不受影响）
- `initLanguage()` 已登录时从 `authStore.user.language` 读取偏好，未登录时从 localStorage 读取
- `authStore.user` 暂时通过 `as any` 访问 `.language`，因为 `User` interface 尚未包含该字段（待 Task 11 补充）

## TypeScript 编译结果

```
✓ built in 1.93s
```

无 TypeScript 错误，仅有来自第三方库（vueuse）的 pre-existing 注释警告。

## Commit ID

`0b5daa8` — feat(i18n): add language Pinia store (Task 3)

## 观察

- `@/api/user` 在 Task 11 创建前不存在，但动态 import 在运行时才执行，且包裹在 try/catch 中，所以不影响编译和运行
- `User` interface 的 `language` 字段将在后续任务中添加，届时可移除 `as any` 类型断言
