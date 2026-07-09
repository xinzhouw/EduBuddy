# Task 6: 修改 main.ts 注册 vue-i18n 和 Element Plus 多语言

## 文件修改

**Files:**
- Modify: `frontend/src/main.ts`

## Interfaces

**Consumes:** 
- i18n 配置（Task 2 创建）
- zhCn/en locale 从 element-plus

**Produces:** 
- 应用全局注册 i18n 和 Element Plus 多语言支持

## 任务描述

修改 main.ts 以注册 vue-i18n 和设置 Element Plus 的默认语言。

### 修改的代码

在 main.ts 中：

1. 在导入部分添加：
```typescript
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import i18n from './i18n'
```

2. 在 `app.use()` 调用中添加：
```typescript
app.use(i18n)  // 注册 i18n
app.use(ElementPlus, { locale: zhCn })  // 改为包含 locale 参数
```

### 完整示例

见计划文档 main.ts 部分。

## 报告位置

完成后写报告到 `/home/xinzhouw/src/EduBuddy/.superpowers/sdd/task-6-i18n-report.md`
