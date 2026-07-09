# Task 8: 修改 App.vue 初始化语言

## 文件修改

**Files:**
- Modify: `frontend/src/App.vue`

## Interfaces

**Consumes:** 
- `useLanguageStore()` - initLanguage() 方法
- `useI18n()` - 访问 locale 对象

**Produces:** 
- 应用启动时正确初始化语言状态

## 任务描述

在 App.vue 的 onMounted hook 中初始化语言，同步 i18n 和 Element Plus locale。

### 实现代码

在 App.vue `<script setup>` 的导入中添加：

```typescript
import { useLanguageStore } from '@/stores/language'
import { useI18n } from 'vue-i18n'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import en from 'element-plus/dist/locale/en.mjs'
```

在 onMounted hook 中添加：

```typescript
onMounted(async () => {
  const langStore = useLanguageStore()
  const { locale } = useI18n()
  
  // 初始化语言
  await langStore.initLanguage()
  
  // 同步 i18n 和 Element Plus locale
  locale.value = langStore.currentLanguage
  const elLocale = langStore.currentLanguage === 'zh' ? zhCn : en
  app.config.globalProperties.$ELEMENT = { locale: elLocale }
  
  // ... 现有的初始化逻辑
})
```

## 报告位置

完成后写报告到 `/home/xinzhouw/src/EduBuddy/.superpowers/sdd/task-8-i18n-report.md`
