# Task 6 完成报告：main.ts 注册 i18n 与 Element Plus 多语言

## 状态
完成 ✅

## 修改文件
`frontend/src/main.ts`

## 变更内容

### 新增导入（imports 区域）
```typescript
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import i18n from './i18n'
```

### 新增 app.use 注册
```typescript
app.use(i18n)                          // 注册 vue-i18n
app.use(ElementPlus, { locale: zhCn }) // Element Plus 改为使用 zhCn locale
```

原来的 `app.use(ElementPlus, { locale: undefined })` 已替换为带 `zhCn` 的版本。

## 前置依赖确认
- `frontend/src/i18n/index.ts` 存在（Task 2 已完成）
- `element-plus/dist/locale/zh-cn.mjs` 由 element-plus 包提供，无需额外安装

## 完成时间
2026-07-09
